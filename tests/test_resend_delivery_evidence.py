import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException


BACKEND_ROOT = str(Path(__file__).parents[1] / "backend")
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
os.environ.setdefault("MONGO_URL", "mongodb://127.0.0.1:27017")
os.environ.setdefault("DB_NAME", "cheshiretoday_test")

from app import email_service as email_module
from app.resend_delivery_evidence import (
    PROVIDER_EVENT_INDEXES,
    PROVIDER_MESSAGE_INDEXES,
    ResendDeliveryEvidenceRepository,
    aggregate_campaign_delivery,
    normalize_resend_event,
    verify_resend_webhook,
)
from backend import server as app_server


class DuplicateKeyError(Exception):
    pass


class FakeCollection:
    def __init__(self):
        self.rows = []
        self.indexes = []

    async def create_index(self, keys, **options):
        self.indexes.append((tuple(keys), dict(options)))

    async def insert_one(self, document):
        if any(row.get("provider") == document.get("provider") and
               row.get("provider_event_id") == document.get("provider_event_id")
               for row in self.rows):
            from pymongo.errors import DuplicateKeyError as MongoDuplicateKeyError
            raise MongoDuplicateKeyError("duplicate")
        self.rows.append(dict(document))
        return SimpleNamespace(inserted_id=len(self.rows))

    async def find_one(self, query):
        for row in self.rows:
            if self._matches(row, query):
                return dict(row)
        return None

    @staticmethod
    def _matches(row, query):
        for key, expected in query.items():
            actual = row.get(key)
            if isinstance(expected, dict) and "$in" in expected:
                if actual not in expected["$in"]:
                    return False
            elif isinstance(expected, dict) and "$nin" in expected:
                if actual in expected["$nin"]:
                    return False
            elif isinstance(expected, dict) and "$ne" in expected:
                if actual == expected["$ne"]:
                    return False
            elif actual != expected:
                return False
        return True

    async def update_one(self, query, update, upsert=False):
        row = next((item for item in self.rows
                    if self._matches(item, query)), None)
        inserted = False
        if row is None and upsert:
            row = {}
            self.rows.append(row)
            inserted = True
        if row is not None:
            if inserted:
                row.update(update.get("$setOnInsert", {}))
            row.update(update.get("$set", {}))
        return SimpleNamespace(
            matched_count=int(row is not None and not inserted),
            modified_count=int(row is not None),
            upserted_id=(len(self.rows) if inserted else None),
        )

    def find(self, query):
        rows = [dict(row) for row in self.rows
                if self._matches(row, query)]
        return FakeCursor(rows)


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    async def to_list(self, _limit):
        return list(self.rows)


def accepted_message(index=1):
    return {
        "to": f"reader{index}@synthetic.invalid",
        "subject": "Synthetic",
        "html": "<p>Body</p>",
        "evidence": {
            "campaign_id": "daily_brief_2026-10-06T07:30:00Z_abcd",
            "newsletter_family": "DailyBrief",
            "recipient_id": f"00000000-0000-4000-8000-{index:012d}",
        },
    }


def resend_response(ids, status=200):
    return httpx.Response(
        status,
        json={"data": [{"id": value} for value in ids]},
        request=httpx.Request("POST", "https://api.resend.com/emails/batch"),
    )


def configured_service():
    service = email_module.EmailService()
    service.resend_enabled = True
    service.resend_api_key = "synthetic-key"
    service.resend_from_email = "news@synthetic.invalid"
    service.last_accepted_recipients = []
    service.last_resend_acceptances = []
    service.resend_last_successful_chunks = 0
    service.resend_last_failed_chunks = 0
    return service


def test_batch_response_ids_follow_documented_request_order(monkeypatch):
    service = configured_service()
    messages = [accepted_message(1), accepted_message(2)]
    captured = []

    def post(_url, *, headers, json, timeout):
        captured.extend(json)
        return resend_response(["email-one", "email-two"])

    monkeypatch.setattr(email_module.httpx, "post", post)
    assert service._send_resend_batch(messages) == 2
    assert [row["provider_message_id"] for row in service.last_resend_acceptances] == [
        "email-one", "email-two"
    ]
    assert [row["recipient_id"] for row in service.last_resend_acceptances] == [
        messages[0]["evidence"]["recipient_id"], messages[1]["evidence"]["recipient_id"]
    ]
    assert all("evidence" not in payload for payload in captured)


