import asyncio
import inspect
import os
from copy import deepcopy

import pytest


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


SOURCE_URL = "https://publisher.example/business-investment"


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, _limit):
        return deepcopy(self.documents)


class FakeArticles:
    def __init__(self, existing=None):
        self.existing = existing or []
        self.inserted = []

    def find(self, *_args, **_kwargs):
        return FakeCursor(self.existing)

    async def insert_one(self, document):
        self.inserted.append(deepcopy(document))


class FakeNewsFeedService:
    def __init__(self, articles):
        self.articles = articles
        self.calls = 0

    async def fetch_all_feeds(self):
        self.calls += 1
        return deepcopy(self.articles)


class FakePerplexityService:
    def __init__(self, content):
        self.content = content
        self.calls = []

    async def generate_article_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.content


def candidate(**overrides):
    article = {
        "title": "Cheshire manufacturer announces major business investment",
        "content": "The source report describes a confirmed investment and expansion.",
        "summary": "The source report describes a confirmed investment and expansion.",
        "image": "https://images.example/investment.jpg",
        "category": "Business",
        "source": "Example Publisher",
        "source_url": SOURCE_URL,
        "is_cheshire_related": False,
        "is_local_source": False,
        "location": "Crewe",
        "priority_location": "Crewe",
        "publishedDate": "2026-07-22T08:00:00+00:00",
    }
    article.update(overrides)
    return article


def safe_long_content(source_tail=True):
    paragraphs = [
        "The manufacturer confirmed a new investment programme for its existing operation. "
        "The announcement explains the timetable and the work planned for the site.",
        "Company representatives said the programme will expand production capacity. "
        "The first phase covers equipment installation and preparation of the building.",
        "The project is expected to support skilled roles across the operation. "
        "Recruitment details will be published through the company's normal channels.",
        "Planning and delivery work will continue through the next financial year. "
        "The business said the schedule remains subject to the usual approvals.",
        "Local suppliers are expected to be invited to compete for suitable contracts. "
        "Procurement information will be issued as individual work packages are confirmed.",
        "The investment forms part of the company's published growth programme. "
        "Further verified updates will be released when each phase reaches completion.",
    ]
    follow_up_prefixes = (
        "A subsequent verified update states that ",
        "Published programme information also says that ",
        "The documented delivery plan further records that ",
        "A separate company update confirms that ",
        "The latest published timetable additionally notes that ",
        "Available procurement material also explains that ",
    )
    content = "\n\n".join(
        paragraphs
        + [prefix + paragraph[0].lower() + paragraph[1:] for prefix, paragraph in zip(follow_up_prefixes, paragraphs)]
    )
    if source_tail:
        content += f"\n\nRead more: {SOURCE_URL}"
    assert len(content) >= 1000
    return content


def run_sync(monkeypatch, *, rss_articles=None, generated_content=None, existing=None):
    articles = FakeArticles(existing=existing)
    news_feed = FakeNewsFeedService(rss_articles or [candidate()])
    perplexity = FakePerplexityService(generated_content or safe_long_content())

    import app.news_feed_service
    import app.perplexity_service

    monkeypatch.setattr(server, "db", type("FakeDatabase", (), {"articles": articles})())
    monkeypatch.setattr(app.news_feed_service, "news_feed_service", news_feed)
    monkeypatch.setattr(app.perplexity_service, "perplexity_service", perplexity)

    result = asyncio.run(server.sync_rss_now(authorized=True))
    return result, articles, news_feed, perplexity


def test_sync_route_remains_admin_authenticated():
    routes = [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == "/api/sync-rss-now"
        and "POST" in getattr(route, "methods", set())
    ]
    assert len(routes) == 1
    dependencies = list(routes[0].dependant.dependencies)
    assert any(dependency.call is server.get_admin_auth for dependency in dependencies)


def test_safe_article_is_sanitized_guarded_and_inserted_publicly(monkeypatch):
    original_summary = (
        "The company confirmed the investment.\n\n"
        "Work starts later this year.\n"
        f"Read more: {SOURCE_URL}"
    )
    result, articles, _news_feed, perplexity = run_sync(
        monkeypatch,
        rss_articles=[candidate(content=original_summary, summary=original_summary)],
    )

    assert result["articles_imported"] == 1
    assert len(perplexity.calls) == 1
    inserted = articles.inserted[0]
    assert inserted["archived"] is False
    assert inserted.get("manual_review_hidden_from_public") is not True
    assert inserted["verification_status"] == "ai_rewrite_auto_screened"
    assert inserted["rewrite_status"] == "ai_rewritten"
    assert inserted["ai_rewritten"] is True
    assert inserted["is_rewritten"] is True
    assert inserted["content"] == safe_long_content(source_tail=False)
    assert "\n\n" in inserted["content"]
    assert "Read more:" not in inserted["content"]
    assert SOURCE_URL not in inserted["content"]
    assert "\n" not in inserted["summary"]
    assert "Read more:" not in inserted["summary"]
    assert SOURCE_URL not in inserted["summary"]
    assert inserted["summary"] == (
        "The company confirmed the investment. Work starts later this year."
    )


