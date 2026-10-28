"""Daily Slice 1: synthetic storage, credentials and providers only."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID
from urllib.parse import parse_qs, urlsplit
from unittest.mock import AsyncMock

import httpx
import pytest

from backend import server
from app.email_service import EmailService
from app.newsletter_delivery import (
    NewsletterDeliveryError,
    PreparedNewsletterDelivery,
    RecipientDeliveryContext,
    create_recipient_context,
    prepare_direct_delivery,
)
from app.newsletter_token_service import NewsletterTokenService
from app.public_article_eligibility import is_public_article_editorially_eligible


def subscriber(index=1, **changes):
    return {"email": f"reader{index}@synthetic.invalid", "active": True,
            "newsletter_management_id": str(UUID(int=index, version=4)),
            "newsletter_token_version": 1, **changes}


ARTICLE = {"id": "article-1", "title": "Cheshire business investment brings 20 jobs",
           "content": "Cheshire business investment will support local jobs and growth.",
           "category": "Business", "image": ""}
TOKEN_SERVICE = NewsletterTokenService("D" * 43)


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("Real provider forbidden")
    import app.email_service as module
    monkeypatch.setattr(module.httpx, "post", forbidden)
    monkeypatch.setattr(module.smtplib, "SMTP", forbidden)
    monkeypatch.setattr(module.smtplib, "SMTP_SSL", forbidden)
    monkeypatch.setattr(server, "newsletter_token_service_from_environment",
                        lambda: NewsletterTokenService("D" * 43))


@pytest.mark.parametrize("field,value", [
    ("newsletter_management_id", None), ("newsletter_management_id", "bad"),
    ("newsletter_management_id", "123e4567-e89b-12d3-a456-426614174000"),
    ("newsletter_token_version", None), ("newsletter_token_version", True),
    ("newsletter_token_version", "1"), ("newsletter_token_version", 0),
    ("newsletter_token_version", 1.0), ("active", None), ("active", False),
])
def test_invalid_selected_context_skipped(field, value):
    record = subscriber(**{field: value})
    if value is None:
        del record[field]
    prepared, counts, token_service = server._prepare_selected_newsletter_deliveries(
        [record["email"]], server._newsletter_candidate_contexts([record]))
    assert not prepared
    assert counts["selected_count"] == counts["skipped_count"] == 1
    assert counts["prepared_count"] == 0
    assert token_service is None


def test_provider_suppressed_selected_context_skipped():
    record = subscriber(provider_suppressed=True)
    prepared, counts, token_service = server._prepare_selected_newsletter_deliveries(
        [record["email"]], server._newsletter_candidate_contexts([record]))
    assert prepared == []
    assert counts == {
        "selected_count": 1,
        "prepared_count": 0,
        "skipped_count": 1,
        "skip_reasons": {"provider_suppressed": 1},
    }
    assert token_service is None


@pytest.mark.parametrize("reverse", [False, True])
def test_ambiguity_before_deduplication(reverse):
    records = [subscriber(), subscriber(2, email=subscriber()["email"])]
    if reverse:
        records.reverse()
    prepared, counts, _ = server._prepare_selected_newsletter_deliveries(
        [records[0]["email"]], server._newsletter_candidate_contexts(records))
    assert not prepared
    assert counts["skip_reasons"] == {"conflicting_email_identity": 1}


def test_duplicate_management_identity_rejects_both_selected_slots():
    shared_id = subscriber(1)["newsletter_management_id"]
    records = [subscriber(1), subscriber(2, newsletter_management_id=shared_id)]
    prepared, counts, _ = server._prepare_selected_newsletter_deliveries(
        [record["email"] for record in records],
        server._newsletter_candidate_contexts(records),
    )
    assert prepared == []
    assert counts["skip_reasons"] == {"duplicate_management_identity": 2}


@pytest.mark.parametrize("configuration", [False, True])
def test_preparation_failure_safe(monkeypatch, caplog, configuration):
    def fail(*a):
        raise RuntimeError("PRIVATE_TOKEN reader1@synthetic.invalid")
    monkeypatch.setattr(server, "newsletter_token_service_from_environment" if configuration else
                        "prepare_direct_delivery", fail)
    records = [subscriber(), subscriber(2)]
    prepared, counts, token_service = server._prepare_selected_newsletter_deliveries(
        [r["email"] for r in records], server._newsletter_candidate_contexts(records))
    assert prepared == []
    assert counts["skip_reasons"] == {"direct_delivery_preparation_failed": 2}
    service = EmailService()
    service.last_accepted_recipients = ["stale"]
    assert service.send_daily_brief(prepared_deliveries=prepared, token_service=token_service,
                                    articles=[ARTICLE]) == (0, None)
    assert service.last_accepted_recipients == []
    assert "PRIVATE_TOKEN" not in caplog.text and records[0]["email"] not in caplog.text


def deliveries(count):
    return [prepare_direct_delivery(create_recipient_context(subscriber(i)).context,
                                    TOKEN_SERVICE) for i in range(1, count + 1)]


def check_message(message, prepared):
    human = prepared.human_unsubscribe_url
    assert human in message["html"] and human in message["text"]
    token = parse_qs(urlsplit(human).fragment)["token"][0]
    assert parse_qs(urlsplit(message["headers"]["List-Unsubscribe"][1:-1]).query)["token"] == [token]
    assert "https://cheshiretoday.co.uk/newsletter/preferences" in message["text"]
    assert "%23token" not in message["html"] and "%23token" not in message["text"]
    assert "Unsubscribe: https://cheshiretoday.co.uk/unsubscribe\n" not in message["text"]


@pytest.mark.parametrize("transport", ["resend", "smtp"])
def test_direct_body_headers_tracking_and_acceptance(monkeypatch, transport):
    service = EmailService()
    service.resend_enabled = transport == "resend"
    service.resend_api_key = "synthetic"
    service.from_email = "sender@synthetic.invalid"
    service.last_accepted_recipients = ["stale"]
    prepared = deliveries(101)
    messages, chunks = [], []
    def post(url, *, json, **kwargs):
        chunks.append(len(json))
        messages.extend([{**item, "to": item["to"][0]} for item in json])
        return httpx.Response(
            200,
            json={"data": [{"id": f"email-{len(chunks)}-{index}"} for index in range(len(json))]},
            request=httpx.Request("POST", "https://synthetic.invalid"),
        )
    def smtp(to, subject, html, text, *, newsletter_headers, feedback_id):
        assert feedback_id == "daily:::cheshtoday"
        messages.append({"to": to, "html": html, "text": text, "headers": newsletter_headers})
        return True
    monkeypatch.setattr("app.email_service.httpx.post", post)
    monkeypatch.setattr(service, "_send_email", smtp)
    count, tracking = service.send_daily_brief(
        prepared_deliveries=prepared, token_service=TOKEN_SERVICE, articles=[ARTICLE])
    assert count == 101
    assert service.last_accepted_recipients == [d.context.email for d in prepared]
    assert chunks == ([100, 1] if transport == "resend" else [])
    for message, delivery in zip(messages, prepared):
        check_message(message, delivery)
        assert service._recipient_tracking_id(tracking, delivery.context.email) in message["html"]
    assert len({m["headers"]["List-Unsubscribe"] for m in messages}) == 101


def test_preview_explicit_and_normal_email_only_fails(monkeypatch):
    service = EmailService()
    service.resend_enabled = False
    service.last_accepted_recipients = ["stale"]
    with pytest.raises(NewsletterDeliveryError):
        service.send_daily_brief(to_emails=["preview@synthetic.invalid"], articles=[ARTICLE])
    with pytest.raises(NewsletterDeliveryError):
        service.send_daily_brief(to_emails=["one@synthetic.invalid", "two@synthetic.invalid"],
                                 articles=[ARTICLE], preview=True)
    assert service.last_accepted_recipients == []
    captured = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: captured.append((a, k)) or True)
    assert service.send_daily_brief(to_emails=["preview@synthetic.invalid"], articles=[ARTICLE], preview=True)[0] == 1
    assert captured[0][1] == {}
    assert "#token=" not in str(captured)


def test_prepared_delivery_binding_accepts_factory_artifact(monkeypatch):
    service = EmailService()
    service.resend_enabled = False
    sent = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: sent.append((a, k)) or True)
    prepared = deliveries(1)
    assert service.send_daily_brief(
        prepared_deliveries=prepared, token_service=TOKEN_SERVICE, articles=[ARTICLE]
    )[0] == 1
    assert len(sent) == 1


def test_prepared_delivery_binding_rejects_cross_wiring_before_provider(monkeypatch):
    service = EmailService()
    service.resend_enabled = False
    contacted = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: contacted.append(True) or True)
    first, second = deliveries(2)
    version_mismatch = RecipientDeliveryContext(
        first.context.email, first.context.newsletter_management_id, 2,
    )
    forged = prepare_direct_delivery(
        first.context, NewsletterTokenService("E" * 43),
    )
    malformed_native = object.__new__(PreparedNewsletterDelivery)
    object.__setattr__(malformed_native, "context", first.context)
    object.__setattr__(malformed_native, "human_unsubscribe_url",
                       first.human_unsubscribe_url)
    object.__setattr__(malformed_native, "native_headers", {
        **dict(first.native_headers),
        "List-Unsubscribe": dict(first.native_headers)["List-Unsubscribe"].replace(
            ">", "&extra=1>"
        ),
    })
    cases = [
        PreparedNewsletterDelivery(first.context, second.human_unsubscribe_url,
                                   second.native_headers),
        PreparedNewsletterDelivery(first.context, first.human_unsubscribe_url,
                                   second.native_headers),
        PreparedNewsletterDelivery(first.context, second.human_unsubscribe_url,
                                   first.native_headers),
        PreparedNewsletterDelivery(second.context, first.human_unsubscribe_url,
                                   first.native_headers),
        PreparedNewsletterDelivery(version_mismatch, first.human_unsubscribe_url,
                                   first.native_headers),
        forged,
        malformed_native,
        PreparedNewsletterDelivery(
            first.context,
            first.human_unsubscribe_url.replace("/unsubscribe#", "/unsubscribe?extra=1#"),
            first.native_headers,
        ),
    ]
    for invalid in cases:
        with pytest.raises(NewsletterDeliveryError) as error:
            service.send_daily_brief(
                prepared_deliveries=[invalid], token_service=TOKEN_SERVICE,
                articles=[ARTICLE],
            )
        assert str(error.value) == "invalid_prepared_delivery"
        assert "token=" not in str(error.value)
    assert contacted == []


def test_daily_contract_rejects_mixed_preview_and_prepared_arguments(monkeypatch):
    service = EmailService()
    contacted = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: contacted.append(True) or True)
    prepared = deliveries(1)
    invalid_calls = [
        {"to_emails": ["preview@synthetic.invalid"], "prepared_deliveries": prepared,
         "token_service": TOKEN_SERVICE},
        {"to_emails": ["preview@synthetic.invalid"], "prepared_deliveries": prepared,
         "token_service": TOKEN_SERVICE, "preview": True},
    ]
    for kwargs in invalid_calls:
        with pytest.raises(NewsletterDeliveryError):
            service.send_daily_brief(articles=[ARTICLE], **kwargs)
    assert contacted == []


class Cursor:
    def __init__(self, rows):
        self.rows = deepcopy(rows)
    async def to_list(self, limit):
        return self.rows[:limit]


class Collection:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.updates, self.inserts, self.projections = [], [], []
    def find(self, query, projection):
        self.projections.append(projection)
        return Cursor(self.rows)
    def aggregate(self, pipeline):
        return Cursor(self.rows)
    async def find_one(self, query):
        if "instance_id" in query:
            return {"_id": "claim", **query}
        return None
    async def insert_one(self, record):
        self.inserts.append(record)
        return SimpleNamespace(inserted_id="claim")
    async def update_one(self, query, update, **kwargs):
        self.updates.append((query, update))
        return SimpleNamespace(matched_count=1)


# Exercise the real scheduled selector, including the fields actually emitted by
# its aggregation. The older general-purpose Collection intentionally does not
# emulate aggregation and cannot detect dropped editorial metadata.
EDITORIAL_NOW = datetime(2026, 10, 28, 7, 30, tzinfo=timezone.utc)
PAPERS_TITLE = (
    "The Papers: 'Budget for a difficult moment' and Netanyahu's 'fate in balance'"
)


def editorial_article(index, **changes):
    return {
        "_id": f"mongo-{index}", "id": f"uuid-{index}",
        "title": "Cheshire business investment brings 20 jobs",
        "summary": "New investment supports Cheshire employers.",
        "content": "Cheshire business investment supports jobs and savings.",
        "category": "Business", "source": "Synthetic publisher",
        "source_url": f"https://publisher.invalid/news/{index}",
        "publishedDate": EDITORIAL_NOW - timedelta(hours=2),
        "author": "Synthetic author", "image": "", "is_local_source": False,
        "force_live": False, "archived": False,
        "manual_review_hidden_from_public": False, **changes,
    }


class EditorialArticleCollection(Collection):
    """Bounded implementation of only the selector's current Mongo stages."""
    def __init__(self, rows):
        super().__init__(rows)
        self.pipelines = []

    @staticmethod
    def matches(row, query):
        for field, condition in query.items():
            if field == "$or":
                if not any(EditorialArticleCollection.matches(row, part)
                           for part in condition):
                    return False
            elif isinstance(condition, dict) and "$ne" in condition:
                if row.get(field) == condition["$ne"]:
                    return False
            elif isinstance(condition, dict) and "$gte" in condition:
                value, boundary = row.get(field), condition["$gte"]
                # Mongo comparisons are type-bracketed; each date representation
                # is tested against its corresponding real query branch.
                if isinstance(value, datetime) and isinstance(boundary, datetime):
                    if value.replace(tzinfo=None) < boundary.replace(tzinfo=None):
                        return False
                elif isinstance(value, str) and isinstance(boundary, str):
                    if value < boundary:
                        return False
                else:
                    return False
            else:
                raise AssertionError(f"Unsupported synthetic predicate: {field}")
        return True

    def aggregate(self, pipeline):
        self.pipelines.append(deepcopy(pipeline))
        rows = deepcopy(self.rows)
        for stage in pipeline:
            if "$match" in stage:
                rows = [row for row in rows if self.matches(row, stage["$match"])]
            elif "$sort" in stage:
                for field, direction in reversed(list(stage["$sort"].items())):
                    rows.sort(key=lambda row: str(row.get(field) or ""),
                              reverse=direction < 0)
            elif "$group" in stage:
                spec, grouped = stage["$group"], {}
                for row in rows:
                    key = row.get(spec["_id"][1:])
                    if key in grouped:
                        continue
                    grouped[key] = {"_id": key}
                    for field, expression in spec.items():
                        if field != "_id":
                            grouped[key][field] = row.get(expression["$first"][1:])
                rows = list(grouped.values())
            elif "$limit" in stage:
                rows = rows[:stage["$limit"]]
            else:
                raise AssertionError("Unsupported synthetic aggregation stage")
        return Cursor(rows)


