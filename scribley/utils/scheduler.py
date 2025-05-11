"""
Scheduling utility for Medium article publishing.
"""

import os
import time
import logging
import json
from datetime import datetime
from pathlib import Path
import schedule
import threading

from ..api import publish_article
from ..config import get_config

logger = logging.getLogger(__name__)

# Directory for storing scheduled posts
SCHEDULER_DIR = Path.home() / ".scribley" / "scheduled"


def _ensure_scheduler_dir():
    """
    Ensure that the scheduler directory exists.
    """
    if not SCHEDULER_DIR.exists():
        SCHEDULER_DIR.mkdir(parents=True)
        logger.debug(f"Created scheduler directory: {SCHEDULER_DIR}")


def schedule_post(file_path, publish_at, title=None, tags=None, 
                status=None, publication_id=None, notify_followers=None):
    """
    Schedule a post to be published at a specific time.
    
    Args:
        file_path (str): Path to the markdown file.
        publish_at (datetime): When to publish the article.
        title (str, optional): Title of the article.
        tags (list, optional): List of tags.
        status (str, optional): Status of the post.
        publication_id (str, optional): ID of the publication.
        notify_followers (bool, optional): Whether to notify followers.
    
    Returns:
        str: ID of the scheduled post.
    """
    # Ensure scheduler directory exists
    _ensure_scheduler_dir()
    
    # Generate a unique ID for the scheduled post
    post_id = f"post_{int(time.time())}_{os.urandom(4).hex()}"
    
    # Create the scheduled post data
    scheduled_post = {
        "id": post_id,
        "file_path": str(Path(file_path).absolute()),
        "publish_at": publish_at.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "tags": tags,
        "status": status,
        "publication_id": publication_id,
        "notify_followers": notify_followers,
        "executed": False
    }
    
    # Save the scheduled post
    post_file = SCHEDULER_DIR / f"{post_id}.json"
    with open(post_file, 'w') as f:
        json.dump(scheduled_post, f, indent=2)
    
    logger.info(f"Scheduled post {post_id} for {publish_at}")
    
    # If scheduling is enabled, start the scheduler if not already running
    config = get_config()
    if config["scheduling"]["enabled"]:
        # This won't start a new thread if already running
        ensure_scheduler_running()
    
    return post_id


def _publish_scheduled_post(post_id):
    """
    Publish a scheduled post.
    
    Args:
        post_id (str): ID of the scheduled post.
    """
    post_file = SCHEDULER_DIR / f"{post_id}.json"
    
    if not post_file.exists():
        logger.error(f"Scheduled post file not found: {post_file}")
        return
    
    try:
        # Load the scheduled post data
        with open(post_file, 'r') as f:
            post_data = json.load(f)
        
        # Skip if already executed
        if post_data.get("executed", False):
            logger.warning(f"Post {post_id} already executed")
            return
        
        # Publish the article
        result = publish_article(
            file_path=post_data["file_path"],
            title=post_data["title"],
            tags=post_data["tags"],
            status=post_data["status"],
            publication_id=post_data["publication_id"],
            notify_followers=post_data["notify_followers"]
        )
        
        # Mark as executed
        post_data["executed"] = True
        post_data["executed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        post_data["result"] = {
            "title": result.get("title"),
            "url": result.get("url"),
            "status": result.get("publishStatus")
        }
        
        # Save the updated data
        with open(post_file, 'w') as f:
            json.dump(post_data, f, indent=2)
        
        logger.info(f"Published scheduled post {post_id}: {result.get('title')}")
        
    except Exception as e:
        logger.error(f"Failed to publish scheduled post {post_id}: {e}")


def _check_scheduled_posts():
    """
    Check for scheduled posts that need to be published.
    """
    _ensure_scheduler_dir()
    
    # Get current time
    now = datetime.now()
    
    # Check all scheduled post files
    for post_file in SCHEDULER_DIR.glob("*.json"):
        try:
            # Load the scheduled post data
            with open(post_file, 'r') as f:
                post_data = json.load(f)
            
            # Skip if already executed
            if post_data.get("executed", False):
                continue
            
            # Check if it's time to publish
            publish_at = datetime.strptime(post_data["publish_at"], "%Y-%m-%d %H:%M:%S")
            if now >= publish_at:
                logger.info(f"Publishing scheduled post {post_data['id']}")
                _publish_scheduled_post(post_data["id"])
            
        except Exception as e:
            logger.error(f"Error checking scheduled post {post_file}: {e}")


def _run_scheduler():
    """
    Run the scheduler in a separate thread.
    """
    config = get_config()
    check_interval = config["scheduling"]["check_interval_minutes"]
    
    # Schedule the check to run periodically
    schedule.every(check_interval).minutes.do(_check_scheduled_posts)
    
    # Run immediately on startup
    _check_scheduled_posts()
    
    logger.info(f"Scheduler running with check interval of {check_interval} minutes")
    
    # Run the scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Sleep for 1 minute


_scheduler_thread = None


def ensure_scheduler_running():
    """
    Ensure that the scheduler is running.
    """
    global _scheduler_thread
    
    # Check if the scheduler thread is already running
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    
    # Start the scheduler thread
    _scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
    _scheduler_thread.start()
    
    logger.info("Scheduler thread started")


def get_scheduled_posts():
    """
    Get all scheduled posts.
    
    Returns:
        list: List of scheduled posts.
    """
    _ensure_scheduler_dir()
    
    posts = []
    for post_file in SCHEDULER_DIR.glob("*.json"):
        try:
            with open(post_file, 'r') as f:
                post_data = json.load(f)
            posts.append(post_data)
        except Exception as e:
            logger.error(f"Error reading scheduled post {post_file}: {e}")
    
    # Sort by publish_at
    posts.sort(key=lambda x: x["publish_at"])
    
    return posts


def delete_scheduled_post(post_id):
    """
    Delete a scheduled post.
    
    Args:
        post_id (str): ID of the scheduled post.
    
    Returns:
        bool: True if the post was deleted, False otherwise.
    """
    post_file = SCHEDULER_DIR / f"{post_id}.json"
    
    if not post_file.exists():
        logger.error(f"Scheduled post file not found: {post_id}")
        return False
    
    try:
        post_file.unlink()
        logger.info(f"Deleted scheduled post {post_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete scheduled post {post_id}: {e}")
        return False 