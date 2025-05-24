"""
Ollama integration for Scribley - enables local AI capabilities.

This integration provides a client for interacting with Ollama's API,
allowing article summarization, tag generation, and other AI features
without relying on external services.
"""

import os
import json
import logging
import httpx
import asyncio
from typing import List, Dict, Any, Optional, Union, AsyncGenerator

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama to provide local AI capabilities."""
    
    def __init__(self, base_url: str = None, model_name_preference: str = None, sync_requests_lib=None):
        self.base_url = base_url or os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        self.model: Optional[str] = None
        self.initialized_successfully: bool = False
        
        if not sync_requests_lib:
            # Fallback if not provided, though it should be by the factory
            import requests as sync_requests_fallback
            sync_requests_to_use = sync_requests_fallback
            logger.warning("OllamaClient initialized without sync_requests_lib, using fallback import.")
        else:
            sync_requests_to_use = sync_requests_lib

        if not self._validate_connection(sync_requests_to_use): 
            logger.warning("OllamaClient initialization failed: _validate_connection returned False.")
            return

        logger.info("OllamaClient: _validate_connection successful. Proceeding to set initial model.")

        preferred_model_from_env = os.environ.get("OLLAMA_MODEL")
        model_to_try_first = model_name_preference or preferred_model_from_env

        if model_to_try_first:
            logger.info(f"OllamaClient attempting to set initial model to '{model_to_try_first}' (from constructor arg or OLLAMA_MODEL env var).")
            if self.set_model(model_to_try_first, sync_requests_to_use):
                logger.info(f"OllamaClient successfully initialized with model: {self.model}")
            else:
                logger.warning(f"OllamaClient: Preferred initial model '{model_to_try_first}' not found or couldn't be set. Current self.model: {self.model}")

        if not self.model: 
            logger.info("OllamaClient: No preferred model was set or it failed. Trying to set to the first available model from /api/tags.")
            try:
                response = sync_requests_to_use.get(f"{self.base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models_data = response.json().get("models", [])
                    if models_data:
                        first_available_model_name = models_data[0].get("name")
                        if first_available_model_name:
                            logger.info(f"OllamaClient: Found first available model: '{first_available_model_name}'. Attempting to set.")
                            if self.set_model(first_available_model_name, sync_requests_to_use):
                                logger.info(f"OllamaClient initialized with first available model: {self.model}")
                            else:
                                logger.error(f"OllamaClient: Critical error - Failed to set model to '{first_available_model_name}' even though it was listed in /api/tags. This implies an issue with set_model logic.")
                        else:
                            logger.warning("OllamaClient: First model from /api/tags has no 'name' attribute.")
                    else:
                        logger.warning("OllamaClient: Ollama is available but has no models installed (/api/tags returned empty list). `self.model` remains None.")
                else:
                    logger.warning(f"OllamaClient: Could not fetch models from /api/tags during init to set a default. Status: {response.status_code}, Response: {response.text[:200]}...")
            except sync_requests_to_use.exceptions.RequestException as e:
                logger.error(f"OllamaClient: RequestException during /api/tags fetch in init: {str(e)}")
            except Exception as e:
                logger.error(f"OllamaClient: Unexpected error fetching/setting first available model during init: {str(e)}", exc_info=True)
        
        if not self.model:
            logger.warning("OllamaClient initialized, but NO model is currently set (e.g., no preference, no env var, no available models, or errors during init). Generation will fail until a model is explicitly set.")
        else:
            logger.info(f"OllamaClient initialization complete. Current model: {self.model}")
            self.initialized_successfully = True
    
    def _validate_connection(self, sync_requests_lib) -> bool:
        """Check if Ollama API is available and responsive."""
        try:
            response = sync_requests_lib.get(f"{self.base_url}/api/tags", timeout=5) 
            if response.status_code == 200:
                logger.info(f"Ollama API connection successful. Found models: {response.json().get('models', [])}")
                return True
            else:
                logger.warning(f"Failed to connect to Ollama API at {self.base_url}/api/tags. Status: {response.status_code}, Response: {response.text}")
                return False
        except sync_requests_lib.exceptions.RequestException as e: 
            logger.warning(f"Error connecting to Ollama API at {self.base_url}/api/tags: {str(e)}")
            return False
        except Exception as e: 
            logger.error(f"Unexpected error during Ollama connection validation: {str(e)}", exc_info=True)
            return False
    
    def set_model(self, model_name: str, sync_requests_lib) -> bool:
        """
        Change the model used by this client.
        """
        try:
            response = sync_requests_lib.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name") for model in models]
                
                if model_name in model_names:
                    self.model = model_name
                    logger.info(f"Model set to {model_name}")
                    return True
                else:
                    logger.warning(f"Model {model_name} not found. Available models: {model_names}")
                    return False
            else:
                logger.warning(f"Failed to get models: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error setting model: {str(e)}")
            return False
    
    def generate_text(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7, top_p: float = 0.9) -> Dict[str, Any]:
        """
        Generate text using Ollama, handling a streaming response internally. (Still uses sync requests)
        """
        import requests as sync_requests # Keep this specific method sync for now if not refactoring all
        if self.model is None:
            logger.error("OllamaClient.generate_text: Attempted to generate text, but no model is set.")
            return {"text": "", "error": "No model configured in Ollama client", "success": False}
        
        logger.info(f"Attempting to generate text with Ollama (streaming) using model: {self.model}")
        
        accumulated_response_text = []
        last_error_message = "Ollama stream ended without a clear error, but no text was generated."
        success = False

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                },
                "stream": True 
            }
            
            if top_p < 1.0:
                payload["options"]["top_p"] = top_p

            logger.debug(f"Ollama /api/generate (streaming) PAYLOAD: {json.dumps(payload, indent=2)}")
            
            with sync_requests.post(
                f"{self.base_url}/api/generate",
                headers={"Content-Type": "application/json"},
                json=payload,
                stream=True, 
                timeout=300  # Increased timeout to 5 minutes
            ) as response:
                logger.debug(f"Ollama /api/generate (streaming) RESPONSE Status: {response.status_code}")
                response.raise_for_status() 

                for line in response.iter_lines(): 
                    if line:
                        try:
                            decoded_line = line.decode('utf-8')
                            json_chunk = json.loads(decoded_line)
                            
                            if "error" in json_chunk:
                                last_error_message = json_chunk["error"]
                                logger.error(f"Ollama stream returned an error: {last_error_message}")
                                success = False
                                break 
                            
                            chunk_text = json_chunk.get("response", "")
                            accumulated_response_text.append(chunk_text)
                            
                            if json_chunk.get("done") is True:
                                logger.info("Ollama stream finished (done:true).")
                                if not "".join(accumulated_response_text).strip() and not chunk_text.strip(): 
                                    logger.warning("Ollama stream finished but no text was generated. Possible content filter or prompt issue.")
                                    last_error_message = "Ollama finished but no text was generated (stream)."
                                success = True 
                                break 

                        except json.JSONDecodeError as e:
                            logger.error(f"Error decoding JSON from Ollama stream: {e}. Line: '{line.decode('utf-8', errors='ignore')}'")
                            last_error_message = "Error decoding stream data from Ollama."
                            success = False
                            break 
                        except Exception as e:
                            logger.error(f"Unexpected error processing Ollama stream line: {e}", exc_info=True)
                            last_error_message = f"Unexpected error during stream processing: {str(e)}"
                            success = False
                            break
                
                if not success and not any(err in last_error_message for err in ["Ollama stream returned an error", "Error decoding stream data", "Unexpected error"]):
                    logger.warning(f"Ollama stream iteration finished, but 'done:true' was not encountered or an error occurred. Accumulated partial text (if any) might be returned.")
                    if not "".join(accumulated_response_text).strip():
                         last_error_message = "Ollama stream ended prematurely or without generating text."

        except sync_requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to or streaming from Ollama /api/generate for model {self.model} at {self.base_url}. Prompt: {prompt[:100]}...", exc_info=True)
            return {"text": "", "error": "Timeout with Ollama during text generation (stream).", "success": False}
        except sync_requests.exceptions.HTTPError as e:
            logger.error(f"HTTPError from Ollama /api/generate for model {self.model}: {e}. Response: {e.response.text if e.response else 'N/A'}", exc_info=True) # type: ignore
            return {"text": "", "error": f"Ollama API HTTP Error: {e.response.status_code if e.response else 'Unknown'}", "raw_error": e.response.text if e.response else str(e), "success": False} # type: ignore
        except sync_requests.exceptions.RequestException as e:
            logger.error(f"RequestException with Ollama /api/generate (streaming) for model {self.model}: {str(e)}. Prompt: {prompt[:100]}...", exc_info=True)
            return {"text": "", "error": f"Ollama connection error (stream): {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error in generate_text (streaming) with Ollama model {self.model}: {str(e)}. Prompt: {prompt[:100]}...", exc_info=True)
            return {"text": "", "error": f"Unexpected error during streaming: {str(e)}", "success": False}

        final_text = "".join(accumulated_response_text).strip()
        if success and final_text:
            return {"text": final_text, "success": True}
        elif success and not final_text: 
            return {"text": "", "error": last_error_message, "success": False} 
        else: 
            return {"text": final_text, "error": last_error_message, "success": False} 
    
    async def chat_completion_stream(self,
                                     messages: List[Dict[str, str]],
                                     max_tokens: int = 500,
                                     temperature: float = 0.7,
                                     top_p: float = 0.9,
                                     model: Optional[str] = None,
                                     retries: int = 3,
                                     base_backoff: float = 2.0) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a chat completion using Ollama, yielding chunks of the response. (Uses httpx)
        Yields dictionaries like {"text_chunk": "...", "done": False, "error": None}
        or {"text_chunk": None, "done": True, "error": "some error message if any"}
        
        Implements exponential backoff retry for 502 errors.
        """
        selected_model_name = model or self.model
        if selected_model_name is None:
            logger.error("OllamaClient.chat_completion_stream: No model set or provided.")
            yield {"text_chunk": None, "done": True, "error": "No model configured or selected in Ollama client"}
            return

        logger.info(f"Attempting to stream chat completion with Ollama model: {selected_model_name}")

        # Prepare payload
        system_message_content = None
        formatted_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_message_content = msg.get("content")
            else:
                formatted_messages.append({"role": msg.get("role"), "content": msg.get("content")})
            
        payload = {
            "model": selected_model_name,
            "messages": formatted_messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        # Only add these parameters if needed, as some models might not support all options
        if max_tokens > 0:
            payload["options"]["num_predict"] = max_tokens
            
        if top_p < 1.0:
            payload["options"]["top_p"] = top_p
        
        if system_message_content:
            payload["system"] = system_message_content

        logger.debug(f"Ollama /api/chat (streaming) PAYLOAD: {json.dumps(payload, indent=2)}")

        # Implement retry loop with exponential backoff
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:  # Increased timeout to 5 minutes
                    async with client.stream("POST",
                        f"{self.base_url}/api/chat",
                        headers={"Content-Type": "application/json"},
                        json=payload,
                    ) as response:
                        logger.debug(f"Ollama /api/chat (streaming) RESPONSE Status: {response.status_code} (attempt {attempt+1}/{retries})")
                        response.raise_for_status() 

                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    json_chunk = json.loads(line)
                                    if "error" in json_chunk:
                                        error_message = json_chunk["error"]
                                        logger.error(f"Ollama chat stream returned an error: {error_message}")
                                        yield {"text_chunk": None, "done": True, "error": error_message}
                                        return

                                    chunk_message = json_chunk.get("message", {})
                                    text_chunk = chunk_message.get("content", "")
                                    is_done = json_chunk.get("done", False)
                                    
                                    if text_chunk:
                                        yield {"text_chunk": text_chunk, "done": False, "error": None}
                                
                                    if is_done:
                                        logger.info("Ollama chat stream finished (done:true).")
                                        yield {"text_chunk": None, "done": True, "error": None} 
                                        return 

                                except json.JSONDecodeError as e:
                                    logger.error(f"Error decoding JSON from Ollama chat stream: {e}. Line: '{line}'")
                                    yield {"text_chunk": None, "done": True, "error": "Error decoding stream data from Ollama."}
                                    return
                                except Exception as e:
                                    logger.error(f"Unexpected error processing Ollama chat stream line: {e}", exc_info=True)
                                    yield {"text_chunk": None, "done": True, "error": f"Unexpected error during stream processing: {str(e)}"}
                                    return
                    
                        logger.warning("Ollama chat stream iteration finished, but 'done:true' was not encountered.")
                        yield {"text_chunk": None, "done": True, "error": "Stream ended without explicit 'done' signal."}
                
                # If we get here without an exception, the request was successful
                # Break out of the retry loop
                break

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                
                # Handle 502 errors with retry logic
                if status_code == 502 and attempt < retries - 1:
                    backoff_time = base_backoff * (2 ** attempt)
                    logger.warning(
                        f"Received 502 from Ollama on attempt {attempt+1}/{retries}. "
                        f"Retrying in {backoff_time}s..."
                    )
                    await asyncio.sleep(backoff_time)
                    continue
                
                # For non-502 errors or the final retry attempt, handle as before
                error_detail_for_yield = f"Ollama API Error: {status_code}."
                log_message_detail = "N/A (initial value)"

                try:
                    if e.response:
                        logger.info(f"Attempting to read error response body for status {status_code} from Ollama. Stream is_closed: {e.response.is_closed}")
                        if not e.response.is_closed:
                            try:
                                await e.response.aread() # This loads the body into e.response.content
                                if e.response.content:
                                    logger.info(f"Successfully read {len(e.response.content)} bytes from Ollama error response.")
                                    try:
                                        decoded_text = e.response.content.decode('utf-8')
                                        log_message_detail = decoded_text
                                        logger.info(f"Decoded Ollama error response: {log_message_detail[:500]}")
                                    except UnicodeDecodeError:
                                        logger.warning("Failed to decode Ollama error response as UTF-8. Logging raw content as repr.")
                                        log_message_detail = repr(e.response.content)
                                else:
                                    logger.warning("Ollama error response body is empty after aread() despite stream not being initially closed.")
                                    log_message_detail = "N/A (empty body after aread)"
                            except httpx.StreamClosed as sc_exc:
                                logger.error(f"httpx.StreamClosed occurred while trying to 'await e.response.aread()'. Stream was likely closed by server. Details: {sc_exc}", exc_info=True)
                                log_message_detail = "N/A (StreamClosed during aread)"
                            except Exception as inner_read_exc:
                                logger.error(f"Unexpected exception during 'await e.response.aread()': {inner_read_exc}", exc_info=True)
                                log_message_detail = f"N/A (unexpected exception during aread: {str(inner_read_exc)})"
                        else:
                            logger.warning(f"Ollama error response stream (status {status_code}) was already closed before attempting read. Cannot read body.")
                            log_message_detail = "N/A (stream was already closed)"
                        
                        error_detail_for_yield = f"Ollama API Error: {status_code}. Detail: {log_message_detail[:200]}"
                    else:
                        logger.warning(f"HTTPStatusError (status {status_code}) caught, but e.response is None. This is unexpected.")
                        log_message_detail = "N/A (no response object in exception)"
                        error_detail_for_yield = f"Ollama API Error: {status_code if status_code else 'Unknown'}. Detail: N/A (no response object)"

                except Exception as outer_read_exc: # Catch any other exceptions in the try block itself
                    logger.error(f"Outer exception while reading/processing Ollama error response body (status {status_code}): {outer_read_exc}", exc_info=True)
                    log_message_detail = f"N/A (outer exception during read: {str(outer_read_exc)})"
                    error_detail_for_yield = f"Ollama API Error: {status_code if status_code else 'Unknown'}. Detail: {log_message_detail[:200]}"

                logger.error(f"HTTPStatusError from Ollama /api/chat for model {selected_model_name}: {e} (attempt {attempt+1}/{retries}). Full Response detail attempt: {log_message_detail[:1000]}", exc_info=True)
                
                # Special case for 502 errors which often indicate Ollama server issues
                if status_code == 502:
                    error_detail_for_yield = f"Ollama API Error: 502 Bad Gateway. This usually indicates that Ollama server is not properly running, the model is not correctly loaded, or the server has insufficient resources. Please check that Ollama is running and has the model '{selected_model_name}' properly loaded."
                
                yield {"text_chunk": None, "done": True, "error": error_detail_for_yield}
                return
                
            except httpx.TimeoutException:
                if attempt < retries - 1:
                    backoff_time = base_backoff * (2 ** attempt)
                    logger.warning(
                        f"Timeout connecting to Ollama on attempt {attempt+1}/{retries}. "
                        f"Retrying in {backoff_time}s..."
                    )
                    await asyncio.sleep(backoff_time)
                    continue
                
                logger.error(f"Timeout streaming from Ollama /api/chat for model {selected_model_name} (all {retries} attempts failed)", exc_info=True)
                yield {"text_chunk": None, "done": True, "error": "Timeout with Ollama during chat generation (stream)."}
                return
                
            except httpx.RequestError as e:
                if attempt < retries - 1:
                    backoff_time = base_backoff * (2 ** attempt)
                    logger.warning(
                        f"Request error with Ollama on attempt {attempt+1}/{retries}: {str(e)}. "
                        f"Retrying in {backoff_time}s..."
                    )
                    await asyncio.sleep(backoff_time)
                    continue
                
                logger.error(f"RequestError with Ollama /api/chat (streaming) for model {selected_model_name} (all {retries} attempts failed): {str(e)}", exc_info=True)
                yield {"text_chunk": None, "done": True, "error": f"Ollama connection error (stream): {str(e)}"}
                return
                
            except Exception as e:
                logger.error(f"Unexpected error in chat_completion_stream with Ollama model {selected_model_name} (attempt {attempt+1}/{retries}): {str(e)}", exc_info=True)
                yield {"text_chunk": None, "done": True, "error": f"Unexpected error during streaming: {str(e)}"}
                return

    def chat_completion(self, 
                     messages: List[Dict[str, str]], 
                     max_tokens: int = 500,
                     temperature: float = 0.7,
                     top_p: float = 0.9,
                     model: str = None) -> Dict[str, Any]:
        """
        Generate a chat completion using Ollama. (Still uses sync requests)
        """
        import requests as sync_requests # Keep this specific method sync for now
        
        if model:
            previous_model = self.model
            if not self.set_model(model, sync_requests):
                logger.warning(f"Failed to set model to {model}, using current model {self.model} instead")
        
        if self.model is None:
            logger.error("OllamaClient.chat_completion: Attempted to generate completion, but no model is set.")
            return {"text": "", "error": "No model configured in Ollama client", "success": False}
        
        logger.info(f"Attempting to generate chat completion with Ollama using model: {self.model}")
        
        try:
            system_message = None
            formatted_messages = []
            
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "system":
                    system_message = content
                else:
                    formatted_messages.append({"role": role, "content": content})
            
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            
            if system_message:
                payload["system"] = system_message
                
            if top_p < 1.0:
                payload["options"]["top_p"] = top_p
                
            logger.debug(f"Ollama /api/chat PAYLOAD: {json.dumps(payload, indent=2)}")
            
            response = sync_requests.post(
                f"{self.base_url}/api/chat",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=300  # Increased timeout to 5 minutes
            )
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data.get("message", {}).get("content", "")
                return {"text": content, "success": True, "full_response": response_data}
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"text": "", "error": error_msg, "success": False}
                
        except Exception as e:
            error_msg = f"Error generating chat completion with Ollama: {str(e)}"
            logger.error(error_msg)
            return {"text": "", "error": error_msg, "success": False}
        finally:
            # Restore previous model if temporary model was used
            if model and previous_model and self.model != previous_model:
                logger.debug(f"Restoring previous model: {previous_model}")
                self.set_model(previous_model, sync_requests)

    def summarize_article(self, article_text: str, max_length: int = 150) -> str:
        """
        Summarize an article using Ollama.
        """
        prompt = f"""Summarize the following article in {max_length} words or less, 
                    focusing on the main points and key takeaways:
                    
                    {article_text}
                    
                    Summary:"""
        
        response = self.generate_text(prompt, max_tokens=max_length * 4) 
        if response["success"]:
            return response["text"].strip()
        else:
            logger.error(f"Error summarizing article: {response.get('error', 'Unknown error')}")
            return ""
    
    def generate_tags(self, article_text: str, max_tags: int = 5) -> List[str]:
        """
        Generate tags for an article using Ollama.
        """
        if len(article_text) > 4000:
            article_text = article_text[:4000] + "..."
        
        prompt = f"""Based on the following article, generate exactly {max_tags} relevant tags. 
                    Each tag should be a single word or short phrase. 
                    Return only the tags separated by commas, with no additional text.
                    
                    Article:
                    {article_text}
                    
                    Tags:"""
        
        response = self.generate_text(prompt, max_tokens=100, temperature=0.3)
        if response["success"]:
            raw_tags = response["text"].strip().split(",")
            tags = [tag.strip() for tag in raw_tags if tag.strip()]
            return tags[:max_tags] 
        else:
            logger.error(f"Error generating tags: {response.get('error', 'Unknown error')}")
            return []
    
    def improve_title(self, original_title: str, article_text: str) -> str:
        """
        Suggest an improved title for an article using Ollama.
        """
        article_excerpt = article_text[:1000] + ("..." if len(article_text) > 1000 else "")
        
        prompt = f"""The following is an article with the title: "{original_title}"
                    
                    Article excerpt:
                    {article_excerpt}
                    
                    Suggest a more engaging and click-worthy title that accurately represents 
                    the content. Return only the suggested title with no additional explanation or text.
                    
                    Suggested title:"""
        
        response = self.generate_text(prompt, max_tokens=50, temperature=0.7)
        if response["success"]:
            return response["text"].strip().strip('"\'')
        else:
            logger.error(f"Error improving title: {response.get('error', 'Unknown error')}")
            return original_title
    
    def check_for_issues(self, article_text: str) -> Dict[str, Any]:
        """
        Check an article for potential issues like grammar, spelling, and readability.
        """
        if len(article_text) > 6000:
            article_text = article_text[:6000] + "..."
        
        prompt = f"""Review the following article text for issues with grammar, spelling, 
                    readability, and overall flow. Provide specific suggestions for improvement 
                    in a structured JSON format with these categories:
                    
                    Article:
                    {article_text}
                    
                    Respond in this exact JSON format:
                    {{
                      "grammar_issues": ["issue 1", "issue 2"],
                      "spelling_issues": ["issue 1", "issue 2"],
                      "readability_suggestions": ["suggestion 1", "suggestion 2"],
                      "flow_improvements": ["improvement 1", "improvement 2"],
                      "overall_rating": "1-10 score with brief explanation"
                    }}
                    """
        
        response = self.generate_text(prompt, max_tokens=500, temperature=0.3)
        if response["success"]:
            try:
                text = response["text"].strip()
                json_start = text.find("{")
                json_end = text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = text[json_start:json_end]
                    return json.loads(json_str)
                else:
                    logger.error("Could not find valid JSON in response")
                    return {"error": "Could not parse feedback"}
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from LLM response: {str(e)}")
                return {"error": "Could not parse feedback", "raw_response": text}
        else:
            logger.error(f"Error checking for issues: {response.get('error', 'Unknown error')}")
            return {"error": response.get("error", "Unknown error")}

    def draft_article(self, 
                    topic: str, 
                    outline: Optional[List[str]] = None, 
                    length: str = "medium", 
                    style: str = "informative",
                    temperature: float = 0.7,
                    top_p: float = 0.9,
                    max_tokens: Optional[int] = None) -> str:
        """
        Generate an article draft based on a topic and optional outline.
        """
        length_ranges = {
            "short": "500-750 words",
            "medium": "1000-1500 words",
            "long": "2000-3000 words"
        }
        
        style_instructions = {
            "informative": "Write in an objective, educational tone that presents facts clearly.",
            "conversational": "Write in a friendly, approachable tone as if speaking directly to the reader.",
            "persuasive": "Write in a compelling tone that aims to convince the reader of a particular viewpoint.",
            "technical": "Write in a precise, detailed tone appropriate for a technically knowledgeable audience."
        }
        
        word_count = length_ranges.get(length.lower(), length_ranges["medium"])
        style_instruction = style_instructions.get(style.lower(), style_instructions["informative"])
        
        outline_text = ""
        if outline:
            outline_points = "\n".join([f"- {point}" for point in outline])
            outline_text = f"\nThe article should cover these points in order:\n{outline_points}\n"
        
        prompt = f"""Write a well-structured article about "{topic}".{outline_text}
                    The article should be approximately {word_count} in length.
                    {style_instruction}
                    
                    Include an engaging introduction that hooks the reader and clearly states the main point.
                    Organize the content with appropriate subheadings.
                    Provide valuable information, insights, or arguments throughout the article.
                    End with a clear conclusion that summarizes the key points.
                    
                    Write the complete article now:
                    """
        
        if max_tokens is None:
            max_tokens_map = {"short": 1000, "medium": 2000, "long": 4000}
            max_tokens = max_tokens_map.get(length.lower(), 2000)
        
        response = self.generate_text(
            prompt=prompt, 
            max_tokens=max_tokens, 
            temperature=temperature,
            top_p=top_p
        )
        
        if response["success"]:
            return response["text"].strip()
        else:
            logger.error(f"Error drafting article: {response.get('error', 'Unknown error')}")
            return ""


if __name__ == "__main__":
    # This example usage would need to be async if testing chat_completion_stream
    # For now, it tests synchronous methods.
    import requests as sync_requests_main
    client = OllamaClient() # __init__ uses sync_requests internally via import
    
    print(f"Ollama connected: {client._validate_connection(sync_requests_main)}") # Pass it if methods expect it
    
    test_article_text = """
    Artificial intelligence has rapidly transformed industries across the globe.
    From healthcare to finance, AI is enabling new possibilities and efficiencies.
    However, with these advancements come significant ethical considerations
    that must be addressed by policymakers and technologists alike.
    """
    
    summary = client.summarize_article(test_article_text)
    print(f"Summary: {summary}")
    
    tags = client.generate_tags(test_article_text)
    print(f"Tags: {tags}")