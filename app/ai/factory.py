from app.ai.contracts import AudioIndexer, GroundedSummarizer, QueryEmbedder, Transcriber
from app.ai.stubs import StubAudioIndexer, StubGroundedSummarizer, StubQueryEmbedder
from app.ai.whisper import WhisperTranscriber


def get_audio_indexer() -> AudioIndexer:
    return StubAudioIndexer()


def get_transcriber() -> Transcriber:
    return WhisperTranscriber()


def get_query_embedder() -> QueryEmbedder:
    return StubQueryEmbedder()


def get_summarizer() -> GroundedSummarizer:
    return StubGroundedSummarizer()
