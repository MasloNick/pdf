"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # -- General --
    APP_NAME: str = "CourtCRM Pro"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # -- Database --
    DATABASE_URL: str = "postgresql+asyncpg://courtcrm:courtcrm@localhost:5432/courtcrm"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://courtcrm:courtcrm@localhost:5432/courtcrm"
    ADDRESS_DB_PATH: str = "data/address.sqlite"

    # -- Redis --
    REDIS_URL: str = "redis://localhost:6379/0"

    # -- Auth / JWT --
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # -- Celery --
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # -- AI Parser --
    AI_MODEL_PATH: str = ""  # path to local GGUF model
    CLAUDE_API_KEY: str = ""
    AI_CONFIDENCE_THRESHOLD: float = 0.65

    # -- Export encryption --
    EXPORT_ENCRYPTION_KEY: str = ""

    # -- Backup --
    BACKUP_DIR: str = "/var/backups/courtcrm"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}


settings = Settings()
