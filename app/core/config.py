"""
Application configuration using Pydantic Settings
"""
from functools import lru_cache
from pathlib import Path
from typing import List
import secrets

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "Skin Disease Analysis API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # Database
    DATABASE_URL: str = "sqlite:///./skin_analysis.db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False
    
    # Security - Generate default if not provided
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    AUTH_REQUIRED: bool = False  # Set to True in production
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "https://ai-front-beta-ashy.vercel.app"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".heic"]
    FILE_RETENTION_DAYS: int = 30
    
    # ML Model
    MODEL_PATH: str = "./app/infrastructure/ml/weights/skin_efficientnet_b4_9.pth"
    MODEL_DEVICE: str = "cpu"
    MODEL_WARMUP: bool = True  # Enable warmup for testing
    PREDICTION_BATCH_SIZE: int = 1
    TOP_K_PREDICTIONS: int = 3
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False  # Disabled by default
    RATE_LIMIT_PER_MINUTE: int = 10
    
    # Monitoring
    ENABLE_METRICS: bool = True
    HEALTH_CHECK_INTERVAL: int = 60
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("UPLOAD_DIR")
    @classmethod
    def validate_upload_dir(cls, v: str) -> str:
        """Ensure upload directory exists"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_async(self) -> str:
        """Get async database URL for SQLAlchemy 2.0"""
        if self.DATABASE_URL.startswith("sqlite"):
            return self.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        elif self.DATABASE_URL.startswith("postgresql"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
