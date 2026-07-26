import asyncio
import copy
import os
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server

FULL_REWRITE = (
    "The Cheshire project represents a substantial local investment with a published "
    "delivery timetable. Confirmed plans explain the work, its purpose and the expected "
    "benefits for residents, visitors and the wider local economy. The first phase will "
    "begin after the remaining routine preparations are complete.\n\n"
    "Project representatives said the programme would improve the existing site and "
    "support its long-term operation. Contractors will carry out the main construction "
    "and refurbishment work, while normal services will continue wherever practical. "
    "Further updates will be issued as milestones are reached.\n\n"
    "Local suppliers will be able to compete for suitable work packages during delivery. "
    "The investment is also expected to support employment and training opportunities, "
    "with recruitment details published through established channels. No unsupported "
    "job total has been announced.\n\n"
    "Planning and access arrangements are covered by the documents released for the "
    "scheme. Those records describe how deliveries, traffic and public access will be "
    "managed during the work. Any additional approvals will follow the normal public "
    "process before the relevant phase starts.\n\n"
    "The completed improvements are intended to strengthen the destination and provide "
    "a better service for the surrounding community. Financial information beyond the "
    "confirmed programme has not been published, and future phases remain subject to "
    "the timetable and approvals set out by the organisations involved."
)


class Cursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, _limit):
        return copy.deepcopy(self.documents)

    def sort(self, *_args):
        return self

    def skip(self, _value):
        return self

    def limit(self, _value):
        return self


class Collection:
    def __init__(self, existing=None):
        self.existing = list(existing or [])
        self.inserted = []

    def find(self, _query, _projection=None):
        return Cursor(self.existing)

    async def insert_one(self, document):
        self.inserted.append(copy.deepcopy(document))
        return SimpleNamespace(inserted_id=f"inserted-{len(self.inserted)}")


class FeedService:
    def __init__(self, candidates):
        self.candidates = candidates

    async def fetch_local_feeds_only(self):
        return copy.deepcopy(self.candidates)

    async def fetch_local_news(self):
        return []


class Perplexity:
    def __init__(self, rewrites=None):
        self.rewrites = rewrites or {}

    async def generate_article_content(self, **kwargs):
        return self.rewrites.get(kwargs["title"], kwargs["summary"])

    async def search_cheshire_news(self, **_kwargs):
        return []


def candidate(title, *, content="Local source text.", image=True, **values):
    document = {
        "title": title,
        "content": content,
        "summary": content,
        "source": "Cheshire Community News",
        "source_url": f"https://publisher.example/{title.lower().replace(' ', '-')}",
        "image": (
            f"https://publisher.example/{title.lower().replace(' ', '-')}.jpg"
            if image
            else ""
        ),
        "location": "Chester",
        "category": "Local News",
        "publishedDate": datetime.now(timezone.utc).isoformat(),
        "is_local_feed": True,
    }
    document.update(values)
    return document


def run_import(
    monkeypatch,
    candidates,
    rewrites=None,
    existing=None,
    archived_existing=None,
):
    articles = Collection(existing)
    archived = Collection(archived_existing)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=articles, archived_articles=archived),
    )
    monkeypatch.setattr(server, "news_feed_service", FeedService(candidates))
    monkeypatch.setattr(server, "perplexity_service", Perplexity(rewrites))
    monkeypatch.setattr(server, "ai_budget_available", lambda _amount: True)
    monkeypatch.setattr(
        server,
        "resolve_imported_article_image",
        lambda image, _url, fetch_page=None: image,
    )
    monkeypatch.setenv("ENABLE_RATIO_REBALANCE", "0")

    async def no_cap(keep=100):
        assert keep == 100

    monkeypatch.setattr(server, "cap_visible_articles", no_cap)
    result = asyncio.run(
        server._import_hybrid_news_internal(
            server.HybridNewsRequest(
                cheshire_articles=10,
                uk_articles=0,
                business_articles=0,
                tech_articles=0,
                use_perplexity=True,
            )
        )
    )
    return result, articles.inserted


def assert_hidden_manual_review(document):
    assert document["manual_review_hidden_from_public"] is True
    assert document["verification_status"] == "needs_manual_review"
    assert document["rewrite_status"] == "manual_review_required"
    assert document["archive_reason"] == "needs_manual_review"


