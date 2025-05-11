"""
CRUD operations for Scribley models
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from . import models

# User operations
def get_user(db: Session, user_id: str):
    """Get a user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    """Get a user by username"""
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user_data: Dict[str, Any]):
    """Create a new user"""
    db_user = models.User(
        id=user_data["id"],
        username=user_data["username"],
        name=user_data["name"],
        url=user_data["url"],
        image_url=user_data.get("image_url")
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: str, user_data: Dict[str, Any]):
    """Update a user"""
    user = get_user(db, user_id)
    if not user:
        return None
    
    for key, value in user_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

# Publication operations
def get_publication(db: Session, publication_id: str):
    """Get a publication by ID"""
    return db.query(models.Publication).filter(models.Publication.id == publication_id).first()

def get_publications(db: Session, skip: int = 0, limit: int = 100):
    """Get all publications"""
    return db.query(models.Publication).offset(skip).limit(limit).all()

def create_publication(db: Session, publication_data: Dict[str, Any]):
    """Create a new publication"""
    db_publication = models.Publication(
        id=publication_data["id"],
        name=publication_data["name"],
        description=publication_data.get("description"),
        url=publication_data.get("url"),
        image_url=publication_data.get("image_url")
    )
    db.add(db_publication)
    db.commit()
    db.refresh(db_publication)
    return db_publication

def update_publication(db: Session, publication_id: str, publication_data: Dict[str, Any]):
    """Update a publication"""
    publication = get_publication(db, publication_id)
    if not publication:
        return None
    
    for key, value in publication_data.items():
        if hasattr(publication, key):
            setattr(publication, key, value)
    
    db.commit()
    db.refresh(publication)
    return publication

# Tag operations
def get_tag(db: Session, tag_id: str):
    """Get a tag by ID"""
    return db.query(models.Tag).filter(models.Tag.id == tag_id).first()

def get_tag_by_name(db: Session, name: str):
    """Get a tag by name"""
    return db.query(models.Tag).filter(models.Tag.name == name).first()

def get_or_create_tag(db: Session, name: str):
    """Get a tag by name or create it if it doesn't exist"""
    tag = get_tag_by_name(db, name)
    if tag:
        return tag
    
    tag = models.Tag(name=name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

# Article operations
def get_article(db: Session, article_id: str):
    """Get an article by ID"""
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if article:
        article._tag_names = [tag.name for tag in article.tags]
    return article

def get_articles(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Get articles with filtering options"""
    query = db.query(models.Article)
    
    # Apply filters
    if status:
        query = query.filter(models.Article.status == status)
    
    if tag:
        tag_obj = get_tag_by_name(db, tag)
        if tag_obj:
            query = query.filter(models.Article.tags.contains(tag_obj))
    
    if user_id:
        query = query.filter(models.Article.user_id == user_id)
    
    # Order by created_at (newest first)
    query = query.order_by(models.Article.created_at.desc())
    
    articles = query.offset(skip).limit(limit).all()
    
    # Convert tags to simple list of names
    for article in articles:
        article._tag_names = [tag.name for tag in article.tags]
        
    return articles

def create_article(db: Session, article_data: Dict[str, Any], user_id: Optional[str] = None):
    """Create a new article"""
    # Create article
    db_article = models.Article(
        title=article_data["title"],
        content=article_data["content"],
        user_id=user_id,
        subtitle=article_data.get("subtitle"),
        status=article_data.get("status", models.ArticleStatus.DRAFT.value)
    )
    
    # Add tags if provided
    if "tags" in article_data and article_data["tags"]:
        for tag_name in article_data["tags"]:
            tag = get_or_create_tag(db, tag_name)
            db_article.tags.append(tag)
    
    # Set publication if provided
    if "publication_id" in article_data and article_data["publication_id"]:
        db_article.publication_id = article_data["publication_id"]
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    # Add tag names property
    db_article._tag_names = [tag.name for tag in db_article.tags]
    
    return db_article

def update_article(db: Session, article_id: str, article_data: Dict[str, Any]):
    """Update an article"""
    article = get_article(db, article_id)
    if not article:
        return None
    
    # Update simple fields
    for key in ["title", "subtitle", "content", "status", "publication_id"]:
        if key in article_data:
            setattr(article, key, article_data[key])
    
    # Update Medium-specific fields
    if "medium_id" in article_data:
        article.medium_id = article_data["medium_id"]
    
    if "medium_url" in article_data:
        article.medium_url = article_data["medium_url"]
    
    # Update published_at if status changes to published
    if "status" in article_data and article_data["status"] in ["public", "unlisted"] and not article.published_at:
        article.published_at = datetime.utcnow()
    
    # Update tags if provided
    if "tags" in article_data:
        # Clear existing tags
        article.tags = []
        
        # Add new tags
        for tag_name in article_data["tags"]:
            tag = get_or_create_tag(db, tag_name)
            article.tags.append(tag)
    
    db.commit()
    db.refresh(article)
    
    # Add tag names property
    article._tag_names = [tag.name for tag in article.tags]
    
    return article

def delete_article(db: Session, article_id: str):
    """Delete an article"""
    article = get_article(db, article_id)
    if not article:
        return False
    
    db.delete(article)
    db.commit()
    return True 