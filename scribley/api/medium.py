"""
Medium API client implementation.
"""

import asyncio
import httpx
import json
import logging
from pathlib import Path
from markdown import markdown
import os
import time
from typing import Dict, Any, Optional, List, Callable, Coroutine
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
                "tags": [],
                # Add rate limiting config
                "rate_limit": {
                    "calls_per_day": 300,     # Medium limits to ~300 calls per day
                    "calls_per_hour": 50,     # Reasonable hourly limit
                    "calls_per_minute": 10,   # Reasonable per-minute limit
                    "min_request_interval": 1  # Minimum seconds between requests
                }
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

# Cache for Medium API responses
medium_api_cache = {}
CACHE_TTL = 300  # 5 minutes cache

# Global rate limiter to prevent multiple instances from exceeding limits
class MediumRateLimiter:
    _instance = None
    _lock = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MediumRateLimiter, cls).__new__(cls)
            cls._instance._initialized = False 
        return cls._instance

    async def _init_async(self):
        if self._initialized:
            return
        self._lock = asyncio.Lock()
        self.request_history = []
        self.last_request_time = 0
        config = get_config()
        rate_limit = config.get("medium", {}).get("rate_limit", {})
        self.calls_per_day = rate_limit.get("calls_per_day", 300)
        self.calls_per_hour = rate_limit.get("calls_per_hour", 50)
        self.calls_per_minute = rate_limit.get("calls_per_minute", 10)
        self.min_request_interval = rate_limit.get("min_request_interval", 1)  # seconds
        self._initialized = True
    
    async def check_rate_limit(self) -> bool:
        """Check if rate limit allows another request"""
        async with self._lock:
            current_time = time.time()
            
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.min_request_interval:
                logger.warning(f"Rate limit: Minimum interval not met. Need to wait {self.min_request_interval - time_since_last_request:.2f} more seconds")
                return False
            
            day_ago = current_time - 86400  # 24 hours in seconds
            self.request_history = [ts for ts in self.request_history if ts > day_ago]
            
            if len(self.request_history) >= self.calls_per_day:
                logger.warning(f"Rate limit: Daily limit of {self.calls_per_day} requests reached")
                return False
            
            hour_ago = current_time - 3600
            hourly_requests = len([ts for ts in self.request_history if ts > hour_ago])
            if hourly_requests >= self.calls_per_hour:
                logger.warning(f"Rate limit: Hourly limit of {self.calls_per_hour} requests reached")
                return False
            
            minute_ago = current_time - 60
            minute_requests = len([ts for ts in self.request_history if ts > minute_ago])
            if minute_requests >= self.calls_per_minute:
                logger.warning(f"Rate limit: Per-minute limit of {self.calls_per_minute} requests reached")
                return False
            
            return True
    
    async def record_request(self):
        """Record that a request was made"""
        async with self._lock:
            current_time = time.time()
            self.request_history.append(current_time)
            self.last_request_time = current_time
    
    async def wait_for_rate_limit(self):
        """Wait until rate limit allows the request"""
        await self._init_async()
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            if await self.check_rate_limit():
                return True
            
            async with self._lock:
                current_time = time.time()
                time_since_last_request = current_time - self.last_request_time
                if time_since_last_request < self.min_request_interval:
                    wait_time = self.min_request_interval - time_since_last_request + 0.1
                else:
                    minute_ago = current_time - 60
                    minute_requests = [ts for ts in self.request_history if ts > minute_ago]
                    if len(minute_requests) >= self.calls_per_minute and minute_requests:
                        wait_time = (minute_requests[0] + 60) - current_time + 0.1
                    else:
                        wait_time = 5
            
            logger.info(f"Rate limit: Waiting {wait_time:.2f} seconds before retry")
            await asyncio.sleep(wait_time)
            retry_count += 1
        
        logger.error("Rate limit: Max retries exceeded")
        return False

# Function to use as a decorator for API methods that need rate limiting
def rate_limited(func: Callable[..., Coroutine[Any, Any, Any]]):
    """Decorator for rate-limited API calls"""
    async def wrapper(*args, **kwargs):
        client_instance = args[0] if args else None
        rate_limiter = MediumRateLimiter()
        await rate_limiter._init_async()

        cache_key = None
        if func.__name__ in ['get_current_user', 'get_user_publications', 'get_post', 'get_publication_contributors']:
            cache_key = f"{func.__name__}:{str(args[1:])}:{str(kwargs)}"
            if cache_key in medium_api_cache:
                cache_entry = medium_api_cache[cache_key]
                if time.time() - cache_entry['timestamp'] < CACHE_TTL:
                    logger.info(f"Using cached response for {func.__name__}")
                    return cache_entry['data']
        
        if not await rate_limiter.wait_for_rate_limit():
            raise Exception(f"Rate limit exceeded for Medium API: {func.__name__}")
        
        try:
            if client_instance and hasattr(client_instance, 'async_client'):
                result = await func(*args, **kwargs)
            else:
                result = await func(*args, **kwargs)

            await rate_limiter.record_request()
            
            if cache_key:
                medium_api_cache[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }
            
            return result
        except Exception as e:
            logger.error(f"Error in rate-limited API call {func.__name__}: {str(e)}")
            raise
    
    return wrapper

