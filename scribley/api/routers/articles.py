from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File, BackgroundTasks
from typing import List, Optional
from sqlalchemy.orm import Session
import os
from tempfile import NamedTemporaryFile
import shutil
from datetime import datetime
import logging

from ..medium import MediumAPIClient
from ..dependencies import get_medium_client
from ..schemas import Article, ArticleCreate, ArticleUpdate, ArticlePublish
from ...database.config import get_db
from ...database import crud

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function for background task
async def _publish_article_to_medium_and_update_db(
    db: Session,
    article_id: str,
    user_id: str,
    article_title: str,
    article_content: str,
    tag_names: List[str],
    publish_status_value: str,
    publication_id_value: Optional[str],
    client: MediumAPIClient
):
    try:
        logger.info(f"Background task started for publishing article ID: {article_id} to Medium.")
        medium_post_data = await client.create_post(
            title=article_title,
            content=article_content,
            content_format="markdown",
            tags=tag_names,
            publish_status=publish_status_value,
            publication_id=publication_id_value
        )
        
        update_data = {
            "medium_id": medium_post_data.get("id"),
            "medium_url": medium_post_data.get("url"),
            "status": publish_status_value,
            "last_published_at": datetime.utcnow()
        }
        
        crud.update_article(db, article_id, update_data)
        logger.info(f"Background task finished. Article ID: {article_id} published and DB updated.")
    except Exception as e:
        logger.error(f"Error in background task for article ID {article_id}: {str(e)}", exc_info=True)
        error_update_data = {
            "status": "publish_failed",
            "medium_error_message": str(e)
        }
        try:
            crud.update_article(db, article_id, error_update_data)
        except Exception as db_error:
            logger.error(f"Failed to update article status after publish error for {article_id}: {db_error}", exc_info=True)

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
    db: Session = Depends(get_db),
    client: MediumAPIClient = Depends(get_medium_client)
):
    """Create a new article"""
    try:
        user_data_response = await client.get_current_user()
        user_medium_id = user_data_response.get("id")
        
        if not user_medium_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user ID from Medium"
            )
        
        article_data = article.dict()
        created_article = crud.create_article(db, article_data, user_id="app_user_id_placeholder")
        return created_article
    except Exception as e:
        logger.error(f"Failed to create article: {str(e)}", exc_info=True)
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
    existing_article = crud.get_article(db, article_id)
    if not existing_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )
    
    article_data = article_update.dict(exclude_unset=True)
    updated_article = crud.update_article(db, article_id, article_data)
    return updated_article

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str,
    db: Session = Depends(get_db)
):
    """Delete an article"""
    existing_article = crud.get_article(db, article_id)
    if not existing_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )
    
    crud.delete_article(db, article_id)
    return None

@router.post("/{article_id}/publish")
async def publish_to_medium(
    article_id: str,
    background_tasks: BackgroundTasks,
    publish_data: Optional[ArticlePublish] = None,
    db: Session = Depends(get_db),
    client: MediumAPIClient = Depends(get_medium_client)
):
    """Publish an article to Medium in the background"""
    article = crud.get_article(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )
    
    try:
        user_data_response = await client.get_current_user()
        user_medium_id = user_data_response.get("id")
        
        if not user_medium_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to get authenticated user ID from Medium. Cannot publish."
            )
        
        if publish_data:
            status_value = publish_data.status
            publication_id = publish_data.publication_id
        else:
            status_value = "public"
            publication_id = None
        
        tag_names = [tag.name for tag in article.tags] if article.tags else []
        
        background_tasks.add_task(
            _publish_article_to_medium_and_update_db,
            db=db,
            article_id=article.id,
            user_id=user_medium_id,
            article_title=article.title,
            article_content=article.content,
            tag_names=tag_names,
            publish_status_value=status_value,
            publication_id_value=publication_id,
            client=client
        )
        
        try:
            crud.update_article(db, article_id, {"status": "publishing"})
        except Exception as e:
            logger.warning(f"Could not update article {article_id} status to 'publishing': {e}", exc_info=True)

        return {"message": "Article publishing process started in the background.", "article_id": article_id}

    except Exception as e:
        logger.error(f"Failed to initiate publishing for article {article_id} to Medium: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate publishing to Medium: {str(e)}"
        )

@router.post("/images/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    image: UploadFile = File(...),
    client: MediumAPIClient = Depends(get_medium_client)
):
    """
    Upload an image to Medium.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPEG, PNG, GIF, or TIFF)."
        )
    
    try:
        suffix = os.path.splitext(image.filename)[1]
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(image.file, temp_file)
            temp_path = temp_file.name
        
        with open(temp_path, "rb") as f:
            image_data = f.read()

        result = await client.upload_image(
            image_data=image_data,
            filename=image.filename,
            content_type=image.content_type
        )
        
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        return result
    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        logger.error(f"Failed to upload image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        ) 