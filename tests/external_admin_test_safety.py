"""Production-safety boundary for legacy HTTP integration tests."""

import os
from urllib.parse import urlparse

import pytest
import requests


_DEFAULT_TEST_USERNAME = "qa-admin@example.invalid"
_DEFAULT_TEST_PASSWORD = "local-test-password-not-a-secret"
_ALLOWED_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


class UnsafeTestTarget(ValueError):
    """Raised before a test can contact a non-loopback HTTP target."""


def validate_loopback_test_url(url: str) -> str:
    """Return a normalised HTTP(S) URL only when its host is loopback."""
    parsed = urlparse(str(url or "").strip())
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeTestTarget("test target must use an explicit HTTP(S) scheme")
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise UnsafeTestTarget("test target must not contain credentials or an invalid host")
    try:
        parsed.port
    except ValueError as exc:
        raise UnsafeTestTarget("test target contains an invalid port") from exc
    if parsed.query or parsed.fragment:
        raise UnsafeTestTarget("test target must not contain a query or fragment")

    if parsed.hostname.lower() not in _ALLOWED_LOOPBACK_HOSTS:
        raise UnsafeTestTarget("test target host is not an approved loopback host")

    return str(url).strip().rstrip("/")


def get_local_test_base_url(environment_name: str = "REACT_APP_BACKEND_URL") -> str:
    """Skip the importing test module unless its configured target is loopback."""
    value = os.environ.get(environment_name, "")
    try:
        return validate_loopback_test_url(value)
    except UnsafeTestTarget as exc:
        pytest.skip(
            f"HTTP integration tests require an explicit loopback target: {exc}",
            allow_module_level=True,
        )


class LoopbackOnlySession(requests.Session):
    """Requests session that refuses external targets and never follows redirects."""

    def request(self, method, url, **kwargs):
        try:
            validate_loopback_test_url(url)
        except UnsafeTestTarget as exc:
            pytest.skip(f"HTTP integration request requires a loopback target: {exc}")
        kwargs["allow_redirects"] = False
        return super().request(method, url, **kwargs)


def get_local_test_session() -> LoopbackOnlySession:
    return LoopbackOnlySession()


def get_local_admin_test_credentials(base_url: str) -> dict[str, str]:
    """Return test-only credentials after proving the target is loopback."""
    try:
        validate_loopback_test_url(base_url)
    except UnsafeTestTarget as exc:
        pytest.skip(f"Admin test credentials require a loopback target: {exc}")

    return {
        "username": os.environ.get("CT_TEST_ADMIN_USERNAME", _DEFAULT_TEST_USERNAME),
        "password": os.environ.get("CT_TEST_ADMIN_PASSWORD", _DEFAULT_TEST_PASSWORD),
    }