def test_low_impact_non_crime_local_story_is_queued(monkeypatch):
    story = candidate("Chester volunteers open a community garden")

    result, inserted = run_import(monkeypatch, [story])

    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert len(inserted) == 1
    assert_hidden_manual_review(inserted[0])
    assert "Community feature" in inserted[0]["manual_review_reason"]
    for field in ("title", "source_url", "image", "location"):
        assert inserted[0][field] == story[field]


@pytest.mark.parametrize(
    "title",
    [
        "Lidl confirms new Ellesmere Port supermarket opening",
        "Chester restaurant opens after major refurbishment",
        "Warrington park attraction reopens after major improvements",
    ],
)
def test_high_value_local_investment_stories_use_strict_public_path(
    monkeypatch,
    title,
):
    story = candidate(title)

    result, inserted = run_import(
        monkeypatch,
        [story],
        rewrites={title: FULL_REWRITE},
    )

    assert result["public_imported"] == 1
    assert result["manual_review_imported"] == 0
    assert result["cheshire_from_rss"] == 1
    assert len(inserted) == 1
    assert inserted[0].get("manual_review_hidden_from_public") is not True


@pytest.mark.parametrize(
    ("story", "expected_reason"),
    [
        (
            candidate("Chester volunteers create a neighbourhood garden"),
            "Community feature",
        ),
        (
            candidate("Ten best places to live near Chester"),
            "Lifestyle",
        ),
    ],
)
def test_manual_review_reason_is_editorially_specific(
    monkeypatch,
    story,
    expected_reason,
):
    result, inserted = run_import(monkeypatch, [story])

    assert result["manual_review_imported"] == 1
    assert expected_reason in inserted[0]["manual_review_reason"]
    assert "failed useful-local relevance gate" not in inserted[0]["manual_review_reason"]


def test_short_local_rewrite_is_queued(monkeypatch):
    story = candidate("Chester council considers a new planning application")
    short = "The council is considering the application."

    result, inserted = run_import(
        monkeypatch,
        [story],
        rewrites={story["title"]: short},
    )

    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert inserted[0]["content"] == short
    assert_hidden_manual_review(inserted[0])
    assert "below public length threshold" in inserted[0]["manual_review_reason"]


def test_crime_duplicate_missing_image_and_spam_remain_rejected(monkeypatch):
    crime = candidate("Man jailed after Chester court hearing")
    duplicate = candidate("Existing Chester community story")
    no_image = candidate("Chester residents discuss local park", image=False)
    spam = candidate("Sponsored shopping deal and gift guide for Chester")
    missing_source = candidate(
        "Chester residents create a neighbourhood project",
        source_url="",
    )
    unsafe = candidate(
        "Chester volunteers discuss a neighbourhood project",
        content="Insiders suggest unsupported details about the project.",
    )
    existing = [{"title": duplicate["title"], "source_url": duplicate["source_url"]}]

    result, inserted = run_import(
        monkeypatch,
        [crime, duplicate, no_image, spam, missing_source, unsafe],
        existing=existing,
    )

    assert result["total_imported"] == 0
    assert result["manual_review_imported"] == 0
    assert inserted == []


def test_multiple_qualifying_local_candidates_may_be_queued(monkeypatch):
    candidates = [
        candidate("Chester residents launch a neighbourhood garden"),
        candidate(
            "Warrington volunteers create a community art project",
            location="Warrington",
        ),
        candidate(
            "Frodsham families organise a local heritage exhibition",
            location="Frodsham",
        ),
    ]

    result, inserted = run_import(monkeypatch, candidates)

    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 3
    assert len(inserted) == 3
    assert all(item["manual_review_hidden_from_public"] is True for item in inserted)


def test_archived_title_or_source_url_duplicate_is_not_inserted(monkeypatch):
    story = candidate("Chester volunteers create a community orchard")
    for archived_record in (
        {"title": story["title"], "source_url": "https://archive.example/other"},
        {"title": "Different archived title", "source_url": story["source_url"]},
    ):
        result, inserted = run_import(
            monkeypatch,
            [story],
            archived_existing=[archived_record],
        )
        assert result["manual_review_imported"] == 0
        assert inserted == []


def test_existing_manual_review_title_or_source_duplicate_is_not_inserted(
    monkeypatch,
):
    story = candidate("Warrington neighbours launch a community workshop")
    for existing_record in (
        {
            "title": story["title"],
            "source_url": "https://existing.example/other",
            "manual_review_hidden_from_public": True,
        },
        {
            "title": "Different Manual Review title",
            "source_url": story["source_url"],
            "manual_review_hidden_from_public": True,
        },
    ):
        result, inserted = run_import(
            monkeypatch,
            [story],
            existing=[existing_record],
        )
        assert result["manual_review_imported"] == 0
        assert inserted == []


