import os
import tempfile
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import AudioStatus
from app.db.models.audio import AudioAsset
from app.media.probe import probe_duration_ms
from app.queue.client import enqueue_audio_processing
from app.repositories.audio import AudioRepository
from app.storage.factory import get_storage


class AudioService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AudioRepository(db)
        self.storage = get_storage()

    def create(self, upload: UploadFile) -> AudioAsset:
        filename = upload.filename or "upload.bin"
        suffix = Path(filename).suffix.lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            total = 0
            upload.file.seek(0)
            while chunk := upload.file.read(1024 * 1024):
                total += len(chunk)
                if total > settings.max_upload_bytes:
                    tmp.close()
                    os.unlink(tmp.name)
                    raise ValueError("File exceeds upload size limit")
                tmp.write(chunk)
            temp_path = Path(tmp.name)

        try:
            duration_ms = probe_duration_ms(temp_path)
            if duration_ms > settings.max_media_duration_seconds * 1000:
                raise ValueError("Media duration exceeds 10 minute limit")

            audio_id = uuid.uuid4()
            storage_key = f"{audio_id}{suffix or '.media'}"
            with temp_path.open("rb") as source:
                self.storage.save(source, storage_key)

            asset = AudioAsset(
                id=audio_id,
                original_filename=filename,
                content_type=upload.content_type,
                storage_key=storage_key,
                size_bytes=total,
                duration_ms=duration_ms,
                status=AudioStatus.QUEUED.value,
            )
            self.repo.add(asset)
            self.db.commit()

            try:
                job = enqueue_audio_processing(audio_id)
            except Exception as exc:
                asset.status = AudioStatus.FAILED.value
                asset.failure_message = "Failed to enqueue media processing"
                self.db.commit()
                raise RuntimeError("Failed to enqueue media processing") from exc

            asset.processing_job_id = job.id
            self.db.commit()
            self.db.refresh(asset)
            return asset
        finally:
            temp_path.unlink(missing_ok=True)
