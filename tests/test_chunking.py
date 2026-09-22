from app.ai.chunking import TranscriptChunker
from app.ai.contracts import GroundingChunk, TranscriptChunk


def test_context_aware_chunker_rechunks_transcript_and_updates_timestamps() -> None:
    transcript = [
        TranscriptChunk(start_ms=0, end_ms=10_000, text="hello world"),
        TranscriptChunk(start_ms=10_000, end_ms=20_000, text="this is a test"),
        TranscriptChunk(start_ms=20_000, end_ms=30_000, text="for chunking"),
        TranscriptChunk(start_ms=30_000, end_ms=46_000, text="later segment"),
        TranscriptChunk(start_ms=46_000, end_ms=65_000, text="with more text"),
    ]

    chunks = TranscriptChunker(min_duration_ms=25_000, max_duration_ms=45_000).chunk(transcript)
    
    print(chunks)

    assert chunks == [
        GroundingChunk(
            start_ms=0,
            end_ms=30_000,
            text="hello world this is a test for chunking",
        ),
        GroundingChunk(
            start_ms=30_000,
            end_ms=65_000,
            text="later segment with more text",
        ),
    ]
