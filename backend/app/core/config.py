"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CourtCRM Pro"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://courtcrm:courtcrm@localhost:5432/courtcrm"
    DATABASE_URL_SYNC: str = "postgresql://courtcrm:courtcrm@localhost:5432/courtcrm"
    DB_ECHO: bool = False

    # SQLite address database
    ADDRESS_DB_PATH: str = "./data/addresses.sqlite"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # JWT Auth
    SECRET_KEY: str = "CHANGE-THIS-TO-RANDOM-SECRET-KEY-IN-PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # File upload
    MAX_UPLOAD_SIZE_MB: int = 100
    UPLOAD_DIR: str = "./uploads"

    # AI Parsing
    LOCAL_LLM_URL: Optional[str] = "http://localhost:8080/v1"
    CLAUDE_API_KEY: Optional[str] = None
    AI_CONFIDENCE_THRESHOLD: float = 0.65

    # Backup
    BACKUP_DIR: str = "./backups"
    BACKUP_ENCRYPTION_KEY: Optional[str] = None

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
