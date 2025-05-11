"""
Medium API client implementation.
"""

import requests
import json
import logging
from pathlib import Path
from markdown import markdown
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Fix the relative import issue
try:
    from scribley.config.config import get_config
except ImportError:
    # Fallback for direct script execution
    import sys
    import yaml
    
    def get_config():
        """Simple fallback config function when the config module can't be imported"""
        config = {
            "medium": {
                "api_token": os.getenv("MEDIUM_API_TOKEN"),
                "publication_id": os.getenv("MEDIUM_PUBLICATION_ID", ""),
                "default_status": "draft",
                "default_license": "all-rights-reserved",
                "notify_followers": False,
                "content_format": "html",
                "canonical_url": "",
                "tags": []
            },
            "user_info": {
                "name": "",
                "username": "",
                "url": ""
            }
        }
        return config

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MediumAPIClient:
    """Client for interacting with the Medium API"""
    
    BASE_URL = "https://api.medium.com/v1"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("MEDIUM_API_TOKEN")
        if not self.token:
            raise ValueError("Medium API token is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Charset": "utf-8"
        }
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get the current user's information"""
        response = requests.get(
            f"{self.BASE_URL}/me",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_user_publications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get publications that the user is a contributor to"""
        response = requests.get(
            f"{self.BASE_URL}/users/{user_id}/publications",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json().get("data", [])
    
    def create_post(
        self,
        user_id: str,
        title: str,
        content: str,
        content_format: str = "markdown",
        tags: Optional[List[str]] = None,
        canonical_url: Optional[str] = None,
        publish_status: str = "draft",
        license: Optional[str] = None,
        publication_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a post on Medium"""
        payload = {
            "title": title,
            "contentFormat": content_format,
            "content": content,
            "publishStatus": publish_status
        }
        
        if tags:
            payload["tags"] = tags
        
        if canonical_url:
            payload["canonicalUrl"] = canonical_url
            
        if license:
            payload["license"] = license
        
        # If publishing to a publication
        if publication_id:
            response = requests.post(
                f"{self.BASE_URL}/publications/{publication_id}/posts",
                headers=self.headers,
                json=payload
            )
        else:
            response = requests.post(
                f"{self.BASE_URL}/users/{user_id}/posts",
                headers=self.headers,
                json=payload
            )
        
        response.raise_for_status()
        return response.json()
    
    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a specific post by ID"""
        response = requests.get(
            f"{self.BASE_URL}/posts/{post_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_publication_contributors(self, publication_id: str) -> List[Dict[str, Any]]:
        """Get contributors for a publication"""
        response = requests.get(
            f"{self.BASE_URL}/publications/{publication_id}/contributors",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json().get("data", [])


def publish_article(file_path, title=None, tags=None, status=None, 
                  publication_id=None, notify_followers=None):
    """
    Publish an article from a file.
    
    Args:
        file_path (str): Path to the markdown file.
        title (str, optional): Title of the article. If not provided, 
                               it will be extracted from the file.
        tags (list, optional): List of tags.
        status (str, optional): Status of the post.
        publication_id (str, optional): ID of the publication.
        notify_followers (bool, optional): Whether to notify followers.
    
    Returns:
        dict: Published article information.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Article file not found: {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract title from the first line if not provided
    if not title:
        first_line = content.split('\n')[0].strip()
        if first_line.startswith('# '):
            title = first_line[2:].strip()
        else:
            title = file_path.stem.replace('-', ' ').replace('_', ' ').title()
    
    # Convert markdown to HTML
    html_content = markdown(content)
    
    # Get configuration
    config = get_config()
    
    # Create Medium client
    client = MediumAPIClient()
    
    # Use publication ID from config if not provided
    if not publication_id and "publication_id" in config["medium"]:
        publication_id = config["medium"]["publication_id"]
    
    # Publish the article
    if publication_id:
        return client.create_post(
            user_id=config["medium"]["user_id"],
            title=title,
            content=html_content,
            content_format="html",
            tags=tags,
            publish_status=status,
            publication_id=publication_id
        )
    else:
        return client.create_post(
            user_id=config["medium"]["user_id"],
            title=title,
            content=html_content,
            content_format="html",
            tags=tags,
            publish_status=status,
            license=config["medium"]["default_license"]
        )


def get_user_details():
    """
    Get details of the authenticated user.
    
    Returns:
        dict: User details.
    """
    client = MediumAPIClient()
    return client.get_current_user() 