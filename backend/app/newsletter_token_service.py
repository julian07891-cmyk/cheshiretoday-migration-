"""Purpose-specific signed tokens for newsletter ownership workflows."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType
from typing import Final
from uuid import UUID

import jwt


NEWSLETTER_LINK_SECRET: Final = "NEWSLETTER_LINK_SECRET"
JWT_ALGORITHM: Final = "HS256"
JWT_ALLOWED_ALGORITHMS: Final = ["HS256"]
TOKEN_CLOCK_SKEW_SECONDS: Final = 60

PREFERENCES_PURPOSE: Final = "preferences"
UNSUBSCRIBE_PURPOSE: Final = "unsubscribe"
REACTIVATE_PURPOSE: Final = "reactivate"
ALLOWED_PURPOSES: Final = frozenset(
    {PREFERENCES_PURPOSE, UNSUBSCRIBE_PURPOSE, REACTIVATE_PURPOSE}
)

NEWSLETTER_PREFERENCE_TOKEN_SECONDS: Final = 30 * 24 * 60 * 60
NEWSLETTER_UNSUBSCRIBE_TOKEN_SECONDS: Final = 180 * 24 * 60 * 60
WEBSITE_PREFERENCE_TOKEN_SECONDS: Final = 30 * 60
COMPATIBILITY_PREFERENCE_TOKEN_SECONDS: Final = 30 * 60
WEBSITE_UNSUBSCRIBE_TOKEN_SECONDS: Final = 30 * 60
COMPATIBILITY_UNSUBSCRIBE_TOKEN_SECONDS: Final = 30 * 60
REACTIVATION_TOKEN_SECONDS: Final = 30 * 60

_EXACT_CLAIMS: Final = frozenset({"sub", "purpose", "ver", "iat", "exp"})
_URL_SAFE_SECRET_RE: Final = re.compile(r"^[A-Za-z0-9_-]{43,}$")


class NewsletterTokenError(Exception):
    """Base class for safe newsletter-token failures."""


class NewsletterTokenConfigurationError(NewsletterTokenError):
    """The dedicated signing secret is missing or too weak."""


class InvalidNewsletterTokenError(NewsletterTokenError):
    """The token is malformed, invalid, or outside the approved contract."""


class ExpiredNewsletterTokenError(InvalidNewsletterTokenError):
    """The token has expired outside the approved clock skew."""


class WrongNewsletterTokenPurposeError(InvalidNewsletterTokenError):
    """The token is valid but cannot authorize the requested operation."""


class NewsletterTokenVersionMismatchError(InvalidNewsletterTokenError):
    """The token version does not match the subscriber's current version."""


class NewsletterTokenExpiryProfileMismatchError(NewsletterTokenError):
    """The requested expiry profile is not approved for the token purpose."""


class NewsletterTokenExpiryProfile(str, Enum):
    NEWSLETTER_PREFERENCES = "newsletter_preferences"
    NEWSLETTER_UNSUBSCRIBE = "newsletter_unsubscribe"
    WEBSITE_PREFERENCES = "website_preferences"
    COMPATIBILITY_PREFERENCES = "compatibility_preferences"
    WEBSITE_UNSUBSCRIBE = "website_unsubscribe"
    COMPATIBILITY_UNSUBSCRIBE = "compatibility_unsubscribe"
    REACTIVATION = "reactivation"


PURPOSE_EXPIRY_PROFILES: Final = MappingProxyType(
    {
        PREFERENCES_PURPOSE: frozenset(
            {
                NewsletterTokenExpiryProfile.NEWSLETTER_PREFERENCES,
                NewsletterTokenExpiryProfile.WEBSITE_PREFERENCES,
                NewsletterTokenExpiryProfile.COMPATIBILITY_PREFERENCES,
            }
        ),
        UNSUBSCRIBE_PURPOSE: frozenset(
            {
                NewsletterTokenExpiryProfile.NEWSLETTER_UNSUBSCRIBE,
                NewsletterTokenExpiryProfile.WEBSITE_UNSUBSCRIBE,
                NewsletterTokenExpiryProfile.COMPATIBILITY_UNSUBSCRIBE,
            }
        ),
        REACTIVATE_PURPOSE: frozenset(
            {NewsletterTokenExpiryProfile.REACTIVATION}
        ),
    }
)


