import asyncio
import ast
import copy
import os
import re
import socket
import subprocess
from datetime import datetime, timedelta, timezone
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


# Stage 2Z-BA: separate from FakeCursor above, whose no-op sort deliberately
# serves route/taxonomy tests. This fixture models only the scalar BSON types
# and query operators exercised below; it is not a MongoDB execution engine.
_LOCAL_MISSING = object()
_LOCAL_BASELINE = "23079ccc317b2a77455dbf8f568fcbb9c1f0163d"


def _local_bson_key(value):
    if value is _LOCAL_MISSING or value is None:
        return (1, 0)
    if isinstance(value, datetime):
        aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        # BSON dates have millisecond precision, including naive UTC dates.
        delta = aware.astimezone(timezone.utc).replace(tzinfo=None) - datetime(1970, 1, 1)
        milliseconds = delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000
        return (9, milliseconds)
    if isinstance(value, ObjectId):
        return (7, value.binary)
    if isinstance(value, str):
        return (3, value.encode("utf-8"))
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return (2, value)
    raise AssertionError(f"Unsupported synthetic BSON type: {type(value).__name__}")


def _local_matches(document, query):
    for field, condition in query.items():
        if field == "$and":
            if not all(_local_matches(document, clause) for clause in condition):
                return False
            continue
        if field == "$or":
            if not any(_local_matches(document, clause) for clause in condition):
                return False
            continue
        value = document.get(field, _LOCAL_MISSING)
        if not isinstance(condition, dict):
            if condition is None and value is _LOCAL_MISSING:
                continue
            if value != condition:
                return False
            continue
        for operator, operand in condition.items():
            if operator == "$exists":
                matches = (value is not _LOCAL_MISSING) == operand
            elif operator == "$ne":
                matches = value is _LOCAL_MISSING or value != operand
            elif operator == "$in":
                matches = value in operand
            else:
                raise AssertionError(f"Unsupported synthetic query operator: {operator}")
            if not matches:
                return False
    return True


class LocalChronologyCursor:
    def __init__(self, documents, projection, read):
        self.documents = copy.deepcopy(documents)
        self.projection = copy.deepcopy(projection)
        self.read = read
        self.offset = 0
        self.cap = None

    def sort(self, field, direction=None):
        specification = [(field, direction)] if isinstance(field, str) else field
        self.read["sort"] = copy.deepcopy(specification)
        # Stable passes implement compound key precedence. Equal-key insertion
        # order here is only a permitted Mongo result, NOT a database guarantee.
        for name, order in reversed(specification):
            assert order in (-1, 1)
            self.documents.sort(
                key=lambda item: _local_bson_key(item.get(name, _LOCAL_MISSING)),
                reverse=order == -1,
            )
        return self

    def skip(self, count):
        assert count >= 0
        self.offset = count
        self.read["skip"] = count
        return self

    def limit(self, count):
        assert count > 0, "Synthetic cursor refuses an unbounded Mongo limit"
        self.cap = count
        self.read["limit"] = count
        return self

    def max_time_ms(self, milliseconds):
        self.read["maxTimeMS"] = milliseconds
        return self

    async def to_list(self, count):
        assert isinstance(count, int) and count > 0, "No unbounded materialisation"
        assert self.cap is not None, "A database cursor limit is required"
        stop = min(count, self.cap)
        page = self.documents[self.offset:self.offset + stop]
        if self.projection is not None:
            assert any(self.projection.values()), "Use an explicit inclusion projection"
            page = [
                {key: value for key, value in item.items() if self.projection.get(key)}
                for item in page
            ]
        self.read["to_list"] = count
        self.read["returned"] = len(page)
        self.read["body_documents"] = sum("content" in item for item in page)
        return copy.deepcopy(page)


class LocalChronologyCollection:
    def __init__(self, documents):
        self.documents = copy.deepcopy(documents)
        self.reads = []

    def find(self, query, projection=None):
        read = {"query": copy.deepcopy(query), "projection": copy.deepcopy(projection)}
        self.reads.append(read)
        return LocalChronologyCursor(
            [item for item in self.documents if _local_matches(item, query)],
            projection,
            read,
        )

    async def count_documents(self, query, **kwargs):
        return sum(_local_matches(item, query) for item in self.documents)

    def aggregate(self, pipeline, **kwargs):
        # BA's reads audit hydrated API projections. Keep metadata aggregation
        # separately observable without weakening any historical assertion.
        simulator = _BECollection(self.documents)
        cursor = simulator.aggregate(pipeline, **kwargs)
        self.aggregate_reads = getattr(self, "__dict__").get("aggregate_reads", [])
        self.aggregate_reads.extend(simulator.reads)
        return cursor

    def __getattr__(self, name):
        raise AssertionError(f"Unsupported collection operation: {name}")


