import asyncio
import inspect
import os
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


SOURCE_URL = "https://publisher.example/feed-story"


def full_quality_content(*, source_tail=False):
    paragraphs = [
        (
            "The manufacturer confirmed an investment programme for its existing operation. "
            "Published plans set out the equipment covered by the first phase. "
            "Work is due to begin after the required approvals are complete."
        ),
        (
            "Company representatives said production will continue during installation. "
            "Contractors will work alongside the existing engineering team. "
            "Access arrangements will be reviewed before construction begins."
        ),
        (
            "Local suppliers will be able to compete for suitable work packages. "
            "Procurement notices will be issued as individual contracts are prepared. "
            "No final value for those contracts has yet been published."
        ),
        (
            "Training will take place before upgraded equipment enters service. "
            "Managers will assess staffing requirements during each delivery phase. "
            "Recruitment details will be released through official company channels."
        ),
        (
            "Planning documents describe how deliveries will be managed at the site. "
            "Normal operations are expected to continue while the work is carried out. "
            "Any further applications will follow the standard public process."
        ),
        (
            "The programme forms part of the company’s published growth plan. "
            "Spending will be phased across the announced implementation timetable. "
            "Financial details beyond that programme have not been disclosed."
        ),
        (
            "Project managers will report progress against the confirmed milestones. "
            "Updates will cover completed work and the next scheduled installation. "
            "The timetable remains subject to the conditions in formal approvals."
        ),
        (
            "The next public update is expected after enabling work is complete. "
            "It will set out progress against the schedule already announced. "
            "Verified information will continue to be released through official channels."
        ),
    ]
    content = "\n\n".join(paragraphs)
    if source_tail:
        content += f"\n\nRead more: {SOURCE_URL}"
    assert len(content) >= 1000
    return content


def candidate(**overrides):
    item = {
        "id": "feed-id",
        "title": "Manufacturer confirms investment programme",
        "content": full_quality_content(),
        "summary": "A manufacturer has confirmed an investment programme.",
        "source": "Example Publisher",
        "source_url": SOURCE_URL,
        "category": "Business",
        "image": "https://images.example/investment.jpg",
        "scope": "uk",
        "location": None,
        "priority_location": None,
        "publishedDate": "2026-07-23T10:00:00+00:00",
        "is_real_news": True,
    }
    item.update(overrides)
    return item


class FakeCursor:
    def __init__(self, documents):
        self.documents = deepcopy(documents)

    async def to_list(self, _limit):
        return deepcopy(self.documents)


class FakeArticles:
    def __init__(self, existing=()):
        self.existing = list(existing)
        self.find_calls = []
        self.inserted = []

    def find(self, query, projection):
        self.find_calls.append((deepcopy(query), deepcopy(projection)))
        return FakeCursor(self.existing)

    async def insert_one(self, document):
        self.inserted.append(deepcopy(document))
        return SimpleNamespace(inserted_id="inserted")


class FakeFeed:
    def __init__(self, articles):
        self.articles = deepcopy(articles)
        self.all_calls = 0
        self.category_calls = []

    async def fetch_all_feeds(self):
        self.all_calls += 1
        return deepcopy(self.articles)

    async def fetch_category_feeds(self, category):
        self.category_calls.append(category)
        return deepcopy(self.articles)


def run_import(monkeypatch, articles, *, existing=(), category=None):
    collection = FakeArticles(existing)
    feed = FakeFeed(articles)
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))
    monkeypatch.setattr(server, "news_feed_service", feed)
    result = asyncio.run(
        server.import_real_news(
            limit=20,
            category=category,
            authorized=True,
        )
    )
    return result, collection, feed


def route_dependencies(route):
    pending = list(route.dependant.dependencies)
    calls = set()
    while pending:
        dependency = pending.pop()
        calls.add(dependency.call)
        pending.extend(dependency.dependencies)
    return calls


def test_route_remains_admin_authenticated():
    routes = [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == "/api/import-real-news"
        and "POST" in getattr(route, "methods", set())
    ]
    assert len(routes) == 1
    assert routes[0].endpoint is server.import_real_news
    assert server.get_admin_auth in route_dependencies(routes[0])


