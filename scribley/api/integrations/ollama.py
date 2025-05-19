"""
Ollama integration for Scribley - enables local AI capabilities.

This integration provides a client for interacting with Ollama's API,
allowing article summarization, tag generation, and other AI features
without relying on external services.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama to provide local AI capabilities."""
    
    def __init__(self, base_url: str = None, model: str = None):
        """
        Initialize the Ollama client.
        
        Args:
            base_url (str, optional): Base URL for Ollama API. Defaults to environment variable or localhost.
            model (str, optional): Default model to use. Defaults to environment variable or 'llama2'.
        """
        self.base_url = base_url or os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama2")
        self._validate_connection()
    
    def _validate_connection(self) -> bool:
        """Check if Ollama is available and the model is loaded."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                if not any(model.get("name") == self.model for model in models):
                    logger.warning(f"Model '{self.model}' not found in Ollama. Available models: {[model.get('name') for model in models]}")
                    return False
                return True
            else:
                logger.warning(f"Failed to connect to Ollama API: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Error connecting to Ollama: {str(e)}")
            return False
    
    def generate_text(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate text using Ollama.
        
        Args:
            prompt (str): The prompt to generate text from
            max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 500.
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            
        Returns:
            Dict[str, Any]: Response containing the generated text
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            if response.status_code == 200:
                return {"text": response.json().get("response", ""), "success": True}
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {"text": "", "error": response.text, "success": False}
                
        except Exception as e:
            logger.error(f"Error generating text with Ollama: {str(e)}")
            return {"text": "", "error": str(e), "success": False}
    
    def summarize_article(self, article_text: str, max_length: int = 150) -> str:
        """
        Summarize an article using Ollama.
        
        Args:
            article_text (str): The article text to summarize
            max_length (int, optional): Maximum length of summary in words. Defaults to 150.
            
        Returns:
            str: The summarized text
        """
        prompt = f"""Summarize the following article in {max_length} words or less, 
                    focusing on the main points and key takeaways:
                    
                    {article_text}
                    
                    Summary:"""
        
        response = self.generate_text(prompt, max_tokens=max_length * 4)  # 4 tokens per word approx
        if response["success"]:
            return response["text"].strip()
        else:
            logger.error(f"Error summarizing article: {response.get('error', 'Unknown error')}")
            return ""
    
    def generate_tags(self, article_text: str, max_tags: int = 5) -> List[str]:
        """
        Generate tags for an article using Ollama.
        
        Args:
            article_text (str): The article text to generate tags for
            max_tags (int, optional): Maximum number of tags to generate. Defaults to 5.
            
        Returns:
            List[str]: List of generated tags
        """
        # Truncate article if too long to avoid context length issues
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
            # Clean and parse tags
            raw_tags = response["text"].strip().split(",")
            tags = [tag.strip() for tag in raw_tags if tag.strip()]
            return tags[:max_tags]  # Ensure we don't exceed max_tags
        else:
            logger.error(f"Error generating tags: {response.get('error', 'Unknown error')}")
            return []
    
    def improve_title(self, original_title: str, article_text: str) -> str:
        """
        Suggest an improved title for an article using Ollama.
        
        Args:
            original_title (str): The original title
            article_text (str): The article text
            
        Returns:
            str: An improved title suggestion
        """
        # Use a shorter excerpt of the article for context
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
        
        Args:
            article_text (str): The article text to check
            
        Returns:
            Dict[str, Any]: Dictionary containing feedback on the article
        """
        # Truncate article if too long
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
                # Extract JSON from the response
                text = response["text"].strip()
                # Find JSON object in the response if it's surrounded by other text
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

    def draft_article(self, topic: str, outline: Optional[List[str]] = None, length: str = "medium", style: str = "informative") -> str:
        """
        Generate an article draft based on a topic and optional outline.
        
        Args:
            topic (str): The main topic for the article
            outline (List[str], optional): List of points to cover in the article. Defaults to None.
            length (str, optional): Desired length of the article ('short', 'medium', 'long'). Defaults to "medium".
            style (str, optional): Writing style ('informative', 'conversational', 'persuasive', 'technical'). Defaults to "informative".
            
        Returns:
            str: The generated article draft
        """
        # Define word count ranges based on length parameter
        length_ranges = {
            "short": "500-750 words",
            "medium": "1000-1500 words",
            "long": "2000-3000 words"
        }
        
        # Style instructions
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
        
        # Calculate max tokens based on length
        max_tokens_map = {"short": 1000, "medium": 2000, "long": 4000}
        max_tokens = max_tokens_map.get(length.lower(), 2000)
        
        response = self.generate_text(prompt, max_tokens=max_tokens, temperature=0.7)
        if response["success"]:
            return response["text"].strip()
        else:
            logger.error(f"Error drafting article: {response.get('error', 'Unknown error')}")
            return ""


# Example usage
if __name__ == "__main__":
    client = OllamaClient()
    
    # Test connection
    print(f"Ollama connected: {client._validate_connection()}")
    
    # Example article for testing
    test_article = """
    Artificial intelligence has rapidly transformed industries across the globe.
    From healthcare to finance, AI is enabling new possibilities and efficiencies.
    However, with these advancements come significant ethical considerations
    that must be addressed by policymakers and technologists alike.
    """
    
    # Test summarization
    summary = client.summarize_article(test_article)
    print(f"Summary: {summary}")
    
    # Test tag generation
    tags = client.generate_tags(test_article)
    print(f"Tags: {tags}") 