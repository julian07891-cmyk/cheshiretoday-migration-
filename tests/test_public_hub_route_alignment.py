import asyncio
import os
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from bson import ObjectId

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_HUBS = ROOT / "frontend/src/config/publicHubs.js"
FRONTEND_APP = ROOT / "frontend/src/App.js"
FRONTEND_HEADER = ROOT / "frontend/src/components/NewsHeader.jsx"
FRONTEND_FOOTER = ROOT / "frontend/src/components/NewsFooter.jsx"

EXPECTED_CATEGORIES = {
    "local-news",
    "uk-news",
    "business",
    "finance",
    "ai-tech",
}
EXPECTED_CATEGORY_CONFIG = {
    "local-news": ("Local", "Local News", ("Local",)),
    "uk-news": ("UK", "UK News", ("UK",)),
    "business": ("Business", "Business", ("Economy", "Economic")),
    "finance": (
        "Finance",
        "Finance",
        ("Tax", "Property", "Property & Tax", "Money"),
    ),
    "ai-tech": ("AI & Tech", "AI & Tech", ("AI", "Tech", "Technology")),
}
EXPECTED_LOCATIONS = {
    "cheshire-general",
    "chester",
    "warrington",
    "crewe",
    "macclesfield",
    "wilmslow",
    "knutsford",
    "northwich",
}
UNSUPPORTED = {"wirral", "stockport", "runcorn"}


class FakeCursor:
    def __init__(self, documents):
        self.documents = [dict(document) for document in documents]

    def sort(self, *args, **kwargs):
        return self

    def skip(self, count):
        self.documents = self.documents[count:]
        return self

    def limit(self, count):
        self.documents = self.documents[:count]
        return self

    async def to_list(self, count):
        return self.documents[:count]


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = list(documents)
        self.queries = []

    def find(self, query, projection=None):
        self.queries.append(query)
        return FakeCursor(self.documents)

    async def count_documents(self, query):
        self.queries.append(query)
        return len(self.documents)


def article(**overrides):
    document = {
        "_id": ObjectId("6a619fe3d25f3963602b219a"),
        "id": "18791001-fd2b-4973-923c-9f7035a0e12b",
        "title": "Cheshire business investment creates new jobs",
        "summary": "A useful public article summary.",
        "category": "Business",
        "location": "chester",
        "is_local_source": True,
        "image": "https://example.com/image.jpg",
        "publishedDate": "2026-07-23T09:00:00Z",
        "created_at": "2026-07-23T09:00:00Z",
        "archived": False,
    }
    document.update(overrides)
    return document


def install_database(monkeypatch, documents=()):
    articles = FakeCollection(documents)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(
            articles=articles,
            authority_pages=FakeCollection(),
        ),
    )
    return articles


def frontend_slugs(section):
    source = FRONTEND_HUBS.read_text()
    block = source.split(f"export const {section} = [", 1)[1].split("];", 1)[0]
    return set(re.findall(r'slug:\s*"([^"]+)"', block))


def test_supported_inventory_is_identical_across_frontend_and_backend():
    assert frontend_slugs("CATEGORY_HUBS") == EXPECTED_CATEGORIES
    assert frontend_slugs("LOCATION_HUBS") == EXPECTED_LOCATIONS
    assert set(server.PUBLIC_CATEGORY_HUBS) == EXPECTED_CATEGORIES
    assert server.PUBLIC_LOCATION_HUBS == EXPECTED_LOCATIONS


def test_public_category_taxonomy_is_explicit_and_complete():
    actual = {
        slug: (
            config["label"],
            config["canonical_category"],
            config["aliases"],
        )
        for slug, config in server.PUBLIC_CATEGORY_HUBS.items()
    }
    assert actual == EXPECTED_CATEGORY_CONFIG


@pytest.mark.parametrize(
    ("value", "slug"),
    [
        ("Local News", "local-news"),
        ("Local", "local-news"),
        ("UK News", "uk-news"),
        ("UK", "uk-news"),
        ("Business", "business"),
        ("Economy", "business"),
        ("Economic", "business"),
        ("Finance", "finance"),
        ("Tax", "finance"),
        ("Property", "finance"),
        ("Property & Tax", "finance"),
        ("Money", "finance"),
        ("AI & Tech", "ai-tech"),
        ("AI", "ai-tech"),
        ("Tech", "ai-tech"),
        ("Technology", "ai-tech"),
    ],
)
def test_each_supported_category_alias_resolves_to_the_correct_hub(value, slug):
    assert server._public_category_hub_for_value(value) is server.PUBLIC_CATEGORY_HUBS[slug]


def test_specialist_and_uk_hub_queries_are_narrow_and_science_is_not_ai():
    expected = {
        "uk-news": ["UK News", "UK"],
        "business": ["Business", "Economy", "Economic"],
        "finance": ["Finance", "Tax", "Property", "Property & Tax", "Money"],
        "ai-tech": ["AI & Tech", "AI", "Tech", "Technology"],
    }
    for slug, categories in expected.items():
        query = {}
        server._apply_public_category_hub_filter(
            query,
            server.PUBLIC_CATEGORY_HUBS[slug],
        )
        assert query == {"category": {"$in": categories}}

    assert "Science" not in expected["ai-tech"]
    assert "Finance" not in expected["uk-news"]
    assert "Business" not in expected["uk-news"]
    assert "AI & Tech" not in expected["uk-news"]


