"""
Perplexity AI Service for Cheshire News
Uses Perplexity API to search for Cheshire-specific news articles
Cost-optimized: Only used for local Cheshire news, not general UK news
"""

import os
import httpx
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


def validate_fact_pack_people(
    fact_pack: Dict[str, Any],
    publisher_content: str = "",
    publisher_url: str = "",
) -> Dict[str, Any]:
    """Downgrade incomplete or unsupported verified person identities."""
    names_and_roles = fact_pack.get("names_and_roles")
    if not isinstance(names_and_roles, list):
        fact_pack["names_and_roles"] = []
        return fact_pack

    uncertain = fact_pack.get("uncertain_or_unverified")
    if not isinstance(uncertain, list):
        uncertain = []

    publisher_text = re.sub(r"\s+", " ", str(publisher_content or "")).strip()
    normalised_publisher_url = str(publisher_url or "").strip().rstrip("/")
    listed_source_keys = {
        (
            urlparse(str(url or "").strip()).netloc.lower(),
            urlparse(str(url or "").strip()).path.rstrip("/"),
        )
        for url in fact_pack.get("source_urls", [])
        if str(url or "").strip()
    }
    honorifics = {
        "dr", "mr", "mrs", "ms", "miss", "prof", "professor",
        "sir", "dame", "lord", "lady", "rev", "reverend",
    }

    for item in names_and_roles:
        if not isinstance(item, dict) or item.get("verified") is not True:
            continue

        name = re.sub(r"\s+", " ", str(item.get("name") or "")).strip()
        tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'’-]+", name)
        reason = ""

        if len(tokens) < 2:
            reason = "incomplete personal name"
        elif tokens[0].rstrip(".").lower() in honorifics and len(tokens) < 3:
            reason = "incomplete honorific-based personal name"
        item_source_url = str(item.get("source_url") or "").strip().rstrip("/")
        publisher_source_key = (
            urlparse(normalised_publisher_url).netloc.lower(),
            urlparse(normalised_publisher_url).path.rstrip("/"),
        )
        item_source_key = (
            urlparse(item_source_url).netloc.lower(),
            urlparse(item_source_url).path.rstrip("/"),
        )
        independent_provenance = (
            bool(item_source_url)
            and item_source_key in listed_source_keys
            and item_source_key != publisher_source_key
        )
        publisher_is_claimed_source = not independent_provenance
        if (
            not reason
            and publisher_text
            and publisher_is_claimed_source
            and not re.search(r"\b" + re.escape(name) + r"\b", publisher_text, re.IGNORECASE)
        ):
            reason = "name was not found in the fetched publisher content"

        if reason:
            item["verified"] = False
            uncertain.append(f"Unverified person identity ({reason}): {name or '[missing name]'}")

    fact_pack["uncertain_or_unverified"] = list(dict.fromkeys(uncertain))
    return fact_pack



# =========================
# HARD DAILY AI SPEND GUARD
# =========================
from datetime import date

DAILY_AI_SPEND_GBP = float(os.getenv("PERPLEXITY_DAILY_BUDGET_GBP", "0.70"))  # ~£20/mo soft target by default
PERPLEXITY_HARD_CAP = os.getenv("PERPLEXITY_HARD_CAP", "0").strip().lower() in ("1","true","yes","y")
_ai_usage = {"date": date.today().isoformat(), "calls": 0}

def ai_budget_available(cost_estimate_gbp: float = 0.05) -> bool:
    today = date.today().isoformat()
    if _ai_usage["date"] != today:
        return True
    projected = (_ai_usage["calls"] + 1) * cost_estimate_gbp
    return projected <= DAILY_AI_SPEND_GBP


def ai_call_allowed(cost_estimate_gbp: float = 0.05) -> bool:
    today = date.today().isoformat()
    if _ai_usage["date"] != today:
        _ai_usage["date"] = today
        _ai_usage["calls"] = 0

    projected = (_ai_usage["calls"] + 1) * cost_estimate_gbp
    if projected > DAILY_AI_SPEND_GBP:
        logger.warning(
            f"Perplexity spend guard: projected £{projected:.2f} exceeds daily budget £{DAILY_AI_SPEND_GBP:.2f}. Proceeding (soft cap)."
        )
        if PERPLEXITY_HARD_CAP:
            return False

    _ai_usage["calls"] += 1
    return True

