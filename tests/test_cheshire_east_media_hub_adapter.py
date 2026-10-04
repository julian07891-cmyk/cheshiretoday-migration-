from backend.app import news_feed_service as news_feed_module


INDEX_HTML = """
<div class="media-info">25/09/2026 - Media release</div>
<img style="margin-bottom: 10px;" src="/images/media-hub/Congleton-Family-Hub-refurb.png"
     alt="25/09/2026 - Congleton Family Hub expands support for local children and families" />
<h3><a href="/council_and_democracy/council_information/media_hub/media_releases/congleton-family-hub-expands-support-for-local-children-and-families.aspx">
25/09/2026 - Congleton Family Hub expands support for local children and families
</a></h3>
<p>Congleton Family Hub has expanded</p>
"""


ARTICLE_HTML = """
<html>
<head>
<meta name="description" content="Congleton Family Hub has expanded" />
<meta property="og:image" content="https://www.cheshireeast.gov.uk/images/non_user/cec-og.png" />
</head>
<body>
<main>
<h1><strong>Congleton Family Hub expands support for local children and families</strong></h1>
<p>25 September 2026</p>
<p>Families in Congleton are set to benefit from enhanced facilities and expanded support services.</p>
<p>The investment will help create even more opportunities for children and young people.</p>
<p>For more information about Family Hubs and the support available across Cheshire East, visit</p>
<p>www.cheshireeast.gov.uk/familyhubs</p>
</main>
</body>
</html>
"""


def test_extract_cheshire_east_media_hub_index_candidates():
    candidates = news_feed_module.extract_cheshire_east_media_hub_candidates(INDEX_HTML)

    assert candidates == [
        {
            "title": "Congleton Family Hub expands support for local children and families",
            "summary": "Congleton Family Hub has expanded",
            "publishedDate": "2026-09-25T00:00:00+0100",
            "source_url": "https://www.cheshireeast.gov.uk/council_and_democracy/council_information/media_hub/media_releases/congleton-family-hub-expands-support-for-local-children-and-families.aspx",
            "image": "https://www.cheshireeast.gov.uk/images/media-hub/Congleton-Family-Hub-refurb.png",
            "source": "Cheshire East Council",
            "category": "Local News",
            "is_real_news": True,
            "is_local_source": True,
            "is_local_feed": True,
        }
    ]


def test_parse_cheshire_east_media_hub_article_body_and_date():
    article = news_feed_module.parse_cheshire_east_media_hub_article_html(
        ARTICLE_HTML,
        "https://www.cheshireeast.gov.uk/council_and_democracy/council_information/media_hub/media_releases/congleton-family-hub-expands-support-for-local-children-and-families.aspx",
    )

    assert article["title"] == "Congleton Family Hub expands support for local children and families"
    assert article["publishedDate"] == "2026-09-25T00:00:00+0100"
    assert article["summary"] == "Congleton Family Hub has expanded"
    assert article["content"] == (
        "Families in Congleton are set to benefit from enhanced facilities and expanded support services.\n\n"
        "The investment will help create even more opportunities for children and young people."
    )
    assert article["source"] == "Cheshire East Council"
    assert article["category"] == "Local News"
    assert article["is_real_news"] is True
    assert article["is_local_source"] is True
    assert article["is_local_feed"] is True
    assert "location" not in article
    assert "priority_location" not in article
    assert article.get("image") in (None, "")


def test_cheshire_east_media_hub_dates_follow_uk_dst():
    assert news_feed_module._cheshire_east_parse_date("25 September 2026") == "2026-09-25T00:00:00+0100"
    assert news_feed_module._cheshire_east_parse_date("15 January 2027") == "2027-01-15T00:00:00+0000"


