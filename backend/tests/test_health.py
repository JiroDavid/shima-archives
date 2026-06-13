from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_channel_endpoint_registered_but_stubbed() -> None:
    response = client.get("/api/v1/channel/yugi2x")
    assert response.status_code == 501
