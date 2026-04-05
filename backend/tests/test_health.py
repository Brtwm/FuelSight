from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_envelope() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"data", "error", "meta"}
    assert payload["error"] is None
    assert payload["data"]["ok"] is True
    assert isinstance(payload["data"]["enable_llm"], bool)
    assert "request_id" in payload["meta"]