def test_fetch_cheshire_east_media_hub_is_bounded_and_fail_safe():
    import asyncio

    index_html = """
    <div class="media-info">02/10/2026 - Media release</div>
    <h3><a href="/council_and_democracy/council_information/media_hub/media_releases/first.aspx">02/10/2026 - First story</a></h3><p>First summary</p>
    <div class="media-info">01/10/2026 - Media release</div>
    <h3><a href="/council_and_democracy/council_information/media_hub/media_releases/second.aspx">01/10/2026 - Second story</a></h3><p>Second summary</p>
    <div class="media-info">30/09/2026 - Media release</div>
    <h3><a href="/council_and_democracy/council_information/media_hub/media_releases/third.aspx">30/09/2026 - Third story</a></h3><p>Third summary</p>
    <div class="media-info">29/09/2026 - Media release</div>
    <h3><a href="/council_and_democracy/council_information/media_hub/media_releases/fourth.aspx">29/09/2026 - Fourth story</a></h3><p>Fourth summary</p>
    """

    def article_html(title, date):
        return f"""
        <html><head><meta name="description" content="{title} summary"></head>
        <body><main><h1>{title}</h1><p>{date}</p><p>{title} body</p></main></body></html>
        """

    responses = {
        news_feed_module.CHESHIRE_EAST_MEDIA_HUB_URL: index_html,
        news_feed_module.CHESHIRE_EAST_MEDIA_HUB_BASE_URL + "/council_and_democracy/council_information/media_hub/media_releases/first.aspx": article_html("First story", "2 October 2026"),
        news_feed_module.CHESHIRE_EAST_MEDIA_HUB_BASE_URL + "/council_and_democracy/council_information/media_hub/media_releases/second.aspx": article_html("Second story", "1 October 2026"),
        news_feed_module.CHESHIRE_EAST_MEDIA_HUB_BASE_URL + "/council_and_democracy/council_information/media_hub/media_releases/third.aspx": article_html("Third story", "30 September 2026"),
    }

    class FakeResponse:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self):
            self.calls = []

        async def get(self, url):
            self.calls.append(url)
            if url not in responses:
                raise RuntimeError("unexpected url")
            return FakeResponse(responses[url])

    client = FakeClient()
    result = asyncio.run(
        news_feed_module.fetch_cheshire_east_media_hub(
            client=client,
            max_articles=3,
         )
    )

    assert [item["title"] for item in result] == [
        "First story",
        "Second story",
        "Third story",
    ]
    assert len(client.calls) == 4
    assert all(item["source"] == "Cheshire East Council" for item in result)
    assert all(item["is_local_source"] is True for item in result)
    assert all(item["is_local_feed"] is True for item in result)
    assert all("location" not in item for item in result)
    assert all("priority_location" not in item for item in result)


def test_fetch_cheshire_east_media_hub_index_failure_returns_empty():
    import asyncio

    class FailingClient:
        async def get(self, url):
            raise RuntimeError("index unavailable")

    result = asyncio.run(
        news_feed_module.fetch_cheshire_east_media_hub(
            client=FailingClient(),
            max_articles=3,
        )
    )

    assert result == []


def test_fetch_cheshire_east_media_hub_article_failure_skips_and_continues():
    import asyncio

    index_html = """
    <div class="media-info">02/10/2026 - Media release</div>
    <h3><a href="/council_and_democracy/council_information/media_hub/media_releases/first.aspx">02/10/2026 - First story</a></h3><p>First summary</p>
    <div class="media-info">01/10/2026 - Media release</div>
    <h3><a href="/council_and_democracy/council_information/media_hub/media_releases/second.aspx">01/10/2026 - Second story</a></h3><p>Second summary</p>
    """

    first_url = news_feed_module.CHESHIRE_EAST_MEDIA_HUB_BASE_URL + "/council_and_democracy/council_information/media_hub/media_releases/first.aspx"
    second_url = news_feed_module.CHESHIRE_EAST_MEDIA_HUB_BASE_URL + "/council_and_democracy/council_information/media_hub/media_releases/second.aspx"

    class FakeResponse:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None

    class FakeClient:
        async def get(self, url):
            if url == news_feed_module.CHESHIRE_EAST_MEDIA_HUB_URL:
                return FakeResponse(index_html)
            if url == first_url:
                raise RuntimeError("article unavailable")
            if url == second_url:
                return FakeResponse("<main><h1>Second story</h1><p>1 October 2026</p><p>Second body</p></main>")
            raise RuntimeError("unexpected url")

    result = asyncio.run(
        news_feed_module.fetch_cheshire_east_media_hub(
            client=FakeClient(),
            max_articles=2,
        )
    )

    assert [item["title"] for item in result] == ["Second story"]


def test_fetch_local_feeds_only_includes_cheshire_east_media_hub(monkeypatch):
    import asyncio
    from backend.app.news_feed_service import NewsFeedService

    service = NewsFeedService(enable_cheshire_east_media_hub=True)

    async def fake_fetch_feed(feed_key):
        return []

    async def fake_media_hub(**_kwargs):
        return [{
            "title": "Congleton Family Hub expands support",
            "summary": "Congleton Family Hub has expanded",
            "content": "Council release body",
            "publishedDate": "2026-09-25T00:00:00+0100",
            "source_url": "https://www.cheshireeast.gov.uk/example.aspx",
            "image": "https://www.cheshireeast.gov.uk/images/example.png",
            "source": "Cheshire East Council",
            "category": "Local News",
            "is_real_news": True,
            "is_local_source": True,
            "is_local_feed": True,
        }]

    service.fetch_feed = fake_fetch_feed
    monkeypatch.setattr(
        news_feed_module,
        "fetch_cheshire_east_media_hub",
        fake_media_hub,
    )

    result = asyncio.run(service.fetch_local_feeds_only())

    assert [item["title"] for item in result] == [
        "Congleton Family Hub expands support"
    ]
    item = result[0]
    assert item["source"] == "Cheshire East Council"
    assert item["feed_priority"] == 1
    assert item["is_local_feed"] is True
    assert item["is_cheshire_related"] is True
    assert "location" not in item
    assert "priority_location" not in item