EXPIRY_PROFILE_SECONDS: Final = MappingProxyType(
    {
        NewsletterTokenExpiryProfile.NEWSLETTER_PREFERENCES: (
            NEWSLETTER_PREFERENCE_TOKEN_SECONDS
        ),
        NewsletterTokenExpiryProfile.NEWSLETTER_UNSUBSCRIBE: (
            NEWSLETTER_UNSUBSCRIBE_TOKEN_SECONDS
        ),
        NewsletterTokenExpiryProfile.WEBSITE_PREFERENCES: (
            WEBSITE_PREFERENCE_TOKEN_SECONDS
        ),
        NewsletterTokenExpiryProfile.COMPATIBILITY_PREFERENCES: (
            COMPATIBILITY_PREFERENCE_TOKEN_SECONDS
        ),
        NewsletterTokenExpiryProfile.WEBSITE_UNSUBSCRIBE: (
            WEBSITE_UNSUBSCRIBE_TOKEN_SECONDS
        ),
        NewsletterTokenExpiryProfile.COMPATIBILITY_UNSUBSCRIBE: (
            COMPATIBILITY_UNSUBSCRIBE_TOKEN_SECONDS
        ),
        NewsletterTokenExpiryProfile.REACTIVATION: REACTIVATION_TOKEN_SECONDS,
    }
)


@dataclass(frozen=True)
class NewsletterTokenClaims:
    subscriber_management_id: str
    purpose: str
    token_version: int
    issued_at: datetime
    expires_at: datetime


def _safe_invalid_token() -> InvalidNewsletterTokenError:
    return InvalidNewsletterTokenError("Newsletter token is invalid.")


def _validate_secret(secret: str | bytes) -> str | bytes:
    if isinstance(secret, bytes):
        if len(secret) < 32:
            raise NewsletterTokenConfigurationError(
                "Newsletter link secret does not meet the strength requirement."
            )
        return secret
    if not isinstance(secret, str) or not _URL_SAFE_SECRET_RE.fullmatch(secret):
        raise NewsletterTokenConfigurationError(
            "Newsletter link secret does not meet the strength requirement."
        )
    return secret


def _canonical_uuid4(value: object) -> str:
    if not isinstance(value, str):
        raise _safe_invalid_token()
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError, TypeError) as exc:
        raise _safe_invalid_token() from exc
    if parsed.version != 4 or str(parsed) != value:
        raise _safe_invalid_token()
    return value


def _validate_purpose(value: object) -> str:
    if not isinstance(value, str) or value not in ALLOWED_PURPOSES:
        raise _safe_invalid_token()
    return value


def _validate_positive_integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise _safe_invalid_token()
    return value


