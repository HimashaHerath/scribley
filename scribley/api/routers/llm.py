"""
Router for LLM-powered features in Scribley.

This router provides endpoints for utilizing local LLM capabilities
such as article summarization, tag generation, and text enhancement.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks
from pydantic import BaseModel, Field

from scribley.api.integrations import get_llm_client, llm_factory

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Schemas ---

class LLMSummaryRequest(BaseModel):
    text: str = Field(..., description="The article text to summarize")
    max_length: int = Field(150, description="Maximum length of the summary in words")
    provider: Optional[str] = Field(None, description="LLM provider to use (ollama or lmstudio)")

class LLMTagsRequest(BaseModel):
    text: str = Field(..., description="The article text to generate tags for")
    max_tags: int = Field(5, description="Maximum number of tags to generate")
    provider: Optional[str] = Field(None, description="LLM provider to use (ollama or lmstudio)")

class LLMTitleRequest(BaseModel):
    title: str = Field(..., description="The original title")
    text: str = Field(..., description="The article text")
    provider: Optional[str] = Field(None, description="LLM provider to use (ollama or lmstudio)")

class LLMIssuesRequest(BaseModel):
    text: str = Field(..., description="The article text to check for issues")
    provider: Optional[str] = Field(None, description="LLM provider to use (ollama or lmstudio)")

class LLMSocialPostRequest(BaseModel):
    title: str = Field(..., description="The article title")
    text: str = Field(..., description="The article text")
    platform: str = Field("twitter", description="Social media platform (twitter, linkedin, facebook, instagram)")
    provider: Optional[str] = Field(None, description="LLM provider to use (ollama or lmstudio)")

class LLMDraftArticleRequest(BaseModel):
    topic: str = Field(..., description="The main topic for the article")
    outline: Optional[List[str]] = Field(None, description="List of points to cover in the article")
    length: str = Field("medium", description="Length of the article: 'short', 'medium', or 'long'")
    style: str = Field("informative", description="Writing style: 'informative', 'conversational', 'persuasive', or 'technical'")
    provider: Optional[str] = Field(None, description="LLM provider to use (ollama or lmstudio)")

class LLMProvidersResponse(BaseModel):
    providers: List[str] = Field([], description="List of available LLM providers")
    default_provider: Optional[str] = Field(None, description="Default LLM provider")
    is_available: bool = Field(False, description="Whether any LLM provider is available")

# --- Helper Functions ---

def get_client_or_error(provider: Optional[str] = None):
    """Get the LLM client or raise an HTTP exception if not available."""
    client = get_llm_client(provider)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No LLM provider available. Please install and run Ollama or LM Studio locally."
        )
    return client

# --- Routes ---

@router.get("/providers", response_model=LLMProvidersResponse)
async def get_llm_providers():
    """Get information about available LLM providers."""
    return {
        "providers": llm_factory.get_available_providers(),
        "default_provider": llm_factory.default_provider,
        "is_available": llm_factory.is_available()
    }

@router.post("/summarize", response_model=Dict[str, str])
async def summarize_text(request: LLMSummaryRequest):
    """
    Summarize an article using a local LLM.
    """
    client = get_client_or_error(request.provider)
    
    try:
        summary = client.summarize_article(request.text, max_length=request.max_length)
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize text: {str(e)}"
        )

@router.post("/tags", response_model=Dict[str, List[str]])
async def generate_tags(request: LLMTagsRequest):
    """
    Generate tags for an article using a local LLM.
    """
    client = get_client_or_error(request.provider)
    
    try:
        tags = client.generate_tags(request.text, max_tags=request.max_tags)
        return {"tags": tags}
    except Exception as e:
        logger.error(f"Error generating tags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tags: {str(e)}"
        )

@router.post("/improve-title", response_model=Dict[str, str])
async def improve_title(request: LLMTitleRequest):
    """
    Suggest an improved title for an article using a local LLM.
    """
    client = get_client_or_error(request.provider)
    
    try:
        improved_title = client.improve_title(request.title, request.text)
        return {"title": improved_title}
    except Exception as e:
        logger.error(f"Error improving title: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to improve title: {str(e)}"
        )

@router.post("/check-issues", response_model=Dict[str, Any])
async def check_issues(request: LLMIssuesRequest):
    """
    Check an article for potential issues using a local LLM.
    """
    client = get_client_or_error(request.provider)
    
    try:
        issues = client.check_for_issues(request.text)
        return issues
    except Exception as e:
        logger.error(f"Error checking for issues: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check for issues: {str(e)}"
        )

@router.post("/social-post", response_model=Dict[str, str])
async def generate_social_post(request: LLMSocialPostRequest):
    """
    Generate a social media post for an article using a local LLM.
    """
    client = get_client_or_error(request.provider)
    
    try:
        # Find the appropriate method based on the client type
        if hasattr(client, "generate_social_post"):
            post = client.generate_social_post(request.title, request.text, platform=request.platform)
        else:
            # Fallback for clients without specific social post method
            platform_prompts = {
                "twitter": f"Create a tweet (max 280 characters) that promotes this article with engaging language and relevant hashtags. Title: {request.title}",
                "linkedin": f"Create a professional LinkedIn post (150-250 words) that highlights the business value and key insights of this article. Title: {request.title}",
                "facebook": f"Create a Facebook post (100-200 words) that engages readers emotionally and encourages them to read and share the article. Title: {request.title}",
                "instagram": f"Create an Instagram caption (150-200 words) that's visually descriptive and uses relevant hashtags at the end. Title: {request.title}"
            }
            
            prompt = platform_prompts.get(request.platform.lower(), platform_prompts["twitter"])
            if hasattr(client, "chat_completion"):
                # For LM Studio-like clients
                messages = [
                    {"role": "system", "content": f"You are a social media specialist skilled at creating engaging content for {request.platform}."},
                    {"role": "user", "content": f"{prompt}\n\nArticle excerpt:\n{request.text[:1500]}..."}
                ]
                response = client.chat_completion(messages=messages, max_tokens=250, temperature=0.7)
                post = response.get("text", "")
            else:
                # For Ollama-like clients
                full_prompt = f"You are a social media specialist. {prompt}\n\nArticle excerpt:\n{request.text[:1500]}...\n\nSocial post:"
                response = client.generate_text(prompt=full_prompt, max_tokens=250, temperature=0.7)
                post = response.get("text", "")
        
        return {"post": post}
    except Exception as e:
        logger.error(f"Error generating social post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate social post: {str(e)}"
        )

@router.post("/draft-article", response_model=Dict[str, str])
async def draft_article(request: LLMDraftArticleRequest):
    """
    Generate an article draft based on a topic and optional outline using a local LLM.
    """
    client = get_client_or_error(request.provider)
    
    try:
        draft = client.draft_article(
            topic=request.topic,
            outline=request.outline,
            length=request.length,
            style=request.style
        )
        
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate article draft. The response was empty."
            )
            
        return {"draft": draft}
    except Exception as e:
        logger.error(f"Error drafting article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to draft article: {str(e)}"
        ) 