import os
import re

import pytest


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend.server import sanitize_rss_text


@pytest.mark.parametrize("value", [None, ""])
def test_empty_input_returns_empty_string(value):
    assert sanitize_rss_text(value) == ""


def test_source_url_is_removed():
    source_url = "https://publisher.example/story"
    assert sanitize_rss_text(f"Story text.\n\n{source_url}", source_url) == "Story text."


@pytest.mark.parametrize(
    "tail",
    [
        "Read more: https://publisher.example/story",
        "Continue reading - https://publisher.example/story",
        "Full story: https://publisher.example/story",
        "Source: https://publisher.example/story",
    ],
)
def test_recognised_source_link_tails_are_removed(tail):
    assert sanitize_rss_text(f"Story text.\n{tail}") == "Story text."


def test_standalone_url_is_removed():
    assert sanitize_rss_text("Story text.\nhttps://other.example/story") == "Story text."


def test_inline_unrelated_url_is_retained():
    text = "Details remain at https://other.example/story for readers."
    assert sanitize_rss_text(text) == text


def test_existing_two_paragraph_input_is_preserved():
    text = "A one-sentence lead.\n\nThe second paragraph adds context and another fact."
    assert sanitize_rss_text(text) == text


def test_existing_perplexity_style_paragraphs_are_preserved():
    text = (
        "Cheshire East Council approved the plan on Monday.\n\n"
        "The scheme includes 40 homes and a public footpath. Two homes will be accessible.\n\n"
        "Work is expected to begin in September. The council will publish updates online."
    )
    assert sanitize_rss_text(text) == text


def test_one_sentence_lead_remains_separate():
    text = (
        "A manufacturer will open a new Crewe site.\n\n"
        "The company confirmed the move on Tuesday. It expects to create 30 jobs.\n\n"
        "Recruitment will begin next month. Applications will be accepted online."
    )
    assert sanitize_rss_text(text).split("\n\n")[0] == "A manufacturer will open a new Crewe site."


def test_excessive_blank_lines_are_normalised():
    text = "First paragraph.\n\n\n\nSecond paragraph."
    assert sanitize_rss_text(text) == "First paragraph.\n\nSecond paragraph."


def test_single_block_with_four_sentences_gets_fallback_paragraphs():
    text = "First fact. Second fact. Third fact. Fourth fact."
    assert sanitize_rss_text(text) == "First fact. Second fact.\n\nThird fact. Fourth fact."


@pytest.mark.parametrize(
    "text",
    [
        "One fact.",
        "One fact. Two facts.",
        "One fact. Two facts. Three facts.",
    ],
)
def test_short_single_blocks_are_not_needlessly_split(text):
    assert sanitize_rss_text(text) == text


def test_summary_mode_remains_one_compact_block():
    text = "First summary sentence.\n\nSecond summary sentence.\nThird summary sentence."
    assert sanitize_rss_text(text, is_summary=True) == (
        "First summary sentence. Second summary sentence. Third summary sentence."
    )


def test_summary_mode_still_removes_source_tail():
    text = "Compact summary.\nRead more: https://publisher.example/story"
    assert sanitize_rss_text(text, is_summary=True) == "Compact summary."


def test_abbreviations_initials_and_decimal_do_not_create_false_boundaries():
    text = (
        "Dr. Jane Smith spoke for Example Ltd. on Monday. "
        "Mr. A. B. Jones reported a 3.5 per cent rise. "
        "No. 10 issued a response. A fourth fact followed."
    )
    result = sanitize_rss_text(text)
    assert result == (
        "Dr. Jane Smith spoke for Example Ltd. on Monday. "
        "Mr. A. B. Jones reported a 3.5 per cent rise.\n\n"
        "No. 10 issued a response. A fourth fact followed."
    )


def test_quoted_speech_and_attribution_remain_in_order():
    text = (
        'The council met on Tuesday. "Work starts on Monday." '
        'Jane Smith said residents would receive letters. '
        'Contractors will arrive at 8am. The road will remain open.'
    )
    result = sanitize_rss_text(text)
    assert result == (
        'The council met on Tuesday. "Work starts on Monday." '
        'Jane Smith said residents would receive letters.\n\n'
        'Contractors will arrive at 8am. The road will remain open.'
    )


def test_fallback_preserves_wording_and_order():
    text = "Alpha begins. Beta follows. Gamma continues. Delta ends."
    result = sanitize_rss_text(text)
    assert re.sub(r"\s+", " ", result) == text


@pytest.mark.parametrize(
    "text,is_summary",
    [
        ("First fact. Second fact. Third fact. Fourth fact.", False),
        ("Lead paragraph.\n\nContext paragraph. More detail.", False),
        ("Summary one.\n\nSummary two.", True),
    ],
)
def test_sanitization_is_idempotent(text, is_summary):
    once = sanitize_rss_text(text, is_summary=is_summary)
    assert sanitize_rss_text(once, is_summary=is_summary) == once
