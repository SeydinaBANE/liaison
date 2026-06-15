"""Configuration applicative chargee depuis l'environnement (12-factor)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parametres applicatifs, prefixes ``LIAISON_`` et charges depuis ``.env``."""

    model_config = SettingsConfigDict(
        env_prefix="LIAISON_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "local"
    log_level: str = "INFO"

    llm_provider: str = "bedrock"
    llm_model_primary: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    llm_model_fallback: str = "anthropic.claude-3-5-haiku-20241022-v1:0"
    llm_api_base: str = ""
    llm_api_key: str = ""

    sql_dsn: str = "postgresql+psycopg://liaison:liaison@localhost:5432/businessdb"
    sql_readonly: bool = True
    sql_allowed_tables: tuple[str, ...] = Field(
        default=("customers", "orders", "invoices", "tickets")
    )

    erp_base_url: str = "http://localhost:9000"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retourne l'instance unique de configuration (mise en cache)."""
    return Settings()