@pytest.fixture
def local_chronology_database(monkeypatch):
    def no_network(*_args, **_kwargs):
        raise AssertionError("Network forbidden in Local chronology synthetic tests")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setenv("UK_FILTER_NOISE", "1")

    def install(documents):
        collection = LocalChronologyCollection(documents)
        monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))
        return collection

    return install


def _local_story(number, published, **changes):
    item = {
        "_id": ObjectId(f"{number:024x}"),
        "title": f"Bulletin{number:05d} Detail{number:05d}",
        "summary": f"Cheshire civic information number {number}.",
        "content": f"Complete source reporting {number}. " * 50,
        "category": "Local News",
        "source": "Synthetic Local Source",
        "source_url": f"https://source.example.test/local/{number}",
        "image": f"https://images.example.test/{number}.jpg",
        "publishedDate": published,
        "is_local_source": True,
        "scope": "cheshire",
        "archived": False,
        "tags": [],
    }
    item.update(changes)
    return item


def _local_page(*, skip=0, limit=30):
    # Invoke the actual /api/articles handler, not an independent sorter.
    return asyncio.run(server.get_articles(
        category="Local News", skip=skip, limit=limit, with_total=True,
    ))


def _local_ids(response):
    return [item["id"] for item in response["articles"]]


def _local_old_pool():
    base = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)
    old = [_local_story(index + 1, base - timedelta(minutes=index)) for index in range(65)]
    recent = _local_story(1000, "2026-10-28T15:01:00+0000", source="Nub News")
    return old, recent


def test_local_bson_fixture_does_not_parse_strings_or_sort_chronologically():
    documents = [
        _local_story(4, None),
        _local_story(3, "zz-malformed"),
        _local_story(2, "2026-10-28T15:01:00Z"),
        _local_story(1, datetime(2026, 3, 1)),
    ]
    read = {}
    cursor = LocalChronologyCursor(documents, {"_id": 1}, read)
    result = asyncio.run(cursor.sort("publishedDate", -1).limit(4).to_list(4))
    assert [item["_id"] for item in result] == [documents[i]["_id"] for i in (3, 1, 2, 0)]
    assert _local_bson_key(None) == _local_bson_key(_LOCAL_MISSING)
    assert _local_bson_key(datetime(2026, 10, 28, 12)) == _local_bson_key(
        datetime(2026, 10, 28, 13, tzinfo=timezone(timedelta(hours=1)))
    )


def test_local_bson_fixture_applies_skip_limit_and_projection_after_sort():
    documents = [
        _local_story(1, "2026-10-28T12:00:00Z"),
        _local_story(2, datetime(2026, 10, 27, 12)),
        _local_story(3, datetime(2026, 10, 26, 12)),
    ]
    read = {}
    cursor = LocalChronologyCursor(documents, {"_id": 1, "publishedDate": 1}, read)
    page = asyncio.run(cursor.sort("publishedDate", -1).skip(1).limit(1).to_list(1))
    assert page == [{"_id": documents[2]["_id"], "publishedDate": documents[2]["publishedDate"]}]
    assert read["returned"] == 1
    assert read["body_documents"] == 0
    page[0]["publishedDate"] = "detached-result-only"
    assert documents[2]["publishedDate"] == datetime(2026, 10, 26, 12)


def test_local_bson_fixture_rejects_unbounded_materialisation():
    cursor = LocalChronologyCursor([], {"_id": 1}, {})
    with pytest.raises(AssertionError, match="unbounded materialisation"):
        asyncio.run(cursor.limit(1).to_list(None))


def test_local_category_recent_nub_precedes_more_than_two_pages_of_old_bson_dates(local_chronology_database):
    old, recent = _local_old_pool()
    local_chronology_database([*old, recent])
    result = _local_page()
    assert result["total"] == 66
    assert len(result["articles"]) == 30
    assert _local_ids(result) == [str(item["_id"]) for item in [recent, *old[:29]]]


@pytest.mark.parametrize("skip", [0, 30, 60])
def test_local_category_global_chronology_precedes_skip_and_limit(local_chronology_database, skip):
    old, recent = _local_old_pool()
    local_chronology_database([*old, recent])
    expected = [recent, *old][skip:skip + 30]
    assert _local_ids(_local_page(skip=skip)) == [str(item["_id"]) for item in expected]


