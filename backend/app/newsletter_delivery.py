"""Opt-in direct-newsletter delivery primitives; no database or transport I/O.

Contexts/artifacts are internal sensitive objects, not logging/API payloads.
Candidate preparation is not an audience selector or a global uniqueness audit.
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping
import base64
import binascii
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from urllib.parse import urlsplit
from uuid import UUID

from .newsletter_token_service import NewsletterTokenService


CANONICAL_ORIGIN = "https://cheshiretoday.co.uk"
ONE_CLICK_PATH = "/api/newsletter/unsubscribe/one-click"
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
_COMPACT_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}")
_HEADER_NAMES = frozenset({"List-Unsubscribe", "List-Unsubscribe-Post"})


class DeliveryReason(str, Enum):
    READY = "ready"
    INVALID_RECORD = "invalid_record"
    INVALID_EMAIL = "invalid_email"
    MISSING_ID = "missing_management_id"
    INVALID_ID = "invalid_management_id"
    MISSING_VERSION = "missing_token_version"
    INVALID_VERSION = "invalid_token_version"
    CONFLICTING_EMAIL = "conflicting_email_identity"
    DUPLICATE_ID = "duplicate_management_identity"


class NewsletterDeliveryError(ValueError):
    """Errors raised here contain only fixed, non-sensitive categories."""


def is_delivery_email(value: object) -> bool:
    """Mirror server.is_deliverable_newsletter_email without importing the app.

    Keep the parity regression until Phase 2B can share the existing selector seam.
    Reject non-strings before applying the existing normalisation/address policy.
    """
    if not isinstance(value, str):
        return False
    email = value.strip().lower()
    if not _EMAIL_RE.fullmatch(email):
        return False
    local, _, domain = email.rpartition("@")
    return not (
        local.startswith("unsubscribe-test-")
        or domain.startswith("example.")
        or ("test" in local and "cheshiretoday" in domain)
    )


def _canonical_id(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = UUID(value)
        return parsed.version == 4 and str(parsed) == value
    except (ValueError, AttributeError, TypeError):
        return False


def _context_reason(record: Mapping) -> DeliveryReason:
    if not is_delivery_email(record.get("email")):
        return DeliveryReason.INVALID_EMAIL
    if "newsletter_management_id" not in record:
        return DeliveryReason.MISSING_ID
    if not _canonical_id(record["newsletter_management_id"]):
        return DeliveryReason.INVALID_ID
    if "newsletter_token_version" not in record:
        return DeliveryReason.MISSING_VERSION
    version = record["newsletter_token_version"]
    # bson.int64.Int64 is an int subclass; bool is also one, but is forbidden.
    if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
        return DeliveryReason.INVALID_VERSION
    return DeliveryReason.READY


@dataclass(frozen=True, slots=True)
class RecipientDeliveryContext:
    email: str = field(repr=False)
    newsletter_management_id: str = field(repr=False)
    newsletter_token_version: int = field(repr=False)

    def __post_init__(self):
        reason = _context_reason({
            "email": self.email,
            "newsletter_management_id": self.newsletter_management_id,
            "newsletter_token_version": self.newsletter_token_version,
        })
        if reason is not DeliveryReason.READY:
            raise NewsletterDeliveryError(reason.value)
        object.__setattr__(self, "email", self.email.strip().lower())


@dataclass(frozen=True, slots=True)
class RecipientContextResult:
    context: RecipientDeliveryContext | None = field(repr=False)
    reason: DeliveryReason


def create_recipient_context(record: object) -> RecipientContextResult:
    """Validate only; invalid input cannot issue a token or provision identity."""
    if not isinstance(record, Mapping):
        return RecipientContextResult(None, DeliveryReason.INVALID_RECORD)
    reason = _context_reason(record)
    if reason is not DeliveryReason.READY:
        return RecipientContextResult(None, reason)
    return RecipientContextResult(
        RecipientDeliveryContext(
            record["email"], record["newsletter_management_id"],
            record["newsletter_token_version"],
        ),
        DeliveryReason.READY,
    )


def prepare_recipient_contexts(records: Iterable[Mapping]) -> tuple[RecipientContextResult, ...]:
    """Reject detected ambiguity in supplied candidates, preserving input order.

    Even identical repeated management IDs are rejected: this helper cannot prove
    whether repeated records represent one document. Invalid peers cannot be
    discarded to make an ambiguous address appear safe. No database scans occur.
    """
    records = tuple(records)
    results = [create_recipient_context(record) for record in records]
    by_email, by_id = defaultdict(list), defaultdict(list)
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            continue
        email = record.get("email")
        if isinstance(email, str):
            by_email[email.strip().lower()].append(index)
        management_id = record.get("newsletter_management_id")
        if _canonical_id(management_id):
            by_id[management_id].append(index)
    duplicate_ids = {i for group in by_id.values() if len(group) > 1 for i in group}
    conflicting_emails = set()
    for group in by_email.values():
        if len(group) > 1:
            contexts = {results[i].context for i in group}
            if None in contexts or len(contexts) > 1:
                conflicting_emails.update(group)
    for index in duplicate_ids | conflicting_emails:
        reason = (DeliveryReason.CONFLICTING_EMAIL if index in conflicting_emails
                  else DeliveryReason.DUPLICATE_ID)
        results[index] = RecipientContextResult(None, reason)
    return tuple(results)


def _compact_token_syntax(token: str) -> bool:
    if len(token) > 4096 or not _COMPACT_TOKEN_RE.fullmatch(token):
        return False
    try:
        segments = token.split(".")
        decoded = [base64.b64decode(part + "=" * (-len(part) % 4),
                                    altchars=b"-_", validate=True) for part in segments]
        # Require canonical unpadded base64url, including valid trailing pad bits.
        if any(base64.urlsafe_b64encode(value).decode().rstrip("=") != part
               for value, part in zip(decoded, segments)):
            return False
        return (
            json.loads(decoded[0]) == {"alg": "HS256", "typ": "JWT"}
            and isinstance(json.loads(decoded[1]), dict)
            and len(decoded[2]) == 32
        )
    except (ValueError, UnicodeError, binascii.Error, RecursionError):
        return False


def validate_newsletter_headers(headers: object) -> dict[str, str]:
    """Return a fresh canonical mapping or raise a value-free validation error.

    This validates transport syntax, not signature/claims. Only the direct issuer
    should prepare headers; the unsubscribe endpoint authenticates the credential.
    """
    invalid = NewsletterDeliveryError("invalid_newsletter_headers")
    if not isinstance(headers, Mapping):
        raise invalid
    items = list(headers.items())
    if len(items) != 2 or {name for name, _ in items} != _HEADER_NAMES:
        raise invalid
    if any(not isinstance(value, str) or "\r" in value or "\n" in value
           for _, value in items):
        raise invalid
    copied = dict(items)
    if copied["List-Unsubscribe-Post"] != "List-Unsubscribe=One-Click":
        raise invalid
    value = copied["List-Unsubscribe"]
    prefix = f"<{CANONICAL_ORIGIN}{ONE_CLICK_PATH}?token="
    if not value.startswith(prefix) or not value.endswith(">"):
        raise invalid
    token = value[len(prefix):-1]
    if not _compact_token_syntax(token):
        raise invalid
    return copied


@dataclass(frozen=True, slots=True)
class _NewsletterHeaders(Mapping[str, str]):
    """Immutable internal headers with safe diagnostics, not safe serialization.

    Explicit Mapping value lookup still reveals credentials by design.
    """
    _items: tuple = field(repr=False)

    def __init__(self, headers):
        object.__setattr__(self, "_items", tuple(validate_newsletter_headers(headers).items()))

    def __getitem__(self, key):
        for name, value in self._items:
            if name == key:
                return value
        raise KeyError("unknown_newsletter_header")

    def __iter__(self):
        return (name for name, _ in self._items)

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return "<NewsletterHeaders redacted>"

    __str__ = __repr__

    def as_transport_dict(self) -> dict[str, str]:
        """Explicit sensitive export: fresh mutable copy, never safe to log."""
        return dict(self._items)


@dataclass(frozen=True, slots=True)
class PreparedNewsletterDelivery:
    context: RecipientDeliveryContext = field(repr=False)
    human_unsubscribe_url: str = field(repr=False)
    native_headers: Mapping[str, str] = field(repr=False)

    def __post_init__(self):
        object.__setattr__(self, "native_headers", _NewsletterHeaders(self.native_headers))


def prepare_direct_delivery(
    context: RecipientDeliveryContext, token_service: NewsletterTokenService,
) -> PreparedNewsletterDelivery:
    """Issue exactly once, sharing the credential across human/text/native links."""
    if not isinstance(context, RecipientDeliveryContext):
        raise NewsletterDeliveryError("invalid_delivery_context")
    try:
        token = token_service.issue_direct_unsubscribe_token(
            context.newsletter_management_id, context.newsletter_token_version,
        )
        return PreparedNewsletterDelivery(
            context,
            f"{CANONICAL_ORIGIN}/unsubscribe#token={token}",
            {
                "List-Unsubscribe": f"<{CANONICAL_ORIGIN}{ONE_CLICK_PATH}?token={token}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            },
        )
    except Exception:
        # Neither provider/issuer exception text nor credential payloads escape.
        raise NewsletterDeliveryError("direct_delivery_preparation_failed") from None


def validate_prepared_delivery(
    delivery: PreparedNewsletterDelivery,
    token_service: NewsletterTokenService,
) -> PreparedNewsletterDelivery:
    """Authenticate one prepared artifact and bind both links to its context."""
    try:
        if not isinstance(delivery, PreparedNewsletterDelivery):
            raise ValueError
        context = delivery.context
        if not isinstance(context, RecipientDeliveryContext):
            raise ValueError

        human = urlsplit(delivery.human_unsubscribe_url)
        if (
            human.scheme != "https"
            or human.netloc != "cheshiretoday.co.uk"
            or human.path != "/unsubscribe"
            or human.query
            or not human.fragment.startswith("token=")
        ):
            raise ValueError
        human_token = human.fragment[len("token="):]
        if not _compact_token_syntax(human_token):
            raise ValueError
        if delivery.human_unsubscribe_url != (
            f"{CANONICAL_ORIGIN}/unsubscribe#token={human_token}"
        ):
            raise ValueError

        headers = validate_newsletter_headers(delivery.native_headers)
        native_value = headers["List-Unsubscribe"]
        native_prefix = f"<{CANONICAL_ORIGIN}{ONE_CLICK_PATH}?token="
        native_token = native_value[len(native_prefix):-1]
        if native_value != f"{native_prefix}{native_token}>" or native_token != human_token:
            raise ValueError

        claims = token_service.verify_direct_unsubscribe_token(
            human_token,
            expected_token_version=context.newsletter_token_version,
        )
        if (
            claims.subscriber_management_id != context.newsletter_management_id
            or claims.token_version != context.newsletter_token_version
        ):
            raise ValueError
        return delivery
    except Exception:
        raise NewsletterDeliveryError("invalid_prepared_delivery") from None
