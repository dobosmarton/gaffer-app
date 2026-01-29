"""
Unit tests for GoogleTokenService.
"""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import httpx
import respx
from cryptography.fernet import Fernet

from app.services.google_token_service import (
    GoogleTokenService,
    GoogleTokenError,
    NoRefreshTokenError,
    TokenRefreshError,
    ACCESS_TOKEN_CACHE_TTL,
)


@pytest.fixture
def token_service(test_settings, cache_service):
    """Create a GoogleTokenService instance for testing."""
    return GoogleTokenService(test_settings, cache_service)


class TestTokenEncryption:
    """Tests for token encryption/decryption."""

    def test_encrypt_and_decrypt_token(self, token_service):
        """Encrypted token can be decrypted back to original."""
        original_token = "test-refresh-token-12345"

        encrypted = token_service._encrypt_token(original_token)
        decrypted = token_service._decrypt_token(encrypted)

        assert decrypted == original_token
        assert encrypted != original_token

    def test_decrypt_with_wrong_key_raises_error(self, test_settings, cache_service):
        """Decrypting with wrong key raises GoogleTokenError."""
        service1 = GoogleTokenService(test_settings, cache_service)

        # Create a new service with different encryption key
        wrong_settings = test_settings.model_copy(
            update={"token_encryption_key": Fernet.generate_key().decode()}
        )
        service2 = GoogleTokenService(wrong_settings, cache_service)

        encrypted = service1._encrypt_token("test-token")

        with pytest.raises(GoogleTokenError, match="Token decryption failed"):
            service2._decrypt_token(encrypted)

    def test_encryption_produces_different_ciphertext_each_time(self, token_service):
        """Same plaintext produces different ciphertext (Fernet uses random IV)."""
        token = "same-token"

        encrypted1 = token_service._encrypt_token(token)
        encrypted2 = token_service._encrypt_token(token)

        assert encrypted1 != encrypted2


@pytest.mark.integration
class TestStoreRefreshToken:
    """Tests for storing refresh tokens. Requires PostgreSQL."""

    @pytest.mark.asyncio
    async def test_store_new_token(self, token_service, pg_session, test_user_id):
        """Can store a new refresh token for a user."""
        user_id_str = str(test_user_id)
        refresh_token = "new-refresh-token"

        await token_service.store_refresh_token(pg_session, user_id_str, refresh_token)

        # Verify token was stored and encrypted
        stored_token = await token_service.get_refresh_token(pg_session, user_id_str)
        assert stored_token == refresh_token

    @pytest.mark.asyncio
    async def test_update_existing_token(self, token_service, pg_session, test_user_id):
        """Storing a token for existing user updates the token."""
        user_id_str = str(test_user_id)
        old_token = "old-refresh-token"
        new_token = "new-refresh-token"

        await token_service.store_refresh_token(pg_session, user_id_str, old_token)
        await token_service.store_refresh_token(pg_session, user_id_str, new_token)

        stored_token = await token_service.get_refresh_token(pg_session, user_id_str)
        assert stored_token == new_token