def test_unauthenticated_request_reaches_no_feed_database_image_or_guard(monkeypatch):
    class Untouched:
        touched = False

        def __getattr__(self, name):
            self.touched = True
            raise AssertionError(f"unexpected unauthenticated access: {name}")

    database = Untouched()
    feed = Untouched()

    async def fail_image(*_args, **_kwargs):
        raise AssertionError("image collaborator must not run before authentication")

    def fail_guard(*_args, **_kwargs):
        raise AssertionError("guard must not run before authentication")

    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "news_feed_service", feed)
    monkeypatch.setattr(server, "get_dynamic_image", fail_image)
    monkeypatch.setattr(server, "apply_ai_manual_review_guard", fail_guard)

    response = TestClient(server.app).post("/api/import-real-news")

    assert response.status_code == 401
    assert database.touched is False
    assert feed.touched is False


def test_existing_title_and_source_url_duplicates_remain_skipped(monkeypatch):
    duplicate_title = candidate(source_url="https://publisher.example/new-url")
    duplicate_url = candidate(
        title="A different feed title",
        source_url=SOURCE_URL.upper(),
    )
    result, collection, _feed = run_import(
        monkeypatch,
        [duplicate_title, duplicate_url],
        existing=[
            {
                "title": duplicate_title["title"].upper(),
                "source_url": SOURCE_URL,
            }
        ],
    )

    assert collection.inserted == []
    assert result["imported"] == 0
    assert result["skipped"] == 2
    assert result["total_fetched"] == 2


def test_body_and_summary_are_sanitized_before_public_insert(monkeypatch):
    article = candidate(
        content=full_quality_content(source_tail=True),
        summary=f"A compact summary.\n\nContinue reading: {SOURCE_URL}",
    )
    result, collection, _feed = run_import(monkeypatch, [article])
    saved = collection.inserted[0]

    assert result["imported"] == 1
    assert saved["content"] == full_quality_content()
    assert saved["summary"] == "A compact summary."
    assert SOURCE_URL not in saved["content"]
    assert "\n" not in saved["summary"]


def test_safe_full_quality_record_inserts_publicly_and_preserves_metadata(monkeypatch):
    article = candidate(
        custom_provenance="feed-metadata",
        location="Warrington",
        priority_location="Warrington",
    )
    result, collection, feed = run_import(
        monkeypatch,
        [article],
        category="Business",
    )
    saved = collection.inserted[0]

    assert result["imported"] == 1
    assert result["skipped"] == 0
    assert feed.category_calls == ["Business"]
    assert len(collection.inserted) == 1
    assert saved.get("manual_review_hidden_from_public") is not True
    for field in (
        "source",
        "source_url",
        "category",
        "image",
        "scope",
        "location",
        "priority_location",
        "custom_provenance",
    ):
        assert saved[field] == article[field]
    assert saved["publishedDate"] == datetime.fromisoformat(
        article["publishedDate"]
    )


def test_short_useful_record_is_retained_hidden_for_manual_review(monkeypatch):
    result, collection, _feed = run_import(
        monkeypatch,
        [
            candidate(
                content="A useful confirmed feed report with limited detail.",
                image_source="rss_feed",
            )
        ],
    )
    saved = collection.inserted[0]

    assert result["imported"] == 1
    assert saved["archived"] is False
    assert saved["manual_review_hidden_from_public"] is True
    assert saved["verification_status"] == "needs_manual_review"
    assert saved["rewrite_status"] == "manual_review_required"
    assert "archive_reason" not in saved
    assert saved["manual_review_created_at"]
    shared_floor_reason = (
        "RSS/fallback article is below the public quality floor and needs "
        "manual review before publication."
    )
    assert saved["manual_review_reason"] == shared_floor_reason
    assert saved["manual_review_reason"].count(
        "below the public quality floor"
    ) == 1
    assert "1000-character public quality threshold" not in saved[
        "manual_review_reason"
    ]


def test_empty_content_is_skipped_without_insertion(monkeypatch):
    result, collection, _feed = run_import(
        monkeypatch,
        [candidate(content=f"Read more: {SOURCE_URL}")],
    )

    assert collection.inserted == []
    assert result["imported"] == 0
    assert result["skipped"] == 1


