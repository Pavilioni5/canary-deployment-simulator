"""
Configuration settings for the Canary Deployment Simulator.
Loads settings from environment variables or .env file.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Cloud-Based Canary Deployment Simulator"
    PROJECT_ID: str = "P71"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Security & JWT
    SECRET_KEY: str = "canary-deployment-simulator-academic-secret-key-p71-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Initial Admin Credentials
    DEFAULT_ADMIN_EMAIL: str = "admin@canary.local"
    DEFAULT_ADMIN_PASSWORD: str = "AdminSecurePassword123!"
    DEFAULT_ADMIN_NAME: str = "Academic Admin"

    # Database
    DATABASE_URL: str = "sqlite:///./canary_simulator.db"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
