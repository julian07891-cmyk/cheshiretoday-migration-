import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


REMOVED_ROUTES = (
    "/api/test-email",
    "/api/clean-all-articles",
    "/api/generate-from-headline",
)

AUTHENTICATED_REPLACEMENTS = (
    ("POST", "/api/send-digest-test"),
    ("POST", "/api/send-weekly-roundup-test"),
    ("POST", "/api/admin/send-campaign-email"),
    ("GET", "/api/admin/email-config/status"),
    ("GET", "/api/admin/email-config/validate-resend"),
    ("POST", "/api/admin/clean-content"),
)


def _routes(method, path):
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and method in getattr(route, "methods", set())
    ]


def _dependency_names(route):
    return {
        getattr(dependency.call, "__name__", "")
        for dependency in route.dependant.dependencies
    }


@pytest.mark.parametrize("path", REMOVED_ROUTES)
def test_legacy_operational_post_is_absent_from_routes_and_openapi(path):
    assert _routes("POST", path) == []

    isolated_app = FastAPI()
    isolated_app.include_router(server.api_router)
    assert "post" not in isolated_app.openapi().get("paths", {}).get(path, {})


@pytest.mark.parametrize("path", REMOVED_ROUTES)
def test_removed_path_returns_404_without_reaching_collaborators(monkeypatch, path):
    class UntouchedDatabase:
        def __init__(self):
            self.touched = False

        def __getattr__(self, name):
            self.touched = True
            raise AssertionError(
                f"database collaborator {name} must not be used for removed routes"
            )

    database = UntouchedDatabase()

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("removed-route collaborator must not be called")

    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server.email_service, "_send_email", fail_if_called)
    monkeypatch.setattr(server, "get_used_images_from_db", fail_if_called)
    monkeypatch.setattr(server, "generate_article_with_gemini", fail_if_called)
    monkeypatch.setattr(server, "get_dynamic_image", fail_if_called)

    isolated_app = FastAPI()
    isolated_app.include_router(server.api_router)
    response = TestClient(isolated_app).post(path)

    assert response.status_code == 404
    assert database.touched is False


@pytest.mark.parametrize("path", REMOVED_ROUTES)
def test_production_style_spa_catch_all_returns_405(path):
    response = TestClient(server.app).post(path)

    assert response.status_code == 405


@pytest.mark.parametrize("method,path", AUTHENTICATED_REPLACEMENTS)
def test_authenticated_replacement_remains_registered(method, path):
    routes = _routes(method, path)

    assert len(routes) == 1
    assert "get_admin_auth" in _dependency_names(routes[0])


def test_active_generation_editing_and_scheduler_paths_remain():
    assert len(_routes("POST", "/api/generate-articles")) == 1
    assert len(_routes("POST", "/api/import-hybrid-news")) == 1
    assert len(_routes("PUT", "/api/admin/articles/{article_id}")) == 1
    assert callable(server.daily_article_generation)
