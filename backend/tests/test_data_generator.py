"""Statistical property tests for the synthetic data generator."""

from __future__ import annotations

from datetime import date
from statistics import mean, pstdev

import pytest

from app.services.data_generator import DataGenerator, GeneratedDataset


@pytest.fixture(scope="module")
def dataset_3y() -> GeneratedDataset:
    gen = DataGenerator(seed=42)
    return gen.generate(
        start_date=date(2023, 1, 1),
        end_date=date(2025, 12, 31),
        product_codes=["AI_92", "AI_95", "DT_S", "DT_W"],
    )


def _volumes(ds: GeneratedDataset, code: str) -> list[float]:
    return [float(r.volume_liters) for r in ds.sales if r.product_code == code]


def _prices(ds: GeneratedDataset, code: str) -> list[float]:
    return [float(r.avg_retail_price_rub) for r in ds.sales if r.product_code == code]


def _purchase_volumes(ds: GeneratedDataset, code: str) -> list[float]:
    return [float(r.volume_liters) for r in ds.purchases if r.product_code == code]


# ---------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------


def test_reproducibility() -> None:
    a = DataGenerator(seed=123).generate(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        product_codes=["AI_92"],
    )
    b = DataGenerator(seed=123).generate(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        product_codes=["AI_92"],
    )
    assert len(a.sales) == len(b.sales)
    for r1, r2 in zip(a.sales, b.sales):
        assert r1.volume_liters == r2.volume_liters
        assert r1.avg_retail_price_rub == r2.avg_retail_price_rub


# ---------------------------------------------------------------
# Autocorrelation
# ---------------------------------------------------------------


def test_autocorrelation_positive(dataset_3y: GeneratedDataset) -> None:
    for code in ["AI_92", "AI_95", "DT_S", "DT_W"]:
        vols = _volumes(dataset_3y, code)
        n = len(vols)
        m = mean(vols)
        num = sum((vols[i] - m) * (vols[i + 1] - m) for i in range(n - 1))
        den = sum((v - m) ** 2 for v in vols)
        acf1 = num / den if den else 0
        assert acf1 > 0.4, f"{code}: lag-1 ACF = {acf1:.3f}, expected > 0.4"


# ---------------------------------------------------------------
# Seasonal patterns
# ---------------------------------------------------------------


def test_seasonal_summer_peak_gasoline(dataset_3y: GeneratedDataset) -> None:
    for code in ["AI_92", "AI_95"]:
        sales = [r for r in dataset_3y.sales if r.product_code == code]
        summer = mean([float(r.volume_liters) for r in sales if r.sale_date.month in (6, 7, 8)])
        winter = mean([float(r.volume_liters) for r in sales if r.sale_date.month in (12, 1, 2)])
        assert summer > winter, f"{code}: summer={summer:.0f} <= winter={winter:.0f}"


def test_seasonal_winter_peak_dt_w(dataset_3y: GeneratedDataset) -> None:
    sales = [r for r in dataset_3y.sales if r.product_code == "DT_W"]
    winter = mean([float(r.volume_liters) for r in sales if r.sale_date.month in (11, 12, 1, 2)])
    summer = mean([float(r.volume_liters) for r in sales if r.sale_date.month in (6, 7, 8)])
    assert winter > summer, f"DT_W: winter={winter:.0f} <= summer={summer:.0f}"


# ---------------------------------------------------------------
# Weekly pattern
# ---------------------------------------------------------------


def test_weekday_pattern(dataset_3y: GeneratedDataset) -> None:
    for code in ["AI_92", "AI_95"]:
        sales = [r for r in dataset_3y.sales if r.product_code == code]
        friday = mean([float(r.volume_liters) for r in sales if r.sale_date.weekday() == 4])
        sunday = mean([float(r.volume_liters) for r in sales if r.sale_date.weekday() == 6])
        assert friday > sunday, f"{code}: Fri={friday:.0f} <= Sun={sunday:.0f}"


# ---------------------------------------------------------------
# Trends
# ---------------------------------------------------------------


def test_price_trend_positive(dataset_3y: GeneratedDataset) -> None:
    for code in ["AI_92", "AI_95", "DT_S", "DT_W"]:
        prices = _prices(dataset_3y, code)
        first_q = mean(prices[:90])
        last_q = mean(prices[-90:])
        assert last_q > first_q, f"{code}: last_q={last_q:.2f} <= first_q={first_q:.2f}"


