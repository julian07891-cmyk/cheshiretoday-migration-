import backend.app.news_feed_service as news_feed_module


HOMEPAGE_HTML = """
<html><body>
  <a href="/news/local-news/online-homeware-retailer-to-open-shop-310103">
    <img src="https://nub.news/api/image/788054/category.png" alt="Shop image">
  </a>
  <a href="/news/local-news/online-homeware-retailer-to-open-shop-310103">
    Online homeware retailer to open bricks-and-mortar store in Macclesfield
  </a>
  <a href="/news/local-news/online-homeware-retailer-to-open-shop-310103#comments">comments</a>
  <a href="/news/local-news/second-story-310104">Second story</a>
  <a href="/jobs/not-news">Job advert</a>
</body></html>
"""


ARTICLE_HTML = """
<html>
<head>
  <meta property="og:title" content="Online homeware retailer to open bricks-and-mortar store in Macclesfield">
  <meta property="og:description" content="A new furniture and homeware shop is opening on Charlotte Street in Macclesfield">
  <meta property="og:image" content="https://images.example/article.jpg">
  <meta property="article:published_time" content="2026-10-04T15:53:00+0100">
</head>
<body>
<main>
  <h1>Online homeware retailer to open bricks-and-mortar store in Macclesfield</h1>
  <p>By Matthew Hancock-Bruce</p>
  <p>A new furniture and homeware shop is opening in Macclesfield.</p>
  <p>Oh So Pretty &amp; Green has announced it will open at 29 Charlotte Street in November.</p>
  <p>The move gives the online retailer a permanent home in the town centre.</p>
  <p>Download our Nub News App!</p>
  <p>It’s FREE and available now</p>
  <p>Local news is in crisis.</p>
  <p>Please consider supporting us.</p>
  <p>Monthly supporters will enjoy an ad-free experience.</p>
</main>
</body>
</html>
"""


def test_nub_homepage_discovers_unique_local_news_urls():
    urls = news_feed_module.extract_nub_news_homepage_urls(
        HOMEPAGE_HTML,
        "https://macclesfield.nub.news/",
    )

    assert urls == [
        "https://macclesfield.nub.news/news/local-news/online-homeware-retailer-to-open-shop-310103",
        "https://macclesfield.nub.news/news/local-news/second-story-310104",
    ]


def test_nub_article_extracts_structured_metadata_and_clean_body():
    article = news_feed_module.parse_nub_news_article_html(
        ARTICLE_HTML,
        "https://macclesfield.nub.news/news/local-news/online-homeware-retailer-to-open-shop-310103",
        "macclesfield",
    )

    assert article["title"] == "Online homeware retailer to open bricks-and-mortar store in Macclesfield"
    assert article["summary"] == "A new furniture and homeware shop is opening on Charlotte Street in Macclesfield"
    assert article["image"] == "https://images.example/article.jpg"
    assert article["publishedDate"] == "2026-10-04T15:53:00+0100"
    assert article["source"] == "Nub News"
    assert article["source_url"].endswith("310103")
    assert article["nub_hub"] == "macclesfield"
    assert article["category"] == "Local News"
    assert article["is_local_source"] is True
    assert "A new furniture and homeware shop is opening in Macclesfield." in article["content"]
    assert "permanent home in the town centre" in article["content"]


def test_nub_article_removes_known_promotional_boilerplate():
    article = news_feed_module.parse_nub_news_article_html(
        ARTICLE_HTML,
        "https://macclesfield.nub.news/news/local-news/example-310103",
        "macclesfield",
    )

    body = article["content"]
    assert "Download our Nub News App" not in body
    assert "FREE and available" not in body
    assert "Local news is in crisis" not in body
    assert "Please consider supporting us" not in body
    assert "Monthly supporters" not in body


def test_nub_article_returns_empty_for_missing_html():
    assert news_feed_module.parse_nub_news_article_html(
        "",
        "https://macclesfield.nub.news/news/local-news/example-1",
        "macclesfield",
    ) == {}


