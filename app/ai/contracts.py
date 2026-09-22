from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


@dataclass(frozen=True, slots=True)
class IndexedChunk:
    ordinal: int
    start_ms: int
    end_ms: int
    text: str
    embedding: list[float]


@dataclass(frozen=True, slots=True)
class GroundingChunk:
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True, slots=True)
class TranscriptSentence:
    start_ms: int
    end_ms: int
    text: str


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> Sequence[TranscriptSentence]:
        """Return timestamped sentence-level transcript segments."""
        ...


class AudioIndexer(Protocol):
    def index(self, audio_path: Path) -> Sequence[IndexedChunk]:
        """Transcribe, timestamp, chunk and embed a media file."""
        ...


class QueryEmbedder(Protocol):
    def embed_query(self, question: str) -> list[float]:
        ...


class GroundedSummarizer(Protocol):
    def summarize(self, question: str, chunks: Sequence[GroundingChunk]) -> str:
        """Produce a concise answer grounded only in the supplied chunks."""
        ...