@pytest.mark.parametrize("body", [
    {}, {"data": []}, {"data": [{"id": "only-one"}]},
    {"data": [{"id": "one"}, {"id": "two"}, {"id": "three"}]},
    {"data": [{"id": "one"}, {"unexpected": "two"}]},
    {"data": [{"id": "duplicate"}, {"id": "duplicate"}]},
])
def test_malformed_batch_success_is_ambiguous_not_accepted(monkeypatch, body):
    service = configured_service()
    monkeypatch.setattr(
        email_module.httpx,
        "post",
        lambda *_a, **_k: httpx.Response(
            200, json=body,
            request=httpx.Request("POST", "https://api.resend.com/emails/batch"),
        ),
    )
    assert service._send_resend_batch([accepted_message(1), accepted_message(2)]) == 0
    assert service.last_resend_acceptances == []
    assert service.last_accepted_recipients == []
    assert service.last_provider_contacted is True


def event(event_type="email.delivered", message_id="email-one", *, created_at=None):
    return {
        "type": event_type,
        "created_at": created_at or "2026-10-06T08:00:00.000Z",
        "data": {
            "email_id": message_id,
            "to": ["private@example.invalid"],
            "subject": "Must not persist",
            "bounce": {"type": "Permanent", "subType": "General", "message": "private detail"},
        },
    }


@pytest.mark.parametrize("event_type", [
    "email.sent", "email.delivered", "email.delivery_delayed",
    "email.failed", "email.bounced", "email.complained",
])
def test_supported_events_normalize_without_raw_recipient(event_type):
    normalized = normalize_resend_event(event(event_type), "msg_event_1")
    assert normalized["provider_event_id"] == "msg_event_1"
    assert normalized["provider_message_id"] == "email-one"
    assert normalized["event_type"] == event_type
    assert "to" not in normalized
    assert "subject" not in normalized
    assert "payload" not in normalized
    if event_type == "email.bounced":
        assert normalized["bounce_type"] == "Permanent"
        assert normalized["bounce_subtype"] == "General"
        assert "message" not in normalized


def test_unsupported_and_malformed_events_are_bounded():
    assert normalize_resend_event(event("email.opened"), "msg_open") is None
    with pytest.raises(ValueError, match="invalid_resend_event"):
        normalize_resend_event({"type": "email.delivered", "data": {}}, "msg_bad")


def repository():
    messages = FakeCollection()
    events = FakeCollection()
    messages.rows.append({
        "provider": "resend",
        "provider_message_id": "email-one",
        "campaign_id": "campaign-one",
        "newsletter_family": "DailyBrief",
        "recipient_id": "00000000-0000-4000-8000-000000000001",
        "accepted_at": datetime(2026, 10, 6, 7, 30, tzinfo=timezone.utc),
        "delivery_state": "accepted",
        "complained": False,
    })
    return ResendDeliveryEvidenceRepository(messages, events), messages, events


def test_acceptance_storage_is_immutable_and_contains_no_plaintext_email():
    repo = ResendDeliveryEvidenceRepository(FakeCollection(), FakeCollection())
    row = {
        "provider_message_id": "email-one",
        "campaign_id": "campaign-one",
        "newsletter_family": "DailyBrief",
        "recipient_id": "00000000-0000-4000-8000-000000000001",
        "email": "must-not-persist@example.invalid",
    }
    assert asyncio.run(repo.save_acceptances([row], run_fields={"date_key": "2026-10-06"})) == 1
    assert asyncio.run(repo.save_acceptances([{**row, "campaign_id": "wrong-campaign"}])) == 0
    stored = repo.messages.rows[0]
    assert stored["campaign_id"] == "campaign-one"
    assert stored["date_key"] == "2026-10-06"
    assert "email" not in stored


def test_event_idempotency_correlation_and_unknown_message_isolation():
    repo, messages, events = repository()
    normalized = normalize_resend_event(event(), "msg_same")
    first = asyncio.run(repo.record_event(normalized))
    second = asyncio.run(repo.record_event(normalized))
    assert first == "recorded"
    assert second == "duplicate"
    assert len(events.rows) == 1
    assert events.rows[0]["campaign_id"] == "campaign-one"
    assert messages.rows[0]["delivery_state"] == "delivered"

    unknown = normalize_resend_event(event(message_id="unknown"), "msg_unknown")
    assert asyncio.run(repo.record_event(unknown)) == "uncorrelated"
    assert events.rows[-1]["correlated"] is False
    assert events.rows[-1].get("campaign_id") is None
    assert messages.rows[0]["provider_message_id"] == "email-one"


