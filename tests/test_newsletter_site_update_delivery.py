"""Slice 5: synthetic Site Update transports, audiences and onboarding state."""
import asyncio
import ast
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email import message_from_string
import smtplib
import subprocess
from types import SimpleNamespace

import httpx
import pytest

from backend import server
from app.email_service import EmailService
from app.newsletter_delivery import (
    NewsletterDeliveryError, PreparedNewsletterDelivery, RecipientDeliveryContext,
    prepare_direct_delivery,
)
from app.newsletter_token_service import NewsletterTokenService
from tests.test_newsletter_daily_delivery import subscriber, deliveries, TOKEN_SERVICE, check_message


ACTIVE = {"$or": [{"active": True}, {"active": {"$exists": False}}]}
IDENTITY_FIELDS = {"_id", "email", "active", "newsletter_management_id", "newsletter_token_version"}
SUBJECTS = {1: "Cheshire Today is evolving — here’s what it means for you", 2: "What’s new on Cheshire Today"}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Real transport forbidden")
    monkeypatch.setattr("app.email_service.httpx.post", forbidden)
    monkeypatch.setattr("app.email_service.smtplib.SMTP", forbidden)
    monkeypatch.setattr("app.email_service.smtplib.SMTP_SSL", forbidden)
    monkeypatch.setattr(server, "newsletter_token_service_from_environment", lambda: TOKEN_SERVICE)
    monkeypatch.setenv("ENABLE_ONBOARDING_AUTOMATION", "1")


def sender(service, part):
    return getattr(service, f"send_site_update_part{part}")


@pytest.mark.parametrize("part", [1, 2])
@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("outcome", ["all", "partial", "zero", "unavailable"])
def test_transport_isolation(monkeypatch, part, resend, outcome):
    service = EmailService()
    service.resend_enabled = resend
    service.smtp_enabled = False
    service.resend_api_key = None if outcome == "unavailable" else "synthetic"
    service.from_email = "sender@synthetic.invalid"
    messages, chunks = [], []
    def post(url, *, json, **kwargs):
        chunks.append(len(json))
        messages.extend([{**m, "to": m["to"][0]} for m in json])
        ok = outcome == "all" or outcome == "partial" and len(chunks) == 2
        return httpx.Response(200 if ok else 400, request=httpx.Request("POST", "https://synthetic.invalid"))
    def smtp(to, subject, html, text, *, newsletter_headers):
        service.last_provider_contacted = True
        messages.append({"to": to, "subject": subject, "html": html, "text": text, "headers": newsletter_headers})
        return outcome == "all" or outcome == "partial" and len(messages) == 101
    monkeypatch.setattr("app.email_service.httpx.post", post)
    if outcome != "unavailable":
        monkeypatch.setattr(service, "_send_email", smtp)
    prepared = deliveries(101)
    service.last_accepted_recipients = ["stale"]
    service.last_provider_contacted = True
    service.resend_last_error = "stale"
    service.resend_last_successful_chunks = service.resend_last_failed_chunks = 99
    count = sender(service, part)(prepared_deliveries=prepared, token_service=TOKEN_SERVICE)
    expected = 101 if outcome == "all" else 1 if outcome == "partial" else 0
    assert type(count) is int and count == expected
    assert service.last_provider_contacted is (outcome != "unavailable")
    assert service.last_accepted_recipients == ([a.context.email for a in prepared] if expected == 101 else
                                              [prepared[-1].context.email] if expected == 1 else [])
    if resend and outcome != "unavailable":
        assert chunks == [100, 1]
        assert service.resend_last_successful_chunks == (2 if outcome == "all" else 1 if outcome == "partial" else 0)
        assert service.resend_last_failed_chunks == (0 if outcome == "all" else 1 if outcome == "partial" else 2)
    for message, artifact in zip(messages, prepared):
        check_message(message, artifact)
        assert message["to"] == artifact.context.email
        assert message["subject"] == SUBJECTS[part]
        assert f'href="{artifact.human_unsubscribe_url}"' in message["html"]
        assert "/email/track/open/SiteUpdatePart" + str(part) in message["html"]
        assert "/email/track/click/" not in message["html"]
        assert "https://cheshiretoday.co.uk/newsletter/preferences" in message["html"]
        content = "Stronger focus on Cheshire business" if part == 1 else "reply to this email"
        assert content in message["html"] and content in message["text"]
        for other in prepared:
            if other is not artifact:
                assert other.human_unsubscribe_url not in message["html"]


