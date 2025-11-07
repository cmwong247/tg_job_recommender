from telegram_job_bot.keywords import KeywordManager, KeywordSuggestion
from telegram_job_bot.database import UserKeyword


def test_merge_suggestions_prioritizes_top_keywords():
    manager = KeywordManager(like_boost=1.0, dislike_penalty=-1.0, weight_decay=0.9, max_keywords=2, negative_promote_at=-2.0)
    keywords = [
        UserKeyword(keyword="python", weight=1.5, is_negative=False),
        UserKeyword(keyword="remote", weight=1.0, is_negative=False),
    ]

    manager.merge_suggestions(
        keywords,
        [
            KeywordSuggestion(keyword="django", sentiment="positive", weight=1.6),
            KeywordSuggestion(keyword="python", sentiment="positive", weight=0.4),
        ],
    )

    assert any(kw.keyword == "django" for kw in keywords)
    assert any(kw.keyword == "python" and kw.weight > 1.5 for kw in keywords)
    assert len([kw for kw in keywords if not kw.is_negative]) == 2


def test_apply_feedback_promotes_negatives():
    manager = KeywordManager(like_boost=1.0, dislike_penalty=-1.0, weight_decay=0.9, max_keywords=4, negative_promote_at=-1.0)
    keywords = [
        UserKeyword(keyword="contract", weight=-0.5, is_negative=False),
    ]

    manager.apply_feedback(keywords, ["contract", "role"], liked=False)
    assert keywords[0].is_negative
