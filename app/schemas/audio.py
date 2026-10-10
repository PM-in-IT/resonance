from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AudioAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    content_type: str | None
    size_bytes: int
    duration_ms: int
    status: str
    failure_message: str | None
    created_at: datetime
    updated_at: datetime
