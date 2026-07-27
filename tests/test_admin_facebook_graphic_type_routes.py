import os
from copy import deepcopy

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from app.facebook_social_asset import ArticleValidationError, ImageContentError


ARTICLE_ID = "507f1f77bcf86cd799439011"
ARTICLE = {
    "_id": ObjectId(ARTICLE_ID),
    "title": "Cheshire investment creates new jobs",
    "category": "Business",
    "image": "https://images.example.test/story.jpg",
}
SVG = b'<svg width="1200" height="630" viewBox="0 0 1200 630"/>'


class ReadOnlyArticles:
    def __init__(self, article=ARTICLE):
        self.article = deepcopy(article)
        self.calls = []

    async def find_one(self, query, projection):
        self.calls.append((deepcopy(query), deepcopy(projection)))
        if self.article is None:
            return None
        if self.article.get("archived") is True:
            return None
        if self.article.get("manual_review_hidden_from_public") is True:
            return None
        return deepcopy(self.article)

    def __getattr__(self, name):
        if any(token in name for token in ("insert", "update", "delete", "replace")):
            raise AssertionError(f"database write attempted: {name}")
        raise AttributeError(name)


def call(monkeypatch, path, *, method="get", body=None, article=ARTICLE, composer=None):
    collection = ReadOnlyArticles(article)
    monkeypatch.setattr(server.db, "articles", collection)
    if composer is not None:
        monkeypatch.setattr(server, "compose_facebook_graphic_svg", composer)
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    try:
        client_method = getattr(TestClient(server.app), method)
        if method == "post":
            response = client_method(path, json=body, headers={"Accept-Encoding": "identity"})
        else:
            response = client_method(path, headers={"Accept-Encoding": "identity"})
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)
    return response, collection


@pytest.mark.parametrize("graphic_type", ["business", "property", "ai-tech", "breaking-news", "event"])
def test_article_type_routes_are_authenticated_read_only_no_store(monkeypatch, graphic_type):
    records = []
    response, collection = call(
        monkeypatch,
        f"/api/admin/social-assets/facebook/article/{graphic_type}/{ARTICLE_ID}",
        composer=lambda article, selected, **kwargs: records.append((article, selected, kwargs)) or SVG,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "no-store"
    assert records == [({"mongo_id": ARTICLE_ID, "title": ARTICLE["title"], "category": "Business", "image": ARTICLE["image"]}, graphic_type, {})]
    assert len(collection.calls) == 1


def test_unauthenticated_request_stops_before_database_and_composer(monkeypatch):
    collection = ReadOnlyArticles()
    monkeypatch.setattr(server.db, "articles", collection)
    monkeypatch.setattr(server, "compose_facebook_graphic_svg", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("composer called")))
    response = TestClient(server.app).get(
        f"/api/admin/social-assets/facebook/article/business/{ARTICLE_ID}",
        headers={"Accept-Encoding": "identity"},
    )
    assert response.status_code == 401
    assert collection.calls == []


@pytest.mark.parametrize(
    ("path", "body"),
    [
        (f"/api/admin/social-assets/facebook/quote/{ARTICLE_ID}", {"quote": "Verified", "attribution": "Source"}),
        (f"/api/admin/social-assets/facebook/poll/{ARTICLE_ID}", {"question": "Your view?", "option_a": "Yes", "option_b": "No"}),
    ],
)
def test_unauthenticated_editor_routes_stop_before_database_and_composer(monkeypatch, path, body):
    collection = ReadOnlyArticles()
    monkeypatch.setattr(server.db, "articles", collection)
    monkeypatch.setattr(server, "compose_facebook_graphic_svg", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("composer called")))
    response = TestClient(server.app).post(path, json=body, headers={"Accept-Encoding": "identity"})
    assert response.status_code == 401
    assert collection.calls == []


def test_malformed_article_id_stops_before_database(monkeypatch):
    collection = ReadOnlyArticles()
    monkeypatch.setattr(server.db, "articles", collection)
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    try:
        response = TestClient(server.app).get(
            "/api/admin/social-assets/facebook/article/business/not-an-object-id",
            headers={"Accept-Encoding": "identity"},
        )
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)
    assert response.status_code == 400
    assert collection.calls == []


