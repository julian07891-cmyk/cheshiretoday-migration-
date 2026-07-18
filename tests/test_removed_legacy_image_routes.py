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
    "/api/update-local-news-images",
    "/api/reassign-all-images-uk",
    "/api/fix-all-images-uk",
)


def _routes(method, path):
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and method in getattr(route, "methods", set())
    ]


@pytest.mark.parametrize("path", REMOVED_ROUTES)
def test_legacy_image_route_is_not_registered(path):
    assert _routes("POST", path) == []


@pytest.mark.parametrize("path", REMOVED_ROUTES)
def test_legacy_image_route_returns_404_without_using_collaborators(
    monkeypatch,
    path,
):
    class UntouchedDatabase:
        def __init__(self):
            self.touched = False

        def __getattr__(self, name):
            self.touched = True
            raise AssertionError(
                f"database collaborator {name} must not be used for removed routes"
            )

    database = UntouchedDatabase()

    def fail_if_image_helper_runs(*_args, **_kwargs):
        raise AssertionError("image helpers must not run for removed routes")

    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "get_dynamic_image", fail_if_image_helper_runs)
    monkeypatch.setattr(server, "select_unique_image", fail_if_image_helper_runs)
    monkeypatch.setattr(server, "auto_fix_duplicate_images", fail_if_image_helper_runs)

    isolated_app = FastAPI()
    isolated_app.include_router(server.api_router)
    response = TestClient(isolated_app).post(path)

    assert response.status_code == 404
    assert database.touched is False


def test_active_article_and_rss_routes_remain_registered():
    assert len(_routes("GET", "/api/articles")) == 1
    assert len(_routes("GET", "/api/rss/rss-sources")) == 1
    assert len(_routes("GET", "/api/rss/feed.xml")) == 1


def test_active_image_helpers_remain_importable():
    assert callable(server.get_dynamic_image)
    assert callable(server.select_unique_image)
    assert callable(server.auto_fix_duplicate_images)
