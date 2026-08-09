import asyncio
import os
import re
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import HTTPException
from starlette.requests import Request

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


MONGO_ID = "6a619fe3d25f3963602b219a"
INTERNAL_UUID = "18791001-fd2b-4973-923c-9f7035a0e12b"
TITLE = "Most sewage spills in England may be illegal, new research suggests"
SLUG = "most-sewage-spills-in-england-may-be-illegal-new-research-suggests"
CANONICAL_URL = f"https://cheshiretoday.co.uk/article/{MONGO_ID}/{SLUG}"


class FakeCursor:
    def __init__(self, documents):
        self.documents = list(documents)

    def sort(self, *args, **kwargs):
        return self

    def limit(self, value):
        self.documents = self.documents[:value]
        return self

    async def to_list(self, value):
        return self.documents[:value]


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = list(documents)

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if "id" in query and document.get("id") == query["id"]:
                result = dict(document)
                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)
                return result
            if "_id" in query and document.get("_id") == query["_id"]:
                result = dict(document)
                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)
                return result
            title_query = query.get("title")
            if isinstance(title_query, dict) and "$regex" in title_query:
                if re.search(
                    title_query["$regex"],
                    str(document.get("title") or ""),
                    re.IGNORECASE,
                ):
                    return dict(document)
        return None

    def find(self, query, projection=None):
        return FakeCursor(dict(document) for document in self.documents)


def article_document(**overrides):
    document = {
        "_id": ObjectId(MONGO_ID),
        "id": INTERNAL_UUID,
        "title": TITLE,
        "summary": "A sufficiently detailed summary for deterministic crawler metadata.",
        "content": "First paragraph.\n\nSecond paragraph.",
        "category": "UK News",
        "scope": "uk",
        "source": "Example Publisher",
        "source_url": "https://example.com/story",
        "image": "https://example.com/image.jpg",
        "publishedDate": "2026-07-22T23:47:27",
        "archived": False,
        "force_live": False,
    }
    document.update(overrides)
    return document


def request(user_agent="Mozilla/5.0"):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [(b"user-agent", user_agent.encode("ascii"))],
        }
    )


def install_database(monkeypatch, *, active=(), archived=()):
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(
            articles=FakeCollection(active),
            archived_articles=FakeCollection(archived),
            authority_pages=FakeCollection(),
        ),
    )


def assert_permanent_redirect(response):
    assert response.status_code == 301
    assert response.headers["location"] == CANONICAL_URL
    assert "?" not in response.headers["location"]


@pytest.mark.parametrize(
    ("article_id", "slug"),
    [
        (INTERNAL_UUID, SLUG),
        (INTERNAL_UUID, "stale-title"),
        (MONGO_ID, "stale-title"),
    ],
)
def test_full_article_variants_redirect_to_mongo_canonical(
    monkeypatch,
    article_id,
    slug,
):
    install_database(monkeypatch, active=[article_document()])

    response = asyncio.run(
        server.serve_article_for_production_slug(
            article_id,
            slug,
            request(),
        )
    )

    assert_permanent_redirect(response)


@pytest.mark.parametrize("article_id", [INTERNAL_UUID, MONGO_ID])
def test_id_only_article_variants_redirect_to_mongo_canonical(
    monkeypatch,
    article_id,
):
    install_database(monkeypatch, active=[article_document()])

    response = asyncio.run(server.serve_article_for_production(article_id))

    assert_permanent_redirect(response)


@pytest.mark.parametrize(
    "user_agent",
    [
        "Mozilla/5.0",
        "Mozilla/5.0 (compatible; Googlebot/2.1)",
    ],
)
def test_current_mongo_canonical_serves_without_redirect(monkeypatch, user_agent):
    install_database(monkeypatch, active=[article_document()])

    response = asyncio.run(
        server.serve_article_for_production_slug(
            MONGO_ID,
            SLUG,
            request(user_agent),
        )
    )

    assert response.status_code == 200
    if "Googlebot" in user_agent:
        html = response.body.decode("utf-8")
        assert f'<link rel="canonical" href="{CANONICAL_URL}">' in html


def test_unknown_uuid_keeps_not_found_and_never_redirects_home(monkeypatch):
    install_database(monkeypatch)

    unknown_uuid = "00000000-0000-4000-8000-000000000000"
    for operation in [
        lambda: server.serve_article_for_production(unknown_uuid),
        lambda: server.serve_article_for_production_slug(
            unknown_uuid,
            SLUG,
            request(),
        ),
        lambda: server.serve_article_for_production_slug(
            unknown_uuid,
            SLUG,
            request("Mozilla/5.0 (compatible; Googlebot/2.1)"),
        ),
    ]:
        with pytest.raises(HTTPException) as exc:
            asyncio.run(operation())

        assert exc.value.status_code == 404


def test_old_slug_only_compatibility_still_redirects_to_mongo_canonical(monkeypatch):
    install_database(monkeypatch, archived=[article_document(archived=True)])

    response = asyncio.run(
        server.serve_article_for_production(
            SLUG,
        )
    )

    assert_permanent_redirect(response)


