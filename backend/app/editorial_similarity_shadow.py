"""Bounded, advisory-only runtime integration for Editorial Similarity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
import unicodedata
from typing import Any, Iterable, Mapping, Optional
from uuid import UUID

from bson import ObjectId

try:
    from app.editorial_similarity import (
        MAX_CONTENT_CHARACTERS,
        MAX_SUMMARY_CHARACTERS,
        MAX_TITLE_CHARACTERS,
        MAX_URL_CHARACTERS,
        EditorialSimilarityResult,
        score_editorial_similarity,
    )
except ModuleNotFoundError:
    from backend.app.editorial_similarity import (
        MAX_CONTENT_CHARACTERS,
        MAX_SUMMARY_CHARACTERS,
        MAX_TITLE_CHARACTERS,
        MAX_URL_CHARACTERS,
        EditorialSimilarityResult,
        score_editorial_similarity,
    )


LOG_PREFIX = "editorial_similarity_shadow"
SCORER_VERSION = "phase2a_v1"
SHADOW_MODE = "scheduled_log_only"
ACTIVE_COMPARISON_LIMIT = 50
ARCHIVED_COMPARISON_LIMIT = 50
COMPARISON_POOL_LIMIT = ACTIVE_COMPARISON_LIMIT + ARCHIVED_COMPARISON_LIMIT
SHORTLIST_LIMIT = 20

ALLOWED_CONTEXTS = frozenset(
    {
        "category_rss",
        "local_rss_manual_review",
        "local_rss",
        "cheshire_fallback",
    }
)
ALLOWED_PROVENANCE = frozenset({"active", "archived", "same_run"})
ALLOWED_BANDS = frozenset({"ineligible", "low", "possible", "likely", "very_likely"})

_REASON_CODES = {
    "Matching planning or application reference": "planning_reference",
    "Same named site or locality": "location",
    "Matching distinctive numerical fact": "distinctive_fact",
    "High headline overlap": "headline_high",
    "Meaningful headline overlap": "headline_meaningful",
    "High textual similarity": "text_high",
    "Meaningful textual similarity": "text_meaningful",
    "Shared distinctive terms": "rare_terms",
    "Shared named organisation": "organisation",
    "Published within six hours": "publication_time",
}
ALLOWED_REASON_CODES = frozenset(_REASON_CODES.values())

_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PLANNING_REFERENCE_RE = re.compile(
    r"\b(?:application|planning|reference|ref)\s*(?:no\.?|number|:)?\s*"
    r"([0-9]{2}/[0-9]{3,}[a-z0-9/-]*)\b",
    re.IGNORECASE,
)
_DISTINCTIVE_FACT_RE = re.compile(
    r"\b([0-9]{1,6})\s+"
    r"(apartments?|business(?:es)?|flats?|homes?|houses?|jobs?|miles?|million|"
    r"pounds?|schools?|storeys?|units?)\b",
    re.IGNORECASE,
)
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
_GENERIC_TERMS = frozenset(
    {
        "after",
        "announced",
        "article",
        "cheshire",
        "confirmed",
        "council",
        "development",
        "final",
        "from",
        "local",
        "news",
        "near",
        "phase",
        "plans",
        "report",
        "reported",
        "scheme",
        "site",
        "story",
        "that",
        "their",
        "this",
        "with",
    }
)
_ELIGIBLE_BAND_RANK = {
    "ineligible": -1,
    "low": 0,
    "possible": 1,
    "likely": 2,
    "very_likely": 3,
}
_MIN_TIMESTAMP = datetime.min.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class EditorialSimilarityShadowEvaluation:
    eligible: bool
    score: int
    band: str
    reason_codes: tuple[str, ...]
    comparison_count: int
    shortlist_count: int
    matched_article_id: Optional[str]
    matched_provenance: Optional[str]


@dataclass(frozen=True)
class _ComparisonRecord:
    article_id: str
    provenance: str
    published_at: datetime
    article: Mapping[str, Any]


def _bounded_string(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return value[:limit]


def _safe_identifier(value: Any) -> Optional[str]:
    if isinstance(value, str):
        identifier = value
    elif type(value) is ObjectId:
        identifier = str(value)
    elif type(value) is UUID:
        identifier = str(value)
    else:
        return None
    if not _SAFE_IDENTIFIER_RE.fullmatch(identifier):
        return None
    return identifier


def _bounded_date(value: Any) -> Any:
    if isinstance(value, datetime):
        return value
    return _bounded_string(value, 128)


def _normalised_timestamp(article: Mapping[str, Any]) -> datetime:
    for field in ("publishedDate", "published_date", "created_at"):
        value = article.get(field)
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str) and value[:128].strip():
            try:
                parsed = datetime.fromisoformat(value[:128].replace("Z", "+00:00"))
            except ValueError:
                continue
        else:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return _MIN_TIMESTAMP


def _timestamp_rank(value: datetime) -> int:
    return (
        value.toordinal() * 86_400_000_000
        + value.hour * 3_600_000_000
        + value.minute * 60_000_000
        + value.second * 1_000_000
        + value.microsecond
    )


def bounded_article_snapshot(article: Mapping[str, Any]) -> dict[str, Any]:
    """Copy only scorer fields with explicit bounds; never mutate the record."""
    return {
        "title": _bounded_string(article.get("title"), MAX_TITLE_CHARACTERS),
        "summary": _bounded_string(article.get("summary"), MAX_SUMMARY_CHARACTERS),
        "content": _bounded_string(article.get("content"), MAX_CONTENT_CHARACTERS),
        "source_url": _bounded_string(article.get("source_url"), MAX_URL_CHARACTERS),
        "location": _bounded_string(article.get("location"), MAX_TITLE_CHARACTERS),
        "priority_location": _bounded_string(
            article.get("priority_location"), MAX_TITLE_CHARACTERS
        ),
        "publishedDate": _bounded_date(article.get("publishedDate")),
        "published_date": _bounded_date(article.get("published_date")),
        "created_at": _bounded_date(article.get("created_at")),
    }


def _normalised_tokens(value: str) -> frozenset[str]:
    normalised = unicodedata.normalize("NFKC", value).casefold()
    return frozenset(
        token
        for token in _TOKEN_RE.findall(normalised)
        if len(token) >= 4 and token not in _GENERIC_TERMS
    )


def _article_shortlist_text(article: Mapping[str, Any]) -> str:
    return " ".join(
        (
            _bounded_string(article.get("title"), MAX_TITLE_CHARACTERS),
            _bounded_string(article.get("summary"), MAX_SUMMARY_CHARACTERS),
            _bounded_string(article.get("content"), MAX_CONTENT_CHARACTERS),
        )
    )


def _planning_references(text: str) -> frozenset[str]:
    return frozenset(value.casefold() for value in _PLANNING_REFERENCE_RE.findall(text))


def _distinctive_facts(text: str) -> frozenset[tuple[str, str]]:
    return frozenset(
        (
            number,
            _SINGULAR_UNITS.get(unit.casefold(), unit.casefold()),
        )
        for number, unit in _DISTINCTIVE_FACT_RE.findall(text)
    )


def _shortlist_score(candidate: Mapping[str, Any], existing: Mapping[str, Any]) -> int:
    candidate_text = _article_shortlist_text(candidate)
    existing_text = _article_shortlist_text(existing)
    score = 0

    if _planning_references(candidate_text) & _planning_references(existing_text):
        score += 100
    if _distinctive_facts(candidate_text) & _distinctive_facts(existing_text):
        score += 70

    candidate_locations = {
        _bounded_string(candidate.get(field), MAX_TITLE_CHARACTERS).strip().casefold()
        for field in ("location", "priority_location")
    } - {"", "cheshire"}
    existing_locations = {
        _bounded_string(existing.get(field), MAX_TITLE_CHARACTERS).strip().casefold()
        for field in ("location", "priority_location")
    } - {"", "cheshire"}
    if candidate_locations & existing_locations:
        score += 60

    title_overlap = _normalised_tokens(
        _bounded_string(candidate.get("title"), MAX_TITLE_CHARACTERS)
    ) & _normalised_tokens(_bounded_string(existing.get("title"), MAX_TITLE_CHARACTERS))
    if len(title_overlap) >= 2:
        score += min(40, len(title_overlap) * 10)

    text_overlap = _normalised_tokens(candidate_text) & _normalised_tokens(
        existing_text
    )
    distinctive_overlap = {token for token in text_overlap if len(token) >= 7}
    if len(distinctive_overlap) >= 2:
        score += min(30, len(distinctive_overlap) * 5)
    return score


def _reason_codes(result: EditorialSimilarityResult) -> tuple[str, ...]:
    return tuple(
        _REASON_CODES[reason] for reason in result.reasons if reason in _REASON_CODES
    )[:5]


def _empty_evaluation(comparison_count: int = 0) -> EditorialSimilarityShadowEvaluation:
    return EditorialSimilarityShadowEvaluation(
        eligible=True,
        score=0,
        band="low",
        reason_codes=(),
        comparison_count=max(0, min(COMPARISON_POOL_LIMIT, comparison_count)),
        shortlist_count=0,
        matched_article_id=None,
        matched_provenance=None,
    )


class EditorialSimilarityShadowEvaluator:
    """Maintain a bounded comparison corpus and select one advisory best match."""

    def __init__(self, records: Iterable[Mapping[str, Any]] = ()) -> None:
        self._records: list[_ComparisonRecord] = []
        for record in records:
            try:
                provenance = record.get("_editorial_similarity_provenance", "active")
                self.add(
                    record,
                    record.get("_id") or record.get("id"),
                    provenance=provenance,
                )
            except Exception:
                continue

    @property
    def pool_size(self) -> int:
        return len(self._records)

    def add(
        self,
        article: Mapping[str, Any],
        article_id: Any,
        *,
        provenance: str = "same_run",
    ) -> bool:
        safe_id = _safe_identifier(article_id)
        if safe_id is None or provenance not in ALLOWED_PROVENANCE:
            return False
        record = _ComparisonRecord(
            article_id=safe_id,
            provenance=provenance,
            published_at=_normalised_timestamp(article),
            article=bounded_article_snapshot(article),
        )
        self._records = [item for item in self._records if item.article_id != safe_id]
        self._records.append(record)
        self._records.sort(key=lambda item: (item.published_at, item.article_id))
        if len(self._records) > COMPARISON_POOL_LIMIT:
            del self._records[: len(self._records) - COMPARISON_POOL_LIMIT]
        return True

    def _shortlist(
        self, candidate: Mapping[str, Any], candidate_id: Optional[str]
    ) -> list[_ComparisonRecord]:
        ranked = []
        for record in self._records:
            if candidate_id is not None and record.article_id == candidate_id:
                continue
            evidence_score = _shortlist_score(candidate, record.article)
            if evidence_score <= 0:
                continue
            ranked.append((evidence_score, record))
        ranked.sort(
            key=lambda item: (
                -item[0],
                -_timestamp_rank(item[1].published_at),
                item[1].article_id,
            )
        )
        return [record for _, record in ranked[:SHORTLIST_LIMIT]]

    def evaluate(
        self, candidate: Mapping[str, Any]
    ) -> EditorialSimilarityShadowEvaluation:
        candidate_snapshot = bounded_article_snapshot(candidate)
        candidate_id = _safe_identifier(candidate.get("_id") or candidate.get("id"))
        shortlist = self._shortlist(candidate_snapshot, candidate_id)
        scored = []
        for record in shortlist:
            result = score_editorial_similarity(candidate_snapshot, record.article)
            scored.append((result, record))

        if not scored:
            return _empty_evaluation(len(self._records))

        scored.sort(
            key=lambda item: (
                -item[0].score,
                -_ELIGIBLE_BAND_RANK.get(item[0].band, -1),
                -_timestamp_rank(item[1].published_at),
                item[1].article_id,
            )
        )
        best_result, best_record = scored[0]
        if best_result.score == 0 and best_result.band != "ineligible":
            return EditorialSimilarityShadowEvaluation(
                eligible=True,
                score=0,
                band="low",
                reason_codes=(),
                comparison_count=len(self._records),
                shortlist_count=len(shortlist),
                matched_article_id=None,
                matched_provenance=None,
            )
        return EditorialSimilarityShadowEvaluation(
            eligible=best_result.eligible,
            score=best_result.score,
            band=best_result.band,
            reason_codes=_reason_codes(best_result),
            comparison_count=len(self._records),
            shortlist_count=len(shortlist),
            matched_article_id=best_record.article_id,
            matched_provenance=best_record.provenance,
        )


def _bounded_int(value: Any, lower: int, upper: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return max(lower, min(upper, value))
    return lower


def format_shadow_log(
    evaluation: EditorialSimilarityShadowEvaluation,
    *,
    candidate_article_id: Any,
    context: str,
) -> str:
    safe_context = (
        context
        if isinstance(context, str) and context in ALLOWED_CONTEXTS
        else "unknown"
    )
    candidate_id = _safe_identifier(candidate_article_id) or "none"
    score = _bounded_int(evaluation.score, 0, 100)
    comparison_count = _bounded_int(
        evaluation.comparison_count, 0, COMPARISON_POOL_LIMIT
    )
    shortlist_count = _bounded_int(evaluation.shortlist_count, 0, SHORTLIST_LIMIT)
    valid_band = isinstance(evaluation.band, str) and evaluation.band in ALLOWED_BANDS
    band = evaluation.band if valid_band else "low"
    eligible = evaluation.eligible if isinstance(evaluation.eligible, bool) else True
    matched_id = _safe_identifier(evaluation.matched_article_id)
    provenance = (
        evaluation.matched_provenance
        if isinstance(evaluation.matched_provenance, str)
        and evaluation.matched_provenance in ALLOWED_PROVENANCE
        else None
    )
    has_match = bool(
        valid_band and matched_id and provenance and (score > 0 or band == "ineligible")
    )
    if not has_match:
        matched_id = None
        provenance = None
        eligible = True
        score = 0
        band = "low"
        reason_source = ()
    else:
        reason_source = (
            evaluation.reason_codes
            if isinstance(evaluation.reason_codes, (tuple, list))
            else ()
        )
    reason_codes = tuple(
        reason
        for reason in reason_source
        if isinstance(reason, str) and reason in ALLOWED_REASON_CODES
    )[:5]
    status = "scored" if matched_id else "no_match"
    return " ".join(
        [
            LOG_PREFIX,
            f"status={status}",
            f"context={safe_context}",
            f"candidate_article_id={candidate_id}",
            f"matched_article_id={matched_id or 'none'}",
            f"matched_provenance={provenance or 'none'}",
            f"eligible={str(eligible).lower()}",
            f"score={score}",
            f"band={band}",
            f"comparison_count={comparison_count}",
            f"shortlist_count={shortlist_count}",
            f"reason_codes={','.join(reason_codes) or 'none'}",
            f"scorer_version={SCORER_VERSION}",
            f"shadow_mode={SHADOW_MODE}",
        ]
    )


async def insert_with_editorial_similarity_shadow(
    collection,
    article: Mapping[str, Any],
    *,
    context: str,
    evaluator: Optional[EditorialSimilarityShadowEvaluator],
    logger,
):
    """Insert exactly once; advisory evaluation and logging can never block it."""
    evaluation = None
    if evaluator is not None:
        try:
            evaluation = evaluator.evaluate(article)
        except Exception:
            evaluation = _empty_evaluation(evaluator.pool_size)

    result = await collection.insert_one(article)

    if evaluator is not None:
        try:
            evaluator.add(article, result.inserted_id, provenance="same_run")
        except Exception:
            pass
        try:
            logger.info(
                format_shadow_log(
                    evaluation or _empty_evaluation(),
                    candidate_article_id=result.inserted_id,
                    context=context,
                )
            )
        except Exception:
            pass
    return result


__all__ = [
    "ACTIVE_COMPARISON_LIMIT",
    "ALLOWED_BANDS",
    "ALLOWED_CONTEXTS",
    "ALLOWED_PROVENANCE",
    "ALLOWED_REASON_CODES",
    "ARCHIVED_COMPARISON_LIMIT",
    "COMPARISON_POOL_LIMIT",
    "SHORTLIST_LIMIT",
    "EditorialSimilarityShadowEvaluation",
    "EditorialSimilarityShadowEvaluator",
    "bounded_article_snapshot",
    "format_shadow_log",
    "insert_with_editorial_similarity_shadow",
]
