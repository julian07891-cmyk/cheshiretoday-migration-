import asyncio
import copy
import os
from datetime import datetime, timezone
from types import SimpleNamespace

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


class Cursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, _limit):
        return copy.deepcopy(self.documents)

    def sort(self, *_args):
        return self

    def skip(self, _value):
        return self

    def limit(self, _value):
        return self


class Collection:
    def __init__(self, existing=None):
        self.existing = list(existing or [])
        self.inserted = []

    def find(self, _query, _projection=None):
        return Cursor(self.existing)

    async def insert_one(self, document):
        self.inserted.append(copy.deepcopy(document))
        return SimpleNamespace(inserted_id=f"inserted-{len(self.inserted)}")


class FeedService:
    def __init__(self, candidates):
        self.candidates = candidates

    async def fetch_local_feeds_only(self):
        return copy.deepcopy(self.candidates)

    async def fetch_local_news(self):
        return []


class Perplexity:
    def __init__(self, rewrites=None):
        self.rewrites = rewrites or {}

    async def generate_article_content(self, **kwargs):
        return self.rewrites.get(kwargs["title"], kwargs["summary"])

    async def search_cheshire_news(self, **_kwargs):
        return []


def candidate(title, *, content="Local source text.", image=True, **values):
    document = {
        "title": title,
        "content": content,
        "summary": content,
        "source": "Cheshire Community News",
        "source_url": f"https://publisher.example/{title.lower().replace(' ', '-')}",
        "image": (
            f"https://publisher.example/{title.lower().replace(' ', '-')}.jpg"
            if image
            else ""
        ),
        "location": "Chester",
        "category": "Local News",
        "publishedDate": datetime.now(timezone.utc).isoformat(),
        "is_local_feed": True,
    }
    document.update(values)
    return document


def run_import(
    monkeypatch,
    candidates,
    rewrites=None,
    existing=None,
    archived_existing=None,
):
    articles = Collection(existing)
    archived = Collection(archived_existing)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=articles, archived_articles=archived),
    )
    monkeypatch.setattr(server, "news_feed_service", FeedService(candidates))
    monkeypatch.setattr(server, "perplexity_service", Perplexity(rewrites))
    monkeypatch.setattr(server, "ai_budget_available", lambda _amount: True)
    monkeypatch.setattr(
        server,
        "resolve_imported_article_image",
        lambda image, _url, fetch_page=None: image,
    )
    monkeypatch.setenv("ENABLE_RATIO_REBALANCE", "0")

    async def no_cap(keep=100):
        assert keep == 100

    monkeypatch.setattr(server, "cap_visible_articles", no_cap)
    result = asyncio.run(
        server._import_hybrid_news_internal(
            server.HybridNewsRequest(
                cheshire_articles=10,
                uk_articles=0,
                business_articles=0,
                tech_articles=0,
                use_perplexity=True,
            )
        )
    )
    return result, articles.inserted


def assert_hidden_manual_review(document):
    assert document["manual_review_hidden_from_public"] is True
    assert document["verification_status"] == "needs_manual_review"
    assert document["rewrite_status"] == "manual_review_required"
    assert document["archive_reason"] == "needs_manual_review"


def test_low_impact_non_crime_local_story_is_queued(monkeypatch):
    story = candidate("Chester volunteers open a community garden")

    result, inserted = run_import(monkeypatch, [story])

    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert len(inserted) == 1
    assert_hidden_manual_review(inserted[0])
    assert "relevance gate" in inserted[0]["manual_review_reason"]
    for field in ("title", "source_url", "image", "location"):
        assert inserted[0][field] == story[field]


def test_short_local_rewrite_is_queued(monkeypatch):
    story = candidate("Chester council considers a new planning application")
    short = "The council is considering the application."

    result, inserted = run_import(
        monkeypatch,
        [story],
        rewrites={story["title"]: short},
    )

    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert inserted[0]["content"] == short
    assert_hidden_manual_review(inserted[0])
    assert "below public length threshold" in inserted[0]["manual_review_reason"]