class MediumAPIClient:
    """Client for interacting with the Medium API"""
    
    BASE_URL = "https://api.medium.com/v1"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("MEDIUM_API_TOKEN")
        if not self.token:
            logger.error("MediumAPIClient: MEDIUM_API_TOKEN is not set or empty.")
            raise ValueError("Medium API token is required")
        
        token_display = f"{self.token[:5]}...{self.token[-4:]}" if len(self.token) > 9 else self.token
        logger.info(f"MediumAPIClient initialized with token: {token_display}")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "User-Agent": "Scribley Bot/1.0"
        }
        self._async_client: Optional[httpx.AsyncClient] = None

    async def get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
        return self._async_client

    async def close_async_client(self):
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    @rate_limited
    async def get_current_user(self) -> Dict[str, Any]:
        """Get the current user's information"""
        url = f"{self.BASE_URL}/me"
        logger.info(f"Attempting to get current user from Medium API: {url}")
        async_client = await self.get_async_client()
        
        try:
            response = await async_client.get(url)
            response.raise_for_status()
            logger.info(f"Successfully fetched user data from /me. Status: {response.status_code}")
            return response.json()
        except httpx.HTTPStatusError as e:
            token_display = f"{self.token[:5]}...{self.token[-4:]}" if len(self.token) > 9 else self.token
            logger.error(f"HTTPStatusError when calling Medium API /me. Status: {e.response.status_code}. URL: {url}")
            logger.error(f"Response content: {e.response.text}")
            logger.error(f"Token used (partial): {token_display}")
            raise
        except httpx.RequestError as e:
            logger.error(f"RequestError when calling Medium API /me: {str(e)}. URL: {e.request.url}")
            raise

    @rate_limited
    async def get_user_publications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get publications that the user is a contributor to"""
        url = f"{self.BASE_URL}/users/{user_id}/publications"
        logger.info(f"Attempting to get publications for user {user_id} from Medium API: {url}")
        async_client = await self.get_async_client()
        try:
            response = await async_client.get(url)
            response.raise_for_status()
            logger.info(f"Successfully fetched publications for user {user_id}. Status: {response.status_code}")
            return response.json().get("data", [])
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTPStatusError when calling Medium API /users/{user_id}/publications. Status: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"RequestError when calling Medium API /users/{user_id}/publications: {str(e)}")
            raise

    @rate_limited
    async def create_post(
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
        if publication_id:
            url = f"{self.BASE_URL}/publications/{publication_id}/posts"
        else:
            url = f"{self.BASE_URL}/me/posts"

        payload = {
            "title": title,
            "contentFormat": content_format,
            "content": content,
            "tags": tags[:5] if tags else None,
            "canonicalUrl": canonical_url,
            "publishStatus": publish_status,
            "license": license,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        logger.info(f"Attempting to create post on Medium. URL: {url}, Payload: {payload}")
        async_client = await self.get_async_client()
        try:
            response = await async_client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully created post. Status: {response.status_code}, Response: {response.json()}")
            return response.json().get("data", {})
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTPStatusError when creating post. Status: {e.response.status_code}, URL: {url}")
            logger.error(f"Response content: {e.response.text}")
            if e.response.status_code == 400:
                try:
                    errors = e.response.json().get('errors')
                    if errors:
                         logger.error(f"Medium API Errors: {errors}")
                except json.JSONDecodeError:
                    pass
            raise
        except httpx.RequestError as e:
            logger.error(f"RequestError when creating post: {str(e)}, URL: {e.request.url}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating post: {str(e)}")
            raise

    @rate_limited
    async def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a specific post by ID"""
        logger.warning("get_post by post_id is not a standard public Medium API V1 operation. This function is a placeholder.")
        return {"error": "Get post by ID is not directly supported in this manner by Medium API v1."}

    @rate_limited
    async def get_publication_contributors(self, publication_id: str) -> List[Dict[str, Any]]:
        """Get contributors for a publication"""
        url = f"{self.BASE_URL}/publications/{publication_id}/contributors"
        logger.info(f"Attempting to get contributors for publication {publication_id} from Medium API: {url}")
        async_client = await self.get_async_client()
        try:
            response = await async_client.get(url)
            response.raise_for_status()
            logger.info(f"Successfully fetched contributors for publication {publication_id}. Status: {response.status_code}")
            return response.json().get("data", [])
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTPStatusError when getting publication contributors. Status: {e.response.status_code}, URL: {url}")
            logger.error(f"Response content: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"RequestError when getting publication contributors: {str(e)}")
            raise

    @rate_limited
    async def upload_image(self, image_data: bytes, filename: str, content_type: str) -> Dict[str, Any]:
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
        url = f"{self.BASE_URL}/images"
        logger.info(f"Attempting to upload image '{filename}' to Medium API. Content-Type: {content_type}")
        
        files = {'image': (filename, image_data, content_type)}
        
        custom_headers = self.headers.copy()
        if 'Content-Type' in custom_headers:
            del custom_headers['Content-Type']

        async_client = await self.get_async_client()
        try:
            response = await async_client.post(url, files=files, headers=custom_headers)
            response.raise_for_status()
            logger.info(f"Successfully uploaded image '{filename}'. Status: {response.status_code}")
            return response.json().get("data", {})
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTPStatusError when uploading image '{filename}'. Status: {e.response.status_code}, URL: {url}")
            logger.error(f"Response content: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"RequestError when uploading image '{filename}': {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading image '{filename}': {str(e)}")
            raise

async def publish_article(file_path, title=None, tags=None, status=None, 
                  publication_id=None, notify_followers=None, client: MediumAPIClient = None):
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
    if client is None:
        temp_client = MediumAPIClient()
    else:
        temp_client = client

    try:
        article_path = Path(file_path)
        if not article_path.exists():
            logger.error(f"Article file not found: {file_path}")
            raise FileNotFoundError(f"Article file not found: {file_path}")

        with open(article_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        
        html_content = markdown(markdown_content)

        default_config = get_config().get("medium", {})
        
        user_info = await temp_client.get_current_user()
        author_id = user_info.get("data", {}).get("id")
        if not author_id:
            logger.error("Could not retrieve author ID from Medium.")
            raise Exception("Could not retrieve author ID.")

        post_title = title or article_path.stem.replace('_', ' ').replace('-', ' ').title()
        post_tags = tags or default_config.get("tags", [])
        publish_status = status or default_config.get("default_status", "draft")

        logger.info(f"Preparing to publish article: '{post_title}'")
        logger.info(f"  Author ID: {author_id}")
        logger.info(f"  Status: {publish_status}")
        logger.info(f"  Tags: {post_tags}")
        if publication_id:
            logger.info(f"  Publication ID: {publication_id}")

        created_post = await temp_client.create_post(
            user_id=author_id,
            title=post_title,
            content=html_content,
            content_format="html",
            tags=post_tags,
            publish_status=publish_status,
            publication_id=publication_id
        )
        
        logger.info(f"Article '{post_title}' published successfully to Medium.")
        logger.info(f"Post details: {created_post}")
        return created_post
    except Exception as e:
        logger.error(f"Failed to publish article '{file_path}': {e}")
        raise
    finally:
        if client is None and temp_client:
             await temp_client.close_async_client()

async def get_user_details(client: MediumAPIClient = None):
    """
    Get details of the authenticated user.
    
    Returns:
        dict: User details.
    """
    if client is None:
        temp_client = MediumAPIClient()
    else:
        temp_client = client
    try:
        user_data = await temp_client.get_current_user()
        logger.info(f"Fetched user details: {user_data.get('data')}")
        return user_data.get("data")
    except Exception as e:
        logger.error(f"Failed to get user details: {e}")
        raise
    finally:
        if client is None and temp_client:
            await temp_client.close_async_client()

async def upload_image_to_medium(image_path: str, client: MediumAPIClient = None) -> Dict[str, Any]:
    """
    Upload an image to Medium from a file path.
    
    Args:
        image_path (str): Path to the image file.
    
    Returns:
        dict: The image data with URL and MD5 hash.
    """
    path = Path(image_path)
    if not path.exists():
        logger.error(f"Image file not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    filename = path.name
    content_type = f'image/{path.suffix.lower().strip(".")}'
    if content_type == 'image/jpg': content_type = 'image/jpeg'

    if client is None:
        temp_client = MediumAPIClient()
    else:
        temp_client = client
        
    try:
        with open(path, "rb") as f:
            image_data = f.read()
        
        upload_result = await temp_client.upload_image(
            image_data=image_data, 
            filename=filename, 
            content_type=content_type
        )
        logger.info(f"Image '{filename}' uploaded successfully. URL: {upload_result.get('url')}")
        return upload_result
    except Exception as e:
        logger.error(f"Failed to upload image '{image_path}': {e}")
        raise
    finally:
        if client is None and temp_client:
            await temp_client.close_async_client() 