import os

import pytest
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


PRODUCTION_ORIGIN = "https://cheshiretoday.co.uk"
LOCAL_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)
PREFLIGHT_HEADERS = {
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "authorization,content-type",
}


@pytest.fixture
def client():
    test_client = TestClient(
        server.app,
        headers={"Accept-Encoding": "identity"},
    )
    try:
        yield test_client
    finally:
        test_client.close()


def _preflight(client, origin):
    return client.options(
        "/api/admin/verify",
        headers={"Origin": origin, **PREFLIGHT_HEADERS},
    )


def test_production_origin_is_allowed_for_authenticated_preflight(client):
    response = _preflight(client, PRODUCTION_ORIGIN)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == PRODUCTION_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"
    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed_headers
    assert "content-type" in allowed_headers


def test_arbitrary_origin_is_not_granted_browser_response_access(client):
    response = _preflight(client, "https://evil.example")

    allowed_origin = response.headers.get("access-control-allow-origin")
    assert allowed_origin != "https://evil.example"
    assert allowed_origin != "*"


@pytest.mark.parametrize("origin", LOCAL_ORIGINS)
def test_local_development_origin_is_allowed(client, origin):
    response = _preflight(client, origin)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_no_origin_health_request_is_unchanged(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "cheshire-news"}
    assert "access-control-allow-origin" not in response.headers


def test_public_api_route_remains_functional_for_approved_origin(client):
    response = client.get(
        "/api/",
        headers={"Origin": PRODUCTION_ORIGIN},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Cheshire News API"}
    assert response.headers["access-control-allow-origin"] == PRODUCTION_ORIGIN


def test_admin_authenticated_read_only_flow_remains_functional(client):
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    try:
        response = client.get(
            "/api/admin/verify",
            headers={"Origin": PRODUCTION_ORIGIN},
        )
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)

    assert response.status_code == 200
    assert response.json() == {"valid": True, "message": "Token is valid"}
    assert response.headers["access-control-allow-origin"] == PRODUCTION_ORIGIN


def test_effective_cors_policy_has_explicit_origins_and_no_regex():
    cors_entries = [
        middleware
        for middleware in server.app.user_middleware
        if middleware.cls is CORSMiddleware
    ]

    assert len(cors_entries) == 1
    policy = cors_entries[0].kwargs
    assert policy["allow_origins"] == [PRODUCTION_ORIGIN, *LOCAL_ORIGINS]
    assert "*" not in policy["allow_origins"]
    assert policy.get("allow_origin_regex") is None
    assert policy["allow_credentials"] is True
    assert policy["allow_methods"] == ["*"]
    assert policy["allow_headers"] == ["*"]
