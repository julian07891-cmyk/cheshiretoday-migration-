import base64
import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import pytest

from backend.app.newsletter_token_service import (
    ALLOWED_PURPOSES,
    COMPATIBILITY_PREFERENCE_TOKEN_SECONDS,
    COMPATIBILITY_UNSUBSCRIBE_TOKEN_SECONDS,
    EXPIRY_PROFILE_SECONDS,
    JWT_ALGORITHM,
    NEWSLETTER_LINK_SECRET,
    NEWSLETTER_PREFERENCE_TOKEN_SECONDS,
    NEWSLETTER_UNSUBSCRIBE_TOKEN_SECONDS,
    PURPOSE_EXPIRY_PROFILES,
    REACTIVATION_TOKEN_SECONDS,
    TOKEN_CLOCK_SKEW_SECONDS,
    WEBSITE_PREFERENCE_TOKEN_SECONDS,
    WEBSITE_UNSUBSCRIBE_TOKEN_SECONDS,
    ExpiredNewsletterTokenError,
    InvalidNewsletterTokenError,
    NewsletterTokenClaims,
    NewsletterTokenConfigurationError,
    NewsletterTokenExpiryProfileMismatchError,
    NewsletterTokenExpiryProfile,
    NewsletterTokenService,
    NewsletterTokenVersionMismatchError,
    WrongNewsletterTokenPurposeError,
    newsletter_token_service_from_environment,
    token_fingerprint,
)


NOW = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
MANAGEMENT_ID = "123e4567-e89b-42d3-a456-426614174000"
UUID_V1 = "123e4567-e89b-12d3-a456-426614174000"
STRONG_SECRET = "A" * 43
OTHER_STRONG_SECRET = "B" * 43
EXACT_CLAIMS = {"sub", "purpose", "ver", "iat", "exp"}


@pytest.fixture
def service():
    return NewsletterTokenService(STRONG_SECRET)


def _payload(
    *,
    purpose="preferences",
    management_id=MANAGEMENT_ID,
    version=1,
    issued_at=None,
    expires_at=None,
    extra=None,
):
    issued_at = int((issued_at or NOW).timestamp())
    expires_at = expires_at if expires_at is not None else issued_at + 1800
    payload = {
        "sub": management_id,
        "purpose": purpose,
        "ver": version,
        "iat": issued_at,
        "exp": expires_at,
    }
    if extra:
        payload.update(extra)
    return payload


def _sign(payload, secret=STRONG_SECRET, algorithm="HS256", headers=None):
    return jwt.encode(
        payload,
        secret,
        algorithm=algorithm,
        headers=headers or {"alg": algorithm, "typ": "JWT"},
    )


def _decode_segment(segment):
    padded = segment + "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))


@pytest.mark.parametrize(
    ("purpose", "profile"),
    [
        ("preferences", NewsletterTokenExpiryProfile.NEWSLETTER_PREFERENCES),
        ("unsubscribe", NewsletterTokenExpiryProfile.NEWSLETTER_UNSUBSCRIBE),
        ("reactivate", NewsletterTokenExpiryProfile.REACTIVATION),
    ],
)
def test_each_purpose_round_trips_with_typed_immutable_claims(
    service, purpose, profile
):
    token = service.issue_newsletter_token(MANAGEMENT_ID, purpose, 7, profile, NOW)
    claims = service.verify_newsletter_token(token, purpose, 7, NOW)

    assert claims == NewsletterTokenClaims(
        subscriber_management_id=MANAGEMENT_ID,
        purpose=purpose,
        token_version=7,
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=EXPIRY_PROFILE_SECONDS[profile]),
    )
    with pytest.raises(FrozenInstanceError):
        claims.token_version = 8


@pytest.mark.parametrize("profile", list(NewsletterTokenExpiryProfile))
def test_every_approved_expiry_profile_uses_its_exact_lifetime(service, profile):
    purpose = (
        "unsubscribe"
        if "unsubscribe" in profile.value
        else "reactivate"
        if profile is NewsletterTokenExpiryProfile.REACTIVATION
        else "preferences"
    )
    token = service.issue_newsletter_token(MANAGEMENT_ID, purpose, 1, profile, NOW)
    payload = jwt.decode(
        token,
        STRONG_SECRET,
        algorithms=["HS256"],
        options={"verify_exp": False, "verify_iat": False},
    )
    assert payload["exp"] - payload["iat"] == EXPIRY_PROFILE_SECONDS[profile]