@pytest.mark.parametrize(
    "article",
    [
        {**ARTICLE, "archived": True},
        {**ARTICLE, "manual_review_hidden_from_public": True},
    ],
)
def test_archived_and_manual_review_articles_are_not_available(monkeypatch, article):
    response, collection = call(
        monkeypatch,
        f"/api/admin/social-assets/facebook/article/business/{ARTICLE_ID}",
        article=article,
    )
    assert response.status_code == 404
    assert len(collection.calls) == 1


def test_missing_article_and_invalid_image_map_safely(monkeypatch):
    response, _ = call(monkeypatch, f"/api/admin/social-assets/facebook/article/business/{ARTICLE_ID}", article=None)
    assert response.status_code == 404
    response, _ = call(
        monkeypatch,
        f"/api/admin/social-assets/facebook/article/business/{ARTICLE_ID}",
        composer=lambda *args, **kwargs: (_ for _ in ()).throw(ImageContentError("private")),
    )
    assert response.status_code == 422
    assert "private" not in response.text


def test_wrong_category_maps_to_safe_400(monkeypatch):
    response, _ = call(
        monkeypatch,
        f"/api/admin/social-assets/facebook/article/property/{ARTICLE_ID}",
        composer=lambda *args, **kwargs: (_ for _ in ()).throw(ArticleValidationError("private")),
    )
    assert response.status_code == 400
    assert "private" not in response.text


def test_template_or_composition_failure_maps_to_safe_500(monkeypatch):
    response, _ = call(
        monkeypatch,
        f"/api/admin/social-assets/facebook/article/business/{ARTICLE_ID}",
        composer=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("private template path")),
    )
    assert response.status_code == 500
    assert "private template path" not in response.text


def test_quote_route_accepts_only_quote_and_attribution(monkeypatch):
    captured = []
    response, _ = call(
        monkeypatch,
        f"/api/admin/social-assets/facebook/quote/{ARTICLE_ID}",
        method="post",
        body={"quote": "Verified & exact", "attribution": "Named source"},
        composer=lambda article, selected, **kwargs: captured.append((selected, kwargs)) or SVG,
    )
    assert response.status_code == 200
    assert captured == [("quote", {"quote": "Verified & exact", "attribution": "Named source"})]
    rejected, _ = call(
        monkeypatch,
        f"/api/admin/social-assets/facebook/quote/{ARTICLE_ID}",
        method="post",
        body={"quote": "Verified", "attribution": "Source", "template": "/tmp/evil.svg"},
        composer=lambda *args, **kwargs: SVG,
    )
    assert rejected.status_code == 422


def test_poll_route_accepts_exactly_two_options(monkeypatch):
    captured = []
    response, _ = call(
        monkeypatch,
        f"/api/admin/social-assets/facebook/poll/{ARTICLE_ID}",
        method="post",
        body={"question": "Your view?", "option_a": "Yes", "option_b": "No"},
        composer=lambda article, selected, **kwargs: captured.append((selected, kwargs)) or SVG,
    )
    assert response.status_code == 200
    assert captured == [("poll", {"question": "Your view?", "option_a": "Yes", "option_b": "No"})]
    rejected, _ = call(
        monkeypatch,
        f"/api/admin/social-assets/facebook/poll/{ARTICLE_ID}",
        method="post",
        body={"question": "Your view?", "option_a": "Yes", "option_b": "No", "option_c": "Maybe"},
        composer=lambda *args, **kwargs: SVG,
    )
    assert rejected.status_code == 422


def test_routes_are_admin_only_and_unique():
    paths = {
        "/api/admin/social-assets/facebook/article/{graphic_type}/{mongo_id}",
        "/api/admin/social-assets/facebook/quote/{mongo_id}",
        "/api/admin/social-assets/facebook/poll/{mongo_id}",
    }
    for path in paths:
        matches = [route for route in server.app.routes if getattr(route, "path", None) == path]
        assert len(matches) == 1
    assert not [route for route in server.app.routes if "social-assets/facebook" in getattr(route, "path", "") and not getattr(route, "path", "").startswith("/api/admin/")]


def test_route_source_contains_no_write_posting_scheduling_or_file_output_path():
    source = open(server.__file__, encoding="utf-8").read()
    route_source = source.split("class FacebookQuoteGraphicRequest", 1)[1].split('@api_router.get("/admin/articles")', 1)[0]
    for forbidden in (
        "insert_one(", "insert_many(", "update_one(", "update_many(",
        "delete_one(", "delete_many(", "write_bytes(", "write_text(",
        "facebook_post", "schedule_",
    ):
        assert forbidden not in route_source
