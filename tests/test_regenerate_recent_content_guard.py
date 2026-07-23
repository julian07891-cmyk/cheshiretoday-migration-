import asyncio
import inspect
import os
from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


SOURCE_URL = "https://publisher.example/recent-story"


def safe_long_content(*, source_tail=False, local_name=""):
    place = f"{local_name} " if local_name else ""
    paragraphs = [
        (
            f"{place}The company confirmed a new investment programme for its existing operation. "
            "The announcement sets out the timetable and the work planned for the site. "
            "Published information confirms that the first phase covers new equipment."
        ),
        (
            "Company representatives said the programme will expand production capacity. "
            "Recruitment details will be published through the normal company channels. "
            "The timetable remains subject to the usual regulatory approvals."
        ),
        (
            "Local suppliers will be invited to compete for suitable contracts. "
            "Procurement information will be issued as work packages are confirmed. "
            "The business will publish progress updates during the delivery period."
        ),
        (
            "The investment forms part of the company’s published growth programme. "
            "Construction and installation work will continue through the next financial year. "
            "Further verified details will be released after each phase is completed."
        ),
        (
            "Initial preparation will focus on the areas identified in the published plan. "
            "Specialist contractors will work alongside the company’s engineering team. "
            "Normal operations are expected to continue while the work is carried out."
        ),
        (
            "Training will be provided before the upgraded equipment enters service. "
            "Managers will review operational requirements as each installation is completed. "
            "The company has not announced changes to its existing product range."
        ),
        (
            "Planning documents describe how deliveries will be managed during construction. "
            "Site access arrangements will be reviewed with the appointed contractors. "
            "Any required applications will follow the standard public process."
        ),
        (
            "Financial details beyond the announced programme have not been published. "
            "The business said spending will be phased across the implementation timetable. "
            "Further procurement notices are expected as individual packages are prepared."
        ),
        (
            "Project managers will monitor progress against the confirmed delivery milestones. "
            "Updates will cover completed work and the next scheduled phase. "
            "The programme remains subject to the conditions set out in formal approvals."
        ),
        (
            "Existing staff will receive information through the company’s usual internal channels. "
            "Recruitment will begin only when individual roles and start dates are confirmed. "
            "No final total for additional posts has yet been published."
        ),
        (
            "The next public update is expected after enabling work has been completed. "
            "That report will set out progress against the timetable already announced. "
            "The company said verified information will be released through official channels."
        ),
    ]
    content = "\n\n".join(paragraphs)
    if source_tail:
        content += f"\n\nRead more: {SOURCE_URL}"
    assert len(content) >= 1200
    return content


def article(**overrides):
    document = {
        "_id": "mongo-article-id",
        "id": "internal-article-id",
        "title": "Manufacturer confirms regional investment programme",
        "summary": "The company has confirmed a new investment programme.",
        "content": "Existing verified article content. " * 20,
        "category": "Business",
        "image": "https://images.example/investment.jpg",
        "source": "Example Publisher",
        "source_url": SOURCE_URL,
        "scope": "uk",
        "location": None,
        "priority_location": None,
        "publishedDate": "2026-07-23T09:00:00+00:00",
        "created_at": "2026-07-23T09:05:00+00:00",
        "archived": False,
        "force_live": False,
    }
    document.update(overrides)
    return document


class FakeCursor:
    def __init__(self, documents, events):
        self.documents = deepcopy(documents)
        self.events = events

    def sort(self, field, direction):
        self.events.append(("sort", field, direction))
        return self

    def limit(self, value):
        self.events.append(("limit", value))
        return self

    async def to_list(self, value):
        self.events.append(("to_list", value))
        return deepcopy(self.documents)


class FakeArticles:
    def __init__(self, documents):
        self.documents = documents
        self.events = []
        self.updates = []

    def find(self, query):
        self.events.append(("find", deepcopy(query)))
        return FakeCursor(self.documents, self.events)

    async def update_one(self, query, update):
        self.updates.append((deepcopy(query), deepcopy(update)))
        return SimpleNamespace(matched_count=1, modified_count=1)

    async def delete_one(self, *_args, **_kwargs):
        raise AssertionError("recent regeneration must never delete an article")


class FakePerplexity:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    async def generate_article_content(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return output


def run_regeneration(monkeypatch, documents, outputs):
    articles = FakeArticles(documents)
    perplexity = FakePerplexity(outputs)
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=articles))
    monkeypatch.setattr(server, "perplexity_service", perplexity)
    result = asyncio.run(server.regenerate_recent_article_content(authorized=True))
    return result, articles, perplexity


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
        if getattr(route, "path", None) == "/api/admin/regenerate-recent-content"
        and "POST" in getattr(route, "methods", set())
    ]
    assert len(routes) == 1
    assert routes[0].endpoint is server.regenerate_recent_article_content
    assert server.get_admin_auth in route_dependencies(routes[0])


