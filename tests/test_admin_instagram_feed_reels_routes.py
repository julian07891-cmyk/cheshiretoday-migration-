import os
from copy import deepcopy

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient


os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "cheshire_test"
os.environ["LOCAL_DEV_NO_DB"] = "1"
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from app import instagram_social_asset


ARTICLE_ID = "507f1f77bcf86cd799439011"
ARTICLE = {
    "_id": ObjectId(ARTICLE_ID),
    "title": "Council investment supports new jobs in Knutsford",
    "category": "Local News",
    "image": "https://images.example.test/story.jpg",
}
FORMATS = (
    ("feed", "compose_instagram_feed_svg", 1080, 1080),
    ("reels-cover", "compose_instagram_reels_cover_svg", 1080, 1920),
)


class ReadOnlyArticles:
    def __init__(self, article=ARTICLE):
        self.article = deepcopy(article)
        self.find_calls = []

    async def find_one(self, query, projection=None):
        self.find_calls.append((query, projection))
        return deepcopy(self.article)

    def __getattr__(self, name):
        if name in {"insert_one", "update_one", "update_many", "delete_one", "delete_many", "replace_one"}:
            raise AssertionError(f"database write attempted: {name}")
        raise AttributeError(name)


def route_path(format_name):
    return f"/api/admin/social-assets/instagram/{format_name}/{ARTICLE_ID}"


def request(monkeypatch, format_name, composer_name, collection, article_id=ARTICLE_ID, composer=None):
    monkeypatch.setattr(server.db, "articles", collection)
    if composer is not None:
        monkeypatch.setattr(server, composer_name, composer)
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    try:
        return TestClient(server.app).get(
            f"/api/admin/social-assets/instagram/{format_name}/{article_id}",
            headers={"Accept-Encoding": "identity"},
        )
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)


@pytest.mark.parametrize("format_name,composer_name,width,height", FORMATS)
def test_routes_are_unique_authenticated_admin_only(format_name, composer_name, width, height):
    matches = [
        route for route in server.app.routes
        if getattr(route, "path", None) == f"/api/admin/social-assets/instagram/{format_name}/{{article_id}}"
        and "GET" in getattr(route, "methods", set())
    ]
    assert len(matches) == 1
    assert server.get_admin_auth in [dependency.call for dependency in matches[0].dependant.dependencies]
    assert not [
        route for route in server.app.routes
        if getattr(route, "path", "").endswith(f"/social-assets/instagram/{format_name}/{{article_id}}")
        and not getattr(route, "path", "").startswith("/api/admin/")
    ]


@pytest.mark.parametrize("format_name,composer_name,width,height", FORMATS)
def test_unauthenticated_stops_before_lookup_and_composition(
    monkeypatch, format_name, composer_name, width, height
):
    collection = ReadOnlyArticles()
    monkeypatch.setattr(server.db, "articles", collection)
    monkeypatch.setattr(server, composer_name, lambda record: pytest.fail("composer called"))
    response = TestClient(server.app).get(
        route_path(format_name), headers={"Accept-Encoding": "identity"}
    )
    assert response.status_code == 401
    assert collection.find_calls == []


@pytest.mark.parametrize("format_name,composer_name,width,height", FORMATS)
def test_invalid_article_states_and_category_fail_safely(
    monkeypatch, format_name, composer_name, width, height
):
    malformed = ReadOnlyArticles()
    assert request(monkeypatch, format_name, composer_name, malformed, article_id="bad-id").status_code == 400
    assert malformed.find_calls == []
    for article in (None, {**ARTICLE, "archived": True}, {**ARTICLE, "manual_review_hidden_from_public": True}):
        assert request(monkeypatch, format_name, composer_name, ReadOnlyArticles(article)).status_code == 404
    assert request(monkeypatch, format_name, composer_name, ReadOnlyArticles({**ARTICLE, "category": "Business"})).status_code == 400
    assert request(monkeypatch, format_name, composer_name, ReadOnlyArticles({**ARTICLE, "image": ""})).status_code == 422


@pytest.mark.parametrize("format_name,composer_name,width,height", FORMATS)
def test_valid_routes_return_read_only_no_store_svg(
    monkeypatch, format_name, composer_name, width, height
):
    svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"/>'.encode()
    records = []
    collection = ReadOnlyArticles({**ARTICLE, "private_note": "not forwarded"})
    response = request(
        monkeypatch,
        format_name,
        composer_name,
        collection,
        composer=lambda record: records.append(record) or svg,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "no-store"
    assert response.content == svg
    assert records == [{
        "mongo_id": ARTICLE_ID,
        "title": ARTICLE["title"],
        "category": ARTICLE["category"],
        "image": ARTICLE["image"],
    }]


@pytest.mark.parametrize("format_name,composer_name,width,height", FORMATS)
def test_typed_failures_do_not_expose_private_details(
    monkeypatch, format_name, composer_name, width, height
):
    for error, status in (
        (instagram_social_asset.ImageContentError("private image"), 422),
        (instagram_social_asset.TemplateValidationError("private template"), 500),
    ):
        response = request(
            monkeypatch,
            format_name,
            composer_name,
            ReadOnlyArticles(),
            composer=lambda record, error=error: (_ for _ in ()).throw(error),
        )
        assert response.status_code == status
        assert "private" not in response.text
