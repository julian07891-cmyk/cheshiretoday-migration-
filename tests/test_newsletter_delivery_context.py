"""Synthetic-only delivery preparation and header contract tests."""

from dataclasses import FrozenInstanceError
import logging
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

from bson.int64 import Int64
import pytest

from backend.app.newsletter_delivery import (
    DeliveryReason, NewsletterDeliveryError, RecipientDeliveryContext,
    create_recipient_context, is_delivery_email, prepare_direct_delivery,
    prepare_recipient_contexts, validate_newsletter_headers,
)
from backend.app.newsletter_token_service import NewsletterTokenService


ID = "123e4567-e89b-42d3-a456-426614174000"
OTHER_ID = "123e4567-e89b-42d3-a456-426614174001"
EMAIL = "reader@synthetic.invalid"


def record(**changes):
    return {"email": EMAIL, "newsletter_management_id": ID,
            "newsletter_token_version": 1, **changes}


def artifact():
    return prepare_direct_delivery(create_recipient_context(record()).context,
                                   NewsletterTokenService("D" * 43))


@pytest.mark.parametrize("version", [1, 2, Int64(3), Int64(2**40)])
def test_valid_context_is_immutable_and_bson_integers_are_supported(version):
    result = create_recipient_context(record(email=f" {EMAIL.upper()} ",
                                            newsletter_token_version=version))
    assert result.reason is DeliveryReason.READY
    assert result.context.email == EMAIL
    assert result.context.newsletter_token_version == version
    with pytest.raises(FrozenInstanceError):
        result.context.email = "changed@synthetic.invalid"
    issued = prepare_direct_delivery(result.context, NewsletterTokenService("D" * 43))
    token = urlsplit(issued.human_unsubscribe_url).fragment.removeprefix("token=")
    assert NewsletterTokenService("D" * 43).verify_direct_unsubscribe_token(token).token_version == version


@pytest.mark.parametrize("field,value,reason", [
    ("newsletter_management_id", ID.upper(), DeliveryReason.INVALID_ID),
    ("newsletter_management_id", ID.replace("-", ""), DeliveryReason.INVALID_ID),
    ("newsletter_management_id", "bad", DeliveryReason.INVALID_ID),
    ("newsletter_management_id", ID.replace("42d3", "12d3"), DeliveryReason.INVALID_ID),
    ("newsletter_management_id", None, DeliveryReason.INVALID_ID),
    ("newsletter_management_id", [ID], DeliveryReason.INVALID_ID),
    *[("newsletter_token_version", value, DeliveryReason.INVALID_VERSION)
      for value in (0, -1, True, False, "1", 1.0, None, [1])],
    *[("email", value, DeliveryReason.INVALID_EMAIL)
      for value in (None, 12, "bad", "a@example.com", "a@example.org",
                    "unsubscribe-test-a@synthetic.invalid", "test@cheshiretoday.co.uk",
                    "reader@synthetic.invalid\r\nBcc: other@synthetic.invalid")],
])
def test_invalid_context_is_value_safe_and_cannot_issue(field, value, reason):
    result = create_recipient_context(record(**{field: value}))
    assert result.context is None
    assert result.reason is reason
    issuer = Mock()
    with pytest.raises(NewsletterDeliveryError, match="^invalid_delivery_context$"):
        prepare_direct_delivery(result.context, issuer)
    issuer.issue_direct_unsubscribe_token.assert_not_called()
    assert EMAIL not in repr(result) and ID not in repr(result)


@pytest.mark.parametrize("field,reason", [
    ("newsletter_management_id", DeliveryReason.MISSING_ID),
    ("newsletter_token_version", DeliveryReason.MISSING_VERSION),
])
def test_missing_identity_never_provisioned(field, reason):
    candidate = record()
    del candidate[field]
    assert create_recipient_context(candidate).reason is reason
    assert field not in candidate


def test_non_record_and_direct_constructor_validation():
    assert create_recipient_context(None).reason is DeliveryReason.INVALID_RECORD
    with pytest.raises(NewsletterDeliveryError, match="invalid_token_version"):
        RecipientDeliveryContext(EMAIL, ID, True)


