"""Rate limiting configuration for the API."""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


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


# Shared limiter instance
limiter = Limiter(key_func=get_user_key)