@pytest.fixture
def scheduled_editorial_run(monkeypatch):
    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return EDITORIAL_NOW.astimezone(tz) if tz else EDITORIAL_NOW.replace(tzinfo=None)

        @classmethod
        def utcnow(cls):
            return EDITORIAL_NOW.replace(tzinfo=None)

    monkeypatch.setattr(server, "datetime", FixedClock)
    monkeypatch.setenv("HOSTNAME", "offline-editorial")
    monkeypatch.setenv("DAILY_BRIEF_SEND_CAP", "2")

    def run(articles):
        rows = [subscriber(1, priority_daily_brief=True), subscriber(2), subscriber(3)]
        db = SimpleNamespace(
            subscribers=Collection(rows), articles=EditorialArticleCollection(articles),
            digest_log=Collection(), email_batch_cursors=Collection(),
            email_send_opportunities=Collection(),
        )
        captured = []
        service = EmailService()
        service.resend_enabled = False

        def send(**kwargs):
            captured.append(deepcopy(kwargs["articles"]))
            service.last_accepted_recipients = [
                delivery.context.email for delivery in kwargs["prepared_deliveries"]
            ]
            service.last_provider_contacted = True
            return len(service.last_accepted_recipients), "synthetic-editorial-campaign"

        monkeypatch.setattr(server, "db", db)
        monkeypatch.setattr(server, "email_service", service)
        monkeypatch.setattr(service, "send_daily_brief", send)
        asyncio.run(server.send_scheduled_news_digest())
        fields = {}
        for _, update in db.digest_log.updates:
            fields.update(update.get("$set", {}))
        # Ensure failures are about editorial selection, not swallowed job errors,
        # missing recipients, transport, or changed persistence/accounting.
        assert len(captured) == 1
        assert fields["status"] == "sent"
        assert fields["selected_count"] == fields["prepared_count"] == 2
        assert fields["accepted_count"] == 2
        assert service.last_accepted_recipients == [subscriber(1)["email"], subscriber(2)["email"]]
        assert len(db.email_batch_cursors.updates) == 1
        assert len(db.email_send_opportunities.updates) == 1
        return captured[0], db

    return run