@pytest.mark.parametrize("part", [1, 2])
@pytest.mark.parametrize("port", [465, 587])
def test_real_smtp_helper_mime_and_partial_acceptance(monkeypatch, part, port):
    service = EmailService()
    service.resend_enabled = False
    service.smtp_enabled = True
    service.smtp_host, service.smtp_port = "smtp.synthetic.invalid", port
    service.smtp_user, service.smtp_password = "synthetic", "synthetic"
    service.from_email = "sender@synthetic.invalid"
    messages = []
    class SMTP:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def ehlo(self): pass
        def starttls(self, **kwargs): pass
        def login(self, *args): pass
        def sendmail(self, from_email, to, content):
            msg = message_from_string(content)
            body = {p.get_content_type(): p.get_payload(decode=True).decode() for p in msg.get_payload()}
            messages.append({"to": to, "html": body["text/html"], "text": body["text/plain"],
                             "headers": dict(msg.items())})
            assert msg["To"] == to
            if len(messages) == 1: raise smtplib.SMTPRecipientsRefused({to: (550, b"synthetic rejection")})
    monkeypatch.setattr("app.email_service.smtplib.SMTP", SMTP)
    monkeypatch.setattr("app.email_service.smtplib.SMTP_SSL", SMTP)
    prepared = deliveries(2)
    assert sender(service, part)(prepared_deliveries=prepared, token_service=TOKEN_SERVICE) == 1
    assert service.last_provider_contacted and service.last_accepted_recipients == [prepared[1].context.email]
    for message, artifact in zip(messages, prepared): check_message(message, artifact)


@pytest.mark.parametrize("part", [1, 2])
@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("kind", ["swap", "human", "native", "malformed", "forged", "uuid", "version", "headers"])
def test_complete_batch_rejected_before_rendering(monkeypatch, part, resend, kind):
    a, b = deliveries(2)
    broken = object.__new__(PreparedNewsletterDelivery)
    for key, value in [("context", a.context), ("human_unsubscribe_url", a.human_unsubscribe_url),
                       ("native_headers", {**dict(a.native_headers), "Unexpected": "header"})]:
        object.__setattr__(broken, key, value)
    bad = {
        "swap": PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, b.native_headers),
        "human": PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, a.native_headers),
        "native": PreparedNewsletterDelivery(a.context, a.human_unsubscribe_url, b.native_headers),
        "malformed": PreparedNewsletterDelivery(a.context, a.human_unsubscribe_url + "&token=x", a.native_headers),
        "forged": prepare_direct_delivery(a.context, NewsletterTokenService("E" * 43)),
        "uuid": PreparedNewsletterDelivery(b.context, a.human_unsubscribe_url, a.native_headers),
        "version": PreparedNewsletterDelivery(RecipientDeliveryContext(a.context.email,
            a.context.newsletter_management_id, 2), a.human_unsubscribe_url, a.native_headers),
        "headers": broken,
    }[kind]
    service = EmailService()
    service.resend_enabled = resend
    calls = []
    for method in ["_generate_tracking_id", "_get_tracking_pixel", "_send_email", "_send_resend_batch"]:
        monkeypatch.setattr(service, method, lambda *a, **k: calls.append(1))
    with pytest.raises(NewsletterDeliveryError, match="^invalid_prepared_delivery$"):
        sender(service, part)(prepared_deliveries=[a, bad, b], token_service=TOKEN_SERVICE)
    assert not calls and not service.last_provider_contacted and not service.last_accepted_recipients


@pytest.mark.parametrize("part", [1, 2])
@pytest.mark.parametrize("kwargs", [{}, {"to_emails": []}, {"to_emails": ["raw@synthetic.invalid"]},
    {"prepared_deliveries": deliveries(1)},
    {"prepared_deliveries": deliveries(1), "to_emails": ["raw@synthetic.invalid"], "token_service": TOKEN_SERVICE}])
def test_prepared_only_contract(part, kwargs):
    service = EmailService()
    service.last_provider_contacted, service.last_accepted_recipients = True, ["stale"]
    with pytest.raises(NewsletterDeliveryError): sender(service, part)(**kwargs)
    assert not service.last_provider_contacted and not service.last_accepted_recipients


