"""
Router for text generation LLM features.
"""

import logging
import json
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator

from scribley.api.integrations import llm_factory
from .utils import get_client_or_error
from .schemas import (
    DraftParams, DraftResponse,
    SentenceCompletionParams, SentenceCompletionResponse,
    GenerateIntroductionParams, GenerateIntroductionResponse
)
from .system_prompts import get_system_prompt, get_chat_messages

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/draft-article")
async def draft_article_route(request: Request, params: DraftParams):
    """
    Draft a complete article based on a topic and outline.
    
    This endpoint generates a full article draft based on the provided topic,
    outline points, and other parameters like length and style.
    """
    client_ip = request.client.host
    logger.info(f"Article draft stream requested by {client_ip} on topic: {params.topic}")
    
    try:
        client = get_client_or_error(params.provider)
        actual_provider_name_for_log = params.provider if params.provider else llm_factory.default_provider
        logger.debug(f"Using LLM provider for streaming: {actual_provider_name_for_log}")
        
        if params.outline:
            outline_content = "\n".join([f"- {point}" for point in params.outline])
            user_prompt = f"""Write an article about {params.topic}.

Use the following outline:
{outline_content}

The article should be {params.length} in length and written in a {params.style} style."""
        else:
            user_prompt = f"""Write an article about {params.topic}.

The article should be {params.length} in length and written in a {params.style} style."""

        generation_params = {
            "temperature": params.temperature if params.temperature is not None else 0.7,
            "top_p": params.top_p if params.top_p is not None else 0.9,
            "max_tokens": params.max_tokens if params.max_tokens is not None else 2000,
        }
        
        messages_for_llm = get_chat_messages("article_draft", user_prompt)

        async def event_generator() -> AsyncGenerator[str, None]:
            try:
                specific_model_for_ollama_client = None
                if params.model:
                    model_parts = params.model.split(":", 1)
                    if len(model_parts) > 1 and model_parts[0] == actual_provider_name_for_log:
                         # Just use the base model name without provider prefix
                         specific_model_for_ollama_client = params.model.split(":", 1)[1]
                    else:
                         # Use the whole string as provided, could be just "gemma3:1b" directly
                         specific_model_for_ollama_client = params.model
                
                logger.debug(f"Streaming with OllamaClient.chat_completion_stream. Model for client: {specific_model_for_ollama_client or '(client default)'}")
                                
                async for chunk_data in client.chat_completion_stream(
                    messages=messages_for_llm,
                    model=specific_model_for_ollama_client, 
                    **generation_params
                ):
                    if chunk_data.get("error"):
                        logger.error(f"Error in stream from OllamaClient: {chunk_data['error']}")
                        yield f"data: {json.dumps({'error': chunk_data['error'], 'done': True})}\n\n"
                        break 
                    
                    text_to_send = chunk_data.get("text_chunk", "")
                    is_done = chunk_data.get("done", False)
                    
                    if text_to_send or is_done:
                        yield f"data: {json.dumps({'text_chunk': text_to_send, 'done': is_done})}\n\n"

                    if is_done:
                        logger.info(f"Article draft stream finished for {client_ip}.")
                        break
            except Exception as e:
                logger.error(f"Error in event_generator for article draft stream: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'error': 'Unable to generate article draft. Please ensure Ollama is running properly and try again.', 'done': True})}\n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error setting up draft_article stream: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while setting up the article draft stream."
        )

