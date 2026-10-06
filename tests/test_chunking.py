from app.ai.chunking import TranscriptChunker
from app.ai.contracts import GroundingChunk, TranscriptChunk


def test_default_chunker_produces_15_to_20_second_excerpts() -> None:
    transcript = [
        TranscriptChunk(
            start_ms=0,
            end_ms=5_000,
            text="one",
        ),
        TranscriptChunk(
            start_ms=5_000,
            end_ms=10_000,
            text="two",
        ),
        TranscriptChunk(
            start_ms=10_000,
            end_ms=15_000,
            text="three",
        ),
        TranscriptChunk(
            start_ms=15_000,
            end_ms=20_000,
            text="four",
        ),
        TranscriptChunk(
            start_ms=20_000,
            end_ms=25_000,
            text="five",
        ),
        TranscriptChunk(
            start_ms=25_000,
            end_ms=30_000,
            text="six",
        ),
        TranscriptChunk(
            start_ms=30_000,
            end_ms=35_000,
            text="seven",
        ),
        TranscriptChunk(
            start_ms=35_000,
            end_ms=40_000,
            text="eight",
        ),
    ]

    chunks = TranscriptChunker().chunk(transcript)

    assert chunks == [
        GroundingChunk(
            start_ms=0,
            end_ms=20_000,
            text="one two three four",
        ),
        GroundingChunk(
            start_ms=20_000,
            end_ms=40_000,
            text="five six seven eight",
        ),
    ]


def test_chunker_splits_on_natural_gap_after_minimum_duration() -> None:
    transcript = [
        TranscriptChunk(
            start_ms=0,
            end_ms=5_000,
            text="one",
        ),
        TranscriptChunk(
            start_ms=5_000,
            end_ms=10_000,
            text="two",
        ),
        TranscriptChunk(
            start_ms=10_000,
            end_ms=15_000,
            text="three",
        ),
        TranscriptChunk(
            start_ms=17_000,
            end_ms=20_000,
            text="four",
        ),
    ]

    chunks = TranscriptChunker().chunk(transcript)

    assert chunks == [
        GroundingChunk(
            start_ms=0,
            end_ms=15_000,
            text="one two three",
        ),
        GroundingChunk(
            start_ms=17_000,
            end_ms=20_000,
            text="four",
        ),
    ]


def test_chunker_does_not_split_too_early_on_gap() -> None:
    transcript = [
        TranscriptChunk(
            start_ms=0,
            end_ms=7_000,
            text="one",
        ),
        TranscriptChunk(
            start_ms=7_000,
            end_ms=14_000,
            text="two",
        ),
        TranscriptChunk(
            start_ms=16_000,
            end_ms=19_000,
            text="three",
        ),
    ]

    chunks = TranscriptChunker().chunk(transcript)

    assert chunks == [
        GroundingChunk(
            start_ms=0,
            end_ms=19_000,
            text="one two three",
        ),
    ]


def test_chunker_preserves_custom_duration_configuration() -> None:
    transcript = [
        TranscriptChunk(
            start_ms=0,
            end_ms=10_000,
            text="hello world",
        ),
        TranscriptChunk(
            start_ms=10_000,
            end_ms=20_000,
            text="this is a test",
        ),
        TranscriptChunk(
            start_ms=20_000,
            end_ms=30_000,
            text="for chunking",
        ),
        TranscriptChunk(
            start_ms=30_000,
            end_ms=46_000,
            text="later segment",
        ),
        TranscriptChunk(
            start_ms=46_000,
            end_ms=65_000,
            text="with more text",
        ),
    ]

    chunks = TranscriptChunker(
        min_duration_ms=25_000,
        max_duration_ms=45_000,
    ).chunk(transcript)

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


def test_chunker_returns_empty_list_for_empty_transcript() -> None:
    assert TranscriptChunker().chunk([]) == []


def test_chunker_ignores_empty_transcript_text() -> None:
    transcript = [
        TranscriptChunk(
            start_ms=0,
            end_ms=5_000,
            text="hello",
        ),
        TranscriptChunk(
            start_ms=5_000,
            end_ms=10_000,
            text="   ",
        ),
        TranscriptChunk(
            start_ms=10_000,
            end_ms=15_000,
            text="world",
        ),
    ]

    chunks = TranscriptChunker().chunk(transcript)

    assert chunks == [
        GroundingChunk(
            start_ms=0,
            end_ms=15_000,
            text="hello world",
        ),
    ]
