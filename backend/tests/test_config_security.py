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
        database_url="postgresql+psycopg://fuelsight:strong-password@db:5432/fuelsight",
    )
    assert len(settings.jwt_secret_key) >= 32


def test_known_placeholder_jwt_secret_is_rejected_in_production() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            jwt_secret_key="change-me-at-least-32-characters-secret",
            database_url="postgresql+psycopg://fuelsight:strong-password@db:5432/fuelsight",
        )


def test_production_template_jwt_placeholder_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            jwt_secret_key="GENERATE_AT_LEAST_32_RANDOM_CHARACTERS",
            database_url="postgresql+psycopg://fuelsight:strong-password@db:5432/fuelsight",
        )


def test_api_docs_default_to_disabled_in_production() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret_key="production-secret-with-more-than-32-characters",
        database_url="postgresql+psycopg://fuelsight:strong-password@db:5432/fuelsight",
    )

    assert settings.enable_api_docs is False


def test_api_docs_default_to_enabled_locally() -> None:
    assert Settings().enable_api_docs is True


def test_production_rejects_default_database_credentials() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            jwt_secret_key="production-secret-with-more-than-32-characters",
        )


def test_production_rejects_database_template_placeholder() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            jwt_secret_key="production-secret-with-more-than-32-characters",
            database_url=(
                "postgresql+psycopg://fuelsight:"
                "GENERATE_A_UNIQUE_DATABASE_PASSWORD@db:5432/fuelsight"
            ),
        )


def test_production_accepts_non_default_database_credentials() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret_key="production-secret-with-more-than-32-characters",
        database_url="postgresql+psycopg://fuelsight:strong-password@db:5432/fuelsight",
    )

    assert settings.app_env == "production"


def test_unsupported_jwt_algorithm_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(jwt_algorithm="none")


def test_cors_origins_default_to_empty_in_production() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret_key="production-secret-with-more-than-32-characters",
        database_url="postgresql+psycopg://fuelsight:strong-password@db:5432/fuelsight",
    )

    assert settings.cors_origins == []


def test_cloud_first_neuraldeep_requires_real_api_key() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            jwt_secret_key="production-secret-with-more-than-32-characters",
            database_url="postgresql+psycopg://fuelsight:strong-password@db:5432/fuelsight",
            enable_llm=True,
            llm_provider_mode="cloud_first",
            llm_provider="neuraldeep",
            llm_api_key="COPY_FROM_LOCAL_ENV_WITHOUT_CHANGES",
        )


def test_phase0_v2_settings_defaults_are_valid() -> None:
    settings = Settings()
    assert settings.external_indicators_mode == "manual_snapshot"
    assert settings.llm_provider_mode == "retrieval_only"
    assert settings.defense_profile == "offline-safe"
    assert settings.import_max_upload_bytes == 10_485_760
    assert settings.import_max_rows == 50_000
    assert settings.fuelsight_seed_demo_users is True


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
