"""Application settings for FuelSight backend."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings loaded from environment."""

    app_env: str = Field(default="local", min_length=1)
    app_port: int = Field(default=8061, ge=1, le=65535)
    app_name: str = Field(default="FuelSight API", min_length=1)
    app_version: str = Field(default="0.1.0", min_length=1)

    database_url: str = Field(
        default="postgresql+psycopg://fuelsight:fuelsight@localhost:5432/fuelsight",
        min_length=1,
    )

    jwt_secret_key: str = Field(default="change-me", min_length=1)
    jwt_algorithm: str = Field(default="HS256", min_length=1)
    jwt_access_ttl_min: int = Field(default=30, ge=1)
    jwt_refresh_ttl_days: int = Field(default=7, ge=1)
    auth_refresh_cookie_name: str = Field(default="fuelsight_refresh_token", min_length=1)
    auth_refresh_cookie_path: str = Field(default="/api/v1/auth", min_length=1)

    enable_llm: bool = False
    kpi_low_margin_threshold_rub_per_liter: float = Field(default=3.0, gt=0)
    model_artifacts_dir: str = Field(default="/opt/fuelsight/artifacts/models", min_length=1)
    news_index_dir: str = Field(default="/opt/fuelsight/artifacts/news", min_length=1)
    news_provider: str = Field(default="gdelt", min_length=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
