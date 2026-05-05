from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.llm.registry import resolve_llm_adapter
from app.models import BacktestRun, NewsDigest, NewsRaw, Product, PurchasesDaily, SalesDaily
from app.schemas.defense import DefenseReportPayload, DefenseStatus
from app.services.analytics_service import AnalyticsService
from app.services.forecast_service import ForecastService
from app.services.kpi_service import KpiService
from app.services.news_service import NewsService


class DefenseReportService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()

    def build_report(self, *, profile: str | None = None) -> DefenseReportPayload:
        run_id = str(uuid4())
        generated_at = datetime.now(UTC)
        normalized_profile = self._normalize_profile(profile or self._settings.defense_profile)
        date_to = self._latest_sales_date() or generated_at.date()
        date_from = date_to - timedelta(days=29)
        product_code = self._default_product_code()

        data_quality = self._build_data_quality(date_from=date_from, date_to=date_to)
        model_quality = self._build_model_quality(product_code=product_code)
        provider_modes = self._build_provider_modes()
        executive_summary = self._build_executive_summary(
            date_from=date_from,
            date_to=date_to,
            product_code=product_code,
        )
        steps = self._build_steps(
            profile=normalized_profile,
            data_quality=data_quality,
            model_quality=model_quality,
            provider_modes=provider_modes,
            executive_summary=executive_summary,
        )
        degradations = [
            step["details"] for step in steps if step["status"] in {"warning", "degraded", "failed"}
        ]
        overall_status = self._overall_status([step["status"] for step in steps])
        report = DefenseReportPayload(
            run_id=run_id,
            generated_at=generated_at.isoformat(),
            profile=normalized_profile,
            overall_status=overall_status,
            steps=steps,
            badges=self._build_badges(
                profile=normalized_profile,
                overall_status=overall_status,
                data_quality=data_quality,
                model_quality=model_quality,
                provider_modes=provider_modes,
            ),
            data_quality=data_quality,
            model_quality=model_quality,
            provider_modes=provider_modes,
            degradations=degradations,
            executive_summary=executive_summary,
            decision_journal=self._build_decision_journal(
                profile=normalized_profile,
                provider_modes=provider_modes,
                model_quality=model_quality,
            ),
            artifacts={},
        )
        artifact_paths = self.write_artifacts(report)
        return report.model_copy(update={"artifacts": artifact_paths})

    def write_artifacts(self, report: DefenseReportPayload) -> dict[str, str]:
        report_dir = self._report_dir(report.run_id)
        report_dir.mkdir(parents=True, exist_ok=True)
        json_path = report_dir / "defense-report.json"
        pdf_path = report_dir / "defense-report.pdf"
        payload = report.model_dump(mode="json")
        payload["artifacts"] = {"json": str(json_path), "pdf": str(pdf_path)}
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._write_pdf(payload=payload, pdf_path=pdf_path)
        return {"json": str(json_path), "pdf": str(pdf_path)}

    def _build_executive_summary(
        self, *, date_from: date, date_to: date, product_code: str
    ) -> dict[str, object]:
        kpi = self._safe_call(
            "kpi",
            lambda: KpiService(self._session, settings=self._settings).get_summary(
                date_from=date_from,
                date_to=date_to,
                product_code=product_code,
            ),
        )
        sales = self._safe_call(
            "sales",
            lambda: AnalyticsService(self._session, settings=self._settings).get_sales(
                date_from=date_from,
                date_to=date_to,
                product_code=product_code,
                granularity="day",
            ),
        )
        margin = self._safe_call(
            "margin",
            lambda: AnalyticsService(self._session, settings=self._settings).get_margin(
                date_from=date_from,
                date_to=date_to,
                product_code=product_code,
                granularity="day",
            ),
        )
        forecast = self._safe_call(
            "forecast",
            lambda: ForecastService(self._session, settings=self._settings).get_latest_forecast(
                product_code=product_code,
                horizon_days=7,
            ),
        )
        backtest = self._safe_call(
            "backtest",
            lambda: ForecastService(self._session, settings=self._settings).get_latest_backtest(
                product_code=product_code,
                horizon_days=7,
            ),
        )
        digest = self._safe_call(
            "digest",
            lambda: NewsService(self._session, settings=self._settings).get_latest_digest(
                period_type="daily"
            ),
        )
        return {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "product_code": product_code,
            "kpi": getattr(kpi, "data", None) or {},
            "sales_points": ((getattr(sales, "data", {}) or {}).get("series") or [])[:14],
            "margin_points": ((getattr(margin, "data", {}) or {}).get("series") or [])[:14],
            "forecast": getattr(forecast, "data", None) or {},
            "backtest": getattr(backtest, "data", None) or {},
            "news_digest": digest or {},
        }

    def _build_data_quality(self, *, date_from: date, date_to: date) -> dict[str, object]:
        product_count = self._session.scalar(
            select(func.count()).select_from(Product).where(Product.is_active.is_(True))
        ) or 0
        sales_days = self._session.execute(
            text(
                """
                SELECT COUNT(DISTINCT CAST(sale_date AS TEXT) || ':' || CAST(product_id AS TEXT))
                FROM sales_daily
                WHERE sale_date >= :date_from AND sale_date <= :date_to
                """
            ),
            {"date_from": date_from, "date_to": date_to},
        ).scalar_one()
        purchase_days = self._session.execute(
            text(
                """
                SELECT COUNT(DISTINCT CAST(purchase_date AS TEXT) || ':' || CAST(product_id AS TEXT))
                FROM purchases_daily
                WHERE purchase_date >= :date_from AND purchase_date <= :date_to
                """
            ),
            {"date_from": date_from, "date_to": date_to},
        ).scalar_one()
        expected_points = max(((date_to - date_from).days + 1) * int(product_count), 1)
        coverage_ratio = min(float(sales_days) / expected_points, 1.0)
        purchase_coverage_ratio = min(float(purchase_days) / expected_points, 1.0)
        fallback_ratio = self._latest_manifest_number(
            root=Path(self._settings.external_cache_dir),
            key="fallback_ratio",
        )
        status: DefenseStatus = "ok"
        if coverage_ratio < 0.85:
            status = "degraded"
        elif coverage_ratio < 0.95 or purchase_coverage_ratio < 0.9:
            status = "warning"
        return {
            "status": status,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "expected_points": expected_points,
            "sales_points": int(sales_days),
            "purchase_points": int(purchase_days),
            "coverage_ratio": round(coverage_ratio, 4),
            "purchase_coverage_ratio": round(purchase_coverage_ratio, 4),
            "external_fallback_ratio": fallback_ratio,
        }

    def _build_model_quality(self, *, product_code: str) -> dict[str, object]:
        product = self._session.scalar(select(Product).where(Product.code == product_code))
        latest = None
        if product is not None:
            latest = self._session.scalar(
                select(BacktestRun)
                .where(BacktestRun.product_id == product.id)
                .where(BacktestRun.horizon_days == 7)
                .order_by(BacktestRun.finished_at.desc().nullslast(), BacktestRun.started_at.desc())
                .limit(1)
            )
        if latest is None:
            return {"status": "degraded", "reason": "Нет последнего backtest для 7 дней."}
        completed_at = latest.finished_at or latest.started_at
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=UTC)
        age_days = (datetime.now(UTC).date() - completed_at.date()).days
        status: DefenseStatus = "ok" if age_days <= 8 else "warning" if age_days <= 14 else "degraded"
        metrics = latest.metrics_json or {}
        return {
            "status": status,
            "product_code": product_code,
            "horizon_days": latest.horizon_days,
            "run_date": completed_at.date().isoformat(),
            "age_days": age_days,
            "mae": metrics.get("mae"),
            "rmse": metrics.get("rmse"),
            "smape": metrics.get("smape"),
            "model_type": latest.model_type,
            "report_path": latest.report_path,
        }

    def _build_provider_modes(self) -> dict[str, object]:
        llm_resolution = resolve_llm_adapter(self._settings)
        try:
            latest_news_mode = self._session.scalar(
                select(NewsRaw.provider_mode).order_by(NewsRaw.published_at.desc()).limit(1)
            )
        except SQLAlchemyError:
            self._session.rollback()
            latest_news_mode = None
        try:
            latest_digest = self._session.scalar(
                select(NewsDigest).order_by(NewsDigest.digest_date.desc()).limit(1)
            )
        except SQLAlchemyError:
            self._session.rollback()
            latest_digest = None
        return {
            "defense_mode": self._settings.defense_mode,
            "defense_profile": self._settings.defense_profile,
            "external_indicators_mode": self._settings.external_indicators_mode,
            "news_provider": self._settings.news_provider,
            "news_provider_mode": latest_news_mode,
            "news_freshness": self._news_freshness(latest_digest),
            "llm_active": llm_resolution.to_payload(),
            "cloud_configured": bool(self._settings.llm_api_key or self._settings.gigachat_auth_key),
        }

    def _build_steps(
        self,
        *,
        profile: str,
        data_quality: dict[str, object],
        model_quality: dict[str, object],
        provider_modes: dict[str, object],
        executive_summary: dict[str, object],
    ) -> list[dict[str, str]]:
        news_digest = executive_summary.get("news_digest")
        forecast = executive_summary.get("forecast")
        llm_active = provider_modes.get("llm_active")
        llm_mode = llm_active.get("mode") if isinstance(llm_active, dict) else "retrieval_only"
        llm_status = self._llm_status_for_profile(profile=profile, llm_mode=str(llm_mode))
        llm_details = (
            "Offline-safe использует проверенные источники без LLM."
            if profile == "offline-safe" and llm_mode == "retrieval_only"
            else f"Итоговый режим LLM: {llm_mode}"
        )
        return [
            {
                "name": "data_quality",
                "status": str(data_quality.get("status", "failed")),
                "details": f"Покрытие продаж {data_quality.get('coverage_ratio')}",
            },
            {
                "name": "model_quality",
                "status": str(model_quality.get("status", "failed")),
                "details": f"Backtest SMAPE {model_quality.get('smape', 'n/a')}",
            },
            {
                "name": "news_digest",
                "status": "ok" if isinstance(news_digest, dict) and news_digest else "degraded",
                "details": "Новостная сводка доступна" if news_digest else "Новостная сводка отсутствует",
            },
            {
                "name": "forecast",
                "status": "ok" if isinstance(forecast, dict) and forecast else "degraded",
                "details": "Прогноз доступен" if forecast else "Прогноз не найден",
            },
            {
                "name": "llm_mode",
                "status": llm_status,
                "details": llm_details,
            },
        ]

    def _build_badges(
        self,
        *,
        profile: str,
        overall_status: DefenseStatus,
        data_quality: dict[str, object],
        model_quality: dict[str, object],
        provider_modes: dict[str, object],
    ) -> list[dict[str, str]]:
        llm_active = provider_modes.get("llm_active")
        llm_mode = llm_active.get("mode") if isinstance(llm_active, dict) else "retrieval_only"
        llm_status = self._llm_status_for_profile(profile=profile, llm_mode=str(llm_mode))
        return [
            {"label": "Defense", "status": overall_status, "value": profile},
            {
                "label": "Data Freshness",
                "status": str(data_quality.get("status", "warning")),
                "value": str(data_quality.get("coverage_ratio")),
            },
            {
                "label": "Model Freshness",
                "status": str(model_quality.get("status", "warning")),
                "value": str(model_quality.get("age_days", "n/a")),
            },
            {
                "label": "LLM Mode",
                "status": llm_status,
                "value": str(llm_mode),
            },
            {
                "label": "News Freshness",
                "status": "ok" if provider_modes.get("news_freshness") == "fresh" else "warning",
                "value": str(provider_modes.get("news_freshness") or "unknown"),
            },
            {
                "label": "Indicators",
                "status": "ok"
                if provider_modes.get("external_indicators_mode") == "live"
                or (
                    profile == "offline-safe"
                    and provider_modes.get("external_indicators_mode") == "manual_snapshot"
                )
                else "degraded",
                "value": str(provider_modes.get("external_indicators_mode")),
            },
        ]

    def _build_decision_journal(
        self, *, profile: str, provider_modes: dict[str, object], model_quality: dict[str, object]
    ) -> list[str]:
        llm_active = provider_modes.get("llm_active")
        llm_mode = llm_active.get("mode") if isinstance(llm_active, dict) else "retrieval_only"
        return [
            f"Профиль защиты: {profile}.",
            f"LLM режим: {llm_mode}; факты берутся только из evidence/citations.",
            f"Качество прогноза контролируется через SMAPE={model_quality.get('smape', 'n/a')}.",
            "При недоступности сети демонстрация остается работоспособной через сохраненные данные.",
        ]

    def _write_pdf(self, *, payload: dict[str, Any], pdf_path: Path) -> None:
        font_name = self._register_cyrillic_font()
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=14 * mm,
            leftMargin=14 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "FuelSightTitle",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=16,
            leading=20,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "FuelSightBody",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=8.5,
            leading=11,
        )
        story: list[Any] = [
            Paragraph("FuelSight: отчет для защиты", title_style),
            Paragraph(
                f"Профиль: {payload['profile']} | Статус: {payload['overall_status']} | "
                f"Сформировано: {payload['generated_at']}",
                body_style,
            ),
            Spacer(1, 4 * mm),
        ]
        badges = payload.get("badges", [])
        badge_rows = [["Показатель", "Статус", "Значение"]] + [
            [item.get("label"), item.get("status"), item.get("value")] for item in badges
        ]
        story.append(self._table(badge_rows, font_name=font_name))
        story.append(Spacer(1, 4 * mm))
        summary = payload.get("executive_summary", {})
        kpi = summary.get("kpi", {}) if isinstance(summary, dict) else {}
        model_quality = payload.get("model_quality", {})
        rows = [
            ["KPI", "Значение"],
            ["Выручка, руб.", self._fmt(kpi.get("revenue_rub"))],
            ["Маржа, руб.", self._fmt(kpi.get("gross_margin_rub"))],
            ["Продажи, л.", self._fmt(kpi.get("sales_volume_liters"))],
            ["SMAPE", self._fmt(model_quality.get("smape"))],
            ["Модель", str(model_quality.get("model_type", "n/a"))],
        ]
        story.append(self._table(rows, font_name=font_name))
        story.append(Spacer(1, 4 * mm))
        news_digest = summary.get("news_digest", {}) if isinstance(summary, dict) else {}
        bullets = news_digest.get("bullet_points", []) if isinstance(news_digest, dict) else []
        story.append(Paragraph("Ключевые новости и решения", title_style))
        for item in bullets[:3]:
            story.append(Paragraph(f"- {item}", body_style))
        for item in payload.get("decision_journal", [])[:4]:
            story.append(Paragraph(f"- {item}", body_style))
        doc.build(story)

    def _table(self, rows: list[list[object]], *, font_name: str) -> Table:
        table = Table(rows, hAlign="LEFT", colWidths=[58 * mm, 35 * mm, 78 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324d")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d7dde5")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
                ]
            )
        )
        return table

    def _register_cyrillic_font(self) -> str:
        for path in (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("C:/Windows/Fonts/arial.ttf"),
        ):
            if path.exists():
                pdfmetrics.registerFont(TTFont("FuelSightSans", str(path)))
                return "FuelSightSans"
        return "Helvetica"

    def _default_product_code(self) -> str:
        demo_code = self._session.scalar(
            select(Product.code)
            .where(Product.is_active.is_(True))
            .where(Product.code == "AI_95")
            .limit(1)
        )
        if demo_code:
            return demo_code
        code = self._session.scalar(
            select(Product.code).where(Product.is_active.is_(True)).order_by(Product.code.asc()).limit(1)
        )
        return code or "AI_95"

    def _latest_sales_date(self) -> date | None:
        return self._session.scalar(select(func.max(SalesDaily.sale_date)))

    def _safe_call(self, name: str, callback) -> Any:
        try:
            return callback()
        except Exception:
            self._session.rollback()
            return {"status": "degraded", "reason": f"{name}_unavailable"}

    def _latest_manifest_number(self, *, root: Path, key: str) -> float | None:
        if not root.exists():
            return None
        for path in sorted(root.rglob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            value = payload.get(key)
            if isinstance(value, (int, float)):
                return round(float(value), 4)
        return None

    def _report_dir(self, run_id: str) -> Path:
        return Path(self._settings.model_artifacts_dir) / "defense" / run_id

    @staticmethod
    def _news_freshness(digest: NewsDigest | None) -> str:
        if digest is None:
            return "degraded"
        age_days = (datetime.now(UTC).date() - digest.digest_date).days
        if age_days <= 2:
            return "fresh"
        if age_days <= 7:
            return "warning"
        return "degraded"

    @staticmethod
    def _overall_status(statuses: list[str]) -> DefenseStatus:
        if "failed" in statuses:
            return "failed"
        if "degraded" in statuses:
            return "degraded"
        if "warning" in statuses:
            return "warning"
        return "ok"

    @staticmethod
    def _llm_status_for_profile(*, profile: str, llm_mode: str) -> DefenseStatus:
        if llm_mode == "cloud_llm":
            return "ok"
        if profile == "offline-safe" and llm_mode == "retrieval_only":
            return "ok"
        if profile == "cloud-enhanced" and llm_mode == "retrieval_only":
            return "warning"
        return "degraded"

    @staticmethod
    def _normalize_profile(value: str) -> str:
        normalized = value.strip().lower()
        if normalized in {"offline-safe", "cloud-enhanced"}:
            return normalized
        return "offline-safe"

    @staticmethod
    def _fmt(value: object) -> str:
        if isinstance(value, (int, float)):
            return f"{value:,.2f}".replace(",", " ")
        if value is None:
            return "n/a"
        return str(value)
