from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GroundingChunk:
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True, slots=True)
class TranscriptChunk:
    start_ms: int
    end_ms: int
    text: str


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> Sequence[TranscriptChunk]:
        """Return timestamped sentence-level transcript segments."""
        ...
        

class Chunker(Protocol):
    def chunk(self, transcript: Sequence[TranscriptChunk]) -> Sequence[GroundingChunk]:
        """Return a sequence of chunks suitable for embedding and indexing."""
        ...


class DocumentEmbedder(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Encode transcript text for vector storage."""
        ...


class QueryEmbedder(Protocol):
    def embed_query(self, question: str) -> list[float]:
        ...


class GroundedSummarizer(Protocol):
    def summarize(self, question: str, chunks: Sequence[GroundingChunk]) -> str:
        """Produce a concise answer grounded only in the supplied chunks."""
        ...
