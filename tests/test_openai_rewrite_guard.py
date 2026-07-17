import asyncio
import json
import os
from types import SimpleNamespace

import pytest


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from backend.app.perplexity_service import validate_fact_pack_people


@pytest.mark.parametrize(
    "content",
    [
        "Experts have raised concerns about NHS support.",
        "Experts raise concerns about NHS support.",
        "Experts expressed concern about NHS support.",
        "Experts voiced concerns about NHS support.",
        "Researchers believe the system needs reform.",
        "Critics argue the policy is ineffective.",
        "Officials say the figures will improve.",
    ],
)
def test_vague_attribution_is_detected(content):
    assert (
        "vague or unnamed attribution"
        in server.find_openai_rewrite_editorial_violations(content)
    )


def test_named_attribution_is_allowed():
    content = (
        "Gareth Lyon, head of health and social care at Policy Exchange, "
        "said the NHS was under pressure."
    )

    assert (
        "vague or unnamed attribution"
        not in server.find_openai_rewrite_editorial_violations(content)
    )


def _openai_response(payload):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(payload))
            )
        ]
    )


def _install_rewrite_mocks(monkeypatch, initial_content, corrected_content):
    calls = []
    responses = [
        {
            "title": "Healthy life expectancy falls",
            "summary": "A verified summary.",
            "content": initial_content,
            "category": "UK News",
            "editor_notes": "",
        },
        {
            "title": "Healthy life expectancy falls",
            "summary": "A verified summary.",
            "content": corrected_content,
            "category": "UK News",
            "editor_notes": "",
        },
    ]

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            return _openai_response(responses[len(calls) - 1])

    class FakeOpenAI:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    async def fake_research_article_facts(**kwargs):
        return {
            "verified_facts": [
                "National Voices reported that people with long-term "
                "conditions felt unsupported."
            ],
            "names_and_roles": [
                {
                    "name": "Gareth Lyon",
                    "role": "Head of health and social care at Policy Exchange",
                    "verified": True,
                }
            ],
            "source_urls": ["https://example.com/source"],
        }

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(server, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        server.perplexity_service,
        "research_article_facts",
        fake_research_article_facts,
    )

    import app.simple_scraper

    monkeypatch.setattr(
        app.simple_scraper,
        "scrape_article",
        lambda *_args, **_kwargs: {
            "ok": True,
            "content": (
                "National Voices reported on long-term conditions. "
                "Gareth Lyon discussed NHS structure and competition."
            ),
        },
    )
    return calls


def test_correction_pass_separates_blended_attribution(monkeypatch):
    initial_content = "Experts have raised concerns about NHS support."
    corrected_content = (
        "National Voices reported that people with long-term conditions felt "
        "unsupported by the NHS.\n\n"
        "Gareth Lyon of Policy Exchange separately argued that NHS structure "
        "and competition affected responsiveness."
    )
    calls = _install_rewrite_mocks(
        monkeypatch,
        initial_content,
        corrected_content,
    )

    result = asyncio.run(
        server.run_openai_article_rewrite_draft(
            {
                "title": "Healthy life expectancy",
                "source_url": "https://example.com/source",
            }
        )
    )

    assert result["editorial_guard_triggered"] is True
    assert result["editorial_guard_violations"] == [
        "vague or unnamed attribution"
    ]
    assert len(calls) == 2
    assert calls[1]["temperature"] == 0
    assert "National Voices reported" in result["content"]
    assert "Gareth Lyon of Policy Exchange" in result["content"]
    assert result["editorial_guard_remaining_violations"] == []
    assert result["editorial_guard_corrected"] is True


def test_remaining_vague_attribution_is_reported(monkeypatch):
    content = "Experts have raised concerns about NHS support."
    calls = _install_rewrite_mocks(monkeypatch, content, content)

    result = asyncio.run(
        server.run_openai_article_rewrite_draft(
            {
                "title": "Healthy life expectancy",
                "source_url": "https://example.com/source",
            }
        )
    )

    assert len(calls) == 2
    assert result["editorial_guard_corrected"] is False
    assert result["editorial_guard_remaining_violations"] == [
        "vague or unnamed attribution"
    ]
    assert "Editorial guard still detected" in result["editor_notes"]


def test_malformed_name_is_downgraded_without_correction():
    fact_pack = {
        "names_and_roles": [
            {
                "name": "Aareth Lyon",
                "role": "Head of health and social care",
                "verified": True,
            }
        ],
        "uncertain_or_unverified": [],
    }

    result = validate_fact_pack_people(
        fact_pack,
        publisher_content="Gareth Lyon discussed the NHS.",
        publisher_url="https://example.com/story",
    )

    assert result["names_and_roles"][0]["name"] == "Aareth Lyon"
    assert result["names_and_roles"][0]["verified"] is False
    assert any(
        "Aareth Lyon" in item
        for item in result["uncertain_or_unverified"]
    )


@pytest.mark.parametrize("name", ["Rees", "McKee", "Sir Michael"])
def test_incomplete_names_are_downgraded(name):
    fact_pack = {
        "names_and_roles": [
            {"name": name, "role": "Expert", "verified": True}
        ]
    }

    result = validate_fact_pack_people(
        fact_pack,
        publisher_content=f"{name} discussed the findings.",
        publisher_url="https://example.com/story",
    )

    assert result["names_and_roles"][0]["verified"] is False
    assert any(
        name in item for item in result["uncertain_or_unverified"]
    )


def test_complete_supported_name_remains_verified():
    fact_pack = {
        "names_and_roles": [
            {
                "name": "Gareth Lyon",
                "role": "Head of health and social care",
                "verified": True,
            }
        ]
    }

    result = validate_fact_pack_people(
        fact_pack,
        publisher_content="Gareth Lyon discussed the NHS.",
        publisher_url="https://example.com/story",
    )

    assert result["names_and_roles"][0]["verified"] is True
    assert result["uncertain_or_unverified"] == []


def test_complete_independently_sourced_name_is_not_over_restricted():
    fact_pack = {
        "names_and_roles": [
            {
                "name": "Jane Smith",
                "role": "Research director",
                "verified": True,
                "source_url": "https://research.example/report",
            }
        ],
        "source_urls": ["https://research.example/report"],
    }

    result = validate_fact_pack_people(
        fact_pack,
        publisher_content="The publisher article does not name the researcher.",
        publisher_url="https://publisher.example/story",
    )

    assert result["names_and_roles"][0]["verified"] is True
    assert result["uncertain_or_unverified"] == []
