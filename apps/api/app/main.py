from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import hype, calendar, auth

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

# Routers
app.include_router(hype.router, prefix="/hype", tags=["hype"])
app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "env": settings.app_env}
