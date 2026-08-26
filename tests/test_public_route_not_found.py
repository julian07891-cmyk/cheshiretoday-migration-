import asyncio
import os
import re
from pathlib import Path

import pytest
from starlette.requests import Request

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT / "frontend/src/App.js"

SUPPORTED_EXACT_PATHS = {
    "admin",
    "jobs",
    "jobs/post",
    "jobs/payment-success",
    "advertise",
    "advertise/pay",
    "advertise/payment-success",
    "privacy",
    "terms",
    "cookies",
    "affiliate-disclosure",
    "contact",
    "unsubscribe",
    "newsletter",
    "newsletter/preferences",
    "newsletter/reactivate",
}

UNSUPPORTED_PATHS = {
    "not-a-real-page",
    "foo/bar/baz",
    "wirral",
    "stockport",
    "runcorn",
    "category/tech",
    "category/ai",
    "category/tax",
    "category/property",
    "category/business/extra",
    "chester/extra",
}


def request_for(path: str, *, user_agent: str = "Mozilla/5.0", query: bytes = b""):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "https",
            "path": f"/{path}",
            "raw_path": f"/{path}".encode(),
            "query_string": query,
            "headers": [(b"user-agent", user_agent.encode())],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 443),
        }
    )


@pytest.mark.parametrize("path", sorted(UNSUPPORTED_PATHS))
def test_unsupported_public_paths_return_safe_404(path):
    response = asyncio.run(server.serve_react_spa(path, request_for(path)))
    body = response.body.decode()

    assert response.status_code == 404
    assert "<title>Page not found | Cheshire Today</title>" in body
    assert '<meta name="robots" content="noindex, follow">' in body
    assert 'rel="canonical"' not in body
    assert "Cheshire Today | Local News, Business, AI &amp; Tech, Finance" not in body
    assert '<a href="/">Return to the Cheshire Today homepage</a>' in body


def test_query_parameters_do_not_turn_unknown_path_into_homepage():
    response = asyncio.run(
        server.serve_react_spa(
            "not-a-real-page",
            request_for(
                "not-a-real-page",
                query=b"token=sensitive&category=business",
            ),
        )
    )
    body = response.body.decode()

    assert response.status_code == 404
    assert "token" not in body
    assert "sensitive" not in body
    assert "category=business" not in body


def test_requested_path_is_escaped_in_not_found_response():
    response = server._public_not_found_response("<script>alert(1)</script>")
    body = response.body.decode()

    assert response.status_code == 404
    assert "<script>alert(1)</script>" not in body
    assert "/&lt;script&gt;alert(1)&lt;/script&gt;" in body


def test_browser_and_googlebot_receive_same_unsupported_status_and_contract():
    browser = asyncio.run(
        server.serve_react_spa("missing/path", request_for("missing/path"))
    )
    crawler = asyncio.run(
        server.serve_react_spa(
            "missing/path",
            request_for("missing/path", user_agent="Googlebot"),
        )
    )

    assert browser.status_code == crawler.status_code == 404
    assert browser.body == crawler.body


def test_supported_spa_inventory_matches_the_frontend_contract():
    assert server.PUBLIC_SPA_EXACT_PATHS == SUPPORTED_EXACT_PATHS
    frontend_routes = set(
        re.findall(
            r'<Route\b[^>]*\bpath="(/[^"]*)"',
            FRONTEND_APP.read_text(),
            flags=re.DOTALL,
        )
    )
    dedicated_server_families = {
        "/",
        "/guides/:slug",
        "/article/:articleId",
        "/article/:articleId/:slug",
        "/:location",
    }
    assert {
        path.lstrip("/")
        for path in frontend_routes - dedicated_server_families
    } == SUPPORTED_EXACT_PATHS
    for path in SUPPORTED_EXACT_PATHS:
        assert server._is_supported_public_spa_path(path)
    for slug in server.PUBLIC_CATEGORY_HUBS:
        assert server._is_supported_public_spa_path(f"category/{slug}")
    for slug in server.PUBLIC_LOCATION_HUBS:
        assert server._is_supported_public_spa_path(slug)


@pytest.mark.parametrize("path", sorted(UNSUPPORTED_PATHS))
def test_unsupported_paths_are_absent_from_spa_allowlist(path):
    assert not server._is_supported_public_spa_path(path)


def test_supported_spa_path_serves_frontend_index(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(server, "_spa_index_or_500", lambda: sentinel)
    monkeypatch.setattr(server, "_admin_spa_index_or_500", lambda: sentinel)

    for path in sorted(SUPPORTED_EXACT_PATHS):
        assert asyncio.run(server.serve_react_spa(path, request_for(path))) is sentinel


def test_homepage_still_serves_frontend_index(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(server, "_spa_index_or_500", lambda: sentinel)

    assert asyncio.run(server.serve_spa_root(request_for(""))) is sentinel


def test_browser_guide_route_keeps_existing_spa_contract(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(server, "_spa_index_or_500", lambda: sentinel)

    response = asyncio.run(
        server.serve_guide_for_production(
            "existing-guide",
            request_for("guides/existing-guide"),
        )
    )

    assert response is sentinel


def test_supported_crawler_hub_keeps_dedicated_html(monkeypatch):
    sentinel = object()

    async def fake_hub(path):
        assert path == "category/business"
        return sentinel

    monkeypatch.setattr(server, "serve_public_hub_html", fake_hub)

    response = asyncio.run(
        server.serve_react_spa(
            "category/business",
            request_for("category/business", user_agent="Googlebot"),
        )
    )
    assert response is sentinel


def test_static_asset_still_uses_file_response(monkeypatch, tmp_path):
    static_file = tmp_path / "asset.txt"
    static_file.write_text("static")
    monkeypatch.setattr(server, "_FRONTEND_DIR", Path(tmp_path))

    response = asyncio.run(
        server.serve_react_spa("asset.txt", request_for("asset.txt"))
    )

    assert response.status_code == 200
    assert Path(response.path) == static_file


def test_unknown_api_route_keeps_fastapi_json_404_contract():
    matching_route = next(
        route
        for route in server.app.routes
        if getattr(route, "path", None) == "/{full_path:path}"
    )
    assert "api/" not in server.PUBLIC_SPA_EXACT_PATHS

    with pytest.raises(Exception) as exc_info:
        asyncio.run(
            matching_route.endpoint(
                "api/definitely-unknown",
                request_for("api/definitely-unknown"),
            )
        )

    assert getattr(exc_info.value, "status_code", None) == 404
    assert getattr(exc_info.value, "detail", None) == "Not Found"
