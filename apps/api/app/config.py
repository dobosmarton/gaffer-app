from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_env: str = "development"
    frontend_url: str = "http://localhost:3000"

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # Anthropic
    anthropic_api_key: str

    # Google OAuth (for refreshing tokens)
    google_client_id: str
    google_client_secret: str

    # ElevenLabs
    elevenlabs_api_key: str
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"  # Default: George

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
