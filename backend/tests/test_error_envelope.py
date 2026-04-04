from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.main import app

TEST_VALIDATION_PATH = "/api/v1/_test/validation"
TEST_ERROR_PATH = "/api/v1/_test/error"


def _register_test_routes() -> None:
    existing_paths = {route.path for route in app.router.routes}
    if TEST_VALIDATION_PATH in existing_paths and TEST_ERROR_PATH in existing_paths:
        return

    router = APIRouter()

    @router.get("/_test/validation")
    def validation_endpoint(limit: int) -> dict[str, int]:
        return {"limit": limit}

    @router.get("/_test/error")
    def error_endpoint() -> dict[str, bool]:
        raise RuntimeError("boom")

    app.include_router(router, prefix="/api/v1")


def test_404_uses_envelope_contract() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/not-found")

    assert response.status_code == 404
    payload = response.json()
    assert set(payload.keys()) == {"data", "error", "meta"}
    assert payload["data"] is None
    assert payload["error"]["code"] == "http_error"
    assert payload["error"]["details"]["status_code"] == 404
    assert "request_id" in payload["meta"]


def test_422_uses_validation_error_envelope() -> None:
    _register_test_routes()
    client = TestClient(app)
    response = client.get(TEST_VALIDATION_PATH, params={"limit": "invalid"})

    assert response.status_code == 422
    payload = response.json()
    assert set(payload.keys()) == {"data", "error", "meta"}
    assert payload["data"] is None
    assert payload["error"]["code"] == "validation_error"
    assert isinstance(payload["error"]["details"]["errors"], list)
    assert "request_id" in payload["meta"]


def test_500_uses_internal_error_envelope() -> None:
    _register_test_routes()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get(TEST_ERROR_PATH)

    assert response.status_code == 500
    payload = response.json()
    assert set(payload.keys()) == {"data", "error", "meta"}
    assert payload["data"] is None
    assert payload["error"]["code"] == "internal_error"
    assert payload["error"]["details"]["exception"] == "RuntimeError"
    assert "request_id" in payload["meta"]
