#!/usr/bin/env python3
"""Deterministic, read-only shadow ranking for RSS story candidates.

Supported invocation from the repository root::

    python3 -m backend.scripts.evaluate_story_ranking_shadow \
        --input candidates.json --as-of 2026-07-23T12:00:00Z

The input is a JSON array or ``{"candidates": [...]}``. The command reads that
snapshot, writes one JSON report to stdout and a concise summary to stderr. It
has no network, database, import, publication or mutation capability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}
CURRENT_ECONOMIC_TERMS = re.compile(
    r"\b(mortgage|rent|rents|tax|budget|inflation|interest\s*rate|rates|jobs|"
    r"wages|economy|economic|business|finance|markets?|prices?|bills?|energy|"
    r"council|planning|housing|investment|trade|tariff|regulation|ofgem|ofwat|"
    r"boe|bank of england)\b",
    re.I,
)
CURRENT_LOW_UTILITY_TERMS = re.compile(
    r"\b(brit awards|baftas|celebrity|film|tv|ceremony|showbiz|royal fashion)\b",
    re.I,
)
CURRENT_PRIORITY_CATEGORIES = {"business", "tech", "finance", "tax", "ai"}
VALID_ORIGINALITY = {"original", "mixed", "press_release", "syndicated", "unknown"}
VALID_LOCALITY = {"town", "cheshire", "regional", "non_local", "unknown"}
VALID_PUBLISHER_TYPES = {"independent", "official", "established", "unknown"}
VALID_SYNDICATION = {"none", "ldrs", "press_release", "syndicated", "unknown"}
VALID_ASSESSMENT_SOURCES = {
    "manual_review",
    "feed_metadata",
    "rule_based",
    "fixture",
}
FORBIDDEN_BODY_FIELDS = {
    "article_body",
    "body",
    "content",
    "description",
    "raw_content",
    "summary",
}
MAX_ASSESSMENT_NOTE_LENGTH = 160


class ShadowRankingError(ValueError):
    """Safe input or configuration failure."""


@dataclass(frozen=True)
class RankingWeights:
    original_reporting: int = 24
    mixed_reporting: int = 10
    press_release_originality: int = 2
    syndicated_originality: int = -8
    town_locality: int = 24
    cheshire_locality: int = 16
    regional_locality: int = 5
    non_local: int = -12
    business_value_unit: int = 6
    editorial_fit_unit: int = 5
    high_quality_image: int = 10
    usable_image: int = 5
    missing_image: int = -8
    freshness_6h: int = 15
    freshness_24h: int = 12
    freshness_72h: int = 8
    freshness_7d: int = 4
    future_date: int = -12
    ldrs_syndication: int = -5
    press_release_syndication: int = -7
    general_syndication: int = -10
    independent_publisher: int = 6
    official_publisher: int = 4
    established_publisher: int = 3
    missing_source_url: int = -10

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any] | None) -> "RankingWeights":
        if values is None:
            return cls()
        if not isinstance(values, Mapping):
            raise ShadowRankingError("weights must be a JSON object")
        allowed = set(cls.__dataclass_fields__)
        unknown = sorted(set(values) - allowed)
        if unknown:
            raise ShadowRankingError("weights contain unknown fields")
        for value in values.values():
            if type(value) is not int:
                raise ShadowRankingError("every weight must be a built-in integer")
        return cls(**dict(values))


@dataclass(frozen=True)
class StoryCandidate:
    candidate_id: str
    title: str
    source: str
    source_url: str
    published_at: datetime
    category: str
    is_local_source: bool
    locality: str
    originality: str
    business_value: int
    editorial_fit: int
    publisher_type: str
    syndication: str
    has_image: bool
    image_width: int | None
    image_height: int | None
    current_importer_selected: bool
    story_key: str | None
    assessment_source: str
    assessment_note: str | None


def _required_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ShadowRankingError(f"{field} must be non-empty text")
    return value.strip()


def _optional_enum(
    payload: Mapping[str, Any], field: str, allowed: set[str], default: str
) -> str:
    value = payload.get(field, default)
    if not isinstance(value, str) or value not in allowed:
        raise ShadowRankingError(f"{field} is invalid")
    return value


def _bounded_int(payload: Mapping[str, Any], field: str, default: int) -> int:
    value = payload.get(field, default)
    if type(value) is not int or not 0 <= value <= 3:
        raise ShadowRankingError(f"{field} must be an integer from 0 to 3")
    return value


def _optional_dimension(payload: Mapping[str, Any], field: str) -> int | None:
    value = payload.get(field)
    if value is None:
        return None
    if type(value) is not int or value <= 0:
        raise ShadowRankingError(f"{field} must be a positive built-in integer")
    return value


def parse_utc_datetime(value: Any, field: str = "published_at") -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ShadowRankingError(f"{field} must be a UTC ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ShadowRankingError(f"{field} must be a UTC ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ShadowRankingError(f"{field} must be timezone-aware UTC")
    return parsed


def parse_candidate(payload: Mapping[str, Any]) -> StoryCandidate:
    if not isinstance(payload, Mapping):
        raise ShadowRankingError("each candidate must be a JSON object")
    if FORBIDDEN_BODY_FIELDS.intersection(payload):
        raise ShadowRankingError("article body fields are not accepted")
    boolean_fields = ("is_local_source", "has_image", "current_importer_selected")
    booleans: dict[str, bool] = {}
    for field in boolean_fields:
        value = payload.get(field, False)
        if type(value) is not bool:
            raise ShadowRankingError(f"{field} must be a boolean")
        booleans[field] = value
    story_key = payload.get("story_key")
    if story_key is not None:
        if not isinstance(story_key, str) or not story_key.strip():
            raise ShadowRankingError("story_key must be non-empty text when supplied")
        story_key = story_key.strip()
    assessment_note = payload.get("assessment_note")
    if assessment_note is not None:
        if not isinstance(assessment_note, str):
            raise ShadowRankingError("assessment_note must be text when supplied")
        assessment_note = assessment_note.strip()
        if not assessment_note or len(assessment_note) > MAX_ASSESSMENT_NOTE_LENGTH:
            raise ShadowRankingError("assessment_note must be concise non-empty text")
        if any(ord(character) < 32 for character in assessment_note):
            raise ShadowRankingError("assessment_note contains control characters")
    return StoryCandidate(
        candidate_id=_required_text(payload, "candidate_id"),
        title=_required_text(payload, "title"),
        source=_required_text(payload, "source"),
        source_url=str(payload.get("source_url") or "").strip(),
        published_at=parse_utc_datetime(payload.get("published_at")),
        category=str(payload.get("category") or "").strip(),
        is_local_source=booleans["is_local_source"],
        locality=_optional_enum(payload, "locality", VALID_LOCALITY, "unknown"),
        originality=_optional_enum(
            payload, "originality", VALID_ORIGINALITY, "unknown"
        ),
        business_value=_bounded_int(payload, "business_value", 0),
        editorial_fit=_bounded_int(payload, "editorial_fit", 0),
        publisher_type=_optional_enum(
            payload, "publisher_type", VALID_PUBLISHER_TYPES, "unknown"
        ),
        syndication=_optional_enum(
            payload, "syndication", VALID_SYNDICATION, "unknown"
        ),
        has_image=booleans["has_image"],
        image_width=_optional_dimension(payload, "image_width"),
        image_height=_optional_dimension(payload, "image_height"),
        current_importer_selected=booleans["current_importer_selected"],
        story_key=story_key,
        assessment_source=_optional_enum(
            payload,
            "assessment_source",
            VALID_ASSESSMENT_SOURCES,
            "",
        ),
        assessment_note=assessment_note,
    )


def canonicalize_url(value: str) -> str:
    try:
        parts = urlsplit(value.strip())
        port = parts.port
    except ValueError:
        return ""
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        return ""
    query = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMETERS and not key.lower().startswith("utm_")
    ]
    netloc = parts.hostname.lower()
    if port and not (
        (parts.scheme.lower() == "https" and port == 443)
        or (parts.scheme.lower() == "http" and port == 80)
    ):
        netloc = f"{netloc}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), netloc, path, urlencode(query), ""))


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def current_importer_score(candidate: StoryCandidate) -> tuple[int, list[dict]]:
    """Mirror the current sync-rss-now candidate score without calling it."""
    contributions: list[dict] = []

    def add(factor: str, value: int, detail: str) -> None:
        if value:
            contributions.append({"factor": factor, "value": value, "detail": detail})

    add("local_source", 3 if candidate.is_local_source else 0, "local RSS source")
    add(
        "priority_category",
        2 if candidate.category.lower() in CURRENT_PRIORITY_CATEGORIES else 0,
        "business/tech/finance/tax/AI category",
    )
    add(
        "economic_title",
        2 if CURRENT_ECONOMIC_TERMS.search(candidate.title) else 0,
        "economic term in title",
    )
    add(
        "low_utility_title",
        -2 if CURRENT_LOW_UTILITY_TERMS.search(candidate.title) else 0,
        "low-utility term in title",
    )
    return sum(item["value"] for item in contributions), contributions


def shadow_score(
    candidate: StoryCandidate, *, as_of: datetime, weights: RankingWeights
) -> tuple[int, list[dict]]:
    contributions: list[dict] = []

    def add(factor: str, value: int, detail: str) -> None:
        contributions.append({"factor": factor, "value": value, "detail": detail})

    originality_values = {
        "original": weights.original_reporting,
        "mixed": weights.mixed_reporting,
        "press_release": weights.press_release_originality,
        "syndicated": weights.syndicated_originality,
        "unknown": 0,
    }
    locality_values = {
        "town": weights.town_locality,
        "cheshire": weights.cheshire_locality,
        "regional": weights.regional_locality,
        "non_local": weights.non_local,
        "unknown": 0,
    }
    publisher_values = {
        "independent": weights.independent_publisher,
        "official": weights.official_publisher,
        "established": weights.established_publisher,
        "unknown": 0,
    }
    syndication_values = {
        "none": 0,
        "ldrs": weights.ldrs_syndication,
        "press_release": weights.press_release_syndication,
        "syndicated": weights.general_syndication,
        "unknown": 0,
    }
    add(
        "original_reporting",
        originality_values[candidate.originality],
        candidate.originality,
    )
    add("locality", locality_values[candidate.locality], candidate.locality)
    add(
        "business_value",
        candidate.business_value * weights.business_value_unit,
        f"level {candidate.business_value}/3",
    )
    add(
        "editorial_fit",
        candidate.editorial_fit * weights.editorial_fit_unit,
        f"level {candidate.editorial_fit}/3",
    )
    if not candidate.has_image:
        image_value, image_detail = weights.missing_image, "missing"
    elif (
        candidate.image_width is not None
        and candidate.image_height is not None
        and candidate.image_width >= 800
        and candidate.image_height >= 450
    ):
        image_value, image_detail = weights.high_quality_image, "at least 800x450"
    else:
        image_value, image_detail = weights.usable_image, "usable or dimensions unknown"
    add("image_quality", image_value, image_detail)
    age_hours = (as_of - candidate.published_at).total_seconds() / 3600
    if age_hours < 0:
        freshness_value, freshness_detail = weights.future_date, "future dated"
    elif age_hours <= 6:
        freshness_value, freshness_detail = weights.freshness_6h, "0-6 hours"
    elif age_hours <= 24:
        freshness_value, freshness_detail = weights.freshness_24h, "6-24 hours"
    elif age_hours <= 72:
        freshness_value, freshness_detail = weights.freshness_72h, "24-72 hours"
    elif age_hours <= 168:
        freshness_value, freshness_detail = weights.freshness_7d, "3-7 days"
    else:
        freshness_value, freshness_detail = 0, "older than 7 days"
    add("freshness", freshness_value, freshness_detail)
    add(
        "syndication",
        syndication_values[candidate.syndication],
        candidate.syndication,
    )
    add(
        "publisher_type",
        publisher_values[candidate.publisher_type],
        candidate.publisher_type,
    )
    add(
        "source_url",
        0 if canonicalize_url(candidate.source_url) else weights.missing_source_url,
        "valid" if canonicalize_url(candidate.source_url) else "missing or invalid",
    )
    return sum(item["value"] for item in contributions), contributions


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, index: int) -> int:
        while self.parent[index] != index:
            self.parent[index] = self.parent[self.parent[index]]
            index = self.parent[index]
        return index

    def union(self, left: int, right: int) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[max(left_root, right_root)] = min(left_root, right_root)


def group_candidates(
    candidates: Sequence[StoryCandidate],
) -> list[list[StoryCandidate]]:
    """Build hard clusters, then conservatively merge fully similar clusters."""
    union = _UnionFind(len(candidates))
    for left in range(len(candidates)):
        for right in range(left + 1, len(candidates)):
            first, second = candidates[left], candidates[right]
            if _hard_grouping_evidence(first, second):
                union.union(left, right)
    grouped: dict[int, list[StoryCandidate]] = {}
    for index, candidate in enumerate(candidates):
        grouped.setdefault(union.find(index), []).append(candidate)
    clusters = [
        sorted(members, key=lambda item: item.candidate_id)
        for members in grouped.values()
    ]
    clusters.sort(key=lambda members: tuple(item.candidate_id for item in members))

    while True:
        merged = False
        for left in range(len(clusters)):
            for right in range(left + 1, len(clusters)):
                if all(
                    _headlines_probably_similar(first.title, second.title)
                    for first in clusters[left]
                    for second in clusters[right]
                ):
                    combined = sorted(
                        clusters[left] + clusters[right],
                        key=lambda item: item.candidate_id,
                    )
                    clusters = [
                        cluster
                        for index, cluster in enumerate(clusters)
                        if index not in {left, right}
                    ]
                    clusters.append(combined)
                    clusters.sort(
                        key=lambda members: tuple(item.candidate_id for item in members)
                    )
                    merged = True
                    break
            if merged:
                break
        if not merged:
            return clusters


def _hard_grouping_evidence(first: StoryCandidate, second: StoryCandidate) -> list[str]:
    evidence: list[str] = []
    if first.story_key and first.story_key == second.story_key:
        evidence.append("explicit story_key")
    first_url, second_url = canonicalize_url(first.source_url), canonicalize_url(
        second.source_url
    )
    if first_url and first_url == second_url:
        evidence.append("canonical URL")
    first_title, second_title = normalize_title(first.title), normalize_title(
        second.title
    )
    if first_title and first_title == second_title:
        evidence.append("exact normalized title")
    return evidence


def _headlines_probably_similar(first_title: str, second_title: str) -> bool:
    first, second = normalize_title(first_title), normalize_title(second_title)
    return bool(
        len(first) >= 24
        and len(second) >= 24
        and SequenceMatcher(None, first, second).ratio() >= 0.86
    )


def grouping_signals(group: Sequence[StoryCandidate]) -> list[dict]:
    """Explain the direct evidence linking candidate pairs in a group."""
    signals: list[dict] = []
    for left in range(len(group)):
        for right in range(left + 1, len(group)):
            first, second = group[left], group[right]
            hard_evidence = _hard_grouping_evidence(first, second)
            evidence = [
                {"signal": signal, "strength": "hard"} for signal in hard_evidence
            ]
            if not hard_evidence and _headlines_probably_similar(
                first.title, second.title
            ):
                evidence.append(
                    {"signal": "probable similar headline", "strength": "heuristic"}
                )
            if evidence:
                signals.append(
                    {
                        "candidate_ids": [first.candidate_id, second.candidate_id],
                        "evidence": evidence,
                    }
                )
    return signals


def _stable_group_id(group: Sequence[StoryCandidate]) -> str:
    stable_ids = "\x1f".join(sorted(item.candidate_id for item in group))
    digest = hashlib.sha256(stable_ids.encode("utf-8")).hexdigest()[:12]
    return f"story-{digest}"


def _ranked_candidate(
    candidate: StoryCandidate,
    *,
    as_of: datetime,
    weights: RankingWeights,
    input_position: int,
) -> dict:
    current_score, current_factors = current_importer_score(candidate)
    score, factors = shadow_score(candidate, as_of=as_of, weights=weights)
    return {
        "candidate_id": candidate.candidate_id,
        "input_position": input_position,
        "title": candidate.title,
        "source": candidate.source,
        "assessment_source": candidate.assessment_source,
        "assessment_note": candidate.assessment_note,
        "canonical_url": canonicalize_url(candidate.source_url),
        "published_at": candidate.published_at.isoformat(),
        "current_importer_selected": candidate.current_importer_selected,
        "current_importer_score": current_score,
        "current_importer_factors": current_factors,
        "shadow_score": score,
        "shadow_factors": factors,
    }


def evaluate(
    candidates: Sequence[StoryCandidate],
    *,
    as_of: datetime,
    weights: RankingWeights | None = None,
) -> dict:
    if as_of.tzinfo is None or as_of.utcoffset() != timezone.utc.utcoffset(as_of):
        raise ShadowRankingError("as_of must be timezone-aware UTC")
    if not candidates:
        raise ShadowRankingError("at least one candidate is required")
    candidate_ids = [candidate.candidate_id for candidate in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ShadowRankingError("candidate_id values must be unique")
    weights = weights or RankingWeights()
    groups = []
    changed_groups = 0
    input_positions = {
        candidate.candidate_id: index for index, candidate in enumerate(candidates)
    }
    grouped_candidates = group_candidates(candidates)
    grouped_candidates.sort(key=_stable_group_id)
    for group in grouped_candidates:
        ranked = [
            _ranked_candidate(
                item,
                as_of=as_of,
                weights=weights,
                input_position=input_positions[item.candidate_id],
            )
            for item in group
        ]
        ranked.sort(
            key=lambda item: (
                -item["shadow_score"],
                -datetime.fromisoformat(item["published_at"]).timestamp(),
                item["candidate_id"],
            )
        )
        explicitly_selected = [
            item for item in ranked if item["current_importer_selected"]
        ]
        if len(explicitly_selected) > 1:
            raise ShadowRankingError(
                "a related-story group cannot have multiple current selections"
            )
        if explicitly_selected:
            current_choice = explicitly_selected[0]
            current_basis = "input marker"
            ordering_tiebreak = False
            tied_current_ids: list[str] = []
            ordering_note = "explicit selection marker; input order was not used"
        else:
            highest_current_score = max(
                item["current_importer_score"] for item in ranked
            )
            tied_current = [
                item
                for item in ranked
                if item["current_importer_score"] == highest_current_score
            ]
            current_choice = min(tied_current, key=lambda item: item["input_position"])
            current_basis = "simulated current stable score"
            ordering_tiebreak = len(tied_current) > 1
            tied_current_ids = sorted(item["candidate_id"] for item in tied_current)
            ordering_note = (
                f"input position {current_choice['input_position']} broke a current-score tie"
                if ordering_tiebreak
                else "current score was unique; input order did not affect the choice"
            )
        preferred = ranked[0]
        changed = current_choice["candidate_id"] != preferred["candidate_id"]
        changed_groups += int(changed)
        group_signals = grouping_signals(group)
        grouping_strengths = {
            evidence["strength"]
            for signal in group_signals
            for evidence in signal["evidence"]
        }
        if len(group) == 1:
            grouping_basis = "singleton"
        elif grouping_strengths == {"hard", "heuristic"}:
            grouping_basis = "mixed"
        else:
            grouping_basis = next(iter(grouping_strengths), "hard")
        groups.append(
            {
                "group_id": _stable_group_id(group),
                "candidate_count": len(ranked),
                "grouping_signals": group_signals,
                "grouping_basis": grouping_basis,
                "current_choice_basis": current_basis,
                "current_choice_ordering_tiebreak": ordering_tiebreak,
                "current_choice_tied_candidate_ids": tied_current_ids,
                "current_choice_ordering_note": ordering_note,
                "current_importer_choice": current_choice["candidate_id"],
                "shadow_preferred_choice": preferred["candidate_id"],
                "choice_changed": changed,
                "score_margin": preferred["shadow_score"]
                - next(
                    item["shadow_score"]
                    for item in ranked
                    if item["candidate_id"] == current_choice["candidate_id"]
                ),
                "candidates": ranked,
            }
        )
    return {
        "mode": "read_only_story_ranking_shadow",
        "as_of": as_of.isoformat(),
        "database_writes": 0,
        "production_importer_calls": 0,
        "current_importer_model": (
            "sync-rss-now candidate_score stable ordering only; downstream "
            "local-target and per-source caps are not simulated"
        ),
        "weights": asdict(weights),
        "diagnostics": {
            "candidate_count": len(candidates),
            "group_count": len(groups),
            "changed_group_count": changed_groups,
            "unchanged_group_count": len(groups) - changed_groups,
        },
        "groups": groups,
    }


def load_input(payload: Any) -> list[StoryCandidate]:
    if isinstance(payload, Mapping):
        payload = payload.get("candidates")
    if not isinstance(payload, list):
        raise ShadowRankingError("input must be an array or contain a candidates array")
    return [parse_candidate(item) for item in payload]


def _read_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _summary(report: Mapping[str, Any]) -> str:
    diagnostics = report["diagnostics"]
    return (
        "Story ranking shadow evaluation (read-only)\n"
        f"Candidates: {diagnostics['candidate_count']} | "
        f"groups: {diagnostics['group_count']} | "
        f"changed preferences: {diagnostics['changed_group_count']}"
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", required=True, help="JSON snapshot path, or - for stdin"
    )
    parser.add_argument(
        "--as-of", required=True, help="timezone-aware UTC ISO-8601 time"
    )
    parser.add_argument(
        "--weights",
        help="optional JSON object overriding named integer weights",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        candidates = load_input(_read_json(args.input))
        weights_payload = json.loads(args.weights) if args.weights else None
        weights = RankingWeights.from_mapping(weights_payload)
        report = evaluate(
            candidates,
            as_of=parse_utc_datetime(args.as_of, "as_of"),
            weights=weights,
        )
    except (OSError, json.JSONDecodeError, ShadowRankingError):
        print("Story ranking shadow evaluation failed safely.", file=sys.stderr)
        return 1
    print(_summary(report), file=sys.stderr)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
