from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File
from typing import List, Optional
from sqlalchemy.orm import Session
import os
from tempfile import NamedTemporaryFile
import shutil
from datetime import datetime

from ..medium import MediumAPIClient, upload_image_to_medium
from ..schemas import Article, ArticleCreate, ArticleUpdate, ArticlePublish
from ...database.config import get_db
from ...database import crud

router = APIRouter()

@router.get("/", response_model=List[Article])
async def get_articles(
    status: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all articles"""
    try:
        articles = crud.get_articles(db, skip=offset, limit=limit, status=status, tag=tag)
        return articles
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get articles: {str(e)}"
        )

@router.post("/", response_model=Article, status_code=status.HTTP_201_CREATED)
async def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db)
):
    """Create a new article"""
    try:
        # Get current user
        client = MediumAPIClient()
        user_data = client.get_current_user()
        user_id = user_data.get("data", {}).get("id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user ID"
            )
        
        # Create the article
        article_data = article.dict()
        article = crud.create_article(db, article_data, user_id=user_id)
        return article
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create article: {str(e)}"
        )

@router.get("/{article_id}", response_model=Article)
async def get_article(
    article_id: str,
    db: Session = Depends(get_db)
):
    """Get an article by ID"""
    article = crud.get_article(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )
    return article

@router.put("/{article_id}", response_model=Article)
async def update_article(
    article_id: str,
    article_update: ArticleUpdate,
    db: Session = Depends(get_db)
):
    """Update an article"""
    # Check if article exists
    existing_article = crud.get_article(db, article_id)
    if not existing_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )
    
    # Update the article
    article_data = article_update.dict(exclude_unset=True)
    updated_article = crud.update_article(db, article_id, article_data)
    return updated_article

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str,
    db: Session = Depends(get_db)
):
    """Delete an article"""
    # Check if article exists
    existing_article = crud.get_article(db, article_id)
    if not existing_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )
    
    # Delete the article
    crud.delete_article(db, article_id)
    return None

@router.post("/{article_id}/publish", response_model=Article)
async def publish_to_medium(
    article_id: str,
    publish_data: Optional[ArticlePublish] = None,
    db: Session = Depends(get_db)
):
    """Publish an article to Medium"""
    # Check if article exists
    article = crud.get_article(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )
    
    # Initialize Medium client
    try:
        client = MediumAPIClient()
        user_data = client.get_current_user()
        user_id = user_data.get("data", {}).get("id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user ID"
            )
        
        # Extract publish data
        if publish_data:
            status_value = publish_data.status
            publication_id = publish_data.publication_id
        else:
            status_value = "public"
            publication_id = None
        
        # Get tag names for Medium API
        tag_names = [tag.name for tag in article.tags] if article.tags else []
        
        # Create the post on Medium
        medium_post = client.create_post(
            user_id=user_id,
            title=article.title,
            content=article.content,
            content_format="markdown",
            tags=tag_names,
            publish_status=status_value,
            publication_id=publication_id
        )
        
        # Update the article with Medium data
        medium_data = medium_post.get("data", {})
        update_data = {
            "medium_id": medium_data.get("id"),
            "medium_url": medium_data.get("url"),
            "status": status_value
        }
        
        # Update the article in the database
        updated_article = crud.update_article(db, article_id, update_data)
        return updated_article
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish to Medium: {str(e)}"
        )

@router.post("/images/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(image: UploadFile = File(...)):
    """
    Upload an image to Medium.
    """
    # Validate file type
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPEG, PNG, GIF, or TIFF)."
        )
    
    # Save file to temporary location
    try:
        suffix = os.path.splitext(image.filename)[1]
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(image.file, temp_file)
            temp_path = temp_file.name
        
        # Upload the image to Medium
        result = upload_image_to_medium(temp_path)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return result
    except Exception as e:
        # Clean up if there's an error
        if 'temp_path' in locals():
            os.unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        ) 