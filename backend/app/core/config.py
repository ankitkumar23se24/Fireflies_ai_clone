"""Application settings, loaded from environment variables (see .env.example)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Meeting Intelligence Platform"
    environment: str = "development"
    database_url: str = "sqlite:///./app.db"
    frontend_url: str = "http://localhost:3000"
    extra_cors_origins: str = ""  # comma separated
    log_level: str = "INFO"
    max_upload_bytes: int = 2 * 1024 * 1024  # 2 MB
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    @property
    def cors_origins(self) -> list[str]:
        origins = [self.frontend_url]
        origins += [o.strip() for o in self.extra_cors_origins.split(",") if o.strip()]
        return [o for o in origins if o != "*"]  # never allow wildcard


@lru_cache
def get_settings() -> Settings:
    return Settings()
