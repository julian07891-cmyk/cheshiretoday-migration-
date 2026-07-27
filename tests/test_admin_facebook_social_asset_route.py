import io
import os
import xml.etree.ElementTree as ET
from copy import deepcopy

from bson import ObjectId
from fastapi.testclient import TestClient
from PIL import Image


os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "cheshire_test"
os.environ["LOCAL_DEV_NO_DB"] = "1"
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from app import facebook_social_asset


ROUTE = "/api/admin/social-assets/facebook/local-news/{mongo_id}"
ARTICLE_ID = "507f1f77bcf86cd799439011"
ARTICLE = {
    "_id": ObjectId(ARTICLE_ID),
    "title": "Council investment supports new jobs in Knutsford",
    "category": "Local News",
    "image": "https://images.example.test/local-story.jpg",
}


class ReadOnlyArticles:
    def __init__(self, article=ARTICLE):
        self.article = deepcopy(article)
        self.find_calls = []

    async def find_one(self, query, projection=None):
        self.find_calls.append((query, projection))
        return self.article

    def __getattr__(self, name):
        if name in {"insert_one", "update_one", "update_many", "delete_one", "delete_many", "replace_one"}:
            raise AssertionError(f"database write attempted: {name}")
        raise AttributeError(name)


def route_entries(path=ROUTE):
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path and "GET" in getattr(route, "methods", set())
    ]


def dependency_calls(dependant):
    calls = []
    for dependency in dependant.dependencies:
        calls.append(dependency.call)
        calls.extend(dependency_calls(dependency))
    return calls


def png_bytes():
    output = io.BytesIO()
    Image.new("RGB", (1200, 800), (30, 64, 138)).save(output, format="PNG")
    return output.getvalue()


def request(monkeypatch, collection, article_id=ARTICLE_ID, composer=None, query=""):
    monkeypatch.setattr(server.db, "articles", collection)
    if composer is not None:
        monkeypatch.setattr(server, "compose_facebook_local_news_svg", composer)
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    try:
        return TestClient(server.app).get(
            f"/api/admin/social-assets/facebook/local-news/{article_id}{query}",
            headers={"Accept-Encoding": "identity"},
        )
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)


def test_route_is_registered_once_as_authenticated_admin_get_only():
    routes = route_entries()
    assert len(routes) == 1
    assert server.get_admin_auth in dependency_calls(routes[0].dependant)
    assert not [
        route
        for route in server.app.routes
        if getattr(route, "path", "").endswith("/social-assets/facebook/local-news/{mongo_id}")
        and not getattr(route, "path", "").startswith("/api/admin/")
    ]


def test_unauthenticated_request_stops_before_database_or_composer(monkeypatch):
    collection = ReadOnlyArticles()
    monkeypatch.setattr(server.db, "articles", collection)
    monkeypatch.setattr(
        server,
        "compose_facebook_local_news_svg",
        lambda article: (_ for _ in ()).throw(AssertionError("composer called")),
    )
    response = TestClient(server.app).get(
        f"/api/admin/social-assets/facebook/local-news/{ARTICLE_ID}",
        headers={"Accept-Encoding": "identity"},
    )
    assert response.status_code == 401
    assert collection.find_calls == []


def test_malformed_id_returns_400_before_database_lookup(monkeypatch):
    collection = ReadOnlyArticles()
    response = request(monkeypatch, collection, article_id="not-an-object-id")
    assert response.status_code == 400
    assert response.json() == {"detail": "Article ID is invalid"}
    assert collection.find_calls == []


def test_unknown_archived_and_manual_review_articles_return_404(monkeypatch):
    for article in (None, {**ARTICLE, "archived": True}, {**ARTICLE, "manual_review_hidden_from_public": True}):
        collection = ReadOnlyArticles(article)
        response = request(monkeypatch, collection)
        assert response.status_code == 404
        assert response.json() == {"detail": "Article not found"}


