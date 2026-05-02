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
    assert "llm_provider" in payload["data"]
    assert "llm_provider_mode" in payload["data"]
    assert "llm_active" in payload["data"]
    assert "cloud_configured" in payload["data"]
    assert "fallback_available" in payload["data"]
    assert "llm_api_key" not in payload["data"]
    assert "request_id" in payload["meta"]
