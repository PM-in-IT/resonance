from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.contracts import GroundingChunk
from app.ai.factory import get_query_embedder, get_summarizer
from app.core.enums import AudioStatus
from app.db.models.query import QueryRecord
from app.repositories.audio import AudioRepository
from app.repositories.queries import QueryRepository
from app.repositories.segments import SegmentRepository
from app.schemas.query import MatchResponse, QueryResponse


class AudioNotReadyError(RuntimeError):
    pass


class QueryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def answer(self, audio_id: UUID, question: str, top_k: int) -> QueryResponse:
        asset = AudioRepository(self.db).get(audio_id)
        if asset is None:
            raise LookupError("Audio not found")
        if asset.status != AudioStatus.READY.value:
            raise AudioNotReadyError(f"Audio is not ready; current status is '{asset.status}'")

        query_embedding = get_query_embedder().embed_query(question)
        segments = SegmentRepository(self.db).nearest(audio_id, query_embedding, top_k)
        if not segments:
            raise RuntimeError("No indexed transcript segments found")

        grounding = [
            GroundingChunk(start_ms=s.start_ms, end_ms=s.end_ms, text=s.text)
            for s in segments
        ]
        summary = get_summarizer().summarize(question, grounding)
        primary = segments[0]

        QueryRepository(self.db).add(
            QueryRecord(
                audio_id=audio_id,
                question=question,
                summary=summary,
                primary_start_ms=primary.start_ms,
                primary_end_ms=primary.end_ms,
            )
        )
        self.db.commit()

        return QueryResponse(
            question=question,
            summary=summary,
            primary_start_ms=primary.start_ms,
            primary_end_ms=primary.end_ms,
            matches=[
                MatchResponse(start_ms=s.start_ms, end_ms=s.end_ms, text=s.text)
                for s in segments
            ],
        )