def test_nub_article_can_reject_missing_required_metadata():
    html = "<html><body><main><p>Body only with no structured metadata.</p></main></body></html>"
    article = news_feed_module.parse_nub_news_article_html(
        html,
        "https://macclesfield.nub.news/news/local-news/example-2",
        "macclesfield",
    )

    assert article["title"] == ""
    assert article["image"] == ""
    assert article["publishedDate"] == ""


def test_nub_cross_hub_canonical_url_deduplication():
    first = {
        "title": "Age UK Cheshire welcomes social care announcement",
        "source_url": "https://sandbach.nub.news/news/local-news/age-uk-cheshire-welcomes-announcement-309895",
    }
    duplicate = {
        "title": "Age UK Cheshire welcomes social care announcement",
        "source_url": "https://congleton.nub.news/news/local-news/age-uk-cheshire-welcomes-announcement-309895#comments",
    }
    unique = {
        "title": "Congleton shop opens",
        "source_url": "https://congleton.nub.news/news/local-news/congleton-shop-opens-309999",
    }

    result = news_feed_module.deduplicate_nub_news_candidates(
        [first, duplicate, unique]
    )

    assert result == [first, unique]


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.requested = []

    async def get(self, url, **_kwargs):
        self.requested.append(url)
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response


def test_fetch_nub_news_hub_fetches_homepage_and_articles():
    base = "https://macclesfield.nub.news/"
    first = base + "news/local-news/story-one-310103"
    second = base + "news/local-news/story-two-310104"

    homepage = f"""
    <html><body>
      <a href="{first}">Story one</a>
      <a href="{first}#comments">Comments</a>
      <a href="{second}">Story two</a>
    </body></html>
    """

    first_html = ARTICLE_HTML
    second_html = ARTICLE_HTML.replace(
        "Online homeware retailer to open bricks-and-mortar store in Macclesfield",
        "Second Macclesfield business story",
    ).replace(
        "2026-10-04T15:53:00+0100",
        "2026-10-04T16:53:00+0100",
    )

    client = FakeClient({
        base: FakeResponse(homepage),
        first: FakeResponse(first_html),
        second: FakeResponse(second_html),
    })

    import asyncio
    articles = asyncio.run(
        news_feed_module.fetch_nub_news_hub(
            "macclesfield",
            client=client,
        )
    )

    assert client.requested == [base, first, second]
    assert len(articles) == 2
    assert articles[0]["nub_hub"] == "macclesfield"
    assert articles[1]["title"] == "Second Macclesfield business story"


def test_fetch_nub_news_hub_skips_broken_article_page():
    base = "https://sandbach.nub.news/"
    broken = base + "news/local-news/broken-story-310200"
    good = base + "news/local-news/good-story-310201"

    homepage = f"""
    <html><body>
      <a href="{broken}">Broken</a>
      <a href="{good}">Good</a>
    </body></html>
    """

    client = FakeClient({
        base: FakeResponse(homepage),
        broken: RuntimeError("network failure"),
        good: FakeResponse(ARTICLE_HTML),
    })

    import asyncio
    articles = asyncio.run(
        news_feed_module.fetch_nub_news_hub(
            "sandbach",
            client=client,
        )
    )

    assert len(articles) == 1
    assert articles[0]["nub_hub"] == "sandbach"


