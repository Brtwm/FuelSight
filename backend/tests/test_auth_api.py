from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.responses import envelope, request_meta
from app.dependencies.auth import get_auth_service, require_roles
from app.main import app
from app.services.auth_service import AuthenticatedUser

TEST_ADMIN_ROUTE = "/api/v1/_test/admin-only"


@dataclass(frozen=True)
class FakeUserRecord:
    user: AuthenticatedUser
    password: str


class FakeAuthService:
    def __init__(self) -> None:
        self._records = [
            FakeUserRecord(
                user=AuthenticatedUser(
                    id=uuid4(),
                    email="admin@fuelsight.local",
                    role="admin",
                    display_name="FuelSight Admin",
                    is_active=True,
                ),
                password="admin12345",
            ),
            FakeUserRecord(
                user=AuthenticatedUser(
                    id=uuid4(),
                    email="analyst@fuelsight.local",
                    role="analyst",
                    display_name="FuelSight Analyst",
                    is_active=True,
                ),
                password="analyst12345",
            ),
        ]

    def authenticate(self, email: str, password: str) -> AuthenticatedUser | None:
        for record in self._records:
            if record.user.email == email and record.password == password:
                return record.user
        return None

    def get_user_by_id(self, user_id: UUID) -> AuthenticatedUser | None:
        for record in self._records:
            if record.user.id == user_id:
                return record.user
        return None


def _register_admin_test_route() -> None:
    existing_paths = {route.path for route in app.router.routes}
    if TEST_ADMIN_ROUTE in existing_paths:
        return

    router = APIRouter()

    @router.get("/_test/admin-only")
    def admin_only(
        request: Request,
        _: AuthenticatedUser = Depends(require_roles("admin")),
    ) -> dict:
        return envelope(data={"ok": True}, error=None, meta=request_meta(request))

    app.include_router(router, prefix="/api/v1")


def _override_auth_service(fake_service: FakeAuthService) -> None:
    app.dependency_overrides[get_auth_service] = lambda: fake_service


def _clear_overrides() -> None:
    app.dependency_overrides.pop(get_auth_service, None)


def test_login_success_returns_access_token_and_cookie() -> None:
    fake_service = FakeAuthService()
    _override_auth_service(fake_service)
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@fuelsight.local", "password": "admin12345"},
    )

    _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["token_type"] == "bearer"
    assert payload["data"]["user"]["role"] == "admin"
    cookie_name = get_settings().auth_refresh_cookie_name
    assert cookie_name in response.cookies


def test_login_invalid_credentials_returns_401() -> None:
    fake_service = FakeAuthService()
    _override_auth_service(fake_service)
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@fuelsight.local", "password": "wrong-password"},
    )

    _clear_overrides()

    assert response.status_code == 401
    payload = response.json()
    assert payload["error"]["code"] == "invalid_credentials"


def test_me_returns_profile_for_valid_access_token() -> None:
    fake_service = FakeAuthService()
    _override_auth_service(fake_service)
    client = TestClient(app)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@fuelsight.local", "password": "analyst12345"},
    )
    access_token = login_response.json()["data"]["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["email"] == "analyst@fuelsight.local"
    assert payload["data"]["role"] == "analyst"


def test_refresh_returns_new_access_token_with_cookie() -> None:
    fake_service = FakeAuthService()
    _override_auth_service(fake_service)
    client = TestClient(app)

    client.post(
        "/api/v1/auth/login",
        json={"email": "admin@fuelsight.local", "password": "admin12345"},
    )
    response = client.post("/api/v1/auth/refresh")

    _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["access_token"]


def test_refresh_without_cookie_returns_401() -> None:
    fake_service = FakeAuthService()
    _override_auth_service(fake_service)
    client = TestClient(app)

    response = client.post("/api/v1/auth/refresh")

    _clear_overrides()

    assert response.status_code == 401
    payload = response.json()
    assert payload["error"]["code"] == "invalid_refresh_token"


def test_logout_clears_refresh_cookie() -> None:
    fake_service = FakeAuthService()
    _override_auth_service(fake_service)
    client = TestClient(app)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@fuelsight.local", "password": "admin12345"},
    )
    access_token = login_response.json()["data"]["access_token"]

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    _clear_overrides()

    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    assert "Max-Age=0" in set_cookie


def test_require_roles_returns_403_for_analyst_on_admin_route() -> None:
    _register_admin_test_route()
    fake_service = FakeAuthService()
    _override_auth_service(fake_service)
    client = TestClient(app)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@fuelsight.local", "password": "analyst12345"},
    )
    access_token = login_response.json()["data"]["access_token"]
    response = client.get(
        TEST_ADMIN_ROUTE,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    _clear_overrides()

    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "http_error"
