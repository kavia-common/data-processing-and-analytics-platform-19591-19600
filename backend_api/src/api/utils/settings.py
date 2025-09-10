from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class AppSettings(BaseSettings):
    """
    Application settings read from environment variables.
    See .env.example for the list of supported variables.
    """

    # Directories
    DATA_DIR: str = Field(default="./data")
    UPLOAD_DIR: str = Field(default="./data/uploads")
    OUTPUT_DIR: str = Field(default="./data/outputs")
    REPORTS_DIR: str = Field(default="./data/reports")
    VIZ_DIR: str = Field(default="./data/viz")

    # CORS
    ALLOW_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # Docs
    DOCS_URL: Optional[str] = Field(default="/docs")
    REDOC_URL: Optional[str] = Field(default="/redoc")

    # SMTP
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: Optional[int] = Field(default=None)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_FROM: Optional[str] = Field(default=None)
    SMTP_USE_TLS: bool = Field(default=True)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings() -> AppSettings:
    """
    Create or retrieve the cached AppSettings instance.
    """
    return AppSettings()
