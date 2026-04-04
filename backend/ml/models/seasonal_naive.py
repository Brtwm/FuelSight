from __future__ import annotations

from dataclasses import dataclass
from statistics import pstdev


@dataclass
class SeasonalNaiveModel:
    seasonal_period: int = 7
    residual_std: float = 0.0

    def fit(self, values: list[float]) -> "SeasonalNaiveModel":
        if len(values) <= self.seasonal_period:
            self.residual_std = 0.0
            return self
        residuals: list[float] = []
        for idx in range(self.seasonal_period, len(values)):
            residuals.append(values[idx] - values[idx - self.seasonal_period])
        self.residual_std = pstdev(residuals) if len(residuals) > 1 else 0.0
        return self

    def predict_next(self, values: list[float]) -> float:
        if not values:
            raise ValueError("values are required")
        if len(values) < self.seasonal_period:
            return values[-1]
        return values[-self.seasonal_period]

    def forecast(self, values: list[float], horizon_days: int) -> list[float]:
        if horizon_days < 1:
            raise ValueError("horizon_days must be >= 1")
        history = [float(value) for value in values]
        forecast: list[float] = []
        for _ in range(horizon_days):
            next_value = max(0.0, self.predict_next(history))
            history.append(next_value)
            forecast.append(next_value)
        return forecast
