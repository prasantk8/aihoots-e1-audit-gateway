"""Configuration via environment variables only — no secrets in code (SECURITY.md).

Uses pydantic-settings so every value is typed, documented, and overridable via
env. Defaults are safe for local `docker compose up`.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIHOOTS_", env_file=".env")

    # Where the SLM backend lives (the containerized model, ADR-002).
    upstream_base_url: str = "http://model:8080"
    upstream_timeout_s: float = 60.0
    default_model: str = "qwen2.5-3b-instruct"

    # Append-only audit log (ADR-001).
    audit_log_path: str = "/data/audit.jsonl"


settings = Settings()
