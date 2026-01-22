from supabase import Client, create_client

from app.config import Settings, get_settings

# Cached client instance
_client: Client | None = None


def get_supabase_client(settings: Settings | None = None) -> Client:
    """Get a Supabase client instance."""
    global _client
    if _client is None:
        if settings is None:
            settings = get_settings()
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client
