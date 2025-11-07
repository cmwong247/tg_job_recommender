from telegram_job_bot.adzuna_client import JobPosting
from telegram_job_bot.database import UserKeyword
from telegram_job_bot.recommender import JobRecommender


def test_recommender_scores_positive_keywords():
    posting = JobPosting(
        job_id="1",
        title="Senior Python Engineer",
        company="ACME",
        location="Remote",
        description="Looking for a python expert",
        url="http://example.com",
        created=None,
    )
    recommender = JobRecommender(max_keyword_contribution=5.0)
    keywords = [
        UserKeyword(keyword="python", weight=2.0, is_negative=False),
        UserKeyword(keyword="remote", weight=1.0, is_negative=False),
    ]

    scored = recommender.score_jobs([posting], keywords)
    assert scored
    assert scored[0].score > 0
    assert "python" in scored[0].matched_keywords


def test_negative_keywords_penalize_scores():
    posting = JobPosting(
        job_id="2",
        title="Contract React Developer",
        company="ACME",
        location="Singapore",
        description="6 month contract role",
        url="http://example.com",
        created=None,
    )
    recommender = JobRecommender()
    keywords = [
        UserKeyword(keyword="contract", weight=-2.0, is_negative=True),
    ]

    scored = recommender.score_jobs([posting], keywords)
    assert not scored
