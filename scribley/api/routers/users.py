from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..medium import MediumAPIClient
from ..dependencies import get_medium_client
from ..schemas import User
from ...database.config import get_db
from ...database import crud

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/me", response_model=User)
async def get_current_user_details(
    db: AsyncSession = Depends(get_db), 
    client: MediumAPIClient = Depends(get_medium_client)
):
    """Get the current authenticated user's information from Medium and sync to DB."""
    try:
        medium_response = await client.get_current_user()
        medium_data = medium_response
        
        if not medium_data or not medium_data.get("id"):
            logger.error(f"Failed to get valid user data from Medium API. Response: {medium_response}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get valid user data from Medium API"
            )
        
        user_medium_id = medium_data["id"]
        user = await crud.get_user(db, user_medium_id)
        
        user_payload = {
            "id": user_medium_id,
            "username": medium_data["username"],
            "name": medium_data["name"],
            "url": medium_data["url"],
            "image_url": medium_data.get("imageUrl")
        }

        if not user:
            logger.info(f"User {user_medium_id} not found in DB, creating.")
            user = await crud.create_user(db, user_payload)
        else:
            logger.info(f"User {user_medium_id} found in DB, updating.")
            update_payload = {k: v for k, v in user_payload.items() if k != "id"}
            user = await crud.update_user(db, user_medium_id, update_payload)
        
        return user
    except Exception as e:
        logger.error(f"Error getting user information: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user information: {str(e)}"
        )

@router.get("/me/publications", response_model=List[Dict[str, Any]])
async def get_my_medium_publications(client: MediumAPIClient = Depends(get_medium_client)):
    """Get publications that the authenticated user is a contributor to on Medium."""
    try:
        user_data_response = await client.get_current_user()
        user_medium_id = user_data_response.get("id")
        
        if not user_medium_id:
            logger.error(f"Failed to get user ID from Medium API for publications. Response: {user_data_response}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user ID for fetching publications"
            )
        
        publications_response = await client.get_user_publications(user_medium_id)
        return publications_response
    except Exception as e:
        logger.error(f"Failed to get user publications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user publications: {str(e)}"
        ) 