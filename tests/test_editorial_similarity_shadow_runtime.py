import asyncio
import copy
import inspect
import os
from types import SimpleNamespace


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


class AggregateCursor:
    def __init__(self, documents, requested_lengths):
        self.documents = documents
        self.requested_lengths = requested_lengths

    async def to_list(self, length):
        self.requested_lengths.append(length)
        return copy.deepcopy(self.documents[:length])


class AggregateCollection:
    def __init__(self, documents=(), *, failure=None):
        self.documents = list(documents)
        self.failure = failure
        self.pipelines = []
        self.requested_lengths = []

    def aggregate(self, pipeline):
        self.pipelines.append(copy.deepcopy(pipeline))
        if self.failure:
            raise self.failure
        return AggregateCursor(self.documents, self.requested_lengths)


class RecordingLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)


def record(article_id):
    return {
        "_id": article_id,
        "title": "A bounded title",
        "summary": "A bounded summary",
        "content": "Bounded article content.",
        "source_url": f"https://publisher.example/{article_id}",
        "location": "Chester",
    }


def test_pool_queries_are_50_plus_50_bounded_before_projection(monkeypatch):
    active = AggregateCollection([record(f"active-{index}") for index in range(80)])
    archived = AggregateCollection([record(f"archived-{index}") for index in range(80)])
    logger = RecordingLogger()
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=active, archived_articles=archived),
    )
    monkeypatch.setattr(server, "logger", logger)

    evaluator = asyncio.run(server._load_editorial_similarity_shadow_evaluator())

    assert evaluator.pool_size == 100
    assert {record.provenance for record in evaluator._records} == {
        "active",
        "archived",
    }
    assert active.requested_lengths == [50]
    assert archived.requested_lengths == [50]
    for collection in (active, archived):
        pipeline = collection.pipelines[0]
        assert pipeline[0] == {"$sort": {"_id": -1}}
        assert pipeline[1] == {"$limit": 50}
        assert "$project" in pipeline[2]
        projection = pipeline[2]["$project"]
        assert set(projection) == {
            "_id",
            "title",
            "summary",
            "content",
            "source_url",
            "location",
            "priority_location",
            "publishedDate",
            "published_date",
            "created_at",
        }
        assert "image" not in projection
        assert "manual_review_hidden_from_public" not in projection
    assert any(
        "editorial_similarity_shadow_pool status=loaded "
        "active_count=50 archived_count=50 pool_count=100" in message
        for message in logger.messages
    )


def test_one_pool_source_failure_is_safe_and_does_not_expose_exception(monkeypatch):
    active = AggregateCollection(failure=RuntimeError("secret database detail"))
    archived = AggregateCollection([record("archived-id")])
    logger = RecordingLogger()
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=active, archived_articles=archived),
    )
    monkeypatch.setattr(server, "logger", logger)

    evaluator = asyncio.run(server._load_editorial_similarity_shadow_evaluator())

    assert evaluator.pool_size == 1
    assert any(
        message
        == "editorial_similarity_shadow_pool status=source_unavailable source=active"
        for message in logger.messages
    )
    assert all("secret database detail" not in message for message in logger.messages)
    assert evaluator._records[0].provenance == "archived"


def test_both_pool_source_failures_return_empty_safe_corpus(monkeypatch):
    logger = RecordingLogger()
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(
            articles=AggregateCollection(failure=RuntimeError("active secret")),
            archived_articles=AggregateCollection(
                failure=RuntimeError("archived secret")
            ),
        ),
    )
    monkeypatch.setattr(server, "logger", logger)

    evaluator = asyncio.run(server._load_editorial_similarity_shadow_evaluator())

    assert evaluator.pool_size == 0
    assert sum("status=source_unavailable" in item for item in logger.messages) == 2
    assert all("secret" not in item for item in logger.messages)


def test_generate_helper_propagates_explicit_shadow_activation(monkeypatch):
    calls = []

    async def fake_import(
        request,
        memory_started_at=None,
        enable_editorial_similarity_shadow=False,
    ):
        calls.append(
            (
                memory_started_at,
                enable_editorial_similarity_shadow,
                request.public_import_limit,
            )
        )
        return {"cheshire_articles": 0, "uk_articles": 0, "total_imported": 0}

    monkeypatch.setattr(server, "_import_hybrid_news_internal", fake_import)
    request = server.GenerateArticlesRequest(
        count=12,
        include_uk_news=True,
        public_import_limit=6,
    )

    asyncio.run(server._generate_articles_internal(request))
    asyncio.run(
        server._generate_articles_internal(
            request,
            memory_started_at=1.0,
            enable_editorial_similarity_shadow=True,
        )
    )

    assert calls == [(None, False, 6), (1.0, True, 6)]


def test_all_four_hybrid_insertions_share_shadow_wrapper_with_fixed_contexts():
    source = inspect.getsource(server._import_hybrid_news_internal)

    assert source.count("await insert_hybrid_article(") == 4
    for context in (
        '"category_rss"',
        '"local_rss_manual_review"',
        '"local_rss"',
        '"cheshire_fallback"',
    ):
        assert source.count(context) == 1
    assert "enable_editorial_similarity_shadow: bool = False" in source


def test_manual_import_routes_do_not_enable_shadow_mode():
    generate_source = inspect.getsource(server.generate_articles)
    hybrid_source = inspect.getsource(server.import_hybrid_news)
    clear_source = inspect.getsource(server.clear_and_refresh_news)

    assert "enable_editorial_similarity_shadow" not in generate_source
    assert "enable_editorial_similarity_shadow" not in hybrid_source
    assert "enable_editorial_similarity_shadow" not in clear_source


def test_shadow_integration_does_not_change_memory_marker_allow_list():
    from backend.app.article_generation_observability import APPROVED_PHASES

    assert len(APPROVED_PHASES) == 12
    assert all("similarity" not in phase for phase in APPROVED_PHASES)