def test_invention_language_is_archived_and_hidden(monkeypatch):
    content = full_quality_content() + (
        "\n\nAccording to local residents, a police spokesperson confirmed the claim."
    )
    _result, collection, _feed = run_import(
        monkeypatch,
        [candidate(content=content)],
    )
    saved = collection.inserted[0]

    assert saved["manual_review_hidden_from_public"] is True
    assert saved["archived"] is True
    assert saved["archive_reason"] == "needs_manual_review"
    assert saved["verification_status"] == "needs_manual_review"
    assert saved["rewrite_status"] == "manual_review_required"
    assert "according to local residents" in saved["manual_review_hits"]
    assert saved["manual_review_reason"].count(
        "risky unsupported-detail wording"
    ) == 1


def test_repetition_and_padding_are_archived_and_hidden(monkeypatch):
    repeated_paragraph = (
        "The published programme covers equipment and contractor appointments. "
        "Officials confirmed the same timetable in the available documents. "
        "Further updates will be issued through the formal reporting process. "
    ) * 4
    repeated = "\n\n".join([repeated_paragraph] * 4)
    padded = full_quality_content() + (
        "\n\nThis serves as a reminder for readers and underscores the importance "
        "of investment."
    )

    result, collection, _feed = run_import(
        monkeypatch,
        [
            candidate(id="repeated", title="Repeated feed report", content=repeated),
            candidate(
                id="padded",
                title="Padded feed report",
                source_url="https://publisher.example/padded",
                content=padded,
            ),
        ],
    )

    assert result["imported"] == 2
    assert len(collection.inserted) == 2
    assert all(item["archived"] is True for item in collection.inserted)
    reasons = [item["manual_review_reason"] for item in collection.inserted]
    assert any("duplicated paragraphs" in reason for reason in reasons)
    assert any("generic AI-style padding" in reason for reason in reasons)
    assert sum(
        reason.count("AI rewrite contains duplicated paragraphs.")
        for reason in reasons
    ) == 1
    assert sum(
        reason.count(
            "AI rewrite contains repeated generic AI-style padding or commentary."
        )
        for reason in reasons
    ) == 1


def test_local_record_without_specific_place_is_hidden(monkeypatch):
    _result, collection, _feed = run_import(
        monkeypatch,
        [
            candidate(
                category="Local News",
                scope="cheshire",
                is_local_source=True,
                location=None,
                priority_location=None,
            )
        ],
    )
    saved = collection.inserted[0]

    assert saved["manual_review_hidden_from_public"] is True
    assert saved["verification_status"] == "needs_manual_review"
    assert saved["rewrite_status"] == "manual_review_required"
    assert "missing a specific town" in saved["manual_review_reason"]
    assert saved["archived"] is False


def test_sanitizer_or_guard_failure_causes_no_partial_insert(monkeypatch):
    original_sanitizer = server.sanitize_rss_text

    def fail_sanitizer(*_args, **_kwargs):
        raise RuntimeError("private sanitizer failure")

    sanitizer_collection = FakeArticles()
    sanitizer_feed = FakeFeed([candidate()])
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=sanitizer_collection),
    )
    monkeypatch.setattr(server, "news_feed_service", sanitizer_feed)
    monkeypatch.setattr(server, "sanitize_rss_text", fail_sanitizer)
    with pytest.raises(HTTPException):
        asyncio.run(server.import_real_news(authorized=True))
    assert sanitizer_collection.inserted == []

    inserted = FakeArticles()
    feed = FakeFeed([candidate()])
    monkeypatch.setattr(server, "sanitize_rss_text", original_sanitizer)
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=inserted))
    monkeypatch.setattr(server, "news_feed_service", feed)

    def fail_guard(*_args, **_kwargs):
        raise RuntimeError("private guard failure")

    monkeypatch.setattr(server, "apply_ai_manual_review_guard", fail_guard)
    with pytest.raises(HTTPException):
        asyncio.run(server.import_real_news(authorized=True))
    assert inserted.inserted == []


def test_no_openai_perplexity_retry_or_other_import_path_is_introduced():
    source = inspect.getsource(server.import_real_news)

    assert "openai" not in source.lower()
    assert "perplexity" not in source.lower()
    assert "_import_hybrid_news_internal" not in source
    assert "sync_rss_now" not in source
    assert "regenerate_" not in source
    assert source.count("insert_one") == 1