@pytest.mark.integration
class TestGetRefreshToken:
    """Tests for retrieving refresh tokens. Requires PostgreSQL."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_token_raises_error(
        self, token_service, pg_session, test_user_id
    ):
        """Getting token for user without token raises NoRefreshTokenError."""
        user_id_str = str(test_user_id)
        with pytest.raises(NoRefreshTokenError, match="No refresh token found"):
            await token_service.get_refresh_token(pg_session, user_id_str)


class TestGetAccessToken:
    """Tests for getting access tokens with caching."""

    @pytest.mark.asyncio
    async def test_returns_cached_token_when_available(
        self, token_service, db_session, test_user_id, cache_service
    ):
        """Returns cached access token without calling Google."""
        user_id_str = str(test_user_id)
        cache_key = f"google_access_token:{user_id_str}"
        cached_token = "cached-access-token"
        await cache_service.set(cache_key, cached_token, ACCESS_TOKEN_CACHE_TTL)

        with respx.mock:
            result = await token_service.get_access_token(db_session, user_id_str)

            assert result == cached_token
            # Verify no Google API call was made
            assert respx.calls.call_count == 0


@pytest.mark.integration
class TestGetAccessTokenIntegration:
    """Integration tests for getting access tokens. Requires PostgreSQL."""

    @pytest.mark.asyncio
    async def test_refreshes_token_on_cache_miss(
        self,
        token_service,
        pg_session,
        test_user_id,
        mock_google_oauth_response,
    ):
        """Refreshes token from Google when not cached."""
        user_id_str = str(test_user_id)
        # Store a refresh token first
        await token_service.store_refresh_token(
            pg_session, user_id_str, "refresh-token"
        )

        with respx.mock:
            # Mock Google token endpoint
            respx.post("https://oauth2.googleapis.com/token").mock(
                return_value=httpx.Response(200, json=mock_google_oauth_response)
            )

            result = await token_service.get_access_token(pg_session, user_id_str)

            assert result == mock_google_oauth_response["access_token"]

    @pytest.mark.asyncio
    async def test_handles_revoked_refresh_token(
        self, token_service, pg_session, test_user_id
    ):
        """Raises NoRefreshTokenError when refresh token is revoked."""
        user_id_str = str(test_user_id)
        await token_service.store_refresh_token(
            pg_session, user_id_str, "revoked-token"
        )

        with respx.mock:
            respx.post("https://oauth2.googleapis.com/token").mock(
                return_value=httpx.Response(
                    400,
                    json={
                        "error": "invalid_grant",
                        "error_description": "Token has been revoked",
                    },
                )
            )

            with pytest.raises(NoRefreshTokenError, match="revoked"):
                await token_service.get_access_token(pg_session, user_id_str)

    @pytest.mark.asyncio
    async def test_handles_token_refresh_error(
        self, token_service, pg_session, test_user_id
    ):
        """Raises TokenRefreshError on general API errors."""
        user_id_str = str(test_user_id)
        await token_service.store_refresh_token(
            pg_session, user_id_str, "refresh-token"
        )

        with respx.mock:
            respx.post("https://oauth2.googleapis.com/token").mock(
                return_value=httpx.Response(
                    500, json={"error": "server_error", "error_description": "Server error"}
                )
            )

            with pytest.raises(TokenRefreshError, match="Failed to refresh token"):
                await token_service.get_access_token(pg_session, user_id_str)


@pytest.mark.integration
class TestRevokeTokens:
    """Tests for revoking user tokens. Requires PostgreSQL."""

    @pytest.mark.asyncio
    async def test_revoke_removes_from_cache_and_db(
        self, token_service, pg_session, test_user_id, cache_service
    ):
        """Revoking tokens removes from both cache and database."""
        user_id_str = str(test_user_id)
        # Store token
        await token_service.store_refresh_token(
            pg_session, user_id_str, "refresh-token"
        )
        cache_key = f"google_access_token:{user_id_str}"
        await cache_service.set(cache_key, "access-token", ACCESS_TOKEN_CACHE_TTL)

        # Revoke
        await token_service.revoke_tokens(pg_session, user_id_str)

        # Verify removed from cache
        cached = await cache_service.get(cache_key)
        assert cached is None

        # Verify removed from database
        with pytest.raises(NoRefreshTokenError):
            await token_service.get_refresh_token(pg_session, user_id_str)


@pytest.mark.integration
class TestHasRefreshToken:
    """Tests for checking if user has refresh token. Requires PostgreSQL."""

    @pytest.mark.asyncio
    async def test_returns_true_when_token_exists(
        self, token_service, pg_session, test_user_id
    ):
        """Returns True when user has a stored token."""
        user_id_str = str(test_user_id)
        await token_service.store_refresh_token(
            pg_session, user_id_str, "refresh-token"
        )

        result = await token_service.has_refresh_token(pg_session, user_id_str)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_no_token(
        self, token_service, pg_session, test_user_id
    ):
        """Returns False when user has no stored token."""
        user_id_str = str(test_user_id)
        result = await token_service.has_refresh_token(pg_session, user_id_str)

        assert result is False
