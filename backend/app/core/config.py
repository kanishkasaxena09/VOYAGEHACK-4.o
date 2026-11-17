import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Intelligent Virtual Travel Agent"
    DEBUG: bool = True

    # Security & JWT
    SECRET_KEY: str = "development_secret_key_needs_to_be_at_least_32_bytes_long_12345"
    JWT_SECRET_KEY: str = "development_secret_key_needs_to_be_at_least_32_bytes_long_12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./travel_agent.db"

    # AI / Groq API
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Travel Providers
    TRAVEL_API_MODE: str = "mock"
    AMADEUS_CLIENT_ID: str | None = None
    AMADEUS_CLIENT_SECRET: str | None = None

    # Redis / Caching
    REDIS_URL: str = "redis://localhost:6379"

    # Logging
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # File paths
    MOCK_DATA_DIR: Path = BASE_DIR / "mock_data"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
