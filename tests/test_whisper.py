import sys
import types
from pathlib import Path

from app.ai.contracts import TranscriptChunk
from app.ai.factory import get_transcriber
from app.ai.whisper import WhisperTranscriber


class FakeSegment:
    def __init__(self, start: float, end: float, text: str) -> None:
        self.start = start
        self.end = end
        self.text = text


class FakeWhisperModel:
    def __init__(self, model_name: str, device: str, compute_type: str) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type

    def transcribe(
            self,
            audio_path: str,
            **kwargs: object,
    ) -> tuple[list[FakeSegment], dict[str, object]]:
        assert audio_path.endswith("example.wav")
        assert kwargs["vad_filter"] is True
        assert kwargs["word_timestamps"] is False
        return [
            FakeSegment(1.2, 2.8, "  hello there  "),
            FakeSegment(3.1, 3.9, "   "),
            FakeSegment(4.4, 5.7, "world"),
        ], {}


def test_whisper_transcriber_converts_segments_to_transcript_chunks(monkeypatch) -> None:
    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        types.SimpleNamespace(
            WhisperModel=FakeWhisperModel,
        ),
    )

    transcriber = WhisperTranscriber(model_name="tiny", device="cpu", compute_type="int8")
    chunks = transcriber.transcribe(Path("/tmp/example.wav"))

    assert chunks == [
        TranscriptChunk(start_ms=1_200, end_ms=2_800, text="hello there"),
        TranscriptChunk(start_ms=4_400, end_ms=5_700, text="world"),
    ]


def test_factory_returns_whisper_transcriber(monkeypatch) -> None:
    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        types.SimpleNamespace(
            WhisperModel=FakeWhisperModel,
        ),
    )

    transcriber = get_transcriber()

    assert isinstance(transcriber, WhisperTranscriber)
