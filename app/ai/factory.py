from app.ai.contracts import AudioIndexer, GroundedSummarizer, QueryEmbedder
from app.ai.stubs import StubAudioIndexer, StubGroundedSummarizer, StubQueryEmbedder


def get_audio_indexer() -> AudioIndexer:
    return StubAudioIndexer()


def get_query_embedder() -> QueryEmbedder:
    return StubQueryEmbedder()


def get_summarizer() -> GroundedSummarizer:
    return StubGroundedSummarizer()
