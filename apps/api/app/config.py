from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_env: str = "development"
    frontend_url: str = "http://localhost:3000"

    # Database (PostgreSQL via Supabase)
    database_url: str  # postgresql+asyncpg://user:pass@host:port/db

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # Anthropic
    anthropic_api_key: str

    # Google OAuth (for refreshing tokens server-side)
    google_client_id: str
    google_client_secret: str

    # Token encryption (Fernet key - generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    token_encryption_key: str

    # ElevenLabs
    elevenlabs_api_key: str
    elevenlabs_voice_id: str = "wo6udizrrtpIxWGp2qJk"

    # Redis (optional - enables distributed caching and rate limiting)
    redis_url: str | None = None

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def redis_enabled(self) -> bool:
        return self.redis_url is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()
