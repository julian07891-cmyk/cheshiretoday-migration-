import base64
import hashlib
import io
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image


os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "cheshire_test"
os.environ["LOCAL_DEV_NO_DB"] = "1"
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from app import facebook_newsletter_asset


ROUTE = "/api/admin/social-assets/facebook/newsletter"


class NoDatabaseAccess:
    def __getattr__(self, name):
        raise AssertionError(f"database access attempted: {name}")


def route_entries():
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == ROUTE and "GET" in getattr(route, "methods", set())
    ]


def dependency_calls(dependant):
    calls = []
    for dependency in dependant.dependencies:
        calls.append(dependency.call)
        calls.extend(dependency_calls(dependency))
    return calls


def authenticated_get(monkeypatch, query=""):
    monkeypatch.setattr(server.db, "articles", NoDatabaseAccess())
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    try:
        return TestClient(server.app).get(
            f"{ROUTE}{query}",
            headers={"Accept-Encoding": "identity"},
        )
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)


def test_newsletter_route_is_one_authenticated_admin_get_with_no_public_alias():
    routes = route_entries()
    assert len(routes) == 1
    assert server.get_admin_auth in dependency_calls(routes[0].dependant)
    assert not [
        route
        for route in server.app.routes
        if getattr(route, "path", "").endswith("/social-assets/facebook/newsletter")
        and not getattr(route, "path", "").startswith("/api/admin/")
    ]


def test_unauthenticated_request_stops_before_database_or_composer(monkeypatch):
    monkeypatch.setattr(server.db, "articles", NoDatabaseAccess())
    monkeypatch.setattr(
        server,
        "compose_facebook_newsletter_svg",
        lambda: (_ for _ in ()).throw(AssertionError("composer called")),
    )
    response = TestClient(server.app).get(ROUTE, headers={"Accept-Encoding": "identity"})
    assert response.status_code == 401


def test_route_returns_deterministic_no_store_svg_without_database_access(monkeypatch):
    response = authenticated_get(monkeypatch)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-disposition"] == (
        'inline; filename="cheshire-today-newsletter-facebook.svg"'
    )
    root = ET.fromstring(response.content)
    assert root.attrib == {
        "width": "1200",
        "height": "630",
        "viewBox": "0 0 1200 630",
        "role": "img",
        "aria-labelledby": "newsletter-facebook-title newsletter-facebook-description",
    }
    rendered_text = " ".join(" ".join(root.itertext()).split())
    assert facebook_newsletter_asset.NEWSLETTER_HEADLINE in rendered_text
    assert facebook_newsletter_asset.NEWSLETTER_SUPPORTING_MESSAGE in rendered_text
    assert facebook_newsletter_asset.NEWSLETTER_CTA in rendered_text
    assert facebook_newsletter_asset.NEWSLETTER_WEBSITE in rendered_text
    assert b"data-placeholder=" not in response.content
    assert b"[HEADLINE]" not in response.content
    for element in root.iter():
        if element.tag.endswith("image"):
            assert element.attrib.get("href", "").startswith("data:image/")


def test_approved_master_and_inverse_logo_are_embedded(monkeypatch):
    response = authenticated_get(monkeypatch)
    assert hashlib.sha256(
        facebook_newsletter_asset.NEWSLETTER_MASTER_SVG_PATH.read_bytes()
    ).hexdigest() == facebook_newsletter_asset.APPROVED_NEWSLETTER_MASTER_SHA256
    root = ET.fromstring(response.content)
    logo_group = next(
        element
        for element in root.iter()
        if element.attrib.get("data-logo-variant") == "inverse"
    )
    logo_image = next(element for element in logo_group if element.tag.endswith("image"))
    assert logo_image.attrib["data-source-sha256"] == facebook_newsletter_asset.APPROVED_LOGO_SHA256
    assert logo_image.attrib["href"].startswith("data:image/png;base64,")
    logo_bytes = base64.b64decode(logo_image.attrib["href"].split(",", 1)[1])
    with Image.open(io.BytesIO(logo_bytes)).convert("RGBA") as logo:
        visible_colours = {(red, green, blue) for red, green, blue, alpha in logo.getdata() if alpha}
    assert visible_colours == {facebook_newsletter_asset.INVERSE_LOGO_COLOUR}


def test_client_values_are_ignored_and_cannot_change_newsletter_copy(monkeypatch):
    response = authenticated_get(
        monkeypatch,
        query="?title=Injected&url=https%3A%2F%2Fevil.example&template=%2Ftmp%2Fevil.svg&image=data%3Aimage%2Fpng",
    )
    assert response.status_code == 200
    assert b"Injected" not in response.content
    assert b"evil.example" not in response.content
    assert facebook_newsletter_asset.NEWSLETTER_HEADLINE.encode() not in response.content
    rendered_text = " ".join(" ".join(ET.fromstring(response.content).itertext()).split())
    assert facebook_newsletter_asset.NEWSLETTER_HEADLINE in rendered_text


def test_composer_and_route_perform_no_file_or_database_write(monkeypatch):
    monkeypatch.setattr(
        Path,
        "write_bytes",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("file write attempted")),
    )
    monkeypatch.setattr(
        Path,
        "write_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("file write attempted")),
    )
    response = authenticated_get(monkeypatch)
    assert response.status_code == 200


def test_template_failure_maps_to_safe_500(monkeypatch):
    monkeypatch.setattr(
        server,
        "compose_facebook_newsletter_svg",
        lambda: (_ for _ in ()).throw(
            facebook_newsletter_asset.TemplateValidationError("private path detail")
        ),
    )
    response = authenticated_get(monkeypatch)
    assert response.status_code == 500
    assert response.json() == {"detail": "Social asset could not be generated"}
    assert "private path detail" not in response.text
