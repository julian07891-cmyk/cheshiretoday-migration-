import os
import asyncio
import copy
import inspect
from types import SimpleNamespace

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


def manual_review_article(**values):
    article = {
        "title": "Chester community project awaits editorial review",
        "content": "A short local source report.",
        "summary": "A short local source report.",
        "source": "Cheshire Community News",
        "source_url": "https://publisher.example/chester-community-project",
        "image": "https://publisher.example/story.jpg",
        "category": "Local News",
        "scope": "cheshire",
        "location": "Chester",
        "publishedDate": "2026-07-24T09:00:00+00:00",
        "manual_review_created_at": "2026-07-25T09:00:00+00:00",
        "manual_review_hidden_from_public": True,
        "manual_review_reason": "Local RSS article needs manual review: Community feature",
        "verification_status": "needs_manual_review",
        "rewrite_status": "manual_review_required",
        "is_local_feed": True,
    }
    article.update(values)
    return article


def test_metadata_generation_is_structured_and_deterministic():
    article = manual_review_article()

    first = server.build_manual_review_editorial_metadata(article)
    second = server.build_manual_review_editorial_metadata(article)

    assert first == second
    assert first == {
        "routing_reason": "Local RSS article needs manual review: Community feature",
        "source_type": "local_rss",
        "detected_locality": "Chester",
        "editorial_topic": "Community feature",
        "rewrite_status": "manual_review_required",
        "rewrite_length": 28,
        "image_status": "available",
        "freshness_bucket": "recent",
        "duplicate_status": "not_flagged",
        "auto_publish_candidate": False,
        "failed_public_gate": "editorial_relevance",
        "publication_recommendation": "Needs rewrite",
    }


def test_recommendation_generation_uses_existing_facts_only():
    strong = manual_review_article(
        content="Verified local reporting. " * 80,
        manual_review_reason="Public import cap reached for scheduled run; queued for manual review",
    )
    borderline = manual_review_article(
        content="Useful local reporting. " * 55,
        manual_review_reason="Local RSS article needs manual review: Soft local news",
    )
    editorial = manual_review_article(
        content="According to local residents, unsupported detail was reported. " * 25,
        manual_review_reason="AI rewrite contained risky invented-detail phrases; verify against source.",
    )

    strong_metadata = server.build_manual_review_editorial_metadata(strong)
    assert strong_metadata["publication_recommendation"] == "Strong candidate"
    assert strong_metadata["auto_publish_candidate"] is True
    assert server.build_manual_review_editorial_metadata(borderline)["publication_recommendation"] == "Borderline"
    assert server.build_manual_review_editorial_metadata(editorial)["publication_recommendation"] == "Needs editorial review"
    assert server.build_manual_review_editorial_metadata(editorial)["auto_publish_candidate"] is False


def test_topic_cap_with_complete_content_and_usable_image_is_candidate():
    article = manual_review_article(
        content="Complete verified local reporting. " * 55,
        manual_review_reason=(
            "Local RSS article needs manual review: "
            "per-run topic cap reached (planning_housing)"
        ),
    )

    metadata = server.build_manual_review_editorial_metadata(article)

    assert metadata["failed_public_gate"] == "topic_cap"
    assert metadata["publication_recommendation"] == "Strong candidate"
    assert metadata["auto_publish_candidate"] is True


def test_short_rewrite_is_not_auto_publish_candidate():
    metadata = server.build_manual_review_editorial_metadata(
        manual_review_article(
            manual_review_reason=(
                "Local RSS article needs manual review: "
                "AI/RSS content remained below public length threshold"
            )
        )
    )

    assert metadata["publication_recommendation"] == "Needs rewrite"
    assert metadata["auto_publish_candidate"] is False


def test_missing_or_weak_image_is_not_auto_publish_candidate():
    for image in ("", "https://www.warringtonguardian.co.uk/resources/images/20771109/x.jpg"):
        metadata = server.build_manual_review_editorial_metadata(
            manual_review_article(
                content="Complete verified local reporting. " * 55,
                image=image,
                manual_review_reason=(
                    "Public import cap reached for scheduled run; queued for manual review"
                ),
            )
        )

        assert metadata["image_status"] in {"missing", "weak"}
        assert metadata["auto_publish_candidate"] is False
        assert metadata["publication_recommendation"] != "Strong candidate"


def test_guarded_manual_review_record_persists_metadata():
    content = "According to local residents, the proposal has already been approved. " * 25
    article = manual_review_article(content=content, manual_review_reason="")

    guarded = server.apply_ai_manual_review_guard(
        article,
        content,
        ai_rewrite_used=True,
        title=article["title"],
    )

    assert guarded["manual_review_hidden_from_public"] is True
    assert guarded["editorial_metadata"] == server.build_manual_review_editorial_metadata(guarded)
    assert guarded["editorial_metadata"]["auto_publish_candidate"] is False


