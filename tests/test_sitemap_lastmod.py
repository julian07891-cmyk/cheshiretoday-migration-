import asyncio
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from types import SimpleNamespace

from bson import ObjectId

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
NOW = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)


class FakeCursor:
    def __init__(self, documents):
        self.documents = [dict(document) for document in documents]

    def sort(self, *args, **kwargs):
        return self

    def limit(self, count):
        self.documents = self.documents[:count]
        return self

    async def to_list(self, count):
        return self.documents[:count]


class ArticleCollection:
    def __init__(self, documents):
        self.documents = list(documents)
        self.find_calls = 0

    def find(self, query, projection=None):
        self.find_calls += 1
        public = [
            document
            for document in self.documents
            if document.get("manual_review_hidden_from_public") is not True
            and (
                document.get("archived") is not True
                or document.get("force_live") is True
            )
        ]
        return FakeCursor(public)


class AuthorityCollection:
    def __init__(self, documents=()):
        self.documents = list(documents)
        self.find_calls = 0

    def find(self, query, projection=None):
        self.find_calls += 1
        live = [
            document
            for document in self.documents
            if document.get("status") in {"published", "live"}
        ]
        return FakeCursor(live)


def article(number, **overrides):
    document = {
        "_id": ObjectId(f"6a619fe3d25f3963602b{number:04x}"),
        "title": f"Useful strategic update {number}",
        "category": "Business",
        "image": "https://example.com/image.jpg",
        "scope": "uk",
        "source": "Example Publisher",
        "publishedDate": "2026-07-10T09:00:00Z",
        "archived": False,
    }
    document.update(overrides)
    return document


def guide(slug="useful-guide", **overrides):
    document = {
        "slug": slug,
        "status": "live",
        "updatedAt": "2026-06-15T10:30:00Z",
        "sections": [{"content": "Useful guide content. " * 50}],
    }
    document.update(overrides)
    return document


def install_database(monkeypatch, articles, guides=()):
    article_collection = ArticleCollection(articles)
    authority_collection = AuthorityCollection(guides)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(
            articles=article_collection,
            authority_pages=authority_collection,
        ),
    )
    return article_collection, authority_collection


def sitemap_entries(response):
    root = ET.fromstring(response.body)
    entries = {}
    for url in root.findall("sm:url", NS):
        loc = url.findtext("sm:loc", namespaces=NS)
        entries[loc] = url.findtext("sm:lastmod", namespaces=NS)
    return entries


def canonical_article_url(document):
    slug = server._article_slug_from_title(document["title"])
    return f"https://cheshiretoday.co.uk/article/{document['_id']}/{slug}"


def test_article_date_prefers_modification_then_publication_then_creation():
    assert server._article_sitemap_datetime(
        {
            "updated_at": "2026-07-21T12:00:00Z",
            "publishedDate": "2026-07-19T12:00:00Z",
            "created_at": "2026-07-18T12:00:00Z",
        },
        now=NOW,
    ).date().isoformat() == "2026-07-21"
    assert server._article_sitemap_datetime(
        {
            "updated_at": "malformed",
            "publishedDate": "2026-07-19T12:00:00Z",
            "created_at": "2026-07-18T12:00:00Z",
        },
        now=NOW,
    ).date().isoformat() == "2026-07-19"
    assert server._article_sitemap_datetime(
        {"created_at": "2026-07-18T12:00:00Z"},
        now=NOW,
    ).date().isoformat() == "2026-07-18"


def test_future_and_malformed_dates_are_never_emitted():
    assert server._parse_sitemap_datetime("not-a-date", now=NOW) is None
    assert server._parse_sitemap_datetime("2026-07-24T00:00:00Z", now=NOW) is None
    assert server._sitemap_lastmod_value("", now=NOW) is None


def test_truthful_lastmods_for_home_index_article_guide_and_hubs(monkeypatch):
    local = article(
        1,
        title="Cheshire investment supports Chester jobs",
        category="Local News",
        scope="cheshire",
        location="chester",
        is_local_source=True,
        publishedDate="2026-07-18T09:00:00Z",
    )
    finance_alias = article(
        2,
        title="Tax policy update for households",
        category="Tax",
        publishedDate="2026-07-19T09:00:00Z",
    )
    ai_alias = article(
        3,
        title="Technology investment update",
        category="Tech",
        publishedDate="2026-07-20T09:00:00Z",
    )
    uk = article(
        4,
        title="National transport policy update",
        category="UK News",
        publishedDate="2026-07-17T09:00:00Z",
    )
    modified = article(
        5,
        title="Business investment update",
        category="Business",
        publishedDate="2026-07-16T09:00:00Z",
        updated_at="2026-07-21T09:00:00Z",
    )
    general = article(
        6,
        title="Cheshire-wide infrastructure update",
        category="Local News",
        scope="cheshire",
        is_local_source=True,
        is_cheshire_related=True,
        publishedDate="2026-07-15T09:00:00Z",
    )
    science = article(
        7,
        title="Generic science research update",
        category="Science",
        publishedDate="2026-07-22T09:00:00Z",
    )
    article_collection, authority_collection = install_database(
        monkeypatch,
        [local, finance_alias, ai_alias, uk, modified, general, science],
        [guide()],
    )

    entries = sitemap_entries(asyncio.run(server.generate_sitemap()))

    assert entries["https://cheshiretoday.co.uk/"] == "2026-07-21"
    assert entries["https://cheshiretoday.co.uk/article-index"] == "2026-07-21"
    assert "https://cheshiretoday.co.uk/latest-articles" not in entries
    assert entries[canonical_article_url(modified)] == "2026-07-21"
    assert entries[canonical_article_url(finance_alias)] == "2026-07-19"
    assert entries["https://cheshiretoday.co.uk/guides/useful-guide"] == "2026-06-15"
    assert entries["https://cheshiretoday.co.uk/category/finance"] == "2026-07-19"
    assert entries["https://cheshiretoday.co.uk/category/ai-tech"] == "2026-07-20"
    assert entries["https://cheshiretoday.co.uk/category/uk-news"] == "2026-07-17"
    assert entries["https://cheshiretoday.co.uk/category/local-news"] == "2026-07-18"
    assert entries["https://cheshiretoday.co.uk/chester"] == "2026-07-18"
    assert entries["https://cheshiretoday.co.uk/cheshire-general"] == "2026-07-15"
    assert canonical_article_url(science) not in entries
    assert article_collection.find_calls == 1
    assert authority_collection.find_calls == 1


