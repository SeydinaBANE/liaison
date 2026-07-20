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
    qdrant_url: str = ""
    qdrant_collection: str = "liaison"

    api_keys: tuple[str, ...] = Field(
        default=("dev-key-viewer:viewer", "dev-key-operator:operator"),
        description="colon-separated key:role pairs",
    )

    @property
    def api_key_mapping(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for entry in self.api_keys:
            if ":" in entry:
                key, role = entry.split(":", 1)
                mapping[key] = role
        return mapping

    rate_limit_max_requests: int = 60
    rate_limit_window_sec: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retourne l'instance unique de configuration (mise en cache)."""
    return Settings()