def test_lookup_uses_exact_active_article_projection(monkeypatch):
    collection = ReadOnlyArticles()
    response = request(monkeypatch, collection, composer=lambda article: b'<svg width="1200" height="630" viewBox="0 0 1200 630"/>')
    assert response.status_code == 200
    query, projection = collection.find_calls[0]
    assert query == {
        "_id": ObjectId(ARTICLE_ID),
        "archived": {"$ne": True},
        "manual_review_hidden_from_public": {"$ne": True},
    }
    assert projection == {"_id": 1, "title": 1, "category": 1, "image": 1}


def test_composer_receives_only_database_fields_and_article_is_unchanged(monkeypatch):
    stored_article = {**ARTICLE, "private_note": "must not be forwarded"}
    original = deepcopy(stored_article)
    collection = ReadOnlyArticles(stored_article)
    composed_records = []

    response = request(
        monkeypatch,
        collection,
        composer=lambda record: composed_records.append(deepcopy(record))
        or b'<svg width="1200" height="630" viewBox="0 0 1200 630"/>',
        query="?image=https%3A%2F%2Fevil.example%2Fimage.jpg&title=Injected&cta=Post",
    )

    assert response.status_code == 200
    assert composed_records == [{
        "mongo_id": ARTICLE_ID,
        "title": ARTICLE["title"],
        "category": "Local News",
        "image": ARTICLE["image"],
    }]
    assert stored_article == original
    assert collection.article == original


def test_non_local_article_returns_400_without_composition(monkeypatch):
    collection = ReadOnlyArticles({**ARTICLE, "category": "Business"})
    monkeypatch.setattr(
        server,
        "compose_facebook_local_news_svg",
        lambda article: (_ for _ in ()).throw(AssertionError("composer called")),
    )
    response = request(monkeypatch, collection)
    assert response.status_code == 400
    assert response.json() == {"detail": "Only Local News articles are supported"}


def test_missing_image_maps_to_safe_422(monkeypatch):
    response = request(monkeypatch, ReadOnlyArticles({**ARTICLE, "image": ""}))
    assert response.status_code == 422
    assert response.json() == {"detail": "Article image is unavailable or unusable"}


def test_valid_local_article_returns_self_contained_no_store_svg(monkeypatch):
    image = facebook_social_asset.ValidatedImage(
        content=png_bytes(), mime_type="image/png", width=1200, height=800
    )
    monkeypatch.setattr(
        facebook_social_asset,
        "fetch_validated_article_image",
        lambda *args, **kwargs: image,
    )
    response = request(monkeypatch, ReadOnlyArticles())
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-disposition"] == (
        f'inline; filename="cheshire-today-{ARTICLE_ID}-facebook-local-news.svg"'
    )
    root = ET.fromstring(response.content)
    assert root.attrib["width"] == "1200"
    assert root.attrib["height"] == "630"
    assert root.attrib["viewBox"] == "0 0 1200 630"
    assert facebook_social_asset.APPROVED_LOGO_SHA256.encode() in response.content
    assert b"data:image/png;base64," in response.content
    assert b"https://images.example.test" not in response.content
    assert b"data-placeholder=" not in response.content
    assert b"[HEADLINE]" not in response.content


def test_image_failure_maps_to_safe_422(monkeypatch):
    def fail_composer(article):
        raise facebook_social_asset.ImageContentError("private image detail")

    response = request(monkeypatch, ReadOnlyArticles(), composer=fail_composer)
    assert response.status_code == 422
    assert response.json() == {"detail": "Article image is unavailable or unusable"}
    assert "private image detail" not in response.text


def test_template_failure_maps_to_safe_500(monkeypatch):
    def fail_composer(article):
        raise facebook_social_asset.TemplateValidationError("private template detail")

    response = request(monkeypatch, ReadOnlyArticles(), composer=fail_composer)
    assert response.status_code == 500
    assert response.json() == {"detail": "Social asset could not be generated"}
    assert "private template detail" not in response.text


def test_unexpected_failure_maps_to_safe_500(monkeypatch):
    def fail_composer(article):
        raise RuntimeError("private unexpected detail")

    response = request(monkeypatch, ReadOnlyArticles(), composer=fail_composer)
    assert response.status_code == 500
    assert response.json() == {"detail": "Social asset could not be generated"}
    assert "private unexpected detail" not in response.text
