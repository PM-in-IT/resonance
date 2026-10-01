from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_page_and_static_assets_are_served() -> None:
    client = TestClient(app)

    page = client.get("/")
    stylesheet = client.get("/static/styles.css")
    script = client.get("/static/app.js")

    assert page.status_code == 200
    assert "Audio intake" in page.text
    assert stylesheet.status_code == 200
    assert script.status_code == 200
