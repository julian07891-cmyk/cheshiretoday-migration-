"""Isolated builder for future newsletter-management emails.

The running application deliberately does not import this module. It owns no
transport, reads no environment variables, performs no I/O at import time, and
accepts its eventual delivery dependency only through constructor injection.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from html import escape
from typing import Final, Protocol
from urllib.parse import quote


CANONICAL_SITE_ORIGIN: Final = "https://cheshiretoday.co.uk"
MAX_TOKEN_LENGTH: Final = 4096
MANAGEMENT_LINK_LIFETIME: Final = timedelta(minutes=30)
EXPIRY_COPY: Final = "This secure link expires in 30 minutes."
IGNORE_COPY: Final = (
    "If you did not request this, you can ignore this email."
)

_EMAIL_RE: Final = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}$"
)


class NewsletterManagementEmailError(Exception):
    """Base class for safe newsletter-management email failures."""


class NewsletterManagementEmailValidationError(
    NewsletterManagementEmailError
):
    """Input does not satisfy the frozen management-email contract."""


class NewsletterTransactionalIndeterminateError(
    NewsletterManagementEmailError
):
    """A transport could not determine whether the provider accepted a send."""


class NewsletterManagementEmailPurpose(str, Enum):
    PREFERENCES = "preferences"
    UNSUBSCRIBE = "unsubscribe"
    REACTIVATE = "reactivate"


class NewsletterManagementEmailResultReason(str, Enum):
    ACCEPTED = "accepted"
    VALIDATION_FAILED = "validation_failed"
    TRANSPORT_REJECTED = "transport_rejected"
    TRANSPORT_ERROR = "transport_error"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class NewsletterManagementEmailRequest:
    recipient_email: str = field(repr=False)
    purpose: NewsletterManagementEmailPurpose
    token: str = field(repr=False)
    expires_at: datetime


@dataclass(frozen=True)
class NewsletterManagementEmailMessage:
    recipient_email: str = field(repr=False)
    subject: str
    html: str = field(repr=False)
    text: str = field(repr=False)


@dataclass(frozen=True)
class NewsletterManagementEmailResult:
    accepted: bool
    reason: NewsletterManagementEmailResultReason


class NewsletterTransactionalTransport(Protocol):
    def send_transactional(
        self,
        message: NewsletterManagementEmailMessage,
    ) -> bool:
        ...


@dataclass(frozen=True)
class _PurposeContent:
    path: str
    subject: str
    heading: str
    explanation: str
    action: str


_PURPOSE_CONTENT: Final = {
    NewsletterManagementEmailPurpose.PREFERENCES: _PurposeContent(
        path="/newsletter/preferences",
        subject="Your Cheshire Today preferences link",
        heading="Manage your newsletter preferences",
        explanation=(
            "Use the secure link below to open your Cheshire Today "
            "newsletter preference management."
        ),
        action="Manage newsletter preferences",
    ),
    NewsletterManagementEmailPurpose.UNSUBSCRIBE: _PurposeContent(
        path="/unsubscribe",
        subject="Confirm your Cheshire Today unsubscribe request",
        heading="Confirm your unsubscribe request",
        explanation=(
            "Use the secure link below to confirm the requested newsletter "
            "unsubscribe action."
        ),
        action="Confirm unsubscribe",
    ),
    NewsletterManagementEmailPurpose.REACTIVATE: _PurposeContent(
        path="/newsletter/reactivate",
        subject="Confirm your Cheshire Today newsletter reactivation",
        heading="Confirm newsletter reactivation",
        explanation=(
            "Use the secure link below to confirm newsletter reactivation "
            "and select your preferences."
        ),
        action="Confirm newsletter reactivation",
    ),
}


def _safe_validation_error() -> NewsletterManagementEmailValidationError:
    return NewsletterManagementEmailValidationError(
        "Newsletter management email request is invalid."
    )


def _contains_control_characters(value: str) -> bool:
    return any(unicodedata.category(character) == "Cc" for character in value)


def _validate_recipient(value: object) -> str:
    if not isinstance(value, str):
        raise _safe_validation_error()
    recipient = value.strip()
    local, separator, domain = recipient.partition("@")
    if (
        not recipient
        or _contains_control_characters(value)
        or not _EMAIL_RE.fullmatch(recipient)
        or separator != "@"
        or len(recipient) > 254
        or len(local) > 64
        or local.startswith(".")
        or local.endswith(".")
        or ".." in local
        or ".." in domain
    ):
        raise _safe_validation_error()
    return recipient


def _validate_token(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > MAX_TOKEN_LENGTH
        or _contains_control_characters(value)
    ):
        raise _safe_validation_error()
    return value


def _validate_utc(value: object) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() != timedelta(0)
    ):
        raise _safe_validation_error()
    return value


def _validate_purpose(value: object) -> NewsletterManagementEmailPurpose:
    if not isinstance(value, NewsletterManagementEmailPurpose):
        raise _safe_validation_error()
    return value


def _validate_site_origin(value: object) -> str:
    if value != CANONICAL_SITE_ORIGIN:
        raise _safe_validation_error()
    return CANONICAL_SITE_ORIGIN


class NewsletterManagementEmailHelper:
    def __init__(
        self,
        *,
        transport: NewsletterTransactionalTransport,
        site_origin: str,
    ) -> None:
        if transport is None or not callable(
            getattr(transport, "send_transactional", None)
        ):
            raise _safe_validation_error()
        self._transport = transport
        self._site_origin = _validate_site_origin(site_origin)

    def build_message(
        self,
        request: NewsletterManagementEmailRequest,
        *,
        now: datetime,
    ) -> NewsletterManagementEmailMessage:
        current = _validate_utc(now)
        if not isinstance(request, NewsletterManagementEmailRequest):
            raise _safe_validation_error()

        recipient = _validate_recipient(request.recipient_email)
        purpose = _validate_purpose(request.purpose)
        token = _validate_token(request.token)
        expires_at = _validate_utc(request.expires_at)
        lifetime = expires_at - current
        if lifetime <= timedelta(0) or lifetime > MANAGEMENT_LINK_LIFETIME:
            raise _safe_validation_error()

        content = _PURPOSE_CONTENT[purpose]
        encoded_token = quote(token, safe="")
        direct_url = (
            f"{self._site_origin}{content.path}#token={encoded_token}"
        )
        html_url = escape(direct_url, quote=True)

        html = (
            '<!DOCTYPE html><html><head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            "</head>"
            '<body style="margin:0;padding:0;background:#f3f4f6;'
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',"
            "Roboto,Arial,sans-serif;color:#1f2937;\">"
            '<div style="max-width:600px;margin:0 auto;padding:24px;">'
            '<div style="background:#1E3A8A;color:#ffffff;padding:24px;'
            'text-align:center;border-radius:12px 12px 0 0;">'
            '<div style="font-size:25px;font-weight:800;">CHESHIRE TODAY</div>'
            "</div>"
            '<div style="background:#ffffff;padding:30px;'
            'border-radius:0 0 12px 12px;">'
            f'<h1 style="font-size:22px;margin:0 0 18px;">'
            f"{escape(content.heading)}</h1>"
            f'<p style="font-size:15px;line-height:1.6;">'
            f"{escape(content.explanation)}</p>"
            '<p style="text-align:center;margin:28px 0;">'
            f'<a href="{html_url}" style="display:inline-block;'
            "background:#2563eb;color:#ffffff;text-decoration:none;"
            'padding:14px 24px;border-radius:8px;font-weight:700;">'
            f"{escape(content.action)}</a></p>"
            '<p style="font-size:13px;line-height:1.6;color:#4b5563;">'
            "If the button does not work, copy and paste this complete "
            "secure link into your browser:</p>"
            f'<p style="font-size:12px;line-height:1.6;overflow-wrap:anywhere;'
            f'color:#1E3A8A;">{html_url}</p>'
            f'<p style="font-size:13px;color:#4b5563;">{EXPIRY_COPY}</p>'
            f'<p style="font-size:13px;color:#4b5563;">{IGNORE_COPY}</p>'
            '<p style="font-size:13px;color:#4b5563;">'
            "For help, reply to this email and the Cheshire Today team "
            "will assist you.</p>"
            "</div></div></body></html>"
        )

        text = (
            "CHESHIRE TODAY\n\n"
            f"{content.heading}\n\n"
            f"{content.explanation}\n\n"
            f"{content.action}:\n{direct_url}\n\n"
            f"{EXPIRY_COPY}\n\n"
            f"{IGNORE_COPY}\n\n"
            "For help, reply to this email and the Cheshire Today team "
            "will assist you."
        )

        return NewsletterManagementEmailMessage(
            recipient_email=recipient,
            subject=content.subject,
            html=html,
            text=text,
        )

    def send(
        self,
        request: NewsletterManagementEmailRequest,
        *,
        now: datetime,
    ) -> NewsletterManagementEmailResult:
        try:
            message = self.build_message(request, now=now)
        except NewsletterManagementEmailValidationError:
            return NewsletterManagementEmailResult(
                accepted=False,
                reason=NewsletterManagementEmailResultReason.VALIDATION_FAILED,
            )

        try:
            accepted = self._transport.send_transactional(message)
        except (TimeoutError, NewsletterTransactionalIndeterminateError):
            return NewsletterManagementEmailResult(
                accepted=False,
                reason=NewsletterManagementEmailResultReason.INDETERMINATE,
            )
        except Exception:
            return NewsletterManagementEmailResult(
                accepted=False,
                reason=NewsletterManagementEmailResultReason.TRANSPORT_ERROR,
            )

        if accepted is True:
            return NewsletterManagementEmailResult(
                accepted=True,
                reason=NewsletterManagementEmailResultReason.ACCEPTED,
            )
        return NewsletterManagementEmailResult(
            accepted=False,
            reason=NewsletterManagementEmailResultReason.TRANSPORT_REJECTED,
        )
