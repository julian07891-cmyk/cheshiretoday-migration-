import asyncio
import copy
import os


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


def _article(identifier, title, summary, **changes):
    article = {
        "_id": identifier,
        "id": identifier,
        "title": title,
        "summary": summary,
        "content": "Stored article body.",
        "category": "UK News",
        "source": "BBC News",
        "source_url": f"https://example.test/{identifier}",
        "publishedDate": "2026-10-06T05:00:00+00:00",
        "is_local_source": False,
    }
    article.update(changes)
    return article


def _visible(article):
    return article.get("archived") is not True and article.get("manual_review_hidden_from_public") is not True


class FakeCursor:
    def __init__(self, documents):
        self.documents = copy.deepcopy(documents)

    def sort(self, *args):
        return self

    def skip(self, value):
        self.documents = self.documents[value:]
        return self

    def limit(self, value):
        self.documents = self.documents[:value]
        return self

    async def to_list(self, value):
        return copy.deepcopy(self.documents if value is None else self.documents[:value])


class FakeArticles:
    def __init__(self, documents):
        self.documents = copy.deepcopy(documents)

    def find(self, query, projection=None):
        documents = [article for article in self.documents if _visible(article)]
        requested_ids = query.get("_id", {}).get("$in") if isinstance(query.get("_id"), dict) else None
        if requested_ids is not None:
            documents = [article for article in documents if article.get("_id") in requested_ids]
        if projection:
            documents = [
                {key: value for key, value in article.items() if key == "_id" or projection.get(key)}
                for article in documents
            ]
        return FakeCursor(documents)

    async def count_documents(self, query):
        return len([article for article in self.documents if _visible(article)])


def test_admin_articles_include_only_binary_public_eligible_records(monkeypatch):
    regional = _article(
        "regional",
        "Glasgow city council reaches pay deal with union",
        "The agreement applies to council workers in Glasgow.",
    )
    national = _article(
        "national",
        "UK inflation outlook includes new figures from Scotland",
        "The Bank of England assessment covers households across Britain.",
        category="Business",
    )
    forced = _article(
        "forced",
        "Glasgow city council reaches pay deal with union",
        "The agreement applies to council workers in Glasgow.",
        force_live=True,
    )
    archived = _article("archived", "UK inflation update", "UK-wide outlook.", archived=True)
    manual = _article(
        "manual",
        "UK schools policy update",
        "Schools across Britain are affected.",
        manual_review_hidden_from_public=True,
    )
    monkeypatch.setattr(server.db, "articles", FakeArticles([regional, national, forced, archived, manual]))
    monkeypatch.setenv("UK_FILTER_NOISE", "1")

    result = asyncio.run(server.get_admin_articles(authorized=True))

    assert [article["id"] for article in result["articles"]] == ["national", "forced"]
    assert result["total"] == 2


def test_admin_applies_public_eligibility_before_pagination_and_count(monkeypatch):
    regional = _article(
        "regional",
        "Glasgow city council reaches pay deal with union",
        "The agreement applies to council workers in Glasgow.",
    )
    first = _article(
        "first",
        "UK inflation outlook includes new figures from Scotland",
        "The Bank of England assessment covers households across Britain.",
        category="Business",
    )
    second = _article(
        "second",
        "UK mortgage rates fall after Bank of England decision",
        "Borrowers across Britain could benefit from the change.",
        category="Finance",
    )
    monkeypatch.setattr(server.db, "articles", FakeArticles([regional, first, second]))
    monkeypatch.setenv("UK_FILTER_NOISE", "1")

    result = asyncio.run(server.get_admin_articles(skip=1, limit=1, authorized=True))

    assert [article["id"] for article in result["articles"]] == ["second"]
    assert result["total"] == 2