@pytest.mark.parametrize("selection_path", ["fresh", "minimum_two", "no_fresh"])
def test_scheduled_editorial_veto_excludes_papers_in_every_selection_path(
    scheduled_editorial_run, selection_path,
):
    papers = editorial_article(
        1, title=PAPERS_TITLE, category="UK News",
        content="Budget changes affect jobs, mortgages and savings.",
    )
    legitimate = editorial_article(2)
    if selection_path == "minimum_two":
        # Score below 30, but not banned by the legacy weak-topic list. One
        # legitimate candidate makes the actual minimum-two branch reachable.
        papers["content"] = "Budget discussion accompanies police coverage."
    if selection_path == "no_fresh":
        for row in (papers, legitimate):
            row["publishedDate"] = EDITORIAL_NOW - timedelta(days=3)
    assert is_public_article_editorially_eligible(papers) is False
    sent, db = scheduled_editorial_run([papers, legitimate])
    assert len(db.articles.pipelines) == (2 if selection_path == "no_fresh" else 1)
    assert legitimate["_id"] in {row["id"] for row in sent}
    assert papers["_id"] not in {row["id"] for row in sent}
    assert all(row["title"] != PAPERS_TITLE for row in sent)


@pytest.mark.parametrize("fallback", [False, True])
def test_scheduled_editorial_aggregation_preserves_shared_policy_metadata(
    monkeypatch, scheduled_editorial_run, fallback,
):
    row = editorial_article(1)
    if fallback:
        row["publishedDate"] = EDITORIAL_NOW - timedelta(days=3)
    evaluated = []

    def capture_eligibility(article):
        evaluated.append(deepcopy(article))
        return is_public_article_editorially_eligible(article)

    monkeypatch.setattr(server, "is_public_article_editorially_eligible", capture_eligibility)
    sent, db = scheduled_editorial_run([row])
    required = {"summary", "source_url", "is_local_source", "force_live"}
    for pipeline in db.articles.pipelines:
        group = next(stage["$group"] for stage in pipeline if "$group" in stage)
        expected = required | {
            "title", "content", "category", "publishedDate", "source", "author", "image",
        }
        missing = sorted(field for field in expected
                         if group.get(field) != {"$first": f"${field}"})
        assert missing == [], f"Editorial fields dropped by aggregation: {missing}"
        assert group["mongo_id"] == {"$first": "$_id"}
        assert group["custom_id"] == {"$first": "$id"}
        assert pipeline[0]["$match"]["archived"] == {"$ne": True}
        assert pipeline[0]["$match"]["manual_review_hidden_from_public"] == {"$ne": True}
    assert sent[0]["id"] == row["_id"]
    assert len(evaluated) == 1
    assert evaluated[0]["summary"] == row["summary"]
    assert "summary" not in sent[0]  # Preserve the committed renderer input.
    for field in required:
        if field != "summary":
            assert sent[0][field] == row[field]


@pytest.mark.parametrize("metadata", [
    {"summary": "The Papers: a newspaper front-page roundup"},
    {"source_url": "https://publisher.invalid/video/budget"},
])
def test_scheduled_editorial_veto_uses_summary_and_source_url(scheduled_editorial_run, metadata):
    rejected = editorial_article(1, **metadata)
    assert is_public_article_editorially_eligible(rejected) is False
    sent, _ = scheduled_editorial_run([
        rejected, editorial_article(2, title="UK tax rules affect Cheshire employers"),
    ])
    assert rejected["_id"] not in {row["id"] for row in sent}


@pytest.mark.parametrize("title,category", [
    ("UK Budget effects on Cheshire households", "UK News"),
    ("Tax changes affecting Cheshire businesses", "Finance"),
    ("Crewe employment investment creates new jobs", "Local News"),
    ("Bank of England interest rates reshape UK mortgage costs", "UK News"),
])
def test_scheduled_editorial_legitimate_reporting_remains_eligible(
    scheduled_editorial_run, title, category,
):
    row = editorial_article(1, title=title, category=category)
    assert is_public_article_editorially_eligible(row) is True
    sent, _ = scheduled_editorial_run([row])
    assert [article["id"] for article in sent] == [row["_id"]]


