from collections.abc import Sequence

from app.ai.contracts import Chunker, GroundingChunk, TranscriptChunk


class TranscriptChunker(Chunker):
    """
    Merge adjacent transcript chunks into tighter, contiguous windows in the 20-45s range.

    The algorithm keeps natural ordering, avoids merging across long silent gaps, and adjusts
    the resulting timestamps to reflect the new merged window boundaries.
    """

    def __init__(
        self,
        min_duration_ms: int = 20_000,
        max_duration_ms: int = 45_000,
        gap_threshold_ms: int = 1_500,
    ) -> None:
        self.min_duration_ms = min_duration_ms
        self.max_duration_ms = max_duration_ms
        self.gap_threshold_ms = gap_threshold_ms

    def chunk(self, transcript: Sequence[TranscriptChunk]) -> list[GroundingChunk]:
        if not transcript:
            return []

        chunks: list[GroundingChunk] = []
        start_ms = transcript[0].start_ms
        end_ms = transcript[0].end_ms
        texts: list[str] = [transcript[0].text.strip()]

        for chunk in transcript[1:]:
            next_text = chunk.text.strip()
            if not next_text:
                continue

            gap_ms = max(0, chunk.start_ms - end_ms)
            projected_end_ms = max(end_ms, chunk.end_ms)
            projected_duration_ms = projected_end_ms - start_ms

            should_split = (
                projected_duration_ms > self.max_duration_ms
                or (
                    gap_ms > self.gap_threshold_ms
                    and projected_duration_ms >= self.min_duration_ms
                )
            )

            if should_split:
                built = self._build_chunk(start_ms, end_ms, texts)
                if built is not None:
                    chunks.append(built)
                start_ms = chunk.start_ms
                end_ms = chunk.end_ms
                texts = [next_text]
                continue

            end_ms = projected_end_ms
            texts.append(next_text)

        built = self._build_chunk(start_ms, end_ms, texts)
        if built is not None:
            chunks.append(built)

        return chunks

    @staticmethod
    def _build_chunk(
        start_ms: int,
        end_ms: int,
        texts: Sequence[str],
    ) -> GroundingChunk | None:
        clean_text = " ".join(part for part in texts if part).strip()
        if not clean_text:
            return None
        return GroundingChunk(start_ms=start_ms, end_ms=end_ms, text=clean_text)