@pytest.mark.parametrize("part", [1, 2])
def test_empty_delivery_resets_state_without_rendering(monkeypatch, part):
    service = EmailService()
    service.last_provider_contacted, service.last_accepted_recipients = True, ["stale"]
    service.resend_last_error = "stale"
    service.resend_last_successful_chunks = service.resend_last_failed_chunks = 99
    monkeypatch.setattr(service, "_generate_tracking_id", lambda *a: pytest.fail("Rendered empty send"))
    assert sender(service, part)(prepared_deliveries=[]) == 0
    assert not service.last_provider_contacted and not service.last_accepted_recipients
    assert service.resend_last_error is None
    assert service.resend_last_successful_chunks == service.resend_last_failed_chunks == 0


class Subscribers:
    def __init__(self, rows, events, service):
        self.rows, self.events, self.service = deepcopy(rows), events, service
        self.queries, self.updates, self.limits = [], [], []
    def find(self, query, projection):
        self.queries.append((query, projection))
        assert query in (ACTIVE, {})
        expected = IDENTITY_FIELDS | ({"created_at", "subscribed_at", "site_update_part1_sent_at", "site_update_part2_sent_at"} if not query else set())
        assert set(projection) == expected
        # Mongo scalar booleans do not equal numeric 1; missing alone passes $exists:false.
        rows = [r for r in self.rows if not query or "active" not in r or r["active"] is True
                or isinstance(r["active"], list) and any(value is True for value in r["active"])]
        collection = self
        class Cursor:
            async def to_list(self, limit):
                collection.limits.append(limit)
                return [{k: deepcopy(v) for k, v in r.items() if projection.get(k)} for r in rows[:limit]]
        return Cursor()
    async def update_many(self, query, update):
        self.events.append("mark")
        self.updates.append((deepcopy(query), deepcopy(update)))
        assert "created_at" not in update["$set"]
        assert len(update["$set"]) == 1
        for row in self.rows:
            if row.get("email") in query["email"]["$in"]: row.update(update["$set"])
        # Simulate another attempt modifying shared diagnostics during an await.
        self.service.last_accepted_recipients.clear()
        self.service.last_provider_contacted = False


def setup(monkeypatch, rows, accepted=(), unavailable=False):
    service = EmailService()
    service.resend_enabled, service.smtp_enabled = False, False
    events, calls, inserts, flags = [], [], [], []
    def smtp(to, subject, *args, **kwargs):
        service.last_provider_contacted = True
        part = 1 if subject == SUBJECTS[1] else 2
        calls.append((part, to))
        return (part, to) in accepted
    if not unavailable: monkeypatch.setattr(service, "_send_email", smtp)
    for part in (1, 2):
        original = sender(service, part)
        def wrapped(*, _original=original, **kwargs):
            result = _original(**kwargs)
            events.append("send")
            return result
        monkeypatch.setattr(service, f"send_site_update_part{part}", wrapped)
    async def insert(record):
        events.append("digest")
        inserts.append(record)
        service.last_accepted_recipients.clear()
        service.last_provider_contacted = False
    async def flag(query, update, *, upsert):
        events.append("flag")
        flags.append((query, update, upsert))
    db = SimpleNamespace(subscribers=Subscribers(rows, events, service),
                         digest_log=SimpleNamespace(insert_one=insert),
                         system_flags=SimpleNamespace(update_one=flag))
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    return SimpleNamespace(db=db, service=service, events=events, calls=calls, logs=inserts, flags=flags)


def manual(part):
    return asyncio.run(getattr(server, f"send_site_update_part{part}")())


def assert_aggregate(record, selected, prepared, accepted, contacted):
    assert record["selected_count"] == record["subscribers_count"] == selected
    assert record["prepared_count"] == prepared
    assert record["skipped_count"] == sum(record["skip_reasons"].values()) == selected - prepared
    assert record["accepted_count"] == record["success_count"] == accepted
    assert record["provider_contacted"] is contacted
    assert "synthetic.invalid" not in str(record) and "token=" not in str(record)
    assert "newsletter_management_id" not in record and "newsletter_token_version" not in record


