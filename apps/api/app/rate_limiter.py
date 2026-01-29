"""Rate limiting configuration for the API."""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import Settings, get_settings


def get_user_key(request: Request) -> str:
    """Get rate limit key from user token or IP address.

    Uses a hash of the auth token for authenticated users,
    falls back to IP address for unauthenticated requests.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Use a hash of the token as the key (more privacy-conscious)
        return f"user:{hash(auth_header)}"
    # Fall back to IP address for unauthenticated requests
    return get_remote_address(request)


def get_limiter(settings: Settings) -> Limiter:
    """Create a limiter instance with appropriate storage backend.

    Uses Redis for distributed rate limiting when REDIS_URL is configured,
    otherwise falls back to in-memory storage (suitable for single instance).
    """
    return Limiter(
        key_func=get_user_key,
        storage_uri=settings.redis_url,
    )


# Shared limiter instance for route decorators
# Uses Redis when REDIS_URL is set, otherwise in-memory
limiter = get_limiter(get_settings())
