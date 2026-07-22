import asyncio
import copy
import inspect
import os
from pathlib import Path
from types import SimpleNamespace


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


SOURCE_URL = "https://publisher.example/cheshire-story"
IMAGE_URL = "https://publisher.example/cheshire-story.jpg"


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, _length):
        return copy.deepcopy(self.documents)


class FakeCollection:
    def __init__(self, existing=None):
        self.existing = list(existing or [])
        self.inserted = []

    def find(self, _query, _projection=None):
        return FakeCursor(self.existing)

    async def insert_one(self, document):
        self.inserted.append(copy.deepcopy(document))
        return SimpleNamespace(inserted_id="offline-id")


class FakeNewsFeedService:
    async def fetch_local_feeds_only(self):
        return []

    async def fetch_local_news(self):
        return []


class FakePerplexityService:
    def __init__(self, candidates):
        self.candidates = copy.deepcopy(candidates)
        self.search_calls = 0

    async def search_cheshire_news(self, *, category, limit):
        self.search_calls += 1
        assert category == "Local News"
        assert limit == 3
        return copy.deepcopy(self.candidates)

    def __getattr__(self, name):
        raise AssertionError(f"unexpected Perplexity operation: {name}")


class FailOnOpenAI:
    def __getattr__(self, name):
        raise AssertionError(f"OpenAI must not be used by fallback import: {name}")


def safe_content():
    first = (
        "Chester employers outlined a new skills programme for local residents. "
        + "The programme gives businesses a structured route to recruit and train staff. " * 10
    )
    second = (
        "Council officers said the initiative would be reviewed against published employment data. "
        + "Participating organisations will publish progress updates through the year. " * 10
    )
    return f"{first}\n\n{second}"


def candidate(*, content=None, summary="A compact summary."):
    return {
        "title": "Chester employers launch local skills programme",
        "content": content if content is not None else safe_content(),
        "summary": summary,
        "category": "Local News",
        "scope": "cheshire",
        "source": "Example Publisher",
        "source_url": SOURCE_URL,
        "image": IMAGE_URL,
        "location": "Chester",
    }


def run_import(monkeypatch, candidates, *, existing=None):
    articles = FakeCollection(existing)
    archived = FakeCollection()
    perplexity = FakePerplexityService(candidates)

    monkeypatch.setattr(server, "db", SimpleNamespace(articles=articles, archived_articles=archived))
    monkeypatch.setattr(server, "news_feed_service", FakeNewsFeedService())
    monkeypatch.setattr(server, "perplexity_service", perplexity)
    monkeypatch.setattr(server, "openai_service", FailOnOpenAI(), raising=False)
    monkeypatch.setenv("ENABLE_RATIO_REBALANCE", "0")

    async def no_cap(keep=100):
        assert keep == 100
        return None

    monkeypatch.setattr(server, "cap_visible_articles", no_cap)

    result = asyncio.run(
        server._import_hybrid_news_internal(
            server.HybridNewsRequest(
                cheshire_articles=1,
                uk_articles=0,
                business_articles=0,
                tech_articles=0,
                use_perplexity=True,
            )
        )
    )
    return result, articles, perplexity


def test_safe_full_length_fallback_stays_public_and_preserves_metadata(monkeypatch):
    body = safe_content() + f"\n\nRead more: {SOURCE_URL}"
    summary = f"First summary line.\n\nSecond summary line.\nFull story: {SOURCE_URL}"
    original = candidate(content=body, summary=summary)

    result, articles, perplexity = run_import(monkeypatch, [original])

    assert perplexity.search_calls == 1
    assert result["public_imported"] == 1
    assert result["manual_review_imported"] == 0
    assert result["cheshire_from_perplexity"] == 1
    assert len(articles.inserted) == 1

    inserted = articles.inserted[0]
    assert inserted.get("manual_review_hidden_from_public") is not True
    assert "\n\n" in inserted["content"]
    assert "Read more:" not in inserted["content"]
    assert inserted["summary"] == "First summary line. Second summary line."
    for field in ("image", "source", "source_url", "category", "scope", "location"):
        assert inserted[field] == original[field]


def test_short_two_sentence_fallback_is_retained_for_manual_review(monkeypatch):
    short = "Chester police reported a fall in recorded crime. Officers published updated figures."

    result, articles, _perplexity = run_import(monkeypatch, [candidate(content=short, summary="")])

    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert len(articles.inserted) == 1
    inserted = articles.inserted[0]
    assert inserted["content"] == short
    assert inserted["summary"] == ""
    assert inserted["manual_review_hidden_from_public"] is True
    assert inserted["verification_status"] == "needs_manual_review"
    assert inserted["rewrite_status"] == "manual_review_required"
    assert inserted["archive_reason"] == "needs_manual_review"
    assert "below the 1000-character public threshold" in inserted["manual_review_reason"]


def test_invention_phrase_and_duplicate_paragraphs_are_hidden(monkeypatch):
    risky = safe_content() + "\n\nA police spokesperson supplied an additional unverified account."
    result, articles, _perplexity = run_import(monkeypatch, [candidate(content=risky)])
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert articles.inserted[0]["manual_review_hidden_from_public"] is True
    assert "police spokesperson" in articles.inserted[0]["manual_review_hits"]

    repeated = "Chester businesses published verified figures for the local programme. " * 9
    repeated_body = f"{repeated}\n\n{repeated}"
    result, articles, _perplexity = run_import(monkeypatch, [candidate(content=repeated_body)])
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert articles.inserted[0]["manual_review_hidden_from_public"] is True
    assert "duplicated paragraphs" in articles.inserted[0]["manual_review_reason"]


def test_duplicate_title_or_source_url_remains_skipped(monkeypatch):
    for existing in (
        [{"title": candidate()["title"], "source_url": "https://other.example/story"}],
        [{"title": "Different title", "source_url": SOURCE_URL}],
    ):
        result, articles, perplexity = run_import(monkeypatch, [candidate()], existing=existing)
        assert result["total_imported"] == 0
        assert result["public_imported"] == 0
        assert result["manual_review_imported"] == 0
        assert articles.inserted == []
        assert perplexity.search_calls == 1


def test_fallback_source_contains_guard_without_openai_path():
    source = inspect.getsource(server._import_hybrid_news_internal)
    fallback = source[source.index("# STEP 3: Import Cheshire news via Perplexity"):]

    assert "sanitize_rss_text(article.get('content',''), article.get('source_url',''), is_summary=False)" in fallback
    assert "sanitize_rss_text(article.get('summary',''), article.get('source_url',''), is_summary=True)" in fallback
    assert "apply_ai_manual_review_guard(" in fallback
    assert "ai_rewrite_used=True" in fallback
    assert "openai_service" not in fallback
