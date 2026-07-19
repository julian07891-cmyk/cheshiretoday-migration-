import importlib
import inspect
import logging
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from backend.app import newsletter_management_email as management


NOW = datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)
RECIPIENT = "owner@example.com"
TOKEN = "header.payload-signature_~"
ORIGIN = "https://cheshiretoday.co.uk"


class FakeTransport:
    def __init__(self, outcome=True, error=None):
        self.outcome = outcome
        self.error = error
        self.calls = []

    def send_transactional(self, message):
        self.calls.append(message)
        if self.error:
            raise self.error
        return self.outcome


def make_request(
    *,
    purpose=management.NewsletterManagementEmailPurpose.PREFERENCES,
    recipient=RECIPIENT,
    token=TOKEN,
    expires_at=None,
):
    return management.NewsletterManagementEmailRequest(
        recipient_email=recipient,
        purpose=purpose,
        token=token,
        expires_at=expires_at or NOW + timedelta(minutes=30),
    )


def make_helper(transport=None, origin=ORIGIN):
    return management.NewsletterManagementEmailHelper(
        transport=transport or FakeTransport(),
        site_origin=origin,
    )


def build(purpose=management.NewsletterManagementEmailPurpose.PREFERENCES, **kwargs):
    return make_helper().build_message(
        make_request(purpose=purpose, **kwargs),
        now=NOW,
    )


def expected_url(purpose, token=TOKEN):
    path = {
        management.NewsletterManagementEmailPurpose.PREFERENCES: (
            "/newsletter/preferences"
        ),
        management.NewsletterManagementEmailPurpose.UNSUBSCRIBE: "/unsubscribe",
        management.NewsletterManagementEmailPurpose.REACTIVATE: (
            "/newsletter/reactivate"
        ),
    }[purpose]
    from urllib.parse import quote

    return f"{ORIGIN}{path}#token={quote(token, safe='')}"


def rendered_content(message):
    return f"{message.subject}\n{message.html}\n{message.text}"


def test_exact_purpose_enum_values():
    assert {
        purpose.value for purpose in management.NewsletterManagementEmailPurpose
    } == {"preferences", "unsubscribe", "reactivate"}


@pytest.mark.parametrize(
    ("purpose", "subject"),
    [
        (
            management.NewsletterManagementEmailPurpose.PREFERENCES,
            "Your Cheshire Today preferences link",
        ),
        (
            management.NewsletterManagementEmailPurpose.UNSUBSCRIBE,
            "Confirm your Cheshire Today unsubscribe request",
        ),
        (
            management.NewsletterManagementEmailPurpose.REACTIVATE,
            "Confirm your Cheshire Today newsletter reactivation",
        ),
    ],
)
def test_exact_fixed_subjects(purpose, subject):
    assert build(purpose).subject == subject


@pytest.mark.parametrize("purpose", ["preferences", "unsubscribe", "reactivate", "other", None])
def test_non_enum_purpose_is_rejected(purpose):
    with pytest.raises(management.NewsletterManagementEmailValidationError):
        make_helper().build_message(make_request(purpose=purpose), now=NOW)


@pytest.mark.parametrize(
    "origin",
    [
        "http://cheshiretoday.co.uk",
        "https://www.cheshiretoday.co.uk",
        "https://mail.cheshiretoday.co.uk",
        "https://user@cheshiretoday.co.uk",
        "https://user:pass@cheshiretoday.co.uk",
        "https://cheshiretoday.co.uk:443",
        "https://cheshiretoday.co.uk/",
        "https://cheshiretoday.co.uk/path",
        "https://cheshiretoday.co.uk?query=1",
        "https://cheshiretoday.co.uk#fragment",
        "https://localhost",
        "https://127.0.0.1",
        "https://CHESHIRETODAY.CO.UK",
        " https://cheshiretoday.co.uk",
        "https://cheshiretoday.co.uk ",
        "cheshiretoday.co.uk",
        "",
        None,
    ],
)
def test_noncanonical_origins_are_rejected(origin):
    with pytest.raises(management.NewsletterManagementEmailValidationError):
        make_helper(origin=origin)


def test_exact_canonical_origin_is_accepted():
    assert make_helper(origin=ORIGIN)