@pytest.mark.parametrize("part", [1, 2])
@pytest.mark.parametrize("outcome", ["all", "partial", "zero", "unavailable"])
def test_manual_query_cap_slots_and_global_flags(monkeypatch, part, outcome):
    rows = [subscriber(i) for i in range(1, 10002)]
    for row in rows[2:10000]: row.pop("newsletter_management_id")
    rows[2].pop("active")
    excluded = [subscriber(20000 + i, active=state) for i, state in enumerate([False, None, 1, "true"])]
    count = 2 if outcome == "all" else 1 if outcome == "partial" else 0
    state = setup(monkeypatch, excluded + rows, [(part, r["email"]) for r in rows[:count]], outcome == "unavailable")
    result = manual(part)
    assert state.db.subscribers.limits == [10000]
    assert state.db.subscribers.queries[0][0] == ACTIVE
    assert state.calls == ([(part, r["email"]) for r in rows[:2]] if outcome != "unavailable" else [])
    assert result["subscribers_targeted"] == 10000
    assert state.events == ["send", "digest", "flag"] and not state.db.subscribers.updates
    record = state.logs[0]
    assert_aggregate(record, 10000, 2, count, outcome != "unavailable")
    assert record["digest_time"] == record["type"] == f"SiteUpdatePart{part}"
    assert record["date_key"] == record["sent_at"].strftime("%Y-%m-%d")
    key = f"site_update_part{part}_sent_global"
    query, update, upsert = state.flags[0]
    assert query == {"key": key} and upsert is True
    assert update["$set"] == {"key": key, "value": True, "sent_at": update["$set"]["sent_at"]}


@pytest.mark.parametrize("part", [1, 2])
@pytest.mark.parametrize("invalid", ["missing_email", None, "", 123, "missing_active", "array_active", "bad_id", "bad_version"])
def test_manual_invalid_fetched_position(monkeypatch, part, invalid):
    row = subscriber()
    if invalid == "missing_email": row.pop("email")
    elif invalid == "missing_active": row.pop("active")
    elif invalid == "array_active": row["active"] = [True]
    elif invalid == "bad_id": row["newsletter_management_id"] = "bad"
    elif invalid == "bad_version": row["newsletter_token_version"] = True
    else: row["email"] = invalid
    state = setup(monkeypatch, [row])
    assert manual(part)["subscribers_targeted"] == 1
    assert_aggregate(state.logs[0], 1, 0, 0, False)
    if invalid in ("missing_active", "array_active"):
        assert state.logs[0]["skip_reasons"] == {"invalid_active_state": 1}
    assert not state.calls


@pytest.mark.parametrize("part", [1, 2])
def test_manual_empty_audience_has_no_mutations(monkeypatch, part):
    state = setup(monkeypatch, [subscriber(active=False)])
    assert manual(part) == {"success": False, "message": "No subscribers found"}
    assert not state.events and not state.calls


def aged(index=1, days=8, **changes):
    return subscriber(index, subscribed_at=(datetime.now(timezone.utc) - timedelta(days=days)).isoformat(), **changes)


def onboard(dry_run=0):
    return asyncio.run(server.admin_run_onboarding_emails(dry_run=dry_run))


def test_onboarding_gate_and_dry_run_eligibility(monkeypatch):
    rows = [aged(1, 4, email="Z@synthetic.invalid"), aged(2, 8, email="a@synthetic.invalid"),
            aged(3, 8, email="A@synthetic.invalid"), aged(4, 1), aged(5, active=False),
            aged(6, site_update_part1_sent_at="already"), aged(7, site_update_part2_sent_at="already"),
            subscriber(8), aged(9, created_at="invalid"), aged(10, created_at=datetime.now(timezone.utc).isoformat())]
    state = setup(monkeypatch, rows)
    monkeypatch.delenv("ENABLE_ONBOARDING_AUTOMATION")
    with pytest.raises(server.HTTPException) as exc: onboard()
    assert exc.value.status_code == 404 and not state.db.subscribers.queries
    monkeypatch.setenv("ENABLE_ONBOARDING_AUTOMATION", "1")
    monkeypatch.setattr(server, "_newsletter_candidate_contexts", lambda *a: pytest.fail("Dry-run identity preparation"))
    result = onboard(1)
    assert result["sample_part1"] == ["a@synthetic.invalid", "reader7@synthetic.invalid", "reader9@synthetic.invalid", "z@synthetic.invalid"]
    assert result["sample_part2"] == ["a@synthetic.invalid", "reader6@synthetic.invalid", "reader9@synthetic.invalid"]
    assert result["due_part1_count"] == 4 and result["due_part2_count"] == 3
    assert state.db.subscribers.limits == [20000]
    assert not state.events and not state.calls and not state.db.subscribers.updates


