from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy import Select, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.core.logging import get_logger, log_event
from app.models import Product, Role, User
from app.services.forecast_service import ForecastService
from app.services.import_service import GenerateDemoPayload, ImportService
from ml.features import FEATURE_NAMES, MAX_LAG, build_feature_vector, normalize_history_rows

IngestEntity = Literal["sales", "purchases"]

DEFAULT_PRODUCTS = ["AI_92", "AI_95", "DT_S", "DT_W"]
DEFAULT_HORIZONS = [1, 7, 30]

logger = get_logger("app.pipeline")


def ingest_internal_sales_daily(
    *,
    source_name: str = "airflow_sales_inbox",
    settings: Settings | None = None,
) -> dict[str, Any]:
    return _run_ingest_job(entity_type="sales", source_name=source_name, settings=settings)


def ingest_internal_purchases_daily(
    *,
    source_name: str = "airflow_purchases_inbox",
    settings: Settings | None = None,
) -> dict[str, Any]:
    return _run_ingest_job(entity_type="purchases", source_name=source_name, settings=settings)


def generate_demo_data(
    *,
    start_date: date,
    end_date: date,
    products: list[str] | None = None,
    seed: int = 42,
    replace_existing: bool = False,
    settings: Settings | None = None,
) -> dict[str, Any]:
    cfg = settings or get_settings()
    normalized_products = products or DEFAULT_PRODUCTS
    run_id = str(uuid4())

    with SessionLocal() as session:
        import_service = ImportService(session, settings=cfg)
        admin_user_id = _get_admin_user_id(session)
        job = import_service.create_job(
            entity_type="historical_data",
            source_type="generated",
            file_name=None,
            started_by=admin_user_id,
        )
        import_service.process_generate_demo_job(
            job_id=job.id,
            payload=GenerateDemoPayload(
                start_date=start_date,
                end_date=end_date,
                products=normalized_products,
                seed=seed,
                replace_existing=replace_existing,
            ),
        )

        session.refresh(job)
        result = {
            "run_id": run_id,
            "job_id": str(job.id),
            "status": job.status,
            "rows_total": job.rows_total,
            "rows_success": job.rows_success,
            "rows_failed": job.rows_failed,
            "error_report_path": job.error_report_path,
            "products": normalized_products,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "seed": seed,
            "replace_existing": replace_existing,
        }

    log_event(logger, "pipeline_generate_demo_data", **result)
    return result