def _validate_timestamp(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise _safe_invalid_token()
    return value


def _require_utc(value: datetime | None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() != timedelta(0):
        raise ValueError("now must be a timezone-aware UTC datetime.")
    return current


def token_fingerprint(token: str) -> str:
    """Return a redacted, deterministic fingerprint suitable for later logs."""
    if not isinstance(token, str):
        raise TypeError("token must be a string.")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]


class NewsletterTokenService:
    def __init__(self, secret: str | bytes):
        self._secret = _validate_secret(secret)

    def issue_newsletter_token(
        self,
        subscriber_management_id: str,
        purpose: str,
        token_version: int,
        expiry_profile: NewsletterTokenExpiryProfile | str,
        now: datetime | None = None,
    ) -> str:
        management_id = _canonical_uuid4(subscriber_management_id)
        approved_purpose = _validate_purpose(purpose)
        approved_version = _validate_positive_integer(token_version)
        try:
            profile = NewsletterTokenExpiryProfile(expiry_profile)
            lifetime_seconds = EXPIRY_PROFILE_SECONDS[profile]
        except (ValueError, KeyError) as exc:
            raise ValueError("expiry_profile must be an approved fixed profile.") from exc
        if profile not in PURPOSE_EXPIRY_PROFILES[approved_purpose]:
            raise NewsletterTokenExpiryProfileMismatchError(
                "Newsletter token expiry profile is not approved for this purpose."
            )

        issued_at = _require_utc(now)
        issued_at_timestamp = int(issued_at.timestamp())
        expires_at_timestamp = issued_at_timestamp + lifetime_seconds
        if expires_at_timestamp <= issued_at_timestamp:
            raise ValueError("Approved expiry must be later than issuance.")

        payload = {
            "sub": management_id,
            "purpose": approved_purpose,
            "ver": approved_version,
            "iat": issued_at_timestamp,
            "exp": expires_at_timestamp,
        }
        return jwt.encode(
            payload,
            self._secret,
            algorithm=JWT_ALGORITHM,
            headers={"alg": JWT_ALGORITHM, "typ": "JWT"},
        )

    def verify_newsletter_token(
        self,
        token: str,
        expected_purpose: str,
        expected_token_version: int | None = None,
        now: datetime | None = None,
    ) -> NewsletterTokenClaims:
        expected = _validate_purpose(expected_purpose)
        if expected_token_version is not None:
            expected_version = _validate_positive_integer(expected_token_version)
        else:
            expected_version = None
        current_timestamp = int(_require_utc(now).timestamp())

        if not isinstance(token, str) or not token:
            raise _safe_invalid_token()
        try:
            header = jwt.get_unverified_header(token)
            if header != {"alg": JWT_ALGORITHM, "typ": "JWT"}:
                raise _safe_invalid_token()
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=JWT_ALLOWED_ALGORITHMS,
                options={
                    "require": sorted(_EXACT_CLAIMS),
                    "verify_exp": False,
                    "verify_iat": False,
                },
            )
        except InvalidNewsletterTokenError:
            raise
        except jwt.PyJWTError as exc:
            raise _safe_invalid_token() from exc

        if not isinstance(payload, dict) or frozenset(payload) != _EXACT_CLAIMS:
            raise _safe_invalid_token()

        management_id = _canonical_uuid4(payload["sub"])
        purpose = _validate_purpose(payload["purpose"])
        version = _validate_positive_integer(payload["ver"])
        issued_at_timestamp = _validate_timestamp(payload["iat"])
        expires_at_timestamp = _validate_timestamp(payload["exp"])

        if expires_at_timestamp <= issued_at_timestamp:
            raise _safe_invalid_token()
        if issued_at_timestamp > current_timestamp + TOKEN_CLOCK_SKEW_SECONDS:
            raise _safe_invalid_token()
        if expires_at_timestamp < current_timestamp - TOKEN_CLOCK_SKEW_SECONDS:
            raise ExpiredNewsletterTokenError("Newsletter token has expired.")
        if purpose != expected:
            raise WrongNewsletterTokenPurposeError(
                "Newsletter token cannot authorize this operation."
            )
        if expected_version is not None and version != expected_version:
            raise NewsletterTokenVersionMismatchError(
                "Newsletter token version is no longer valid."
            )

        return NewsletterTokenClaims(
            subscriber_management_id=management_id,
            purpose=purpose,
            token_version=version,
            issued_at=datetime.fromtimestamp(issued_at_timestamp, timezone.utc),
            expires_at=datetime.fromtimestamp(expires_at_timestamp, timezone.utc),
        )


def newsletter_token_service_from_environment() -> NewsletterTokenService:
    secret = os.environ.get(NEWSLETTER_LINK_SECRET)
    if not secret:
        raise NewsletterTokenConfigurationError(
            "Newsletter link secret is not configured."
        )
    return NewsletterTokenService(secret)
