import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Force pydantic-settings to read from .env by clearing any global env overrides for Groq
if "GROQ_API_KEY" in os.environ:
    del os.environ["GROQ_API_KEY"]

class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_SECRET_KEY: str = "changeme"
    DEBUG: bool = True

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "devos_db"
    DB_USER: str = "devos_user"
    DB_PASSWORD: str = "password"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # GitHub
    GITHUB_TOKEN: str = ""

    # LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # JWT
    JWT_SECRET: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = Path(__file__).resolve().parents[2] / ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
