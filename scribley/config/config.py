"""
Configuration management for Scribley.
"""

import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

CONFIG_DIR = Path.home() / ".scribley"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "medium": {
        "api_token": os.getenv("MEDIUM_API_TOKEN", ""),
        "publication_id": os.getenv("MEDIUM_PUBLICATION_ID", ""),
        "default_status": "draft",  # Options: draft, public, unlisted
        "default_license": "all-rights-reserved",
        "notify_followers": False,
        "content_format": "html",   # Options: html, markdown
        "canonical_url": "",        # Default canonical URL if cross-posting
        "tags": []                  # Default tags for all articles
    },
    "paths": {
        "articles_dir": "articles",
        "templates_dir": "templates"
    },
    "scheduling": {
        "enabled": False,
        "check_interval_minutes": 15,
        "preferred_time": "09:00",  # Preferred time of day for posts
        "max_posts_per_day": 1      # Limit posts per day
    },
    "user_info": {
        "name": "",
        "username": "",
        "url": ""
    }
}


def initialize_config():
    """
    Initialize the configuration directory and file if it doesn't exist.
    """
    # Create config directory if it doesn't exist
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True)
    
    # Create default config file if it doesn't exist
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        print(f"Created default configuration at {CONFIG_FILE}")
    
    return get_config()


def get_config():
    """
    Get the current configuration.
    
    Returns:
        dict: The configuration dictionary.
    """
    if not CONFIG_FILE.exists():
        return initialize_config()
    
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update with any environment variables
    if os.getenv("MEDIUM_API_TOKEN"):
        config["medium"]["api_token"] = os.getenv("MEDIUM_API_TOKEN")
    
    if os.getenv("MEDIUM_PUBLICATION_ID"):
        config["medium"]["publication_id"] = os.getenv("MEDIUM_PUBLICATION_ID")
    
    return config


def update_config(new_config):
    """
    Update the configuration file.
    
    Args:
        new_config (dict): The new configuration dictionary.
    """
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(new_config, f, default_flow_style=False)
    
    return get_config()


def update_user_info(user_data):
    """
    Update the user information in the configuration.
    
    Args:
        user_data (dict): User information from Medium API.
    
    Returns:
        dict: Updated configuration.
    """
    config = get_config()
    
    # Extract relevant user information
    config["user_info"] = {
        "name": user_data.get("name", ""),
        "username": user_data.get("username", ""),
        "url": user_data.get("url", "")
    }
    
    return update_config(config)


def get_config_file_path():
    """
    Get the path to the configuration file.
    
    Returns:
        Path: Path to the configuration file.
    """
    return CONFIG_FILE 