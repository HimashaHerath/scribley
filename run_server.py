#!/usr/bin/env python
"""
Simplified server script to run the FastAPI app directly.
This works around package import issues.
"""
import os
import uvicorn
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

def main():
    # Set up logging
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Starting Scribley API server...")
    print(f"Medium API token is {'set' if os.getenv('MEDIUM_API_TOKEN') else 'NOT SET'}")
    
    # Run the server directly using uvicorn
    uvicorn.run(
        "scribley.api.app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level=log_level
    )

if __name__ == "__main__":
    main() 