def test_existing_manual_review_record_without_metadata_remains_compatible():
    legacy = manual_review_article(
        manual_review_reason="Moved back to Manual Review for editor rewrite before publication",
        image="",
        publishedDate="not-a-date",
    )
    legacy.pop("editorial_metadata", None)

    metadata = server.build_manual_review_editorial_metadata(legacy)

    assert metadata["routing_reason"] == legacy["manual_review_reason"]
    assert metadata["image_status"] == "missing"
    assert metadata["freshness_bucket"] == "unknown"
    assert metadata["publication_recommendation"] == "Needs editorial review"
    assert set(metadata) == {
        "routing_reason",
        "source_type",
        "detected_locality",
        "editorial_topic",
        "rewrite_status",
        "rewrite_length",
        "image_status",
        "freshness_bucket",
        "duplicate_status",
        "auto_publish_candidate",
        "failed_public_gate",
        "publication_recommendation",
    }


class ManualReviewCursor:
    def __init__(self, documents):
        self.documents = copy.deepcopy(documents)
        self.sort_spec = None
        self.skip_value = 0
        self.limit_value = None

    def sort(self, sort_spec):
        self.sort_spec = sort_spec
        for field, direction in reversed(sort_spec):
            self.documents.sort(
                key=lambda document: str(document.get(field) or ""),
                reverse=direction == -1,
            )
        return self

    def skip(self, value):
        self.skip_value = value
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    async def to_list(self, limit):
        end = self.skip_value + min(limit, self.limit_value)
        return copy.deepcopy(self.documents[self.skip_value:end])


class ManualReviewCollection:
    def __init__(self, documents):
        self.documents = documents
        self.count_query = None
        self.find_query = None
        self.projection = None
        self.last_cursor = None

    async def count_documents(self, query):
        self.count_query = query
        return len(self.documents)

    def find(self, query, projection):
        self.find_query = query
        self.projection = projection
        assert projection["editorial_metadata"] == 1
        self.last_cursor = ManualReviewCursor(self.documents)
        return self.last_cursor


def test_admin_list_exposes_derived_metadata_for_legacy_records(monkeypatch):
    legacy = manual_review_article()
    legacy["_id"] = "mongo-id"
    legacy.pop("editorial_metadata", None)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=ManualReviewCollection([legacy])),
    )

    result = asyncio.run(server.get_manual_review_articles(auth=True))

    assert result["total"] == 1
    assert result["articles"][0]["id"] == "mongo-id"
    assert result["articles"][0]["editorial_metadata"] == (
        server.build_manual_review_editorial_metadata(legacy)
    )


def test_admin_manual_review_pagination_contract_and_deterministic_sort(monkeypatch):
    documents = [
        manual_review_article(_id="same-a", publishedDate="2026-07-24T09:00:00+00:00"),
        manual_review_article(_id="older-z", publishedDate="2026-07-23T09:00:00+00:00"),
        manual_review_article(_id="same-c", publishedDate="2026-07-24T09:00:00+00:00"),
        manual_review_article(_id="same-b", publishedDate="2026-07-24T09:00:00+00:00"),
    ]
    collection = ManualReviewCollection(documents)
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))

    result = asyncio.run(server.get_manual_review_articles(auth=True))

    expected_query = {
        "manual_review_hidden_from_public": True,
        "$or": [{"archived": {"$exists": False}}, {"archived": False}],
    }
    assert collection.count_query == expected_query
    assert collection.find_query == expected_query
    assert collection.last_cursor.sort_spec == [
        ("publishedDate", -1),
        ("_id", -1),
    ]
    assert collection.last_cursor.skip_value == 0
    assert collection.last_cursor.limit_value == 100
    assert list(result) == ["success", "articles", "total", "skip", "limit"]
    assert result["success"] is True
    assert result["total"] == 4
    assert result["skip"] == 0
    assert result["limit"] == 100
    assert [article["id"] for article in result["articles"]] == [
        "same-c",
        "same-b",
        "same-a",
        "older-z",
    ]


def test_admin_manual_review_pagination_bounds_and_auth_dependency(monkeypatch):
    collection = ManualReviewCollection([])
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))

    result = asyncio.run(
        server.get_manual_review_articles(skip=-10, limit=999, auth=True)
    )

    auth_default = inspect.signature(
        server.get_manual_review_articles
    ).parameters["auth"].default
    assert auth_default.dependency is server.get_admin_auth
    assert result["skip"] == 0
    assert result["limit"] == 250
    assert collection.last_cursor.skip_value == 0
    assert collection.last_cursor.limit_value == 250