def test_fetch_nub_news_hubs_aggregates_and_deduplicates(monkeypatch):
    import asyncio

    calls = []

    async def fake_fetch(hub, client=None, timeout=12.0):
        calls.append(hub)
        if hub == "sandbach":
            return [
                {
                    "title": "Shared Cheshire care story",
                    "source_url": "https://sandbach.nub.news/news/local-news/shared-story-309895",
                    "nub_hub": "sandbach",
                },
                {
                    "title": "Sandbach unique story",
                    "source_url": "https://sandbach.nub.news/news/local-news/sandbach-unique-310001",
                    "nub_hub": "sandbach",
                },
            ]
        if hub == "congleton":
            return [
                {
                    "title": "Shared Cheshire care story",
                    "source_url": "https://congleton.nub.news/news/local-news/shared-story-309895",
                    "nub_hub": "congleton",
                },
                {
                    "title": "Congleton unique story",
                    "source_url": "https://congleton.nub.news/news/local-news/congleton-unique-310002",
                    "nub_hub": "congleton",
                },
            ]
        hub_ids = {"macclesfield": 310100, "nantwich": 310101, "crewe": 310102, "alsager": 310103}
        return [
            {
                "title": f"{hub.title()} unique story",
                "source_url": f"https://{hub}.nub.news/news/local-news/{hub}-unique-{hub_ids[hub]}",
                "nub_hub": hub,
            }
        ]

    monkeypatch.setattr(news_feed_module, "fetch_nub_news_hub", fake_fetch)

    hubs = [
        "macclesfield",
        "sandbach",
        "congleton",
        "nantwich",
        "crewe",
        "alsager",
    ]

    articles = asyncio.run(
        news_feed_module.fetch_nub_news_hubs(hubs)
    )

    assert calls == hubs
    assert len(articles) == 7
    assert sum(
        1 for article in articles
        if article["source_url"].endswith("309895")
    ) == 1
    assert {article["nub_hub"] for article in articles} >= {
        "macclesfield",
        "sandbach",
        "nantwich",
        "crewe",
        "alsager",
    }


def test_nub_news_configured_hubs_are_explicit_and_bounded():
    assert news_feed_module.NUB_NEWS_HUBS == (
        "macclesfield",
        "sandbach",
        "congleton",
        "nantwich",
        "crewe",
        "alsager",
        "chester",
        "wilmslow",
    )


def test_nub_hub_is_hint_not_authoritative_location():
    article = news_feed_module.parse_nub_news_article_html(
        ARTICLE_HTML,
        "https://macclesfield.nub.news/news/local-news/example-310103",
        "macclesfield",
    )

    assert article["nub_hub"] == "macclesfield"
    assert "location" not in article
    assert "priority_location" not in article


def test_fetch_configured_nub_news_uses_only_configured_hubs(monkeypatch):
    import asyncio

    observed = []

    async def fake_multi(hubs, client=None, timeout=12.0):
        observed.extend(hubs)
        return [{"title": "Example"}]

    monkeypatch.setattr(news_feed_module, "fetch_nub_news_hubs", fake_multi)

    result = asyncio.run(
        news_feed_module.fetch_configured_nub_news()
    )

    assert observed == list(news_feed_module.NUB_NEWS_HUBS)
    assert result == [{"title": "Example"}]


def test_select_nub_news_coverage_keeps_at_most_one_story_per_hub():
    articles = [
        {
            "title": "Macclesfield newest",
            "nub_hub": "macclesfield",
            "publishedDate": "2026-10-04T17:00:00+0100",
            "source_url": "https://macclesfield.nub.news/news/local-news/newest-310301",
        },
        {
            "title": "Macclesfield older",
            "nub_hub": "macclesfield",
            "publishedDate": "2026-10-04T15:00:00+0100",
            "source_url": "https://macclesfield.nub.news/news/local-news/older-310300",
        },
        {
            "title": "Sandbach newest",
            "nub_hub": "sandbach",
            "publishedDate": "2026-10-04T16:00:00+0100",
            "source_url": "https://sandbach.nub.news/news/local-news/newest-310401",
        },
    ]

    selected = news_feed_module.select_nub_news_coverage_candidates(articles)

    assert [item["title"] for item in selected] == [
        "Macclesfield newest",
        "Sandbach newest",
    ]


def test_select_nub_news_coverage_never_creates_location_from_hub():
    article = {
        "title": "Macclesfield business story",
        "nub_hub": "macclesfield",
        "publishedDate": "2026-10-04T17:00:00+0100",
        "source_url": "https://macclesfield.nub.news/news/local-news/story-310500",
    }

    selected = news_feed_module.select_nub_news_coverage_candidates([article])

    assert len(selected) == 1
    assert "location" not in selected[0]
    assert "priority_location" not in selected[0]


