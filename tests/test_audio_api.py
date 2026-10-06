from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.db.models.audio import AudioAsset
from app.main import app
from app.repositories.audio import AudioRepository


def _fake_db():
    yield object()


def test_list_audio_returns_previous_recordings(monkeypatch) -> None:
    first_id = uuid4()
    second_id = uuid4()

    assets = [
        AudioAsset(
            id=first_id,
            original_filename="lecture-2.wav",
            content_type="audio/wav",
            storage_key=f"{first_id}.wav",
            size_bytes=2_000_000,
            duration_ms=120_000,
            status="ready",
            processing_job_id=None,
            failure_message=None,
            created_at=datetime(
                2026,
                10,
                6,
                10,
                0,
                tzinfo=UTC,
            ),
            updated_at=datetime(
                2026,
                10,
                6,
                10,
                1,
                tzinfo=UTC,
            ),
        ),
        AudioAsset(
            id=second_id,
            original_filename="lecture-1.wav",
            content_type="audio/wav",
            storage_key=f"{second_id}.wav",
            size_bytes=1_000_000,
            duration_ms=60_000,
            status="ready",
            processing_job_id=None,
            failure_message=None,
            created_at=datetime(
                2026,
                10,
                5,
                10,
                0,
                tzinfo=UTC,
            ),
            updated_at=datetime(
                2026,
                10,
                5,
                10,
                1,
                tzinfo=UTC,
            ),
        ),
    ]

    captured: dict[str, int] = {}

    def fake_list_recent(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AudioAsset]:
        captured["limit"] = limit
        captured["offset"] = offset
        return assets

    monkeypatch.setattr(
        AudioRepository,
        "list_recent",
        fake_list_recent,
    )

    app.dependency_overrides[get_db] = _fake_db

    try:
        client = TestClient(app)

        response = client.get(
            "/api/v1/audio",
            params={
                "limit": 20,
                "offset": 10,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured == {
        "limit": 20,
        "offset": 10,
    }

    payload = response.json()

    assert len(payload) == 2

    assert payload[0]["id"] == str(first_id)
    assert payload[0]["original_filename"] == "lecture-2.wav"
    assert payload[0]["duration_ms"] == 120_000
    assert payload[0]["status"] == "ready"

    assert payload[1]["id"] == str(second_id)
    assert payload[1]["original_filename"] == "lecture-1.wav"


def test_list_audio_rejects_invalid_pagination() -> None:
    app.dependency_overrides[get_db] = _fake_db

    try:
        client = TestClient(app)

        too_large = client.get(
            "/api/v1/audio",
            params={"limit": 101},
        )
        negative_offset = client.get(
            "/api/v1/audio",
            params={"offset": -1},
        )
    finally:
        app.dependency_overrides.clear()

    assert too_large.status_code == 422
    assert negative_offset.status_code == 422