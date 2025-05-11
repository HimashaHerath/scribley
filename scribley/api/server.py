import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_server():
    """Start the FastAPI server with Uvicorn"""
    port = int(os.getenv("API_PORT", 5000))
    uvicorn.run(
        "scribley.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )

if __name__ == "__main__":
    start_server() 