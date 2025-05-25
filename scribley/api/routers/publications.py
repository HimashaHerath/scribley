from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..medium import MediumAPIClient
from ..dependencies import get_medium_client
from ..schemas import Publication
from ...database.config import get_db
from ...database import crud

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Publication])
async def get_my_synced_publications(
    db: AsyncSession = Depends(get_db),
    client: MediumAPIClient = Depends(get_medium_client)
):
    """Get publications the user contributes to, synced from Medium to local DB."""
    try:
        user_data_response = await client.get_current_user()
        user_medium_id = user_data_response.get("id")
        
        if not user_medium_id:
            logger.error(f"Failed to get user ID from Medium API. Response: {user_data_response}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user ID for fetching publications"
            )
        
        medium_publications_list = await client.get_user_publications(user_medium_id)
        
        synced_publications = []
        if medium_publications_list:
            for pub_data_from_medium in medium_publications_list:
                if not pub_data_from_medium or not pub_data_from_medium.get("id"):
                    logger.warning(f"Skipping invalid publication data from Medium: {pub_data_from_medium}")
                    continue

                pub_id = pub_data_from_medium["id"]
                publication_payload = {
                    "id": pub_id,
                    "name": pub_data_from_medium["name"],
                    "description": pub_data_from_medium.get("description", ""),
                    "url": pub_data_from_medium.get("url", ""),
                    "image_url": pub_data_from_medium.get("imageUrl", "")
                }
                
                db_pub = await crud.get_publication(db, pub_id)
                if not db_pub:
                    logger.info(f"Publication ID {pub_id} not in DB, creating.")
                    created_pub = await crud.create_publication(db, publication_payload)
                    synced_publications.append(created_pub)
                else:
                    logger.info(f"Publication ID {pub_id} found in DB, updating.")
                    update_payload = {k: v for k, v in publication_payload.items() if k != "id"}
                    updated_pub = await crud.update_publication(db, pub_id, update_payload)
                    synced_publications.append(updated_pub)
            return synced_publications
        else:
            logger.info(f"No publications returned from Medium for user {user_medium_id}. Checking local DB.")
            db_publications = await crud.get_publications(db)
            return db_publications

    except Exception as e:
        logger.error(f"Failed to get publications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get publications: {str(e)}"
        )

@router.get("/{publication_id}", response_model=Publication)
async def get_specific_publication(
    publication_id: str, 
    db: AsyncSession = Depends(get_db),
    client: MediumAPIClient = Depends(get_medium_client)
):
    """Get a specific publication by ID, ensuring it's one the user has access to via Medium sync."""
    try:
        db_publication = await crud.get_publication(db, publication_id)
        if db_publication:
            return db_publication

        logger.info(f"Publication {publication_id} not in local DB or verification needed. Fetching from Medium.")
        user_data_response = await client.get_current_user()
        user_medium_id = user_data_response.get("id")
        
        if not user_medium_id:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user ID")
        
        medium_publications_list = await client.get_user_publications(user_medium_id)
        
        for pub_data_from_medium in medium_publications_list:
            if pub_data_from_medium.get("id") == publication_id:
                publication_payload = {
                    "id": pub_data_from_medium["id"],
                    "name": pub_data_from_medium["name"],
                    "description": pub_data_from_medium.get("description", ""),
                    "url": pub_data_from_medium.get("url", ""),
                    "image_url": pub_data_from_medium.get("imageUrl", "")
                }
                existing_pub = await crud.get_publication(db, publication_id)
                if not existing_pub:
                    return await crud.create_publication(db, publication_payload)
                else:
                    update_payload = {k:v for k,v in publication_payload.items() if k != "id"}
                    return await crud.update_publication(db, publication_id, update_payload)
        
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Publication with ID {publication_id} not found or not accessible.")
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to get publication {publication_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get publication: {str(e)}")

@router.get("/{publication_id}/contributors", response_model=List[Dict[str, Any]])
async def get_medium_publication_contributors(
    publication_id: str, 
    client: MediumAPIClient = Depends(get_medium_client)
):
    """Get contributors for a publication directly from Medium."""
    try:
        contributors_response = await client.get_publication_contributors(publication_id)
        return contributors_response
    except Exception as e:
        logger.error(f"Failed to get publication contributors for {publication_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get publication contributors: {str(e)}"
        ) 