def test_event_arriving_before_acceptance_is_reconciled_without_retry():
    repo = ResendDeliveryEvidenceRepository(FakeCollection(), FakeCollection())
    normalized = normalize_resend_event(event(), "msg_early")
    assert asyncio.run(repo.record_event(normalized)) == "uncorrelated"
    assert repo.events.rows[0]["correlated"] is False

    row = {
        "provider_message_id": "email-one",
        "campaign_id": "campaign-one",
        "newsletter_family": "DailyBrief",
        "recipient_id": "00000000-0000-4000-8000-000000000001",
    }
    assert asyncio.run(repo.save_acceptances([row])) == 1
    assert repo.events.rows[0]["correlated"] is True
    assert repo.events.rows[0]["campaign_id"] == "campaign-one"
    assert repo.messages.rows[0]["delivery_state"] == "delivered"


def test_out_of_order_state_does_not_regress_and_complaint_is_retained():
    repo, messages, events = repository()
    for index, kind in enumerate((
        "email.delivery_delayed", "email.delivered", "email.delivery_delayed",
        "email.complained", "email.bounced",
    )):
        assert asyncio.run(repo.record_event(
            normalize_resend_event(event(kind), f"msg_{index}")
        )) == "recorded"
    assert messages.rows[0]["delivery_state"] == "bounced"
    assert messages.rows[0]["complained"] is True
    assert len(events.rows) == 5


def test_bounce_is_not_downgraded_by_late_delivery():
    repo, messages, _events = repository()
    for index, kind in enumerate(("email.bounced", "email.delivered")):
        assert asyncio.run(repo.record_event(
            normalize_resend_event(event(kind), f"msg_terminal_{index}")
        )) == "recorded"
    assert messages.rows[0]["delivery_state"] == "bounced"


def test_failed_is_terminal_but_does_not_override_confirmed_delivery():
    repo, messages, _events = repository()
    assert asyncio.run(repo.record_event(
        normalize_resend_event(event("email.failed"), "msg_failed")
    )) == "recorded"
    assert messages.rows[0]["delivery_state"] == "failed"
    assert asyncio.run(repo.record_event(
        normalize_resend_event(event("email.delivered"), "msg_late_delivery")
    )) == "recorded"
    assert messages.rows[0]["delivery_state"] == "failed"

    repo2, messages2, _events2 = repository()
    assert asyncio.run(repo2.record_event(
        normalize_resend_event(event("email.delivered"), "msg_delivered_first")
    )) == "recorded"
    assert asyncio.run(repo2.record_event(
        normalize_resend_event(event("email.failed"), "msg_late_failure")
    )) == "recorded"
    assert messages2.rows[0]["delivery_state"] == "delivered"


def test_campaign_aggregation_uses_accepted_denominator():
    repo, messages, events = repository()
    messages.rows.extend([
        {"provider": "resend", "provider_message_id": "email-two",
         "campaign_id": "campaign-one", "delivery_state": "delayed", "complained": False},
        {"provider": "resend", "provider_message_id": "email-three",
         "campaign_id": "campaign-one", "delivery_state": "accepted", "complained": True},
    ])
    result = asyncio.run(aggregate_campaign_delivery(messages, "campaign-one"))
    assert result == {
        "campaign_id": "campaign-one", "accepted": 3, "delivered": 0,
        "delayed": 1, "bounced": 0, "failed": 0, "complained": 1,
        "complaint_rate": pytest.approx(1 / 3),
        "complaint_rate_denominator": "accepted",
    }


def test_index_contracts_are_minimal_and_unique():
    assert ("provider", "provider_message_id") in [tuple(key for key, _ in i.keys) for i in PROVIDER_MESSAGE_INDEXES]
    assert any(i.unique for i in PROVIDER_MESSAGE_INDEXES)
    assert ("provider", "provider_event_id") in [tuple(key for key, _ in i.keys) for i in PROVIDER_EVENT_INDEXES]
    assert any(i.unique for i in PROVIDER_EVENT_INDEXES)


def test_webhook_verification_requires_secret_and_exact_raw_body(monkeypatch):
    raw = b'{"type":"email.delivered","data":{"email_id":"email-one"}}'
    seen = {}

    class Verifier:
        def __init__(self, secret):
            seen["secret"] = secret

        def verify(self, payload, headers):
            seen["payload"] = payload
            seen["headers"] = headers

    headers = {"svix-id": "msg_one", "svix-timestamp": "1", "svix-signature": "v1,test"}
    assert verify_resend_webhook(raw, headers, "whsec_test", verifier_factory=Verifier) == json.loads(raw)
    assert seen["payload"] == raw
    assert seen["headers"] == headers
    with pytest.raises(ValueError, match="webhook_not_configured"):
        verify_resend_webhook(raw, headers, "", verifier_factory=Verifier)
    with pytest.raises(ValueError, match="invalid_webhook_signature"):
        verify_resend_webhook(raw, {}, "whsec_test", verifier_factory=Verifier)


