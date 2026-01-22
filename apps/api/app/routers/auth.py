from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.supabase_client import get_supabase_client

router = APIRouter()


class StoreTokenRequest(BaseModel):
    refresh_token: str


class StoreTokenResponse(BaseModel):
    success: bool


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
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@router.post("/store-google-token", response_model=StoreTokenResponse)
async def store_google_token(
    request: StoreTokenRequest,
    user_id: str = Depends(get_user_id_from_token),
    settings: Settings = Depends(get_settings),
):
    """Store the user's Google refresh token securely."""
    supabase = get_supabase_client(settings)

    # Upsert the token into user_google_tokens table
    try:
        supabase.table("user_google_tokens").upsert({
            "user_id": user_id,
            "refresh_token": request.refresh_token,
        }).execute()

        return StoreTokenResponse(success=True)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store token: {str(e)}"
        )
