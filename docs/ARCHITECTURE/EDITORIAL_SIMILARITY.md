# Cheshire Today — Editorial Similarity Architecture

> **Reconstruction status:** Phase 2A and Phase 2B current code at HEAD. Calibration and UI work are not complete.

## Document purpose

Document the deterministic scorer and its scheduled-only shadow integration, including guarantees that prevent operational decisions.

## Authority and evidence

Primary evidence: `backend/app/editorial_similarity.py`, `backend/app/editorial_similarity_shadow.py`, four integration points in `backend/server.py`, `tests/test_editorial_similarity.py`, `tests/test_editorial_similarity_shadow.py`, and `tests/test_editorial_similarity_shadow_runtime.py`. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Use it to interpret shadow logs and design later reviewed phases. Do not use scores as publication instructions.

## Phase 2A pure scorer

`score_editorial_similarity(candidate, existing)` is deterministic, side-effect-free and identity-free. Its immutable `EditorialSimilarityResult` contains only `eligible`, integer `score` (0–100), a band (`ineligible`, `low`, `possible`, `likely`, `very_likely`) and a bounded tuple of allow-listed reason codes.

Inputs are independently bounded before normalisation: title 300 characters, summary 2,000, content 4,000, source URL 2,048, and tokenisation 600 tokens. Valid exact normalised-title or canonical source-URL matches return the `ineligible` result because Version 1 should own them. Unexpected exceptions return an eligible score-zero low-band fallback without input content.

Signals include headline/text overlap, planning references, distinctive facts, locality/site, organisations and time/follow-up evidence. No MongoDB, network, provider, image or filesystem access exists.

## Phase 2B scheduled shadow integration

Only `daily_article_generation -> _generate_articles_internal -> _import_hybrid_news_internal` passes `enable_editorial_similarity_shadow=True`; defaults are false and Admin/manual imports cannot activate it through request data.

The initial corpus loads at most 50 newest active plus 50 newest archived snapshots. Snapshots retain safe identity, bounded scorer fields, normalised timestamp and allow-listed provenance. Successfully inserted records can enter the same-run corpus. The corpus cap is 100 and oldest records are evicted deterministically.

## Shortlist and selection

A cheap deterministic shortlist uses bounded title-token overlap, planning-reference overlap, distinctive fact overlap and locality/site evidence. Generic terms alone do not admit every record. The shortlist and pure-scorer call count are each capped at 20 per candidate.

Best eligible match ordering is: highest score, strongest eligible band, newest normalised timestamp, then stable safe ID. Ineligible results cannot displace meaningful eligible matches. Provenance is allow-listed as `active`, `archived` or `same_run`.

## Logging contract

After every successful enabled insertion, a bounded log attempt records either the best advisory or a zero/no-match event. The schema validates fixed event/status, context, candidate/matched safe IDs, provenance, eligibility, score, band, reason codes, comparison/shortlist counts, scorer version and shadow identifier. It excludes article text, URLs, sources, images, raw tokens, payloads and exception text.

## Shadow-only guarantees

At current HEAD the subsystem does **not** block, merge, archive, delete, update, reject, reroute to Manual Review or change publication. It stores no article metadata, adds no API/UI, and never replaces Version 1 exact duplicate prevention. Pool, snapshot, scorer and logger failures fail open after the existing insert decision.

## Observation gate

At least three normal scheduled runs must be observed before threshold, UI or operational-decision work. Review pool sizes, comparison and shortlist counts, bands, reasons, provenance, scheduler duration, memory and unchanged publication outcomes. Do not trigger manual imports to manufacture evidence.

## Protected boundaries

Keep the pure result identity-free; explicit scheduled activation only; corpus and shortlist caps; privacy-safe logs; one article insert; and Version 1 authority.

## Known limitations

Cheap shortlisting can miss semantically related stories without shared bounded signals. Logs provide sampled operational evidence, not labelled ground truth. Images are intentionally excluded.

## Related documents

[Article Pipeline](ARTICLE_PIPELINE.md), [Monitoring](../OPERATIONS/MONITORING.md), [Scheduler](../OPERATIONS/SCHEDULER.md), [Decision Register](../DECISION_REGISTER.md), and [Architecture Master](../ARCHITECTURE_MASTER.md).