def test_local_category_equivalent_instants_use_explicit_mongo_id_ascending_tie(local_chronology_database):
    # Prospective Local-only tie contract; current Mongo sort has no identity tie.
    values = [
        "2026-10-28T12:00:00Z",
        "2026-10-28T13:00:00+01:00",
        datetime(2026, 10, 28, 12, tzinfo=timezone.utc),
        datetime(2026, 10, 28, 12),
    ]
    documents = [_local_story(index + 1, value) for index, value in enumerate(values)]
    local_chronology_database(list(reversed(documents)))
    assert _local_ids(_local_page()) == [str(item["_id"]) for item in documents]


@pytest.mark.parametrize("reverse", [False, True])
def test_local_category_equal_dates_have_identity_tie_independent_of_scan_order(local_chronology_database, reverse):
    documents = [_local_story(i, datetime(2026, 10, 28, 12)) for i in (1, 2, 3)]
    local_chronology_database(list(reversed(documents)) if reverse else documents)
    assert _local_ids(_local_page()) == [str(item["_id"]) for item in documents]


def test_local_category_offsets_compare_instants_not_iso_lexical_order(local_chronology_database):
    newer = _local_story(1, "2026-10-28T11:30:00Z")
    older = _local_story(2, "2026-10-28T12:00:00+01:00")
    local_chronology_database([older, newer])
    assert _local_ids(_local_page()) == [str(newer["_id"]), str(older["_id"])]


def test_local_category_missing_and_malformed_dates_cannot_displace_valid_dates(local_chronology_database):
    valid = _local_story(1, "2026-10-28T12:00:00Z")
    malformed = _local_story(2, "zz-not-a-date", created_at="2099-01-01T00:00:00Z")
    missing = _local_story(3, None)
    absent = _local_story(4, None)
    absent.pop("publishedDate")
    local_chronology_database([malformed, missing, absent, valid])
    assert _local_ids(_local_page(limit=1)) == [str(valid["_id"])]


def test_local_category_adjacent_pages_are_complete_and_globally_ordered(local_chronology_database):
    base = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
    documents = [
        _local_story(i + 1, (base - timedelta(minutes=i)).isoformat() if i % 2 else base - timedelta(minutes=i))
        for i in range(12)
    ]
    local_chronology_database(list(reversed(documents)))
    pages = [_local_ids(_local_page(skip=offset, limit=4)) for offset in (0, 4, 8)]
    combined = [identifier for page in pages for identifier in page]
    assert len(combined) == len(set(combined)) == len(documents)
    assert set(combined) == {str(item["_id"]) for item in documents}
    assert combined == [str(item["_id"]) for item in documents]


def test_local_category_equal_date_pages_use_identity_order_without_gaps(local_chronology_database):
    date = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
    documents = [_local_story(i, date) for i in range(1, 9)]
    scan_order = [documents[i - 1] for i in (4, 8, 2, 6, 1, 7, 3, 5)]
    local_chronology_database(scan_order)
    pages = [_local_ids(_local_page(skip=offset, limit=2)) for offset in (0, 2, 4, 6)]
    combined = [identifier for page in pages for identifier in page]
    assert len(combined) == len(set(combined)) == 8
    assert set(combined) == {str(item["_id"]) for item in documents}
    assert combined == [str(item["_id"]) for item in documents]


def test_local_category_visibility_and_independent_locality_are_filtered_before_paging(local_chronology_database):
    date = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
    allowed = [
        _local_story(1, date),
        _local_story(2, date - timedelta(minutes=1), is_local_source=False, scope="cheshire"),
        _local_story(3, date - timedelta(minutes=2), is_local_source=False, scope="uk", location="chester"),
    ]
    excluded = [
        _local_story(10, date, archived=True, force_live=True),
        _local_story(11, date, manual_review_hidden_from_public=True, force_live=True),
        _local_story(12, date, is_local_source=False, scope="uk", location="london"),
        _local_story(13, date, category="Business"),
    ]
    local_chronology_database([*excluded, *allowed])
    response = _local_page()
    assert response["total"] == 3
    assert _local_ids(response) == [str(item["_id"]) for item in allowed]


def test_local_category_read_preserves_source_values_types_and_bounded_projection(local_chronology_database):
    documents = [
        _local_story(1, datetime(2026, 10, 28, 12)),
        _local_story(2, "2026-10-28T11:00:00+0000", source="Nub News"),
    ]
    collection = local_chronology_database(documents)
    before = copy.deepcopy(collection.documents)
    response = _local_page(limit=1)
    assert collection.documents == before
    assert type(collection.documents[1]["publishedDate"]) is str
    assert "created_at" not in collection.documents[1]
    assert len(response["articles"]) <= 1
    assert response["articles"][0]["publishedDate"] == documents[0]["publishedDate"]
    assert collection.reads
    assert sum(read["body_documents"] for read in collection.reads) <= 1
    for read in collection.reads:
        assert read["limit"] <= 1
        assert read["to_list"] <= 1
        assert read["returned"] <= 1
        assert read["projection"]["_id"] == 1
        assert {"title", "publishedDate"} <= set(read["projection"])
        # Current category projection includes content; do not pretend it is
        # metadata-only or require a renderer/policy change in this RED stage.
        # force_live is permitted metadata for preserving the shared exception;
        # it must not require another full-document read.
        assert set(read["projection"]) <= {
            "_id", "title", "content", "summary", "category", "author",
            "publishedDate", "image", "tags", "featured", "source",
            "source_url", "scope", "is_local_source", "force_live",
        }


