import asyncio
import os
from pathlib import Path

from PIL import Image
from starlette.requests import Request


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (ROOT / "frontend/src/App.js").read_text()


def request_for(*, user_agent="Mozilla/5.0"):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "https",
            "path": "/newsletter",
            "raw_path": b"/newsletter",
            "query_string": b"",
            "headers": [(b"user-agent", user_agent.encode())],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 443),
        }
    )


def test_newsletter_is_a_supported_public_spa_route(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(server, "_spa_index_or_500", lambda: sentinel)

    assert "newsletter" in server.PUBLIC_SPA_EXACT_PATHS
    assert 'path="/newsletter"' in APP_SOURCE
    assert asyncio.run(server.serve_react_spa("newsletter", request_for())) is sentinel


def test_facebook_crawler_gets_dedicated_newsletter_metadata():
    response = asyncio.run(
        server.serve_react_spa(
            "newsletter",
            request_for(user_agent="facebookexternalhit/1.1"),
        )
    )
    body = response.body.decode()

    assert response.status_code == 200
    assert "Page not found" not in body
    assert "Cheshire Today Newsletter | Local News and Business Briefing" in body
    assert (
        'content="Subscribe free to the Cheshire Today newsletter for local news, '
        'business, property, finance and AI &amp; Tech updates from across Cheshire."'
        in body
    )
    assert '<link rel="canonical" href="https://cheshiretoday.co.uk/newsletter">' in body
    assert '<meta name="robots" content="index, follow">' in body
    assert '<meta property="og:type" content="website">' in body
    assert '<meta property="og:url" content="https://cheshiretoday.co.uk/newsletter">' in body
    assert '<meta property="og:title" content="Stay ahead with Cheshire’s daily briefing">' in body
    assert (
        '<meta property="og:image" content="https://cheshiretoday.co.uk/cheshire-today-newsletter-share.png">'
        in body
    )
    assert '<meta property="og:image:width" content="1200">' in body
    assert '<meta property="og:image:height" content="630">' in body
    assert '<meta name="twitter:card" content="summary_large_image">' in body
    assert (
        '<meta name="twitter:image" content="https://cheshiretoday.co.uk/cheshire-today-newsletter-share.png">'
        in body
    )
    assert "/social-share.jpg" not in body


def test_dedicated_newsletter_social_image_exists_and_is_exact_png():
    image_path = ROOT / "frontend/public/cheshire-today-newsletter-share.png"
    assert image_path.is_file()
    with Image.open(image_path) as image:
        assert image.format == "PNG"
        assert image.size == (1200, 630)
        assert image.mode in {"RGB", "RGBA"}


def test_secure_newsletter_management_routes_remain_supported():
    assert "newsletter/preferences" in server.PUBLIC_SPA_EXACT_PATHS
    assert "newsletter/reactivate" in server.PUBLIC_SPA_EXACT_PATHS


def test_unknown_route_still_returns_real_404():
    response = asyncio.run(
        server.serve_react_spa(
            "newsletter/not-a-real-page",
            request_for(user_agent="facebookexternalhit/1.1"),
        )
    )
    assert response.status_code == 404
    assert b"Page not found | Cheshire Today" in response.body