def test_specialist_uk_scope_does_not_change_uk_hub_lastmod(monkeypatch):
    finance = article(
        10,
        category="Finance",
        scope="uk",
        publishedDate="2026-07-22T09:00:00Z",
    )
    business = article(
        11,
        category="Business",
        scope="uk",
        publishedDate="2026-07-21T09:00:00Z",
    )
    ai = article(
        12,
        category="AI & Tech",
        scope="uk",
        publishedDate="2026-07-20T09:00:00Z",
    )
    uk = article(
        13,
        category="UK News",
        scope="uk",
        publishedDate="2026-07-10T09:00:00Z",
    )
    install_database(monkeypatch, [finance, business, ai, uk])

    entries = sitemap_entries(asyncio.run(server.generate_sitemap()))

    assert entries["https://cheshiretoday.co.uk/category/uk-news"] == "2026-07-10"


def test_weak_local_label_does_not_change_local_hub_lastmod(monkeypatch):
    strong = article(
        20,
        title="Cheshire council investment update",
        category="Local News",
        scope="cheshire",
        location="crewe",
        publishedDate="2026-07-10T09:00:00Z",
    )
    weak = article(
        21,
        title="Generic national update",
        category="Local News",
        scope="uk",
        publishedDate="2026-07-22T09:00:00Z",
    )
    install_database(monkeypatch, [strong, weak])

    entries = sitemap_entries(asyncio.run(server.generate_sitemap()))

    assert entries["https://cheshiretoday.co.uk/category/local-news"] == "2026-07-10"


def test_empty_hubs_and_invalid_guide_dates_omit_lastmod(monkeypatch):
    business = article(
        30,
        category="Business",
        publishedDate="2026-07-10T09:00:00Z",
    )
    install_database(
        monkeypatch,
        [business],
        [guide(slug="invalid-date-guide", updatedAt="invalid")],
    )

    entries = sitemap_entries(asyncio.run(server.generate_sitemap()))

    assert entries["https://cheshiretoday.co.uk/category/finance"] is None
    assert entries["https://cheshiretoday.co.uk/northwich"] is None
    assert entries["https://cheshiretoday.co.uk/guides/invalid-date-guide"] is None


def test_archived_and_manual_review_articles_do_not_influence_dates_but_force_live_does(
    monkeypatch,
):
    public = article(40, publishedDate="2026-07-10T09:00:00Z")
    archived = article(
        41,
        publishedDate="2026-07-22T09:00:00Z",
        archived=True,
    )
    hidden = article(
        42,
        publishedDate="2026-07-21T09:00:00Z",
        manual_review_hidden_from_public=True,
    )
    force_live = article(
        43,
        publishedDate="2026-07-20T09:00:00Z",
        archived=True,
        force_live=True,
    )
    install_database(monkeypatch, [public, archived, hidden, force_live])

    entries = sitemap_entries(asyncio.run(server.generate_sitemap()))

    assert entries["https://cheshiretoday.co.uk/"] == "2026-07-20"
    assert canonical_article_url(archived) not in entries
    assert canonical_article_url(hidden) not in entries
    assert entries[canonical_article_url(force_live)] == "2026-07-20"


def test_malformed_article_date_omits_lastmod_without_removing_url(monkeypatch):
    malformed = article(
        50,
        publishedDate="malformed",
        updated_at="2027-01-01T00:00:00Z",
    )
    install_database(monkeypatch, [malformed])

    entries = sitemap_entries(asyncio.run(server.generate_sitemap()))

    assert canonical_article_url(malformed) in entries
    assert entries[canonical_article_url(malformed)] is None
    assert entries["https://cheshiretoday.co.uk/"] is None


def test_sitemap_inventory_count_is_unchanged(monkeypatch):
    public = article(60)
    install_database(monkeypatch, [public], [guide()])

    entries = sitemap_entries(asyncio.run(server.generate_sitemap()))

    expected_static = 1 + 1 + len(server.PUBLIC_LOCATION_HUBS) + len(
        server.PUBLIC_CATEGORY_HUBS
    )
    assert len(entries) == expected_static + 1 + 1
