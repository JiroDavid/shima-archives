from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unimplemented_endpoint_returns_501() -> None:
    response = client.get("/api/v1/vod/123/chat")
    assert response.status_code == 501