@pytest.mark.parametrize("exception", ["force_live", "is_local_source"])
def test_scheduled_editorial_preserves_existing_shared_policy_exceptions(
    scheduled_editorial_run, exception,
):
    # These are existing helper contracts, not new rescue rules. The metadata
    # contract above prevents a future veto from losing their provenance.
    row = editorial_article(1, title=PAPERS_TITLE, category="UK News",
                            **{exception: True})
    assert is_public_article_editorially_eligible(row) is True
    sent, _ = scheduled_editorial_run([row])
    assert [article["id"] for article in sent] == [row["_id"]]


@pytest.mark.parametrize("iso_date", [False, True])
def test_scheduled_editorial_keeps_existing_scoring_and_date_representations(
    scheduled_editorial_run, iso_date,
):
    national = editorial_article(
        1, title="Bank of England mortgage rates outlook", category="UK News",
        content="Mortgage rates affect household bills.", summary="Mortgage costs.",
    )
    local = editorial_article(
        2, title="Crewe factory investment creates 20 jobs", category="Local News",
        content="Crewe factory investment supports jobs.", summary="Local investment.",
    )
    if iso_date:
        for row in (national, local):
            row["publishedDate"] = row["publishedDate"].isoformat()
    assert all(is_public_article_editorially_eligible(row) for row in (national, local))
    sent, db = scheduled_editorial_run([national, local])
    # Existing local/business scoring outranks the national money-only item.
    assert [row["id"] for row in sent] == [local["_id"], national["_id"]]
    assert len(db.articles.pipelines) == 1


@pytest.mark.parametrize("fallback", [False, True])
def test_scheduled_editorial_status_freshness_and_topic_dedupe_controls(
    scheduled_editorial_run, fallback,
):
    winner = editorial_article(1)
    duplicate = editorial_article(2, title="Cheshire business investment brings 20 new jobs")
    hidden = editorial_article(3, title="Tax savings for households", manual_review_hidden_from_public=True)
    archived = editorial_article(4, title="UK mortgage rates and prices", archived=True)
    stale = editorial_article(5, title="Nantwich housing plan supports growth",
                              publishedDate=EDITORIAL_NOW - timedelta(days=4))
    rows = [winner, duplicate, hidden, archived]
    if fallback:
        for row in rows:
            row["publishedDate"] = EDITORIAL_NOW - timedelta(days=3)
    else:
        rows.append(stale)
    sent, db = scheduled_editorial_run(rows)
    assert [row["id"] for row in sent] == [winner["_id"]]
    assert len(db.articles.pipelines) == (2 if fallback else 1)


@pytest.mark.parametrize("pool", ["fresh_rejected", "fallback_rejected", "empty"])
def test_scheduled_zero_eligible_finalises_owned_digest_without_delivery(
    monkeypatch, scheduled_editorial_run, pool,
):
    # Reuse the fixed clock/environment setup, not the successful-send-only
    # runner: an empty eligible pool must never enter that runner's send mock.
    rows = [] if pool == "empty" else [editorial_article(
        1, title=PAPERS_TITLE, category="UK News",
    )]
    if pool == "fallback_rejected":
        rows[0]["publishedDate"] = EDITORIAL_NOW - timedelta(days=3)
    assert all(not is_public_article_editorially_eligible(row) for row in rows)
    db = SimpleNamespace(
        subscribers=Collection([subscriber(1), subscriber(2)]),
        articles=EditorialArticleCollection(rows), digest_log=Collection(),
        email_batch_cursors=Collection(), email_send_opportunities=Collection(),
    )
    service = EmailService()
    service.resend_enabled = False
    send_calls, phases = [], []

    def unexpected_send(**kwargs):
        # Return normally so an erroneous send cannot masquerade as a passing
        # pre-provider failure through the outer exception handler.
        send_calls.append(kwargs)
        return 0, None

    evidence = AsyncMock(return_value=(True, 0))
    ledger = AsyncMock(return_value=0)
    cursor = AsyncMock()
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(service, "send_daily_brief", unexpected_send)
    monkeypatch.setattr(server, "_save_last_resend_acceptances", evidence)
    monkeypatch.setattr(server, "_save_email_send_opportunities", ledger)
    monkeypatch.setattr(server, "_save_email_batch_cursor", cursor)
    monkeypatch.setattr(
        server, "log_daily_brief_memory",
        lambda _logger, phase, _started_at, counts=None: phases.append(phase),
    )
    asyncio.run(server.send_scheduled_news_digest())

    assert send_calls == []
    evidence.assert_not_awaited()
    ledger.assert_not_awaited()
    cursor.assert_not_awaited()
    assert db.email_send_opportunities.updates == []
    assert db.email_batch_cursors.updates == []
    assert service.last_accepted_recipients == []
    assert len(db.articles.pipelines) == (1 if pool == "fresh_rejected" else 2)
    assert len(db.digest_log.inserts) == 1
    claim = db.digest_log.inserts[0]
    fields = dict(claim)
    for _, update in db.digest_log.updates:
        fields.update(update.get("$set", {}))
    # Existing Daily Brief zero-acceptance completion uses failed/completed_at;
    # Weekly Roundup independently establishes failed for no articles pre-send.
    assert fields["status"] == "failed", "No-send digest left in an in-progress state"
    assert fields["success_count"] == fields["accepted_count"] == 0
    assert fields["provider_contacted"] is False
    assert fields["articles_count"] == 0
    assert isinstance(fields.get("completed_at"), datetime)
    assert fields["completed_at"] == EDITORIAL_NOW
    terminal_query, _ = next(
        (query, update) for query, update in reversed(db.digest_log.updates)
        if update.get("$set", {}).get("status") == "failed"
    )
    assert terminal_query["instance_id"] == claim["instance_id"]
    assert terminal_query["digest_time"] == claim["digest_time"]
    assert terminal_query["date_key"] == claim["date_key"]
    assert "provider_returned" not in phases
    assert "send_ledger_persistence_completed" not in phases
    assert "batch_cursor_persistence_completed" not in phases
    assert phases[-1] == "function_returned"


