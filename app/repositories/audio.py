from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.audio import AudioAsset


class AudioRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, asset: AudioAsset) -> AudioAsset:
        self.db.add(asset)
        self.db.flush()
        return asset

    def get(self, audio_id: UUID) -> AudioAsset | None:
        return self.db.get(AudioAsset, audio_id)
