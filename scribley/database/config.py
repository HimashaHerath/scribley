"""
Database configuration for Scribley
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Create the database directory if it doesn't exist
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

# Database URL (SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_DIR}/scribley.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()

def get_db():
    """
    Get a database session.
    
    This function creates a new session for each request and
    closes it when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 