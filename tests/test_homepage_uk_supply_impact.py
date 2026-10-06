"""Offline regressions for the shared public article eligibility rules."""

import pytest

from backend.app.public_article_eligibility import (
    is_public_article_editorially_eligible,
    is_uk_feed_noise,
)

DIESEL = {
    "title": "UK Engages European Allies on Emergency Diesel Stockpiles Amid US Supply Threats",
    "summary": "The UK is in discussions with European nations regarding the potential release of emergency diesel reserves following threats from the Trump administration to cut off US supplies.",
    "category": "UK News",
    "source": "The Guardian",
    "source_url": "https://www.theguardian.com/business/2026/oct/01/britain-talks-european-allies-eu-emergency-diesel-stockpiles-reserves",
}
EDUCATION = {
    "title": "UK schools introduce national artificial intelligence guidance",
    "summary": "Schools across Britain will use the new education guidance from next term.",
    "category": "UK News",
    "source": "BBC News",
    "source_url": "https://www.bbc.co.uk/news/articles/uk-schools-guidance",
}

SCOTLAND_AI_TEACHER = {
    **EDUCATION,
    "title": "Scotland's first AI teacher warns pupils: Don't trust everything it tells you",
    "summary": "Jamie Laycock says schools must help youngsters understand both the opportunities and dangers of AI.",
    "source_url": "https://www.bbc.co.uk/news/articles/c6qjk9n7gge7o",
}
GLASGOW_COUNCIL_PAY_DEAL = {
    **DIESEL,
    "title": "Glasgow city council reaches pay deal with union to avert fire-and-rehire plan",
    "summary": "‘Strong and fair’ proposal to be taken to members’ ballot after previous offer led Unison to walk out of negotiations Glasgow city council has reached an agreement with the trade union Unison over pay and grading, averting one of the UK’s biggest ever fire-and-rehire exercises.",
}


@pytest.fixture
def is_noise():
    return is_uk_feed_noise


def test_exact_diesel_metadata_is_accepted_without_body(is_noise):
    assert "content" not in DIESEL
    assert is_noise(DIESEL) is False


def test_plural_schools_education_story_is_accepted(is_noise):
    assert is_noise(EDUCATION) is False


@pytest.mark.parametrize("article", [
    SCOTLAND_AI_TEACHER,
    {
        **DIESEL,
        "title": "Failure to support Scotland's most disadvantaged 'costs £5.8bn a year'",
        "summary": "Failing to support Scotland's most disadvantaged costs at least £5.8bn a year, according to new analysis.",
        "category": "Business",
    },
    GLASGOW_COUNCIL_PAY_DEAL,
])
def test_devolved_or_regional_only_stories_are_excluded(is_noise, article):
    assert is_noise(article) is True


@pytest.mark.parametrize("incidental_scope", [
    "The agreement would be one of the UK's biggest settlements.",
    "The Glasgow agreement sets a British record.",
    "The union also represents workers elsewhere in the UK.",
])
def test_incidental_uk_or_british_mentions_do_not_prove_national_scope(is_noise, incidental_scope):
    article = {
        **DIESEL,
        "title": "Glasgow city council reaches a local pay agreement",
        "summary": incidental_scope,
    }
    assert is_noise(article) is True


def test_uk_wide_economic_story_mentioning_scotland_is_retained(is_noise):
    article = {
        **DIESEL,
        "title": "UK inflation outlook includes new figures from Scotland",
        "summary": "The Bank of England assessment covers households across Britain.",
    }
    assert is_noise(article) is False


def test_chester_university_local_story_remains_eligible():
    article = {
        "title": "University of Chester launches new skills programme",
        "summary": "The programme will support students and employers across Cheshire.",
        "category": "Local News",
        "source": "University of Chester",
        "source_url": "https://www.chester.ac.uk/news/skills-programme",
        "is_local_source": True,
    }
    assert is_public_article_editorially_eligible(article) is True


