#!/usr/bin/env python
"""
Sets up the Medium API token in the .env file.
"""
import os
from pathlib import Path

def setup_token():
    token = "2f99427ba36c6091121716bdf73b4cb90ae8e2802aa7182bd8a43bfa60d04de90"
    env_path = Path(".env")
    
    if env_path.exists():
        # Read existing content
        with open(env_path, 'r') as f:
            content = f.read()
        
        if "MEDIUM_API_TOKEN" in content:
            # Update existing token
            lines = content.splitlines()
            updated_lines = []
            for line in lines:
                if line.startswith("MEDIUM_API_TOKEN="):
                    updated_lines.append(f"MEDIUM_API_TOKEN={token}")
                else:
                    updated_lines.append(line)
            updated_content = "\n".join(updated_lines)
            
            with open(env_path, 'w') as f:
                f.write(updated_content)
            print("✅ Updated existing MEDIUM_API_TOKEN in .env file")
        else:
            # Append token to existing file
            with open(env_path, 'a') as f:
                f.write(f"\nMEDIUM_API_TOKEN={token}\n")
            print("✅ Added MEDIUM_API_TOKEN to existing .env file")
    else:
        # Create new .env file
        with open(env_path, 'w') as f:
            f.write(f"MEDIUM_API_TOKEN={token}\n")
        print("✅ Created new .env file with MEDIUM_API_TOKEN")
    
    print("\n⚠️ IMPORTANT: Keep your .env file secure and never commit it to version control")
    print("   It has been added to your .gitignore file to prevent accidental commits")
    
    # Add to .gitignore if it exists
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        if ".env" not in content:
            with open(gitignore_path, 'a') as f:
                f.write("\n# Environment variables\n.env\n")
            print("✅ Added .env to .gitignore file")

if __name__ == "__main__":
    setup_token()
    print("\nNext steps:")
    print("1. Run 'python test_backend.py' to test your connection to Medium's API")
    print("2. Restart your FastAPI server: python scribley_api.py")
    print("3. Try your frontend application again") 