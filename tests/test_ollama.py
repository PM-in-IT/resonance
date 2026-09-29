import httpx

from app.ai.contracts import GroundingChunk
from app.ai.ollama import OllamaError, OllamaGroundedSummarizer


def test_summarizer_sends_question_and_timestamped_excerpts(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, *, json: dict[str, object], timeout: float) -> httpx.Response:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={"message": {"content": "The lecture defines resonance. [1]"}},
            request=request,
        )

    monkeypatch.setattr("app.ai.ollama.httpx.post", fake_post)
    summarizer = OllamaGroundedSummarizer(
        base_url="http://ollama:11434/",
        model="qwen2.5:3b",
        timeout_seconds=90,
    )

    answer = summarizer.summarize(
        "What is resonance?",
        [GroundingChunk(12_345, 20_000, "Resonance is a response at a natural frequency.")],
    )

    assert answer == "The lecture defines resonance. [1]"
    assert captured["url"] == "http://ollama:11434/api/chat"
    assert captured["timeout"] == 90
    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["model"] == "qwen2.5:3b"
    messages = payload["messages"]
    assert isinstance(messages, list)
    assert messages[1]["content"] == (
        "Question:\nWhat is resonance?\n\nRetrieved transcript excerpts:\n"
        "[1] 00:00:12.345-00:00:20.000: "
        "Resonance is a response at a natural frequency."
    )


def test_summarizer_returns_fallback_without_calling_ollama(monkeypatch) -> None:
    def unexpected_post(*args: object, **kwargs: object) -> httpx.Response:
        raise AssertionError("Ollama should not be called without retrieved excerpts")

    monkeypatch.setattr("app.ai.ollama.httpx.post", unexpected_post)

    answer = OllamaGroundedSummarizer().summarize("Unknown topic?", [])

    assert answer == "I could not find relevant information in this recording."


def test_summarizer_reports_ollama_connection_failure(monkeypatch) -> None:
    def failed_post(*args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("app.ai.ollama.httpx.post", failed_post)

    try:
        OllamaGroundedSummarizer().summarize(
            "Question?",
            [GroundingChunk(0, 1_000, "A transcript excerpt.")],
        )
    except OllamaError as exc:
        assert str(exc) == "Could not connect to Ollama"
    else:
        raise AssertionError("Expected OllamaError")