@pytest.mark.parametrize("outcome", ["all", "partial", "zero", "unavailable"])
def test_onboarding_marks_only_accepted_and_snapshots_before_await(monkeypatch, outcome):
    rows = [aged(1, email="Reader1@synthetic.invalid"), aged(2)]
    # Reverse which recipient each part accepts to expose cross-part contamination.
    accepted = [(1, "reader1@synthetic.invalid"), (2, "reader2@synthetic.invalid")]
    if outcome == "all": accepted += [(1, "reader2@synthetic.invalid"), (2, "reader1@synthetic.invalid")]
    if outcome in ("zero", "unavailable"): accepted = []
    state = setup(monkeypatch, rows, accepted, outcome == "unavailable")
    result = onboard()
    count = 2 if outcome == "all" else 1 if outcome == "partial" else 0
    assert result["sent_part1"] == result["sent_part2"] == count
    for part, record in enumerate(state.logs, 1):
        assert_aggregate(record, 2, 2, count, outcome != "unavailable")
        assert record["digest_time"] == "AutoOnboarding" and record["type"] == f"SiteUpdatePart{part}Auto"
        for row in state.db.subscribers.rows:
            assert (f"site_update_part{part}_sent_at" in row) is ((part, row["email"].lower()) in accepted)
            assert "created_at" not in row
    assert state.events == (["send", "mark", "digest"] * 2 if count else ["send", "digest"] * 2)
    assert len(state.db.subscribers.updates) == (2 if count else 0)
    assert not state.flags


def test_onboarding_live_order_independent_due_and_no_created_at_rewrite(monkeypatch):
    rows = [aged(3, 4, created_at=(datetime.now(timezone.utc) - timedelta(days=4)).isoformat()),
            aged(2, site_update_part1_sent_at="already"), aged(1, site_update_part2_sent_at="already")]
    state = setup(monkeypatch, rows, [(1, "reader1@synthetic.invalid"), (1, "reader3@synthetic.invalid"),
                                    (2, "reader2@synthetic.invalid")])
    result = onboard()
    assert (result["sent_part1"], result["sent_part2"]) == (2, 1)
    assert state.calls == [(1, "reader1@synthetic.invalid"), (1, "reader3@synthetic.invalid"),
                           (2, "reader2@synthetic.invalid")]
    for before, after in zip(rows, state.db.subscribers.rows):
        assert after.get("created_at") == before.get("created_at")
        assert after["subscribed_at"] == before["subscribed_at"]


@pytest.mark.parametrize("path", [1, 2, "onboarding"])
@pytest.mark.parametrize("outcome", ["all", "partial", "zero", "unavailable"])
def test_endpoint_resend_accounting(monkeypatch, path, outcome):
    rows = [aged(i) for i in range(1, 102)]
    state = setup(monkeypatch, rows)
    state.service.resend_enabled = True
    state.service.resend_api_key = None if outcome == "unavailable" else "synthetic"
    state.service.from_email = "sender@synthetic.invalid"
    accepted_by_part = {1: [], 2: []}
    chunks = {1: [], 2: []}
    def post(url, *, json, **kwargs):
        part = 1 if json[0]["subject"] == SUBJECTS[1] else 2
        chunks[part].append(len(json))
        ok = outcome == "all" or outcome == "partial" and len(chunks[part]) == 2
        if ok: accepted_by_part[part].extend(m["to"][0] for m in json)
        return httpx.Response(200 if ok else 400, request=httpx.Request("POST", "https://synthetic.invalid"))
    monkeypatch.setattr("app.email_service.httpx.post", post)
    onboard() if path == "onboarding" else manual(path)
    expected = 101 if outcome == "all" else 1 if outcome == "partial" else 0
    for record in state.logs: assert_aggregate(record, 101, 101, expected, outcome != "unavailable")
    for part in ([1, 2] if path == "onboarding" else [path]):
        assert chunks[part] == ([] if outcome == "unavailable" else [100, 1])
        if path == "onboarding":
            marked = [r["email"] for r in state.db.subscribers.rows if f"site_update_part{part}_sent_at" in r]
            assert set(marked) == set(accepted_by_part[part])
    assert not state.calls


