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
from backend.app.news_feed_service import NewsFeedService


SOURCE_URL = "https://www.theguardian.com/money/example"


class FakeCursor:
    def __init__(self, documents):
        self.documents = list(documents)

    async def to_list(self, _length):
        return copy.deepcopy(self.documents)


class FakeCollection:
    def __init__(self):
        self.inserted = []

    def find(self, _query, _projection=None):
        return FakeCursor([])

    async def insert_one(self, document):
        self.inserted.append(copy.deepcopy(document))
        return SimpleNamespace(inserted_id="offline-id")


class FakeFeeds:
    def __init__(self, article):
        self.article = copy.deepcopy(article)

    async def fetch_all_feeds(self):
        return [copy.deepcopy(self.article)]

    async def fetch_local_feeds_only(self):
        return []

    async def fetch_local_news(self):
        return []


class FakePerplexity:
    def __init__(self, rewrite):
        self.rewrite = rewrite
        self.rewrite_calls = 0

    async def generate_article_content(self, **_kwargs):
        self.rewrite_calls += 1
        if isinstance(self.rewrite, Exception):
            raise self.rewrite
        return self.rewrite


def source_preview():
    return (
        "The cost of living remains high for students.\n\n"
        "Household budgets remain under pressure across the country.\n\n"
        "Continue reading..."
    )


def complete_rewrite():
    paragraphs = [
        "Published figures describe the financial pressures facing students. The data compares maintenance support with typical household costs and explains the reported gap.",
        "Accommodation remains the largest regular expense for many students. Rent levels vary by city, property type and whether utility bills are included in the agreement.",
        "Universities publish details of bursaries and hardship funds through their official support services. Eligibility and application requirements differ between institutions.",
        "Budgeting tools can help students separate rent and essential bills from discretionary spending. Providers recommend checking balances before committing to larger purchases.",
        "Student bank accounts may include interest-free overdrafts or other incentives. Applicants should compare repayment terms as well as any introductory benefits offered.",
        "Discount schemes can reduce some travel, food and entertainment costs. The available savings depend on the retailer and may require current student identification.",
        "Meal planning is another way to make spending more predictable. Preparing a shopping list can reduce waste and limit unplanned purchases during the week.",
        "Support advisers recommend reviewing a budget when income or accommodation costs change. Verified guidance remains available through university and public advice services.",
    ]
    return "\n\n".join(paragraphs)


def rss_candidate():
    return {
        "id": "feed-id",
        "title": "Student budgets remain under pressure as costs rise",
        "content": source_preview(),
        "summary": "Students continue to face higher household costs.",
        "source": "The Guardian",
        "source_url": SOURCE_URL,
        "category": "Finance",
        "image": "https://i.guim.co.uk/example.jpg",
        "publishedDate": datetime.now(timezone.utc).isoformat(),
        "is_cheshire_related": False,
    }


def run_hybrid(monkeypatch, *, ai_available, rewrite=None, source_content=None):
    articles = FakeCollection()
    archived = FakeCollection()
    perplexity = FakePerplexity(rewrite)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=articles, archived_articles=archived),
    )
    article = rss_candidate()
    if source_content is not None:
        article["content"] = source_content
    monkeypatch.setattr(server, "news_feed_service", FakeFeeds(article))
    monkeypatch.setattr(server, "perplexity_service", perplexity)
    monkeypatch.setattr(server, "ai_budget_available", lambda _amount: ai_available)

    async def no_cap(keep=100):
        assert keep == 100

    monkeypatch.setattr(server, "cap_visible_articles", no_cap)
    result = asyncio.run(
        server._import_hybrid_news_internal(
            server.HybridNewsRequest(
                cheshire_articles=0,
                uk_articles=1,
                business_articles=0,
                tech_articles=0,
                use_perplexity=True,
            )
        )
    )
    return result, articles.inserted, perplexity


def test_clean_html_preserves_block_boundaries_without_splitting_inline_text():
    html = (
        "<p>Eligible for a <strong>student</strong> bursary</p>"
        "<p>Like late-night study sessions &amp; shared meals.</p>"
        "<div>Students are more money-conscious than ever.</div>"
        "<div>“It is difficult,” an adviser said.</div>"
    )

    cleaned = NewsFeedService()._clean_html(html)

    assert "student bursary" in cleaned
    assert "bursaryLike" not in cleaned
    assert "bursary\n\nLike" in cleaned
    assert "ever.“It" not in cleaned
    assert "ever.\n\n“It" in cleaned
    assert "sessions & shared" in cleaned


def test_terminal_continuation_variants_are_detected_and_removed():
    for marker in (
        "Continue reading",
        "Continue reading...",
        "Continue reading…",
        "Continue reading:",
        "Continue reading -",
        "READ MORE...",
        "Read more…",
        "Full story...",
    ):
        value = f"Complete sentence.\n\n{marker}"
        assert server.has_terminal_rss_continuation_marker(value) is True
        assert server.sanitize_rss_text(value) == "Complete sentence."


