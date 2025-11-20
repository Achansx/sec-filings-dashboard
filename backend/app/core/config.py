"""
Application configuration management using Pydantic Settings.
"""
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    PROJECT_NAME: str = "SEC Filings Dashboard"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Database
    POSTGRES_USER: str = "secfilings"
    POSTGRES_PASSWORD: str = "secfilings_dev"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "secfilings"
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """Assemble database URL from components if not provided."""
        if isinstance(v, str):
            return v
        return (
            f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_HOST')}:"
            f"{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
        )

    # Test Database
    TEST_DATABASE_URL: Optional[str] = None

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_dev_password"
    REDIS_URL: Optional[str] = None

    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
        """Assemble Redis URL from components if not provided."""
        if isinstance(v, str):
            return v
        password = values.get('REDIS_PASSWORD')
        if password:
            return (
                f"redis://:{password}@{values.get('REDIS_HOST')}:"
                f"{values.get('REDIS_PORT')}/0"
            )
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/0"

    # Elasticsearch
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_URL: Optional[str] = None

    @validator("ELASTICSEARCH_URL", pre=True)
    def assemble_elasticsearch_connection(cls, v: Optional[str], values: dict) -> str:
        """Assemble Elasticsearch URL from components if not provided."""
        if isinstance(v, str):
            return v
        return f"http://{values.get('ELASTICSEARCH_HOST')}:{values.get('ELASTICSEARCH_PORT')}"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # SEC API
    SEC_API_USER_AGENT: str = "your-name your-email@example.com"
    SEC_API_RATE_LIMIT: int = 10  # requests per second

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @validator("CELERY_BROKER_URL", pre=True)
    def assemble_celery_broker(cls, v: Optional[str], values: dict) -> str:
        """Use Redis URL as Celery broker."""
        if isinstance(v, str):
            return v
        return values.get("REDIS_URL", "")

    @validator("CELERY_RESULT_BACKEND", pre=True)
    def assemble_celery_backend(cls, v: Optional[str], values: dict) -> str:
        """Use Redis URL as Celery result backend."""
        if isinstance(v, str):
            return v
        return values.get("REDIS_URL", "")

    # Database Connection Pool Settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )


# Create global settings instance
settings = Settings()
