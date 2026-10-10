from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    app_env: str = "dev"
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+psycopg://resonance:resonance@localhost:5432/resonance"
    )

    redis_url: str = "redis://localhost:6379/0"
    rq_queue_name: str = "media"

    processing_job_timeout_seconds: int = 30 * 60
    processing_job_result_ttl_seconds: int = 60 * 60

    storage_backend: str = "local"
    local_storage_path: Path = Path("./data/uploads")

    max_upload_bytes: int = 100 * 1024 * 1024
    max_media_duration_seconds: int = 600

    embedding_dimension: int = 384
    sentence_transformer_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    sentence_transformer_device: str = "cpu"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_request_timeout_seconds: float = 180.0

    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()