def test_unrelated_low_value_uk_human_interest_stays_rejected(is_noise):
    article = {
        **EDUCATION,
        "title": "UK collector shares a lifelong hobby",
        "summary": "The enthusiast says the collection brings back happy memories.",
    }
    assert is_noise(article) is True


@pytest.mark.parametrize("title", [
    "Britain reviews strategic petrol reserves",
    "British ministers discuss fuel supply security",
    "UK prepares for diesel shortages",
])
def test_bounded_supply_context(is_noise, title):
    assert is_noise({**DIESEL, "title": title, "summary": ""}) is False


@pytest.mark.parametrize("title", [
    "UK walkers fuel their enthusiasm for autumn",
    "UK collector restores a diesel engine",
    "British nature reserves welcome visitors",
    "UK hobbyists share a supply of coloured beads",
    "UK enthusiasts discuss fuel supplies for their models",
    "Canada reviews emergency diesel stockpiles",
    "UKulele enthusiasts discuss emergency diesel stockpiles",
    "UK discusses emergency diesel stockpilesque sculptures",
])
def test_isolated_words_and_missing_context_stay_rejected(is_noise, title):
    assert is_noise({**DIESEL, "title": title, "summary": ""}) is True


@pytest.mark.parametrize("changes", [
    {"source": "BBC Sport"},
    {"category": "Sports"},
    {"source_url": "https://example.test/sport/story"},
    {"source_url": "https://example.test/video/story"},
    {"title": "Watch video: UK emergency diesel stockpiles"},
    {"title": "The papers: UK emergency diesel stockpiles"},
    {"title": "The papers: Britain's boundless energy"},
    {"title": "MP discusses UK emergency diesel stockpiles"},
])
def test_earlier_noise_and_politics_guards_keep_precedence(is_noise, changes):
    assert is_noise({**DIESEL, **changes}) is True


@pytest.mark.parametrize("title", [
    "UK inflation slows as prices stabilise",
    "UK energy bills fall",
    "Council announces housing investment",
])
def test_existing_economic_acceptance_unchanged(is_noise, title):
    assert is_noise({**DIESEL, "title": title, "summary": ""}) is False


def test_body_does_not_supply_missing_metadata_context(is_noise):
    assert is_noise({**DIESEL, "title": "UK officials meet", "summary": "",
                     "content": DIESEL["title"] + " " + DIESEL["summary"]}) is True


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("prefix,accepted", [("", True), ("Podcast: ", False), ("Murder inquiry: ", False)])
def test_real_handler_keeps_later_guards_and_fallback(monkeypatch, fallback, prefix, accepted):
    import asyncio
    from tests.test_homepage_article_list_timing import FakeArticlesCollection, _article, server

    article = {**_article(1, local=False), **DIESEL, "title": prefix + DIESEL["title"]}
    collection = FakeArticlesCollection(
        local=[], uk=[_article(2, local=False)] if fallback else [article],
        fallback=[article] if fallback else [],
    )
    monkeypatch.setattr(server.db, "articles", collection)
    monkeypatch.setenv("UK_FILTER_NOISE", "1")
    result = asyncio.run(server.get_articles(limit=80))
    assert [a["id"] for a in result] == (["article-1"] if accepted else [])
    # Query-contract assertions, not claims that this lightweight fake executes Mongo filters.
    for call in collection.calls:
        if call[0] == "find":
            query = call[1]
            assert (query.get("manual_review_hidden_from_public") == {"$ne": True}
                    or {"manual_review_hidden_from_public": {"$ne": True}} in query.get("$and", []))
            archive_clause = {"$or": [{"archived": {"$exists": False}}, {"archived": False}]}
            assert (archive_clause in query.get("$and", [])
                    or query.get("$or") == archive_clause["$or"])


def test_the_papers_remains_excluded_by_shared_eligibility():
    article = {**DIESEL, "title": "The papers: UK emergency diesel stockpiles"}
    assert is_public_article_editorially_eligible(article) is False