@router.post("/complete-sentence", response_model=SentenceCompletionResponse)
async def complete_sentence_route(request: Request, params: SentenceCompletionParams):
    """
    Complete the current sentence or paragraph based on context.
    
    This endpoint completes the sentence or paragraph that the user is currently writing,
    using the provided context.
    """
    client_ip = request.client.host
    context_length = len(params.contextText.strip())
    logger.info(f"Sentence completion requested by {client_ip} with {context_length} chars of context")
    
    try:
        # Make sure we have enough context
        if context_length < 3:
            logger.warning(f"Context too short for completion: {context_length} chars")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide more context for completion"
            )
            
        client = get_client_or_error(params.provider)
        actual_provider_name_for_log = params.provider if params.provider else llm_factory.default_provider
        logger.debug(f"Using LLM provider: {actual_provider_name_for_log}")
    
        # Configure generation parameters for sentence completion
        generation_params = {
            "temperature": 0.7,  # More creative
            "top_p": 0.9,
            "max_tokens": 100,   # Shorter completion for sentences
        }
        
        # Craft a user prompt
        user_prompt = params.contextText
        
        try:
            # Get formatted messages with system prompt
            messages = get_chat_messages("sentence_completion", user_prompt)
            
            # Use the client-specific generation method
            specific_model = None
            if params.model:
                model_parts = params.model.split(":", 1)
                if len(model_parts) > 1 and model_parts[0] == actual_provider_name_for_log:
                    specific_model = model_parts[1]
                    logger.debug(f"Using specific model for completion: {specific_model}")
                    result = client.chat_completion(messages, model=specific_model, **generation_params)
                else:
                    # Use the whole string as provided
                    specific_model = params.model
                    logger.debug(f"Using model as provided: {specific_model}")
                    result = client.chat_completion(messages, model=specific_model, **generation_params)
            else:
                logger.debug(f"Using default model for completion")
                result = client.chat_completion(messages, **generation_params)
            
            model_used = f"{actual_provider_name_for_log}:{specific_model or client.model}"
            logger.info(f"Successfully completed sentence using {model_used}")
            
            # Return just the completion part
            return {
                "completion": result.strip(),
                "model_used": model_used
            }
        except Exception as e:
            logger.error(f"Error completing sentence: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to complete sentence: {str(e)}"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in complete_sentence: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while completing the sentence"
        )

@router.post("/generate-introduction", response_model=GenerateIntroductionResponse)
async def generate_introduction_route(request: Request, params: GenerateIntroductionParams):
    """
    Generate an engaging introduction for an article based on its title and keywords.
    
    This endpoint creates an introduction paragraph that hooks the reader and
    introduces the main topic of the article.
    """
    client_ip = request.client.host
    logger.info(f"Introduction generation requested by {client_ip} for title: {params.title}")
    
    try:
        client = get_client_or_error(params.provider)
        actual_provider_name_for_log = params.provider if params.provider else llm_factory.default_provider
        logger.debug(f"Using LLM provider: {actual_provider_name_for_log}")
        
        keywords_text = ""
        if params.keywords and len(params.keywords) > 0:
            keywords_text = "Include the following keywords: " + ", ".join(params.keywords)
            logger.debug(f"Using {len(params.keywords)} keywords for introduction")
        
        # Craft the user prompt
        user_prompt = f"""Write an engaging introduction paragraph for an article titled "{params.title}".
The introduction should hook the reader, introduce the main topic, and set the stage for the rest of the article.
{keywords_text}
Make it approximately 3-5 sentences long.
"""
        
        # Configure generation parameters
        generation_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 250,  # Introduction length
        }
        
        try:
            # Get formatted messages with system prompt
            messages = get_chat_messages("introduction", user_prompt)
            
            # Use the client-specific generation method
            specific_model = None
            if params.model:
                model_parts = params.model.split(":", 1)
                if len(model_parts) > 1 and model_parts[0] == actual_provider_name_for_log:
                    specific_model = model_parts[1]
                    logger.debug(f"Using specific model for introduction: {specific_model}")
                    result = client.chat_completion(messages, model=specific_model, **generation_params)
                else:
                    # Use the whole string as provided
                    specific_model = params.model
                    logger.debug(f"Using model as provided: {specific_model}")
                    result = client.chat_completion(messages, model=specific_model, **generation_params)
            else:
                logger.debug(f"Using default model for introduction")
                result = client.chat_completion(messages, **generation_params)
            
            model_used = f"{actual_provider_name_for_log}:{specific_model or client.model}"
            logger.info(f"Successfully generated introduction using {model_used}")
            
            # Return the introduction
            return {
                "introduction": result.strip(),
                "model_used": model_used
            }
        except Exception as e:
            logger.error(f"Error generating introduction: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate introduction: {str(e)}"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_introduction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the introduction"
        ) 