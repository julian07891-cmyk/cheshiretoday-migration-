import asyncio
import copy

from backend.app.news_feed_service import RSS_FEEDS, NewsFeedService


KNUTSFORD_URL = "https://www.knutsfordguardian.co.uk/news/rss/"


def article(title, *, summary="", content="", image="https://img.test/story.jpg"):
    return {
        "title": title,
        "summary": summary,
        "content": content,
        "image": image,
        "source_url": "https://www.knutsfordguardian.co.uk/news/story",
    }


def test_only_knutsford_guardian_is_added_to_production_feed_registry():
    config = RSS_FEEDS["knutsford_guardian"]
    assert config == {
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
    assert "northwich_guardian" not in RSS_FEEDS
    assert "runcorn_widnes_world" not in RSS_FEEDS
    assert "nantwich_news" not in RSS_FEEDS


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


def test_existing_local_feed_order_is_preserved_before_knutsford_addition():
    source = NewsFeedService.fetch_local_feeds_only.__code__.co_consts
    flattened = repr(source)
    assert flattened.index("warrington_guardian") < flattened.index(
        "chester_standard"
    )
    assert flattened.index("chester_standard") < flattened.index(
        "knutsford_guardian"
    )
