"""Adzuna API client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping

import requests

from .config import Settings


@dataclass(slots=True)
class JobPosting:
    job_id: str
    title: str
    company: str | None
    location: str | None
    description: str | None
    url: str | None
    created: str | None


class AdzunaClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def search(self, keywords: Iterable[str], *, page: int = 1, where: str = "Singapore") -> List[JobPosting]:
        params = {
            "app_id": self.settings.adzuna_app_id,
            "app_key": self.settings.adzuna_app_key,
            "results_per_page": self.settings.adzuna_results_per_page,
            "what": " ".join(keywords),
            "where": where,
            "sort_by": "date",
        }

        url = f"{self.settings.adzuna_base_url}/{page}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        return [self._to_posting(item) for item in payload.get("results", [])]

    @staticmethod
    def _to_posting(item: Mapping) -> JobPosting:
        return JobPosting(
            job_id=str(item.get("id")),
            title=item.get("title", ""),
            company=(item.get("company") or {}).get("display_name"),
            location=(item.get("location") or {}).get("display_name"),
            description=item.get("description"),
            url=item.get("redirect_url"),
            created=item.get("created"),
        )
