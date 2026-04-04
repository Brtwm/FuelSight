from __future__ import annotations

import math


def mae(actual: list[float], predicted: list[float]) -> float:
    if not actual or not predicted or len(actual) != len(predicted):
        raise ValueError("actual and predicted must have the same non-empty length")
    return sum(abs(a - p) for a, p in zip(actual, predicted, strict=True)) / len(actual)


def rmse(actual: list[float], predicted: list[float]) -> float:
    if not actual or not predicted or len(actual) != len(predicted):
        raise ValueError("actual and predicted must have the same non-empty length")
    mse = sum((a - p) ** 2 for a, p in zip(actual, predicted, strict=True)) / len(actual)
    return math.sqrt(mse)


def smape(actual: list[float], predicted: list[float]) -> float:
    if not actual or not predicted or len(actual) != len(predicted):
        raise ValueError("actual and predicted must have the same non-empty length")
    values: list[float] = []
    for a, p in zip(actual, predicted, strict=True):
        denominator = (abs(a) + abs(p)) / 2.0
        if denominator <= 1e-9:
            values.append(0.0)
            continue
        values.append(abs(a - p) / denominator)
    return (sum(values) / len(values)) * 100.0
