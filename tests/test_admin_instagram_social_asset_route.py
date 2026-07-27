import os
from copy import deepcopy

from bson import ObjectId
from fastapi.testclient import TestClient


os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "cheshire_test"
os.environ["LOCAL_DEV_NO_DB"] = "1"
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from app import instagram_social_asset


ROUTE = "/api/admin/social-assets/instagram/story/{article_id}"
ARTICLE_ID = "507f1f77bcf86cd799439011"
ARTICLE = {
    "_id": ObjectId(ARTICLE_ID),
    "title": "Council investment supports new jobs in Knutsford",
    "category": "Local News",
    "image": "https://images.example.test/story.jpg",
}


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


def routes():
    return [
        route for route in server.app.routes
        if getattr(route, "path", None) == ROUTE and "GET" in getattr(route, "methods", set())
    ]


def dependency_calls(dependant):
    calls = []
    for dependency in dependant.dependencies:
        calls.append(dependency.call)
        calls.extend(dependency_calls(dependency))
    return calls


def request(monkeypatch, collection, article_id=ARTICLE_ID, composer=None, query=""):
    monkeypatch.setattr(server.db, "articles", collection)
    if composer is not None:
        monkeypatch.setattr(server, "compose_instagram_top_story_svg", composer)
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    try:
        return TestClient(server.app).get(
            f"/api/admin/social-assets/instagram/story/{article_id}{query}",
            headers={"Accept-Encoding": "identity"},
        )
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)


def test_route_is_unique_authenticated_admin_only():
    assert len(routes()) == 1
    assert server.get_admin_auth in dependency_calls(routes()[0].dependant)
    assert not [
        route for route in server.app.routes
        if getattr(route, "path", "").endswith("/social-assets/instagram/story/{article_id}")
        and not getattr(route, "path", "").startswith("/api/admin/")
    ]


def test_unauthenticated_stops_before_lookup_and_composition(monkeypatch):
    collection = ReadOnlyArticles()
    monkeypatch.setattr(server.db, "articles", collection)
    monkeypatch.setattr(server, "compose_instagram_top_story_svg", lambda record: (_ for _ in ()).throw(AssertionError("composer called")))
    response = TestClient(server.app).get(
        f"/api/admin/social-assets/instagram/story/{ARTICLE_ID}",
        headers={"Accept-Encoding": "identity"},
    )
    assert response.status_code == 401
    assert collection.find_calls == []


def test_malformed_missing_archived_and_manual_review_records_are_rejected(monkeypatch):
    malformed = ReadOnlyArticles()
    response = request(monkeypatch, malformed, article_id="bad-id")
    assert response.status_code == 400
    assert malformed.find_calls == []
    for article in (None, {**ARTICLE, "archived": True}, {**ARTICLE, "manual_review_hidden_from_public": True}):
        response = request(monkeypatch, ReadOnlyArticles(article))
        assert response.status_code == 404


def test_exact_read_only_lookup_and_database_fields(monkeypatch):
    collection = ReadOnlyArticles({**ARTICLE, "private_note": "not forwarded"})
    records = []
    response = request(
        monkeypatch,
        collection,
        composer=lambda record: records.append(record) or b'<svg width="1080" height="1920" viewBox="0 0 1080 1920"/>',
        query="?image=https://evil.example/image.jpg&title=Injected&template=evil",
    )
    assert response.status_code == 200
    assert collection.find_calls == [({
        "_id": ObjectId(ARTICLE_ID),
        "archived": {"$ne": True},
        "manual_review_hidden_from_public": {"$ne": True},
    }, {"_id": 1, "title": 1, "category": 1, "image": 1})]
    assert records == [{
        "mongo_id": ARTICLE_ID,
        "title": ARTICLE["title"],
        "category": "Local News",
        "image": ARTICLE["image"],
    }]


def test_wrong_category_and_missing_image_fail_safely(monkeypatch):
    assert request(monkeypatch, ReadOnlyArticles({**ARTICLE, "category": "Business"})).status_code == 400
    response = request(monkeypatch, ReadOnlyArticles({**ARTICLE, "image": ""}))
    assert response.status_code == 422
    assert response.json() == {"detail": "Article image is unavailable or unusable"}


def test_valid_response_is_exact_self_contained_svg(monkeypatch):
    svg = b'<?xml version="1.0"?><svg width="1080" height="1920" viewBox="0 0 1080 1920"><image href="data:image/png;base64,AA=="/></svg>'
    response = request(monkeypatch, ReadOnlyArticles(), composer=lambda record: svg)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-disposition"] == f'inline; filename="cheshire-today-{ARTICLE_ID}-instagram-story-top-story.svg"'
    assert response.content == svg


def test_typed_composer_failures_map_without_private_details(monkeypatch):
    failures = [
        (instagram_social_asset.ImageContentError("private image"), 422),
        (instagram_social_asset.TemplateValidationError("private template"), 500),
        (RuntimeError("private unexpected"), 500),
    ]
    for error, status in failures:
        response = request(
            monkeypatch,
            ReadOnlyArticles(),
            composer=lambda record, error=error: (_ for _ in ()).throw(error),
        )
        assert response.status_code == status
        assert "private" not in response.text