def signed_headers(secret, raw, *, timestamp=None, message_id="msg_signed"):
    from svix.webhooks import Webhook

    timestamp = timestamp or datetime.now(timezone.utc)
    return {
        "svix-id": message_id,
        "svix-timestamp": str(int(timestamp.timestamp())),
        "svix-signature": Webhook(secret).sign(message_id, timestamp, raw.decode()),
    }


def test_real_svix_verifier_accepts_fresh_and_rejects_stale_or_tampered_body():
    secret = "whsec_dGVzdC13ZWJob29rLXNlY3JldA=="
    raw = json.dumps(event(), separators=(",", ":")).encode()
    fresh = signed_headers(secret, raw)
    assert verify_resend_webhook(raw, fresh, secret)["type"] == "email.delivered"
    with pytest.raises(ValueError, match="invalid_webhook_signature"):
        verify_resend_webhook(raw + b" ", fresh, secret)
    stale = signed_headers(
        secret, raw, timestamp=datetime.now(timezone.utc) - timedelta(minutes=6),
        message_id="msg_stale",
    )
    with pytest.raises(ValueError, match="invalid_webhook_signature"):
        verify_resend_webhook(raw, stale, secret)


def test_signed_malformed_json_is_rejected_after_signature_verification():
    secret = "whsec_dGVzdC13ZWJob29rLXNlY3JldA=="
    raw = b"not-json"
    with pytest.raises(ValueError, match="malformed_webhook_payload"):
        verify_resend_webhook(raw, signed_headers(secret, raw), secret)


class FakeRequest:
    def __init__(self, raw, headers):
        self._raw = raw
        self.headers = headers

    async def stream(self):
        yield self._raw


def test_webhook_route_fails_closed_without_secret(monkeypatch):
    monkeypatch.delenv("RESEND_WEBHOOK_SECRET", raising=False)
    with pytest.raises(HTTPException) as caught:
        asyncio.run(app_server.receive_resend_webhook(FakeRequest(b"{}", {})))
    assert caught.value.status_code == 503
    assert caught.value.detail == "Webhook unavailable"


def test_webhook_route_verifies_and_persists_bounded_event(monkeypatch, caplog):
    secret = "whsec_dGVzdC13ZWJob29rLXNlY3JldA=="
    raw = json.dumps(event(), separators=(",", ":")).encode()
    headers = signed_headers(secret, raw, message_id="msg_route")
    recorded = []

    class Repository:
        async def record_event(self, normalized):
            recorded.append(normalized)
            return "recorded"

    monkeypatch.setenv("RESEND_WEBHOOK_SECRET", secret)
    monkeypatch.setattr(
        app_server, "_resend_delivery_evidence_repository", lambda: Repository()
    )
    response = asyncio.run(
        app_server.receive_resend_webhook(FakeRequest(raw, headers))
    )
    assert response.status_code == 204
    assert recorded[0]["provider_event_id"] == "msg_route"
    assert recorded[0]["provider_message_id"] == "email-one"
    assert "to" not in recorded[0] and "payload" not in recorded[0]
    assert "private@example.invalid" not in caplog.text


def test_webhook_route_rejects_invalid_signature_and_malformed_json(monkeypatch):
    secret = "whsec_dGVzdC13ZWJob29rLXNlY3JldA=="
    monkeypatch.setenv("RESEND_WEBHOOK_SECRET", secret)
    valid_raw = json.dumps(event(), separators=(",", ":")).encode()
    bad_signature = signed_headers(secret, valid_raw)
    for raw, headers in (
        (valid_raw + b" ", bad_signature),
        (b"not-json", signed_headers(secret, b"not-json", message_id="msg_bad_json")),
    ):
        with pytest.raises(HTTPException) as caught:
            asyncio.run(app_server.receive_resend_webhook(FakeRequest(raw, headers)))
        assert caught.value.status_code == 400
        assert caught.value.detail == "Invalid webhook"


def test_webhook_route_rejects_oversized_body_before_verification(monkeypatch):
    monkeypatch.setenv("RESEND_WEBHOOK_SECRET", "whsec_test")
    request = FakeRequest(b"x" * (256 * 1024 + 1), {})
    with pytest.raises(HTTPException) as caught:
        asyncio.run(app_server.receive_resend_webhook(request))
    assert caught.value.status_code == 413
    assert caught.value.detail == "Webhook payload too large"
