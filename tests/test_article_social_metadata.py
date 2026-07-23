import asyncio
import os

from bson import ObjectId

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


def test_newsquest_article_uses_source_open_graph_image(monkeypatch):
    async def run():
        article = {
            "_id": ObjectId("6a619fe3d25f3963602b219b"),
            "id": "article-123",
            "title": "Farm shop submits new licence plans",
            "summary": "A Cheshire farm shop has submitted plans to expand its customer offering.",
            "content": "Article body.",
            "category": "Local News",
            "image": "https://www.chesterstandard.co.uk/resources/images/20025600/",
            "source_url": (
                "https://www.chesterstandard.co.uk/news/"
                "26295203.popular-chester-farm-shop-lodges-licence-application/"
            ),
            "publishedDate": "2026-07-21T08:00:00",
        }

        async def fake_find_article(article_id):
            assert article_id == "article-123"
            return article

        class FakeResponse:
            def read(self):
                return (
                    b'<meta property="og:image" '
                    b'content="https://www.chesterstandard.co.uk/'
                    b'resources/images/20025600.jpg?type=og-image">'
                )

        def fake_urlopen(request, timeout=8):
            assert request.full_url == article["source_url"]
            assert timeout == 8
            return FakeResponse()

        monkeypatch.setattr(
            server,
            "_find_article_by_any_id",
            fake_find_article,
        )

        import urllib.request

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

        response = await server.serve_article_html("article-123")
        html = response.body.decode("utf-8")

        expected = (
            "https://www.chesterstandard.co.uk/"
            "resources/images/20025600.jpg?type=og-image"
        )

        assert f'<meta property="og:image" content="{expected}">' in html
        assert (
            f'<meta property="og:image:secure_url" content="{expected}">'
            in html
        )
        assert (
            'content="https://www.chesterstandard.co.uk/'
            'resources/images/20025600/"'
            not in html
        )

    asyncio.run(run())

def test_contentful_article_uses_facebook_sized_social_image(monkeypatch):
    async def run():
        article = {
            "_id": ObjectId("6a619fe3d25f3963602b219c"),
            "id": "article-contentful",
            "title": "Council tax refund confirmed",
            "summary": (
                "A Cheshire homeowner successfully challenged the council "
                "tax band on their property."
            ),
            "content": "Article body.",
            "category": "Finance",
            "image": (
                "https://images.ctfassets.net/example/image/hero.jpg"
                "?fm=jpg&w=800&h=600&q=70&fl=progressive"
            ),
            "source_url": "https://example.com/story",
            "publishedDate": "2026-07-22T08:00:00",
        }

        async def fake_find_article(article_id):
            assert article_id == "article-contentful"
            return article

        monkeypatch.setattr(
            server,
            "_find_article_by_any_id",
            fake_find_article,
        )

        response = await server.serve_article_html("article-contentful")
        html = response.body.decode("utf-8")

        expected = (
            "https://images.ctfassets.net/example/image/hero.jpg"
            "?fm=jpg&amp;w=1200&amp;h=630&amp;fit=fill&amp;q=85"
        )

        assert f'<meta property="og:image" content="{expected}">' in html
        assert (
            f'<meta property="og:image:secure_url" content="{expected}">'
            in html
        )
        assert f'<meta name="twitter:image" content="{expected}">' in html
        assert "w=800" not in html

    asyncio.run(run())
