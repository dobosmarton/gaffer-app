import logging

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.google_token_service import (
    GoogleTokenError,
    GoogleTokenService,
    get_google_token_service,
)
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()


class StoreTokenRequest(BaseModel):
    refresh_token: str


class StoreTokenResponse(BaseModel):
    success: bool
    message: str | None = None


class TokenStatusResponse(BaseModel):
    has_google_token: bool


async def get_user_id_from_token(
    authorization: str = Header(...),
    settings: Settings = Depends(get_settings),
) -> str:
    """Extract and verify user ID from Supabase JWT."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    supabase = get_supabase_client(settings)

    try:
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_response.user.id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("/store-google-token", response_model=StoreTokenResponse)
async def store_google_token(
    request: StoreTokenRequest,
    user_id: str = Depends(get_user_id_from_token),
    token_service: GoogleTokenService = Depends(get_google_token_service),
):
    """Store the user's Google refresh token securely (encrypted)."""
    # Validate refresh token
    if not request.refresh_token or not request.refresh_token.strip():
        logger.warning(f"Empty refresh token received for user {user_id[:8]}...")
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No refresh token provided. Please re-authenticate with Google.",
                "needs_google_auth": True,
            }
        )

    try:
        await token_service.store_refresh_token(user_id, request.refresh_token)
        logger.info(f"Token stored for user {user_id[:8]}...")
        return StoreTokenResponse(success=True, message="Token stored successfully")
    except GoogleTokenError as e:
        logger.error(f"Failed to store token for user {user_id[:8]}...: {e}")
        raise HTTPException(status_code=500, detail="Failed to store token")


@router.get("/google-token-status", response_model=TokenStatusResponse)
async def get_google_token_status(
    user_id: str = Depends(get_user_id_from_token),
    token_service: GoogleTokenService = Depends(get_google_token_service),
):
    """Check if the user has a stored Google refresh token."""
    has_token = await token_service.has_refresh_token(user_id)
    return TokenStatusResponse(has_google_token=has_token)


@router.delete("/google-token")
async def revoke_google_token(
    user_id: str = Depends(get_user_id_from_token),
    token_service: GoogleTokenService = Depends(get_google_token_service),
):
    """Revoke/delete the user's stored Google tokens."""
    try:
        await token_service.revoke_tokens(user_id)
        return {"success": True}
    except GoogleTokenError as e:
        logger.error(f"Failed to revoke token for user {user_id[:8]}...: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke token")
