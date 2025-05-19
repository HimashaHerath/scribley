"""
LM Studio integration for Scribley - enables local AI capabilities.

This integration provides a client for interacting with LM Studio's API,
allowing local LLM inference for article processing and enhancement.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class LMStudioClient:
    """Client for interacting with LM Studio to provide local AI capabilities."""
    
    def __init__(self, base_url: str = None):
        """
        Initialize the LM Studio client.
        
        Args:
            base_url (str, optional): Base URL for LM Studio API. Defaults to environment variable or localhost.
        """
        self.base_url = base_url or os.environ.get("LMSTUDIO_API_URL", "http://localhost:1234/v1")
        self._validate_connection()
    
    def _validate_connection(self) -> bool:
        """Check if LM Studio is available."""
        try:
            # LM Studio follows OpenAI API format, so we can check models endpoint
            response = requests.get(f"{self.base_url}/models")
            if response.status_code == 200:
                models = response.json().get("data", [])
                if models:
                    logger.info(f"Connected to LM Studio. Available models: {[model.get('id') for model in models]}")
                    return True
                else:
                    logger.warning("No models found in LM Studio.")
                    return False
            else:
                logger.warning(f"Failed to connect to LM Studio API: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Error connecting to LM Studio: {str(e)}")
            return False
    
    def chat_completion(self, 
                         messages: List[Dict[str, str]], 
                         max_tokens: int = 500,
                         temperature: float = 0.7,
                         model: str = "local-model") -> Dict[str, Any]:
        """
        Generate a chat completion using LM Studio.
        
        Args:
            messages (List[Dict[str, str]]): List of message objects with role and content
            max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 500.
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            model (str, optional): Model to use. Defaults to "local-model".
            
        Returns:
            Dict[str, Any]: Response containing the generated completion
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # Extract the content from the first choice
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"text": content, "success": True, "full_response": response_data}
            else:
                error_msg = f"LM Studio API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"text": "", "error": error_msg, "success": False}
                
        except Exception as e:
            error_msg = f"Error generating completion with LM Studio: {str(e)}"
            logger.error(error_msg)
            return {"text": "", "error": error_msg, "success": False}
    
    def summarize_article(self, article_text: str, max_length: int = 150) -> str:
        """
        Summarize an article using LM Studio.
        
        Args:
            article_text (str): The article text to summarize
            max_length (int, optional): Maximum length of summary in words. Defaults to 150.
            
        Returns:
            str: The summarized text
        """
        system_prompt = f"You are a professional content summarizer. Create concise summaries that capture the main points in {max_length} words or less."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Summarize the following article, focusing on the main points and key takeaways:\n\n{article_text}"}
        ]
        
        response = self.chat_completion(
            messages=messages,
            max_tokens=max_length * 4,  # 4 tokens per word approx
            temperature=0.3  # Lower temperature for more deterministic summary
        )
        
        if response["success"]:
            return response["text"].strip()
        else:
            logger.error(f"Error summarizing article: {response.get('error', 'Unknown error')}")
            return ""
    
    def generate_tags(self, article_text: str, max_tags: int = 5) -> List[str]:
        """
        Generate tags for an article using LM Studio.
        
        Args:
            article_text (str): The article text to generate tags for
            max_tags (int, optional): Maximum number of tags to generate. Defaults to 5.
            
        Returns:
            List[str]: List of generated tags
        """
        # Truncate article if too long to avoid context length issues
        if len(article_text) > 4000:
            article_text = article_text[:4000] + "..."
        
        system_prompt = "You are a content tagging specialist. Generate relevant tags that accurately represent the content and would perform well in search algorithms."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Based on the following article, generate exactly {max_tags} relevant tags. Each tag should be a single word or short phrase. Return only the tags separated by commas, with no additional text, explanation, or numbering.\n\nArticle:\n{article_text}"}
        ]
        
        response = self.chat_completion(
            messages=messages,
            max_tokens=100,
            temperature=0.3
        )
        
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
        Suggest an improved title for an article using LM Studio.
        
        Args:
            original_title (str): The original title
            article_text (str): The article text
            
        Returns:
            str: An improved title suggestion
        """
        # Use a shorter excerpt of the article for context
        article_excerpt = article_text[:1000] + ("..." if len(article_text) > 1000 else "")
        
        system_prompt = "You are a headline optimization expert for a digital publication. Your job is to create engaging, click-worthy titles that accurately represent the content without being misleading or using clickbait tactics."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"The following is an article with the title: \"{original_title}\"\n\nArticle excerpt:\n{article_excerpt}\n\nSuggest a more engaging and click-worthy title that accurately represents the content. Return only the suggested title with no additional explanation or text."}
        ]
        
        response = self.chat_completion(
            messages=messages,
            max_tokens=50,
            temperature=0.7
        )
        
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
        
        system_prompt = "You are a professional editor and writing coach. Your job is to review articles and provide structured feedback on grammar, spelling, readability, and overall flow. Provide specific suggestions for improvement."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review the following article text for issues with grammar, spelling, readability, and overall flow. Provide specific suggestions for improvement in a structured JSON format with these categories:\n\nArticle:\n{article_text}\n\nRespond in this exact JSON format:\n{{\n  \"grammar_issues\": [\"issue 1\", \"issue 2\"],\n  \"spelling_issues\": [\"issue 1\", \"issue 2\"],\n  \"readability_suggestions\": [\"suggestion 1\", \"suggestion 2\"],\n  \"flow_improvements\": [\"improvement 1\", \"improvement 2\"],\n  \"overall_rating\": \"1-10 score with brief explanation\"\n}}"}
        ]
        
        response = self.chat_completion(
            messages=messages,
            max_tokens=500,
            temperature=0.3
        )
        
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

    def generate_social_post(self, article_title: str, article_text: str, platform: str = "twitter") -> str:
        """
        Generate a social media post for an article.
        
        Args:
            article_title (str): The article title
            article_text (str): The article text
            platform (str, optional): Social media platform. Defaults to "twitter".
            
        Returns:
            str: Generated social media post
        """
        # Truncate article if too long
        article_excerpt = article_text[:1500] + ("..." if len(article_text) > 1500 else "")
        
        platform_instructions = {
            "twitter": "Create a tweet (max 280 characters) that promotes this article with engaging language and relevant hashtags.",
            "linkedin": "Create a professional LinkedIn post (150-250 words) that highlights the business value and key insights of this article.",
            "facebook": "Create a Facebook post (100-200 words) that engages readers emotionally and encourages them to read and share the article.",
            "instagram": "Create an Instagram caption (150-200 words) that's visually descriptive and uses relevant hashtags at the end."
        }
        
        instruction = platform_instructions.get(platform.lower(), platform_instructions["twitter"])
        
        system_prompt = f"You are a social media specialist skilled at creating engaging content for {platform}."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{instruction}\n\nArticle Title: {article_title}\n\nArticle Excerpt:\n{article_excerpt}"}
        ]
        
        response = self.chat_completion(
            messages=messages,
            max_tokens=250,
            temperature=0.7
        )
        
        if response["success"]:
            return response["text"].strip()
        else:
            logger.error(f"Error generating social post: {response.get('error', 'Unknown error')}")
            return ""

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
            outline_text = f"The article should cover these points in order:\n{outline_points}"
        
        system_prompt = "You are a professional content writer skilled at creating well-structured, engaging articles on any topic."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Write a well-structured article about "{topic}".
                {outline_text}
                
                The article should be approximately {word_count} in length.
                {style_instruction}
                
                Include an engaging introduction that hooks the reader and clearly states the main point.
                Organize the content with appropriate subheadings.
                Provide valuable information, insights, or arguments throughout the article.
                End with a clear conclusion that summarizes the key points.
                
                Write the complete article now."""}
        ]
        
        # Calculate max tokens based on length
        max_tokens_map = {"short": 1000, "medium": 2000, "long": 4000}
        max_tokens = max_tokens_map.get(length.lower(), 2000)
        
        response = self.chat_completion(messages=messages, max_tokens=max_tokens, temperature=0.7)
        
        if response["success"]:
            return response["text"].strip()
        else:
            logger.error(f"Error drafting article: {response.get('error', 'Unknown error')}")
            return ""


# Example usage
if __name__ == "__main__":
    client = LMStudioClient()
    
    # Test connection
    print(f"LM Studio connected: {client._validate_connection()}")
    
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