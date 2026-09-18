from uuid import UUID

from app.ai.factory import get_audio_indexer
from app.core.enums import AudioStatus
from app.db.models.segment import TranscriptSegment
from app.db.session import SessionLocal
from app.repositories.audio import AudioRepository
from app.repositories.segments import SegmentRepository
from app.storage.factory import get_storage


def process_audio(audio_id_raw: str) -> None:
    audio_id = UUID(audio_id_raw)
    db = SessionLocal()
    try:
        asset = AudioRepository(db).get(audio_id)
        if asset is None:
            return

        asset.status = AudioStatus.PROCESSING.value
        asset.failure_message = None
        db.commit()

        media_path = get_storage().resolve_local_path(asset.storage_key)
        chunks = get_audio_indexer().index(media_path)

        rows = [
            TranscriptSegment(
                audio_id=audio_id,
                ordinal=chunk.ordinal,
                start_ms=chunk.start_ms,
                end_ms=chunk.end_ms,
                text=chunk.text,
                embedding=chunk.embedding,
            )
            for chunk in chunks
        ]
        SegmentRepository(db).replace_for_audio(audio_id, rows)
        asset.status = AudioStatus.READY.value
        db.commit()
    except Exception as exc:
        db.rollback()
        asset = AudioRepository(db).get(audio_id)
        if asset is not None:
            asset.status = AudioStatus.FAILED.value
            asset.failure_message = str(exc)[:2000]
            db.commit()
        raise
    finally:
        db.close()
