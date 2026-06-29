"""
config/settings.py
Central configuration — reads from .env, exposes typed settings.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "3306")))
    name: str = field(default_factory=lambda: os.getenv("DB_NAME", "finance_analyzer"))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))

    @property
    def url(self) -> str:
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}?charset=utf8mb4"
        )


@dataclass(frozen=True)
class AppConfig:
    title: str = "AI Personal Finance Analyzer"
    version: str = "1.0.0"
    page_icon: str = "💰"
    layout: str = "wide"
    categories: tuple = (
        "Food",
        "Transport",
        "Shopping",
        "Bills",
        "Entertainment",
        "Healthcare",
        "Income",
        "Other",
    )
    anomaly_contamination: float = 0.05
    gemini_model: str = "gemini-1.5-flash"
    gemini_api_key: str = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", "")
    )


DB_CONFIG = DatabaseConfig()
APP_CONFIG = AppConfig()
