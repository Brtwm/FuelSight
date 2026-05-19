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
                    email="sales@fuelsight.local",
                    role="sales",
                    display_name="FuelSight Sales",
                    is_active=True,
                ),
                password="sales12345",
            ),
            FakeUserRecord(
                user=AuthenticatedUser(
                    id=uuid4(),
                    email="accounting@fuelsight.local",
                    role="accounting",
                    display_name="FuelSight Accounting",
                    is_active=True,
                ),
                password="accounting12345",
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
            FakeUserRecord(
                user=AuthenticatedUser(
                    id=uuid4(),
                    email="director@fuelsight.local",
                    role="director",
                    display_name="FuelSight Director",
                    is_active=True,
                ),
                password="director12345",
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
        entity_types: tuple[str, ...] | None = None,
        status: str | None = None,
        limit: int = 20,
    ):
        rows = list(self._jobs.values())
        if entity_type:
            rows = [row for row in rows if row.entity_type == entity_type]
        if entity_types:
            rows = [row for row in rows if row.entity_type in entity_types]
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


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _sales_file() -> dict[str, tuple[str, str, str]]:
    return {
        "file": (
            "sales.csv",
            "date,product_code,volume_liters,revenue_rub,avg_retail_price_rub\n2026-03-01,AI_95,1000,58000,58",
            "text/csv",
        )
    }


def _purchases_file() -> dict[str, tuple[str, str, str]]:
    return {
        "file": (
            "purchases.csv",
            "date,product_code,volume_liters,purchase_price_rub,supplier_name,logistics_cost_rub\n2026-03-01,AI_95,1000,52,Supplier,1000",
            "text/csv",
        )
    }


def _generate_demo_payload() -> dict[str, object]:
    return {
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "products": ["AI_92", "AI_95", "DT_S", "DT_W"],
        "seed": 42,
        "replace_existing": False,
    }


def _upload_sales(client: TestClient, token: str):
    return client.post(
        "/api/v1/import/sales",
        headers=_auth_headers(token),
        files=_sales_file(),
    )


def _upload_purchases(client: TestClient, token: str):
    return client.post(
        "/api/v1/import/purchases",
        headers=_auth_headers(token),
        files=_purchases_file(),
    )


def _generate_demo(client: TestClient, token: str):
    return client.post(
        "/api/v1/import/generate-demo",
        headers=_auth_headers(token),
        json=_generate_demo_payload(),
    )


def _list_jobs(client: TestClient, token: str, entity_type: str | None = None):
    params = {"entity_type": entity_type} if entity_type is not None else None
    return client.get(
        "/api/v1/import/jobs",
        headers=_auth_headers(token),
        params=params,
    )


def _get_job_details(client: TestClient, token: str, job_id: str):
    return client.get(
        f"/api/v1/import/jobs/{job_id}",
        headers=_auth_headers(token),
    )


def test_upload_sales_returns_queued_job_for_admin(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    _setup_overrides(fake_auth, fake_import)
    monkeypatch.setattr(imports_api, "_process_file_job_in_background", lambda **_: None)

    client = TestClient(app)
    admin_token = _login(client, "admin@fuelsight.local", "admin12345")

    response = _upload_sales(client, admin_token)

    _cleanup_overrides()

    assert response.status_code == 202
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["entity_type"] == "sales"
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["display_label"] == "sales"
    assert payload["data"]["provenance_mode"] == "manual_snapshot"
    assert payload["data"]["quality_status"] is None


def test_upload_sales_returns_403_for_analyst(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    _setup_overrides(fake_auth, fake_import)
    monkeypatch.setattr(imports_api, "_process_file_job_in_background", lambda **_: None)

    client = TestClient(app)
    analyst_token = _login(client, "analyst@fuelsight.local", "analyst12345")

    response = _upload_sales(client, analyst_token)

    _cleanup_overrides()

    assert response.status_code == 403


def test_upload_sales_rejects_empty_file(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    _setup_overrides(fake_auth, fake_import)
    monkeypatch.setattr(imports_api, "_process_file_job_in_background", lambda **_: None)

    client = TestClient(app)
    admin_token = _login(client, "admin@fuelsight.local", "admin12345")

    response = client.post(
        "/api/v1/import/sales",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("sales.csv", "", "text/csv")},
    )

    _cleanup_overrides()

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "Файл пустой"


def test_upload_sales_rejects_oversized_file(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    _setup_overrides(fake_auth, fake_import)
    monkeypatch.setattr(imports_api, "_process_file_job_in_background", lambda **_: None)
    monkeypatch.setattr(imports_api.settings, "import_max_upload_bytes", 8)

    client = TestClient(app)
    admin_token = _login(client, "admin@fuelsight.local", "admin12345")

    response = client.post(
        "/api/v1/import/sales",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("sales.csv", "123456789", "text/csv")},
    )

    _cleanup_overrides()

    assert response.status_code == 413
    payload = response.json()
    assert payload["error"]["code"] == "upload_too_large"
    assert "Файл слишком большой" in payload["error"]["message"]


def test_import_permission_matrix(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    _setup_overrides(fake_auth, fake_import)
    monkeypatch.setattr(imports_api, "_process_file_job_in_background", lambda **_: None)
    monkeypatch.setattr(imports_api, "_process_generate_demo_job_in_background", lambda **_: None)

    client = TestClient(app)
    tokens = {
        role: _login(client, f"{role}@fuelsight.local", f"{role}12345")
        for role in ("admin", "sales", "accounting", "analyst", "director")
    }

    admin_sales_response = _upload_sales(client, tokens["admin"])
    admin_purchases_response = _upload_purchases(client, tokens["admin"])
    admin_generate_response = _generate_demo(client, tokens["admin"])
    sales_response = _upload_sales(client, tokens["sales"])
    sales_purchases_response = _upload_purchases(client, tokens["sales"])
    sales_generate_response = _generate_demo(client, tokens["sales"])
    accounting_response = _upload_purchases(client, tokens["accounting"])
    accounting_sales_response = _upload_sales(client, tokens["accounting"])
    accounting_generate_response = _generate_demo(client, tokens["accounting"])
    analyst_sales_response = _upload_sales(client, tokens["analyst"])
    analyst_purchases_response = _upload_purchases(client, tokens["analyst"])
    analyst_generate_response = _generate_demo(client, tokens["analyst"])
    director_sales_response = _upload_sales(client, tokens["director"])
    director_purchases_response = _upload_purchases(client, tokens["director"])
    director_generate_response = _generate_demo(client, tokens["director"])

    _cleanup_overrides()

    assert admin_sales_response.status_code == 202
    assert admin_purchases_response.status_code == 202
    assert admin_generate_response.status_code == 202
    assert sales_response.status_code == 202
    assert sales_purchases_response.status_code == 403
    assert sales_generate_response.status_code == 403
    assert accounting_response.status_code == 202
    assert accounting_sales_response.status_code == 403
    assert accounting_generate_response.status_code == 403
    assert analyst_sales_response.status_code == 403
    assert analyst_purchases_response.status_code == 403
    assert analyst_generate_response.status_code == 403
    assert director_sales_response.status_code == 403
    assert director_purchases_response.status_code == 403
    assert director_generate_response.status_code == 403


def test_import_history_permissions_filter_by_role(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    _setup_overrides(fake_auth, fake_import)
    monkeypatch.setattr(imports_api, "_process_file_job_in_background", lambda **_: None)
    monkeypatch.setattr(imports_api, "_process_generate_demo_job_in_background", lambda **_: None)

    client = TestClient(app)
    admin_token = _login(client, "admin@fuelsight.local", "admin12345")
    sales_token = _login(client, "sales@fuelsight.local", "sales12345")
    accounting_token = _login(client, "accounting@fuelsight.local", "accounting12345")
    analyst_token = _login(client, "analyst@fuelsight.local", "analyst12345")
    director_token = _login(client, "director@fuelsight.local", "director12345")

    sales_job_id = _upload_sales(client, sales_token).json()["data"]["job_id"]
    purchases_job_id = _upload_purchases(client, accounting_token).json()["data"]["job_id"]
    demo_job_id = _generate_demo(client, admin_token).json()["data"]["job_id"]

    admin_list_response = _list_jobs(client, admin_token)
    analyst_list_response = _list_jobs(client, analyst_token)
    sales_list_response = _list_jobs(client, sales_token)
    accounting_list_response = _list_jobs(client, accounting_token)
    director_list_response = _list_jobs(client, director_token)
    sales_forbidden_filter_response = _list_jobs(client, sales_token, entity_type="purchases")
    accounting_forbidden_filter_response = _list_jobs(
        client,
        accounting_token,
        entity_type="sales",
    )

    admin_details_response = _get_job_details(client, admin_token, demo_job_id)
    analyst_details_response = _get_job_details(client, analyst_token, demo_job_id)
    sales_details_response = _get_job_details(client, sales_token, sales_job_id)
    sales_forbidden_details_response = _get_job_details(client, sales_token, purchases_job_id)
    accounting_details_response = _get_job_details(client, accounting_token, purchases_job_id)
    accounting_forbidden_details_response = _get_job_details(
        client,
        accounting_token,
        sales_job_id,
    )
    director_details_response = _get_job_details(client, director_token, sales_job_id)

    _cleanup_overrides()

    assert admin_list_response.status_code == 200
    assert {row["entity_type"] for row in admin_list_response.json()["data"]} == {
        "sales",
        "purchases",
        "historical_data",
    }
    assert analyst_list_response.status_code == 200
    assert {row["entity_type"] for row in analyst_list_response.json()["data"]} == {
        "sales",
        "purchases",
        "historical_data",
    }
    assert sales_list_response.status_code == 200
    assert [row["entity_type"] for row in sales_list_response.json()["data"]] == ["sales"]
    assert accounting_list_response.status_code == 200
    assert [row["entity_type"] for row in accounting_list_response.json()["data"]] == [
        "purchases"
    ]
    assert director_list_response.status_code == 403
    assert sales_forbidden_filter_response.status_code == 403
    assert accounting_forbidden_filter_response.status_code == 403

    assert admin_details_response.status_code == 200
    assert analyst_details_response.status_code == 200
    assert sales_details_response.status_code == 200
    assert sales_forbidden_details_response.status_code == 403
    assert accounting_details_response.status_code == 200
    assert accounting_forbidden_details_response.status_code == 403
    assert director_details_response.status_code == 403


def test_generate_and_jobs_endpoints(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    _setup_overrides(fake_auth, fake_import)
    monkeypatch.setattr(imports_api, "_process_file_job_in_background", lambda **_: None)
    monkeypatch.setattr(imports_api, "_process_generate_demo_job_in_background", lambda **_: None)

    client = TestClient(app)
    admin_token = _login(client, "admin@fuelsight.local", "admin12345")

    generate_response = _generate_demo(client, admin_token)

    assert generate_response.status_code == 202
    job_id = generate_response.json()["data"]["job_id"]
    generate_payload = generate_response.json()["data"]
    assert generate_payload["display_label"] == "initial_history"
    assert generate_payload["provenance_mode"] == "manual_snapshot"
    assert generate_payload["quality_status"] is None

    list_response = _list_jobs(client, admin_token)
    assert list_response.status_code == 200
    rows = list_response.json()["data"]
    assert len(rows) == 1
    assert rows[0]["id"] == job_id
    assert rows[0]["entity_type"] == "historical_data"
    assert rows[0]["display_label"] == "initial_history"
    assert rows[0]["provenance_mode"] == "manual_snapshot"
    assert rows[0]["quality_status"] is None

    details_response = _get_job_details(client, admin_token, job_id)

    _cleanup_overrides()

    assert details_response.status_code == 200
    details = details_response.json()["data"]
    assert details["id"] == job_id
    assert details["status"] == "queued"
    assert details["started_by"] == str(fake_auth.get_admin().id)
    assert details["display_label"] == "initial_history"
    assert details["provenance_mode"] == "manual_snapshot"
    assert details["quality_status"] is None