@pytest.mark.parametrize(
    "recipient",
    [
        "",
        "   ",
        "not-an-email",
        "name@",
        "@example.com",
        "name@example",
        "name @example.com",
        "name@example..com",
        ".name@example.com",
        "name.@example.com",
        "first..last@example.com",
        "name\n@example.com",
        "name\r@example.com",
        "name\t@example.com",
        "name\x00@example.com",
        "name\x1f@example.com",
        None,
    ],
)
def test_invalid_recipients_are_rejected(recipient):
    with pytest.raises(management.NewsletterManagementEmailValidationError):
        build(recipient=recipient)


def test_valid_recipient_is_trimmed_only_for_envelope():
    message = build(recipient="  owner@example.com  ")
    assert message.recipient_email == RECIPIENT
    assert RECIPIENT not in message.subject
    assert RECIPIENT not in message.html
    assert RECIPIENT not in message.text


@pytest.mark.parametrize(
    "token",
    [
        "",
        " ",
        "\n",
        "token\nvalue",
        "token\rvalue",
        "token\tvalue",
        "token\x00value",
        "token\x01value",
        None,
        "x" * 4097,
    ],
)
def test_invalid_tokens_are_rejected(token):
    with pytest.raises(management.NewsletterManagementEmailValidationError):
        build(token=token)


def test_maximum_length_token_is_accepted():
    message = build(token="x" * 4096)
    assert "#token=" in message.html


@pytest.mark.parametrize(
    "token",
    [
        TOKEN,
        "token with spaces",
        "token/with/slashes",
        "token%already",
        "token+plus",
        "tøken-unicode",
    ],
)
def test_token_round_trips_after_exactly_one_fragment_decode(token):
    url = expected_url(
        management.NewsletterManagementEmailPurpose.PREFERENCES,
        token,
    )
    message = build(token=token)
    assert url in message.html
    assert url in message.text
    fragment = urlsplit(url).fragment
    assert fragment.startswith("token=")
    assert unquote(fragment.removeprefix("token=")) == token


def test_percent_in_token_is_not_double_encoded():
    message = build(token="value%2Fpart")
    url = expected_url(
        management.NewsletterManagementEmailPurpose.PREFERENCES,
        "value%2Fpart",
    )
    assert "%252F" in url
    assert "%25252F" not in message.html
    assert unquote(urlsplit(url).fragment.removeprefix("token=")) == "value%2Fpart"


@pytest.mark.parametrize(
    "now",
    [
        datetime(2026, 7, 19, 12, 0),
        datetime(
            2026,
            7,
            19,
            13,
            0,
            tzinfo=timezone(timedelta(hours=1)),
        ),
        None,
        "2026-07-19T12:00:00Z",
    ],
)
def test_now_must_be_timezone_aware_utc(now):
    with pytest.raises(management.NewsletterManagementEmailValidationError):
        make_helper().build_message(make_request(), now=now)


@pytest.mark.parametrize(
    "expires_at",
    [
        datetime(2026, 7, 19, 12, 30),
        datetime(
            2026,
            7,
            19,
            13,
            30,
            tzinfo=timezone(timedelta(hours=1)),
        ),
        None,
        "2026-07-19T12:30:00Z",
    ],
)
def test_expiry_must_be_timezone_aware_utc(expires_at):
    request = make_request(expires_at=NOW + timedelta(minutes=30))
    object.__setattr__(request, "expires_at", expires_at)
    with pytest.raises(management.NewsletterManagementEmailValidationError):
        make_helper().build_message(request, now=NOW)


@pytest.mark.parametrize(
    "expires_at",
    [
        NOW - timedelta(seconds=1),
        NOW,
        NOW + timedelta(minutes=30, seconds=1),
        NOW + timedelta(hours=1),
    ],
)
def test_invalid_expiry_window_is_rejected(expires_at):
    with pytest.raises(management.NewsletterManagementEmailValidationError):
        build(expires_at=expires_at)


@pytest.mark.parametrize(
    "expires_at",
    [NOW + timedelta(seconds=1), NOW + timedelta(minutes=30)],
)
def test_approved_expiry_boundaries_are_accepted(expires_at):
    assert build(expires_at=expires_at)