@pytest.mark.parametrize("line_ending", ["\n", "\r\n", "\r"])
def test_terminal_marker_normalises_line_endings_before_detection(line_ending):
    value = f"First paragraph.{line_ending}{line_ending}Continue reading... \t "

    assert server.has_terminal_rss_continuation_marker(value) is True
    assert server.sanitize_rss_text(value) == "First paragraph."


def test_continuation_phrase_inside_prose_is_not_detected_or_removed():
    for value in (
        "Readers should continue reading the guidance before applying.",
        'The minister said people should "continue reading" the document.',
    ):
        assert server.has_terminal_rss_continuation_marker(value) is False
        assert server.sanitize_rss_text(value) == value

    non_terminal = (
        "An editor introduced the source material.\n\n"
        "Continue reading...\n\n"
        "Further verified reporting follows."
    )
    assert server.has_terminal_rss_continuation_marker(non_terminal) is False
    assert server.sanitize_rss_text(non_terminal) == non_terminal


def test_raw_rss_preview_is_manual_review_bound_when_ai_is_unavailable(monkeypatch):
    result, inserted, perplexity = run_hybrid(
        monkeypatch,
        ai_available=False,
    )

    assert perplexity.rewrite_calls == 0
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert len(inserted) == 1
    article = inserted[0]
    assert "Continue reading" not in article["content"]
    assert article["manual_review_hidden_from_public"] is True
    assert article["verification_status"] == "needs_manual_review"
    assert article["rewrite_status"] == "manual_review_required"
    assert article.get("archived") is not True
    assert "incomplete RSS preview" in article["manual_review_reason"]


@pytest.mark.parametrize(
    "source,rewrite",
    [
        (source_preview(), source_preview()),
        (
            source_preview(),
            source_preview().replace("\n\nContinue reading...", ""),
        ),
        (
            source_preview().replace("Continue reading...", "Continue reading…"),
            source_preview().replace("\n\nContinue reading...", ""),
        ),
        (
            source_preview(),
            source_preview().replace("\n\n", "   ").replace("Continue reading...", ""),
        ),
        (
            source_preview().replace("\n", "\r"),
            source_preview().replace("\n\nContinue reading...", ""),
        ),
        (
            source_preview(),
            source_preview().replace(".", "!").replace("Continue reading!!!", ""),
        ),
        (
            source_preview(),
            server.sanitize_rss_text(source_preview()),
        ),
        (
            source_preview(),
            source_preview()
            .replace("remains high", "is elevated")
            .replace("\n\nContinue reading...", ""),
        ),
    ],
)
def test_near_identical_rewrites_remain_manual_review_bound(
    monkeypatch,
    source,
    rewrite,
):
    result, inserted, perplexity = run_hybrid(
        monkeypatch,
        ai_available=True,
        rewrite=rewrite,
        source_content=source,
    )

    assert perplexity.rewrite_calls == 1
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert inserted[0]["manual_review_hidden_from_public"] is True
    assert "incomplete RSS preview" in inserted[0]["manual_review_reason"]


def test_ai_rewrite_exception_falls_back_to_manual_review(monkeypatch):
    result, inserted, perplexity = run_hybrid(
        monkeypatch,
        ai_available=True,
        rewrite=RuntimeError("offline rewrite failure"),
    )

    assert perplexity.rewrite_calls == 1
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert inserted[0]["manual_review_hidden_from_public"] is True
    assert "incomplete RSS preview" in inserted[0]["manual_review_reason"]


def test_long_lightly_altered_preview_remains_manual_review_bound(monkeypatch):
    source = f"{complete_rewrite()}\n\nContinue reading..."
    rewrite = complete_rewrite().replace(
        "Published figures",
        "Official figures",
        1,
    )
    assert len(rewrite) >= 1000

    result, inserted, _perplexity = run_hybrid(
        monkeypatch,
        ai_available=True,
        rewrite=rewrite,
        source_content=source,
    )

    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert inserted[0]["manual_review_hidden_from_public"] is True
    assert "incomplete RSS preview" in inserted[0]["manual_review_reason"]


def test_complete_ai_rewrite_replaces_preview_and_remains_public(monkeypatch):
    rewrite = complete_rewrite()
    result, inserted, perplexity = run_hybrid(
        monkeypatch,
        ai_available=True,
        rewrite=rewrite,
    )

    assert perplexity.rewrite_calls == 1
    assert result["public_imported"] == 1
    assert result["manual_review_imported"] == 0
    assert len(inserted) == 1
    article = inserted[0]
    assert article["content"] == rewrite
    assert article.get("manual_review_hidden_from_public") is not True


def test_complete_rss_content_without_marker_keeps_existing_sanitizer_contract():
    content = "First fact. Second fact. Third fact. Fourth fact."

    assert server.has_terminal_rss_continuation_marker(content) is False
    assert server.sanitize_rss_text(content) == (
        "First fact. Second fact.\n\nThird fact. Fourth fact."
    )
