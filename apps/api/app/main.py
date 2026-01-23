from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import get_settings
from app.routers import hype, calendar, auth


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to prevent XSS and other attacks."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

settings = get_settings()

app = FastAPI(
    title="Gaffer API",
    description="AI-generated football manager-style hype speeches",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Routers
app.include_router(hype.router, prefix="/hype", tags=["hype"])
app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "env": settings.app_env}
