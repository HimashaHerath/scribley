"""
Initialize the database with tables and initial data.
"""
import logging
from .config import Base, engine
from . import models

logger = logging.getLogger(__name__)

def init_db():
    """
    Initialize the database by creating all tables.
    """
    logger.info("Creating database tables...")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")

def reset_db():
    """
    Reset the database by dropping and recreating all tables.
    Use with caution as this will delete all data!
    """
    logger.warning("Dropping all database tables...")
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped.")
    
    # Recreate tables
    init_db()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the database
    init_db() 