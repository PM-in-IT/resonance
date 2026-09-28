import sys
import types

from app.ai.embeddings import SentenceTransformerEmbedder


class FakeSentenceTransformer:
    def __init__(self, model_name: str, device: str) -> None:
        self.model_name = model_name
        self.device = device
        self.encoded_texts: list[str] = []
        self.encode_options: dict[str, object] = {}

    def encode(self, texts: list[str], **kwargs: object) -> list[list[float]]:
        self.encoded_texts.extend(texts)
        self.encode_options = kwargs
        return [[0.6, 0.8] for _ in texts]


def test_sentence_transformer_encodes_document_batches_and_queries(monkeypatch) -> None:
    model_holder: list[FakeSentenceTransformer] = []

    def create_model(model_name: str, device: str) -> FakeSentenceTransformer:
        model = FakeSentenceTransformer(model_name, device)
        model_holder.append(model)
        return model

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        types.SimpleNamespace(SentenceTransformer=create_model),
    )

    embedder = SentenceTransformerEmbedder(model_name="test-model", device="cpu")

    document_vectors = embedder.embed_documents(["first chunk", "second chunk"])
    query_vector = embedder.embed_query("search question")

    assert document_vectors == [[0.6, 0.8], [0.6, 0.8]]
    assert query_vector == [0.6, 0.8]
    assert model_holder[0].model_name == "test-model"
    assert model_holder[0].device == "cpu"
    assert model_holder[0].encoded_texts == [
        "first chunk",
        "second chunk",
        "search question",
    ]
    assert model_holder[0].encode_options == {
        "convert_to_numpy": True,
        "normalize_embeddings": True,
        "show_progress_bar": False,
    }


def test_sentence_transformer_returns_no_vectors_for_no_documents(monkeypatch) -> None:
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer),
    )

    embedder = SentenceTransformerEmbedder(model_name="test-model", device="cpu")

    assert embedder.embed_documents([]) == []