def test_yoy_trend_visible(dataset_3y: GeneratedDataset) -> None:
    for code in ["AI_92", "AI_95"]:
        sales = [r for r in dataset_3y.sales if r.product_code == code]
        year1 = mean([float(r.volume_liters) for r in sales if r.sale_date.year == 2023])
        year3 = mean([float(r.volume_liters) for r in sales if r.sale_date.year == 2025])
        assert year3 > year1, f"{code}: year3={year3:.0f} <= year1={year1:.0f}"


# ---------------------------------------------------------------
# Purchase volume buffer
# ---------------------------------------------------------------


def test_purchase_volume_buffer(dataset_3y: GeneratedDataset) -> None:
    for code in ["AI_92", "DT_W"]:
        s_vols = _volumes(dataset_3y, code)
        p_vols = _purchase_volumes(dataset_3y, code)
        ratio = mean(p_vols) / mean(s_vols)
        assert ratio > 1.03, f"{code}: purchase/sales ratio={ratio:.3f}, expected > 1.03"
        assert ratio < 1.25, f"{code}: purchase/sales ratio={ratio:.3f}, expected < 1.25"


# ---------------------------------------------------------------
# Holiday effect
# ---------------------------------------------------------------


def test_holiday_demand_dip(dataset_3y: GeneratedDataset) -> None:
    """New Year days should have lower demand on average."""
    code = "AI_92"
    sales = [r for r in dataset_3y.sales if r.product_code == code]
    jan_holiday = mean(
        [float(r.volume_liters) for r in sales if r.sale_date.month == 1 and r.sale_date.day <= 8]
    )
    jan_workday = mean(
        [float(r.volume_liters) for r in sales if r.sale_date.month == 1 and r.sale_date.day > 8]
    )
    assert jan_holiday < jan_workday, (
        f"Jan holiday avg={jan_holiday:.0f} >= Jan workday avg={jan_workday:.0f}"
    )


# ---------------------------------------------------------------
# Row count sanity
# ---------------------------------------------------------------


def test_row_count(dataset_3y: GeneratedDataset) -> None:
    expected_days = (date(2025, 12, 31) - date(2023, 1, 1)).days + 1  # 1096
    expected_total = expected_days * 4  # 4 products
    assert len(dataset_3y.sales) == expected_total
    assert len(dataset_3y.purchases) == expected_total


def test_event_pressure_external_context_affects_sales_level() -> None:
    start = date(2025, 1, 1)
    end = date(2025, 3, 31)
    days = (end - start).days + 1
    context_low = {
        "event_pressure_score": {
            start.fromordinal(start.toordinal() + idx): 0.0 for idx in range(days)
        }
    }
    context_high = {
        "event_pressure_score": {
            start.fromordinal(start.toordinal() + idx): 0.8 for idx in range(days)
        }
    }

    low_dataset = DataGenerator(seed=7).generate(
        start_date=start,
        end_date=end,
        product_codes=["AI_95"],
        external_context=context_low,
    )
    high_dataset = DataGenerator(seed=7).generate(
        start_date=start,
        end_date=end,
        product_codes=["AI_95"],
        external_context=context_high,
    )

    low_avg = mean(float(row.volume_liters) for row in low_dataset.sales)
    high_avg = mean(float(row.volume_liters) for row in high_dataset.sales)
    assert high_avg < low_avg


def test_cross_product_dynamics_create_share_variability() -> None:
    dataset = DataGenerator(seed=17).generate(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 6, 30),
        product_codes=["AI_92", "AI_95"],
    )
    volumes_by_day: dict[date, dict[str, float]] = {}
    for row in dataset.sales:
        volumes_by_day.setdefault(row.sale_date, {})
        volumes_by_day[row.sale_date][row.product_code] = float(row.volume_liters)

    shares: list[float] = []
    for day, item in sorted(volumes_by_day.items()):
        if "AI_92" not in item or "AI_95" not in item:
            continue
        total = item["AI_92"] + item["AI_95"]
        if total <= 0:
            continue
        shares.append(item["AI_95"] / total)
    assert len(shares) > 30
    assert pstdev(shares) > 0.01
