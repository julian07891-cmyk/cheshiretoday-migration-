"""Regression coverage for the HTTP integration-test production boundary."""

from unittest.mock import Mock

import pytest
import requests

from tests import external_admin_test_safety as safety


@pytest.mark.parametrize(
    ("target", "expected"),
    (
        ("http://localhost", "http://localhost"),
        ("https://localhost:8443/", "https://localhost:8443"),
        ("http://127.0.0.1", "http://127.0.0.1"),
        ("http://[::1]:8000", "http://[::1]:8000"),
    ),
)
def test_loopback_targets_are_allowed(target, expected):
    assert safety.validate_loopback_test_url(target) == expected


@pytest.mark.parametrize(
    "target",
    (
        "",
        "localhost:8000",
        "not a url",
        "https://cheshiretoday.co.uk",
        "https://www.cheshiretoday.co.uk",
        "https://example.onrender.com",
        "http://8.8.8.8",
        "http://127.0.0.2",
        "http://2001:4860:4860::8888",
        "http://localhost.example.com",
        "http://127.0.0.1.example.com",
        "http://user:password@localhost:8000",
        "ftp://localhost/file",
    ),
)
def test_unsafe_or_ambiguous_targets_are_rejected(target):
    with pytest.raises(safety.UnsafeTestTarget):
        safety.validate_loopback_test_url(target)


def test_default_configuration_skips_before_creating_a_target(monkeypatch):
    monkeypatch.delenv("REACT_APP_BACKEND_URL", raising=False)
    with pytest.raises(pytest.skip.Exception):
        safety.get_local_test_base_url()


def test_mutating_external_request_is_refused_before_transport(monkeypatch):
    transport = Mock(side_effect=AssertionError("transport must not run"))
    monkeypatch.setattr(requests.Session, "request", transport)
    with pytest.raises(pytest.skip.Exception):
        safety.get_local_test_session().post(
            "https://cheshiretoday.co.uk/api/admin/login", json={}
        )
    transport.assert_not_called()


def test_credentials_are_not_read_before_target_approval(monkeypatch):
    def fail_if_read(*_args, **_kwargs):
        raise AssertionError("credential environment was read")

    monkeypatch.setattr(safety.os.environ, "get", fail_if_read)
    with pytest.raises(pytest.skip.Exception):
        safety.get_local_admin_test_credentials("https://example.onrender.com")


def test_redirects_are_not_followed(monkeypatch):
    redirect = requests.Response()
    redirect.status_code = 302
    redirect.headers["Location"] = "https://cheshiretoday.co.uk/api/articles"
    transport = Mock(return_value=redirect)
    monkeypatch.setattr(requests.Session, "request", transport)

    response = safety.get_local_test_session().get("http://localhost:8000/start")

    assert response.status_code == 302
    transport.assert_called_once()
    assert transport.call_args.kwargs["allow_redirects"] is False
