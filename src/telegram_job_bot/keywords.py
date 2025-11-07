"""Adaptive keyword management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .database import UserKeyword


@dataclass(slots=True)
class KeywordSuggestion:
    keyword: str
    sentiment: str  # "positive" or "negative"
    weight: float
    rationale: str | None = None


class KeywordManager:
    """Apply adaptive keyword logic based on user interactions."""

    def __init__(self, *, like_boost: float, dislike_penalty: float, weight_decay: float, max_keywords: int, negative_promote_at: float):
        self.like_boost = like_boost
        self.dislike_penalty = dislike_penalty
        self.weight_decay = weight_decay
        self.max_keywords = max_keywords
        self.negative_promote_at = negative_promote_at

    def decay(self, keywords: Iterable[UserKeyword]) -> None:
        for kw in keywords:
            kw.weight *= self.weight_decay

    def apply_feedback(self, keywords: List[UserKeyword], job_tokens: Sequence[str], liked: bool) -> None:
        """Reinforce or penalize keywords that match the job tokens."""

        delta = self.like_boost if liked else self.dislike_penalty
        normalized_tokens = {token.lower() for token in job_tokens}

        for keyword in keywords:
            if keyword.keyword.lower() in normalized_tokens:
                keyword.weight += delta
                if not liked and keyword.weight <= self.negative_promote_at:
                    keyword.is_negative = True
                if liked and keyword.is_negative and keyword.weight > 0:
                    keyword.is_negative = False

        self._prune(keywords)

    def merge_suggestions(self, keywords: List[UserKeyword], suggestions: Iterable[KeywordSuggestion]) -> None:
        by_term = {kw.keyword.lower(): kw for kw in keywords}

        for suggestion in suggestions:
            term = suggestion.keyword.lower()
            existing = by_term.get(term)
            weight_delta = suggestion.weight if suggestion.sentiment == "positive" else -abs(suggestion.weight)

            if existing:
                existing.weight += weight_delta
                existing.rationale = suggestion.rationale
                if existing.weight <= self.negative_promote_at:
                    existing.is_negative = True
                elif existing.weight > 0:
                    existing.is_negative = False
            else:
                keywords.append(
                    UserKeyword(
                        keyword=suggestion.keyword,
                        weight=weight_delta,
                        is_negative=weight_delta < 0,
                        rationale=suggestion.rationale,
                    )
                )

        self._prune(keywords)

    def _prune(self, keywords: List[UserKeyword]) -> None:
        positives = [kw for kw in keywords if not kw.is_negative]
        negatives = [kw for kw in keywords if kw.is_negative]
        positives.sort(key=lambda kw: kw.weight, reverse=True)
        negatives.sort(key=lambda kw: kw.weight)

        kept = positives[: self.max_keywords] + negatives
        keywords[:] = kept
