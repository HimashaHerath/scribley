from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, timedelta
import logging
from fastapi import Request
import time
from starlette.middleware.base import BaseHTTPMiddleware

from .routers import articles, publications, users, llm
from ..database.init_db import init_db
from scribley.api.database import get_db, engine, Base
from scribley.api.medium import MediumAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Scribley API",
    description="API for Medium automation",
    version="0.1.0",
)

# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app, 
        max_requests: int = 100, 
        window_seconds: int = 900,  # 15 minutes default
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.exclude_paths = exclude_paths or ["/", "/api/health"]
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        path = request.url.path
        
        # Skip rate limiting for excluded paths
        if path in self.exclude_paths:
            return await call_next(request)

        # Clean up old requests
        current_time = time.time()
        self._cleanup_old_requests(current_time)

        # Check if client is rate limited
        if self._is_rate_limited(client_ip, current_time):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return HTMLResponse(
                status_code=429,
                content="Too many requests. Please try again later."
            )

        # Add request to tracking
        self._add_request(client_ip, current_time)
        
        # Process the request
        return await call_next(request)

    def _cleanup_old_requests(self, current_time):
        cutoff = current_time - self.window_seconds
        for ip in list(self.requests.keys()):
            self.requests[ip] = [ts for ts in self.requests[ip] if ts > cutoff]
            if not self.requests[ip]:
                del self.requests[ip]

    def _is_rate_limited(self, client_ip, current_time):
        if client_ip not in self.requests:
            return False
        
        # Count requests in the current window
        cutoff = current_time - self.window_seconds
        count = len([ts for ts in self.requests[client_ip] if ts > cutoff])
        return count >= self.max_requests

    def _add_request(self, client_ip, current_time):
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)

# Get environment variables
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Rate limiting settings
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "100"))
RATE_LIMIT_WINDOW = os.getenv("RATE_LIMIT_WINDOW", "15m")
# Parse window time (e.g., 15m, 1h)
if RATE_LIMIT_WINDOW.endswith('m'):
    rate_limit_seconds = int(RATE_LIMIT_WINDOW[:-1]) * 60
elif RATE_LIMIT_WINDOW.endswith('h'):
    rate_limit_seconds = int(RATE_LIMIT_WINDOW[:-1]) * 3600
else:
    rate_limit_seconds = 900  # Default 15 minutes

# Configure CORS with more secure settings
allowed_origins = os.getenv("CORS_ORIGINS", FRONTEND_URL).split(",")
allowed_methods = ["GET", "POST", "PUT", "DELETE"] if not DEBUG else ["*"]
allowed_headers = ["Authorization", "Content-Type"] if not DEBUG else ["*"]

logger.info(f"CORS origins configured: {allowed_origins}")

# Add middleware
from starlette.responses import HTMLResponse

# Add middleware for rate limiting if not in debug mode
if not DEBUG:
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=RATE_LIMIT_MAX,
        window_seconds=rate_limit_seconds
    )
    logger.info(f"Rate limiting enabled: {RATE_LIMIT_MAX} requests per {RATE_LIMIT_WINDOW}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=allowed_methods,
    allow_headers=allowed_headers,
    expose_headers=["Content-Type", "X-Total-Count"] if not DEBUG else ["*"],
    max_age=86400  # 24 hours cache for preflight requests
)

# Initialize API settings
@app.on_event("startup")
async def startup_event():
    """Initialize API settings and database"""
    # Check if Medium API token is set
    medium_token = os.getenv("MEDIUM_API_TOKEN")
    if not medium_token:
        logger.warning("MEDIUM_API_TOKEN environment variable not set. API functionality will be limited.")
        logger.warning("Please set your Medium API token to enable full functionality.")
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization complete.")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "API is running", "service": "Scribley"}

# Add a health endpoint that doesn't count against rate limits
@app.get("/api/health")
async def health_check():
    """Health check endpoint that doesn't count against rate limits"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Include routers from other modules
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])
app.include_router(publications.router, prefix="/api/publications", tags=["Publications"])
app.include_router(llm.router, prefix="/api/llm", tags=["LLM"]) 