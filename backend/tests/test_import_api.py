from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.v1 import imports as imports_api
from app.dependencies.auth import get_auth_service
from app.dependencies.imports import get_import_service
from app.main import app
from app.services.auth_service import AuthenticatedUser


@dataclass(frozen=True)
class FakeUserRecord:
    user: AuthenticatedUser
    password: str


@dataclass
class FakeImportJob:
    id: UUID
    entity_type: str
    source_type: str
    file_name: str | None
    status: str
    rows_total: int
    rows_success: int
    rows_failed: int
    error_report_path: str | None
    started_by: UUID
    started_at: datetime
    finished_at: datetime | None


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

    def get_admin(self) -> AuthenticatedUser:
        return self._records[0].user


class FakeImportService:
    def __init__(self) -> None:
        self._jobs: dict[UUID, FakeImportJob] = {}

    def create_job(
        self,
        *,
        entity_type: str,
        source_type: str,
        file_name: str | None,
        started_by: UUID,
    ) -> FakeImportJob:
        job = FakeImportJob(
            id=uuid4(),
            entity_type=entity_type,
            source_type=source_type,
            file_name=file_name,
            status="queued",
            rows_total=0,
            rows_success=0,
            rows_failed=0,
            error_report_path=None,
            started_by=started_by,
            started_at=datetime.now(UTC),
            finished_at=None,
        )
        self._jobs[job.id] = job
        return job

    def list_jobs(
        self,
        *,
        entity_type: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ):
        rows = list(self._jobs.values())
        if entity_type:
            rows = [row for row in rows if row.entity_type == entity_type]
        if status:
            rows = [row for row in rows if row.status == status]
        return sorted(rows, key=lambda item: item.started_at, reverse=True)[:limit]

    def get_job(self, *, job_id: UUID):
        return self._jobs.get(job_id)


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def _setup_overrides(fake_auth: FakeAuthService, fake_import: FakeImportService) -> None:
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_import_service] = lambda: fake_import


def _cleanup_overrides() -> None:
    app.dependency_overrides.pop(get_auth_service, None)
    app.dependency_overrides.pop(get_import_service, None)


def test_upload_sales_returns_queued_job_for_admin(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    _setup_overrides(fake_auth, fake_import)
    monkeypatch.setattr(imports_api, "_process_file_job_in_background", lambda **_: None)

    client = TestClient(app)
    admin_token = _login(client, "admin@fuelsight.local", "admin12345")

    response = client.post(
        "/api/v1/import/sales",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={
            "file": (
                "sales.csv",
                "date,product_code,volume_liters,revenue_rub,avg_retail_price_rub\n2026-03-01,AI_95,1000,58000,58",
                "text/csv",
            )
        },
    )

    _cleanup_overrides()

    assert response.status_code == 202
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["entity_type"] == "sales"
    assert payload["data"]["status"] == "queued"


def test_upload_sales_returns_403_for_analyst(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    _setup_overrides(fake_auth, fake_import)
    monkeypatch.setattr(imports_api, "_process_file_job_in_background", lambda **_: None)

    client = TestClient(app)
    analyst_token = _login(client, "analyst@fuelsight.local", "analyst12345")

    response = client.post(
        "/api/v1/import/sales",
        headers={"Authorization": f"Bearer {analyst_token}"},
        files={
            "file": (
                "sales.csv",
                "date,product_code,volume_liters,revenue_rub,avg_retail_price_rub\n2026-03-01,AI_95,1000,58000,58",
                "text/csv",
            )
        },
    )

    _cleanup_overrides()

    assert response.status_code == 403


def test_generate_and_jobs_endpoints(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    _setup_overrides(fake_auth, fake_import)
    monkeypatch.setattr(imports_api, "_process_file_job_in_background", lambda **_: None)
    monkeypatch.setattr(imports_api, "_process_generate_demo_job_in_background", lambda **_: None)

    client = TestClient(app)
    admin_token = _login(client, "admin@fuelsight.local", "admin12345")

    generate_response = client.post(
        "/api/v1/import/generate-demo",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "products": ["AI_92", "AI_95", "DT_S", "DT_W"],
            "seed": 42,
            "replace_existing": False,
        },
    )

    assert generate_response.status_code == 202
    job_id = generate_response.json()["data"]["job_id"]

    list_response = client.get(
        "/api/v1/import/jobs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_response.status_code == 200
    rows = list_response.json()["data"]
    assert len(rows) == 1
    assert rows[0]["id"] == job_id
    assert rows[0]["entity_type"] == "historical_data"

    details_response = client.get(
        f"/api/v1/import/jobs/{job_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    _cleanup_overrides()

    assert details_response.status_code == 200
    details = details_response.json()["data"]
    assert details["id"] == job_id
    assert details["status"] == "queued"
    assert details["started_by"] == str(fake_auth.get_admin().id)
