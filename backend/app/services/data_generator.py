"""Synthetic historical data generator for FuelSight.

Produces realistic daily sales and purchases with:
- AR(1) autocorrelated demand
- Weekly demand patterns (Fri peak, Sun trough)
- Russian public-holiday effects
- Two-harmonic seasonality (summer_peak / winter_peak modes)
- Long-term demand (+4 %/y) and price (+8 %/y) trends
- Ornstein-Uhlenbeck price dynamics with mean reversion
- Supply shocks with lagged retail price response
- Promo / demand-surge / demand-dip events
- Supplier-specific purchase price spreads
- Purchase volume buffer over sales volume
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from random import Random

from app.services.data_generator_config import (
    DEFAULT_PRODUCT_CONFIGS,
    DEMAND_DIP_MAGNITUDE,
    DEMAND_DIP_PROBABILITY,
    DEMAND_SURGE_MAGNITUDE,
    DEMAND_SURGE_PROBABILITY,
    DEMAND_TREND_ANNUAL,
    HOLIDAY_DEMAND_FACTOR,
    NEW_YEAR_DEMAND_FACTORS,
    PRE_HOLIDAY_DAYS,
    PRE_HOLIDAY_DEMAND_FACTOR,
    PRICE_DAILY_VOLATILITY,
    PRICE_MEAN_REVERSION_SPEED,
    PRICE_TREND_ANNUAL,
    PROMO_DEMAND_BOOST,
    PROMO_PRICE_DISCOUNT,
    PROMO_PROBABILITY,
    RU_HOLIDAYS,
    SUPPLY_SHOCK_MAGNITUDE,
    SUPPLY_SHOCK_PROBABILITY,
    SUPPLY_SHOCK_RETAIL_PASSTHROUGH,
    SUPPLY_SHOCK_RETAIL_RESPONSE_RATE,
    WEEKLY_DEMAND_FACTORS,
    ProductConfig,
    SupplierConfig,
)

# ---------------------------------------------------------------------------
# Output dataclasses (pure data — no ORM dependency)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GeneratedSalesRow:
    sale_date: date
    product_code: str
    volume_liters: Decimal
    revenue_rub: Decimal
    avg_retail_price_rub: Decimal


@dataclass(frozen=True)
class GeneratedPurchaseRow:
    purchase_date: date
    product_code: str
    volume_liters: Decimal
    purchase_price_rub: Decimal
    logistics_cost_rub: Decimal
    supplier_name: str
    total_cost_rub: Decimal


@dataclass(frozen=True)
class GeneratedDataset:
    sales: list[GeneratedSalesRow]
    purchases: list[GeneratedPurchaseRow]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class DataGenerator:
    """Produces synthetic fuel sales and purchase data."""

    def __init__(
        self,
        seed: int,
        product_configs: dict[str, ProductConfig] | None = None,
    ) -> None:
        self._rng = Random(seed)
        self._configs = product_configs or DEFAULT_PRODUCT_CONFIGS

    # -- public API ---------------------------------------------------------

    def generate(
        self,
        *,
        start_date: date,
        end_date: date,
        product_codes: list[str],
    ) -> GeneratedDataset:
        """Generate sales + purchases for *product_codes* over the date range."""
        date_points = _date_range(start=start_date, end=end_date)
        codes = sorted(product_codes)

        all_sales: list[GeneratedSalesRow] = []
        all_purchases: list[GeneratedPurchaseRow] = []

        for code in codes:
            cfg = self._configs[code]
            sales, purchases = self._generate_product_series(
                cfg=cfg,
                start_date=start_date,
                date_points=date_points,
            )
            all_sales.extend(sales)
            all_purchases.extend(purchases)

        return GeneratedDataset(sales=all_sales, purchases=all_purchases)

    # -- per-product series -------------------------------------------------

    def _generate_product_series(
        self,
        *,
        cfg: ProductConfig,
        start_date: date,
        date_points: list[date],
    ) -> tuple[list[GeneratedSalesRow], list[GeneratedPurchaseRow]]:
        sales: list[GeneratedSalesRow] = []
        purchases: list[GeneratedPurchaseRow] = []

        prev_demand: float = cfg.base_demand
        price_deviation: float = 0.0
        pending_retail_adj: float = 0.0

        for current_date in date_points:
            days_elapsed = (current_date - start_date).days
            doy = current_date.timetuple().tm_yday
            weekday = current_date.weekday()

            # --- trends ---
            demand_trend = 1.0 + DEMAND_TREND_ANNUAL * (days_elapsed / 365.0)
            price_trend = 1.0 + PRICE_TREND_ANNUAL * (days_elapsed / 365.0)

            # --- seasonality ---
            seasonal = _seasonal_factor(doy=doy, cfg=cfg)

            # --- weekly ---
            weekly = WEEKLY_DEMAND_FACTORS.get(weekday, 1.0)

            # --- holidays ---
            holiday = _holiday_demand_factor(current_date)

            # --- price dynamics (OU process) ---
            drift_target = price_trend - 1.0
            price_deviation += PRICE_MEAN_REVERSION_SPEED * (
                drift_target - price_deviation
            )
            price_deviation += self._rng.gauss(0, PRICE_DAILY_VOLATILITY)

            # --- promo ---
            promo_price_adj = 0.0
            promo_demand_adj = 0.0
            if self._rng.random() < PROMO_PROBABILITY:
                promo_price_adj = -self._rng.uniform(*PROMO_PRICE_DISCOUNT)
                promo_demand_adj = self._rng.uniform(*PROMO_DEMAND_BOOST)

            retail_price = cfg.base_retail_price * (
                1.0 + price_deviation + promo_price_adj
            )

            # --- supply shock ---
            purchase_shock_adj = 0.0
            if self._rng.random() < SUPPLY_SHOCK_PROBABILITY:
                purchase_shock_adj = self._rng.uniform(*SUPPLY_SHOCK_MAGNITUDE)
                passthrough = purchase_shock_adj * self._rng.uniform(
                    *SUPPLY_SHOCK_RETAIL_PASSTHROUGH
                )
                pending_retail_adj += passthrough

            if pending_retail_adj > 0.002:
                daily_pass = pending_retail_adj * self._rng.uniform(
                    *SUPPLY_SHOCK_RETAIL_RESPONSE_RATE
                )
                retail_price *= 1.0 + daily_pass
                pending_retail_adj -= daily_pass
            else:
                pending_retail_adj = 0.0

            retail_price = max(cfg.base_retail_price * 0.7, retail_price)

            # --- price effect on demand ---
            price_effect = (
                retail_price / (cfg.base_retail_price * price_trend)
            ) - 1.0

            # --- demand target ---
            target_demand = (
                cfg.base_demand
                * demand_trend
                * seasonal
                * weekly
                * holiday
                * (1.0 - cfg.elasticity * price_effect)
                * (1.0 + promo_demand_adj)
            )

            # --- demand shocks (exclusive) ---
            roll = self._rng.random()
            if roll < DEMAND_SURGE_PROBABILITY:
                target_demand *= 1.0 + self._rng.uniform(*DEMAND_SURGE_MAGNITUDE)
            elif roll < DEMAND_SURGE_PROBABILITY + DEMAND_DIP_PROBABILITY:
                target_demand *= 1.0 - self._rng.uniform(*DEMAND_DIP_MAGNITUDE)

            # --- AR(1) demand ---
            noise = (
                target_demand * cfg.noise_std * self._rng.gauss(0, 1)
            )
            demand = (
                cfg.ar_coefficient * prev_demand
                + (1.0 - cfg.ar_coefficient) * target_demand
                + noise
            )
            demand = max(cfg.min_demand, demand)
            prev_demand = demand

            # --- purchase price ---
            base_ratio = self._rng.uniform(
                cfg.purchase_margin_low, cfg.purchase_margin_high
            )
            supplier = _select_supplier(self._rng, cfg.suppliers)
            purchase_base = (
                retail_price * base_ratio * (1.0 + supplier.price_spread)
            )
            purchase_price = max(15.0, purchase_base * (1.0 + purchase_shock_adj))

            # --- purchase volume (with buffer) ---
            buffer = self._rng.uniform(
                cfg.purchase_volume_buffer_low,
                cfg.purchase_volume_buffer_high,
            )
            purchase_volume = demand * buffer

            # --- logistics ---
            logistics_per_l = self._rng.uniform(
                cfg.logistics_cost_per_liter_low,
                cfg.logistics_cost_per_liter_high,
            )
            logistics_cost = purchase_volume * logistics_per_l

            # --- decimals ---
            s_vol = Decimal(f"{demand:.3f}")
            s_price = Decimal(f"{retail_price:.4f}")
            s_revenue = Decimal(f"{demand * retail_price:.2f}")

            p_vol = Decimal(f"{purchase_volume:.3f}")
            p_price = Decimal(f"{purchase_price:.4f}")
            p_logistics = Decimal(f"{logistics_cost:.2f}")
            p_total = Decimal(
                f"{purchase_volume * purchase_price + logistics_cost:.2f}"
            )

            sales.append(
                GeneratedSalesRow(
                    sale_date=current_date,
                    product_code=cfg.code,
                    volume_liters=s_vol,
                    revenue_rub=s_revenue,
                    avg_retail_price_rub=s_price,
                )
            )
            purchases.append(
                GeneratedPurchaseRow(
                    purchase_date=current_date,
                    product_code=cfg.code,
                    volume_liters=p_vol,
                    purchase_price_rub=p_price,
                    logistics_cost_rub=p_logistics,
                    supplier_name=supplier.name,
                    total_cost_rub=p_total,
                )
            )

        return sales, purchases


# ---------------------------------------------------------------------------
# Pure helper functions (no state)
# ---------------------------------------------------------------------------


def _seasonal_factor(*, doy: int, cfg: ProductConfig) -> float:
    primary = cfg.seasonal_amplitude * math.sin(
        2 * math.pi * (doy - cfg.seasonal_phase_shift) / 365
    )
    secondary = (cfg.seasonal_amplitude * 0.35) * math.sin(
        4 * math.pi * (doy - cfg.seasonal_phase_shift * 0.5) / 365
    )
    base = 1.0 + primary + secondary

    if cfg.seasonal_mode == "winter_peak":
        base = 2.0 - base

    return max(0.15, base)


def _holiday_demand_factor(current_date: date) -> float:
    month, day = current_date.month, current_date.day

    if month == 1 and day in NEW_YEAR_DEMAND_FACTORS:
        return NEW_YEAR_DEMAND_FACTORS[day]

    if (month, day) in RU_HOLIDAYS:
        return HOLIDAY_DEMAND_FACTOR

    for offset in range(1, PRE_HOLIDAY_DAYS + 1):
        future = current_date + timedelta(days=offset)
        if (future.month, future.day) in RU_HOLIDAYS:
            return PRE_HOLIDAY_DEMAND_FACTOR

    return 1.0


def _select_supplier(
    rng: Random,
    suppliers: tuple[SupplierConfig, ...],
) -> SupplierConfig:
    total = sum(s.weight for s in suppliers)
    roll = rng.uniform(0, total)
    cumulative = 0.0
    for s in suppliers:
        cumulative += s.weight
        if roll <= cumulative:
            return s
    return suppliers[-1]


def _date_range(*, start: date, end: date) -> list[date]:
    n = (end - start).days
    return [start + timedelta(days=i) for i in range(n + 1)]
