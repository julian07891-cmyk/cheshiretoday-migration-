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
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


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

        # Provider implementation will be added after account/API key setup.
        return self._not_wired_result(article, "Gemini")

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