def test_local_category_returned_source_date_values_remain_unchanged(local_chronology_database):
    documents = [
        _local_story(1, datetime(2026, 10, 28, 12, tzinfo=timezone.utc)),
        _local_story(2, "2026-10-28T11:00:00+0000", source="Nub News"),
    ]
    collection = local_chronology_database(documents)
    response = _local_page(limit=2)
    originals = {str(item["_id"]): item["publishedDate"] for item in documents}
    assert {item["id"]: item["publishedDate"] for item in response["articles"]} == originals
    assert collection.documents == documents


@pytest.mark.parametrize("title,eligible", [
    ("Chester council budget supports local businesses", True),
    ("Chester opinion: local council budget", False),
])
def test_local_chronology_does_not_redefine_shared_editorial_policy(title, eligible):
    # This is a policy control, not a claim that the category handler currently
    # invokes this helper. Adding that invocation needs its own explicit scope.
    assert server.is_public_article_editorially_eligible(_local_story(1, None, title=title)) is eligible


@pytest.mark.parametrize("changes", [
    {"title": "Chester opinion: council services"},
    {
        "title": "The Papers: Budget national press roundup",
        "is_local_source": False,
        "scope": "cheshire",
    },
])
def test_local_category_shared_editorial_veto_is_not_bypassed_by_locality(local_chronology_database, changes):
    # Separate policy-parity RED required by contract G. This is NOT evidence
    # that changing chronology alone will close the existing category veto gap.
    date = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
    excluded = _local_story(2, date, **changes)
    accepted = _local_story(1, date - timedelta(minutes=1))
    assert server.is_public_article_editorially_eligible(excluded) is False
    local_chronology_database([excluded, accepted])
    response = _local_page(limit=1)
    assert _local_ids(response) == [str(accepted["_id"])]


@pytest.mark.parametrize("changes", [
    {"is_local_source": True},
    {"is_local_source": False, "scope": "cheshire", "force_live": True},
])
def test_local_category_preserves_shared_local_and_force_live_exceptions(local_chronology_database, changes):
    story = _local_story(1, datetime(2026, 10, 28, 12), title="The Papers: Budget national press roundup", **changes)
    assert server.is_public_article_editorially_eligible(story) is True
    local_chronology_database([story])
    assert _local_ids(_local_page()) == [str(story["_id"])]


def _local_baseline_text(path):
    return subprocess.check_output(
        ["git", "show", f"{_LOCAL_BASELINE}:{path}"], cwd=ROOT, text=True,
    )


def test_local_chronology_preserves_other_server_surface_implementations():
    baseline = ast.parse(_local_baseline_text("backend/server.py"))
    current = ast.parse((ROOT / "backend/server.py").read_text())
    protected = {
        "get_article", "latest_articles_html", "generate_sitemap",
        "generate_news_sitemap", "serve_public_hub_html",
        "_remove_duplicates_internal", "cap_visible_articles",
    }
    def definitions(tree):
        return {
            node.name: ast.dump(node, include_attributes=False)
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in protected
        }
    assert set(definitions(current)) == protected
    assert definitions(current) == definitions(baseline)

    def preserved_get_articles_branches(tree):
        function = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_articles")
        branches = {}
        for node in ast.walk(function):
            if not isinstance(node, ast.If):
                continue
            condition = ast.unparse(node.test)
            if condition.startswith("search and len(search)") or condition.startswith("(not category or category == 'all')"):
                branches[condition] = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
        assert len(branches) == 2
        return branches
    assert preserved_get_articles_branches(current) == preserved_get_articles_branches(baseline)


def test_local_chronology_preserves_homepage_latest_hero_and_sidebar_contracts():
    path = "frontend/src/pages/HomePageV1.jsx"
    assert (ROOT / path).read_text() == _local_baseline_text(path)


def test_local_chronology_preserves_shared_public_editorial_helper():
    path = "backend/app/public_article_eligibility.py"
    assert (ROOT / path).read_text() == _local_baseline_text(path)


