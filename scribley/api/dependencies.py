from fastapi import Request, HTTPException, status
from .medium import MediumAPIClient

async def get_medium_client(request: Request) -> MediumAPIClient:
    if not hasattr(request.app.state, 'medium_client') or request.app.state.medium_client is None:
        # This case should ideally be handled by the startup event ensuring client is initialized.
        # If it happens, it means startup failed or was bypassed.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Medium API client not initialized. Check server logs."
        )
    return request.app.state.medium_client 