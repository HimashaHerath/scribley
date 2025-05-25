"""
Database configuration for Scribley
"""
import os
# from sqlalchemy import create_engine # Replaced with async version
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession # Added
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Create the database directory if it doesn't exist
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

# Database URL (SQLite)
DATABASE_URL_SYNC = os.getenv("DATABASE_URL", f"sqlite:///{DB_DIR}/scribley.db")
# Modify for aiosqlite
if DATABASE_URL_SYNC.startswith("sqlite:///"):
    DATABASE_URL_ASYNC = DATABASE_URL_SYNC.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
else: # In case a different DB is used later, this might need adjustment
    DATABASE_URL_ASYNC = DATABASE_URL_SYNC # Or raise an error if not SQLite and async is intended

# Create SQLAlchemy async engine
engine = create_async_engine(
    DATABASE_URL_ASYNC,
    # connect_args={"check_same_thread": False} # check_same_thread is for sqlite sync
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true" # Optional: for debugging SQL
)

# Create an async session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    class_=AsyncSession # Use AsyncSession
)

# Create a base class for declarative models
Base = declarative_base()

async def get_db() -> AsyncSession: # Changed to async def and type hint
    """
    Get an asynchronous database session.
    
    This function creates a new async session for each request and
    closes it when the request is done.
    """
    async with SessionLocal() as session: # Use async context manager for session
        try:
            yield session
        finally:
            # The async context manager handles session closing automatically.
            # For older SQLAlchemy versions or manual management:
            # await session.close()
            pass # Session is closed by async with block 