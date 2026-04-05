from __future__ import annotations

from pathlib import Path

from ml.features import FEATURE_NAMES

try:
    from catboost import CatBoostRegressor

    _CATBOOST_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - exercised when dependency is unavailable
    CatBoostRegressor = None  # type: ignore[assignment]
    _CATBOOST_IMPORT_ERROR = exc


def is_catboost_available() -> bool:
    return CatBoostRegressor is not None


class CatBoostDemandModel:
    def __init__(self, model: CatBoostRegressor) -> None:  # type: ignore[valid-type]
        self._model = model

    @classmethod
    def train(cls, x_train: list[list[float]], y_train: list[float]) -> "CatBoostDemandModel":
        if CatBoostRegressor is None:
            raise RuntimeError(
                "CatBoost is unavailable in the current environment"
            ) from _CATBOOST_IMPORT_ERROR
        if not x_train or not y_train:
            raise ValueError("Training data is empty")
        model = CatBoostRegressor(
            loss_function="RMSE",
            depth=6,
            learning_rate=0.05,
            iterations=250,
            random_seed=42,
            verbose=False,
            allow_writing_files=False,
        )
        model.fit(x_train, y_train)
        return cls(model)

    def predict_next(self, features: list[float]) -> float:
        return float(self._model.predict([features])[0])

    def predict_batch(self, x_values: list[list[float]]) -> list[float]:
        return [float(value) for value in self._model.predict(x_values)]

    def feature_importance_map(self) -> dict[str, float]:
        values = self._model.get_feature_importance(type="PredictionValuesChange")
        return {name: float(weight) for name, weight in zip(FEATURE_NAMES, values, strict=False)}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._model.save_model(str(path))

    @classmethod
    def load(cls, path: Path) -> "CatBoostDemandModel":
        if CatBoostRegressor is None:
            raise RuntimeError(
                "CatBoost is unavailable in the current environment"
            ) from _CATBOOST_IMPORT_ERROR
        model = CatBoostRegressor()
        model.load_model(str(path))
        return cls(model)
