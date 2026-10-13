import asyncio
import os
from copy import deepcopy
from datetime import datetime

from bson import ObjectId


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


class InsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class UpdateResult:
    matched_count = 1
    modified_count = 1


class FakeArticles:
    def __init__(self, existing=None):
        self.existing = deepcopy(existing)
        self.inserted = None
        self.updated = None

    async def insert_one(self, article):
        inserted_id = ObjectId("64b7f9d4aabbccddeeff0011")
        article["_id"] = inserted_id
        self.inserted = deepcopy(article)
        return InsertResult(inserted_id)

    async def find_one(self, query):
        if not self.existing:
            return None
        if query.get("id") == self.existing.get("id"):
            return deepcopy(self.existing)
        if query.get("_id") == self.existing.get("_id"):
            return deepcopy(self.existing)
        return None

    async def update_one(self, query, operation):
        self.updated = (deepcopy(query), deepcopy(operation))
        return UpdateResult()


def _manual_article(**changes):
    values = {
        "title": "A manually created Cheshire article",
        "summary": "A verified summary.",
        "content": "Verified manually written article content about Chester.",
        "category": "Local News",
        "image": "https://example.test/image.jpg",
        "author": "Cheshire Today",
        "source": "Manual Entry",
        "source_url": "",
        "tags": ["Chester"],
        "featured": False,
        "scope": "cheshire",
        "force_live": False,
        "location": "chester",
    }
    values.update(changes)
    return server.ManualArticleCreate(**values)


def test_manual_create_returns_canonical_mongo_id_separate_from_article_uuid(monkeypatch):
    articles = FakeArticles()
    monkeypatch.setattr(server.db, "articles", articles)

    result = asyncio.run(server.create_manual_article(_manual_article(), authorized=True))

    assert result["mongo_id"] == "64b7f9d4aabbccddeeff0011"
    assert ObjectId.is_valid(result["mongo_id"])
    assert result["article"]["id"]
    assert result["article"]["id"] != result["mongo_id"]
    assert articles.inserted["id"] == result["article"]["id"]
    assert str(articles.inserted["_id"]) == result["mongo_id"]
    assert isinstance(articles.inserted["publishedDate"], datetime)
    assert articles.inserted["publishedDate"].tzinfo is not None


def test_manual_update_returns_existing_canonical_mongo_id_without_changing_identity(monkeypatch):
    mongo_id = ObjectId("64b7f9d4aabbccddeeff0012")
    article_uuid = "12f79f40-e147-4c94-9328-d8d00d979ee6"
    existing = {
        "_id": mongo_id,
        "id": article_uuid,
        "title": "Archived article before correction",
        "content": "Original verified content.",
        "category": "Local News",
        "author": "Cheshire Today",
        "source": "Manual Entry",
        "source_url": "",
        "image": "https://example.test/image.jpg",
        "tags": ["Chester"],
        "featured": False,
        "force_live": False,
        "scope": "cheshire",
        "manual_review_hidden_from_public": True,
        "archive_reason": "needs_manual_review",
    }
    articles = FakeArticles(existing)
    monkeypatch.setattr(server.db, "articles", articles)

    result = asyncio.run(
        server.update_article(
            article_uuid,
            _manual_article(
                title="Corrected and restored article",
                content="Corrected verified content about Chester.",
            ),
            authorized=True,
        )
    )

    assert result["mongo_id"] == str(mongo_id)
    assert result["article_id"] == article_uuid
    assert result["restored_from_manual_review"] is True
    assert articles.updated[0] == {"id": article_uuid}
    assert "id" not in articles.updated[1]["$set"]
    assert "_id" not in articles.updated[1]["$set"]
