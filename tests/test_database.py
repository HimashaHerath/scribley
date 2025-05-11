#!/usr/bin/env python
"""
Test script for SQLite database functionality.
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add parent directory to Python path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from scribley.database.init_db import init_db, reset_db
    from scribley.database.config import SessionLocal
    from scribley.database import crud, models
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

def test_database():
    """Test database functionality"""
    logger.info("Testing database functionality...")
    
    # Initialize the database (creates tables if they don't exist)
    init_db()
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Test user operations
        logger.info("Testing user operations...")
        test_user = {
            "id": "test-user-id",
            "username": "testuser",
            "name": "Test User",
            "url": "https://medium.com/@testuser",
            "image_url": "https://example.com/avatar.jpg"
        }
        
        # Create user
        user = crud.create_user(db, test_user)
        logger.info(f"Created user: {user.username}")
        
        # Get user
        retrieved_user = crud.get_user(db, user.id)
        logger.info(f"Retrieved user: {retrieved_user.username}")
        
        # Test publication operations
        logger.info("Testing publication operations...")
        test_publication = {
            "id": "test-publication-id",
            "name": "Test Publication",
            "description": "A test publication",
            "url": "https://medium.com/test-publication",
            "image_url": "https://example.com/publication.jpg"
        }
        
        # Create publication
        publication = crud.create_publication(db, test_publication)
        logger.info(f"Created publication: {publication.name}")
        
        # Get publications
        publications = crud.get_publications(db)
        logger.info(f"Retrieved {len(publications)} publications")
        
        # Test article operations
        logger.info("Testing article operations...")
        test_article = {
            "title": "Test Article",
            "subtitle": "A test article",
            "content": "This is a test article content.",
            "tags": ["test", "example", "sqlite"],
            "status": "draft"
        }
        
        # Create article
        article = crud.create_article(db, test_article, user_id=user.id)
        logger.info(f"Created article: {article.title}")
        
        # Get article
        retrieved_article = crud.get_article(db, article.id)
        logger.info(f"Retrieved article: {retrieved_article.title}")
        
        # Get articles
        articles = crud.get_articles(db)
        logger.info(f"Retrieved {len(articles)} articles")
        
        # Update article
        update_data = {
            "title": "Updated Test Article",
            "status": "public"
        }
        updated_article = crud.update_article(db, article.id, update_data)
        logger.info(f"Updated article: {updated_article.title}")
        
        logger.info("All database operations completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Error during database test: {e}")
        return False
    finally:
        db.close()

def reset_database():
    """Reset the database (for testing purposes)"""
    logger.warning("Resetting database...")
    reset_db()
    logger.warning("Database reset complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    
    success = test_database()
    sys.exit(0 if success else 1) 