class PerplexityService:
    """Service for searching Cheshire-specific news using Perplexity API"""
    
    def __init__(self):
        self.timeout = 60.0
    
    @property
    def api_key(self):
        """Get API key dynamically to ensure it's loaded from environment"""
        return os.environ.get('PERPLEXITY_API_KEY', '')
        
    def _get_headers(self) -> dict:
        """Get headers for Perplexity API requests"""
        key = self.api_key
        if not key:
            logger.warning("PERPLEXITY_API_KEY not found in environment")
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
    
    async def search_cheshire_news(self, category: str = None, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Search for Cheshire-specific news using Perplexity API
        Cost-optimized: Returns minimal results for cost efficiency
        
        Args:
            category: Optional category to filter news (e.g., "Local News", "Business")
            limit: Maximum number of articles to return (default 3 for cost efficiency)
            
        Returns:
            List of article dictionaries with title, content, source_url, image (if available)
        """
        if not self.api_key:
            logger.error("Perplexity API key not configured")
            return []

        # Soft budget guard (optional hard cap via PERPLEXITY_HARD_CAP=1)
        if not ai_call_allowed(0.05):
            logger.warning("Perplexity budget guard: skipping search_cheshire_news() call")
            return []
        
        # Build search query focused on Cheshire
        cheshire_locations = [
            "Cheshire", "Chester", "Macclesfield", "Wilmslow", "Knutsford",
            "Alderley Edge", "Prestbury", "Congleton", "Crewe", "Nantwich",
            "Warrington", "Northwich", "Sandbach"
        ]
        
        if category and category != "Local News":
            query = f"Latest {category.lower()} news in Cheshire, UK today. Focus on {', '.join(cheshire_locations[:5])} area."
        else:
            query = f"Latest local news in Cheshire, UK today. Include news from {', '.join(cheshire_locations[:5])}."
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": "sonar",  # Most cost-effective model
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a news researcher for Cheshire Today, a local news website. 
                            Search for the most recent news stories specifically about Cheshire, UK and nearby areas.
                            Return ONLY factual, current news stories with verifiable sources.
                            Format each article as JSON with: title, summary (2-3 sentences), source_name, source_url
                            Return a JSON array of articles. Maximum 3 articles."""
                        },
                        {
                            "role": "user", 
                            "content": query
                        }
                    ],
                    "max_tokens": 1024,  # Limit tokens for cost efficiency
                    "temperature": 0.1,  # Low temperature for factual responses
                    "return_citations": True,
                    "search_recency_filter": "day"  # Only recent news
                }
                
                response = await client.post(
                    PERPLEXITY_API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                    return []
                
                data = response.json()
                
                # Extract articles from response
                articles = self._parse_perplexity_response(data, category)
                
                logger.info(f"Found {len(articles)} Cheshire news articles via Perplexity")
                return articles[:limit]
                
        except httpx.TimeoutException:
            logger.error("Perplexity API timeout")
            return []
        except Exception as e:
            logger.error(f"Error searching Perplexity: {str(e)}")
            return []
    
    def _parse_perplexity_response(self, data: dict, category: str = None) -> List[Dict[str, Any]]:
        """Parse Perplexity API response into article format"""
        articles = []
        
        try:
            # Get the response content
            choices = data.get('choices', [])
            if not choices:
                return []
            
            content = choices[0].get('message', {}).get('content', '')
            citations = data.get('citations', [])
            
            # Try to parse as JSON
            import json
            try:
                # Try to extract JSON from the response
                # Sometimes the response includes markdown code blocks
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                elif '```' in content:
                    json_start = content.find('```') + 3
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                
                parsed_articles = json.loads(content)
                
                if isinstance(parsed_articles, list):
                    for item in parsed_articles:
                        article = {
                            'title': item.get('title', ''),
                            'content': item.get('summary', item.get('content', '')),
                            'source': item.get('source_name', 'Perplexity AI'),
                            'source_url': item.get('source_url', ''),
                            'category': category or 'Local News',
                            'image': None,  # Will be filled from RSS or stock photos
                            'publishedDate': datetime.now(timezone.utc).isoformat(),
                            'is_cheshire_related': True,
                            'is_real_news': True
                        }
                        if article['title'] and article['content']:
                            articles.append(article)
                            
            except json.JSONDecodeError:
                # If not valid JSON, try to extract articles from plain text
                logger.warning("Could not parse Perplexity response as JSON, extracting from text")
                
                # Create a single article from the response
                if content and len(content) > 50:
                    # Use citations as sources if available
                    source_url = citations[0] if citations else ''
                    
                    article = {
                        'title': f"Cheshire News Update: {category or 'Local News'}",
                        'content': content[:500],
                        'source': 'Perplexity AI',
                        'source_url': source_url,
                        'category': category or 'Local News',
                        'image': None,
                        'publishedDate': datetime.now(timezone.utc).isoformat(),
                        'is_cheshire_related': True,
                        'is_real_news': True
                    }
                    articles.append(article)
                    
        except Exception as e:
            logger.error(f"Error parsing Perplexity response: {str(e)}")
        
        return articles

    async def generate_article_content(self, title: str, summary: str, source: str, source_url: str = "") -> str:

        # =========================
        # HARD COST GUARD (DEFAULT OFF)
        # Set PERPLEXITY_ENABLED=true to allow paid generation.
        # =========================
        import os
        enabled = os.getenv("PERPLEXITY_ENABLED", "true").strip().lower() in ("1", "true", "yes", "y")
        if not enabled:
            # Return a free fallback (RSS summary + link) instead of calling Perplexity
            fallback = (summary or "").strip()
            if source_url:
                if fallback:
                    fallback = f"{fallback}\n\nRead the full story at the source: {source_url}"
                else:
                    fallback = f"Read the full story at the source: {source_url}"
            return fallback or "Read the full story at the source."
        """
        Generate detailed article content using Perplexity's web search.
        Searches for real information about the news topic and creates a summary.
        
        Cost: ~$0.005 per call
        
        Args:
            title: Article headline
            summary: Short description from RSS feed
            source: Original source (BBC, Guardian, etc.)
            source_url: URL to original article
            
        Returns:
            Detailed article content aiming for 700-900 words and 2000+ characters.
        """
        if not self.api_key:
            logger.error("Perplexity API key not configured")
            return ""  # No fallback articles: caller must skip weak/failed rewrites

        # Soft budget guard (optional hard cap via PERPLEXITY_HARD_CAP=1)
        if not ai_call_allowed(0.05):
            logger.warning("Perplexity budget guard: skipping generate_article_content() call")
            return ""  # No fallback articles: caller must skip weak/failed rewrites
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a careful UK local news rewrite editor for Cheshire Today.

Your task is to research the story using the provided Source URL as the primary reference, then rewrite it as a clean, original Cheshire Today article without inventing facts.

CRITICAL ACCURACY RULES:
1. The Source URL is the primary reference. Do not override it with guesses from the headline.
2. Verify the exact venue, business name, road, village, town, council area and county before naming them.
3. If the exact location is not confirmed by the source URL or another reliable source, use only a broad phrase such as "in Cheshire" or "in the local area".
4. Never invent street names, town centres, quotes, anonymous residents, repair bills, smashed windows, police involvement, social media reaction, business history or previous incidents unless they are clearly supported by the source material.
5. Do not pad thin stories with generic background. Accuracy is more important than length.
6. If source material is limited, write a shorter accurate article rather than adding unsupported details.
7. Attribute claims carefully, using wording such as "according to the source report" or "the business said" only where supported.
8. Use British English and short paragraphs for mobile reading.
9. Add local context only when it is directly relevant and does not introduce unsupported claims.
10. Write like a human UK local/business editor, not an AI explainer. Lead with the concrete fact first.
11. Avoid generic explainer phrases such as "this matters because", "fresh attention", "a notable step", "underlines", "on the face of it", "the episode is a striking example", and "continues to shape".
12. Do not repeat the same point in consecutive paragraphs. Vary sentence openings and keep the tone calm, direct and natural.
13. Plain text only: no markdown, no asterisks, no headings, no bullet points.
14. Do not include word counts, character counts, citations lists, inline citation labels, or meta information at the end.
15. Never write bracketed source labels such as [Source: Chester Standard], [Source: BBC], or similar.
16. Every paragraph must introduce a new verified fact. Remove paragraphs that merely repeat, generalise, speculate, praise, inspire or conclude.
17. End with the final known fact or practical next step. Do not add an essay-style summary, moral or inspirational conclusion.

NEVER fabricate details to make the article longer.
NEVER include a claim unless it is supported by the source URL, the supplied summary, or reputable corroborating sources."""
                        },
                        {
                            "role": "user",
                            "content": f"""Rewrite this as a Cheshire Today news article using verified facts only.

Headline: {title}
Summary: {summary}
Source: {source}
Source URL: {source_url}

Before writing, identify the verified facts from the source URL, especially:
- exact business or venue name
- exact location
- who said what
- what happened
- when it happened
- whether any police, council, parents, residents or customers are actually mentioned

Use only verified details in the finished article. If the source URL is unavailable, paywalled or too thin, rely only on the headline and summary and avoid all unsupported specifics.

Write clean plain text paragraphs. Aim for a useful article, but do not force 2000+ characters by inventing details. A shorter accurate article is better than a longer inaccurate one. Do not add word count at the end:"""
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.2,
                    "return_citations": True,
                    "search_recency_filter": "week"
                }
                
                response = await client.post(
                    PERPLEXITY_API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=90.0  # Longer timeout for long-form content generation
                )
                
                if response.status_code != 200:
                    logger.error(f"Perplexity content generation error: {response.status_code}")
                    return ""  # No fallback articles: caller must skip failed rewrites
                
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                
                # Clean up content - remove markdown formatting and word counts
                import re
                content = re.sub(r'\[\d+\]', '', content)
                content = re.sub(r'\[\s*Source\s*:[^\]]+\]', '', content, flags=re.IGNORECASE)  # Remove citation brackets [1], [2]
                content = re.sub(r'\*+', '', content)  # Remove asterisks
                content = re.sub(r'#+\s*', '', content)  # Remove markdown headers
                content = re.sub(r'_+', '', content)  # Remove underscores (italic markdown)
                content = re.sub(r'\s*\(Word count:?\s*\d+\)', '', content, flags=re.IGNORECASE)  # Remove word count
                content = re.sub(r'\s*\(Character count:?\s*\d+\)', '', content, flags=re.IGNORECASE)  # Remove character count
                content = re.sub(r'\s*Word count:?\s*\d+\.?\s*$', '', content, flags=re.IGNORECASE)  # Remove trailing word count
                content = re.sub(r'[ \t]+', ' ', content).strip()  # Clean up extra spaces
                
                # CRITICAL: Detect and reject refusal messages from Perplexity
                refusal_indicators = [
                    "I cannot write",
                    "I can't write",
                    "cannot fabricate",
                    "can't fabricate",
                    "no source to support",
                    "no evidence of",
                    "As Perplexity",
                    "my core responsibility",
                    "I'd be happy to",
                    "If you'd like me to",
                    "I could create a news article covering",
                    "maintain strict accuracy",
                    "ground every claim",
                    "These are real, documented events",
                    "Alternatively, if you have"
                ]
                
                content_lower = content.lower()
                is_refusal = any(indicator.lower() in content_lower for indicator in refusal_indicators)
                
                if is_refusal:
                    logger.warning(f"Perplexity refused the first rewrite for: {title[:40]}... Retrying once.")
                    content = ""

                # Perplexity's responsibility is to return any usable factual rewrite.
                # Publication length and editorial quality decisions belong in server.py.
                if content:
                    logger.info(f"Generated {len(content)} chars of content for: {title[:40]}...")
                    return content

                logger.warning(f"Perplexity returned empty content for: {title[:40]}... Retrying once.")

                retry_payload = {
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a senior UK local and business news writer for Cheshire Today. Write a clear, natural, publication-quality article in British English using plain text only. Lead with the concrete fact, use short paragraphs, avoid generic AI-explainer phrases, avoid repetition, and keep the tone calm, human and practical. Use only verified facts supported by the source material. Write to the natural length supported by the available facts; a concise accurate article is better than a padded one. Every paragraph must add new information. Never include bracketed source labels such as [Source: ...]. Do not add an essay-style conclusion. Do not refuse, do not explain limitations, and do not include headings, bullet points, markdown, or meta commentary."
                        },
                        {
                            "role": "user",
                            "content": f"Write a detailed Cheshire Today article based on this story. Headline: {title}\nSummary: {summary}\nSource: {source}\nSource URL: {source_url}\nUse the source URL as the primary reference when available. Add only relevant, supported context. Avoid generic AI-style phrases including this matters because, a notable step, fresh attention, underlines and on the face of it. Return plain text paragraphs only."
                        }
                    ],
                    "max_tokens": 2400,
                    "temperature": 0.4,
                    "return_citations": True,
                    "search_recency_filter": "week"
                }

                retry_response = await client.post(
                    PERPLEXITY_API_URL,
                    headers=self._get_headers(),
                    json=retry_payload,
                    timeout=90.0
                )

                if retry_response.status_code == 200:
                    retry_data = retry_response.json()
                    retry_content = retry_data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    import re
                    retry_content = re.sub(r'\[\d+\]', '', retry_content)
                    retry_content = re.sub(r'\[\s*Source\s*:[^\]]+\]', '', retry_content, flags=re.IGNORECASE)
                    retry_content = re.sub(r'\*+', '', retry_content)
                    retry_content = re.sub(r'#+\s*', '', retry_content)
                    retry_content = re.sub(r'_+', '', retry_content)
                    retry_content = re.sub(r'\s*\(Word count:?\s*\d+\)', '', retry_content, flags=re.IGNORECASE)
                    retry_content = re.sub(r'\s*\(Character count:?\s*\d+\)', '', retry_content, flags=re.IGNORECASE)
                    retry_content = re.sub(r'\s*Word count:?\s*\d+\.?\s*$', '', retry_content, flags=re.IGNORECASE)
                    retry_content = re.sub(r'[ \t]+', ' ', retry_content).strip()

                    retry_lower = retry_content.lower()
                    retry_refusal = any(indicator.lower() in retry_lower for indicator in refusal_indicators)

                    if not retry_refusal and retry_content:
                        logger.info(f"Retry generated {len(retry_content)} chars for: {title[:40]}...")
                        return retry_content

                logger.warning(f"Retry returned no usable content for: {title[:40]}... Returning empty skip signal.")
                return ""  # No fallback articles: caller must skip weak/failed rewrites
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout generating content for: {title[:40]}...")
            return ""
        except Exception as e:
            logger.error(f"Error generating article content: {str(e)}")
            return ""

    async def research_article_facts(
        self,
        title: str,
        summary: str = "",
        source: str = "",
        source_url: str = "",
        publisher_content: str = "",
    ) -> Dict[str, Any]:
        """Research an article for the admin OpenAI draft workflow.

        Returns a structured factual pack only. It does not write, save,
        publish, archive or modify an article.
        """
        import asyncio
        import json
        import re
        from urllib.parse import urlparse

        if not self.api_key:
            logger.error("Perplexity API key not configured for article fact research")
            return {}

        if not ai_call_allowed(0.05):
            logger.warning("Perplexity budget guard blocked article fact research")
            return {}

        system_prompt = """You are a meticulous UK news researcher working for Cheshire Today.

Research the supplied story using the Source URL as the primary reference and reputable corroborating sources where necessary.

Return valid JSON only.

Accuracy rules:
- Do not write a finished news article.
- Do not invent or infer missing details.
- Do not treat the supplied summary as automatically accurate.
- Verify names, roles, dates, locations, organisations, figures and quotations.
- For people, provide the complete published name and complete role.
- Do not mark surname-only, given-name-only, honorific-plus-given-name, inferred or reconstructed identities as verified.
- Put incomplete or conflicting person identities in uncertain_or_unverified.
- For awards, legal decisions, regulatory action, appointments and similar staged processes, determine the exact current status from the responsible official body.
- Treat entered, nominated, commended, shortlisted, finalist and winner as distinct statuses. Never substitute one status for another.
- Use the exact terminology published by the official organiser or responsible authority.
- If the official organiser says finalists will be announced later, do not describe the current status as shortlisted or finalist unless the organiser explicitly does so.
- Never use slash-separated or combined alternatives such as commended/shortlisted or nominated/finalist in verified fields.
- If the precise status cannot be resolved, place the claim only in uncertain_or_unverified and explain the conflict in contradictions.
- Include a factual claim only when it is supported by a directly relevant source.
- Keep direct quotations only when their exact wording and speaker are verified.
- Identify contradictions, uncertainty or details that could not be verified.
- For award, legal, regulatory or official status, give priority to the responsible official body over publisher headlines, social posts or promotional wording.
- For an award-stage story, populate official_status, official_source_name and official_source_url only when a direct page from the responsible award organiser confirms the exact subject, award and current stage.
- A newspaper, social-media post, search result, directory or unrelated awards website is not an official-status source.
- Leave the official-status fields empty when that direct official confirmation cannot be found.
- Exclude sources concerning a different year, country, organisation, institution or unrelated event.
- Include only source URLs that directly support or contradict the story being researched.
- Do not include generic background merely to make the fact pack longer.
- Do not include markdown, citation brackets or commentary outside the JSON.

Return exactly this JSON structure:
{
  "verified_headline_facts": ["fact"],
  "verified_facts": ["fact"],
  "names_and_roles": [
    {"name": "complete published name", "role": "complete role", "verified": true, "source_url": "https://supporting-source.example"}
  ],
  "dates": ["date and what it relates to"],
  "locations": ["verified place"],
  "figures": ["verified number and context"],
  "quotations": [
    {"quote": "exact verified quotation", "speaker": "speaker"}
  ],
  "practical_information": ["deadline, action, contact or next step"],
  "uncertain_or_unverified": ["claim that could not be confirmed"],
  "contradictions": ["meaningful disagreement between sources"],
  "official_status": "exact official award status or empty string",
  "official_source_name": "responsible official body or empty string",
  "official_source_url": "direct official confirmation URL or empty string",
  "source_urls": ["https://source.example"],
  "research_summary": "brief factual overview for the editor"
}
"""

        user_prompt = f"""Research this story for a Cheshire Today admin rewrite.

Headline: {title}
Existing summary: {summary}
Named source: {source}
Primary source URL: {source_url}

Check the primary source first, then locate the responsible official organiser, authority or original record where one exists. Resolve the exact current status using the official terminology. Use only sources directly relevant to this specific story, organisation and year. Return the structured fact pack and nothing else."""

        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 2200,
            "temperature": 0.1,
            "return_citations": True,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    PERPLEXITY_API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=90.0,
                )

            if response.status_code != 200:
                logger.error(
                    f"Perplexity article fact research error: "
                    f"{response.status_code} - {response.text[:500]}"
                )
                return {}

            data = response.json()
            raw = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            if not raw:
                return {}

            if "```" in raw:
                match = re.search(r"\{.*\}", raw, flags=re.S)
                if match:
                    raw = match.group(0)

            fact_pack = json.loads(raw)

            if not isinstance(fact_pack, dict):
                return {}

            citations = data.get("citations") or []
            existing_urls = fact_pack.get("source_urls")
            if not isinstance(existing_urls, list):
                existing_urls = []

            for citation in citations:
                url = str(citation or "").strip()
                if url and url not in existing_urls:
                    existing_urls.append(url)

            existing_urls = list(dict.fromkeys(
                str(url or "").strip()
                for url in existing_urls
                if str(url or "").strip()
            ))
            fact_pack["source_urls"] = existing_urls
            fact_pack = validate_fact_pack_people(
                fact_pack,
                publisher_content=publisher_content,
                publisher_url=source_url,
            )

            status_aliases = {
                "entered": "entered",
                "entrant": "entered",
                "nominated": "nominated",
                "nominee": "nominated",
                "nomination": "nominated",
                "commended": "commended",
                "commendation": "commended",
                "shortlist": "shortlisted",
                "shortlisted": "shortlisted",
                "finalist": "finalist",
                "finalists": "finalist",
                "winner": "winner",
                "winners": "winner",
                "won": "winner",
                "winning": "winner",
            }
            status_terms = tuple(dict.fromkeys(status_aliases.values()))
            status_word_pattern = "|".join(
                sorted(
                    (re.escape(term) for term in status_aliases),
                    key=len,
                    reverse=True,
                )
            )
            status_pattern = re.compile(
                r"\b(" + status_word_pattern + r")\b",
                flags=re.IGNORECASE,
            )
            ambiguous_status_pattern = re.compile(
                r"\b(" + status_word_pattern + r")\b"
                r"\s*(?:/|or)\s*"
                r"\b(" + status_word_pattern + r")\b",
                flags=re.IGNORECASE,
            )

            story_text = f"{title} {summary}".lower()
            award_status_keywords = (
                "award",
                "awards",
            )
            award_status_story = (
                bool(status_pattern.search(story_text))
                or any(
                    keyword in story_text
                    for keyword in award_status_keywords
                )
            )

            def normalise_host(url: str) -> str:
                host = urlparse(str(url or "")).netloc.lower()
                return host[4:] if host.startswith("www.") else host

            official_status_raw = str(
                fact_pack.get("official_status") or ""
            ).strip().lower()
            official_status = status_aliases.get(
                official_status_raw,
                official_status_raw,
            )
            official_source_name = str(
                fact_pack.get("official_source_name") or ""
            ).strip()
            official_source_url = str(
                fact_pack.get("official_source_url") or ""
            ).strip()

            primary_host = normalise_host(source_url)
            official_host = normalise_host(official_source_url)
            blocked_official_hosts = {
                "facebook.com",
                "instagram.com",
                "linkedin.com",
                "tiktok.com",
                "twitter.com",
                "x.com",
                "youtube.com",
            }

            def host_is_blocked(host: str) -> bool:
                return any(
                    host == blocked
                    or host.endswith("." + blocked)
                    for blocked in blocked_official_hosts
                )

            def normalise_url(url: str) -> str:
                return str(url or "").strip().rstrip("/")

            listed_urls = {
                normalise_url(url)
                for url in existing_urls
                if normalise_url(url)
            }

            official_url_listed = (
                normalise_url(official_source_url) in listed_urls
            )
            official_candidate_valid = (
                official_status in status_terms
                and bool(official_source_name)
                and official_source_url.startswith(("http://", "https://"))
                and official_url_listed
                and bool(official_host)
                and official_host != primary_host
                and not host_is_blocked(official_host)
            )

            subject_names = []
            names_and_roles = fact_pack.get("names_and_roles")
            if isinstance(names_and_roles, list):
                for item in names_and_roles:
                    if not isinstance(item, dict):
                        continue
                    if item.get("verified") is not True:
                        continue

                    name = str(item.get("name") or "").strip()
                    if len(name) < 4:
                        continue

                    subject_names.append(name)
                    without_the = re.sub(
                        r"^the\s+",
                        "",
                        name,
                        flags=re.IGNORECASE,
                    ).strip()
                    if without_the and without_the != name:
                        subject_names.append(without_the)

            official_page_fetched = False
            official_subject_confirmed = False
            official_status_confirmed = False
            official_validation_error = ""

            if official_candidate_valid and subject_names:
                try:
                    from app.simple_scraper import scrape_article

                    official_result = await asyncio.to_thread(
                        scrape_article,
                        official_source_url,
                        20,
                    )

                    official_text = " ".join(
                        [
                            str(official_result.get("title") or ""),
                            str(official_result.get("content") or ""),
                        ]
                    )
                    official_text_normalised = re.sub(
                        r"\s+",
                        " ",
                        official_text,
                    ).strip().lower()

                    official_page_fetched = (
                        official_result.get("ok") is True
                        and bool(official_text_normalised)
                    )

                    official_status_words = [
                        alias
                        for alias, canonical in status_aliases.items()
                        if canonical == official_status
                    ]
                    official_status_page_pattern = re.compile(
                        r"\b(?:"
                        + "|".join(
                            re.escape(word)
                            for word in official_status_words
                        )
                        + r")\b",
                        flags=re.IGNORECASE,
                    )

                    subject_windows = []
                    if official_page_fetched:
                        for name in subject_names:
                            subject_text = re.sub(
                                r"\s+",
                                " ",
                                name,
                            ).strip().lower()

                            if not subject_text:
                                continue

                            for subject_match in re.finditer(
                                re.escape(subject_text),
                                official_text_normalised,
                            ):
                                window_start = max(
                                    0,
                                    subject_match.start() - 500,
                                )
                                window_end = min(
                                    len(official_text_normalised),
                                    subject_match.end() + 500,
                                )
                                subject_windows.append(
                                    official_text_normalised[
                                        window_start:window_end
                                    ]
                                )

                    official_subject_confirmed = bool(subject_windows)
                    official_status_confirmed = any(
                        official_status_page_pattern.search(window)
                        for window in subject_windows
                    )

                    if not official_page_fetched:
                        official_validation_error = str(
                            official_result.get("error")
                            or "Official page could not be reliably extracted"
                        )
                    elif not official_subject_confirmed:
                        official_validation_error = (
                            "The declared official page did not contain the "
                            "verified subject name"
                        )
                    elif not official_status_confirmed:
                        official_validation_error = (
                            "The declared status was not found near the subject "
                            "on the official page"
                        )

                except Exception as official_error:
                    official_validation_error = str(official_error)[:200]

            elif official_candidate_valid and not subject_names:
                official_validation_error = (
                    "No verified subject name was supplied for official-page "
                    "validation"
                )

            official_status_verified = (
                official_candidate_valid
                and official_page_fetched
                and official_subject_confirmed
                and official_status_confirmed
            )

            fact_pack["official_status_verified"] = official_status_verified
            fact_pack["official_status_validation"] = {
                "source_url_listed": official_url_listed,
                "source_host_distinct_from_publisher": (
                    bool(official_host)
                    and official_host != primary_host
                ),
                "page_fetched": official_page_fetched,
                "subject_confirmed": official_subject_confirmed,
                "status_confirmed": official_status_confirmed,
                "error": official_validation_error,
            }

            uncertain = fact_pack.get("uncertain_or_unverified")
            if not isinstance(uncertain, list):
                uncertain = []

            contradictions = fact_pack.get("contradictions")
            if not isinstance(contradictions, list):
                contradictions = []

            for field in ("verified_headline_facts", "verified_facts"):
                values = fact_pack.get(field)
                if not isinstance(values, list):
                    fact_pack[field] = []
                    continue

                verified_values = []
                for value in values:
                    value_text = str(value or "").strip()
                    status_matches = {
                        status_aliases.get(match.lower(), match.lower())
                        for match in status_pattern.findall(value_text)
                    }

                    reject_reason = ""

                    if ambiguous_status_pattern.search(value_text):
                        reject_reason = "ambiguous status wording"
                    elif (
                        award_status_story
                        and status_matches
                        and not official_status_verified
                    ):
                        reject_reason = (
                            "status was not confirmed by a direct official source"
                        )
                    elif (
                        official_status_verified
                        and status_matches
                        and official_status not in status_matches
                    ):
                        reject_reason = (
                            "status conflicts with the official confirmed status"
                        )

                    if reject_reason:
                        uncertain.append(
                            f"Unverified award-status claim ({reject_reason}): "
                            f"{value_text}"
                        )
                        continue

                    verified_values.append(value)

                fact_pack[field] = verified_values

            if award_status_story and not official_status_verified:
                dates = fact_pack.get("dates")
                if isinstance(dates, list):
                    for value in dates:
                        value_text = str(value or "").strip()
                        if value_text:
                            uncertain.append(
                                "Award-stage date not independently "
                                f"confirmed by an official source: {value_text}"
                            )
                fact_pack["dates"] = []

                contradictions.append(
                    "The research did not provide a directly cited official "
                    "source confirming the exact current status. Publisher or "
                    "third-party status wording must not be treated as verified."
                )
                fact_pack["research_summary"] = (
                    "The subject and location may be supported, but the exact "
                    "award status was not independently "
                    "confirmed by a directly cited official source."
                )

            fact_pack["uncertain_or_unverified"] = list(dict.fromkeys(uncertain))
            fact_pack["contradictions"] = list(dict.fromkeys(contradictions))
            return fact_pack

        except json.JSONDecodeError:
            logger.warning(
                f"Perplexity returned invalid fact-pack JSON for: {title[:60]}"
            )
            return {}
        except httpx.TimeoutException:
            logger.error(
                f"Perplexity article fact research timed out for: {title[:60]}"
            )
            return {}
        except Exception as error:
            logger.error(
                f"Perplexity article fact research failed for "
                f"{title[:60]}: {str(error)}"
            )
            return {}

    async def search_trending_cheshire_topics(self) -> List[str]:
        """
        Get trending topics in Cheshire for news generation
        Cost-optimized: Returns topic keywords only
        """
        if not self.api_key:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a news editor. Return ONLY a JSON array of 5 trending news topics in Cheshire, UK. Format: [\"topic1\", \"topic2\", ...]"
                        },
                        {
                            "role": "user",
                            "content": "What are the top 5 trending news topics in Cheshire, UK right now?"
                        }
                    ],
                    "max_tokens": 256,
                    "temperature": 0.1,
                    "search_recency_filter": "day"
                }
                
                response = await client.post(
                    PERPLEXITY_API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # Parse topics
                import json
                try:
                    if '```' in content:
                        json_start = content.find('[')
                        json_end = content.rfind(']') + 1
                        content = content[json_start:json_end]
                    topics = json.loads(content)
                    if isinstance(topics, list):
                        return topics[:5]
                except:
                    pass
                
                return []
                
        except Exception as e:
            logger.error(f"Error fetching trending topics: {str(e)}")
            return []

    async def generate_image_search_query(self, title: str, content: str, category: str) -> str:
        """
        Generate a smart, specific image search query for an article.
        This ensures images match the actual article content.
        
        Cost: ~$0.005 per call
        
        Args:
            title: Article title
            content: Article content/summary
            category: Article category
            
        Returns:
            A specific image search query string
        """
        if not self.api_key:
            logger.error("Perplexity API key not configured")
            return ""
        
        try:
            async with httpx.AsyncClient() as client:
                # Truncate content to save tokens
                short_content = content[:300] if content else ""
                
                payload = {
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are an image search expert. Given a news article, generate a SHORT, SPECIFIC image search query (3-5 words) that would find a relevant stock photo.

Rules:
- Focus on the MAIN SUBJECT of the article
- Be SPECIFIC (not generic like "news" or "UK")
- For people stories: describe the situation, not the person
- For location stories: include the type of place
- For health: include medical imagery keywords
- For sports: include the specific sport
- Return ONLY the search query, nothing else."""
                        },
                        {
                            "role": "user",
                            "content": f"Title: {title}\nCategory: {category}\nContent: {short_content}\n\nGenerate image search query:"
                        }
                    ],
                    "max_tokens": 50,
                    "temperature": 0.1
                }
                
                response = await client.post(
                    PERPLEXITY_API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Perplexity image query error: {response.status_code}")
                    return ""
                
                data = response.json()
                query = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                
                # Clean up the query
                query = query.replace('"', '').replace("'", "").strip()
                
                # Limit length
                if len(query) > 50:
                    query = ' '.join(query.split()[:5])
                
                logger.info(f"Generated image query for '{title[:30]}...': '{query}'")
                return query
                
        except Exception as e:
            logger.error(f"Error generating image query: {str(e)}")
            return ""


# Global instance
perplexity_service = PerplexityService()
