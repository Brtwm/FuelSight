"""Configuration constants for FuelSight synthetic data generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SupplierConfig:
    """Single fuel supplier."""

    name: str
    price_spread: float  # relative spread vs base purchase price
    weight: float  # probability weight for random selection


@dataclass(frozen=True)
class ProductConfig:
    """Product-level generation parameters."""

    code: str
    name: str

    # Pricing
    base_retail_price: float  # руб/л at period start
    purchase_margin_low: float  # purchase_price / retail_price ratio min
    purchase_margin_high: float  # purchase_price / retail_price ratio max

    # Demand
    base_demand: float  # mean litres/day
    elasticity: float  # price elasticity of demand (0..1)
    min_demand: float  # floor litres/day

    # Seasonality
    seasonal_mode: str  # "summer_peak" | "winter_peak"
    seasonal_amplitude: float  # primary harmonic amplitude
    seasonal_phase_shift: int  # day-of-year shift for peak

    # Autocorrelation & noise
    ar_coefficient: float  # AR(1) coefficient (0..1)
    noise_std: float  # noise as fraction of demand level

    # Purchase specifics
    purchase_volume_buffer_low: float  # purchase_vol / sales_vol min
    purchase_volume_buffer_high: float  # purchase_vol / sales_vol max
    logistics_cost_per_liter_low: float  # руб/л min
    logistics_cost_per_liter_high: float  # руб/л max

    # Suppliers
    suppliers: tuple[SupplierConfig, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CuratedEvent:
    """Curated recurring event used for external context and generator realism."""

    code: str
    title: str
    start_month: int
    start_day: int
    end_month: int
    end_day: int
    pressure_score: float
    demand_delta_pct: float = 0.0
    purchase_delta_pct: float = 0.0


# ---------------------------------------------------------------------------
# Russian public holidays  (month, day)
# ---------------------------------------------------------------------------

RU_HOLIDAYS: frozenset[tuple[int, int]] = frozenset(
    {
        (1, 1),
        (1, 2),
        (1, 3),
        (1, 4),
        (1, 5),
        (1, 6),
        (1, 7),
        (1, 8),
        (2, 23),
        (3, 8),
        (5, 1),
        (5, 9),
        (6, 12),
        (11, 4),
    }
)

PRE_HOLIDAY_DAYS: int = 2

NEW_YEAR_DEMAND_FACTORS: dict[int, float] = {
    1: 0.70,
    2: 0.72,
    3: 0.75,
    4: 0.78,
    5: 0.82,
    6: 0.85,
    7: 0.88,
    8: 0.92,
}

HOLIDAY_DEMAND_FACTOR: float = 0.85
PRE_HOLIDAY_DEMAND_FACTOR: float = 1.10

# ---------------------------------------------------------------------------
# Weekly demand pattern (0=Mon, 6=Sun)
# ---------------------------------------------------------------------------

WEEKLY_DEMAND_FACTORS: dict[int, float] = {
    0: 0.95,
    1: 0.98,
    2: 1.00,
    3: 1.02,
    4: 1.08,
    5: 1.04,
    6: 0.93,
}

# ---------------------------------------------------------------------------
# Price dynamics (Ornstein-Uhlenbeck)
# ---------------------------------------------------------------------------

PRICE_MEAN_REVERSION_SPEED: float = 0.05
PRICE_DAILY_VOLATILITY: float = 0.008

# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------

DEMAND_TREND_ANNUAL: float = 0.04  # +4 %/year
PRICE_TREND_ANNUAL: float = 0.08  # +8 %/year

# ---------------------------------------------------------------------------
# Shocks & promos
# ---------------------------------------------------------------------------

PROMO_PROBABILITY: float = 0.025
PROMO_PRICE_DISCOUNT: tuple[float, float] = (0.03, 0.08)
PROMO_DEMAND_BOOST: tuple[float, float] = (0.08, 0.15)

SUPPLY_SHOCK_PROBABILITY: float = 0.008
SUPPLY_SHOCK_MAGNITUDE: tuple[float, float] = (0.12, 0.28)
SUPPLY_SHOCK_RETAIL_PASSTHROUGH: tuple[float, float] = (0.5, 0.8)
SUPPLY_SHOCK_RETAIL_RESPONSE_RATE: tuple[float, float] = (0.12, 0.30)

DEMAND_SURGE_PROBABILITY: float = 0.012
DEMAND_SURGE_MAGNITUDE: tuple[float, float] = (0.18, 0.40)

DEMAND_DIP_PROBABILITY: float = 0.010
DEMAND_DIP_MAGNITUDE: tuple[float, float] = (0.15, 0.35)

# ---------------------------------------------------------------------------
# Supplier pools
# ---------------------------------------------------------------------------

_GASOLINE_SUPPLIERS: tuple[SupplierConfig, ...] = (
    SupplierConfig(name="ЛУКОЙЛ-Трейд", price_spread=0.0, weight=0.35),
    SupplierConfig(name="РН-Снабжение", price_spread=-0.015, weight=0.30),
    SupplierConfig(name="ГазПромНефть-Снабжение", price_spread=0.008, weight=0.20),
    SupplierConfig(name="Татнефть-Ойл", price_spread=-0.020, weight=0.15),
)

_DIESEL_SUPPLIERS: tuple[SupplierConfig, ...] = (
    SupplierConfig(name="ГазПромНефть-Снабжение", price_spread=0.0, weight=0.30),
    SupplierConfig(name="БашНефть-Ресурс", price_spread=0.012, weight=0.20),
    SupplierConfig(name="РН-Снабжение", price_spread=-0.010, weight=0.30),
    SupplierConfig(name="Сургутнефтегаз", price_spread=0.005, weight=0.20),
)

# ---------------------------------------------------------------------------
# Product configurations   (4 products, ГОСТ-based naming)
# ---------------------------------------------------------------------------

DEFAULT_PRODUCT_CONFIGS: dict[str, ProductConfig] = {
    "AI_92": ProductConfig(
        code="AI_92",
        name="Бензин АИ-92",
        base_retail_price=52.0,
        base_demand=12500.0,
        elasticity=0.42,
        seasonal_mode="summer_peak",
        seasonal_amplitude=0.08,
        seasonal_phase_shift=100,
        ar_coefficient=0.70,
        noise_std=0.04,
        min_demand=2500.0,
        purchase_margin_low=0.78,
        purchase_margin_high=0.85,
        purchase_volume_buffer_low=1.05,
        purchase_volume_buffer_high=1.15,
        logistics_cost_per_liter_low=0.20,
        logistics_cost_per_liter_high=0.45,
        suppliers=_GASOLINE_SUPPLIERS,
    ),
    "AI_95": ProductConfig(
        code="AI_95",
        name="Бензин АИ-95",
        base_retail_price=58.0,
        base_demand=9800.0,
        elasticity=0.47,
        seasonal_mode="summer_peak",
        seasonal_amplitude=0.09,
        seasonal_phase_shift=100,
        ar_coefficient=0.70,
        noise_std=0.04,
        min_demand=1800.0,
        purchase_margin_low=0.78,
        purchase_margin_high=0.84,
        purchase_volume_buffer_low=1.05,
        purchase_volume_buffer_high=1.12,
        logistics_cost_per_liter_low=0.22,
        logistics_cost_per_liter_high=0.48,
        suppliers=_GASOLINE_SUPPLIERS,
    ),
    "DT_S": ProductConfig(
        code="DT_S",
        name="ДТ летнее ЕВРО",
        base_retail_price=63.0,
        base_demand=6200.0,
        elasticity=0.35,
        seasonal_mode="summer_peak",
        seasonal_amplitude=0.35,
        seasonal_phase_shift=90,
        ar_coefficient=0.72,
        noise_std=0.05,
        min_demand=800.0,
        purchase_margin_low=0.80,
        purchase_margin_high=0.86,
        purchase_volume_buffer_low=1.08,
        purchase_volume_buffer_high=1.18,
        logistics_cost_per_liter_low=0.25,
        logistics_cost_per_liter_high=0.50,
        suppliers=_DIESEL_SUPPLIERS,
    ),
    "DT_W": ProductConfig(
        code="DT_W",
        name="ДТ зимнее ЕВРО",
        base_retail_price=68.0,
        base_demand=5500.0,
        elasticity=0.32,
        seasonal_mode="winter_peak",
        seasonal_amplitude=0.30,
        seasonal_phase_shift=90,
        ar_coefficient=0.72,
        noise_std=0.05,
        min_demand=700.0,
        purchase_margin_low=0.79,
        purchase_margin_high=0.85,
        purchase_volume_buffer_low=1.08,
        purchase_volume_buffer_high=1.18,
        logistics_cost_per_liter_low=0.28,
        logistics_cost_per_liter_high=0.55,
        suppliers=_DIESEL_SUPPLIERS,
    ),
}

# ---------------------------------------------------------------------------
# Curated event catalog
# ---------------------------------------------------------------------------

CURATED_EVENT_CATALOG: tuple[CuratedEvent, ...] = (
    CuratedEvent(
        code="spring_refinery_repairs",
        title="Плановые ремонты НПЗ весной",
        start_month=3,
        start_day=20,
        end_month=4,
        end_day=20,
        pressure_score=0.35,
        purchase_delta_pct=3.0,
    ),
    CuratedEvent(
        code="may_holiday_mobility",
        title="Майские праздники и рост мобильности",
        start_month=5,
        start_day=1,
        end_month=5,
        end_day=11,
        pressure_score=0.20,
        demand_delta_pct=4.0,
    ),
    CuratedEvent(
        code="summer_logistics_tension",
        title="Летние логистические ограничения",
        start_month=7,
        start_day=10,
        end_month=8,
        end_day=20,
        pressure_score=0.28,
        purchase_delta_pct=2.2,
    ),
    CuratedEvent(
        code="autumn_fx_volatility",
        title="Осенняя волатильность валюты",
        start_month=9,
        start_day=15,
        end_month=10,
        end_day=20,
        pressure_score=0.22,
        purchase_delta_pct=1.8,
    ),
    CuratedEvent(
        code="winter_diesel_peak",
        title="Зимний пик спроса на ДТ",
        start_month=11,
        start_day=20,
        end_month=2,
        end_day=15,
        pressure_score=0.30,
        demand_delta_pct=3.0,
    ),
)


def event_pressure_for_day(day_value: date) -> float:
    score = 0.0
    month_day = day_value.month * 100 + day_value.day
    for event in CURATED_EVENT_CATALOG:
        start_key = event.start_month * 100 + event.start_day
        end_key = event.end_month * 100 + event.end_day
        if start_key <= end_key:
            active = start_key <= month_day <= end_key
        else:
            active = month_day >= start_key or month_day <= end_key
        if active:
            score += event.pressure_score
    return max(-1.0, min(1.0, score))


def event_effect_for_day(day_value: date) -> tuple[float, float]:
    demand_delta_pct = 0.0
    purchase_delta_pct = 0.0
    month_day = day_value.month * 100 + day_value.day
    for event in CURATED_EVENT_CATALOG:
        start_key = event.start_month * 100 + event.start_day
        end_key = event.end_month * 100 + event.end_day
        if start_key <= end_key:
            active = start_key <= month_day <= end_key
        else:
            active = month_day >= start_key or month_day <= end_key
        if active:
            demand_delta_pct += event.demand_delta_pct
            purchase_delta_pct += event.purchase_delta_pct
    return demand_delta_pct, purchase_delta_pct