@pytest.mark.parametrize("scenario", [
    "exception", "different_owner", "sent", "failed", "partial", "ambiguous",
    "zero_match", "owned_sending",
])
def test_zero_eligible_completion_preserves_owner_and_terminal_state(
    monkeypatch, scheduled_editorial_run, caplog, scenario,
):
    caplog.set_level("INFO", logger="backend.server")

    class OwnershipDigest(Collection):
        def __init__(self):
            super().__init__()
            self.record = None
            self.before_completion = None
            self.completion_attempts = []

        async def insert_one(self, record):
            self.record = deepcopy(record)
            return await super().insert_one(record)

        async def find_one(self, query):
            if self.record and all(self.record.get(k) == v for k, v in query.items()):
                return {"_id": "claim", **self.record}
            return None

        async def update_one(self, query, update, **kwargs):
            fields = update.get("$set", {})
            if fields.get("status") == "failed":
                self.completion_attempts.append(deepcopy(query))
                if self.before_completion is None:
                    if scenario in {"exception", "different_owner"}:
                        self.record["instance_id"] = "replacement-owner"
                        self.record["status"] = "sent"
                    elif scenario in {"sent", "failed", "partial", "ambiguous"}:
                        self.record["status"] = scenario
                    elif scenario == "zero_match":
                        self.record["status"] = "cancelled"
                    self.before_completion = deepcopy(self.record)
                    if scenario == "exception":
                        raise RuntimeError("PRIVATE_EXCEPTION reader@synthetic.invalid")
            matched = int(all(self.record.get(k) == v for k, v in query.items()))
            self.updates.append((deepcopy(query), deepcopy(update)))
            if matched:
                self.record.update(deepcopy(fields))
            return SimpleNamespace(matched_count=matched)

    digest = OwnershipDigest()
    db = SimpleNamespace(
        subscribers=Collection([subscriber()]),
        articles=EditorialArticleCollection([editorial_article(1, title=PAPERS_TITLE)]),
        digest_log=digest, email_batch_cursors=Collection(),
        email_send_opportunities=Collection(),
    )
    service = EmailService()
    send_calls, phases = [], []

    def forbidden_send(**kwargs):
        send_calls.append(True)
        return 0, None

    evidence, ledger, cursor = AsyncMock(), AsyncMock(), AsyncMock()
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(service, "send_daily_brief", forbidden_send)
    monkeypatch.setattr(server, "_save_last_resend_acceptances", evidence)
    monkeypatch.setattr(server, "_save_email_send_opportunities", ledger)
    monkeypatch.setattr(server, "_save_email_batch_cursor", cursor)
    monkeypatch.setattr(server, "log_daily_brief_memory",
                        lambda _l, phase, _s, counts=None: phases.append(phase))
    asyncio.run(server.send_scheduled_news_digest())

    assert send_calls == []
    evidence.assert_not_awaited()
    ledger.assert_not_awaited()
    cursor.assert_not_awaited()
    assert len(db.articles.pipelines) == 1
    assert len(digest.completion_attempts) == 1, "Completion retried through outer handler"
    guard = digest.completion_attempts[0]
    assert guard == {
        "digest_time": "DailyBrief", "date_key": "20261028",
        "instance_id": digest.inserts[0]["instance_id"], "status": "sending",
    }
    assert "PRIVATE_EXCEPTION" not in caplog.text
    assert "reader@synthetic.invalid" not in caplog.text
    assert "provider_returned" not in phases
    assert "completion_persistence_completed" not in phases
    assert phases[-1] == "function_returned"
    if scenario == "owned_sending":
        assert digest.record["status"] == "failed"
        assert digest.record["completed_at"] == EDITORIAL_NOW
        assert digest.record["accepted_count"] == digest.record["success_count"] == 0
        assert digest.record["provider_contacted"] is False
    else:
        assert digest.record == digest.before_completion
        assert "completed_at" not in digest.record
        assert "Digest log updated" not in caplog.text
        expected = ("Daily Brief no-article finalisation failed" if scenario == "exception"
                    else "Daily Brief no-article finalisation not confirmed")
        assert expected in caplog.text


@pytest.mark.parametrize("format_index", [0, 1], ids=["html", "plain_text"])
def test_scheduled_secondary_excerpt_preserves_committed_body_derived_output(
    monkeypatch, scheduled_editorial_run, format_index,
):
    hero = editorial_article(1)
    secondary = editorial_article(
        2, title="UK mortgage rates outlook", category="UK News",
        content="Mortgage bills affect households. Further verified reporting follows.",
        summary="A different stored summary must not replace the existing newsletter excerpt.",
    )
    assert is_public_article_editorially_eligible(secondary)
    selected, _ = scheduled_editorial_run([hero, secondary])
    assert [row["id"] for row in selected] == [hero["_id"], secondary["_id"]]
    # HEAD's two aggregation branches omitted summary. Reconstruct that exact
    # presentation input, not a different version of the shared email renderer.
    committed_input = [{key: value for key, value in row.items() if key != "summary"}
                       for row in selected]
    renderer = EmailService()
    renderer.resend_enabled = False
    messages = []

    def capture(_to, _subject, html, text, **kwargs):
        messages.append((html, text))
        return True

    monkeypatch.setattr(renderer, "_send_email", capture)
    monkeypatch.setattr(renderer, "_generate_tracking_id", lambda *_: "fixed-excerpt-test")
    prepared = deliveries(1)
    for articles in (committed_input, selected):
        assert renderer.send_daily_brief(
            prepared_deliveries=prepared, token_service=TOKEN_SERVICE, articles=articles,
        )[0] == 1
    assert len(messages) == 2
    expected_html, expected_text = messages[0]
    actual_html, actual_text = messages[1]
    assert "Mortgage bills affect households." in expected_html
    assert "Mortgage bills affect households." in expected_text
    assert "A different stored summary" not in expected_html
    assert "A different stored summary" not in expected_text
    assert messages[1][format_index] == messages[0][format_index], (
        "Eligibility metadata changed the secondary excerpt"
    )


@pytest.mark.parametrize("manual", [False, True])
@pytest.mark.parametrize("accepted", [0, 1])
def test_real_daily_selection_slots_accounting_and_cursor(monkeypatch, manual, accepted):
    rows = [subscriber(1, priority_daily_brief=True),
            subscriber(2, newsletter_management_id=None), subscriber(3), subscriber(4)]
    db = SimpleNamespace(subscribers=Collection(rows), articles=Collection([ARTICLE]),
                         digest_log=Collection(), email_batch_cursors=Collection(),
                         email_send_opportunities=Collection())
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setenv("DAILY_BRIEF_SEND_CAP", "3")
    monkeypatch.setenv("HOSTNAME", "offline")
    service = EmailService()
    service.resend_enabled = False
    captured = []
    def smtp(to, *args, **kwargs):
        captured.append(to)
        return len(captured) <= accepted
    monkeypatch.setattr(service, "_send_email", smtp)
    monkeypatch.setattr(server, "email_service", service)
    if manual:
        result = asyncio.run(server.send_digest_now())
        counts = result["delivery_counts"]
    else:
        asyncio.run(server.send_scheduled_news_digest())
        fields = {}
        for _, update in db.digest_log.updates:
            fields.update(update["$set"])
        counts = fields
        assert fields["planned_batch_start"] == 0
        assert fields["planned_batch_next"] == 2
        assert fields["planned_batch_size"] == 3
        assert bool(db.email_batch_cursors.updates) is bool(accepted)
        assert bool(db.email_send_opportunities.updates) is bool(accepted)
    assert captured == [rows[0]["email"], rows[2]["email"]]  # No backfill from row 4.
    assert counts["selected_count"] == 3
    assert counts["prepared_count"] == 2 and counts["skipped_count"] == 1
    assert counts["accepted_count"] == accepted
    assert service.last_accepted_recipients == captured[:accepted]
    assert {"email", "active", "newsletter_management_id", "newsletter_token_version"} <= set(db.subscribers.projections[0])


@pytest.mark.parametrize("manual", [False, True])
def test_daily_query_excludes_provider_suppressed_before_selection(monkeypatch, manual):
    class FilteringCollection(Collection):
        def find(self, query, projection):
            self.projections.append(projection)
            assert {"provider_suppressed": {"$ne": True}} in query["$and"]
            assert projection["provider_suppressed"] == 1
            return Cursor([row for row in self.rows if row.get("provider_suppressed") is not True])

    rows = [subscriber(1, provider_suppressed=True, priority_daily_brief=True),
            subscriber(2), subscriber(3)]
    db = SimpleNamespace(subscribers=FilteringCollection(rows), articles=Collection([ARTICLE]),
                         digest_log=Collection(), email_batch_cursors=Collection(),
                         email_send_opportunities=Collection())
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setenv("DAILY_BRIEF_SEND_CAP", "2")
    monkeypatch.setenv("HOSTNAME", "offline")
    service = EmailService()
    service.resend_enabled = False
    captured = []
    monkeypatch.setattr(service, "_send_email", lambda to, *a, **k: captured.append(to) or True)
    monkeypatch.setattr(server, "email_service", service)
    if manual:
        asyncio.run(server.send_digest_now())
    else:
        asyncio.run(server.send_scheduled_news_digest())
    assert captured == [rows[1]["email"], rows[2]["email"]]


