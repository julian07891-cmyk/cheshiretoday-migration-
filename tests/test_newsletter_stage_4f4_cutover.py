import inspect
import os
from pathlib import Path

from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from backend.app import email_service as email_service_module


RETIRED_ROUTES = (
    ("GET", "/api/newsletter/preferences/reader%40example.com"),
    ("PUT", "/api/newsletter/preferences"),
    ("POST", "/api/newsletter/email-preferences"),
    ("PUT", "/api/newsletter/email-preferences"),
    ("GET", "/api/newsletter/email-preferences/reader%40example.com"),
    ("POST", "/api/newsletter/unsubscribe"),
)

SECURE_ROUTES = (
    ("POST", "/api/newsletter/preferences/verify"),
    ("PUT", "/api/newsletter/preferences/secure"),
    ("POST", "/api/newsletter/preferences/request-link"),
    ("POST", "/api/newsletter/unsubscribe/confirm"),
    ("POST", "/api/newsletter/unsubscribe/one-click"),
    ("POST", "/api/newsletter/unsubscribe/request-link"),
    ("POST", "/api/newsletter/reactivate/request-link"),
    ("POST", "/api/newsletter/reactivate/confirm"),
)


def _registrations(method, path):
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and method in getattr(route, "methods", set())
    ]


def test_retired_email_only_routes_are_absent_and_unreachable():
    client = TestClient(server.app)
    openapi_paths = server.app.openapi()["paths"]

    assert "/api/newsletter/preferences/{email}" not in openapi_paths
    assert "/api/newsletter/preferences" not in openapi_paths
    assert "/api/newsletter/email-preferences" not in openapi_paths
    assert "/api/newsletter/email-preferences/{email}" not in openapi_paths
    assert "/api/newsletter/unsubscribe" not in openapi_paths

    for method, path in RETIRED_ROUTES:
        response = client.request(method, path, json={"email": "reader@example.com"})
        assert response.status_code in {404, 405}


def test_secure_and_signup_routes_remain_registered_once():
    for method, path in SECURE_ROUTES:
        assert len(_registrations(method, path)) == 1
    assert len(_registrations("POST", "/api/subscribe")) == 1
    assert len(_registrations("POST", "/api/newsletter/subscribe")) == 1


def test_authenticated_admin_subscriber_routes_remain_registered():
    assert len(_registrations("GET", "/api/admin/subscribers")) == 1
    assert len(_registrations("GET", "/api/admin/subscribers/cold-report")) == 1
    assert len(_registrations("DELETE", "/api/admin/subscribers/{email}")) == 1


def test_gates_are_enabled():
    assert server.NEWSLETTER_REQUEST_LINKS_ENABLED is True
    assert server.NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is True
    source = inspect.getsource(server)
    assert "NEWSLETTER_REQUEST_LINKS_ENABLED = True" in source
    assert "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED = True" in source


def test_routine_management_urls_are_clean_and_untracked():
    source = Path(email_service_module.__file__).read_text(encoding="utf-8")
    server_source = Path(server.__file__).read_text(encoding="utf-8")

    for text in (source, server_source):
        assert "/newsletter/preferences?email=" not in text
        assert "/unsubscribe?email=" not in text
    assert '_get_tracked_url(tracking_id, prefs_url)' not in source
    assert '_get_tracked_url(tracking_id, unsub_url)' not in source
    assert '_get_tracked_url(recipient_tracking_id, prefs_url)' not in source
    assert '_get_tracked_url(recipient_tracking_id, unsub_url)' not in source


def test_outbound_one_click_headers_remain_fail_closed_pending_challenges():
    source = Path(email_service_module.__file__).read_text(encoding="utf-8")

    assert '"List-Unsubscribe"' not in source
    assert '"List-Unsubscribe-Post"' not in source
    assert "newsletter/unsubscribe/one-click?token=" not in source