def test_fetch_local_feeds_only_includes_bounded_nub_supplement(monkeypatch):
    import asyncio
    from backend.app.news_feed_service import NewsFeedService

    service = NewsFeedService(enable_nub_news=True)

    async def fake_fetch_feed(feed_key):
        if feed_key == "cheshire_live_macclesfield":
            return [{
                "title": "Existing Cheshire Live Macclesfield story",
                "publishedDate": "2026-10-04T14:00:00+0100",
                "source_url": "https://cheshire-live.example/macclesfield",
                "image": "https://img.example/cl.jpg",
            }]
        if feed_key == "knutsford_guardian":
            return [{
                "title": "Knutsford council story",
                "summary": "Knutsford council story",
                "content": "Knutsford council story",
                "publishedDate": "2026-10-04T13:00:00+0100",
                "source_url": "https://knutsford.example/story",
                "image": "https://img.example/kg.jpg",
            }]
        return []

    nub = [
        {
            "title": "Macclesfield Nub story",
            "nub_hub": "macclesfield",
            "publishedDate": "2026-10-04T17:00:00+0100",
            "source_url": "https://macclesfield.nub.news/news/local-news/story-310700",
            "image": "https://img.example/nub1.jpg",
            "category": "Local News",
            "source": "Nub News",
        },
        {
            "title": "Macclesfield older Nub story",
            "nub_hub": "macclesfield",
            "publishedDate": "2026-10-04T16:00:00+0100",
            "source_url": "https://macclesfield.nub.news/news/local-news/story-310699",
            "image": "https://img.example/nub2.jpg",
            "category": "Local News",
            "source": "Nub News",
        },
        {
            "title": "Sandbach Nub story",
            "nub_hub": "sandbach",
            "publishedDate": "2026-10-04T16:30:00+0100",
            "source_url": "https://sandbach.nub.news/news/local-news/story-310701",
            "image": "https://img.example/nub3.jpg",
            "category": "Local News",
            "source": "Nub News",
        },
    ]

    async def fake_configured_nub_news(**_kwargs):
        return nub

    service.fetch_feed = fake_fetch_feed
    monkeypatch.setattr(
        news_feed_module,
        "fetch_configured_nub_news",
        fake_configured_nub_news,
    )

    result = asyncio.run(service.fetch_local_feeds_only())

    titles = [item["title"] for item in result]

    assert titles == [
        "Existing Cheshire Live Macclesfield story",
        "Knutsford council story",
        "Macclesfield Nub story",
        "Sandbach Nub story",
    ]

    nub_items = [item for item in result if item.get("source") == "Nub News"]
    assert len(nub_items) == 2
    assert all(item["feed_priority"] == 1 for item in nub_items)
    assert all(item["is_local_feed"] is True for item in nub_items)
    assert all(item["is_cheshire_related"] is True for item in nub_items)
    assert all("location" not in item for item in nub_items)
    assert all("priority_location" not in item for item in nub_items)


def test_nub_article_preserves_legitimate_text_after_inline_app_promo():
    html = ARTICLE_HTML.replace("<p>Download our Nub News App!</p>", "<p>Download our Nub News App!</p><p>The council said the scheme will create 25 jobs.</p>")
    article = news_feed_module.parse_nub_news_article_html(html, "https://macclesfield.nub.news/news/local-news/example-310800", "macclesfield")
    assert "The council said the scheme will create 25 jobs." in article["content"]


def test_nub_article_preserves_short_sentence_starting_with_by():
    html = ARTICLE_HTML.replace("<p>A new furniture and homeware shop is opening in Macclesfield.</p>", "<p>A new furniture and homeware shop is opening in Macclesfield.</p><p>By 2027, the scheme will create 25 jobs.</p>")
    article = news_feed_module.parse_nub_news_article_html(html, "https://macclesfield.nub.news/news/local-news/example-310801", "macclesfield")
    assert "By 2027, the scheme will create 25 jobs." in article["content"]
