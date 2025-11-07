"""Job scoring utilities."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .adzuna_client import JobPosting
from .database import UserKeyword


@dataclass(slots=True)
class ScoredJob:
    job: JobPosting
    score: float
    matched_keywords: List[str]


class JobRecommender:
    def __init__(self, *, max_keyword_contribution: float = 2.0):
        self.max_keyword_contribution = max_keyword_contribution

    def score_jobs(self, postings: Iterable[JobPosting], keywords: Sequence[UserKeyword]) -> List[ScoredJob]:
        keyword_weights = {kw.keyword.lower(): kw.weight for kw in keywords if kw.weight > 0 and not kw.is_negative}
        negative_terms = {kw.keyword.lower(): kw.weight for kw in keywords if kw.is_negative}

        scored: List[ScoredJob] = []
        for posting in postings:
            tokens = self._tokenize(posting)
            score, matched = self._score_tokens(tokens, keyword_weights, negative_terms)
            if score > 0:
                scored.append(ScoredJob(job=posting, score=score, matched_keywords=matched))
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored

    def _score_tokens(self, tokens: Counter, positives: dict[str, float], negatives: dict[str, float]) -> tuple[float, List[str]]:
        total = 0.0
        matched: List[str] = []

        for term, weight in positives.items():
            match_count = tokens.get(term, 0)
            if match_count:
                contribution = min(weight * match_count, self.max_keyword_contribution)
                total += contribution
                matched.append(term)

        for term, weight in negatives.items():
            if tokens.get(term, 0):
                total += weight  # weight is negative

        return total, matched

    def _tokenize(self, posting: JobPosting) -> Counter:
        tokens = []
        for value in (posting.title, posting.description or ""):
            if value:
                tokens.extend(token.strip(".,!()[]{}:/\\\"'?").lower() for token in value.split())
        return Counter(tokens)
