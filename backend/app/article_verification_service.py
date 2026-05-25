"""
Article verification and rewrite service for Cheshire Today.

Purpose:
- Keep RSS discovery as the source of candidate articles.
- Verify selected articles before publication.
- Return structured decisions: publish, manual_review, or reject.
- Keep provider choice configurable and budget-safe.

This service is intentionally disabled by default until API keys and Render env vars
are configured.
"""

import os
import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_verification_usage = {
    "date": date.today().isoformat(),
    "calls": 0,
    "estimated_spend_gbp": 0.0,
}



@dataclass
class VerificationResult:
    publishable: bool
    manual_review_required: bool
    reject: bool
    reason: str
    category: str
    verified_facts: List[str]
    unsupported_claims: List[str]
    source_urls: List[str]
    cheshire_angle: str
    rewritten_article: str
    estimated_cost_gbp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "publishable": self.publishable,
            "manual_review_required": self.manual_review_required,
            "reject": self.reject,
            "reason": self.reason,
            "category": self.category,
            "verified_facts": self.verified_facts,
            "unsupported_claims": self.unsupported_claims,
            "source_urls": self.source_urls,
            "cheshire_angle": self.cheshire_angle,
            "rewritten_article": self.rewritten_article,
            "estimated_cost_gbp": self.estimated_cost_gbp,
        }