def test_unauthenticated_request_starts_no_database_or_perplexity_work(monkeypatch):
    class Untouched:
        touched = False

        def __getattr__(self, name):
            self.touched = True
            raise AssertionError(f"unexpected unauthenticated access: {name}")

    database = Untouched()
    perplexity = Untouched()
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "perplexity_service", perplexity)

    response = TestClient(server.app).post(
        "/api/admin/regenerate-recent-content"
    )

    assert response.status_code == 401
    assert database.touched is False
    assert perplexity.touched is False


def test_selection_window_order_and_limit_are_unchanged(monkeypatch):
    result, articles, _perplexity = run_regeneration(
        monkeypatch,
        [article()],
        [safe_long_content()],
    )

    assert result["recent_articles_found"] == 1
    assert articles.events[0][0] == "find"
    query = articles.events[0][1]
    cutoff = datetime.fromisoformat(query["publishedDate"]["$gte"])
    age = datetime.now(cutoff.tzinfo) - cutoff
    assert 47.9 <= age.total_seconds() / 3600 <= 48.1
    assert ("sort", "publishedDate", -1) in articles.events
    assert ("limit", 25) in articles.events
    assert ("to_list", 25) in articles.events
    assert "archived" not in query
    assert "manual_review_hidden_from_public" not in query


def test_safe_long_rewrite_is_sanitized_and_saved_once(monkeypatch):
    generated = safe_long_content(source_tail=True)
    result, articles, perplexity = run_regeneration(
        monkeypatch,
        [article()],
        [generated],
    )

    assert result["regenerated"] == 1
    assert result["safe_regenerated"] == 1
    assert result["manual_review_routed"] == 0
    assert len(perplexity.calls) == 1
    assert len(articles.updates) == 1
    query, update = articles.updates[0]
    assert query == {"_id": "mongo-article-id"}
    assert set(update) == {"$set"}
    saved = update["$set"]
    assert saved["content"] == safe_long_content(source_tail=False)
    assert SOURCE_URL not in saved["content"]
    assert saved["content_generated"] is True
    assert saved["ai_rewritten"] is True
    assert saved["is_rewritten"] is True
    assert saved["verification_status"] == "ai_rewrite_auto_screened"
    assert saved["rewrite_status"] == "ai_rewritten"
    assert datetime.fromisoformat(saved["content_regenerated_at"])


def test_safe_rewrite_preserves_article_metadata(monkeypatch):
    original = article(featured=True, tags=["Business"], custom_field="keep")
    _result, articles, _perplexity = run_regeneration(
        monkeypatch,
        [original],
        [safe_long_content()],
    )
    saved = articles.updates[0][1]["$set"]

    protected_fields = {
        "_id",
        "id",
        "title",
        "summary",
        "category",
        "image",
        "source",
        "source_url",
        "scope",
        "location",
        "priority_location",
        "publishedDate",
        "created_at",
        "force_live",
        "featured",
        "tags",
        "custom_field",
    }
    assert protected_fields.isdisjoint(saved)
    assert saved["original_summary"] == original["summary"]
    assert "archived" not in saved


def test_existing_archived_or_hidden_state_is_not_auto_restored(monkeypatch):
    original = article(
        archived=True,
        archive_reason="manual_admin",
        manual_review_hidden_from_public=True,
        verification_status="needs_manual_review",
        rewrite_status="manual_review_required",
    )
    result, articles, _perplexity = run_regeneration(
        monkeypatch,
        [original],
        [safe_long_content()],
    )
    saved = articles.updates[0][1]["$set"]

    assert result["safe_regenerated"] == 0
    assert result["manual_review_routed"] == 1
    assert "manual_review_hidden_from_public" not in saved
    assert "verification_status" not in saved
    assert "rewrite_status" not in saved
    assert "archived" not in saved
    assert "archive_reason" not in saved


def test_empty_shorter_and_below_floor_rewrites_do_not_update(monkeypatch):
    current = safe_long_content()
    documents = [
        article(_id="empty", content=current),
        article(_id="shorter", content=current),
        article(_id="below-floor", content="Existing content. " * 10),
    ]
    outputs = [
        "",
        current[:-100],
        "A valid but still short rewrite. " * 20,
    ]

    result, articles, _perplexity = run_regeneration(
        monkeypatch,
        documents,
        outputs,
    )

    assert articles.updates == []
    assert result["regenerated"] == 0
    assert result["skipped_empty"] == 1
    assert result["skipped_too_short"] == 2
    assert result["processing_failures"] == 0