def test_local_hub_requires_category_and_independent_local_evidence():
    query = {}
    server._apply_public_category_hub_filter(
        query,
        server.PUBLIC_CATEGORY_HUBS["local-news"],
    )

    assert query["$and"][0] == {"category": {"$in": ["Local News", "Local"]}}
    evidence = query["$and"][1]["$or"]
    assert {"is_local_source": True} in evidence
    assert {"scope": {"$in": ["cheshire", "local"]}} in evidence
    assert any("location" in clause for clause in evidence)


def test_article_matching_multiple_local_signals_is_returned_once(monkeypatch):
    collection = install_database(
        monkeypatch,
        [
            article(
                category="Local News",
                is_local_source=True,
                scope="cheshire",
                location="chester",
            )
        ],
    )

    response = asyncio.run(server.serve_public_hub_html("category/local-news"))
    html = response.body.decode()

    assert len(collection.queries) >= 1
    assert html.count("Cheshire business investment creates new jobs") == 1


def test_frontend_registers_reader_category_and_location_routes():
    source = FRONTEND_APP.read_text()
    assert "CATEGORY_HUBS.map" in source
    assert "path={`/category/${slug}`}" in source
    assert 'path="/:location"' in source
    assert "findLocationHub(location)" in source


def test_navigation_uses_the_supported_hub_inventory():
    assert 'from "../config/publicHubs"' in FRONTEND_HEADER.read_text()
    footer = FRONTEND_FOOTER.read_text()
    assert 'from "../config/publicHubs"' in footer
    for slug in EXPECTED_CATEGORIES:
        assert f"/category/{slug}" in footer


def test_sitemap_contains_every_supported_hub_and_no_unsupported_hub(monkeypatch):
    install_database(monkeypatch, [article()])

    response = asyncio.run(server.generate_sitemap())
    xml = response.body.decode()

    for slug in EXPECTED_CATEGORIES:
        assert f"https://cheshiretoday.co.uk/category/{slug}" in xml
    for slug in EXPECTED_LOCATIONS:
        assert f"https://cheshiretoday.co.uk/{slug}" in xml
    for slug in UNSUPPORTED:
        assert f"https://cheshiretoday.co.uk/{slug}" not in xml


@pytest.mark.parametrize("slug", sorted(EXPECTED_CATEGORIES))
def test_crawler_category_hub_has_content_and_self_canonical(monkeypatch, slug):
    install_database(monkeypatch, [article()])

    response = asyncio.run(server.serve_public_hub_html(f"category/{slug}"))
    html = response.body.decode()

    assert response.status_code == 200
    assert f'<link rel="canonical" href="https://cheshiretoday.co.uk/category/{slug}">' in html
    assert "Cheshire business investment creates new jobs" in html
    assert 'content="index, follow, max-image-preview:large"' in html


@pytest.mark.parametrize("slug", sorted(EXPECTED_LOCATIONS - {"cheshire-general"}))
def test_crawler_location_hub_has_content_and_self_canonical(monkeypatch, slug):
    collection = install_database(monkeypatch, [article()])

    response = asyncio.run(server.serve_public_hub_html(slug))
    html = response.body.decode()

    assert response.status_code == 200
    assert f'<link rel="canonical" href="https://cheshiretoday.co.uk/{slug}">' in html
    assert "Cheshire business investment creates new jobs" in html
    assert collection.queries[0]["location"] == slug


def test_public_hub_queries_exclude_archived_and_manual_review_articles(monkeypatch):
    collection = install_database(monkeypatch)

    asyncio.run(server.serve_public_hub_html("category/business"))
    query = collection.queries[0]

    assert query["$or"] == [
        {"archived": {"$exists": False}},
        {"archived": False},
    ]
    assert query["manual_review_hidden_from_public"] == {"$ne": True}


def test_empty_supported_hub_is_explicit_and_not_homepage(monkeypatch):
    install_database(monkeypatch)

    response = asyncio.run(server.serve_public_hub_html("northwich"))
    html = response.body.decode()

    assert '<link rel="canonical" href="https://cheshiretoday.co.uk/northwich">' in html
    assert "<h1>Northwich news | Cheshire Today</h1>" in html
    assert "No public articles are currently available for this section." in html
    assert "Cheshire Today | Local News, Business, AI &amp; Tech, Finance" not in html


def test_unsupported_hubs_are_absent_from_crawler_inventory(monkeypatch):
    install_database(monkeypatch)

    for slug in UNSUPPORTED:
        try:
            asyncio.run(server.serve_public_hub_html(slug))
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 404
        else:
            raise AssertionError(f"{slug} unexpectedly remained a crawler hub")
