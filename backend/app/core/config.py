"""Application settings for FuelSight backend skeleton."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_port: int = 8061
    app_name: str = "FuelSight API"
    app_version: str = "0.1.0"

    database_url: str = "postgresql+psycopg://fuelsight:fuelsight@localhost:5432/fuelsight"

    jwt_secret_key: str = "change-me"
    jwt_access_ttl_min: int = 30
    jwt_refresh_ttl_days: int = 7

    enable_llm: bool = False
    model_artifacts_dir: str = "/opt/fuelsight/artifacts/models"
    news_index_dir: str = "/opt/fuelsight/artifacts/news"
    news_provider: str = "gdelt"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