def build_feature_store_daily(
    *,
    run_date: date | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    cfg = settings or get_settings()
    run_id = str(uuid4())
    effective_date = run_date or datetime.now(UTC).date()

    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT
                  p.code AS product_code,
                  v.date::date AS date,
                  v.volume_liters,
                  v.avg_retail_price_rub,
                  v.avg_purchase_price_rub,
                  v.gross_margin_rub_per_liter
                FROM vw_margin_daily v
                JOIN products p ON p.id = v.product_id
                WHERE p.is_active = TRUE
                ORDER BY p.code, v.date
                """
            )
        ).mappings()

        grouped_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped_rows[str(row["product_code"])].append(dict(row))

    feature_rows: list[dict[str, Any]] = []
    for product_code, product_rows in grouped_rows.items():
        history_points = normalize_history_rows(product_rows)
        if len(history_points) <= MAX_LAG:
            continue

        for index in range(MAX_LAG, len(history_points) - 1):
            vector = build_feature_vector(history_points, index)
            payload = {
                "product_code": product_code,
                "as_of_date": history_points[index].day.isoformat(),
                "target_date": history_points[index + 1].day.isoformat(),
                "target_volume_liters": round(history_points[index + 1].volume_liters, 6),
            }
            for feature_name, feature_value in zip(FEATURE_NAMES, vector, strict=True):
                payload[feature_name] = round(float(feature_value), 6)
            feature_rows.append(payload)

    output_dir = Path(cfg.feature_store_dir) / effective_date.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "features_daily.csv"

    fieldnames = [
        "product_code",
        "as_of_date",
        "target_date",
        "target_volume_liters",
        *FEATURE_NAMES,
    ]
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        if feature_rows:
            writer.writerows(feature_rows)

    result = {
        "run_id": run_id,
        "status": "success",
        "feature_rows": len(feature_rows),
        "products_covered": sorted({row["product_code"] for row in feature_rows}),
        "output_path": str(output_path),
    }
    log_event(logger, "pipeline_build_feature_store", **result)
    return result


def train_models_weekly(
    *,
    window_type: Literal["rolling", "expanding"] = "rolling",
    product_codes: list[str] | None = None,
    horizons: list[int] | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    cfg = settings or get_settings()
    run_id = str(uuid4())

    with SessionLocal() as session:
        forecast_service = ForecastService(session=session, settings=cfg)
        active_codes = _resolve_active_product_codes(session, product_codes)
        horizon_values = horizons or DEFAULT_HORIZONS

        outcomes: list[dict[str, Any]] = []
        for product_code in active_codes:
            for horizon in horizon_values:
                entry: dict[str, Any] = {
                    "product_code": product_code,
                    "horizon_days": horizon,
                    "window_type": window_type,
                }
                try:
                    response = forecast_service.run_backtest(
                        product_code=product_code,
                        horizon_days=horizon,
                        window_type=window_type,
                    )
                    entry["status"] = "success"
                    entry["model_type"] = response.data["model_type"]
                    entry["model_version"] = response.data["model_version"]
                    entry["smape"] = response.data["metrics"]["smape"]
                except ValueError as exc:
                    entry["status"] = "skipped"
                    entry["reason"] = str(exc)
                outcomes.append(entry)

    success_count = len([item for item in outcomes if item["status"] == "success"])
    result = {
        "run_id": run_id,
        "status": "success",
        "window_type": window_type,
        "products": active_codes,
        "horizons": horizon_values,
        "total_runs": len(outcomes),
        "success_runs": success_count,
        "skipped_runs": len(outcomes) - success_count,
        "runs": outcomes,
    }
    log_event(
        logger,
        "pipeline_train_models_weekly",
        run_id=run_id,
        total_runs=result["total_runs"],
        success_runs=result["success_runs"],
        skipped_runs=result["skipped_runs"],
    )
    return result


def ingest_external_indicators_daily(
    *,
    provider: str = "stub",
    settings: Settings | None = None,
) -> dict[str, Any]:
    cfg = settings or get_settings()
    run_id = str(uuid4())
    timestamp = datetime.now(UTC)

    output_dir = Path(cfg.news_index_dir) / "external_indicators_stub"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"heartbeat_{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"

    payload = {
        "run_id": run_id,
        "provider": provider,
        "status": "stub_ok",
        "message": "Phase 7 stub: external indicators ingestion is disabled.",
        "generated_at": timestamp.isoformat(),
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "run_id": run_id,
        "status": "success",
        "provider": provider,
        "output_path": str(output_path),
    }
    log_event(logger, "pipeline_ingest_external_indicators", **result)
    return result


def _run_ingest_job(
    *,
    entity_type: IngestEntity,
    source_name: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    cfg = settings or get_settings()
    run_id = str(uuid4())
    inbox_dir = Path(
        cfg.pipeline_sales_inbox_dir if entity_type == "sales" else cfg.pipeline_purchases_inbox_dir
    )
    archive_root = Path(cfg.pipeline_inbox_archive_dir)
    inbox_dir.mkdir(parents=True, exist_ok=True)
    archive_root.mkdir(parents=True, exist_ok=True)

    files = sorted(
        [
            path
            for path in inbox_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".csv", ".xlsx"}
        ],
        key=lambda item: item.name,
    )

    processed: list[dict[str, Any]] = []
    with SessionLocal() as session:
        import_service = ImportService(session=session, settings=cfg)
        admin_user_id = _get_admin_user_id(session)

        for path in files:
            job = import_service.create_job(
                entity_type=entity_type,
                source_type=path.suffix.lower().lstrip("."),
                file_name=path.name,
                started_by=admin_user_id,
            )
            import_service.process_file_job(
                job_id=job.id,
                entity_type=entity_type,
                file_name=path.name,
                file_bytes=path.read_bytes(),
                source_name=source_name,
            )
            session.refresh(job)

            archived_to = _archive_file(
                source_path=path,
                entity_type=entity_type,
                status=job.status,
                archive_root=archive_root,
            )
            entry = {
                "file_name": path.name,
                "job_id": str(job.id),
                "status": job.status,
                "rows_total": job.rows_total,
                "rows_success": job.rows_success,
                "rows_failed": job.rows_failed,
                "error_report_path": job.error_report_path,
                "archived_to": str(archived_to),
            }
            processed.append(entry)
            log_event(logger, "pipeline_ingest_file", entity_type=entity_type, **entry)

    status = "success" if processed else "noop"
    result = {
        "run_id": run_id,
        "entity_type": entity_type,
        "status": status,
        "files_seen": len(files),
        "files_processed": len(processed),
        "jobs": processed,
    }
    log_event(logger, "pipeline_ingest_summary", **result)
    return result


def _archive_file(
    *,
    source_path: Path,
    entity_type: IngestEntity,
    status: str,
    archive_root: Path,
) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    destination_dir = archive_root / entity_type / status
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination = destination_dir / source_path.name
    if destination.exists():
        destination = destination_dir / f"{source_path.stem}_{timestamp}{source_path.suffix}"
    source_path.rename(destination)
    return destination


def _get_admin_user_id(session: Session) -> UUID:
    statement: Select[tuple[User]] = (
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(Role.slug == "admin", User.is_active.is_(True))
        .order_by(User.created_at.asc())
        .limit(1)
    )
    admin = session.scalar(statement)
    if admin is None:
        raise RuntimeError("Active admin user is required for pipeline operations")
    return admin.id


def _resolve_active_product_codes(
    session: Session,
    requested_codes: list[str] | None,
) -> list[str]:
    if requested_codes:
        return [code.strip().upper() for code in requested_codes]

    statement: Select[tuple[Product]] = (
        select(Product)
        .where(Product.is_active.is_(True))
        .order_by(Product.code.asc())
    )
    return [item.code for item in session.scalars(statement)]
