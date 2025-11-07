"""Application configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
import os
from typing import List

try:  # pragma: no cover - optional dependency for local development convenience
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    def load_dotenv() -> bool:  # type: ignore
        return False


load_dotenv()


@dataclass(slots=True)
class Settings:
    """Runtime configuration resolved from environment variables."""

    telegram_token: str = field(default_factory=lambda: _require("TELEGRAM_BOT_TOKEN"))
    adzuna_app_id: str = field(default_factory=lambda: _require("ADZUNA_APP_ID"))
    adzuna_app_key: str = field(default_factory=lambda: _require("ADZUNA_APP_KEY"))
    adzuna_country: str = field(default="sg")
    adzuna_results_per_page: int = field(default=25)
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./job_bot.db"))

    like_boost: float = 1.0
    dislike_penalty: float = -1.0
    weight_decay: float = 0.98
    negative_promote_at: float = -2.0
    max_keywords: int = 8

    daily_job_count: int = 5
    realtime_min_count: int = 2
    realtime_max_count: int = 3

    default_notification_time: time = field(default=time(hour=9, minute=0))
    notification_slots: List[time] = field(default_factory=lambda: _generate_half_hour_slots())

    @property
    def adzuna_base_url(self) -> str:
        return f"https://api.adzuna.com/v1/api/jobs/{self.adzuna_country}/search"


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _generate_half_hour_slots() -> List[time]:
    return [time(hour=h, minute=m) for h in range(0, 24) for m in (0, 30)]
