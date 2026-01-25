"""
Google Token Service

Handles secure storage and management of Google OAuth tokens following
the BFF (Backend-for-Frontend) pattern. Refresh tokens are encrypted
at rest and access tokens are cached to minimize Google API calls.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models import UserGoogleToken

logger = logging.getLogger(__name__)

# In-memory cache for access tokens (per-user)
# In production, consider using Redis for multi-instance deployments
_access_token_cache: dict[str, tuple[str, datetime]] = {}

# Access tokens are valid for ~1 hour, but we refresh early to avoid edge cases
ACCESS_TOKEN_CACHE_TTL = timedelta(minutes=50)


class GoogleTokenError(Exception):
    """Base exception for Google token operations."""

    pass


class NoRefreshTokenError(GoogleTokenError):
    """Raised when user has no refresh token stored."""

    pass


class TokenRefreshError(GoogleTokenError):
    """Raised when refresh token exchange fails."""

    pass


class GoogleTokenService:
    """Service for managing Google OAuth tokens securely."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._fernet = Fernet(settings.token_encryption_key.encode())

    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token for storage."""
        return self._fernet.encrypt(token.encode()).decode()

    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a stored token."""
        try:
            return self._fernet.decrypt(encrypted_token.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt token - encryption key may have changed")
            raise GoogleTokenError("Token decryption failed")

    async def store_refresh_token(
        self, db: AsyncSession, user_id: str, refresh_token: str
    ) -> None:
        """Store an encrypted refresh token for a user."""
        encrypted_token = self._encrypt_token(refresh_token)
        now = datetime.now(timezone.utc)

        try:
            stmt = insert(UserGoogleToken).values(
                user_id=user_id,
                refresh_token=encrypted_token,
                updated_at=now,
            ).on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "refresh_token": encrypted_token,
                    "updated_at": now,
                },
            )
            await db.execute(stmt)
            await db.commit()
            logger.info(f"Stored refresh token for user {user_id[:8]}...")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to store refresh token: {e}")
            raise GoogleTokenError("Failed to store refresh token")

    async def get_refresh_token(self, db: AsyncSession, user_id: str) -> str:
        """Retrieve and decrypt the refresh token for a user."""
        try:
            stmt = select(UserGoogleToken.refresh_token).where(
                UserGoogleToken.user_id == user_id
            )
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()
        except Exception:
            row = None

        if not row:
            raise NoRefreshTokenError("No refresh token found for user")

        return self._decrypt_token(row)

    async def _exchange_refresh_token(self, refresh_token: str) -> tuple[str, Optional[str]]:
        """Exchange a refresh token for a new access token.

        Returns:
            Tuple of (access_token, new_refresh_token or None)
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=30,
            )

            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error_description", error_data.get("error", "Unknown error"))
                logger.error(f"Token refresh failed: {error_msg}")

                # Check if refresh token was revoked
                if error_data.get("error") == "invalid_grant":
                    raise NoRefreshTokenError("Refresh token has been revoked")

                raise TokenRefreshError(f"Failed to refresh token: {error_msg}")

            token_data = response.json()
            access_token = token_data["access_token"]
            # Google may issue a new refresh token (rotation)
            new_refresh_token = token_data.get("refresh_token")

            return access_token, new_refresh_token

    async def get_access_token(self, db: AsyncSession, user_id: str) -> str:
        """Get a valid access token for a user.

        This method:
        1. Checks the in-memory cache first
        2. If not cached or expired, retrieves refresh token from DB
        3. Exchanges refresh token for new access token
        4. Caches the new access token
        5. Updates refresh token if Google issued a new one
        """
        # Check cache first
        if user_id in _access_token_cache:
            token, expires_at = _access_token_cache[user_id]
            if datetime.now(timezone.utc) < expires_at:
                logger.debug(f"Using cached access token for user {user_id[:8]}...")
                return token

        # Cache miss or expired - get refresh token from DB
        refresh_token = await self.get_refresh_token(db, user_id)

        # Exchange for access token
        access_token, new_refresh_token = await self._exchange_refresh_token(refresh_token)

        # Cache the new access token
        expires_at = datetime.now(timezone.utc) + ACCESS_TOKEN_CACHE_TTL
        _access_token_cache[user_id] = (access_token, expires_at)
        logger.info(f"Refreshed and cached access token for user {user_id[:8]}...")

        # If Google issued a new refresh token, update our stored one
        if new_refresh_token and new_refresh_token != refresh_token:
            logger.info(f"Google issued new refresh token for user {user_id[:8]}..., updating")
            await self.store_refresh_token(db, user_id, new_refresh_token)

        return access_token

    async def revoke_tokens(self, db: AsyncSession, user_id: str) -> None:
        """Remove all tokens for a user (e.g., on logout or disconnect)."""
        # Remove from cache
        _access_token_cache.pop(user_id, None)

        # Remove from database
        try:
            stmt = delete(UserGoogleToken).where(UserGoogleToken.user_id == user_id)
            await db.execute(stmt)
            await db.commit()
            logger.info(f"Revoked tokens for user {user_id[:8]}...")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to revoke tokens: {e}")
            raise GoogleTokenError("Failed to revoke tokens")

    async def has_refresh_token(self, db: AsyncSession, user_id: str) -> bool:
        """Check if a user has a stored refresh token."""
        try:
            await self.get_refresh_token(db, user_id)
            return True
        except NoRefreshTokenError:
            return False


# Dependency for FastAPI
def get_google_token_service() -> GoogleTokenService:
    """Get a GoogleTokenService instance."""
    settings = get_settings()
    return GoogleTokenService(settings)