def test_scheduled_all_invalid_is_preparation_failure_without_provider(monkeypatch, caplog):
    rows = [subscriber(1, newsletter_management_id=None),
            subscriber(2, newsletter_token_version=0)]
    db = SimpleNamespace(subscribers=Collection(rows), articles=Collection([ARTICLE]),
                         digest_log=Collection(), email_batch_cursors=Collection(),
                         email_send_opportunities=Collection())
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setenv("HOSTNAME", "offline")
    service = EmailService()
    service.resend_enabled = False
    contacted = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: contacted.append(True) or True)
    monkeypatch.setattr(server, "email_service", service)
    asyncio.run(server.send_scheduled_news_digest())
    fields = {}
    for _, update in db.digest_log.updates:
        fields.update(update["$set"])
    assert contacted == []
    assert fields["status"] == "failed"
    assert fields["provider_contacted"] is False
    assert fields["provider_error"] == "Daily Brief preparation produced no provider messages"
    assert fields["prepared_count"] == 0 and fields["skipped_count"] == 2
    assert not db.email_batch_cursors.updates and not db.email_send_opportunities.updates
    assert "provider failure" not in caplog.text.lower()


@pytest.mark.parametrize("transport", ["smtp_disabled", "resend_unconfigured"])
def test_scheduled_prepared_but_transport_unavailable_is_not_provider_contact(
    monkeypatch, caplog, transport,
):
    db = SimpleNamespace(
        subscribers=Collection([subscriber()]),
        articles=Collection([ARTICLE]),
        digest_log=Collection(),
        email_batch_cursors=Collection(),
        email_send_opportunities=Collection(),
    )
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setenv("HOSTNAME", "offline")

    service = EmailService()
    phases = []
    if transport == "smtp_disabled":
        service.resend_enabled = False
        service.smtp_enabled = False
    else:
        service.resend_enabled = True
        service.resend_api_key = None
        service.from_email = "sender@synthetic.invalid"

    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(
        server,
        "log_daily_brief_memory",
        lambda _logger, phase, _started_at, counts=None: phases.append(
            (phase, dict(counts or {}))
        ),
    )
    asyncio.run(server.send_scheduled_news_digest())

    fields = {}
    for _, update in db.digest_log.updates:
        fields.update(update["$set"])

    assert fields["selected_count"] == 1
    assert fields["prepared_count"] == 1
    assert fields["skipped_count"] == 0
    assert fields["accepted_count"] == 0
    assert fields["status"] == "failed"
    assert fields["provider_contacted"] is False
    assert fields["provider_error"] == "Daily Brief transport unavailable before provider contact"
    assert not db.email_batch_cursors.updates
    assert not db.email_send_opportunities.updates
    assert service.last_accepted_recipients == []
    assert "provider failure" not in caplog.text.lower()
    phase_counts = dict(phases)
    assert phase_counts["acceptance_evidence_snapshot_completed"] == {
        "acceptance_evidence_count": 0,
        "accepted_recipient_count": 0,
    }
    assert phase_counts["acceptance_evidence_persistence_completed"] == {
        "attempted_evidence_count": 0,
        "inserted_evidence_count": 0,
    }
    assert "send_ledger_persistence_completed" not in phase_counts
    assert "batch_cursor_persistence_completed" not in phase_counts


@pytest.mark.parametrize("invalid_priority,expected", [
    (True, [2]),
    (False, [1]),
])
def test_invalid_selected_slot_never_backfills_priority_or_rotation(
    monkeypatch, invalid_priority, expected,
):
    if invalid_priority:
        rows = [subscriber(1, priority_daily_brief=True, newsletter_token_version=0),
                subscriber(2), subscriber(3)]
    else:
        rows = [subscriber(1, priority_daily_brief=True),
                subscriber(2, newsletter_token_version=0), subscriber(3)]
    db = SimpleNamespace(subscribers=Collection(rows), articles=Collection([ARTICLE]),
                         digest_log=Collection(), email_batch_cursors=Collection(),
                         email_send_opportunities=Collection())
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setenv("DAILY_BRIEF_SEND_CAP", "2")
    monkeypatch.setenv("HOSTNAME", "offline")
    service = EmailService()
    service.resend_enabled = False
    captured = []
    monkeypatch.setattr(service, "_send_email", lambda to, *a, **k: captured.append(to) or True)
    monkeypatch.setattr(server, "email_service", service)
    asyncio.run(server.send_scheduled_news_digest())
    assert captured == [subscriber(index)["email"] for index in expected]
    assert subscriber(3)["email"] not in captured


@pytest.mark.parametrize("start,cap,expected,next_index", [
    (2, 3, [1, 4, 2], 1), (0, 1, [1], 0), (99, 3, [1, 2, 3], 2),
])
def test_scheduled_rotation_order_and_cap_parity(monkeypatch, start, cap, expected, next_index):
    rows = [subscriber(4), subscriber(2), subscriber(1, signup_source="website"), subscriber(3)]
    db = SimpleNamespace(subscribers=Collection(rows), articles=Collection([ARTICLE]),
                         digest_log=Collection(), email_batch_cursors=Collection(),
                         email_send_opportunities=Collection())
    async def cursor(query):
        return {"next_index": start}
    db.email_batch_cursors.find_one = cursor
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setenv("DAILY_BRIEF_SEND_CAP", str(cap))
    monkeypatch.setenv("HOSTNAME", "offline")
    service = EmailService()
    service.resend_enabled = False
    captured = []
    monkeypatch.setattr(service, "_send_email", lambda to, *a, **k: captured.append(to) or True)
    monkeypatch.setattr(server, "email_service", service)
    asyncio.run(server.send_scheduled_news_digest())
    assert captured == [subscriber(i)["email"] for i in expected]
    assert db.email_batch_cursors.updates[-1][1]["$set"]["next_index"] == next_index


def test_resend_partial_chunk_acceptance(monkeypatch):
    service = EmailService()
    service.resend_enabled = True
    service.resend_api_key = "synthetic"
    service.from_email = "sender@synthetic.invalid"
    calls = []
    def post(url, *, json, **kwargs):
        calls.append(len(json))
        status = 400 if len(calls) == 1 else 200
        return httpx.Response(
            status,
            json={"data": [{"id": f"email-{len(calls)}-{index}"} for index in range(len(json))]},
            request=httpx.Request("POST", "https://synthetic.invalid"),
        )
    monkeypatch.setattr("app.email_service.httpx.post", post)
    prepared = deliveries(101)
    assert service.send_daily_brief(prepared_deliveries=prepared, token_service=TOKEN_SERVICE,
                                    articles=[ARTICLE])[0] == 1
    assert calls == [100, 1]
    assert service.last_accepted_recipients == [prepared[-1].context.email]


