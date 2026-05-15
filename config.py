# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Улучшенная конфигурация с использованием pydantic-settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore"
    )

    # === Основные настройки приложения ===
    APP_NAME: str = "Repo Validator Agent"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 80

    # === Безопасность и лимиты ===
    MAX_REPO_SIZE_MB: int = 150
    ANALYSIS_TIMEOUT_SEC: int = 1800          # 30 минут
    MAX_SESSIONS: int = 50
    SESSION_TTL_SECONDS: int = 3600 * 2       # 2 часа

    # === Redis (будет использоваться позже) ===
    REDIS_URL: str = "redis://localhost:6379/0"

    # === CORS ===
    ALLOWED_ORIGINS: List[str] = [
        "https://prizolov.ru",
        "http://prizolov.ru",
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:3000",
    ]

    # === GitHub Integration ===
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None

    # === LLM / AI ===
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"   # или yandex, grok и т.д.
    MAX_TOKENS_PER_REQUEST: int = 8000


# Singleton
settings = Settings()