@pytest.mark.parametrize("records,reason", [
    ([record(), record(email=EMAIL.upper(), newsletter_management_id=OTHER_ID)],
     DeliveryReason.CONFLICTING_EMAIL),
    ([record(), record(newsletter_token_version=2)], DeliveryReason.CONFLICTING_EMAIL),
    ([record(), record(newsletter_token_version=None)], DeliveryReason.CONFLICTING_EMAIL),
    ([record(), record(email="other@synthetic.invalid")], DeliveryReason.DUPLICATE_ID),
    ([record(), record()], DeliveryReason.DUPLICATE_ID),
    ([record(), record(email=None)], DeliveryReason.DUPLICATE_ID),
])
def test_all_ambiguous_peers_rejected_independent_of_order(records, reason):
    for candidates in (records, list(reversed(records))):
        results = prepare_recipient_contexts(candidates)
        assert all(result.context is None and result.reason is reason for result in results)


def test_unambiguous_candidate_order_and_aggregate_reasons():
    results = prepare_recipient_contexts([
        record(), record(email="other@synthetic.invalid", newsletter_management_id=OTHER_ID),
        {},
    ])
    assert [r.context.email for r in results if r.context] == [EMAIL, "other@synthetic.invalid"]
    assert [r.reason for r in results].count(DeliveryReason.INVALID_EMAIL) == 1


def test_one_issuance_same_credential_and_safe_representations():
    service = NewsletterTokenService("D" * 43)
    issuer = Mock(wraps=service)
    context = create_recipient_context(record()).context
    prepared = prepare_direct_delivery(context, issuer)
    issuer.issue_direct_unsubscribe_token.assert_called_once_with(ID, 1)
    human = urlsplit(prepared.human_unsubscribe_url)
    native = urlsplit(prepared.native_headers["List-Unsubscribe"][1:-1])
    token = parse_qs(human.fragment)["token"][0]
    assert native.scheme == human.scheme == "https"
    assert native.netloc == human.netloc == "cheshiretoday.co.uk"
    assert human.path == "/unsubscribe" and not human.query
    assert native.path == "/api/newsletter/unsubscribe/one-click"
    assert parse_qs(native.query) == {"token": [token]}
    assert prepared.native_headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert service.verify_direct_unsubscribe_token(token).purpose == "unsubscribe"
    assert "preferences" not in prepared.human_unsubscribe_url
    assert all(secret not in repr(prepared) + repr(context) for secret in (token, ID, EMAIL))
    with pytest.raises(TypeError):
        prepared.native_headers["List-Unsubscribe"] = "changed"
    with pytest.raises(FrozenInstanceError):
        prepared.human_unsubscribe_url = "changed"


def test_preparation_error_suppresses_issuer_exception(caplog):
    issuer = Mock()
    issuer.issue_direct_unsubscribe_token.side_effect = RuntimeError(f"secret {EMAIL} {ID}")
    with pytest.raises(NewsletterDeliveryError) as error:
        prepare_direct_delivery(create_recipient_context(record()).context, issuer)
    assert str(error.value) == "direct_delivery_preparation_failed"
    assert error.value.__suppress_context__
    assert not caplog.text


def test_nested_header_diagnostics_and_explicit_exports(caplog):
    issuer = Mock(wraps=NewsletterTokenService("D" * 43))
    prepared = prepare_direct_delivery(create_recipient_context(record()).context, issuer)
    headers = prepared.native_headers
    native = headers["List-Unsubscribe"][1:-1]
    token = parse_qs(urlsplit(native).query)["token"][0]
    outputs = [repr(headers), str(headers), repr([headers]), repr((headers,)),
               repr({"headers": headers}), f"{headers}", f"{headers!r}",
               str(Exception(headers)), repr(Exception(headers)), repr(prepared)]
    with caplog.at_level(logging.INFO):
        logging.getLogger("synthetic.headers").info("headers=%s repr=%r", headers, headers)
    assert all(secret not in " ".join(outputs) + caplog.text
               for secret in (token, native, EMAIL, ID))
    first, second = headers.as_transport_dict(), headers.as_transport_dict()
    assert type(first) is type(second) is dict
    assert first == second == dict(headers) and first is not second
    first.clear()
    assert headers.as_transport_dict() == second
    with pytest.raises(TypeError):
        headers["List-Unsubscribe"] = "changed"
    with pytest.raises(FrozenInstanceError):
        headers._items = ()
    assert parse_qs(urlsplit(prepared.human_unsubscribe_url).fragment) == {"token": [token]}
    issuer.issue_direct_unsubscribe_token.assert_called_once_with(ID, 1)


