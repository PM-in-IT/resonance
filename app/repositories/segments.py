from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.segment import TranscriptSegment


class SegmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def replace_for_audio(self, audio_id: UUID, segments: list[TranscriptSegment]) -> None:
        self.db.execute(delete(TranscriptSegment).where(TranscriptSegment.audio_id == audio_id))
        self.db.add_all(segments)

    def nearest(
        self, audio_id: UUID, query_embedding: list[float], top_k: int
    ) -> list[TranscriptSegment]:
        stmt = (
            select(TranscriptSegment)
            .where(TranscriptSegment.audio_id == audio_id)
            .order_by(TranscriptSegment.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        return list(self.db.scalars(stmt))
