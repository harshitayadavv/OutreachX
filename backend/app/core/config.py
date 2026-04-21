from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Absolute path to .env — works regardless of where Python is launched from.
# This file: backend/app/core/config.py
# .env lives: backend/.env  ->  go up 3 levels (core -> app -> backend)
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # LLM
    groq_api_key: str = ""

    # Discovery
    serpapi_api_key: str = ""

    # Contact finders (Phase 2)
    hunter_api_key: str = ""
    apollo_api_key: str = ""

    # Database (Phase 3)
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/outreachx"

    # Redis (Phase 3)
    redis_url: str = "redis://localhost:6379"

    # Email (Phase 6)
    sendgrid_api_key: str = ""
    from_email: str = ""

    # SMTP fallback
    smtp_host:     str = "smtp.gmail.com"
    smtp_port:     int = 587
    smtp_user:     str = ""
    smtp_password: str = ""

    # App
    app_env: str = "development"
    secret_key: str = "change-me"

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings -- reads .env once from an absolute path."""
    s = Settings()
    loaded = "found" if ENV_FILE.exists() else "NOT FOUND -- check path"
    print(f"[Config] .env -> {ENV_FILE}  [{loaded}]")
    print(f"[Config] GROQ_API_KEY    : {'SET' if s.groq_api_key else 'not set'}")
    print(f"[Config] SERPAPI_API_KEY : {'SET' if s.serpapi_api_key else 'not set'}")
    return s