def test_sync_preserves_article_metadata(monkeypatch):
    original = candidate()
    _result, articles, _news_feed, _perplexity = run_sync(
        monkeypatch,
        rss_articles=[original],
    )
    inserted = articles.inserted[0]

    for field in (
        "title",
        "image",
        "category",
        "source",
        "source_url",
        "location",
        "priority_location",
        "publishedDate",
    ):
        if field == "publishedDate":
            assert inserted[field].isoformat() == original[field]
        else:
            assert inserted[field] == original[field]
    assert inserted["scope"] == "uk"


def test_risky_invention_phrase_is_inserted_hidden_for_manual_review(monkeypatch):
    risky = safe_long_content(source_tail=False) + (
        "\n\nAccording to local residents, a spokesperson confirmed additional details."
    )
    _result, articles, _news_feed, _perplexity = run_sync(
        monkeypatch,
        generated_content=risky,
    )
    inserted = articles.inserted[0]

    assert inserted["manual_review_hidden_from_public"] is True
    assert inserted["archived"] is True
    assert inserted["verification_status"] == "needs_manual_review"
    assert inserted["rewrite_status"] == "ai_rewrite_needs_review"
    assert inserted["archive_reason"] == "needs_manual_review"
    assert inserted["manual_review_created_at"]
    assert inserted["archived_at"]
    assert "according to local residents" in inserted["manual_review_hits"]


@pytest.mark.parametrize(
    "generated_content,expected_reason",
    [
        (
            "\n\n".join([safe_long_content(False).split("\n\n")[0]] * 8),
            "AI rewrite contains duplicated paragraphs.",
        ),
        (
            "\n\n".join(
                f"The same opening words appear in this paragraph number {index}. "
                + ("Verified context follows with further material. " * 12)
                for index in range(6)
            ),
            "AI rewrite repeats the same paragraph openings or sentence structure.",
        ),
    ],
)
def test_editorial_repetition_is_inserted_hidden_for_manual_review(
    monkeypatch,
    generated_content,
    expected_reason,
):
    assert len(generated_content) >= 1000
    _result, articles, _news_feed, _perplexity = run_sync(
        monkeypatch,
        generated_content=generated_content,
    )
    inserted = articles.inserted[0]

    assert inserted["manual_review_hidden_from_public"] is True
    assert inserted["archived"] is True
    assert inserted["rewrite_status"] == "manual_review_required"
    assert expected_reason in inserted["manual_review_reason"]


def test_short_perplexity_output_remains_rejected(monkeypatch):
    result, articles, _news_feed, perplexity = run_sync(
        monkeypatch,
        generated_content="Short output.",
    )

    assert len(perplexity.calls) == 1
    assert result["articles_imported"] == 0
    assert articles.inserted == []


@pytest.mark.parametrize(
    "existing",
    [
        [{"title": candidate()["title"], "source_url": "https://other.example/story"}],
        [{"title": "Different title", "source_url": SOURCE_URL}],
    ],
)
def test_duplicate_title_or_source_url_handling_remains_unchanged(monkeypatch, existing):
    result, articles, _news_feed, perplexity = run_sync(
        monkeypatch,
        existing=existing,
    )

    assert result["articles_imported"] == 0
    assert perplexity.calls == []
    assert articles.inserted == []


def test_sync_path_does_not_call_openai_or_change_other_generation_paths():
    sync_source = inspect.getsource(server.sync_rss_now)
    scheduler_source = inspect.getsource(server.daily_article_generation)
    hybrid_source = inspect.getsource(server._import_hybrid_news_internal)

    assert "run_openai" not in sync_source
    assert "openai_service" not in sync_source
    assert "sanitize_rss_text(" in sync_source
    assert "apply_ai_manual_review_guard(" in sync_source
    assert "_generate_articles_internal(" in scheduler_source
    assert "_import_hybrid_news_internal(" in hybrid_source
