"""Safety boundary for legacy external Admin integration tests."""

import os
from urllib.parse import urlparse

import pytest


_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
_DEFAULT_TEST_USERNAME = "qa-admin@example.invalid"
_DEFAULT_TEST_PASSWORD = "local-test-password-not-a-secret"


def get_local_admin_test_credentials(base_url: str) -> dict[str, str]:
    """Return test-only credentials after proving the target is loopback."""
    parsed = urlparse(str(base_url or "").strip())
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in _LOOPBACK_HOSTS:
        pytest.skip(
            "External Admin authentication tests require an explicit loopback API target"
        )

    return {
        "username": os.environ.get("CT_TEST_ADMIN_USERNAME", _DEFAULT_TEST_USERNAME),
        "password": os.environ.get("CT_TEST_ADMIN_PASSWORD", _DEFAULT_TEST_PASSWORD),
    }
