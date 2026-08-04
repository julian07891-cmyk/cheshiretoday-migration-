"""Deterministic, side-effect-free editorial same-event similarity scoring.

This module is deliberately independent from Cheshire Today's Version 1
duplicate prevention.  It performs no I/O and never mutates either input.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
import re
import unicodedata
from typing import Any, Literal, Mapping, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ConfidenceBand = Literal[
    "ineligible",
    "low",
    "possible",
    "likely",
    "very_likely",
]

MAX_TITLE_CHARACTERS = 300
MAX_SUMMARY_CHARACTERS = 2_000
MAX_CONTENT_CHARACTERS = 4_000
MAX_ARTICLE_CHARACTERS = (
    MAX_TITLE_CHARACTERS + MAX_SUMMARY_CHARACTERS + MAX_CONTENT_CHARACTERS + 2
)
MAX_URL_CHARACTERS = 2_048
MAX_TOKENS = 600
MAX_REASONS = 5

_TRACKING_PARAMETERS = {
    "at_campaign",
    "at_medium",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}

_STOP_WORDS = {
    "a",
    "about",
    "after",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "before",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "its",
    "near",
    "new",
    "of",
    "on",
    "or",
    "over",
    "said",
    "that",
    "the",
    "their",
    "this",
    "to",
    "under",
    "was",
    "were",
    "will",
    "with",
}

_COMMON_NEWS_TERMS = {
    "announced",
    "article",
    "cheshire",
    "confirmed",
    "council",
    "development",
    "final",
    "local",
    "news",
    "phase",
    "plans",
    "report",
    "reported",
    "scheme",
    "site",
    "story",
}

_CHESHIRE_PLACES = {
    "alderley edge",
    "alsager",
    "birchwood house",
    "chester",
    "congleton",
    "crewe",
    "ellesmere port",
    "hough",
    "knutsford",
    "macclesfield",
    "middlewich",
    "nantwich",
    "northwich",
    "runcorn",
    "sandbach",
    "shavington",
    "warrington",
    "widnes",
    "wilmslow",
    "winsford",
}

_NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "thirteen": "13",
    "fourteen": "14",
    "fifteen": "15",
    "sixteen": "16",
    "seventeen": "17",
    "eighteen": "18",
    "nineteen": "19",
    "twenty": "20",
}

_DISTINCTIVE_UNITS = {
    "apartment",
    "apartments",
    "business",
    "businesses",
    "flat",
    "flats",
    "home",
    "homes",
    "house",
    "houses",
    "job",
    "jobs",
    "mile",
    "miles",
    "million",
    "pound",
    "pounds",
    "school",
    "schools",
    "storey",
    "storeys",
    "unit",
    "units",
}

_SINGULAR_UNITS = {
    "apartments": "apartment",
    "businesses": "business",
    "flats": "flat",
    "homes": "home",
    "houses": "house",
    "jobs": "job",
    "miles": "mile",
    "pounds": "pound",
    "schools": "school",
    "storeys": "storey",
    "units": "unit",
}

_ORGANISATION_SUFFIXES = (
    "Council",
    "NHS",
    "Trust",
    "University",
    "College",
    "Police",
    "Authority",
    "Committee",
    "Department",
    "Agency",
    "Company",
    "Group",
)

_PLANNING_REFERENCE_RE = re.compile(
    r"\b(?:application|planning|reference|ref)\s*(?:no\.?|number|:)?\s*"
    r"([0-9]{2}/[0-9]{3,}[a-z0-9/-]*)\b",
    re.IGNORECASE,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_TAG_RE = re.compile(r"<[^>]+>")
_ORG_RE = re.compile(
    r"\b([A-Z][A-Za-z&'-]*(?:\s+[A-Z][A-Za-z&'-]*){0,5}\s+(?:"
    + "|".join(_ORGANISATION_SUFFIXES)
    + r"))\b"
)


@dataclass(frozen=True)
class EditorialSimilarityResult:
    """Bounded advisory result for one candidate/existing article pair."""

    eligible: bool
    score: int
    band: ConfidenceBand
    reasons: tuple[str, ...]


def _bounded_text(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    text = unescape(value[:limit])
    return _TAG_RE.sub(" ", text)


def _normalise_text(value: Any, limit: int = MAX_ARTICLE_CHARACTERS) -> str:
    text = unicodedata.normalize("NFKC", _bounded_text(value, limit)).casefold()
    return " ".join(_TOKEN_RE.findall(text))


def _article_text(article: Mapping[str, Any]) -> str:
    parts = (
        _bounded_text(article.get("title"), MAX_TITLE_CHARACTERS),
        _bounded_text(article.get("summary"), MAX_SUMMARY_CHARACTERS),
        _bounded_text(article.get("content"), MAX_CONTENT_CHARACTERS),
    )
    return " ".join(parts)


def _tokens(
    value: Any,
    *,
    limit: int = MAX_ARTICLE_CHARACTERS,
    remove_common_news_terms: bool = False,
) -> frozenset[str]:
    result = []
    for token in _TOKEN_RE.findall(_normalise_text(value, limit)):
        if token in _STOP_WORDS:
            continue
        if remove_common_news_terms and token in _COMMON_NEWS_TERMS:
            continue
        result.append(token)
        if len(result) >= MAX_TOKENS:
            break
    return frozenset(result)


def _containment(first: frozenset[str], second: frozenset[str]) -> float:
    if not first or not second:
        return 0.0
    return len(first & second) / min(len(first), len(second))


def _canonical_source_url(value: Any) -> str:
    if not isinstance(value, str) or len(value) > MAX_URL_CHARACTERS:
        return ""
    raw = value.strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
        query = urlencode(
            [
                (key, val)
                for key, val in parse_qsl(parts.query, keep_blank_values=True)
                if not key.casefold().startswith("utm_")
                and key.casefold() not in _TRACKING_PARAMETERS
            ],
            doseq=True,
        )
        path = parts.path.rstrip("/") or "/"
        return urlunsplit(
            (parts.scheme.casefold(), parts.netloc.casefold(), path, query, "")
        )
    except (TypeError, ValueError):
        return raw.casefold()


def _normalise_exact_title(value: Any) -> str:
    return " ".join(_bounded_text(value, MAX_TITLE_CHARACTERS).casefold().split())


def _is_version_one_exact_match(
    candidate: Mapping[str, Any], existing: Mapping[str, Any]
) -> bool:
    candidate_title_value = candidate.get("title")
    existing_title_value = existing.get("title")
    candidate_title = _normalise_exact_title(candidate_title_value)
    existing_title = _normalise_exact_title(existing_title_value)
    if candidate_title and candidate_title == existing_title:
        return True

    candidate_url = _canonical_source_url(
        candidate.get("source_url") or candidate.get("url") or candidate.get("link")
    )
    existing_url = _canonical_source_url(
        existing.get("source_url") or existing.get("url") or existing.get("link")
    )
    return bool(candidate_url and candidate_url == existing_url)


def _planning_references(text: str) -> frozenset[str]:
    return frozenset(match.casefold() for match in _PLANNING_REFERENCE_RE.findall(text))


def _locations(article: Mapping[str, Any], text: str) -> frozenset[str]:
    found = {
        _normalise_text(article.get(field))
        for field in ("location", "priority_location")
        if _normalise_text(article.get(field))
    }
    normalised = _normalise_text(text)
    found.update(place for place in _CHESHIRE_PLACES if place in normalised)
    return frozenset(found)


def _distinctive_facts(text: str) -> frozenset[tuple[str, str]]:
    normalised = _normalise_text(text)
    for word, number in _NUMBER_WORDS.items():
        normalised = re.sub(rf"\b{word}\b", number, normalised)
    pattern = re.compile(
        r"\b([0-9]{1,6})\s+(" + "|".join(sorted(_DISTINCTIVE_UNITS)) + r")\b"
    )
    facts = set()
    for number, unit in pattern.findall(normalised):
        facts.add((number, _SINGULAR_UNITS.get(unit, unit)))
    return frozenset(facts)


def _organisations(text: str) -> frozenset[str]:
    return frozenset(
        _normalise_text(value)
        for value in _ORG_RE.findall(_bounded_text(text, MAX_ARTICLE_CHARACTERS))
    )


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        parsed = value
    elif value:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _publication_time(article: Mapping[str, Any]) -> Optional[datetime]:
    return _parse_datetime(
        article.get("publishedDate")
        or article.get("published_date")
        or article.get("created_at")
    )


def _event_stages(text: str) -> frozenset[str]:
    normalised = _normalise_text(text)
    stages = set()
    patterns = {
        "proposal": r"\b(proposal|proposed|application submitted|plans unveiled)\b",
        "decision": r"\b(approved|approval|green light|permission granted|refused|rejected)\b",
        "construction": r"\b(under construction|construction began|work begins|building work|built)\b",
        "completion": r"\b(completed|completion|opened|opens|finished)\b",
        "appeal": r"\b(appeal|appealed|planning inspector)\b",
    }
    for stage, pattern in patterns.items():
        if re.search(pattern, normalised):
            stages.add(stage)
    return frozenset(stages)


def _score_editorial_similarity(
    candidate: Mapping[str, Any],
    existing: Mapping[str, Any],
) -> EditorialSimilarityResult:
    if _is_version_one_exact_match(candidate, existing):
        return EditorialSimilarityResult(
            eligible=False,
            score=0,
            band="ineligible",
            reasons=(),
        )

    candidate_text = _article_text(candidate)
    existing_text = _article_text(existing)
    score = 0
    reasons: list[str] = []
    families: set[str] = set()

    planning_match = bool(
        _planning_references(candidate_text) & _planning_references(existing_text)
    )
    if planning_match:
        score += 30
        families.add("planning_reference")
        reasons.append("Matching planning or application reference")

    location_match = bool(
        _locations(candidate, candidate_text) & _locations(existing, existing_text)
    )
    if location_match:
        score += 20
        families.add("location")
        reasons.append("Same named site or locality")

    fact_match = bool(
        _distinctive_facts(candidate_text) & _distinctive_facts(existing_text)
    )
    if fact_match:
        score += 20
        families.add("distinctive_fact")
        reasons.append("Matching distinctive numerical fact")

    title_similarity = _containment(
        _tokens(candidate.get("title"), limit=MAX_TITLE_CHARACTERS),
        _tokens(existing.get("title"), limit=MAX_TITLE_CHARACTERS),
    )
    if title_similarity >= 0.65:
        score += 10
        families.add("headline")
        reasons.append("High headline overlap")
    elif title_similarity >= 0.40:
        score += 7
        families.add("headline")
        reasons.append("Meaningful headline overlap")
    elif title_similarity >= 0.25:
        score += 4
        families.add("headline")

    body_similarity = _containment(_tokens(candidate_text), _tokens(existing_text))
    if body_similarity >= 0.55:
        score += 15
        families.add("text")
        reasons.append("High textual similarity")
    elif body_similarity >= 0.35:
        score += 12
        families.add("text")
        reasons.append("Meaningful textual similarity")
    elif body_similarity >= 0.22:
        score += 8
        families.add("text")

    rare_overlap = _tokens(candidate_text, remove_common_news_terms=True) & _tokens(
        existing_text, remove_common_news_terms=True
    )
    rare_overlap = {token for token in rare_overlap if len(token) >= 7}
    if len(rare_overlap) >= 4:
        score += 10
        families.add("rare_terms")
        reasons.append("Shared distinctive terms")
    elif len(rare_overlap) >= 2:
        score += 6
        families.add("rare_terms")

    if _organisations(candidate_text) & _organisations(existing_text):
        score += 5
        families.add("organisation")
        reasons.append("Shared named organisation")

    candidate_time = _publication_time(candidate)
    existing_time = _publication_time(existing)
    if candidate_time and existing_time:
        hours_apart = abs((candidate_time - existing_time).total_seconds()) / 3600
        if hours_apart <= 6:
            score += 5
            families.add("time")
            reasons.append("Published within six hours")
        elif hours_apart <= 72:
            score += 2
            families.add("time")

    candidate_stages = _event_stages(candidate_text)
    existing_stages = _event_stages(existing_text)
    if (
        candidate_stages
        and existing_stages
        and candidate_stages.isdisjoint(existing_stages)
    ):
        score = max(0, score - 20)

    score = min(100, score)
    strong_identity = planning_match or (location_match and fact_match)

    if score >= 85 and strong_identity and len(families) >= 4:
        band: ConfidenceBand = "very_likely"
    elif score >= 70 and strong_identity and len(families) >= 3:
        band = "likely"
    elif score >= 50:
        band = "possible"
        score = min(score, 84 if strong_identity else 69)
    else:
        band = "low"

    bounded_reasons = tuple(reasons[:MAX_REASONS]) if band != "low" else ()
    return EditorialSimilarityResult(
        eligible=True,
        score=score,
        band=band,
        reasons=bounded_reasons,
    )


def score_editorial_similarity(
    candidate: Mapping[str, Any],
    existing: Mapping[str, Any],
) -> EditorialSimilarityResult:
    """Score whether two records likely describe the same underlying event.

    Exact Version 1 title/source-URL matches are marked ineligible so this
    advisory scorer cannot become an alternative exact-duplicate engine. Any
    unexpected malformed-input failure returns a conservative advisory result.
    """

    try:
        return _score_editorial_similarity(candidate, existing)
    except Exception:
        return EditorialSimilarityResult(
            eligible=True,
            score=0,
            band="low",
            reasons=(),
        )


__all__ = [
    "EditorialSimilarityResult",
    "score_editorial_similarity",
]