@pytest.mark.parametrize("kwargs", [
    {"prepared_deliveries": []}, {"prepared_deliveries": ["bad"]},
    {"prepared_deliveries": [], "preview": True},
])
def test_attempt_start_clears_stale_acceptance(kwargs):
    service = EmailService()
    service.last_accepted_recipients = ["stale"]
    try:
        service.send_daily_brief(articles=[], **kwargs)
    except NewsletterDeliveryError:
        pass
    assert service.last_accepted_recipients == []


def test_single_address_preview_endpoint_does_not_lookup_identity(monkeypatch):
    service = EmailService()
    service.resend_enabled = False
    captured = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: captured.append((a, k)) or True)
    monkeypatch.setattr(server, "email_service", service)
    # No subscribers/ledger/cursor collection is provided: any access would fail.
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=Collection([ARTICLE])))
    result = asyncio.run(server.send_digest_test("preview@synthetic.invalid", False))
    assert result["emails_sent"] == 1
    assert captured[0][0][0] == "preview@synthetic.invalid"
    assert captured[0][1] == {} and "#token=" not in str(captured)


@pytest.mark.parametrize("manual", [False, True])
def test_outer_provider_failure_never_exposes_prepared_message(monkeypatch, caplog, manual):
    db = SimpleNamespace(subscribers=Collection([subscriber()]), articles=Collection([ARTICLE]),
                         digest_log=Collection(), email_batch_cursors=Collection(),
                         email_send_opportunities=Collection())
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setenv("HOSTNAME", "offline")
    service = EmailService()
    service.resend_enabled = False
    def fail(*a, **k):
        raise RuntimeError("PRIVATE_TOKEN " + str(k) + str(a))
    monkeypatch.setattr(service, "_send_email", fail)
    monkeypatch.setattr(server, "email_service", service)
    if manual:
        with pytest.raises(server.HTTPException) as error:
            asyncio.run(server.send_digest_now())
        assert error.value.detail == "Daily Brief unavailable"
    else:
        asyncio.run(server.send_scheduled_news_digest())
    persisted = str(db.digest_log.updates) + str(db.digest_log.inserts)
    assert "PRIVATE_TOKEN" not in caplog.text + persisted
    assert "#token=" not in caplog.text + persisted
    assert subscriber()["email"] not in caplog.text + persisted


def test_accepted_snapshot_survives_other_send_during_persistence(monkeypatch):
    db = SimpleNamespace(subscribers=Collection([subscriber()]), articles=Collection([ARTICLE]),
                         digest_log=Collection(), email_batch_cursors=Collection(),
                         email_send_opportunities=Collection())
    service = EmailService()
    service.resend_enabled = False
    original = db.digest_log.update_one
    async def update(query, mutation, **kwargs):
        if mutation.get("$set", {}).get("success_count") == 1:
            service.last_accepted_recipients = []
        return await original(query, mutation, **kwargs)
    db.digest_log.update_one = update
    accepted = []
    async def ledger(kind, tracking, recipients, provider):
        accepted.extend(recipients)
        return len(recipients)
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(server, "_save_email_send_opportunities", ledger)
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: True)
    monkeypatch.setenv("HOSTNAME", "offline")
    asyncio.run(server.send_scheduled_news_digest())
    assert accepted == [subscriber()["email"]]


def test_daily_acceptance_snapshots_precede_first_persistence_await(monkeypatch):
    original_email = subscriber()["email"]
    replacement_email = "replacement@synthetic.invalid"
    original_evidence = {
        "provider_message_id": "provider-original",
        "campaign_id": "campaign-original",
        "newsletter_family": "DailyBrief",
        "recipient_id": "recipient-original",
    }
    db = SimpleNamespace(
        subscribers=Collection([subscriber()]),
        articles=Collection([ARTICLE]),
        digest_log=Collection(),
        email_batch_cursors=Collection(),
        email_send_opportunities=Collection(),
    )
    service = EmailService()
    service.resend_enabled = True
    captured_evidence = []
    captured_ledger = []

    def send(**_kwargs):
        service.last_accepted_recipients = [original_email]
        service.last_resend_acceptances = [original_evidence]
        service.last_provider_contacted = True
        service.resend_last_error = None
        service.resend_last_successful_chunks = 1
        service.resend_last_failed_chunks = 0
        return 1, "campaign-original"

    async def persist_acceptances(
        *, rows=None, run_fields=None, include_completion=False
    ):
        assert include_completion is True
        assert run_fields["digest_time"] == "DailyBrief"
        assert len(run_fields["date_key"]) == 8
        service.last_accepted_recipients = [replacement_email]
        original_evidence["campaign_id"] = "campaign-mutated"
        service.last_resend_acceptances = [{
            **original_evidence,
            "provider_message_id": "provider-replacement",
        }]
        service.last_provider_contacted = False
        service.resend_last_error = "replacement send failed"
        service.resend_last_successful_chunks = 0
        service.resend_last_failed_chunks = 1
        captured_evidence.extend(rows or ())
        return True, len(rows or ())

    async def persist_ledger(_kind, _tracking, recipients, _provider):
        captured_ledger.extend(recipients)
        return len(recipients)

    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(service, "send_daily_brief", send)
    monkeypatch.setattr(server, "_save_last_resend_acceptances", persist_acceptances)
    monkeypatch.setattr(server, "_save_email_send_opportunities", persist_ledger)
    monkeypatch.setenv("HOSTNAME", "offline")

    asyncio.run(server.send_scheduled_news_digest())

    assert captured_evidence == [{
        "provider_message_id": "provider-original",
        "campaign_id": "campaign-original",
        "newsletter_family": "DailyBrief",
        "recipient_id": "recipient-original",
    }]
    assert captured_ledger == [original_email]
    final_fields = {}
    for _query, update in db.digest_log.updates:
        final_fields.update(update.get("$set", {}))
    assert final_fields["success_count"] == 1
    assert final_fields["accepted_count"] == 1
    assert final_fields["provider_contacted"] is True
    assert final_fields["provider_error"] is None
    assert final_fields["resend_successful_chunks"] == 1
    assert final_fields["resend_failed_chunks"] == 0


def test_daily_evidence_checkpoint_distinguishes_attempted_from_inserted(monkeypatch):
    rows = [subscriber(1), subscriber(2)]
    db = SimpleNamespace(
        subscribers=Collection(rows),
        articles=Collection([ARTICLE]),
        digest_log=Collection(),
        email_batch_cursors=Collection(),
        email_send_opportunities=Collection(),
    )
    service = EmailService()
    service.resend_enabled = True
    phases = []
    provider_calls = []

    def send(**_kwargs):
        provider_calls.append(True)
        service.last_accepted_recipients = [row["email"] for row in rows]
        service.last_resend_acceptances = [
            {
                "provider_message_id": f"provider-{index}",
                "campaign_id": "campaign",
                "newsletter_family": "DailyBrief",
                "recipient_id": f"recipient-{index}",
            }
            for index in range(2)
        ]
        service.last_provider_contacted = True
        return 2, "campaign"

    async def persist_acceptances(
        *, rows, run_fields=None, include_completion=False
    ):
        assert include_completion is True
        assert len(rows) == 2
        return True, 1

    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(service, "send_daily_brief", send)
    monkeypatch.setattr(server, "_save_last_resend_acceptances", persist_acceptances)
    monkeypatch.setattr(
        server,
        "log_daily_brief_memory",
        lambda _logger, phase, _started_at, counts=None: phases.append(
            (phase, dict(counts or {}))
        ),
    )
    monkeypatch.setenv("HOSTNAME", "offline")

    asyncio.run(server.send_scheduled_news_digest())

    assert provider_calls == [True]
    phase_counts = dict(phases)
    assert phase_counts["acceptance_evidence_snapshot_completed"] == {
        "acceptance_evidence_count": 2,
        "accepted_recipient_count": 2,
    }
    assert phase_counts["acceptance_evidence_persistence_completed"] == {
        "attempted_evidence_count": 2,
        "inserted_evidence_count": 1,
    }


