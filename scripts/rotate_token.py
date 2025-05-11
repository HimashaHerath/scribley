#!/usr/bin/env python3
"""
Token Rotation Utility for Scribley
-----------------------------------
This script helps with securely rotating Medium API tokens:
1. Updates the .env file with a new token
2. Tests the new token for validity
3. Creates a backup of previous tokens
"""

import os
import sys
import re
import datetime
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv, set_key

# Constants
ENV_FILE = Path(".env")
BACKUP_DIR = Path("tokens/backups")
TOKEN_HISTORY_FILE = BACKUP_DIR / "token_history.log"
MEDIUM_API_URL = "https://api.medium.com/v1/me"

def validate_token(token):
    """Validate a Medium API token by making a test request"""
    if not token:
        return False, "Token cannot be empty"
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(MEDIUM_API_URL, headers=headers)
        if response.status_code == 200:
            return True, "Token is valid"
        return False, f"Invalid token: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Error validating token: {str(e)}"

def backup_current_token():
    """Create a backup of the current token"""
    # Create backup directory if it doesn't exist
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load current env file
    load_dotenv(ENV_FILE)
    current_token = os.getenv("MEDIUM_API_TOKEN")
    
    if not current_token:
        return False, "No token found to backup"
    
    # Create timestamp for the backup
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Log to token history
    with open(TOKEN_HISTORY_FILE, "a+") as f:
        f.write(f"{timestamp}: Token rotated - {current_token[:5]}...{current_token[-5:] if len(current_token) > 10 else ''}\n")
    
    return True, f"Current token backed up at {timestamp}"

def update_token(new_token):
    """Update the .env file with the new token"""
    if not ENV_FILE.exists():
        # Create from template if doesn't exist
        with open("env.example", "r") as template:
            with open(ENV_FILE, "w") as env_file:
                for line in template:
                    if line.startswith("MEDIUM_API_TOKEN="):
                        env_file.write(f"MEDIUM_API_TOKEN={new_token}\n")
                    else:
                        env_file.write(line)
        return True, "Created new .env file with token"
    
    # If file exists, update the token
    try:
        set_key(ENV_FILE, "MEDIUM_API_TOKEN", new_token)
        return True, "Token updated successfully"
    except Exception as e:
        return False, f"Error updating token: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Rotate Medium API token securely")
    parser.add_argument("--token", "-t", help="New Medium API token to use")
    parser.add_argument("--validate-only", "-v", action="store_true", help="Validate current token without rotation")
    args = parser.parse_args()
    
    if args.validate_only:
        load_dotenv(ENV_FILE)
        current_token = os.getenv("MEDIUM_API_TOKEN")
        valid, message = validate_token(current_token)
        status = "✅" if valid else "❌"
        print(f"{status} Current token: {message}")
        return 0 if valid else 1
    
    if not args.token:
        print("Please provide a new token with --token or -t option")
        print("Example: python scripts/rotate_token.py -t your-new-token")
        return 1
    
    # Validate the new token first
    valid, message = validate_token(args.token)
    if not valid:
        print(f"❌ {message}")
        return 1
    
    # Backup current token
    backup_success, backup_message = backup_current_token()
    if backup_success:
        print(f"✅ {backup_message}")
    else:
        print(f"⚠️ {backup_message}")
    
    # Update with new token
    success, message = update_token(args.token)
    if success:
        print(f"✅ {message}")
        print("✅ New token validated and installed successfully")
        return 0
    else:
        print(f"❌ {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 