@pytest.mark.parametrize("invalid", ["missing_active", None, "true", 1, "bad_id", "bad_version"])
def test_onboarding_invalid_selected_states_and_identity(monkeypatch, invalid):
    row = aged()
    if invalid == "missing_active": row.pop("active")
    elif invalid == "bad_id": row["newsletter_management_id"] = "bad"
    elif invalid == "bad_version": row.pop("newsletter_token_version")
    else: row["active"] = invalid
    state = setup(monkeypatch, [row, aged(2, active=False), aged(3)], [(1, "reader3@synthetic.invalid"), (2, "reader3@synthetic.invalid")])
    result = onboard()
    assert result["due_part1_count"] == result["due_part2_count"] == 2
    assert state.calls == [(1, "reader3@synthetic.invalid"), (2, "reader3@synthetic.invalid")]
    for record in state.logs:
        assert_aggregate(record, 2, 1, 1, True)
        if invalid not in ("bad_id", "bad_version"):
            assert record["skip_reasons"] == {"invalid_active_state": 1}


@pytest.mark.parametrize("path", [1, 2, "onboarding"])
@pytest.mark.parametrize("field", ["email", "newsletter_management_id"])
def test_candidate_ambiguity_not_hidden_by_selection(monkeypatch, path, field):
    rows = [aged(1), aged(2)]
    rows[1][field] = rows[0][field].upper() if field == "email" else rows[0][field]
    if path == "onboarding":
        # Even a conflicting identity not itself due must not be hidden.
        rows[1]["created_at"] = datetime.now(timezone.utc).isoformat()
    state = setup(monkeypatch, rows)
    onboard() if path == "onboarding" else manual(path)
    assert not state.calls
    for record in state.logs: assert record["skipped_count"] == record["selected_count"]
    assert not state.db.subscribers.updates


@pytest.mark.parametrize("path", [1, 2, "onboarding"])
@pytest.mark.parametrize("failure", ["configuration", "signing", "sender"])
def test_private_failures_and_mutation_order(monkeypatch, caplog, path, failure):
    state = setup(monkeypatch, [aged()])
    def fail(*args, **kwargs): raise ValueError("PRIVATE_TOKEN secret@synthetic.invalid")
    if failure == "sender": monkeypatch.setattr(state.service, "_send_email", fail)
    else:
        monkeypatch.setattr(server, "newsletter_token_service_from_environment" if failure == "configuration" else "prepare_direct_delivery", fail)
    run = onboard if path == "onboarding" else lambda: manual(path)
    if failure == "sender":
        with pytest.raises(server.HTTPException) as error: run()
        assert error.value.status_code == 500
        assert error.value.detail == ("Onboarding emails unavailable" if path == "onboarding" else f"Site Update Part {path} unavailable")
        assert not state.events and not state.flags
    else:
        run()
        for record in state.logs:
            assert_aggregate(record, 1, 0, 0, False)
            assert record["skip_reasons"] == {"direct_delivery_preparation_failed": 1}
    assert not state.calls and not state.db.subscribers.updates
    assert "PRIVATE_TOKEN" not in caplog.text and "secret@" not in caplog.text


def test_slice5_commit_only_changed_slice5_production_functions():
    for path, allowed in [
        ("backend/server.py", {"send_site_update_part1", "send_site_update_part2", "admin_run_onboarding_emails"}),
        ("backend/app/email_service.py", {"send_site_update_part1", "send_site_update_part2"}),
    ]:
        old = subprocess.check_output(["git", "show", "14d05a9:" + path], text=True)
        def without_targets(source):
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in allowed:
                    node.body, node.args = [], None
            return ast.dump(tree, include_attributes=False)
        # Slice 5 is committed; Slice 6 has the live working-tree scope guard.
        committed = subprocess.check_output(["git", "show", "4503c28:" + path], text=True)
        assert without_targets(old) == without_targets(committed)
