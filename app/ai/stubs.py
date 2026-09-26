from collections.abc import Sequence
from pathlib import Path

from app.ai.contracts import GroundingChunk, IndexedChunk


class StubAudioIndexer:
    def index(self, audio_path: Path) -> Sequence[IndexedChunk]:
        raise NotImplementedError("Wire the AI/ML AudioIndexer implementation in app.ai.factory")


class StubQueryEmbedder:
    def embed_query(self, question: str) -> list[float]:
        raise NotImplementedError("Wire the AI/ML QueryEmbedder implementation in app.ai.factory")


class StubGroundedSummarizer:
    def summarize(
        self,
        question: str,
        chunks: Sequence[GroundingChunk],
    ) -> str:
        raise NotImplementedError(
            "Wire the AI/ML GroundedSummarizer implementation "
            "in app.ai.factory"
        )
