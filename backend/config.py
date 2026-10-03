import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./placement.db")
    ai_provider: str | None = os.getenv("AI_PROVIDER") or None
    ai_api_key: str | None = os.getenv("AI_API_KEY") or None
    ai_model: str | None = os.getenv("AI_MODEL") or None
    ai_base_url: str | None = os.getenv("AI_BASE_URL") or None


settings = Settings()