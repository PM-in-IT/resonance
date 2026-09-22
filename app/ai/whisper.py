from pathlib import Path
from typing import Any

from app.ai.contracts import TranscriptChunk
from app.core.config import settings


class WhisperTranscriber:
    """Transcribe local media with a lazily loaded faster-whisper model."""

    def __init__(
        self,
        model_name: str = settings.whisper_model,
        device: str = settings.whisper_device,
        compute_type: str = settings.whisper_compute_type,
    ) -> None:
        from faster_whisper import WhisperModel 

        self._model = WhisperModel(model_name, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: Path) -> list[TranscriptChunk]:
        segments, _ = self._model.transcribe(
            str(audio_path),
            vad_filter=True,
            word_timestamps=False,
        )
        return [self._to_sentence(segment) for segment in segments if segment.text.strip()]

    @staticmethod
    def _to_sentence(segment: Any) -> TranscriptChunk:
        return TranscriptChunk(
            start_ms=round(float(segment.start) * 1000),
            end_ms=round(float(segment.end) * 1000),
            text=segment.text.strip(),
        )