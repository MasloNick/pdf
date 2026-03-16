"""Application configuration via environment variables."""

from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # ── General ──────────────────────────────────────────────
    APP_NAME: str = "CourtCRM Pro"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "CHANGE-ME-in-production"
    ENVIRONMENT: Literal["development", "production"] = "development"

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://courtcrm:courtcrm@localhost:5432/courtcrm"
    )
    DATABASE_ECHO: bool = False

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Address DB (SQLite) ──────────────────────────────────
    ADDRESS_DB_PATH: Path = Path("data/addresses.sqlite")

    # ── JWT Auth ─────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE-ME-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # ── AI Parsing ───────────────────────────────────────────
    AI_CONFIDENCE_THRESHOLD: float = 0.65
    LOCAL_LLM_URL: str = "http://localhost:8080/v1"  # llama.cpp / vLLM
    LOCAL_LLM_MODEL: str = "MamayLM-Gemma-2-9B-IT-v0.1"
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

    # ── Backup / Export ──────────────────────────────────────
    BACKUP_DIR: Path = Path("backups")
    EXPORT_ENCRYPTION_KEY: str = ""  # AES-256 key for export files

    # ── Scheduler ────────────────────────────────────────────
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_CRON_HOUR: int = 2  # daily tasks start at 02:00

    @property
    def async_database_url(self) -> str:
        return str(self.DATABASE_URL)

    @property
    def sync_database_url(self) -> str:
        return str(self.DATABASE_URL).replace("+asyncpg", "")


settings = Settings()
