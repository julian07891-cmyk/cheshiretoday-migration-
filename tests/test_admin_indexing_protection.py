import asyncio
import os
from pathlib import Path

import pytest
from starlette.requests import Request

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


ADMIN_ROBOTS_DIRECTIVE = "noindex, nofollow, noarchive"


def request_for(path: str):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "https",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [(b"user-agent", b"Mozilla/5.0")],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 443),
        }
    )


@pytest.fixture
def frontend_index(monkeypatch, tmp_path):
    index_html = tmp_path / "index.html"
    index_html.write_text("<html><body>Cheshire Today SPA</body></html>")
    monkeypatch.setattr(server, "_FRONTEND_DIR", Path(tmp_path))
    monkeypatch.setattr(server, "_INDEX_HTML", index_html)
    return index_html


@pytest.mark.parametrize("path", ["admin", "admin/"])
def test_admin_get_has_first_byte_noindex_without_redirect(frontend_index, path):
    response = asyncio.run(server.serve_react_spa(path, request_for(f"/{path}")))

    assert response.status_code == 200
    assert response.headers["x-robots-tag"] == ADMIN_ROBOTS_DIRECTIVE
    assert response.headers.getlist("x-robots-tag") == [ADMIN_ROBOTS_DIRECTIVE]
    assert "location" not in response.headers
    assert Path(response.path) == frontend_index


@pytest.mark.parametrize("path", ["admin", "admin/"])
def test_admin_head_has_first_byte_noindex_without_redirect(frontend_index, path):
    response = asyncio.run(server.head_react_spa(path))

    assert response.status_code == 200
    assert response.headers["x-robots-tag"] == ADMIN_ROBOTS_DIRECTIVE
    assert response.headers.getlist("x-robots-tag") == [ADMIN_ROBOTS_DIRECTIVE]
    assert "location" not in response.headers
    assert Path(response.path) == frontend_index


def test_admin_noindex_header_is_not_added_to_public_spa(frontend_index):
    response = asyncio.run(server.serve_spa_root(request_for("/")))

    assert response.status_code == 200
    assert "x-robots-tag" not in response.headers
    assert Path(response.path) == frontend_index


def test_nested_admin_path_remains_noindex_404(frontend_index):
    response = asyncio.run(
        server.serve_react_spa(
            "admin/settings",
            request_for("/admin/settings"),
        )
    )
    body = response.body.decode()

    assert response.status_code == 404
    assert '<meta name="robots" content="noindex, follow">' in body
    assert "x-robots-tag" not in response.headers


def _robots_group(content: str, user_agent: str):
    groups = {}
    current_agents = []
    current_rules = []

    def store_group():
        for agent in current_agents:
            groups.setdefault(agent, []).extend(current_rules)

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = [part.strip() for part in line.split(":", 1)]
        if key.lower() == "user-agent":
            if current_rules:
                store_group()
                current_agents = []
                current_rules = []
            current_agents.append(value)
        elif current_agents:
            current_rules.append((key.lower(), value))
    store_group()
    return groups[user_agent]


@pytest.mark.parametrize("user_agent", ["*", "Googlebot", "Googlebot-News"])
def test_admin_paths_are_disallowed_for_relevant_robots_groups(user_agent):
    rules = _robots_group(server.get_robots_content(), user_agent)

    assert ("disallow", "/admin") in rules
    assert ("disallow", "/api/admin/") in rules


def test_public_robots_and_sitemap_contract_is_preserved():
    content = server.get_robots_content()
    googlebot_rules = _robots_group(content, "Googlebot")
    news_rules = _robots_group(content, "Googlebot-News")

    assert ("allow", "/") in googlebot_rules
    assert ("allow", "/article/") in googlebot_rules
    assert ("allow", "/api/seo/article/") in googlebot_rules
    assert ("allow", "/") in news_rules
    assert ("allow", "/article/") in news_rules
    assert "Sitemap: https://cheshiretoday.co.uk/sitemap.xml" in content
    assert "Sitemap: https://cheshiretoday.co.uk/news-sitemap.xml" in content


def test_admin_api_verify_remains_authenticated():
    route = next(
        route
        for route in server.app.routes
        if getattr(route, "path", None) == "/api/admin/verify"
    )

    assert "GET" in route.methods
    assert route.dependant.dependencies
    assert any(
        dependency.call is server.get_admin_auth
        for dependency in route.dependant.dependencies
    )
