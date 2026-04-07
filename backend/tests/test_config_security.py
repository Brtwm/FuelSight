from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_short_jwt_secret_is_allowed_for_local_env() -> None:
    settings = Settings(app_env="local", jwt_secret_key="short-secret")
    assert settings.jwt_secret_key == "short-secret"


def test_short_jwt_secret_is_allowed_for_test_env() -> None:
    settings = Settings(app_env="test", jwt_secret_key="short-secret")
    assert settings.jwt_secret_key == "short-secret"


def test_short_jwt_secret_is_rejected_outside_local_and_test() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production", jwt_secret_key="short-secret")


def test_long_jwt_secret_is_accepted_outside_local_and_test() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret_key="phase9-production-like-secret-with-32-plus-chars",
    )
    assert len(settings.jwt_secret_key) >= 32