def test_crime_duplicate_missing_image_and_spam_remain_rejected(monkeypatch):
    crime = candidate("Man jailed after Chester court hearing")
    duplicate = candidate("Existing Chester community story")
    no_image = candidate("Chester residents discuss local park", image=False)
    spam = candidate("Sponsored shopping deal and gift guide for Chester")
    missing_source = candidate(
        "Chester residents create a neighbourhood project",
        source_url="",
    )
    unsafe = candidate(
        "Chester volunteers discuss a neighbourhood project",
        content="Insiders suggest unsupported details about the project.",
    )
    existing = [{"title": duplicate["title"], "source_url": duplicate["source_url"]}]

    result, inserted = run_import(
        monkeypatch,
        [crime, duplicate, no_image, spam, missing_source, unsafe],
        existing=existing,
    )

    assert result["total_imported"] == 0
    assert result["manual_review_imported"] == 0
    assert inserted == []


def test_multiple_qualifying_local_candidates_may_be_queued(monkeypatch):
    candidates = [
        candidate("Chester residents launch a neighbourhood garden"),
        candidate(
            "Warrington volunteers create a community art project",
            location="Warrington",
        ),
        candidate(
            "Frodsham families organise a local heritage exhibition",
            location="Frodsham",
        ),
    ]

    result, inserted = run_import(monkeypatch, candidates)

    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 3
    assert len(inserted) == 3
    assert all(item["manual_review_hidden_from_public"] is True for item in inserted)


def test_archived_title_or_source_url_duplicate_is_not_inserted(monkeypatch):
    story = candidate("Chester volunteers create a community orchard")
    for archived_record in (
        {"title": story["title"], "source_url": "https://archive.example/other"},
        {"title": "Different archived title", "source_url": story["source_url"]},
    ):
        result, inserted = run_import(
            monkeypatch,
            [story],
            archived_existing=[archived_record],
        )
        assert result["manual_review_imported"] == 0
        assert inserted == []


def test_existing_manual_review_title_or_source_duplicate_is_not_inserted(
    monkeypatch,
):
    story = candidate("Warrington neighbours launch a community workshop")
    for existing_record in (
        {
            "title": story["title"],
            "source_url": "https://existing.example/other",
            "manual_review_hidden_from_public": True,
        },
        {
            "title": "Different Manual Review title",
            "source_url": story["source_url"],
            "manual_review_hidden_from_public": True,
        },
    ):
        result, inserted = run_import(
            monkeypatch,
            [story],
            existing=[existing_record],
        )
        assert result["manual_review_imported"] == 0
        assert inserted == []


class PublicQueryCollection:
    def __init__(self, documents):
        self.documents = copy.deepcopy(documents)
        self.queries = []

    def find(self, query, _projection=None):
        self.queries.append(copy.deepcopy(query))
        query_text = repr(query)
        if "manual_review_hidden_from_public" in query_text:
            visible = [
                document
                for document in self.documents
                if document.get("manual_review_hidden_from_public") is not True
            ]
        else:
            visible = self.documents
        return Cursor(visible)

    async def count_documents(self, query):
        query_text = repr(query)
        if "manual_review_hidden_from_public" in query_text:
            return sum(
                document.get("manual_review_hidden_from_public") is not True
                for document in self.documents
            )
        return len(self.documents)


def test_manual_review_records_do_not_enter_public_or_live_counts(monkeypatch):
    result, inserted = run_import(
        monkeypatch,
        [candidate("Chester neighbours create a community reading shelf")],
    )

    assert result["cheshire_from_rss"] == 0
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert inserted[0]["manual_review_hidden_from_public"] is True

    public_collection = PublicQueryCollection(inserted)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=public_collection),
    )
    response = asyncio.run(
        server.get_articles(
            search="community",
            limit=20,
            include_archived=False,
        )
    )

    assert response["articles"] == []
    assert response["total"] == 0
    assert any(
        {"manual_review_hidden_from_public": {"$ne": True}}
        in query.get("$and", [])
        for query in public_collection.queries
    )