class PublicQueryCollection:
    def __init__(self, documents):
        self.documents = copy.deepcopy(documents)
        self.queries = []

    def find(self, query, _projection=None):
        self.queries.append(copy.deepcopy(query))
        query_text = repr(query)
        if "manual_review_hidden_from_public" in query_text:
            visible = [
                document
                for document in self.documents
                if document.get("manual_review_hidden_from_public") is not True
            ]
        else:
            visible = self.documents
        return Cursor(visible)

    async def count_documents(self, query):
        query_text = repr(query)
        if "manual_review_hidden_from_public" in query_text:
            return sum(
                document.get("manual_review_hidden_from_public") is not True
                for document in self.documents
            )
        return len(self.documents)


def test_manual_review_records_do_not_enter_public_or_live_counts(monkeypatch):
    result, inserted = run_import(
        monkeypatch,
        [candidate("Chester neighbours create a community reading shelf")],
    )

    assert result["cheshire_from_rss"] == 0
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert inserted[0]["manual_review_hidden_from_public"] is True

    public_collection = PublicQueryCollection(inserted)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=public_collection),
    )
    response = asyncio.run(
        server.get_articles(
            search="community",
            limit=20,
            include_archived=False,
        )
    )

    assert response["articles"] == []
    assert response["total"] == 0
    assert any(
        {"manual_review_hidden_from_public": {"$ne": True}}
        in query.get("$and", [])
        for query in public_collection.queries
    )


def test_county_wide_civic_candidate_is_hidden_manual_review_only(monkeypatch):
    story = candidate(
        "Cheshire East council approves major infrastructure investment",
        location=None,
        county_wide_manual_review_candidate=True,
        county_wide_scope="cheshire_east",
    )

    result, inserted = run_import(monkeypatch, [story])

    assert result["cheshire_from_rss"] == 0
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert len(inserted) == 1
    assert_hidden_manual_review(inserted[0])
    assert inserted[0]["county_wide_manual_review_candidate"] is True
    assert inserted[0]["county_wide_scope"] == "cheshire_east"
    assert inserted[0].get("location") is None
    assert inserted[0]["manual_review_reason"] == (
        "Local RSS article needs manual review: County-wide Cheshire story "
        "without a qualifying town match"
    )


@pytest.mark.parametrize(
    "title",
    [
        "Families enjoy entertainment and lifestyle activities across Cheshire",
        "Annual summer event takes place across the county",
    ],
)
def test_low_value_county_wide_signal_is_not_retained(monkeypatch, title):
    story = candidate(
        title,
        location=None,
        county_wide_manual_review_candidate=True,
        county_wide_scope="cheshire",
    )

    result, inserted = run_import(monkeypatch, [story])

    assert result["cheshire_from_rss"] == 0
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 0
    assert inserted == []


def test_unsafe_county_wide_candidates_remain_rejected(monkeypatch):
    weak_image = candidate(
        "Across Cheshire councils announce a community programme",
        county_wide_manual_review_candidate=True,
        county_wide_scope="cheshire",
    )
    weak_image["image"] = (
        "https://www.warringtonguardian.co.uk/resources/images/20771109.jpg"
    )
    candidates = [
        candidate(
            "Police investigate county-wide Cheshire incident",
            county_wide_manual_review_candidate=True,
            county_wide_scope="cheshire",
        ),
        candidate(
            "Sponsored county-wide Cheshire shopping promotion",
            county_wide_manual_review_candidate=True,
            county_wide_scope="cheshire",
        ),
        candidate(
            "County-wide Cheshire community service expands",
            county_wide_manual_review_candidate=True,
            county_wide_scope="cheshire",
            image=False,
        ),
        candidate(
            "Across Cheshire residents launch a public service project",
            county_wide_manual_review_candidate=True,
            county_wide_scope="cheshire",
            source_url="",
        ),
        weak_image,
    ]

    result, inserted = run_import(monkeypatch, candidates)

    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 0
    assert inserted == []


def test_duplicate_county_wide_candidate_remains_rejected(monkeypatch):
    story = candidate(
        "Across Cheshire councils approve service investment",
        county_wide_manual_review_candidate=True,
        county_wide_scope="cheshire",
    )

    result, inserted = run_import(
        monkeypatch,
        [story],
        existing=[{"title": story["title"], "source_url": story["source_url"]}],
    )

    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 0
    assert inserted == []