class ArticleVerificationService:
    """
    Provider-agnostic verification pipeline.

    Current safe default:
    - disabled unless ARTICLE_VERIFICATION_ENABLED=true
    - does not publish anything directly
    - caller decides whether to publish or send to Manual Review
    """

    def __init__(self):
        self.enabled = os.getenv("ARTICLE_VERIFICATION_ENABLED", "false").strip().lower() in ("1", "true", "yes", "y")
        self.provider = os.getenv("ARTICLE_VERIFICATION_PROVIDER", "gemini").strip().lower()
        self.daily_budget_gbp = float(os.getenv("ARTICLE_VERIFICATION_DAILY_BUDGET_GBP", "1.30"))
        self.hard_cap = os.getenv("ARTICLE_VERIFICATION_HARD_CAP", "1").strip().lower() in ("1", "true", "yes", "y")
        self.timeout = float(os.getenv("ARTICLE_VERIFICATION_TIMEOUT_SECONDS", "60"))
        self.per_call_estimate_gbp = float(os.getenv("ARTICLE_VERIFICATION_COST_ESTIMATE_GBP", "0.08"))

    def _refresh_budget_config(self):
        self.daily_budget_gbp = float(os.getenv("ARTICLE_VERIFICATION_DAILY_BUDGET_GBP", str(self.daily_budget_gbp)))
        self.hard_cap = os.getenv("ARTICLE_VERIFICATION_HARD_CAP", "1").strip().lower() in ("1", "true", "yes", "y")
        self.per_call_estimate_gbp = float(os.getenv("ARTICLE_VERIFICATION_COST_ESTIMATE_GBP", str(self.per_call_estimate_gbp)))

    def get_budget_status(self) -> Dict[str, Any]:
        self._refresh_budget_config()

        today = date.today().isoformat()
        if _verification_usage["date"] != today:
            return {
                "date": today,
                "calls": 0,
                "estimated_spend_gbp": 0.0,
                "daily_budget_gbp": self.daily_budget_gbp,
                "per_call_estimate_gbp": self.per_call_estimate_gbp,
                "hard_cap": self.hard_cap,
            }

        return {
            "date": _verification_usage["date"],
            "calls": _verification_usage["calls"],
            "estimated_spend_gbp": round(float(_verification_usage["estimated_spend_gbp"]), 4),
            "daily_budget_gbp": self.daily_budget_gbp,
            "per_call_estimate_gbp": self.per_call_estimate_gbp,
            "hard_cap": self.hard_cap,
        }

    def _budget_allows_call(self) -> bool:
        self._refresh_budget_config()

        today = date.today().isoformat()
        if _verification_usage["date"] != today:
            _verification_usage["date"] = today
            _verification_usage["calls"] = 0
            _verification_usage["estimated_spend_gbp"] = 0.0

        projected = _verification_usage["estimated_spend_gbp"] + self.per_call_estimate_gbp
        if projected > self.daily_budget_gbp:
            logger.warning(
                f"Article verification budget guard: projected £{projected:.2f} exceeds daily budget £{self.daily_budget_gbp:.2f}."
            )
            if self.hard_cap:
                return False

        _verification_usage["calls"] += 1
        _verification_usage["estimated_spend_gbp"] = projected
        return True

    async def verify_and_rewrite_candidate(self, article: Dict[str, Any]) -> VerificationResult:
        """
        Verify and rewrite one selected RSS candidate.

        This is a placeholder-safe implementation until provider credentials are added.
        It returns Manual Review when disabled so no article can accidentally publish.
        """
        title = (article.get("title") or "").strip()
        category = (article.get("category") or "").strip() or "Unknown"
        source_url = (article.get("source_url") or "").strip()

        if not self.enabled:
            return VerificationResult(
                publishable=False,
                manual_review_required=True,
                reject=False,
                reason="Structured verification service is disabled. Configure provider keys and ARTICLE_VERIFICATION_ENABLED=true before using automatic verified publishing.",
                category=category,
                verified_facts=[],
                unsupported_claims=[],
                source_urls=[source_url] if source_url else [],
                cheshire_angle="",
                rewritten_article="",
            )

        if not self._budget_allows_call():
            return VerificationResult(
                publishable=False,
                manual_review_required=True,
                reject=False,
                reason=f"Article verification daily budget reached. Daily budget £{self.daily_budget_gbp:.2f}; hard cap is enabled.",
                category=category,
                verified_facts=[],
                unsupported_claims=[],
                source_urls=[source_url] if source_url else [],
                cheshire_angle="",
                rewritten_article="",
                estimated_cost_gbp=0.0,
            )

        if self.provider == "tavily":
            return await self._verify_with_tavily(article)

        if self.provider == "openai":
            return await self._verify_with_openai(article)

        if self.provider == "gemini":
            return await self._verify_with_gemini(article)

        return VerificationResult(
            publishable=False,
            manual_review_required=True,
            reject=False,
            reason=f"Unknown ARTICLE_VERIFICATION_PROVIDER: {self.provider}",
            category=category,
            verified_facts=[],
            unsupported_claims=[],
            source_urls=[source_url] if source_url else [],
            cheshire_angle="",
            rewritten_article="",
        )

    async def _verify_with_tavily(self, article: Dict[str, Any]) -> VerificationResult:
        api_key = os.getenv("TAVILY_API_KEY", "").strip()
        if not api_key:
            return self._missing_key_result(article, "TAVILY_API_KEY")

        # Provider implementation will be added after account/API key setup.
        return self._not_wired_result(article, "Tavily")

    async def _verify_with_openai(self, article: Dict[str, Any]) -> VerificationResult:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return self._missing_key_result(article, "OPENAI_API_KEY")

        # Provider implementation will be added after account/API key setup.
        return self._not_wired_result(article, "OpenAI")

    async def _verify_with_gemini(self, article: Dict[str, Any]) -> VerificationResult:
        api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key:
            return self._missing_key_result(article, "GEMINI_API_KEY or GOOGLE_API_KEY")

        try:
            import asyncio
            from google import genai
            from google.genai import types

            model = os.getenv("GEMINI_VERIFICATION_MODEL", "gemini-2.5-flash")
            client = genai.Client(api_key=api_key)

            source_text = await self._fetch_source_text(article.get("source_url", ""))
            evidence_prompt = self._build_gemini_evidence_prompt(article, source_text)

            def run_evidence_call():
                return client.models.generate_content(
                    model=model,
                    contents=evidence_prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1,
                        max_output_tokens=2500,
                    ),
                )

            evidence_response = await asyncio.wait_for(
                asyncio.to_thread(run_evidence_call),
                timeout=self.timeout,
            )

            evidence_text = (getattr(evidence_response, "text", "") or "").strip()
            grounding_urls = self._extract_gemini_grounding_urls(evidence_response)

            if not evidence_text:
                return VerificationResult(
                    publishable=False,
                    manual_review_required=True,
                    reject=False,
                    reason="Gemini grounding returned no evidence text. Article needs Manual Review.",
                    category=(article.get("category") or "Unknown"),
                    verified_facts=[],
                    unsupported_claims=[],
                    source_urls=grounding_urls or ([article.get("source_url")] if article.get("source_url") else []),
                    cheshire_angle="",
                    rewritten_article="",
                    estimated_cost_gbp=self.per_call_estimate_gbp,
                )

            json_prompt = self._build_gemini_json_prompt(article, evidence_text, grounding_urls)

            def run_json_call():
                return client.models.generate_content(
                    model=model,
                    contents=json_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=3500,
                        response_mime_type="application/json",
                    ),
                )

            json_response = await asyncio.wait_for(
                asyncio.to_thread(run_json_call),
                timeout=self.timeout,
            )

            raw_text = (getattr(json_response, "text", "") or "").strip()
            result = self._parse_verification_json(raw_text, article, grounding_urls)
            result.estimated_cost_gbp = self.per_call_estimate_gbp
            return result

        except Exception as e:
            logger.error(f"Gemini verification failed: {str(e)}")
            return VerificationResult(
                publishable=False,
                manual_review_required=True,
                reject=False,
                reason=f"Gemini verification failed and article needs Manual Review: {str(e)[:180]}",
                category=(article.get("category") or "Unknown"),
                verified_facts=[],
                unsupported_claims=[],
                source_urls=[article.get("source_url")] if article.get("source_url") else [],
                cheshire_angle="",
                rewritten_article="",
                estimated_cost_gbp=self.per_call_estimate_gbp,
            )

    async def _fetch_source_text(self, source_url: str) -> str:
        """Fetch limited readable text from the original source URL for verification context."""
        if not source_url:
            return ""

        try:
            from bs4 import BeautifulSoup

            async with httpx.AsyncClient(
                timeout=min(self.timeout, 20.0),
                follow_redirects=True,
                headers={
                    "User-Agent": "CheshireTodayBot/1.0 (+https://cheshiretoday.co.uk)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            ) as client:
                response = await client.get(source_url)

            if response.status_code >= 400:
                logger.warning(f"Source fetch failed {response.status_code}: {source_url[:120]}")
                return ""

            soup = BeautifulSoup(response.text or "", "html.parser")
            for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
                tag.decompose()

            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            meta_desc = ""
            meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if meta and meta.get("content"):
                meta_desc = meta.get("content", "").strip()

            paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
            body = " ".join([x for x in paragraphs if x])
            text = "\n".join([x for x in [title, meta_desc, body] if x]).strip()
            return text[:6000]

        except Exception as e:
            logger.warning(f"Source fetch exception for verification: {str(e)[:180]}")
            return ""

    def _build_gemini_evidence_prompt(self, article: Dict[str, Any], source_text: str = "") -> str:
        title = (article.get("title") or "").strip()
        summary = (article.get("summary") or article.get("content") or "").strip()
        source = (article.get("source") or "").strip()
        source_url = (article.get("source_url") or "").strip()
        category = (article.get("category") or "").strip()

        return f"""You are researching facts for Cheshire Today.

Check this article candidate using Google Search grounding. Do not write the article yet.

Cheshire Today strategy:
- Hybrid Cheshire local + Business/Finance + AI/Tech authority platform.
- Avoid weak generic filler, crime-heavy filler, celebrity filler, sports filler, and exaggerated claims.
- Prioritise practical relevance to Cheshire readers, households, workers, small businesses, investors, taxpayers and technology users.

Article candidate:
Title: {title}
Category: {category}
Source: {source}
Source URL: {source_url}
Summary/content:
{summary[:3000]}

Fetched source text from source URL:
{(source_text or "")[:6000]}

Return concise evidence notes only:
- Whether the source URL/source claim is verifiable.
- Key verified facts with dates, names, figures and source names.
- Any unsupported or risky claims.
- Whether it is suitable for Cheshire Today.
- Whether a Cheshire reader angle is justified.
"""

    def _build_gemini_json_prompt(self, article: Dict[str, Any], evidence_text: str, grounding_urls: List[str]) -> str:
        title = (article.get("title") or "").strip()
        summary = (article.get("summary") or article.get("content") or "").strip()
        source = (article.get("source") or "").strip()
        source_url = (article.get("source_url") or "").strip()
        category = (article.get("category") or "").strip()
        urls_text = "\n".join([str(u) for u in (grounding_urls or [])[:10]])

        return f"""You are the verification editor for Cheshire Today.

Use only the evidence notes below. Return only valid JSON. Do not include markdown.

Article candidate:
Title: {title}
Category: {category}
Source: {source}
Source URL: {source_url}
Original summary/content:
{summary[:2500]}

Grounded evidence notes:
{evidence_text[:5000]}

Grounding/source URLs:
{urls_text}

Return only valid JSON with this exact shape:
{{
  "publishable": false,
  "manual_review_required": true,
  "reject": false,
  "reason": "short reason",
  "category": "Business|Finance|Tech|Local News|UK News|Other",
  "verified_facts": ["fact 1", "fact 2"],
  "unsupported_claims": ["claim 1"],
  "source_urls": ["https://..."],
  "cheshire_angle": "short practical angle or empty string",
  "rewritten_article": "plain text article, no markdown, 1000-2200 characters only if verified"
}}

Rules:
- publishable=true only if rewritten_article is accurate, useful, and based only on verified facts.
- manual_review_required=true if facts are thin, source access is weak, article is too opinion-led, rewrite is uncertain, or Cheshire Today suitability is borderline.
- reject=true for crime-heavy filler, celebrity filler, sport, weak generic filler, unsupported viral/social claims, or stories with no useful reader/economic relevance.
- For Cheshire local stories, require a specific town, village, road, venue, site, business, council area, school, hospital, or named local place.
- National Business, Finance, Tech, AI, Science, Tax, Property or UK-wide stories do not need a Cheshire location, named Cheshire source, local case study, or local quote. Clear practical relevance to Cheshire households, workers, small businesses, taxpayers, investors or technology users is enough.
- Do not mark a verified national Business, Finance, Tech, AI, Science, Tax, Property or UK-wide story as manual_review_required only because it lacks a specific Cheshire example.
- For national Business/Finance/cost-of-living stories, verified facts from a reliable national source plus clear practical relevance to Cheshire households, workers, small businesses or taxpayers is sufficient for publishable=true.
- Only require specific Cheshire evidence when the article makes a specific Cheshire/local claim.
- If verified facts are strong and unsupported_claims is empty, produce a rewritten_article with a practical Cheshire reader framing, but do not invent local examples.
- Do not leave rewritten_article empty unless reject=true or there are not enough verified facts to write safely.
- Do not invent quotes, numbers, locations, officials, costs, dates, jobs, homes, reactions or local impact.
"""

    def _parse_verification_json(self, raw_text: str, article: Dict[str, Any], grounding_urls: Optional[List[str]] = None) -> VerificationResult:
        import re

        grounding_urls = grounding_urls or []
        text = (raw_text or "").strip()

        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"```$", "", text).strip()

        try:
            data = json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    data = {}
            else:
                data = {}

        if not isinstance(data, dict):
            data = {}

        source_urls = data.get("source_urls") or []
        if not isinstance(source_urls, list):
            source_urls = []
        for url in grounding_urls:
            if url and url not in source_urls:
                source_urls.append(url)

        rewritten_article = str(data.get("rewritten_article") or "").strip()
        verified_facts = data.get("verified_facts") if isinstance(data.get("verified_facts"), list) else []
        unsupported_claims = data.get("unsupported_claims") if isinstance(data.get("unsupported_claims"), list) else []

        has_unsupported_claims = len(unsupported_claims) > 0
        unverified_numeric_claims = self._find_unverified_numeric_claims(rewritten_article, verified_facts)
        publishable = (
            bool(data.get("publishable"))
            and len(rewritten_article) >= 1000
            and len(verified_facts) >= 2
            and not has_unsupported_claims
            and not unverified_numeric_claims
        )
        manual_review_required = bool(data.get("manual_review_required")) or not publishable or has_unsupported_claims or bool(unverified_numeric_claims)
        reject = bool(data.get("reject"))

        final_publishable = publishable and not reject and not manual_review_required
        final_reason = str(data.get("reason") or "").strip()
        if final_publishable and not final_reason:
            final_reason = "Verified facts and rewrite passed automatic dry-run checks."
        elif not final_reason:
            final_reason = "Gemini response could not fully prove safe automatic publishing."

        return VerificationResult(
            publishable=final_publishable,
            manual_review_required=manual_review_required and not reject,
            reject=reject,
            reason=final_reason,
            category=str(data.get("category") or article.get("category") or "Unknown").strip(),
            verified_facts=[str(x).strip() for x in verified_facts if str(x).strip()][:12],
            unsupported_claims=([str(x).strip() for x in unsupported_claims if str(x).strip()] + unverified_numeric_claims)[:12],
            source_urls=[str(x).strip() for x in source_urls if str(x).strip()][:10],
            cheshire_angle=str(data.get("cheshire_angle") or "").strip(),
            rewritten_article=rewritten_article,
        )

    def _find_unverified_numeric_claims(self, rewritten_article: str, verified_facts: List[str]) -> List[str]:
        import re

        article_text = rewritten_article or ""
        facts_text = " ".join([str(x) for x in (verified_facts or [])])

        numeric_patterns = [
            r"£\s?\d+(?:\.\d+)?\s?(?:bn|m|million|billion)?",
            r"\d+(?:\.\d+)?\s?%",
            r"\b\d+(?:\.\d+)?p\b",
            r"\b\d+(?:\.\d+)?\s?(?:pence|per cent|million|billion|bn|m)\b",
            r"\b(?:19|20)\d{2}\b",
            r"\bQ[1-4]\s+(?:19|20)\d{2}\b",
        ]

        unverified = []
        seen = set()
        for pattern in numeric_patterns:
            for match in re.findall(pattern, article_text, flags=re.IGNORECASE):
                value = match.strip()
                if value.lower() in seen:
                    continue
                seen.add(value.lower())
                if value not in facts_text:
                    unverified.append(f"Rewrite contains numeric claim not present in verified_facts: {value}")

        return unverified[:6]

    def _extract_gemini_grounding_urls(self, response: Any) -> List[str]:
        urls = []
        try:
            candidates = getattr(response, "candidates", []) or []
            for candidate in candidates:
                grounding_metadata = getattr(candidate, "grounding_metadata", None)
                chunks = getattr(grounding_metadata, "grounding_chunks", []) if grounding_metadata else []
                for chunk in chunks or []:
                    web = getattr(chunk, "web", None)
                    uri = getattr(web, "uri", "") if web else ""
                    if uri and uri not in urls:
                        urls.append(uri)
        except Exception:
            pass
        return urls[:10]

    def _missing_key_result(self, article: Dict[str, Any], key_name: str) -> VerificationResult:
        return VerificationResult(
            publishable=False,
            manual_review_required=True,
            reject=False,
            reason=f"Missing {key_name}. Article requires Manual Review until provider is configured.",
            category=(article.get("category") or "Unknown"),
            verified_facts=[],
            unsupported_claims=[],
            source_urls=[article.get("source_url")] if article.get("source_url") else [],
            cheshire_angle="",
            rewritten_article="",
        )

    def _not_wired_result(self, article: Dict[str, Any], provider_name: str) -> VerificationResult:
        return VerificationResult(
            publishable=False,
            manual_review_required=True,
            reject=False,
            reason=f"{provider_name} verification is configured but not wired into the publishing pipeline yet.",
            category=(article.get("category") or "Unknown"),
            verified_facts=[],
            unsupported_claims=[],
            source_urls=[article.get("source_url")] if article.get("source_url") else [],
            cheshire_angle="",
            rewritten_article="",
        )


article_verification_service = ArticleVerificationService()
