from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.rate_limiter import limiter
from app.routers import hype, calendar, auth
from app.services.cache_service import init_cache_service, close_cache_service


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to prevent XSS and other attacks."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize and cleanup resources."""
    # Initialize cache service (Redis or fallback)
    await init_cache_service(settings)
    yield
    # Cleanup
    await close_cache_service()


app = FastAPI(
    title="Gaffer API",
    description="AI-generated football manager-style hype speeches",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiter (with Redis support when configured)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - restrict to specific methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Routers
app.include_router(hype.router, prefix="/hype", tags=["hype"])
app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