# Stage 2Z-BE: additive contract tests. BA fixtures and assertions above remain
# untouched. This small interpreter rejects unsupported aggregation operations;
# it is not a substitute for the completed real-Mongo BC7 benchmark.
def _be_date(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return value.replace(microsecond=value.microsecond // 1000 * 1000)


def _be_expression(expression, document):
    if isinstance(expression, str) and expression.startswith("$"):
        return document.get(expression[1:])
    if not isinstance(expression, dict):
        return expression
    assert len(expression) == 1, "Unsupported expression shape"
    operator, value = next(iter(expression.items()))
    if operator == "$type":
        item = _be_expression(value, document)
        return "date" if isinstance(item, datetime) else "string" if isinstance(item, str) else "null"
    if operator == "$eq":
        return _be_expression(value[0], document) == _be_expression(value[1], document)
    if operator == "$convert":
        assert value["to"] == "date"
        item = _be_date(_be_expression(value["input"], document))
        return item if item is not None else value.get("onError")
    if operator == "$switch":
        for branch in value["branches"]:
            if _be_expression(branch["case"], document):
                return _be_expression(branch["then"], document)
        return _be_expression(value.get("default"), document)
    raise AssertionError(f"Unsupported aggregation expression: {operator}")


def _be_selected_ids(query):
    if isinstance(query, dict):
        if isinstance(query.get("_id"), dict) and "$in" in query["_id"]:
            return query["_id"]["$in"]
        for value in query.values():
            result = _be_selected_ids(value)
            if result is not None:
                return result
    if isinstance(query, list):
        for value in query:
            result = _be_selected_ids(value)
            if result is not None:
                return result
    return None


class _BEReadCursor(LocalChronologyCursor):
    def max_time_ms(self, milliseconds):
        self.read["maxTimeMS"] = milliseconds
        return self

    async def to_list(self, count=None, **kwargs):
        count = kwargs.get("length", count)
        result = await super().to_list(count)
        if self.read.get("aggregate") and self.collection.after_selection:
            hook, self.collection.after_selection = self.collection.after_selection, None
            hook(self.collection)
        return result


class _BECollection(LocalChronologyCollection):
    def __init__(self, documents):
        super().__init__(documents)
        self.counts = []
        self.after_selection = None
        self.failure = None
        self.phase = None
        self.attempts = {"count": 0, "selection": 0, "hydration": 0}

    def _raise(self, phase):
        self.attempts[phase] += 1
        if self.phase == phase:
            raise self.failure

    async def count_documents(self, query, **kwargs):
        self.counts.append({"query": copy.deepcopy(query), **kwargs})
        self._raise("count")
        return sum(_local_matches(item, query) for item in self.documents)

    def find(self, query, projection=None, **kwargs):
        selected = _be_selected_ids(query)
        self._raise("hydration" if selected is not None else "selection")
        cursor = super().find(query, projection)
        cursor = _BEReadCursor(cursor.documents, projection, cursor.read)
        cursor.collection = self
        cursor.read.update(kwargs)
        return cursor

    def aggregate(self, pipeline, **kwargs):
        self._raise("selection")
        read = {"aggregate": True, "pipeline": copy.deepcopy(pipeline), **kwargs}
        self.reads.append(read)
        documents = copy.deepcopy(self.documents)
        cap = None
        for stage in pipeline:
            assert len(stage) == 1
            operator, value = next(iter(stage.items()))
            if operator == "$match":
                documents = [item for item in documents if _local_matches(item, value)]
            elif operator == "$project":
                assert value.get("_id", 1) != 0
                documents = [{key: item[key] for key, included in value.items() if included and key in item}
                             for item in documents]
                read["projection"] = copy.deepcopy(value)
            elif operator in ("$set", "$addFields"):
                for item in documents:
                    item.update({key: _be_expression(expr, item) for key, expr in value.items()})
            elif operator == "$sort":
                read["sort_fields"] = set().union(*(item.keys() for item in documents)) if documents else set()
                for key, direction in reversed(list(value.items())):
                    documents.sort(key=lambda item: _local_bson_key(item.get(key)), reverse=direction == -1)
            elif operator == "$skip":
                documents = documents[value:]
            elif operator == "$limit":
                assert 0 < value <= 600
                cap = value
                documents = documents[:value]
            else:
                raise AssertionError(f"Unsupported aggregation stage: {operator}")
        cursor = _BEReadCursor(documents, None, read)
        cursor.collection = self
        cursor.cap = cap
        return cursor


@pytest.fixture
def be_database(local_chronology_database, monkeypatch):
    local_chronology_database([])  # retain BA socket guards and synthetic policy settings
    monkeypatch.setattr(socket.socket, "connect_ex", lambda *_args: pytest.fail("Network forbidden"))

    def install(documents):
        collection = _BECollection(documents)
        monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))
        return collection
    return install


