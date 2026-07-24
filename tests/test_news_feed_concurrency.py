import asyncio

from backend.app.news_feed_service import NewsFeedService


def test_fetch_all_feeds_uses_bounded_concurrency():
    service = NewsFeedService()
    service.feeds = {
        f"feed_{index}": {
            "url": f"https://example.com/{index}.xml",
            "source": f"Source {index}",
            "category": "UK News",
        }
        for index in range(20)
    }

    active = 0
    peak = 0

    async def fake_fetch_feed(_feed_key):
        nonlocal active, peak

        active += 1
        peak = max(peak, active)

        await asyncio.sleep(0.01)

        active -= 1
        return []

    service.fetch_feed = fake_fetch_feed

    asyncio.run(service.fetch_all_feeds())

    assert peak <= 8