@pytest.mark.parametrize("mutate", [
    lambda h: {**h, "Bcc": EMAIL},
    lambda h: {**h, "list-unsubscribe": h["List-Unsubscribe"]},
    lambda h: {"List-Unsubscribe": h["List-Unsubscribe"]},
    lambda h: {**h, "List-Unsubscribe": 1},
    lambda h: {**h, "List-Unsubscribe-Post": "wrong"},
    *[lambda h, old=old, new=new: {**h, "List-Unsubscribe": h["List-Unsubscribe"].replace(old, new)}
      for old, new in [("https:", "http:"), ("cheshiretoday.co.uk", "evil.invalid"),
                       ("one-click", "other"), ("?token=", "?other="),
                       (">", "&extra=1>"), (">", "&token=other>"),
                       ("<", ""), (">", ""), (">", "\r>"), (">", "\n>"),
                       (">", "#fragment>"), ("?token=", "?token=%20")]],
    lambda h: {**h, "List-Unsubscribe": "<https://cheshiretoday.co.uk/api/newsletter/unsubscribe/one-click?token=bad>"},
    lambda h: {**h, "List-Unsubscribe-Post": "List-Unsubscribe=One-Click\nBcc: evil"},
    lambda h: list(h.items()),
])
def test_invalid_headers_rejected_without_values(mutate):
    with pytest.raises(NewsletterDeliveryError, match="^invalid_newsletter_headers$"):
        validate_newsletter_headers(mutate(dict(artifact().native_headers)))


def test_validated_headers_are_fresh_copies():
    headers = dict(artifact().native_headers)
    first = validate_newsletter_headers(headers)
    second = validate_newsletter_headers(headers)
    headers.clear()
    first.clear()
    assert set(second) == {"List-Unsubscribe", "List-Unsubscribe-Post"}


@pytest.mark.parametrize("token", ["a.b." + "A" * 43, "e30.e30." + "A" * 43,
                                   "a" * 4097, "", "a.b.c", "a.b.c,d.e.f"])
def test_malformed_compact_token_syntax_rejected(token):
    headers = dict(artifact().native_headers)
    headers["List-Unsubscribe"] = f"<https://cheshiretoday.co.uk/api/newsletter/unsubscribe/one-click?token={token}>"
    with pytest.raises(NewsletterDeliveryError, match="^invalid_newsletter_headers$"):
        validate_newsletter_headers(headers)


def test_email_policy_matches_existing_selector():
    # Inspect the actual function without importing server/provider collaborators.
    import ast
    from pathlib import Path
    source = ast.parse((Path(__file__).parents[1] / "backend/server.py").read_text())
    function = next(n for n in source.body if isinstance(n, ast.FunctionDef)
                    and n.name == "is_deliverable_newsletter_email")
    pattern = next(n for n in source.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "NEWSLETTER_EMAIL_REGEX"
                           for t in n.targets))
    import re
    namespace = {"re": re}
    exec(compile(ast.Module(body=[pattern, function], type_ignores=[]), "<selector>", "exec"), namespace)
    for email in [EMAIL, EMAIL.upper(), f" {EMAIL} ", "a@example.com", "bad", "",
                  "unsubscribe-test-x@synthetic.invalid", "test@cheshiretoday.co.uk"]:
        assert is_delivery_email(email) == namespace["is_deliverable_newsletter_email"](email)
