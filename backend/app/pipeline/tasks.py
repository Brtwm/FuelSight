from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy import Select, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.core.logging import get_logger, log_event
from app.models import Product, Role, User
from app.repositories import ExternalIndicatorsRepository
from app.services.external_indicators_service import (
    DEFAULT_EXTERNAL_INDICATORS,
    ExternalIndicatorsService,
)
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
        rows = list(
            session.execute(
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
        )
        grouped_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped_rows[str(row["product_code"])].append(dict(row))

        window_start: date | None = None
        window_end: date | None = None
        if rows:
            window_start = min(item["date"] for item in rows)
            window_end = max(item["date"] for item in rows)

        coverage_ratio = 0.0
        fallback_ratio = 1.0
        provider_mode_counts: dict[str, int] = {}
        dominant_provider_mode: str | None = None
        if window_start is not None and window_end is not None:
            indicators_repo = ExternalIndicatorsRepository(session)
            raw_points = indicators_repo.get_points_with_mode(
                start_date=window_start,
                end_date=window_end,
                indicator_codes=DEFAULT_EXTERNAL_INDICATORS,
            )
            indicator_values, indicator_modes, coverage_ratio, fallback_ratio, provider_mode_counts = (
                _build_indicator_context(
                    start_date=window_start,
                    end_date=window_end,
                    raw_points=raw_points,
                    indicator_codes=DEFAULT_EXTERNAL_INDICATORS,
                )
            )
            dominant_provider_mode = _dominant_provider_mode(provider_mode_counts)
            _enrich_rows_with_context(
                grouped_rows=grouped_rows,
                indicator_values=indicator_values,
                indicator_modes=indicator_modes,
            )

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

    feature_sources = [
        "lag_rolling",
        "calendar",
        "price_margin",
        "external_indicators",
        "event_pressure",
        "cross_product_context",
    ]
    external_quality_status, external_quality_reasons = _classify_external_context_quality(
        coverage_ratio=coverage_ratio,
        fallback_ratio=fallback_ratio,
    )
    manifest_path = output_dir / f"feature_refresh_manifest_{run_id}.json"
    manifest_payload = {
        "run_id": run_id,
        "run_date": effective_date.isoformat(),
        "status": "ok" if feature_rows and external_quality_status == "ok" else "warning",
        "quality_status": external_quality_status,
        "reasons": external_quality_reasons,
        "window": {
            "start_date": min((row["as_of_date"] for row in feature_rows), default=None),
            "end_date": max((row["as_of_date"] for row in feature_rows), default=None),
        },
        "feature_rows": len(feature_rows),
        "products_covered": sorted({row["product_code"] for row in feature_rows}),
        "feature_names": FEATURE_NAMES,
        "feature_sources": feature_sources,
        "coverage_ratio": round(coverage_ratio, 6),
        "fallback_ratio": round(fallback_ratio, 6),
        "provider_mode_counts": provider_mode_counts,
        "provider_mode": dominant_provider_mode,
        "external_context": {
            "quality_status": external_quality_status,
            "reasons": external_quality_reasons,
            "coverage_ratio": round(coverage_ratio, 6),
            "fallback_ratio": round(fallback_ratio, 6),
            "provider_mode": dominant_provider_mode,
            "provider_mode_counts": provider_mode_counts,
            "manifest_run_date": effective_date.isoformat(),
        },
        "output_path": str(output_path),
    }
    manifest_path.write_text(
        json.dumps(manifest_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = {
        "run_id": run_id,
        "status": external_quality_status if feature_rows else "warning",
        "quality_status": external_quality_status,
        "reasons": external_quality_reasons,
        "run_date": effective_date.isoformat(),
        "feature_rows": len(feature_rows),
        "products_covered": sorted({row["product_code"] for row in feature_rows}),
        "feature_sources": feature_sources,
        "coverage_ratio": round(coverage_ratio, 6),
        "fallback_ratio": round(fallback_ratio, 6),
        "provider_mode_counts": provider_mode_counts,
        "provider_mode": dominant_provider_mode,
        "output_path": str(output_path),
        "manifest_path": str(manifest_path),
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
    run_timestamp = datetime.now(UTC)
    feature_manifest = _load_latest_feature_refresh_manifest(cfg.feature_store_dir)
    feature_refresh_status, feature_refresh_reasons = _evaluate_feature_refresh_status(
        manifest=feature_manifest,
        now=run_timestamp,
    )

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
                    entry["model_freshness"] = response.data.get("model_freshness")
                    entry["retrain_status"] = response.data.get("retrain_status")
                except ValueError as exc:
                    entry["status"] = "skipped"
                    entry["reason"] = str(exc)
                outcomes.append(entry)

    success_count = len([item for item in outcomes if item["status"] == "success"])
    degraded_count = len(
        [
            item
            for item in outcomes
            if item.get("status") == "success" and item.get("retrain_status") in {"degraded", "failed"}
        ]
    )
    warning_count = len(
        [
            item
            for item in outcomes
            if item.get("status") == "success" and item.get("retrain_status") == "warning"
        ]
    )
    result_status = "success"
    if success_count == 0 or feature_refresh_status == "degraded" or degraded_count > 0:
        result_status = "degraded"
    elif feature_refresh_status == "warning" or warning_count > 0:
        result_status = "warning"

    manifests_root = Path(cfg.model_artifacts_dir) / "manifests"
    train_manifest_dir = manifests_root / "train_backtest"
    train_manifest_dir.mkdir(parents=True, exist_ok=True)
    train_manifest_path = train_manifest_dir / f"train_backtest_manifest_{run_id}.json"
    train_manifest = {
        "run_id": run_id,
        "run_date": run_timestamp.date().isoformat(),
        "status": result_status,
        "window_type": window_type,
        "products": active_codes,
        "horizons": horizon_values,
        "total_runs": len(outcomes),
        "success_runs": success_count,
        "skipped_runs": len(outcomes) - success_count,
        "feature_refresh": {
            "status": feature_refresh_status,
            "reasons": feature_refresh_reasons,
            "manifest_path": feature_manifest.get("manifest_path") if feature_manifest else None,
            "coverage_ratio": feature_manifest.get("coverage_ratio") if feature_manifest else None,
            "fallback_ratio": feature_manifest.get("fallback_ratio") if feature_manifest else None,
            "provider_mode": feature_manifest.get("provider_mode") if feature_manifest else None,
            "provider_mode_counts": feature_manifest.get("provider_mode_counts") if feature_manifest else None,
            "quality_status": feature_manifest.get("quality_status") if feature_manifest else None,
        },
        "runs": outcomes,
    }
    train_manifest_path.write_text(
        json.dumps(train_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    freshness_manifest_dir = manifests_root / "model_freshness"
    freshness_manifest_dir.mkdir(parents=True, exist_ok=True)
    freshness_manifest_path = freshness_manifest_dir / f"model_freshness_manifest_{run_id}.json"
    freshness_manifest = {
        "run_id": run_id,
        "run_date": run_timestamp.date().isoformat(),
        "status": result_status,
        "feature_refresh_status": feature_refresh_status,
        "feature_refresh_reasons": feature_refresh_reasons,
        "external_context_quality": {
            "status": feature_manifest.get("quality_status") if feature_manifest else None,
            "coverage_ratio": feature_manifest.get("coverage_ratio") if feature_manifest else None,
            "fallback_ratio": feature_manifest.get("fallback_ratio") if feature_manifest else None,
            "provider_mode": feature_manifest.get("provider_mode") if feature_manifest else None,
            "provider_mode_counts": feature_manifest.get("provider_mode_counts") if feature_manifest else None,
            "manifest_run_date": feature_manifest.get("run_date") if feature_manifest else None,
            "reasons": feature_manifest.get("reasons") if feature_manifest else None,
        },
        "models": [
            {
                "product_code": item["product_code"],
                "horizon_days": item["horizon_days"],
                "model_version": item.get("model_version"),
                "model_freshness": item.get("model_freshness"),
                "retrain_status": item.get("retrain_status"),
            }
            for item in outcomes
            if item.get("status") == "success"
        ],
    }
    freshness_manifest_path.write_text(
        json.dumps(freshness_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = {
        "run_id": run_id,
        "status": result_status,
        "window_type": window_type,
        "products": active_codes,
        "horizons": horizon_values,
        "total_runs": len(outcomes),
        "success_runs": success_count,
        "skipped_runs": len(outcomes) - success_count,
        "feature_refresh_status": feature_refresh_status,
        "feature_refresh_reasons": feature_refresh_reasons,
        "feature_refresh_manifest_path": feature_manifest.get("manifest_path") if feature_manifest else None,
        "train_backtest_manifest_path": str(train_manifest_path),
        "model_freshness_manifest_path": str(freshness_manifest_path),
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
    provider: str = "auto",
    run_date: date | None = None,
    lookback_days: int = 365,
    settings: Settings | None = None,
) -> dict[str, Any]:
    cfg = settings or get_settings()
    normalized_provider = provider.strip().lower()
    if normalized_provider not in {"auto", "live", "cached", "manual_snapshot"}:
        raise ValueError("provider must be one of auto, live, cached, manual_snapshot")

    effective_run_date = run_date or datetime.now(UTC).date()
    effective_lookback_days = max(lookback_days, 1)
    start_date = effective_run_date - timedelta(days=effective_lookback_days - 1)

    prefer_live = normalized_provider in {"auto", "live"}
    with SessionLocal() as session:
        service = ExternalIndicatorsService(session=session, settings=cfg)
        ingest_result = service.ingest_range(
            start_date=start_date,
            end_date=effective_run_date,
            indicator_codes=DEFAULT_EXTERNAL_INDICATORS,
            prefer_live=prefer_live,
            run_date=effective_run_date,
        )

    manifest_dir = Path(cfg.external_cache_dir) / "manifests" / effective_run_date.isoformat()
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"external_indicators_manifest_{ingest_result.run_id}.json"
    manifest_payload = ingest_result.to_manifest(manifest_path=str(manifest_path))
    manifest_payload["provider_request"] = normalized_provider
    manifest_payload["lookback_days"] = effective_lookback_days
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    quality_status = getattr(ingest_result, "quality_status", None)
    reasons = getattr(ingest_result, "reasons", None)
    if not isinstance(quality_status, str) or quality_status not in {"ok", "warning", "degraded", "failed"}:
        raw_coverage_ratio = getattr(ingest_result, "coverage_ratio", None)
        raw_fallback_ratio = getattr(ingest_result, "fallback_ratio", None)
        coverage_ratio_value = float(raw_coverage_ratio) if raw_coverage_ratio is not None else 0.0
        fallback_ratio_value = float(raw_fallback_ratio) if raw_fallback_ratio is not None else 1.0
        quality_status, fallback_reasons = _classify_external_context_quality(
            coverage_ratio=coverage_ratio_value,
            fallback_ratio=fallback_ratio_value,
        )
        if not isinstance(reasons, list):
            reasons = fallback_reasons

    result = {
        "run_id": ingest_result.run_id,
        "status": quality_status,
        "quality_status": quality_status,
        "reasons": reasons if isinstance(reasons, list) else [],
        "provider": normalized_provider,
        "run_date": effective_run_date.isoformat(),
        "window": {
            "start_date": start_date.isoformat(),
            "end_date": effective_run_date.isoformat(),
            "lookback_days": effective_lookback_days,
        },
        "expected_points": ingest_result.expected_points,
        "written_points": ingest_result.written_points,
        "coverage_ratio": ingest_result.coverage_ratio,
        "fallback_ratio": ingest_result.fallback_ratio,
        "provider_mode_counts": ingest_result.provider_mode_counts,
        "indicator_coverage": manifest_payload["indicator_coverage"],
        "manifest_path": str(manifest_path),
        "cache_dir": ingest_result.cache_dir,
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


def _build_indicator_context(
    *,
    start_date: date,
    end_date: date,
    raw_points: dict[str, list[dict[str, Any]]],
    indicator_codes: list[str],
) -> tuple[dict[str, dict[date, float]], dict[str, dict[date, str]], float, float, dict[str, int]]:
    dates = _date_points(start_date, end_date)
    values: dict[str, dict[date, float]] = {}
    modes: dict[str, dict[date, str]] = {}
    mode_counter: Counter[str] = Counter()
    actual_points = 0
    fallback_points = 0

    for code in indicator_codes:
        points = raw_points.get(code, [])
        by_date_value: dict[date, float] = {}
        by_date_mode: dict[date, str] = {}
        for point in points:
            point_date = point.get("indicator_date")
            if not isinstance(point_date, date):
                continue
            by_date_value[point_date] = float(point.get("value_numeric") or 0.0)
            point_mode = str(point.get("provider_mode") or "manual_snapshot").strip().lower()
            by_date_mode[point_date] = point_mode
            mode_counter[point_mode] += 1
            actual_points += 1
            if point_mode != "live":
                fallback_points += 1

        code_values: dict[date, float] = {}
        code_modes: dict[date, str] = {}
        last_value: float | None = None
        last_mode = "manual_snapshot"
        for current_date in dates:
            if current_date in by_date_value:
                last_value = by_date_value[current_date]
                last_mode = by_date_mode.get(current_date, last_mode)
            code_values[current_date] = 0.0 if last_value is None else last_value
            code_modes[current_date] = last_mode

        values[code] = code_values
        modes[code] = code_modes

    expected_points = max(len(indicator_codes) * len(dates), 1)
    coverage_ratio = actual_points / expected_points
    fallback_ratio = (fallback_points / actual_points) if actual_points > 0 else 1.0
    return values, modes, coverage_ratio, fallback_ratio, dict(mode_counter)


def _enrich_rows_with_context(
    *,
    grouped_rows: dict[str, list[dict[str, Any]]],
    indicator_values: dict[str, dict[date, float]],
    indicator_modes: dict[str, dict[date, str]],
) -> None:
    all_rows = [row for rows in grouped_rows.values() for row in rows]
    by_group_volume: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for row in all_rows:
        group = _product_group(str(row.get("product_code", "")))
        day = row["date"]
        by_group_volume[group][day] += float(row.get("volume_liters") or 0.0)

    for product_code, rows in grouped_rows.items():
        group = _product_group(product_code)
        rows.sort(key=lambda item: item["date"])
        for row in rows:
            day = row["date"]
            group_volume = by_group_volume[group].get(day, 0.0)
            product_volume = float(row.get("volume_liters") or 0.0)
            row["product_share_in_group"] = (product_volume / group_volume) if group_volume > 0 else 0.0
            row["group_volume_liters"] = group_volume
            row["group_volume_lag_1"] = by_group_volume[group].get(day - timedelta(days=1), group_volume)
            row["group_volume_lag_7"] = by_group_volume[group].get(
                day - timedelta(days=7),
                row["group_volume_lag_1"],
            )

            for indicator_code in DEFAULT_EXTERNAL_INDICATORS:
                row[indicator_code] = indicator_values.get(indicator_code, {}).get(day, 0.0)

            row["provider_mode"] = _dominant_provider_mode_for_day(day=day, indicator_modes=indicator_modes)


def _dominant_provider_mode_for_day(
    *,
    day: date,
    indicator_modes: dict[str, dict[date, str]],
) -> str:
    counter: Counter[str] = Counter()
    for code in DEFAULT_EXTERNAL_INDICATORS:
        mode = indicator_modes.get(code, {}).get(day)
        if not mode:
            continue
        counter[mode] += 1
    if not counter:
        return "manual_snapshot"
    return counter.most_common(1)[0][0]


def _date_points(start_date: date, end_date: date) -> list[date]:
    days = (end_date - start_date).days
    return [start_date + timedelta(days=index) for index in range(days + 1)]


def _product_group(product_code: str) -> str:
    normalized = product_code.strip().upper()
    if normalized.startswith("AI_"):
        return "gasoline"
    return "diesel"


def _dominant_provider_mode(mode_counts: dict[str, int]) -> str | None:
    if not mode_counts:
        return None
    return sorted(mode_counts.items(), key=lambda item: item[1], reverse=True)[0][0]


def _load_latest_feature_refresh_manifest(feature_store_dir: str) -> dict[str, Any] | None:
    root = Path(feature_store_dir)
    if not root.exists():
        return None
    manifests = sorted(
        root.glob("*/feature_refresh_manifest_*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not manifests:
        return None
    payload = json.loads(manifests[0].read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    payload["manifest_path"] = str(manifests[0])
    return payload


def _evaluate_feature_refresh_status(
    *,
    manifest: dict[str, Any] | None,
    now: datetime,
) -> tuple[str, list[str]]:
    if manifest is None:
        return "degraded", ["feature_refresh_manifest_missing"]

    reasons: list[str] = []
    coverage_ratio = float(manifest.get("coverage_ratio") or 0.0)
    fallback_ratio = float(manifest.get("fallback_ratio") or 1.0)
    run_date_raw = manifest.get("run_date")
    run_date = None
    if isinstance(run_date_raw, str):
        try:
            run_date = date.fromisoformat(run_date_raw)
        except ValueError:
            run_date = None
    age_days = 999
    if run_date is not None:
        age_days = (now.date() - run_date).days

    if age_days > 1:
        reasons.append(f"feature_manifest_stale_days={age_days}")
    base_quality_status, base_quality_reasons = _classify_external_context_quality(
        coverage_ratio=coverage_ratio,
        fallback_ratio=fallback_ratio,
    )
    reasons.extend(base_quality_reasons)

    if age_days <= 1 and coverage_ratio >= 0.95 and fallback_ratio <= 0.25:
        return "fresh", reasons
    if age_days <= 2 and base_quality_status in {"ok", "warning"}:
        return "warning", reasons
    return "degraded", reasons


def _classify_external_context_quality(
    *,
    coverage_ratio: float,
    fallback_ratio: float,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if coverage_ratio < 0.85:
        reasons.append(f"coverage_ratio={coverage_ratio:.3f}<0.85")
    elif coverage_ratio < 0.95:
        reasons.append(f"coverage_ratio={coverage_ratio:.3f}<0.95")
    if fallback_ratio > 0.5:
        reasons.append(f"fallback_ratio={fallback_ratio:.3f}>0.5")
    elif fallback_ratio > 0.25:
        reasons.append(f"fallback_ratio={fallback_ratio:.3f}>0.25")

    if coverage_ratio < 0.85 or fallback_ratio > 0.5:
        return "degraded", reasons
    if reasons:
        return "warning", reasons
    return "ok", reasons
