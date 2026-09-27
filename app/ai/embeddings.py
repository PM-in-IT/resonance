from collections.abc import Sequence
from typing import Any

from app.core.config import settings


class SentenceTransformerEmbedder:
    """Create normalized text vectors with Sentence Transformers."""

    def __init__(
        self,
        model_name: str = settings.sentence_transformer_model,
        device: str = settings.sentence_transformer_device,
    ) -> None:
        from sentence_transformers import SentenceTransformer  

        self._model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._encode(texts)

    def embed_query(self, question: str) -> list[float]:
        vectors = self._encode([question])
        if not vectors:
            raise ValueError("Cannot embed an empty query")
        return vectors[0]

    def _encode(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        encoded: Any = self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        matrix = encoded.tolist() if hasattr(encoded, "tolist") else encoded
        return [[float(value) for value in vector] for vector in matrix]