from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from app.schemas.backtests import BacktestMetrics, BacktestPayload
from app.schemas.chat import ChatAnswerPayload, CitationPayload
from app.schemas.forecasts import ForecastPayload, ForecastPoint, TrainingWindowPayload
from app.schemas.imports import ImportJobSummary
from app.schemas.news import NewsDigestPayload


def test_import_job_summary_supports_phase0_contract_fields() -> None:
    payload = ImportJobSummary(
        id=uuid4(),
        entity_type="historical_data",
        source_type="generated",
        file_name=None,
        status="completed",
        rows_total=100,
        rows_success=100,
        rows_failed=0,
        error_report_path=None,
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        display_label="initial_history",
        provenance_mode="manual_snapshot",
        quality_status="ok",
    )
    dumped = payload.model_dump(mode="json")
    assert dumped["display_label"] == "initial_history"
    assert dumped["provenance_mode"] == "manual_snapshot"
    assert dumped["quality_status"] == "ok"


def test_forecast_and_backtest_payloads_support_health_fields() -> None:
    training_window = TrainingWindowPayload(start_date=date(2026, 1, 1), end_date=date(2026, 3, 31))

    forecast = ForecastPayload(
        product_code="AI_95",
        horizon_days=7,
        model_type="catboost",
        model_status="active",
        scenario_name="base",
        forecast_points=[ForecastPoint(target_date=date(2026, 4, 10), y_hat=1.0, y_lo=0.9, y_hi=1.1)],
        drivers=["trend"],
        model_freshness="fresh",
        training_window=training_window,
        baseline_comparison={"seasonal_naive": {"smape": 5.1}},
        feature_sources=["lag", "calendar"],
        retrain_status="ok",
        provider_mode="cached",
    )
    assert forecast.model_dump(mode="json")["provider_mode"] == "cached"

    backtest = BacktestPayload(
        product_code="AI_95",
        horizon_days=7,
        model_type="catboost",
        window_type="rolling",
        metrics=BacktestMetrics(mae=1.0, rmse=2.0, smape=3.0),
        comparison={"catboost": BacktestMetrics(mae=1.0, rmse=2.0, smape=3.0)},
        trained_at=datetime.now(UTC),
        model_freshness="warning",
        training_window=training_window,
        baseline_comparison={"seasonal_naive": {"smape": 5.3}},
        feature_sources=["lag"],
        retrain_status="warning",
        provider_mode="manual_snapshot",
    )
    assert backtest.model_dump(mode="json")["provider_mode"] == "manual_snapshot"


def test_news_and_chat_payloads_support_provider_contract_fields() -> None:
    digest = NewsDigestPayload(
        digest_date=date(2026, 4, 8),
        period_type="daily",
        summary_text="summary",
        bullet_points=["a"],
        source_ids=["id1"],
        llm_mode="off",
        provider_mode="cached",
        news_freshness="warning",
    )
    assert digest.model_dump(mode="json")["provider_mode"] == "cached"

    answer = ChatAnswerPayload(
        answer="ok",
        citations=[
            CitationPayload(
                type="news",
                ref_id="n1",
                title="title",
                provider_mode="retrieval_only",
                confidence=0.8,
                source_type="news_raw",
            )
        ],
        mode="retrieval_only",
        provider_mode="retrieval_only",
    )
    dumped = answer.model_dump(mode="json")
    assert dumped["citations"][0]["provider_mode"] == "retrieval_only"

