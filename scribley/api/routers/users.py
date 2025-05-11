from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from ..medium import MediumAPIClient
from ..schemas import User
from ...database.config import get_db
from ...database import crud

router = APIRouter()

@router.get("/me", response_model=User)
async def get_current_user(db: Session = Depends(get_db)):
    """Get the current authenticated user's information"""
    try:
        # Get user from Medium API
        client = MediumAPIClient()
        medium_response = client.get_current_user()
        
        # Extract user data from Medium API response
        medium_data = medium_response.get("data", {})
        
        if not medium_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user data from Medium API"
            )
        
        # Check if user exists in database
        user = crud.get_user(db, medium_data["id"])
        
        # If user doesn't exist, create it
        if not user:
            user_data = {
                "id": medium_data["id"],
                "username": medium_data["username"],
                "name": medium_data["name"],
                "url": medium_data["url"],
                "image_url": medium_data.get("imageUrl")
            }
            user = crud.create_user(db, user_data)
        # If user exists but data might have changed, update it
        else:
            user_data = {
                "username": medium_data["username"],
                "name": medium_data["name"],
                "url": medium_data["url"],
                "image_url": medium_data.get("imageUrl")
            }
            user = crud.update_user(db, user.id, user_data)
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user information: {str(e)}"
        )

@router.get("/me/publications", response_model=List[Dict[str, Any]])
async def get_user_publications():
    """Get publications that the user is a contributor to"""
    try:
        # Use the real Medium API client
        client = MediumAPIClient()
        user_data = client.get_current_user()
        
        # Extract user ID from Medium API response
        user_id = user_data.get("data", {}).get("id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user ID"
            )
        
        # Get user's publications
        publications = client.get_user_publications(user_id)
        return publications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user publications: {str(e)}"
        ) 