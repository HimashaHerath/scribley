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
            # Log an error before raising, so it's clear if the token was missing vs. invalid
            logger.error("MediumAPIClient: MEDIUM_API_TOKEN is not set or empty.")
            raise ValueError("Medium API token is required")
        
        # Log partial token for debugging
        token_display = f"{self.token[:5]}...{self.token[-4:]}" if len(self.token) > 9 else self.token
        logger.info(f"MediumAPIClient initialized with token: {token_display}")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get the current user's information"""
        url = f"{self.BASE_URL}/me"
        logger.info(f"Attempting to get current user from Medium API: {url}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers
            )
            response.raise_for_status()  # This will raise an HTTPError for 4xx/5xx responses
            logger.info(f"Successfully fetched user data from /me. Status: {response.status_code}")
            return response.json()
        except requests.exceptions.HTTPError as e:
            token_display = f"{self.token[:5]}...{self.token[-4:]}" if len(self.token) > 9 else self.token
            logger.error(f"HTTPError when calling Medium API /me. Status: {e.response.status_code}. URL: {url}")
            logger.error(f"Response content: {e.response.text}")
            logger.error(f"Token used (partial): {token_display}")
            # Re-raise the exception to be handled by the caller, ensuring the original error isn't masked
            # This allows the FastAPI endpoint to return the correct HTTP status and detail.
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException when calling Medium API /me: {str(e)}. URL: {url}")
            raise # Re-raise to be handled by caller
        except Exception as e:
            logger.error(f"Unexpected error in get_current_user: {str(e)}. URL: {url}", exc_info=True)
            raise # Re-raise to be handled by caller
    
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
    
    def upload_image(self, image_data: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """
        Upload an image to Medium.
        
        Args:
            image_data (bytes): The binary data of the image.
            filename (str): The filename of the image.
            content_type (str): The MIME type of the image (e.g., 'image/jpeg', 'image/png', etc.).
        
        Returns:
            Dict[str, Any]: The uploaded image information containing 'url' and 'md5'.
        
        Raises:
            requests.exceptions.HTTPError: If the request fails.
        """
        # Create a multipart form-data request with image data
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Accept-Charset": "utf-8"
        }
        
        files = {
            'image': (filename, image_data, content_type)
        }
        
        response = requests.post(
            f"{self.BASE_URL}/images",
            headers=headers,
            files=files
        )
        
        response.raise_for_status()
        return response.json().get("data", {})


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


def upload_image_to_medium(image_path: str) -> Dict[str, Any]:
    """
    Upload an image to Medium from a file path.
    
    Args:
        image_path (str): Path to the image file.
    
    Returns:
        dict: The image data with URL and MD5 hash.
    """
    # Get file details
    import os
    import mimetypes
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Get the file's content type
    content_type, _ = mimetypes.guess_type(image_path)
    if not content_type or not content_type.startswith('image/'):
        raise ValueError(f"File is not a recognized image format: {image_path}")
    
    # Read the file data
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Upload to Medium
    client = MediumAPIClient()
    filename = os.path.basename(image_path)
    
    return client.upload_image(image_data, filename, content_type) 