@pytest.mark.parametrize(
    ("purpose", "profile"),
    [
        ("preferences", NewsletterTokenExpiryProfile.NEWSLETTER_PREFERENCES),
        ("preferences", NewsletterTokenExpiryProfile.WEBSITE_PREFERENCES),
        ("preferences", NewsletterTokenExpiryProfile.COMPATIBILITY_PREFERENCES),
        ("unsubscribe", NewsletterTokenExpiryProfile.NEWSLETTER_UNSUBSCRIBE),
        ("unsubscribe", NewsletterTokenExpiryProfile.WEBSITE_UNSUBSCRIBE),
        ("unsubscribe", NewsletterTokenExpiryProfile.COMPATIBILITY_UNSUBSCRIBE),
        ("reactivate", NewsletterTokenExpiryProfile.REACTIVATION),
    ],
)
def test_every_approved_purpose_profile_pair_issues_and_verifies(
    service, purpose, profile
):
    token = service.issue_newsletter_token(MANAGEMENT_ID, purpose, 3, profile, NOW)
    claims = service.verify_newsletter_token(token, purpose, 3, NOW)

    assert claims.purpose == purpose
    assert claims.expires_at - claims.issued_at == timedelta(
        seconds=EXPIRY_PROFILE_SECONDS[profile]
    )


@pytest.mark.parametrize(
    ("purpose", "profile"),
    [
        ("preferences", NewsletterTokenExpiryProfile.NEWSLETTER_UNSUBSCRIBE),
        ("preferences", NewsletterTokenExpiryProfile.WEBSITE_UNSUBSCRIBE),
        ("preferences", NewsletterTokenExpiryProfile.COMPATIBILITY_UNSUBSCRIBE),
        ("preferences", NewsletterTokenExpiryProfile.REACTIVATION),
        ("unsubscribe", NewsletterTokenExpiryProfile.NEWSLETTER_PREFERENCES),
        ("unsubscribe", NewsletterTokenExpiryProfile.WEBSITE_PREFERENCES),
        ("unsubscribe", NewsletterTokenExpiryProfile.COMPATIBILITY_PREFERENCES),
        ("unsubscribe", NewsletterTokenExpiryProfile.REACTIVATION),
        ("reactivate", NewsletterTokenExpiryProfile.NEWSLETTER_PREFERENCES),
        ("reactivate", NewsletterTokenExpiryProfile.WEBSITE_PREFERENCES),
        ("reactivate", NewsletterTokenExpiryProfile.COMPATIBILITY_PREFERENCES),
        ("reactivate", NewsletterTokenExpiryProfile.NEWSLETTER_UNSUBSCRIBE),
        ("reactivate", NewsletterTokenExpiryProfile.WEBSITE_UNSUBSCRIBE),
        ("reactivate", NewsletterTokenExpiryProfile.COMPATIBILITY_UNSUBSCRIBE),
    ],
)
def test_invalid_purpose_profile_pair_fails_closed_without_sensitive_output(
    service, purpose, profile
):
    issued_token = None
    with pytest.raises(NewsletterTokenExpiryProfileMismatchError) as captured:
        issued_token = service.issue_newsletter_token(
            MANAGEMENT_ID, purpose, 1, profile, NOW
        )

    message = str(captured.value)
    assert issued_token is None
    assert MANAGEMENT_ID not in message
    assert STRONG_SECRET not in message
    assert purpose not in message
    assert profile.value not in message
    assert message.count(".") < 2