def _be_request(**parameters):
    import httpx

    async def request():
        # No lifespan/startup, real sockets, production DB, or provider transport.
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app, raise_app_exceptions=False),
                                     base_url="http://synthetic.test") as client:
            return await client.get("/api/articles", params={"category": "Local News", "with_total": "true", **parameters})
    return asyncio.run(request())


@pytest.mark.parametrize("representation", [
    datetime(2026, 10, 28, 12, 0, 0, 123000, tzinfo=timezone.utc),
    datetime(2026, 10, 28, 12, 0, 0, 123000),
    "2026-10-28T12:00:00.123001Z", "2026-10-28T13:00:00.123999+01:00",
    "2026-10-28T12:00:00.123777",
])
def test_be_millisecond_ties_use_identity_without_rewriting_values(be_database, representation):
    first = _local_story(1, representation)
    second = _local_story(2, "2026-10-28T12:00:00.123999Z")
    collection = be_database([second, first])
    before = copy.deepcopy(collection.documents)
    response = _local_page(limit=2)
    assert _local_ids(response) == [str(first["_id"]), str(second["_id"])]
    assert collection.documents == before
    assert {item["id"]: item["publishedDate"] for item in response["articles"]} == {
        str(item["_id"]): item["publishedDate"] for item in before}


@pytest.mark.parametrize("skip,limit", [(0, 1), (0, 30), (570, 30), (599, 1)])
def test_be_supported_window_boundaries_and_truthful_total(be_database, skip, limit):
    documents = [_local_story(i, "2026-10-28T12:00:00Z") for i in range(1, 602)]
    be_database(list(reversed(documents)))
    response = _be_request(skip=skip, limit=limit)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 601  # full matching count, not a fabricated 600 cap
    assert data["skip"] == skip and data["limit"] == limit
    assert _local_ids(data) == [str(item["_id"]) for item in documents[skip:skip + limit]]


@pytest.mark.parametrize("parameters", [
    {"skip": -1}, {"skip": 600}, {"skip": "1.5"}, {"skip": "not-an-integer"},
    {"limit": 0}, {"limit": -1}, {"limit": 31}, {"limit": "1.5"},
    {"limit": "not-an-integer"}, {"skip": 590, "limit": 20},
])
def test_be_invalid_pagination_is_422_without_database_work(be_database, parameters):
    collection = be_database([])
    response = _be_request(**parameters)
    assert response.status_code == 422
    assert collection.reads == [] and collection.counts == []


def test_be_default_limit_stays_twenty(be_database):
    be_database([_local_story(i, "2026-10-28T12:00:00Z") for i in range(1, 31)])
    response = _be_request()
    assert response.status_code == 200
    assert response.json()["limit"] == 20
    assert len(response.json()["articles"]) == 20


def test_be_resource_contract_and_body_hydration_bound(be_database):
    collection = be_database([_local_story(i, "2026-10-28T12:00:00Z") for i in range(1, 66)])
    assert _be_request(limit=30).status_code == 200
    selections = [read for read in collection.reads if read.get("aggregate")]
    hydrations = [read for read in collection.reads if not read.get("aggregate")]
    assert len(selections) == len(hydrations) == len(collection.counts) == 1
    selection, hydration = selections[0], hydrations[0]
    assert selection["maxTimeMS"] == 2000 and selection["allowDiskUse"] is False
    assert "content" not in selection["sort_fields"]
    first_project = next(stage["$project"] for stage in selection["pipeline"] if "$project" in stage)
    assert first_project == {"_id": 1, "publishedDate": 1}
    assert selection["to_list"] <= 30 and selection["returned"] <= 30
    assert len(_be_selected_ids(hydration["query"])) <= 30
    assert hydration["maxTimeMS"] == 2000
    assert hydration["limit"] <= 30 and hydration["to_list"] <= 30
    assert collection.counts[0]["maxTimeMS"] == 2000
    assert "sort" not in hydration  # restore selected order, not raw BSON order


@pytest.mark.parametrize("phase", ["count", "selection", "hydration"])
@pytest.mark.parametrize("kind,status", [("timeout", 503), ("unavailable", 503), ("unexpected", 500)])
def test_be_failures_are_truthful_private_and_never_retry(be_database, phase, kind, status):
    from pymongo.errors import ExecutionTimeout, ServerSelectionTimeoutError
    collection = be_database([_local_story(1, "2026-10-28T12:00:00Z")])
    errors = {"timeout": ExecutionTimeout, "unavailable": ServerSelectionTimeoutError, "unexpected": RuntimeError}
    collection.phase, collection.failure = phase, errors[kind]("PRIVATE_DB_PAYLOAD_SENTINEL")
    response = _be_request(limit=1)
    assert response.status_code == status
    assert "PRIVATE_DB_PAYLOAD_SENTINEL" not in response.text
    assert "articles" not in response.json() and "total" not in response.json()
    assert len(collection.counts) <= 1 and len(collection.reads) <= 2
    assert all(attempts <= 1 for attempts in collection.attempts.values())


