from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

# Load .env from project root (container root)
load_dotenv()


class Settings(BaseModel):
    """Central application settings loaded from environment variables."""

    ENV: str = Field(default=os.getenv("ENV", "development"), description="Application environment")
    DATA_DIR: str = Field(default=os.getenv("DATA_DIR", "data/uploads"), description="Directory for uploaded files")
    RESULTS_DIR: str = Field(default=os.getenv("RESULTS_DIR", "data/results"), description="Directory for results/exports")
    SMTP_HOST: str = Field(default=os.getenv("SMTP_HOST", ""), description="SMTP server host")
    SMTP_PORT: int = Field(default=int(os.getenv("SMTP_PORT", "587")), description="SMTP server port")
    SMTP_USER: str = Field(default=os.getenv("SMTP_USER", ""), description="SMTP user/login")
    SMTP_PASSWORD: str = Field(default=os.getenv("SMTP_PASSWORD", ""), description="SMTP password/secret")
    SMTP_TLS: bool = Field(default=(os.getenv("SMTP_TLS", "true").lower() == "true"), description="Use TLS for SMTP connection")
    DEFAULT_REPORT_RECIPIENT: EmailStr | None = Field(default=os.getenv("DEFAULT_REPORT_RECIPIENT") or None, description="Default recipient for summary reports")
    SUPPORT_EMAIL: EmailStr = Field(default=os.getenv("SUPPORT_EMAIL", "support@example.com"), description="Support contact email")
    SITE_URL: str = Field(default=os.getenv("SITE_URL", "http://localhost:3001"), description="Public site URL")
    CORS_ALLOW_ORIGINS: List[str] = Field(default_factory=lambda: os.getenv("CORS_ALLOW_ORIGINS", "*").split(","))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    PUBLIC_INTERFACE
    Return a cached Settings instance.
    """
    settings = Settings()
    # Ensure directories exist
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    return settings