@pytest.mark.parametrize(
    ("purpose", "path", "action"),
    [
        (
            management.NewsletterManagementEmailPurpose.PREFERENCES,
            "/newsletter/preferences",
            "Manage newsletter preferences",
        ),
        (
            management.NewsletterManagementEmailPurpose.UNSUBSCRIBE,
            "/unsubscribe",
            "Confirm unsubscribe",
        ),
        (
            management.NewsletterManagementEmailPurpose.REACTIVATE,
            "/newsletter/reactivate",
            "Confirm newsletter reactivation",
        ),
    ],
)
def test_exact_url_and_action_contracts(purpose, path, action):
    message = build(purpose)
    url = expected_url(purpose)
    assert url == f"{ORIGIN}{path}#token={TOKEN}"
    assert message.html.count("<a ") == 1
    assert message.html.count(f">{action}</a>") == 1
    assert message.text.count(f"{action}:\n{url}") == 1
    assert message.html.count(url) == 2
    assert message.text.count(url) == 1


@pytest.mark.parametrize(
    "purpose", list(management.NewsletterManagementEmailPurpose)
)
def test_management_urls_have_no_tracking_or_identity_data(purpose):
    message = build(purpose)
    content = rendered_content(message)
    url = expected_url(purpose)
    parsed = urlsplit(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "cheshiretoday.co.uk"
    assert parsed.query == ""
    assert parsed.username is None
    assert parsed.password is None
    assert parsed.port is None
    assert "?email=" not in content
    assert "utm_" not in content.lower()
    assert "analytics" not in content.lower()
    assert "/email/track/" not in content
    assert "tracking_id" not in content
    assert "bit.ly" not in content
    assert "tinyurl" not in content
    assert RECIPIENT not in content


@pytest.mark.parametrize(
    "purpose", list(management.NewsletterManagementEmailPurpose)
)
def test_required_safe_copy_is_present(purpose):
    message = build(purpose)
    assert "CHESHIRE TODAY" in message.html
    assert "CHESHIRE TODAY" in message.text
    assert management.EXPIRY_COPY in message.html
    assert management.EXPIRY_COPY in message.text
    assert management.IGNORE_COPY in message.html
    assert management.IGNORE_COPY in message.text
    assert "reply to this email" in message.html
    assert "reply to this email" in message.text


@pytest.mark.parametrize(
    "forbidden",
    [
        "subscriber_management_id",
        "newsletter_management_id",
        "mongodb",
        "token version",
        "active state",
        "daily_brief",
        "weekly_roundup",
        "breaking_news",
        "provider",
        "campaign",
        "<script",
        "display:none",
        'width="1"',
        "tracking pixel",
    ],
)
def test_rendered_messages_exclude_private_or_tracking_content(forbidden):
    assert forbidden not in rendered_content(build()).lower()


def test_unsubscribe_copy_does_not_claim_current_subscription_state():
    content = rendered_content(
        build(management.NewsletterManagementEmailPurpose.UNSUBSCRIBE)
    ).lower()
    assert "currently subscribed" not in content
    assert "you are subscribed" not in content


def test_reactivation_copy_does_not_expose_unsubscribe_history():
    content = rendered_content(
        build(management.NewsletterManagementEmailPurpose.REACTIVATE)
    ).lower()
    assert "previously unsubscribed" not in content
    assert "unsubscribe history" not in content


@pytest.mark.parametrize(
    "instance",
    [
        make_request(),
        build(),
        management.NewsletterManagementEmailResult(
            True,
            management.NewsletterManagementEmailResultReason.ACCEPTED,
        ),
    ],
)
def test_public_models_are_immutable(instance):
    field_name = fields(instance)[0].name
    with pytest.raises(FrozenInstanceError):
        setattr(instance, field_name, "changed")


def test_success_calls_transport_exactly_once_with_built_message():
    transport = FakeTransport(True)
    helper = make_helper(transport)
    request = make_request()
    expected = helper.build_message(request, now=NOW)
    result = helper.send(request, now=NOW)
    assert transport.calls == [expected]
    assert result == management.NewsletterManagementEmailResult(
        accepted=True,
        reason=management.NewsletterManagementEmailResultReason.ACCEPTED,
    )


def test_false_transport_result_is_rejected_without_retry():
    transport = FakeTransport(False)
    result = make_helper(transport).send(make_request(), now=NOW)
    assert len(transport.calls) == 1
    assert result == management.NewsletterManagementEmailResult(
        accepted=False,
        reason=management.NewsletterManagementEmailResultReason.TRANSPORT_REJECTED,
    )


@pytest.mark.parametrize(
    "error",
    [
        TimeoutError("private timeout details"),
        management.NewsletterTransactionalIndeterminateError(
            "private ambiguous-delivery details"
        ),
    ],
)
def test_ambiguous_transport_failure_is_indeterminate_without_retry(error):
    transport = FakeTransport(error=error)
    result = make_helper(transport).send(make_request(), now=NOW)
    assert len(transport.calls) == 1
    assert result == management.NewsletterManagementEmailResult(
        accepted=False,
        reason=management.NewsletterManagementEmailResultReason.INDETERMINATE,
    )


def test_other_transport_exception_is_safely_categorized_without_retry():
    transport = FakeTransport(
        error=RuntimeError(f"{RECIPIENT} {TOKEN} private provider response")
    )
    result = make_helper(transport).send(make_request(), now=NOW)
    assert len(transport.calls) == 1
    assert result == management.NewsletterManagementEmailResult(
        accepted=False,
        reason=management.NewsletterManagementEmailResultReason.TRANSPORT_ERROR,
    )
    assert RECIPIENT not in repr(result)
    assert TOKEN not in repr(result)


def test_validation_failure_never_calls_transport():
    transport = FakeTransport()
    result = make_helper(transport).send(
        make_request(token="invalid\nvalue"),
        now=NOW,
    )
    assert transport.calls == []
    assert result == management.NewsletterManagementEmailResult(
        accepted=False,
        reason=management.NewsletterManagementEmailResultReason.VALIDATION_FAILED,
    )


def test_constructor_requires_transport():
    with pytest.raises(management.NewsletterManagementEmailValidationError):
        management.NewsletterManagementEmailHelper(
            transport=None,
            site_origin=ORIGIN,
        )


def test_result_contains_only_safe_fields():
    assert [field.name for field in fields(management.NewsletterManagementEmailResult)] == [
        "accepted",
        "reason",
    ]


def test_sensitive_request_and_message_fields_are_redacted_from_repr():
    request = make_request()
    message = build()
    assert RECIPIENT not in repr(request)
    assert TOKEN not in repr(request)
    assert RECIPIENT not in repr(message)
    assert TOKEN not in repr(message)
    assert "<html" not in repr(message)


def test_safe_validation_exception_contains_no_sensitive_input():
    recipient = "private-address@example.com"
    token = "private-token-value"
    request = make_request(recipient=recipient, token=token, expires_at=NOW)
    with pytest.raises(
        management.NewsletterManagementEmailValidationError
    ) as exc_info:
        make_helper().build_message(request, now=NOW)
    message = str(exc_info.value)
    assert recipient not in message
    assert token not in message
    assert ORIGIN not in message
    assert "<html" not in message


def test_module_emits_no_logs_or_print_output(caplog, capsys):
    caplog.set_level(logging.DEBUG)
    make_helper().send(make_request(), now=NOW)
    assert caplog.records == []
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_module_import_is_runtime_isolated(monkeypatch):
    source = Path(management.__file__).read_text()
    forbidden = [
        "backend.server",
        "backend.app.email_service",
        "MongoClient",
        "AsyncIOMotor",
        "create_index(",
        "os.environ",
        "getenv(",
        "httpx",
        "requests",
        "smtplib",
        "FastAPI",
        "APIRouter",
    ]
    for value in forbidden:
        assert value not in source
    reloaded = importlib.reload(management)
    assert reloaded


def test_stage_4f1_runtime_imports_are_narrow():
    repository = Path(__file__).resolve().parents[1]
    importers = []
    for path in (repository / "backend").rglob("*.py"):
        if path.name == "newsletter_management_email.py":
            continue
        if "newsletter_management_email" in path.read_text(errors="ignore"):
            importers.append(path.relative_to(repository).as_posix())
    assert importers == [
        "backend/server.py",
        "backend/app/email_service.py",
    ]


def test_stage_4f1_runtime_wiring_remains_gated_and_lazy():
    repository = Path(__file__).resolve().parents[1]
    server = (repository / "backend/server.py").read_text()
    email_service = (repository / "backend/app/email_service.py").read_text()
    assert "NEWSLETTER_REQUEST_LINKS_ENABLED = False" in server
    assert "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED = False" in server
    assert "def _create_newsletter_management_email_helper(" in server
    assert "def send_newsletter_management_transactional(" in email_service


def test_transport_protocol_has_only_the_frozen_send_contract():
    members = {
        name
        for name, value in inspect.getmembers(
            management.NewsletterTransactionalTransport
        )
        if callable(value) and not name.startswith("_")
    }
    assert members == {"send_transactional"}
