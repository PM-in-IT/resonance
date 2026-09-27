import logging
from collections.abc import Sequence
from uuid import UUID

from app.ai.contracts import GroundingChunk
from app.ai.factory import get_chunker, get_transcriber
from app.core.enums import AudioStatus
from app.db.models.segment import TranscriptSegment
from app.db.session import SessionLocal
from app.repositories.audio import AudioRepository
from app.repositories.segments import SegmentRepository
from app.storage.factory import get_storage

logger = logging.getLogger(__name__)


class EmptyTranscriptError(RuntimeError):
    pass


class InvalidChunkError(RuntimeError):
    pass


def process_audio(audio_id_raw: str) -> None:
    audio_id = UUID(audio_id_raw)
    db = SessionLocal()

    try:
        asset = AudioRepository(db).get(audio_id)

        if asset is None:
            logger.warning(
                "Processing job references unknown audio asset",
                extra={
                    "audio_id": str(audio_id),
                },
            )
            return

        # Makes the job reasonably idempotent if the same successful
        # job is accidentally delivered again.
        if asset.status == AudioStatus.READY.value:
            logger.info(
                "Audio asset is already ready; skipping processing",
                extra={
                    "audio_id": str(audio_id),
                },
            )
            return

        asset.status = AudioStatus.PROCESSING.value
        asset.failure_message = None
        db.commit()

        media_path = get_storage().resolve_local_path(
            asset.storage_key
        )

        transcriber = get_transcriber()
        chunker = get_chunker()

        transcript = transcriber.transcribe(media_path)

        if not transcript:
            raise EmptyTranscriptError(
                "No speech could be transcribed from the media"
            )

        chunks = list(
            chunker.chunk(transcript)
        )

        if not chunks:
            raise EmptyTranscriptError(
                "No searchable transcript chunks were produced"
            )

        _validate_chunks(chunks)

        rows = [
            TranscriptSegment(
                audio_id=audio_id,
                ordinal=ordinal,
                start_ms=chunk.start_ms,
                end_ms=chunk.end_ms,
                text=chunk.text,
                embedding=None,
            )
            for ordinal, chunk in enumerate(chunks)
        ]

        SegmentRepository(db).replace_for_audio(
            audio_id,
            rows,
        )

        asset.status = AudioStatus.READY.value
        asset.failure_message = None

        db.commit()

        logger.info(
            "Audio processing completed",
            extra={
                "audio_id": str(audio_id),
                "segment_count": len(rows),
            },
        )

    except EmptyTranscriptError as exc:
        logger.info(
            "Audio processing produced no transcript",
            extra={
                "audio_id": str(audio_id),
            },
        )

        _mark_failed(
            db,
            audio_id,
            str(exc),
        )

        raise

    except InvalidChunkError:
        logger.exception(
            "AI pipeline returned invalid transcript chunks",
            extra={
                "audio_id": str(audio_id),
            },
        )

        _mark_failed(
            db,
            audio_id,
            "Audio processing produced invalid transcript data",
        )

        raise

    except Exception:
        logger.exception(
            "Audio processing failed",
            extra={
                "audio_id": str(audio_id),
            },
        )

        _mark_failed(
            db,
            audio_id,
            "Audio processing failed",
        )

        raise

    finally:
        db.close()


def _validate_chunks(
    chunks: Sequence[GroundingChunk],
) -> None:
    previous_start_ms = -1

    for chunk in chunks:
        if chunk.start_ms < 0:
            raise InvalidChunkError(
                "Chunk start timestamp cannot be negative"
            )

        if chunk.end_ms <= chunk.start_ms:
            raise InvalidChunkError(
                "Chunk end timestamp must be after start timestamp"
            )

        if chunk.start_ms < previous_start_ms:
            raise InvalidChunkError(
                "Transcript chunks are not ordered"
            )

        if not chunk.text.strip():
            raise InvalidChunkError(
                "Transcript chunk text cannot be empty"
            )

        previous_start_ms = chunk.start_ms


def _mark_failed(
    db,
    audio_id: UUID,
    message: str,
) -> None:
    db.rollback()

    asset = AudioRepository(db).get(audio_id)

    if asset is None:
        return

    asset.status = AudioStatus.FAILED.value
    asset.failure_message = message[:2000]

    try:
        db.commit()
    except Exception:
        db.rollback()

        logger.exception(
            "Could not persist failed audio status",
            extra={
                "audio_id": str(audio_id),
            },
        )