def test_approved_purpose_profile_mapping_is_exact_and_immutable():
    assert PURPOSE_EXPIRY_PROFILES == {
        "preferences": {
            NewsletterTokenExpiryProfile.NEWSLETTER_PREFERENCES,
            NewsletterTokenExpiryProfile.WEBSITE_PREFERENCES,
            NewsletterTokenExpiryProfile.COMPATIBILITY_PREFERENCES,
        },
        "unsubscribe": {
            NewsletterTokenExpiryProfile.NEWSLETTER_UNSUBSCRIBE,
            NewsletterTokenExpiryProfile.WEBSITE_UNSUBSCRIBE,
            NewsletterTokenExpiryProfile.COMPATIBILITY_UNSUBSCRIBE,
        },
        "reactivate": {NewsletterTokenExpiryProfile.REACTIVATION},
    }
    with pytest.raises(TypeError):
        PURPOSE_EXPIRY_PROFILES["preferences"] = frozenset()


def test_expiry_constants_are_frozen_to_the_approved_values():
    assert NEWSLETTER_PREFERENCE_TOKEN_SECONDS == 30 * 24 * 60 * 60
    assert NEWSLETTER_UNSUBSCRIBE_TOKEN_SECONDS == 180 * 24 * 60 * 60
    assert WEBSITE_PREFERENCE_TOKEN_SECONDS == 30 * 60
    assert COMPATIBILITY_PREFERENCE_TOKEN_SECONDS == 30 * 60
    assert WEBSITE_UNSUBSCRIBE_TOKEN_SECONDS == 30 * 60
    assert COMPATIBILITY_UNSUBSCRIBE_TOKEN_SECONDS == 30 * 60
    assert REACTIVATION_TOKEN_SECONDS == 30 * 60


def test_issued_token_has_exact_claims_safe_header_and_no_private_data(service):
    token = service.issue_newsletter_token(
        MANAGEMENT_ID,
        "preferences",
        2,
        NewsletterTokenExpiryProfile.NEWSLETTER_PREFERENCES,
        NOW,
    )
    header_segment, payload_segment, _ = token.split(".")
    header = _decode_segment(header_segment)
    payload = _decode_segment(payload_segment)

    assert header == {"alg": "HS256", "typ": "JWT"}
    assert set(payload) == EXACT_CLAIMS
    serialized = json.dumps(payload)
    for forbidden in (
        "email",
        "name",
        "active",
        "mongo",
        "tracking",
        "admin",
        "commenter",
    ):
        assert forbidden not in serialized.lower()


@pytest.mark.parametrize("claim", sorted(EXACT_CLAIMS))
def test_missing_claim_is_rejected(service, claim):
    payload = _payload()
    del payload[claim]
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(
            _sign(payload), "preferences", now=NOW
        )


def test_extra_claim_is_rejected(service):
    token = _sign(_payload(extra={"email": "private@example.invalid"}))
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(token, "preferences", now=NOW)


def test_hs256_signature_succeeds(service):
    token = _sign(_payload(), algorithm=JWT_ALGORITHM)
    assert service.verify_newsletter_token(
        token, "preferences", now=NOW
    ).purpose == "preferences"


def test_unsupported_algorithm_is_rejected(service):
    token = jwt.encode(
        _payload(),
        "C" * 64,
        algorithm="HS512",
        headers={"alg": "HS512", "typ": "JWT"},
    )
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(token, "preferences", now=NOW)


def test_none_algorithm_is_rejected(service):
    token = jwt.encode(
        _payload(), key="", algorithm="none", headers={"alg": "none", "typ": "JWT"}
    )
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(token, "preferences", now=NOW)


