from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings

DEFAULT_DATE_RANGE_DAYS = 30


@dataclass(frozen=True)
class DateRange:
    date_from: date
    date_to: date


@dataclass(frozen=True)
class ExecutiveReportResult:
    data: dict[str, Any]
    meta: dict[str, Any]


class ExecutiveReportService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()

    def build_report(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
    ) -> ExecutiveReportResult:
        date_range = self._resolve_date_range(date_from=date_from, date_to=date_to)
        generated_at = datetime.now(UTC)
        kpi, has_sales_data, has_purchase_data = self._build_kpi(date_range)
        problem_products = self._build_problem_products(date_range)
        margin_risks = self._build_margin_risks(problem_products)
        demand_forecast = self._build_demand_forecast()
        market_context = self._build_market_context(date_range)
        warnings = self._build_warnings(
            has_sales_data=has_sales_data,
            has_purchase_data=has_purchase_data,
            has_forecast_data=bool(demand_forecast),
            has_news_data=bool(market_context),
        )
        recommendations = self._build_recommendations(
            problem_products=problem_products,
            has_sales_data=has_sales_data,
            has_purchase_data=has_purchase_data,
            has_forecast_data=bool(demand_forecast),
        )

        data = {
            "report_id": str(uuid4()),
            "generated_at": generated_at,
            "period": {
                "date_from": date_range.date_from,
                "date_to": date_range.date_to,
            },
            "executive_summary": self._build_executive_summary(
                kpi=kpi,
                problem_products=problem_products,
                has_sales_data=has_sales_data,
            ),
            "kpi": kpi,
            "problem_products": problem_products,
            "demand_forecast": demand_forecast,
            "margin_risks": margin_risks,
            "market_context": market_context,
            "recommendations": recommendations,
            "data_quality": {
                "has_sales_data": has_sales_data,
                "has_purchase_data": has_purchase_data,
                "has_forecast_data": bool(demand_forecast),
                "has_news_data": bool(market_context),
                "warnings": warnings,
            },
        }
        return ExecutiveReportResult(
            data=data,
            meta={
                "date_from": date_range.date_from.isoformat(),
                "date_to": date_range.date_to.isoformat(),
                "generated_at": generated_at.isoformat(),
            },
        )

    def _build_kpi(self, date_range: DateRange) -> tuple[dict[str, float], bool, bool]:
        sales_row = self._session.execute(
            text(
                """
                SELECT
                  COALESCE(SUM(volume_liters), 0)::numeric AS sales_volume_liters,
                  COALESCE(SUM(revenue_rub), 0)::numeric AS revenue_rub,
                  COUNT(*)::int AS rows_count
                FROM sales_daily
                WHERE sale_date BETWEEN :date_from AND :date_to
                """
            ),
            self._base_params(date_range),
        ).mappings().one()
        margin_row = self._session.execute(
            text(
                """
                SELECT
                  COALESCE(SUM(gross_margin_rub), 0)::numeric AS gross_margin_rub,
                  COALESCE(SUM(revenue_rub), 0)::numeric AS covered_revenue_rub,
                  COUNT(*) FILTER (WHERE NOT purchase_data_missing)::int AS covered_rows_count
                FROM vw_margin_daily
                WHERE date BETWEEN :date_from AND :date_to
                  AND NOT purchase_data_missing
                """
            ),
            self._base_params(date_range),
        ).mappings().one()
        purchase_count = self._session.scalar(
            text(
                """
                SELECT COUNT(*)::int
                FROM purchases_daily
                WHERE purchase_date BETWEEN :date_from AND :date_to
                """
            ),
            self._base_params(date_range),
        )

        gross_margin = self._to_float(margin_row["gross_margin_rub"])
        covered_revenue = self._to_float(margin_row["covered_revenue_rub"])
        gross_margin_pct = (gross_margin / covered_revenue * 100.0) if covered_revenue > 0 else 0.0
        return (
            {
                "revenue_rub": round(self._to_float(sales_row["revenue_rub"]), 2),
                "sales_volume_liters": round(self._to_float(sales_row["sales_volume_liters"]), 3),
                "gross_margin_rub": round(gross_margin, 2),
                "gross_margin_pct": round(gross_margin_pct, 2),
            },
            int(sales_row["rows_count"] or 0) > 0,
            int(purchase_count or 0) > 0 and int(margin_row["covered_rows_count"] or 0) > 0,
        )

    def _build_problem_products(self, date_range: DateRange) -> list[dict[str, Any]]:
        threshold = self._settings.kpi_low_margin_threshold_rub_per_liter
        rows = self._session.execute(
            text(
                """
                SELECT
                  v.product_code,
                  p.name AS product_name,
                  AVG(v.gross_margin_pct)::numeric AS margin_pct,
                  AVG(v.gross_margin_rub_per_liter)::numeric AS margin_rub_per_liter,
                  COUNT(*)::int AS low_days
                FROM vw_margin_daily v
                JOIN products p ON p.id = v.product_id
                WHERE v.date BETWEEN :date_from AND :date_to
                  AND NOT v.purchase_data_missing
                  AND v.gross_margin_rub_per_liter < :threshold
                GROUP BY v.product_code, p.name
                ORDER BY AVG(v.gross_margin_rub_per_liter), COUNT(*) DESC
                LIMIT 5
                """
            ),
            {**self._base_params(date_range), "threshold": threshold},
        ).mappings().all()

        return [
            {
                "product_code": row["product_code"],
                "product_name": row["product_name"],
                "reason": (
                    f"Средняя маржа ниже порога {threshold:.2f} руб/л "
                    f"в {int(row['low_days'])} дн."
                ),
                "margin_pct": round(self._to_float(row["margin_pct"]), 2),
                "recommendation": "Проверить закупочную цену и актуальность розничной цены.",
            }
            for row in rows
        ]

    @staticmethod
    def _build_margin_risks(problem_products: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "product_code": item["product_code"],
                "risk": "Маржа ниже целевого порога.",
                "impact": "Снижение валовой прибыли по продукту.",
                "recommendation": item["recommendation"],
            }
            for item in problem_products
        ]

    def _build_demand_forecast(self) -> list[dict[str, Any]]:
        rows = self._session.execute(
            text(
                """
                WITH latest_groups AS (
                  SELECT DISTINCT ON (p.id)
                    p.id AS product_id,
                    p.code AS product_code,
                    p.name AS product_name,
                    f.horizon_days,
                    f.forecast_date
                  FROM forecasts f
                  JOIN products p ON p.id = f.product_id
                  WHERE p.is_active
                    AND f.scenario_name = 'base'
                  ORDER BY
                    p.id,
                    CASE WHEN f.horizon_days = 7 THEN 0 ELSE 1 END,
                    f.created_at DESC,
                    f.forecast_date DESC
                )
                SELECT
                  lg.product_code,
                  lg.product_name,
                  lg.horizon_days,
                  SUM(f.y_hat)::numeric AS forecast_volume_liters
                FROM latest_groups lg
                JOIN forecasts f
                  ON f.product_id = lg.product_id
                 AND f.horizon_days = lg.horizon_days
                 AND f.forecast_date = lg.forecast_date
                 AND f.scenario_name = 'base'
                GROUP BY lg.product_code, lg.product_name, lg.horizon_days
                ORDER BY lg.product_code
                LIMIT 8
                """
            )
        ).mappings().all()

        return [
            {
                "product_code": row["product_code"],
                "product_name": row["product_name"],
                "forecast_period": f"{int(row['horizon_days'])} дней",
                "forecast_volume_liters": round(self._to_float(row["forecast_volume_liters"]), 3),
                "risk_level": "low",
            }
            for row in rows
        ]

    def _build_market_context(self, date_range: DateRange) -> list[dict[str, Any]]:
        digest = self._session.execute(
            text(
                """
                SELECT digest_date, period_type, summary_text
                FROM news_digests
                WHERE digest_date <= :date_to
                ORDER BY digest_date DESC, created_at DESC
                LIMIT 1
                """
            ),
            self._base_params(date_range),
        ).mappings().first()
        if digest is not None:
            return [
                {
                    "title": "Новостная сводка",
                    "summary": digest["summary_text"],
                    "source": f"news_digest:{digest['period_type']}",
                    "published_at": None,
                }
            ]

        rows = self._session.execute(
            text(
                """
                SELECT title, snippet, source_name, published_at
                FROM news_raw
                WHERE published_at::date BETWEEN :date_from AND :date_to
                ORDER BY published_at DESC
                LIMIT 3
                """
            ),
            self._base_params(date_range),
        ).mappings().all()
        return [
            {
                "title": row["title"],
                "summary": row["snippet"] or "Краткое описание новости недоступно.",
                "source": row["source_name"],
                "published_at": row["published_at"],
            }
            for row in rows
        ]

    @staticmethod
    def _build_executive_summary(
        *,
        kpi: dict[str, float],
        problem_products: list[dict[str, Any]],
        has_sales_data: bool,
    ) -> str:
        if not has_sales_data:
            return "Данных недостаточно для управленческих выводов."
        risk_text = (
            f"обнаружено проблемных продуктов: {len(problem_products)}"
            if problem_products
            else "критичных низкомаржинальных продуктов не выявлено"
        )
        return (
            f"За период выручка составила {kpi['revenue_rub']:.0f} руб., "
            f"объем продаж {kpi['sales_volume_liters']:.0f} л, "
            f"валовая маржа {kpi['gross_margin_rub']:.0f} руб. "
            f"({kpi['gross_margin_pct']:.2f}%). По марже {risk_text}."
        )

    @staticmethod
    def _build_recommendations(
        *,
        problem_products: list[dict[str, Any]],
        has_sales_data: bool,
        has_purchase_data: bool,
        has_forecast_data: bool,
    ) -> list[str]:
        recommendations: list[str] = []
        if not has_sales_data:
            recommendations.append("Обновить данные продаж перед принятием управленческих решений.")
        if has_sales_data and not has_purchase_data:
            recommendations.append("Загрузить закупки для полноценного расчета валовой маржи.")
        if problem_products:
            recommendations.append(
                "Разобрать продукты с низкой маржей и проверить ценовые решения."
            )
        if not has_forecast_data:
            recommendations.append("Запустить прогноз спроса для управленческого планирования.")
        if not recommendations:
            recommendations.append("Продолжить мониторинг KPI, маржи и прогноза спроса.")
        return recommendations

    @staticmethod
    def _build_warnings(
        *,
        has_sales_data: bool,
        has_purchase_data: bool,
        has_forecast_data: bool,
        has_news_data: bool,
    ) -> list[str]:
        warnings: list[str] = []
        if not has_sales_data:
            warnings.append("Нет данных продаж за выбранный период.")
        if not has_purchase_data:
            warnings.append("Нет данных закупок или покрытия маржи за выбранный период.")
        if not has_forecast_data:
            warnings.append("Нет сохраненного прогноза спроса.")
        if not has_news_data:
            warnings.append("Нет доступных новостей или рыночной сводки.")
        return warnings

    @staticmethod
    def _resolve_date_range(*, date_from: date | None, date_to: date | None) -> DateRange:
        today = datetime.now(UTC).date()
        resolved_to = date_to or today
        resolved_from = date_from or (resolved_to - timedelta(days=DEFAULT_DATE_RANGE_DAYS - 1))
        if resolved_from > resolved_to:
            raise ValueError("date_from must be less than or equal to date_to")
        return DateRange(date_from=resolved_from, date_to=resolved_to)

    @staticmethod
    def _base_params(date_range: DateRange) -> dict[str, date]:
        return {"date_from": date_range.date_from, "date_to": date_range.date_to}

    @staticmethod
    def _to_float(value: object) -> float:
        if value is None:
            return 0.0
        return float(value)