def test_uuid_reader_and_googlebot_share_the_same_redirect(monkeypatch):
    install_database(monkeypatch, active=[article_document()])

    locations = []
    for user_agent in [
        "Mozilla/5.0",
        "Mozilla/5.0 (compatible; Googlebot/2.1)",
    ]:
        response = asyncio.run(
            server.serve_article_for_production_slug(
                INTERNAL_UUID,
                SLUG,
                request(user_agent),
            )
        )
        assert response.status_code == 301
        locations.append(response.headers["location"])

    assert locations == [CANONICAL_URL, CANONICAL_URL]


def test_archived_uuid_redirects_then_mongo_page_remains_noindex(monkeypatch):
    archived = article_document(archived=True)
    install_database(monkeypatch, archived=[archived])

    redirect = asyncio.run(
        server.serve_article_for_production_slug(
            INTERNAL_UUID,
            SLUG,
            request("Mozilla/5.0 (compatible; Googlebot/2.1)"),
        )
    )
    assert_permanent_redirect(redirect)

    response = asyncio.run(server.serve_article_html(MONGO_ID))
    html = response.body.decode("utf-8")
    assert f'<link rel="canonical" href="{CANONICAL_URL}">' in html
    assert (
        '<meta name="robots" '
        'content="noindex, follow, max-image-preview:large">'
    ) in html


def test_force_live_archived_article_remains_indexable(monkeypatch):
    install_database(
        monkeypatch,
        archived=[article_document(archived=True, force_live=True)],
    )

    response = asyncio.run(server.serve_article_html(MONGO_ID))
    html = response.body.decode("utf-8")

    assert 'content="index, follow, max-image-preview:large"' in html
    assert 'content="noindex, follow, max-image-preview:large"' not in html


def test_manual_review_hidden_article_remains_noindex(monkeypatch):
    install_database(
        monkeypatch,
        active=[article_document(manual_review_hidden_from_public=True)],
    )

    response = asyncio.run(server.serve_article_html(MONGO_ID))
    html = response.body.decode("utf-8")

    assert (
        '<meta name="robots" '
        'content="noindex, follow, max-image-preview:large">'
    ) in html

    with pytest.raises(HTTPException) as exc:
        asyncio.run(server.get_article(MONGO_ID))
    assert exc.value.status_code == 404


@pytest.mark.parametrize("article_id", [MONGO_ID, INTERNAL_UUID])
def test_legacy_seo_article_uses_current_mongo_canonical(monkeypatch, article_id):
    install_database(monkeypatch, active=[article_document()])

    response = asyncio.run(server.get_seo_article_page(article_id, request()))
    html = response.body.decode("utf-8")

    assert response.status_code == 200
    assert f'<link rel="canonical" href="{CANONICAL_URL}">' in html
    assert f'<meta property="og:url" content="{CANONICAL_URL}">' in html
    assert f'<meta name="twitter:url" content="{CANONICAL_URL}">' in html
    assert f'"@id": "{CANONICAL_URL}"' in html
    assert f'href="{CANONICAL_URL}" class="cta"' in html


def test_legacy_seo_article_uses_current_title_slug(monkeypatch):
    current_title = "Updated Cheshire Article Headline"
    current_slug = "updated-cheshire-article-headline"
    canonical = f"https://cheshiretoday.co.uk/article/{MONGO_ID}/{current_slug}"
    install_database(monkeypatch, active=[article_document(title=current_title)])

    response = asyncio.run(server.get_seo_article_page(INTERNAL_UUID, request()))
    html = response.body.decode("utf-8")

    assert response.status_code == 200
    assert f'<link rel="canonical" href="{canonical}">' in html
    assert f'<meta property="og:url" content="{canonical}">' in html


@pytest.mark.parametrize(
    ("collection", "overrides", "expected_directive"),
    [
        (
            "active",
            {"manual_review_hidden_from_public": True},
            "noindex, follow, max-image-preview:large",
        ),
        (
            "archived",
            {"archived": True},
            "noindex, follow, max-image-preview:large",
        ),
        (
            "archived",
            {"archived": True, "force_live": True},
            "index, follow, max-image-preview:large",
        ),
    ],
)
def test_legacy_seo_article_uses_shared_visibility_contract(
    monkeypatch,
    collection,
    overrides,
    expected_directive,
):
    install_database(monkeypatch, **{collection: [article_document(**overrides)]})

    response = asyncio.run(server.get_seo_article_page(MONGO_ID, request()))
    html = response.body.decode("utf-8")

    assert response.status_code == 200
    assert f'<meta name="robots" content="{expected_directive}">' in html
    assert response.headers["x-robots-tag"] == expected_directive


def test_sitemap_continues_to_emit_only_mongo_article_identity(monkeypatch):
    install_database(monkeypatch, active=[article_document()])

    response = asyncio.run(server.generate_sitemap())
    xml = response.body.decode("utf-8")

    assert CANONICAL_URL in xml
    assert INTERNAL_UUID not in xml


def test_sensitive_query_values_are_not_forwarded(monkeypatch):
    install_database(monkeypatch, active=[article_document()])
    req = Request(
        {
            "type": "http",
            "method": "GET",
            "path": f"/article/{INTERNAL_UUID}/{SLUG}",
            "query_string": b"token=private&auth=secret&utm_source=test",
            "headers": [(b"user-agent", b"Mozilla/5.0")],
        }
    )

    response = asyncio.run(
        server.serve_article_for_production_slug(
            INTERNAL_UUID,
            SLUG,
            req,
        )
    )

    assert_permanent_redirect(response)
    assert "private" not in response.headers["location"]
    assert "secret" not in response.headers["location"]