def test_risky_invention_language_is_saved_hidden_for_manual_review(monkeypatch):
    risky = safe_long_content() + (
        "\n\nAccording to local residents, a police spokesperson confirmed more details."
    )
    result, articles, _perplexity = run_regeneration(
        monkeypatch,
        [article()],
        [risky],
    )
    saved = articles.updates[0][1]["$set"]

    assert result["regenerated"] == 1
    assert result["safe_regenerated"] == 0
    assert result["manual_review_routed"] == 1
    assert saved["content"] == risky
    assert saved["manual_review_hidden_from_public"] is True
    assert saved["archived"] is True
    assert saved["archive_reason"] == "needs_manual_review"
    assert saved["verification_status"] == "needs_manual_review"
    assert saved["rewrite_status"] == "ai_rewrite_needs_review"
    assert saved["manual_review_created_at"]
    assert saved["archived_at"]
    assert "according to local residents" in saved["manual_review_hits"]


def test_repetitive_or_padded_rewrite_is_routed_to_manual_review(monkeypatch):
    repeated_paragraph = (
        "The company confirmed the same published investment timetable. "
        "The programme covers equipment, recruitment and supplier contracts. "
        "Further verified updates will be issued during the delivery period. "
    ) * 4
    repeated = "\n\n".join([repeated_paragraph] * 4)
    padded = safe_long_content() + (
        "\n\nThis serves as a reminder for readers. "
        "The announcement also underscores the importance of investment."
    )

    result, articles, _perplexity = run_regeneration(
        monkeypatch,
        [article(_id="repeated"), article(_id="padded")],
        [repeated, padded],
    )

    assert result["manual_review_routed"] == 2
    assert len(articles.updates) == 2
    reasons = [
        update["$set"]["manual_review_reason"]
        for _query, update in articles.updates
    ]
    assert any("duplicated paragraphs" in reason for reason in reasons)
    assert any("generic AI-style padding" in reason for reason in reasons)


def test_missing_location_local_rewrite_is_hidden_without_forced_archive(monkeypatch):
    result, articles, _perplexity = run_regeneration(
        monkeypatch,
        [
            article(
                category="Local News",
                scope="cheshire",
                location=None,
                priority_location=None,
            )
        ],
        [safe_long_content()],
    )
    saved = articles.updates[0][1]["$set"]

    assert result["manual_review_routed"] == 1
    assert saved["manual_review_hidden_from_public"] is True
    assert saved["verification_status"] == "needs_manual_review"
    assert saved["rewrite_status"] == "manual_review_required"
    assert "missing a specific town" in saved["manual_review_reason"]
    assert "archived" not in saved
    assert "archive_reason" not in saved


def test_guard_processing_failure_causes_no_partial_update(monkeypatch):
    def fail_guard(*_args, **_kwargs):
        raise RuntimeError("private guard failure")

    monkeypatch.setattr(server, "apply_ai_manual_review_guard", fail_guard)
    result, articles, _perplexity = run_regeneration(
        monkeypatch,
        [article()],
        [safe_long_content()],
    )

    assert articles.updates == []
    assert result["regenerated"] == 0
    assert result["processing_failures"] == 1
    assert "private guard failure" not in str(result)


def test_sanitizer_processing_failure_causes_no_partial_update(monkeypatch):
    def fail_sanitizer(*_args, **_kwargs):
        raise RuntimeError("private sanitizer failure")

    monkeypatch.setattr(server, "sanitize_rss_text", fail_sanitizer)
    result, articles, _perplexity = run_regeneration(
        monkeypatch,
        [article()],
        [safe_long_content()],
    )

    assert articles.updates == []
    assert result["regenerated"] == 0
    assert result["processing_failures"] == 1
    assert "private sanitizer failure" not in str(result)


def test_perplexity_failure_is_reported_without_update_or_retry(monkeypatch):
    result, articles, perplexity = run_regeneration(
        monkeypatch,
        [article()],
        [RuntimeError("private provider failure")],
    )

    assert len(perplexity.calls) == 1
    assert articles.updates == []
    assert result["processing_failures"] == 1
    assert "private provider failure" not in str(result)


def test_no_openai_or_other_route_is_added_to_regeneration_path():
    source = inspect.getsource(server.regenerate_recent_article_content)

    assert "OpenAI" not in source
    assert "openai" not in source.lower()
    assert "_import_hybrid_news_internal" not in source
    assert "sync_rss_now" not in source
    assert "regenerate_article_content" not in source
    assert "delete_" not in source