@pytest.mark.parametrize("change", ["missing", "archived", "hidden", "category", "locality"])
def test_be_hydration_revalidates_without_refilling_or_mutating(be_database, change):
    documents = [_local_story(i, "2026-10-28T12:00:00Z") for i in range(1, 5)]
    collection = be_database(documents)
    expected_after_race = []

    def race(current):
        if change == "missing":
            current.documents = [item for item in current.documents if item["_id"] != documents[0]["_id"]]
        else:
            target = next(item for item in current.documents if item["_id"] == documents[0]["_id"])
            if change == "archived":
                target["archived"] = True
            elif change == "hidden":
                target["manual_review_hidden_from_public"] = True
            elif change == "category":
                target["category"] = "Business"
            else:
                target.update(is_local_source=False, scope="uk", location="london")
        current.documents.reverse()  # hydration cannot rely on collection order
        expected_after_race.extend(copy.deepcopy(current.documents))

    collection.after_selection = race
    response = _be_request(limit=3)
    assert response.status_code == 200
    assert expected_after_race, "Metadata selection must precede revalidation"
    assert _local_ids(response.json()) == [str(documents[i]["_id"]) for i in (1, 2)]
    assert collection.documents == expected_after_race
    assert sum(bool(read.get("aggregate")) for read in collection.reads) == 1
    hydration = [read for read in collection.reads if not read.get("aggregate")]
    assert len(hydration) == 1
    assert set(_be_selected_ids(hydration[0]["query"])) == {item["_id"] for item in documents[:3]}
    assert all(_local_matches(item, hydration[0]["query"]) is False for item in documents[3:])


def test_be_interpreter_normalizes_milliseconds_and_rejects_unsupported_operators():
    assert _be_date("2026-10-28T13:00:00.123999+01:00") == _be_date("2026-10-28T12:00:00.123001Z")
    assert _be_date("2026-10-28T12:00:00.123") == datetime(2026, 10, 28, 12, 0, 0, 123000, tzinfo=timezone.utc)
    assert _be_date("malformed") is None and _be_date(None) is None
    with pytest.raises(AssertionError, match="Unsupported aggregation expression"):
        _be_expression({"$unsupported": 1}, {})


def test_be_invalid_dates_are_last_and_do_not_gain_import_freshness(be_database):
    documents = [
        _local_story(1, "malformed", created_at="2099-01-01T00:00:00Z"),
        _local_story(2, None),
        _local_story(3, "2026-10-28T12:00:00.123Z"),
    ]
    documents[1].pop("publishedDate")
    collection = be_database(documents)
    before = copy.deepcopy(collection.documents)
    assert _local_ids(_local_page(limit=3)) == [str(documents[i]["_id"]) for i in (2, 0, 1)]
    assert collection.documents == before


def test_be_aggregation_fixture_executes_pipeline_and_preserves_options():
    documents = [_local_story(2, "2026-10-28T13:00:00.123999+01:00"),
                 _local_story(1, "2026-10-28T12:00:00.123001Z")]
    collection = _BECollection(documents)
    key = {"$switch": {"branches": [
        {"case": {"$eq": [{"$type": "$publishedDate"}, "date"]}, "then": "$publishedDate"},
        {"case": {"$eq": [{"$type": "$publishedDate"}, "string"]},
         "then": {"$convert": {"input": "$publishedDate", "to": "date", "onError": None, "onNull": None}}},
    ], "default": None}}
    cursor = collection.aggregate([
        {"$match": {"archived": False}}, {"$project": {"_id": 1, "publishedDate": 1}},
        {"$set": {"normalized": key}}, {"$sort": {"normalized": -1, "_id": 1}},
        {"$skip": 0}, {"$limit": 1},
    ], maxTimeMS=2000, allowDiskUse=False)
    result = asyncio.run(cursor.to_list(1))
    assert result[0]["_id"] == documents[1]["_id"]
    assert collection.documents == documents
    assert collection.reads[0]["maxTimeMS"] == 2000
    assert collection.reads[0]["allowDiskUse"] is False
    assert "content" not in collection.reads[0]["sort_fields"]


