from functools import lru_cache

from app.ai.chunking import TranscriptChunker
from app.ai.contracts import (
    Chunker,
    DocumentEmbedder,
    GroundedSummarizer,
    QueryEmbedder,
    Transcriber,
)
from app.ai.embeddings import SentenceTransformerEmbedder
from app.ai.ollama import OllamaGroundedSummarizer
from app.ai.whisper import WhisperTranscriber


def get_transcriber() -> Transcriber:
    return WhisperTranscriber()


def get_chunker() -> Chunker:
    return TranscriptChunker()


@lru_cache(maxsize=1)
def get_text_embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder()


def get_document_embedder() -> DocumentEmbedder:
    return get_text_embedder()


def get_query_embedder() -> QueryEmbedder:
    return get_text_embedder()


def get_summarizer() -> GroundedSummarizer:
    return OllamaGroundedSummarizer()
