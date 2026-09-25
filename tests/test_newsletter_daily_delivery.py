"""Daily Slice 1: synthetic storage, credentials and providers only."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace
from uuid import UUID
from urllib.parse import parse_qs, urlsplit

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
        return httpx.Response(200, request=httpx.Request("POST", "https://synthetic.invalid"))
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
    if transport == "smtp_disabled":
        service.resend_enabled = False
        service.smtp_enabled = False
    else:
        service.resend_enabled = True
        service.resend_api_key = None
        service.from_email = "sender@synthetic.invalid"

    monkeypatch.setattr(server, "email_service", service)
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
        return httpx.Response(400 if len(calls) == 1 else 200,
                              request=httpx.Request("POST", "https://synthetic.invalid"))
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
