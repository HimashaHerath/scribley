from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from ..medium import MediumAPIClient
from ..schemas import Publication
from ...database.config import get_db
from ...database import crud

router = APIRouter()

@router.get("/", response_model=List[Publication])
async def get_publications(db: Session = Depends(get_db)):
    """Get all publications the user contributes to"""
    try:
        # Get user information to get user ID
        client = MediumAPIClient()
        user_data = client.get_current_user()
        user_id = user_data.get("data", {}).get("id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user ID"
            )
        
        # First, check the database for cached publications
        db_publications = crud.get_publications(db)
        
        # If we already have publications, return them
        if db_publications:
            return db_publications
        
        # Otherwise, get user's publications from Medium API
        medium_publications = client.get_user_publications(user_id)
        
        # Store publications in the database
        for pub in medium_publications:
            publication_data = {
                "id": pub["id"],
                "name": pub["name"],
                "description": pub.get("description", ""),
                "url": pub.get("url", ""),
                "image_url": pub.get("imageUrl", "")
            }
            
            # Check if publication already exists
            db_pub = crud.get_publication(db, pub["id"])
            if not db_pub:
                crud.create_publication(db, publication_data)
            else:
                crud.update_publication(db, pub["id"], publication_data)
        
        # Fetch updated publications
        return crud.get_publications(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get publications: {str(e)}"
        )

@router.get("/{publication_id}", response_model=Publication)
async def get_publication(publication_id: str):
    """Get a specific publication by ID"""
    try:
        # Get user information to get user ID
        client = MediumAPIClient()
        user_data = client.get_current_user()
        user_id = user_data.get("data", {}).get("id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user ID"
            )
        
        # Get user's publications
        publications_data = client.get_user_publications(user_id)
        
        # Find the requested publication
        for pub in publications_data:
            if pub.get("id") == publication_id:
                return Publication(
                    id=pub.get("id", ""),
                    name=pub.get("name", ""),
                    description=pub.get("description", ""),
                    url=pub.get("url", ""),
                    image_url=pub.get("imageUrl", "")
                )
        
        # If we get here, publication wasn't found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publication with ID {publication_id} not found"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get publication: {str(e)}"
        )

@router.get("/{publication_id}/contributors")
async def get_publication_contributors(publication_id: str):
    """Get contributors for a publication"""
    try:
        client = MediumAPIClient()
        contributors = client.get_publication_contributors(publication_id)
        return contributors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get publication contributors: {str(e)}"
        ) 