# Stage 2Z-BH: ineffective search must not escape the ordinary Local contract.
@pytest.mark.parametrize("search", ["", "x"])
def test_bh_ineffective_search_keeps_local_chronology_and_query_bounds(be_database, search):
    old, recent = _local_old_pool()
    excluded = [
        _local_story(2001, "2027-01-01T00:00:00Z", archived=True),
        _local_story(2002, "2027-01-01T00:00:00Z", manual_review_hidden_from_public=True),
        _local_story(2003, "2027-01-01T00:00:00Z", is_local_source=False, scope="uk", location="london"),
        _local_story(2004, "2027-01-01T00:00:00Z", category="Business"),
    ]
    collection = be_database([*old, recent, *excluded])
    before = copy.deepcopy(collection.documents)
    response = _be_request(search=search, limit=30)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 66
    assert _local_ids(data) == [str(item["_id"]) for item in [recent, *old[:29]]]
    assert collection.documents == before
    assert collection.counts[0]["maxTimeMS"] == 2000
    assert collection.attempts == {"count": 1, "selection": 1, "hydration": 1}
    selection, hydration = collection.reads
    assert selection["aggregate"] is True
    assert selection["maxTimeMS"] == 2000 and selection["allowDiskUse"] is False
    assert "content" not in selection["sort_fields"]
    assert selection["to_list"] <= 30 and selection["returned"] <= 30
    assert hydration["maxTimeMS"] == 2000
    assert len(_be_selected_ids(hydration["query"])) == 30
    assert hydration["limit"] == hydration["to_list"] == 30
    assert "sort" not in hydration


@pytest.mark.parametrize("parameters", [{"limit": 31}, {"skip": 600}, {"skip": 590, "limit": 20}])
def test_bh_one_character_search_cannot_bypass_pagination(be_database, parameters):
    collection = be_database([])
    response = _be_request(search="x", **parameters)
    assert response.status_code == 422
    assert collection.reads == [] and collection.counts == []


@pytest.mark.parametrize("phase", ["count", "selection", "hydration"])
@pytest.mark.parametrize("kind,status", [("timeout", 503), ("unavailable", 503), ("unexpected", 500)])
def test_bh_one_character_search_keeps_truthful_private_errors(be_database, phase, kind, status):
    from pymongo.errors import ExecutionTimeout, ServerSelectionTimeoutError
    collection = be_database([_local_story(1, "2026-10-28T12:00:00Z")])
    errors = {"timeout": ExecutionTimeout, "unavailable": ServerSelectionTimeoutError, "unexpected": RuntimeError}
    collection.phase, collection.failure = phase, errors[kind]("BH_PRIVATE_FAILURE_SENTINEL")
    response = _be_request(search="x", limit=1)
    assert response.status_code == status
    assert "BH_PRIVATE_FAILURE_SENTINEL" not in response.text
    assert "articles" not in response.json() and "total" not in response.json()
    assert all(attempts <= 1 for attempts in collection.attempts.values())


@pytest.mark.parametrize("search", ["xx", "long query"])
def test_bh_effective_search_keeps_existing_response_and_query(be_database, monkeypatch, search):
    be_database([])  # install socket guards; do not run application startup
    document = article(id="existing-search-identity", title=f"Cheshire {search} reporting")
    collection = FakeCollection([document])
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))
    response = _be_request(search=search, skip=0, limit=31)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"articles", "total", "search"}
    assert data["search"] == search and data["total"] == 1
    assert data["articles"][0]["id"] == "existing-search-identity"
    assert "_id" not in data["articles"][0]
    assert data["articles"][0]["canonicalUrl"].startswith("https://cheshiretoday.co.uk/article/")
    assert collection.queries == [{"$and": [
        {"$or": [{"archived": {"$exists": False}}, {"archived": False}]},
        {"manual_review_hidden_from_public": {"$ne": True}},
        {"$or": [{"title": {"$regex": re.escape(search), "$options": "i"}},
                 {"content": {"$regex": re.escape(search), "$options": "i"}}]},
    ]}]


@pytest.mark.parametrize("search", ["", "x"])
@pytest.mark.parametrize("category,include_archived", [("Business", False), ("Local News", True)])
def test_bh_nonlocal_and_archive_inclusive_paths_remain_unchanged(be_database, search, category, include_archived):
    documents = [_local_story(i, datetime(2026, 10, 28, 12), category=category,
                              archived=include_archived) for i in range(1, 33)]
    collection = be_database(documents)
    response = _be_request(category=category, include_archived=str(include_archived).lower(), search=search, limit=31)
    assert response.status_code == 200
    assert len(response.json()["articles"]) == 31
    assert response.json()["total"] == 32
    assert len(collection.reads) == 1 and not collection.reads[0].get("aggregate")
    assert collection.reads[0]["sort"] == [("publishedDate", -1)]
    assert "maxTimeMS" not in collection.counts[0]
