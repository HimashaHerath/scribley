"""
CRUD operations for Scribley models
"""
# from sqlalchemy.orm import Session # Replaced by AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession # Added
from sqlalchemy import select # Added
from typing import List, Optional, Dict, Any
from datetime import datetime

from . import models

# User operations
async def get_user(db: AsyncSession, user_id: str):
    """Get a user by ID"""
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str):
    """Get a user by username"""
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data: Dict[str, Any]):
    """Create a new user"""
    db_user = models.User(
        id=user_data["id"],
        username=user_data["username"],
        name=user_data["name"],
        url=user_data["url"],
        image_url=user_data.get("image_url")
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: str, user_data: Dict[str, Any]):
    """Update a user"""
    user = await get_user(db, user_id)
    if not user:
        return None
    
    for key, value in user_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    return user

# Publication operations
async def get_publication(db: AsyncSession, publication_id: str):
    """Get a publication by ID"""
    result = await db.execute(select(models.Publication).filter(models.Publication.id == publication_id))
    return result.scalar_one_or_none()

async def get_publications(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all publications"""
    result = await db.execute(select(models.Publication).offset(skip).limit(limit))
    return result.scalars().all()

async def create_publication(db: AsyncSession, publication_data: Dict[str, Any]):
    """Create a new publication"""
    db_publication = models.Publication(
        id=publication_data["id"],
        name=publication_data["name"],
        description=publication_data.get("description"),
        url=publication_data.get("url"),
        image_url=publication_data.get("image_url")
    )
    db.add(db_publication)
    await db.commit()
    await db.refresh(db_publication)
    return db_publication

async def update_publication(db: AsyncSession, publication_id: str, publication_data: Dict[str, Any]):
    """Update a publication"""
    publication = await get_publication(db, publication_id)
    if not publication:
        return None
    
    for key, value in publication_data.items():
        if hasattr(publication, key):
            setattr(publication, key, value)
    
    await db.commit()
    await db.refresh(publication)
    return publication

# Tag operations
async def get_tag(db: AsyncSession, tag_id: str):
    """Get a tag by ID"""
    result = await db.execute(select(models.Tag).filter(models.Tag.id == tag_id))
    return result.scalar_one_or_none()

async def get_tag_by_name(db: AsyncSession, name: str):
    """Get a tag by name"""
    result = await db.execute(select(models.Tag).filter(models.Tag.name == name))
    return result.scalar_one_or_none()

async def get_or_create_tag(db: AsyncSession, name: str):
    """Get a tag by name or create it if it doesn't exist"""
    tag = await get_tag_by_name(db, name)
    if tag:
        return tag
    
    tag = models.Tag(name=name)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag

# Article operations
async def get_article(db: AsyncSession, article_id: str):
    """Get an article by ID"""
    # Eagerly load tags to avoid separate queries later if possible with async
    # This requires relationship configuration in models.py (e.g., lazy='selectin')
    # For now, keeping it simple. If performance is an issue, review relationship loading.
    result = await db.execute(
        select(models.Article)
        .options(models.selectinload(models.Article.tags)) # Example of eager loading
        .filter(models.Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if article:
        # Accessing article.tags here should be fine if selectinload worked
        article._tag_names = [tag.name for tag in article.tags]
    return article

async def get_articles(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Get articles with filtering options"""
    stmt = select(models.Article).options(models.selectinload(models.Article.tags))
    
    # Apply filters
    if status:
        stmt = stmt.filter(models.Article.status == status)
    
    if tag:
        # This subquery for tag might need adjustment for async or could be less efficient.
        # Consider alternative ways to filter by tag name if performance is critical.
        tag_obj = await get_tag_by_name(db, tag)
        if tag_obj:
            # Filtering by relationship containment
            stmt = stmt.filter(models.Article.tags.contains(tag_obj))
    
    if user_id:
        stmt = stmt.filter(models.Article.user_id == user_id)
    
    # Order by created_at (newest first)
    stmt = stmt.order_by(models.Article.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    articles = result.scalars().all()
    
    # Convert tags to simple list of names
    for article_item in articles:
        article_item._tag_names = [tag.name for tag in article_item.tags]
        
    return articles

async def create_article(db: AsyncSession, article_data: Dict[str, Any], user_id: Optional[str] = None):
    """Create a new article"""
    db_article = models.Article(
        title=article_data["title"],
        content=article_data["content"],
        user_id=user_id,
        subtitle=article_data.get("subtitle"),
        status=article_data.get("status", models.ArticleStatus.DRAFT.value)
    )
    
    if "tags" in article_data and article_data["tags"]:
        tags_to_add = []
        for tag_name in article_data["tags"]:
            tag = await get_or_create_tag(db, tag_name) # This commits, be careful with multiple calls
            tags_to_add.append(tag)
        db_article.tags.extend(tags_to_add)
            
    if "publication_id" in article_data and article_data["publication_id"]:
        db_article.publication_id = article_data["publication_id"]
    
    db.add(db_article)
    await db.commit()
    await db.refresh(db_article)
    
    # Eager load tags after creation for _tag_names property
    # This requires re-fetching or careful state management if not using selectinload by default.
    # For simplicity, we reload the specific attribute if needed after refresh.
    # await db.refresh(db_article, attribute_names=['tags']) # If tags are not loaded by default after refresh
    db_article._tag_names = [tag.name for tag in db_article.tags]
    
    return db_article

async def update_article(db: AsyncSession, article_id: str, article_data: Dict[str, Any]):
    """Update an article"""
    article = await get_article(db, article_id) # get_article now eager loads tags
    if not article:
        return None
    
    for key in ["title", "subtitle", "content", "status", "publication_id", "medium_id", "medium_url", "medium_error_message", "last_published_at"]:
        if key in article_data:
            setattr(article, key, article_data[key])
    
    if "status" in article_data and article_data["status"] in ["public", "unlisted"] and not article.published_at:
        # This logic might need refinement if last_published_at is also in article_data
        if "last_published_at" not in article_data: 
             article.published_at = datetime.utcnow()
    
    if "tags" in article_data:
        article.tags.clear() # Clear existing tags
        tags_to_add = []
        for tag_name in article_data["tags"]:
            tag = await get_or_create_tag(db, tag_name) # This commits
            tags_to_add.append(tag)
        article.tags.extend(tags_to_add)
    
    await db.commit()
    await db.refresh(article)
    # await db.refresh(article, attribute_names=['tags']) # Refresh tags if necessary
    article._tag_names = [tag.name for tag in article.tags]
    
    return article

async def delete_article(db: AsyncSession, article_id: str):
    """Delete an article"""
    article = await get_article(db, article_id)
    if not article:
        return False # Or raise an exception
    
    await db.delete(article) # Use await for delete
    await db.commit()
    return True 