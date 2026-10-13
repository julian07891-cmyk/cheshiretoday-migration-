import asyncio
import copy
import os
import re
from datetime import datetime, timedelta, timezone


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


def _article(identifier, published_date):
    return {
        "_id": identifier,
        "id": f"article-{identifier}",
        "title": f"Article {identifier}",
        "summary": "A verified Cheshire summary.",
        "content": "Stored article body.",
        "category": "Local News",
        "source": "Cheshire Test Source",
        "source_url": f"https://example.test/{identifier}",
        "publishedDate": published_date,
        "is_local_source": True,
    }


def _mongo_mixed_date_sort_key(value):
    """Approximate Mongo's descending BSON type ordering for this regression."""
    if isinstance(value, datetime):
        comparable = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return (3, comparable.timestamp())
    if isinstance(value, str):
        return (2, value)
    return (1, "")


def _title_search_pattern(query):
    if not isinstance(query, dict):
        return None
    title_clause = query.get("title")
    if isinstance(title_clause, dict) and "$regex" in title_clause:
        return title_clause["$regex"]
    for operator in ("$and", "$or"):
        for clause in query.get(operator, []):
            pattern = _title_search_pattern(clause)
            if pattern is not None:
                return pattern
    return None


class FakeCursor:
    def __init__(self, documents):
        self.documents = copy.deepcopy(documents)

    def sort(self, field, direction):
        assert field == "publishedDate"
        self.documents.sort(
            key=lambda article: _mongo_mixed_date_sort_key(article.get(field)),
            reverse=direction < 0,
        )
        return self

    async def to_list(self, value):
        documents = self.documents if value is None else self.documents[:value]
        return copy.deepcopy(documents)


class FakeArticles:
    def __init__(self, documents):
        self.documents = copy.deepcopy(documents)

    def find(self, query, projection=None):
        documents = [
            article
            for article in self.documents
            if article.get("archived") is not True
            and article.get("manual_review_hidden_from_public") is not True
        ]

        requested_ids = query.get("_id", {}).get("$in") if isinstance(query.get("_id"), dict) else None
        if requested_ids is not None:
            documents = [article for article in documents if article.get("_id") in requested_ids]

        title_pattern = _title_search_pattern(query)
        if title_pattern is not None:
            documents = [
                article
                for article in documents
                if re.search(title_pattern, article.get("title", ""), re.I)
            ]

        if projection:
            documents = [
                {
                    key: value
                    for key, value in article.items()
                    if key == "_id" or projection.get(key)
                }
                for article in documents
            ]
        return FakeCursor(documents)


def _admin_articles(monkeypatch, documents, **kwargs):
    monkeypatch.setattr(server.db, "articles", FakeArticles(documents))
    monkeypatch.setenv("UK_FILTER_NOISE", "1")
    return asyncio.run(server.get_admin_articles(authorized=True, **kwargs))


def test_admin_sorts_mixed_bson_and_iso_dates_chronologically_before_first_page(monkeypatch):
    base = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
    imported = [
        _article(f"imported-{index:02d}", base - timedelta(minutes=index))
        for index in range(55)
    ]
    manual = _article("manual-recent", "2026-10-13T08:11:20.629758+00:00")
    manual["title"] = "Three Wilmslow organisations receive £6,000 in community grants"

    result = _admin_articles(monkeypatch, [*imported, manual], skip=0, limit=50)

    assert result["total"] == 56
    assert len(result["articles"]) == 50
    assert result["articles"][0]["id"] == "article-manual-recent"
    assert result["articles"][0]["mongo_id"] == "manual-recent"


def test_admin_paginates_after_normalising_mixed_publication_dates(monkeypatch):
    documents = [
        _article("newest-datetime", datetime(2026, 10, 13, 10, 0, tzinfo=timezone.utc)),
        _article("newer-iso", "2026-10-13T09:00:00+00:00"),
        _article("older-naive", datetime(2026, 10, 13, 8, 0)),
        _article("invalid", "not-a-date"),
        _article("missing", None),
    ]

    first_page = _admin_articles(monkeypatch, documents, skip=0, limit=2)
    second_page = _admin_articles(monkeypatch, documents, skip=2, limit=3)

    assert [article["id"] for article in first_page["articles"]] == [
        "article-newest-datetime",
        "article-newer-iso",
    ]
    assert [article["id"] for article in second_page["articles"]] == [
        "article-older-naive",
        "article-invalid",
        "article-missing",
    ]


def test_admin_exact_title_search_preserves_article_and_mongo_identity(monkeypatch):
    target = _article("manual-search-id", "2026-10-13T08:11:20.629758+00:00")
    target["id"] = "6aaf168a-6a9a-4343-9fb5-7a6f4041341a"
    target["title"] = "Three Wilmslow organisations receive £6,000 in community grants"
    other = _article("other-id", datetime(2026, 10, 13, 10, 0, tzinfo=timezone.utc))

    result = _admin_articles(
        monkeypatch,
        [other, target],
        search=target["title"],
        skip=0,
        limit=50,
    )

    assert result["total"] == 1
    assert result["articles"][0]["id"] == "6aaf168a-6a9a-4343-9fb5-7a6f4041341a"
    assert result["articles"][0]["mongo_id"] == "manual-search-id"
