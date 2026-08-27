from functools import lru_cache
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration comes from environment variables only."""
    supabase_url: str | None = None
    supabase_key: str | None = None
    built_in_forge_api_url: str | None = None
    built_in_forge_api_key: str | None = None
    document_bucket: str | None = None
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    @property
    def has_project_supabase_connection(self) -> bool:
        return bool(
            self.supabase_url
            and self.supabase_url.startswith("https://")
            and ".supabase.co" in self.supabase_url
            and self.supabase_key
            and os.getenv("SUPABASE_PROJECT_VALIDATED") == "true"
        )

    @property
    def has_llm_connection(self) -> bool:
        return bool(self.built_in_forge_api_url and self.built_in_forge_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
