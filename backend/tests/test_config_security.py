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


def test_phase0_v2_settings_defaults_are_valid() -> None:
    settings = Settings()
    assert settings.external_indicators_mode == "manual_snapshot"
    assert settings.llm_provider_mode == "retrieval_only"
    assert settings.defense_profile == "offline-safe"


def test_invalid_external_indicators_mode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(external_indicators_mode="unknown")


def test_invalid_llm_provider_mode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(llm_provider_mode="cloud_only")


def test_invalid_llm_provider_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(llm_provider="unsupported")


def test_phase_i_llm_settings_defaults_are_safe() -> None:
    settings = Settings()
    assert settings.llm_timeout_seconds == 60.0
    assert settings.llm_max_evidence_chars == 6000
    assert settings.llm_embedding_dimensions == 64


def test_llm_embedding_dimensions_matches_rag_vector_schema() -> None:
    with pytest.raises(ValidationError):
        Settings(llm_embedding_dimensions=768)


def test_invalid_defense_profile_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(defense_profile="online-only")
