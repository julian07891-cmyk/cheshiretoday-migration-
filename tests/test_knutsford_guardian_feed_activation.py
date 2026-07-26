import asyncio
import copy

from backend.app.news_feed_service import RSS_FEEDS, NewsFeedService


KNUTSFORD_URL = "https://www.knutsfordguardian.co.uk/news/rss/"
RUNCORN_WIDNES_URL = "https://www.runcornandwidnesworld.co.uk/news/rss/"
NANTWICH_URL = "https://thenantwichnews.co.uk/feed/"


def article(title, *, summary="", content="", image="https://img.test/story.jpg"):
    return {
        "title": title,
        "summary": summary,
        "content": content,
        "image": image,
        "source_url": "https://www.knutsfordguardian.co.uk/news/story",
    }


def test_only_approved_newsquest_feeds_are_in_production_feed_registry():
    assert RSS_FEEDS["knutsford_guardian"] == {
        "url": KNUTSFORD_URL,
        "source": "Knutsford Guardian",
        "category": "Local News",
        "priority": 0,
        "is_local": True,
        "allowed_location_terms": {
            "knutsford": "knutsford",
            "wilmslow": "wilmslow",
            "alderley edge": "wilmslow",
            "handforth": "wilmslow",
        },
    }
    assert RSS_FEEDS["runcorn_widnes_world"] == {
        "url": RUNCORN_WIDNES_URL,
        "source": "Runcorn & Widnes World",
        "category": "Local News",
        "priority": 0,
        "is_local": True,
        "allowed_location_terms": {
            "runcorn": "warrington",
            "widnes": "warrington",
            "halton": "warrington",
        },
    }
    assert RSS_FEEDS["nantwich_news"] == {
        "url": NANTWICH_URL,
        "source": "Nantwich News",
        "category": "Local News",
        "priority": 0,
        "is_local": True,
        "allowed_location_terms": {
            "nantwich": "crewe",
        },
        "allowed_county_review_terms": {
            "cheshire east": "cheshire_east",
            "across cheshire": "cheshire",
            "across the county": "cheshire",
            "county-wide cheshire": "cheshire",
            "county wide cheshire": "cheshire",
        },
    }
    assert "northwich_guardian" not in RSS_FEEDS


def test_feed_area_matching_is_word_bounded_and_maps_existing_locations():
    match = NewsFeedService._match_allowed_feed_location
    terms = RSS_FEEDS["knutsford_guardian"]["allowed_location_terms"]
    assert match(article("Knutsford council approves plans"), terms) == "knutsford"
    assert match(article("New business opens in Wilmslow"), terms) == "wilmslow"
    assert match(article("Alderley Edge school investment"), terms) == "wilmslow"
    assert match(article("Handforth transport consultation"), terms) == "wilmslow"
    assert match(article("County-wide Cheshire police appeal"), terms) is None
    assert match(article("A business in Notknutsford expands"), terms) is None


def test_local_fetch_keeps_only_genuine_knutsford_feed_area_articles():
    service = NewsFeedService()
    calls = []
    knutsford_items = [
        article("Knutsford council approves new homes"),
        article("Wilmslow school receives investment"),
        article("Major refurbishment in Alderley Edge"),
        article("Handforth transport consultation opens"),
        article("County-wide Cheshire scheme announced"),
    ]

    async def fake_fetch(feed_key):
        calls.append(feed_key)
        if feed_key == "knutsford_guardian":
            return copy.deepcopy(knutsford_items)
        return []

    service.fetch_feed = fake_fetch
    result = asyncio.run(service.fetch_local_feeds_only())

    assert "knutsford_guardian" in calls
    assert [item["title"] for item in result] == [
        "Knutsford council approves new homes",
        "Wilmslow school receives investment",
        "Major refurbishment in Alderley Edge",
        "Handforth transport consultation opens",
    ]
    assert [item["location"] for item in result] == [
        "knutsford",
        "wilmslow",
        "wilmslow",
        "wilmslow",
    ]
    assert all(item["is_cheshire_related"] is True for item in result)
    assert all(item["is_local_feed"] is True for item in result)
    assert all(item["feed_priority"] == 1 for item in result)


def test_runcorn_widnes_matching_is_word_bounded_and_maps_to_warrington():
    match = NewsFeedService._match_allowed_feed_location
    terms = RSS_FEEDS["runcorn_widnes_world"]["allowed_location_terms"]
    assert match(article("Runcorn transport plans approved"), terms) == "warrington"
    assert match(article("New investment announced in Widnes"), terms) == "warrington"
    assert match(article("Halton schools receive funding"), terms) == "warrington"
    assert match(article("County-wide Cheshire scheme announced"), terms) is None
    assert match(article("A project by Haltonian Ltd"), terms) is None


def test_local_fetch_keeps_only_genuine_runcorn_widnes_area_articles():
    service = NewsFeedService()
    calls = []
    feed_items = [
        article("Runcorn transport plans approved"),
        article("New investment announced in Widnes"),
        article("Halton schools receive funding"),
        article("County-wide Cheshire scheme announced"),
    ]

    async def fake_fetch(feed_key):
        calls.append(feed_key)
        if feed_key == "runcorn_widnes_world":
            return copy.deepcopy(feed_items)
        return []

    service.fetch_feed = fake_fetch
    result = asyncio.run(service.fetch_local_feeds_only())

    assert "runcorn_widnes_world" in calls
    assert [item["title"] for item in result] == [
        "Runcorn transport plans approved",
        "New investment announced in Widnes",
        "Halton schools receive funding",
    ]
    assert all(item["location"] == "warrington" for item in result)
    assert all(item["is_cheshire_related"] is True for item in result)
    assert all(item["is_local_feed"] is True for item in result)
    assert all(item["feed_priority"] == 1 for item in result)


def test_nantwich_town_and_county_review_matching_are_kept_separate():
    service = NewsFeedService()
    items = [
        article("Nantwich hospital investment approved"),
        article("Cheshire East council approves infrastructure funding"),
        article("Regional investment announced for Staffordshire"),
        article("Nantwichian company announces a product launch"),
    ]

    async def fake_fetch(feed_key):
        if feed_key == "nantwich_news":
            return copy.deepcopy(items)
        return []

    service.fetch_feed = fake_fetch
    result = asyncio.run(service.fetch_local_feeds_only())

    assert [item["title"] for item in result] == [
        "Nantwich hospital investment approved",
        "Cheshire East council approves infrastructure funding",
    ]
    town, county = result
    assert town["location"] == "crewe"
    assert town.get("county_wide_manual_review_candidate") is not True
    assert "location" not in county
    assert county["county_wide_manual_review_candidate"] is True
    assert county["county_wide_scope"] == "cheshire_east"


def test_existing_local_feed_order_is_preserved_before_newsquest_additions():
    source = NewsFeedService.fetch_local_feeds_only.__code__.co_consts
    flattened = repr(source)
    assert flattened.index("warrington_guardian") < flattened.index(
        "chester_standard"
    )
    assert flattened.index("chester_standard") < flattened.index(
        "knutsford_guardian"
    )
    assert flattened.index("knutsford_guardian") < flattened.index(
        "runcorn_widnes_world"
    )
    assert flattened.index("runcorn_widnes_world") < flattened.index(
        "nantwich_news"
    )
