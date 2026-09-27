import logging
import tempfile
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import AudioStatus
from app.db.models.audio import AudioAsset
from app.media.probe import InvalidMediaError, probe_duration_ms
from app.queue.client import (
    audio_processing_job_id,
    enqueue_audio_processing,
)
from app.repositories.audio import AudioRepository
from app.storage.factory import get_storage

logger = logging.getLogger(__name__)


class AudioUploadError(RuntimeError):
    pass


class MediaTooLargeError(AudioUploadError):
    pass


class MediaTooLongError(AudioUploadError):
    pass


class UnsupportedMediaError(AudioUploadError):
    pass


class ProcessingQueueUnavailableError(AudioUploadError):
    def __init__(self, audio_id: UUID) -> None:
        self.audio_id = audio_id

        super().__init__(
            "Audio was uploaded, but processing could not be queued"
        )


class AudioService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AudioRepository(db)
        self.storage = get_storage()

    def create(self, upload: UploadFile) -> AudioAsset:
        filename = self._normalize_filename(
            upload.filename or "upload.media"
        )

        suffix = self._safe_suffix(filename)

        temp_path: Path | None = None

        try:
            temp_path, size_bytes = self._copy_to_temporary_file(
                upload,
                suffix,
            )

            try:
                duration_ms = probe_duration_ms(temp_path)
            except InvalidMediaError as exc:
                raise UnsupportedMediaError(
                    "Uploaded file is not a supported media file"
                ) from exc

            max_duration_ms = (
                settings.max_media_duration_seconds * 1000
            )

            if duration_ms > max_duration_ms:
                raise MediaTooLongError(
                    "Media duration exceeds the 10 minute limit"
                )

            audio_id = uuid.uuid4()
            storage_key = f"{audio_id}{suffix}"

            with temp_path.open("rb") as source:
                self.storage.save(
                    source,
                    storage_key,
                )

            job_id = audio_processing_job_id(audio_id)

            asset = AudioAsset(
                id=audio_id,
                original_filename=filename,
                content_type=upload.content_type,
                storage_key=storage_key,
                size_bytes=size_bytes,
                duration_ms=duration_ms,
                status=AudioStatus.QUEUED.value,
                processing_job_id=job_id,
                failure_message=None,
            )

            try:
                self.repo.add(asset)
                self.db.commit()
            except Exception:
                self.db.rollback()
                self.storage.delete(storage_key)
                raise

            try:
                enqueue_audio_processing(audio_id)
            except Exception as exc:
                logger.exception(
                    "Failed to enqueue audio processing",
                    extra={
                        "audio_id": str(audio_id),
                        "job_id": job_id,
                    },
                )

                self._mark_enqueue_failed(asset)

                raise ProcessingQueueUnavailableError(
                    audio_id
                ) from exc

            self.db.refresh(asset)

            return asset

        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def _copy_to_temporary_file(
        self,
        upload: UploadFile,
        suffix: str,
    ) -> tuple[Path, int]:
        temp_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
            ) as temporary:
                temp_path = Path(temporary.name)

                upload.file.seek(0)

                size_bytes = 0

                while True:
                    chunk = upload.file.read(1024 * 1024)

                    if not chunk:
                        break

                    size_bytes += len(chunk)

                    if size_bytes > settings.max_upload_bytes:
                        raise MediaTooLargeError(
                            "File exceeds the upload size limit"
                        )

                    temporary.write(chunk)

            return temp_path, size_bytes

        except Exception:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

            raise

    def _mark_enqueue_failed(
        self,
        asset: AudioAsset,
    ) -> None:
        asset.status = AudioStatus.FAILED.value
        asset.failure_message = (
            "Audio processing is temporarily unavailable"
        )

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

            logger.exception(
                "Failed to persist queue failure state",
                extra={
                    "audio_id": str(asset.id),
                },
            )

    @staticmethod
    def _normalize_filename(filename: str) -> str:
        normalized = filename.replace("\\", "/")
        normalized = normalized.rsplit("/", 1)[-1].strip()

        return normalized or "upload.media"

    @staticmethod
    def _safe_suffix(filename: str) -> str:
        suffix = Path(filename).suffix.lower()

        if (
            not suffix
            or len(suffix) > 10
            or not suffix[1:].isalnum()
        ):
            return ".media"

        return suffix