def test_tampered_payload_is_rejected(service):
    token = _sign(_payload())
    header, payload, signature = token.split(".")
    decoded = _decode_segment(payload)
    decoded["ver"] = 9
    altered = base64.urlsafe_b64encode(
        json.dumps(decoded, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(
            f"{header}.{altered}.{signature}", "preferences", now=NOW
        )


def test_tampered_signature_is_rejected(service):
    token = _sign(_payload())
    altered = f"{token[:-1]}{'A' if token[-1] != 'A' else 'B'}"
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(altered, "preferences", now=NOW)


def test_wrong_secret_is_rejected():
    token = _sign(_payload())
    with pytest.raises(InvalidNewsletterTokenError):
        NewsletterTokenService(OTHER_STRONG_SECRET).verify_newsletter_token(
            token, "preferences", now=NOW
        )


@pytest.mark.parametrize(
    ("issued_purpose", "expected_purpose"),
    [
        ("preferences", "unsubscribe"),
        ("preferences", "reactivate"),
        ("unsubscribe", "preferences"),
        ("unsubscribe", "reactivate"),
        ("reactivate", "preferences"),
        ("reactivate", "unsubscribe"),
    ],
)
def test_purpose_isolation(service, issued_purpose, expected_purpose):
    token = _sign(_payload(purpose=issued_purpose))
    with pytest.raises(WrongNewsletterTokenPurposeError):
        service.verify_newsletter_token(token, expected_purpose, now=NOW)


def test_unknown_purpose_is_rejected_during_issuance(service):
    with pytest.raises(InvalidNewsletterTokenError):
        service.issue_newsletter_token(
            MANAGEMENT_ID,
            "admin",
            1,
            NewsletterTokenExpiryProfile.NEWSLETTER_PREFERENCES,
            NOW,
        )


def test_unknown_purpose_in_forged_token_is_rejected(service):
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(
            _sign(_payload(purpose="admin")), "preferences", now=NOW
        )


@pytest.mark.parametrize(
    "management_id",
    ["not-a-uuid", UUID_V1, MANAGEMENT_ID.upper(), f"{{{MANAGEMENT_ID}}}"],
)
def test_invalid_non_v4_or_noncanonical_management_id_is_rejected(
    service, management_id
):
    with pytest.raises(InvalidNewsletterTokenError):
        service.issue_newsletter_token(
            management_id,
            "preferences",
            1,
            NewsletterTokenExpiryProfile.NEWSLETTER_PREFERENCES,
            NOW,
        )


def test_forged_invalid_management_id_is_rejected(service):
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(
            _sign(_payload(management_id="not-a-uuid")),
            "preferences",
            now=NOW,
        )


def test_canonical_uuid4_is_accepted(service):
    assert UUID(MANAGEMENT_ID).version == 4
    token = service.issue_newsletter_token(
        MANAGEMENT_ID,
        "preferences",
        1,
        NewsletterTokenExpiryProfile.WEBSITE_PREFERENCES,
        NOW,
    )
    assert (
        service.verify_newsletter_token(token, "preferences", now=NOW)
        .subscriber_management_id
        == MANAGEMENT_ID
    )


@pytest.mark.parametrize("version", [0, -1, True, "1"])
def test_invalid_version_is_rejected_during_issuance(service, version):
    with pytest.raises(InvalidNewsletterTokenError):
        service.issue_newsletter_token(
            MANAGEMENT_ID,
            "preferences",
            version,
            NewsletterTokenExpiryProfile.WEBSITE_PREFERENCES,
            NOW,
        )


@pytest.mark.parametrize("version", [0, -1, True, "1"])
def test_invalid_version_in_forged_token_is_rejected(service, version):
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(
            _sign(_payload(version=version)), "preferences", now=NOW
        )


def test_version_match_and_mismatch(service):
    token = _sign(_payload(version=4))
    assert service.verify_newsletter_token(
        token, "preferences", expected_token_version=4, now=NOW
    ).token_version == 4
    with pytest.raises(NewsletterTokenVersionMismatchError):
        service.verify_newsletter_token(
            token, "preferences", expected_token_version=5, now=NOW
        )


@pytest.mark.parametrize("claim", ["iat", "exp"])
@pytest.mark.parametrize("bad_timestamp", [True, 1.5, "1"])
def test_non_integer_timestamps_are_rejected(service, claim, bad_timestamp):
    payload = _payload()
    payload[claim] = bad_timestamp
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(
            _sign(payload), "preferences", now=NOW
        )


def test_exp_equal_to_iat_is_rejected(service):
    timestamp = int(NOW.timestamp())
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(
            _sign(_payload(expires_at=timestamp)), "preferences", now=NOW
        )


def test_expired_token_and_clock_skew_boundary(service):
    within_skew = _sign(
        _payload(
            issued_at=NOW - timedelta(minutes=2),
            expires_at=int((NOW - timedelta(seconds=60)).timestamp()),
        )
    )
    beyond_skew = _sign(
        _payload(
            issued_at=NOW - timedelta(minutes=2),
            expires_at=int((NOW - timedelta(seconds=61)).timestamp()),
        )
    )
    assert service.verify_newsletter_token(
        within_skew, "preferences", now=NOW
    ).purpose == "preferences"
    with pytest.raises(ExpiredNewsletterTokenError):
        service.verify_newsletter_token(beyond_skew, "preferences", now=NOW)


def test_future_iat_clock_skew_boundary(service):
    within_skew = _sign(
        _payload(
            issued_at=NOW + timedelta(seconds=60),
            expires_at=int((NOW + timedelta(minutes=31)).timestamp()),
        )
    )
    beyond_skew = _sign(
        _payload(
            issued_at=NOW + timedelta(seconds=61),
            expires_at=int((NOW + timedelta(minutes=31)).timestamp()),
        )
    )
    assert TOKEN_CLOCK_SKEW_SECONDS == 60
    assert service.verify_newsletter_token(
        within_skew, "preferences", now=NOW
    ).purpose == "preferences"
    with pytest.raises(InvalidNewsletterTokenError):
        service.verify_newsletter_token(beyond_skew, "preferences", now=NOW)


def test_naive_and_non_utc_now_are_rejected(service):
    with pytest.raises(ValueError):
        service.issue_newsletter_token(
            MANAGEMENT_ID,
            "preferences",
            1,
            NewsletterTokenExpiryProfile.WEBSITE_PREFERENCES,
            NOW.replace(tzinfo=None),
        )
    with pytest.raises(ValueError):
        service.verify_newsletter_token(
            _sign(_payload()),
            "preferences",
            now=NOW.astimezone(timezone(timedelta(hours=1))),
        )


def test_unapproved_expiry_profile_is_rejected(service):
    with pytest.raises(ValueError):
        service.issue_newsletter_token(
            MANAGEMENT_ID, "preferences", 1, "arbitrary", NOW
        )


@pytest.mark.parametrize("secret", [b"", b"A" * 31, "", "A" * 42, "!" * 43])
def test_missing_empty_or_weak_constructor_secret_fails_closed(secret):
    with pytest.raises(NewsletterTokenConfigurationError):
        NewsletterTokenService(secret)


def test_known_32_byte_test_secret_and_strong_string_are_accepted():
    NewsletterTokenService(b"T" * 32)
    NewsletterTokenService(STRONG_SECRET)


@pytest.mark.parametrize("missing_value", [None, ""])
def test_environment_factory_fails_closed_for_missing_or_empty_secret(
    monkeypatch, missing_value
):
    if missing_value is None:
        monkeypatch.delenv(NEWSLETTER_LINK_SECRET, raising=False)
    else:
        monkeypatch.setenv(NEWSLETTER_LINK_SECRET, missing_value)
    with pytest.raises(NewsletterTokenConfigurationError):
        newsletter_token_service_from_environment()


def test_environment_factory_rejects_weak_and_accepts_strong_secret(monkeypatch):
    monkeypatch.setenv(NEWSLETTER_LINK_SECRET, "weak")
    with pytest.raises(NewsletterTokenConfigurationError):
        newsletter_token_service_from_environment()
    monkeypatch.setenv(NEWSLETTER_LINK_SECRET, STRONG_SECRET)
    assert isinstance(newsletter_token_service_from_environment(), NewsletterTokenService)


def test_fingerprint_is_short_hex_and_deterministic():
    first = token_fingerprint("example-token")
    second = token_fingerprint("example-token")
    assert first == second
    assert len(first) <= 12
    assert all(character in "0123456789abcdef" for character in first)


def test_errors_do_not_expose_sensitive_inputs(service):
    raw_token = _sign(_payload(extra={"private": "decoded-secret"}))
    subscriber_id = MANAGEMENT_ID
    secret = STRONG_SECRET
    with pytest.raises(InvalidNewsletterTokenError) as captured:
        service.verify_newsletter_token(raw_token, "preferences", now=NOW)
    message = str(captured.value)
    assert raw_token not in message
    assert subscriber_id not in message
    assert secret not in message
    assert "decoded-secret" not in message
    assert token_fingerprint(raw_token) not in message


def test_allowed_purposes_are_exact():
    assert ALLOWED_PURPOSES == {"preferences", "unsubscribe", "reactivate"}