def test_daily_evidence_partial_persistence_failure_omits_success_phase(monkeypatch):
    rows = [subscriber(1)]
    db = SimpleNamespace(
        subscribers=Collection(rows),
        articles=Collection([ARTICLE]),
        digest_log=Collection(),
        email_batch_cursors=Collection(),
        email_send_opportunities=Collection(),
    )
    service = EmailService()
    service.resend_enabled = True
    phases = []

    def send(**_kwargs):
        service.last_accepted_recipients = [rows[0]["email"]]
        service.last_resend_acceptances = [{
            "provider_message_id": "provider-one",
            "campaign_id": "campaign",
            "newsletter_family": "DailyBrief",
            "recipient_id": "recipient-one",
        }]
        service.last_provider_contacted = True
        return 1, "campaign"

    async def persist_acceptances(
        *, rows, run_fields=None, include_completion=False
    ):
        assert include_completion is True
        return False, None

    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(service, "send_daily_brief", send)
    monkeypatch.setattr(server, "_save_last_resend_acceptances", persist_acceptances)
    monkeypatch.setattr(
        server,
        "log_daily_brief_memory",
        lambda _logger, phase, _started_at, counts=None: phases.append(
            (phase, dict(counts or {}))
        ),
    )
    monkeypatch.setenv("HOSTNAME", "offline")

    asyncio.run(server.send_scheduled_news_digest())

    phase_counts = dict(phases)
    assert "acceptance_evidence_persistence_completed" not in phase_counts
    assert phase_counts["completion_persistence_completed"] == {
        "accepted_count": 1
    }
    assert db.email_send_opportunities.updates
    assert db.email_batch_cursors.updates


def test_scheduled_daily_memory_checkpoints_are_ordered_and_bounded(monkeypatch):
    rows = [subscriber(1, priority_daily_brief=True), subscriber(2)]
    db = SimpleNamespace(
        subscribers=Collection(rows), articles=Collection([ARTICLE]),
        digest_log=Collection(), email_batch_cursors=Collection(),
        email_send_opportunities=Collection(),
    )
    service = EmailService()
    service.resend_enabled = False
    provider_calls = []
    phases = []

    def record(_logger, phase, started_at, counts=None):
        assert started_at == 10.0
        phases.append((phase, dict(counts or {})))

    def smtp(to, *_args, **_kwargs):
        service.last_provider_contacted = True
        provider_calls.append(to)
        return True

    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(
        server, "start_daily_brief_memory_observability", lambda: 10.0, raising=False
    )
    monkeypatch.setattr(server, "log_daily_brief_memory", record, raising=False)
    monkeypatch.setattr(service, "_send_email", smtp)
    monkeypatch.setenv("HOSTNAME", "offline")

    asyncio.run(server.send_scheduled_news_digest())

    assert provider_calls == [row["email"] for row in rows]
    assert [phase for phase, _counts in phases] == [
        "scheduled_start",
        "subscriber_materialisation_completed",
        "candidate_context_preparation_completed",
        "recipient_selection_completed",
        "article_selection_completed",
        "delivery_preparation_completed",
        "provider_returned",
        "acceptance_evidence_snapshot_completed",
        "acceptance_evidence_persistence_completed",
        "digest_result_persistence_completed",
        "send_ledger_persistence_completed",
        "batch_cursor_persistence_completed",
        "completion_persistence_completed",
        "function_returned",
    ]
    assert phases[1][1] == {"subscriber_count": 2}
    assert phases[2][1] == {"candidate_count": 2}
    assert phases[3][1] == {
        "priority_count": 1, "rotating_count": 1, "selected_count": 2,
    }
    assert phases[4][1] == {"article_count": 1}
    assert phases[5][1] == {
        "selected_count": 2, "prepared_count": 2, "skipped_count": 0,
    }
    assert phases[6][1] == {"accepted_count": 2}
    assert phases[7][1] == {
        "acceptance_evidence_count": 0,
        "accepted_recipient_count": 2,
    }
    assert phases[8][1] == {
        "attempted_evidence_count": 0,
        "inserted_evidence_count": 0,
    }
    assert phases[9][1] == {}
    assert phases[10][1] == {
        "accepted_recipient_count": 2,
        "ledger_row_count": 2,
    }
    assert phases[11][1] == {}
    assert phases[12][1] == {"accepted_count": 2}
    final_fields = {}
    for _query, update in db.digest_log.updates:
        final_fields.update(update.get("$set", {}))
    assert final_fields["status"] == "sent"
    assert final_fields["accepted_count"] == 2


@pytest.mark.parametrize("failed_phase", [
    "acceptance_evidence_snapshot_completed",
    "acceptance_evidence_persistence_completed",
    "digest_result_persistence_completed",
    "send_ledger_persistence_completed",
    "batch_cursor_persistence_completed",
])
def test_daily_memory_diagnostic_failure_preserves_delivery_and_completion(
    monkeypatch, failed_phase,
):
    rows = [subscriber(1, priority_daily_brief=True), subscriber(2)]
    db = SimpleNamespace(
        subscribers=Collection(rows), articles=Collection([ARTICLE]),
        digest_log=Collection(), email_batch_cursors=Collection(),
        email_send_opportunities=Collection(),
    )
    service = EmailService()
    service.resend_enabled = False
    provider_calls = []

    observed_phases = []

    def fail_diagnostic(_logger, phase, _started_at, _counts=None):
        observed_phases.append(phase)
        if phase == failed_phase:
            raise RuntimeError("private diagnostic exception")

    def smtp(to, *_args, **_kwargs):
        service.last_provider_contacted = True
        provider_calls.append(to)
        return True

    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(
        server, "start_daily_brief_memory_observability", lambda: 10.0, raising=False
    )
    monkeypatch.setattr(server, "log_daily_brief_memory", fail_diagnostic, raising=False)
    monkeypatch.setattr(service, "_send_email", smtp)
    monkeypatch.setenv("HOSTNAME", "offline")

    asyncio.run(server.send_scheduled_news_digest())

    assert provider_calls == [row["email"] for row in rows]
    final_fields = {}
    for _query, update in db.digest_log.updates:
        final_fields.update(update.get("$set", {}))
    assert final_fields["status"] == "sent"
    assert final_fields["success_count"] == 2
    assert final_fields["accepted_count"] == 2
    assert failed_phase in observed_phases
    assert db.email_send_opportunities.updates
    assert db.email_batch_cursors.updates
