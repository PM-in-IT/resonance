from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://resonance:resonance@localhost:5432/resonance"
    redis_url: str = "redis://localhost:6379/0"
    rq_queue_name: str = "media"
    storage_backend: str = "local"
    local_storage_path: Path = Path("./data/uploads")
    max_upload_bytes: int = 100 * 1024 * 1024
    max_media_duration_seconds: int = 600
    embedding_dimension: int = 0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
