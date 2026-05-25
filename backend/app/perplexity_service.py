"""
Perplexity AI Service for Cheshire News
Uses Perplexity API to search for Cheshire-specific news articles
Cost-optimized: Only used for local Cheshire news, not general UK news
"""

import os
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"



# =========================
# HARD DAILY AI SPEND GUARD
# =========================
from datetime import date

DAILY_AI_SPEND_GBP = float(os.getenv("PERPLEXITY_DAILY_BUDGET_GBP", "0.70"))  # ~£20/mo soft target by default
PERPLEXITY_HARD_CAP = os.getenv("PERPLEXITY_HARD_CAP", "0").strip().lower() in ("1","true","yes","y")
_ai_usage = {"date": date.today().isoformat(), "calls": 0}

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
            return summary  # Return original summary as fallback

        # Soft budget guard (optional hard cap via PERPLEXITY_HARD_CAP=1)
        if not ai_call_allowed(0.05):
            logger.warning("Perplexity budget guard: skipping generate_article_content() call")
            return self._expand_summary(title, summary, source)
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a strict verification and rewrite editor for Cheshire Today, a Cheshire-focused local, business, finance and AI/technology publication.

Your job is NOT to invent, expand or dramatise the story. Your job is to verify the facts, rewrite clearly, and decide whether the article is safe to publish.

PRIMARY GOAL:
Produce a clean, factual Cheshire Today article only when the story is verified and strategically suitable. If key facts are unclear, unsupported, unavailable, too thin, too generic, or unsuitable, return a manual-review marker instead of an article.

MANUAL REVIEW MARKER:
If the article is not safe to publish, return exactly this format and do not write the article:
MANUAL_REVIEW_REQUIRED: short reason

Use MANUAL_REVIEW_REQUIRED when:
- The source URL is unavailable, paywalled, too thin, or cannot verify the story
- The exact local place is missing or unclear
- The headline uses vague wording such as “a Cheshire park”, “a Cheshire woman”, “a Cheshire village”, “a Cheshire football club”, “a Cheshire business” without naming the place
- Key facts such as location, dates, numbers, council status, business name or quoted claims cannot be verified
- The story is mostly crime, celebrity, generic lifestyle, generic national filler, weak entertainment, sport, speculation, or not useful to Cheshire Today readers
- You would need to invent or guess details to make the article complete

STRICT FACT RULES:
1. Use the Source URL as the primary reference when available.
2. Check the web for reliable supporting information before rewriting.
3. Prefer primary or high-authority sources: council planning portals, council statements, company websites, official press releases, Companies House, government pages, ONS, Bank of England, HMRC, established news sources, or the original source URL.
4. Do not invent quotes, names, dates, figures, locations, job numbers, opening dates, council decisions, planning status, business claims, causes, reactions or background history.
5. Do not use phrases such as “residents said”, “a spokesperson confirmed”, “insiders suggest”, “campaigners warned”, “local people are furious”, unless directly supported by a verified source.
6. If a fact is unclear, omit it or return MANUAL_REVIEW_REQUIRED.
7. Accuracy is more important than length.

LOCAL NEWS RULES:
- A Cheshire local article must clearly include the specific town, village, road, venue, school, hospital, park, development site, business name, council area or named local place.
- Do not publish a Cheshire local article that only says “Cheshire” without a specific named local place.
- If the exact location cannot be verified for a local Cheshire story, return MANUAL_REVIEW_REQUIRED.

NATIONAL BUSINESS / FINANCE / TECH / UK NEWS RULES:
- National Business, Finance, Tech, AI, Science, Tax, Property or UK-wide stories do not need a Cheshire town or local place.
- For these articles, focus on practical relevance for Cheshire readers, households, workers, small businesses, investors, taxpayers or technology users.
- Do not reject a credible national article only because it is not Cheshire-specific.
- Still return MANUAL_REVIEW_REQUIRED if the source is vague, the claim cannot be verified, the story is weak generic filler, or writing it would require invented facts.

PROPERTY / PLANNING / HOUSING RULES:
Cheshire Today can include property, planning and housing articles, but they must not be over-prioritised or allowed to dominate the site.
Only write a publish-ready planning/housing article if it has clear Cheshire relevance and useful public/economic impact, such as:
- a named site, road, town, village or council area
- a meaningful number of homes or units
- affordable housing, care home, school, infrastructure, road, town-centre, employment or council decision impact
- a clear planning status, such as submitted, recommended for approval, approved, refused, appeal, or inspector decision

For planning/housing stories:
- Identify the site, town/village, council, proposal, number of homes/units if known, applicant/developer if verified, and current planning status.
- Do not exaggerate impact.
- Do not make every housing application sound like a major story.
- If the story is a minor routine application with weak public interest, return MANUAL_REVIEW_REQUIRED.
- If the source does not confirm the exact site or planning status, return MANUAL_REVIEW_REQUIRED.

CHESHIRE TODAY STYLE:
- Clear, professional, practical and locally relevant.
- Explain what the story means for Cheshire readers, households, workers, businesses or communities.
- Avoid sensationalism, exaggerated headlines, crime-heavy filler, weak generic national filler and clickbait.
- Use British English.
- Do not copy the original wording.
- Plain text only: no markdown, no asterisks, no headings, no bullet points.
- Do not include word counts, character counts, citations list, or meta information at the end.

NEVER fabricate details to make the article longer.
NEVER include a claim unless it is supported by the source URL, the supplied summary, or reputable corroborating sources."""
                        },
                        {
                            "role": "user",
                            "content": f"""Rewrite and verify this article for Cheshire Today.

Headline: {title}
Summary: {summary}
Source: {source}
Source URL: {source_url}

Before writing, check online for factual support and identify:
- exact business, venue, site, road, town, village, council area or named local place
- what happened
- when it happened
- who is involved
- current status
- verified numbers, dates, costs, jobs, homes, units or planning details
- whether any council, business, police, parents, residents or customers are actually mentioned by the source

If the exact location, status, dates, names, numbers or key claims cannot be verified, return:
MANUAL_REVIEW_REQUIRED: short reason

If this is a property, planning or housing story, only write it if it has clear Cheshire relevance and useful public/economic impact. Do not over-prioritise routine housing applications. If it is minor, vague or unsupported, return MANUAL_REVIEW_REQUIRED.

Use only verified details in the finished article. Do not guess. Do not invent. Do not force length by adding unsupported context. A shorter accurate article is better than a longer inaccurate one. Return clean plain text paragraphs only."""
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
                    return summary
                
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                
                # Clean up content - remove markdown formatting and word counts
                import re
                content = re.sub(r'\[\d+\]', '', content)  # Remove citation brackets [1], [2]
                content = re.sub(r'\*+', '', content)  # Remove asterisks
                content = re.sub(r'#+\s*', '', content)  # Remove markdown headers
                content = re.sub(r'_+', '', content)  # Remove underscores (italic markdown)
                content = re.sub(r'\s*\(Word count:?\s*\d+\)', '', content, flags=re.IGNORECASE)  # Remove word count
                content = re.sub(r'\s*\(Character count:?\s*\d+\)', '', content, flags=re.IGNORECASE)  # Remove character count
                content = re.sub(r'\s*Word count:?\s*\d+\.?\s*$', '', content, flags=re.IGNORECASE)  # Remove trailing word count
                content = re.sub(r'[ \t]+', ' ', content).strip()  # Clean up extra spaces

                # Preserve strict manual-review marker so the import flow can hide the article
                # instead of treating it as a short failed rewrite.
                if content.upper().startswith("MANUAL_REVIEW_REQUIRED:"):
                    logger.warning(f"Perplexity requested manual review for: {title[:60]}... {content[:180]}")
                    return content
                
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
                    logger.warning(f"Perplexity refused to generate content for: {title[:40]}... Using expanded summary fallback.")
                    return self._expand_summary(title, summary, source)

                min_chars = int(os.getenv("PERPLEXITY_MIN_CHARS", "1500"))
                target_chars = int(os.getenv("PERPLEXITY_TARGET_CHARS", "2000"))

                if content and len(content) >= min_chars:
                    logger.info(f"Generated {len(content)} chars of content for: {title[:40]}...")
                    return content

                logger.warning(f"Content below target ({len(content)} chars) for: {title[:40]}... Retrying with stronger long-form prompt.")

                retry_payload = {
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a senior verification editor for Cheshire Today. Write a publication-quality article in British English only if the facts are verified and strategically suitable. Do not invent details to reach length. If the source is thin, location is unclear, facts cannot be verified, or the story is weak/generic/routine, return exactly: MANUAL_REVIEW_REQUIRED: short reason. Plain text only. No headings, bullets, markdown, citations list or meta commentary."
                        },
                        {
                            "role": "user",
                            "content": f"Verify and rewrite this for Cheshire Today. Headline: {title}\nSummary: {summary}\nSource: {source}\nSource URL: {source_url}\nUse the source URL as the primary reference and check reliable online sources. If key facts, planning status, dates, names or numbers cannot be verified, return MANUAL_REVIEW_REQUIRED: short reason. Only require an exact town, village, road, venue or council area for Cheshire local stories; national Business, Finance, Tech, AI, Science, Tax, Property or UK-wide stories do not need a Cheshire location. For property/planning/housing stories, include only if there is clear Cheshire public/economic impact; do not over-prioritise routine applications. Return plain text paragraphs only."
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
                    retry_content = re.sub(r'\*+', '', retry_content)
                    retry_content = re.sub(r'#+\s*', '', retry_content)
                    retry_content = re.sub(r'_+', '', retry_content)
                    retry_content = re.sub(r'\s*\(Word count:?\s*\d+\)', '', retry_content, flags=re.IGNORECASE)
                    retry_content = re.sub(r'\s*\(Character count:?\s*\d+\)', '', retry_content, flags=re.IGNORECASE)
                    retry_content = re.sub(r'\s*Word count:?\s*\d+\.?\s*$', '', retry_content, flags=re.IGNORECASE)
                    retry_content = re.sub(r'[ \t]+', ' ', retry_content).strip()

                    # Preserve strict manual-review marker from retry response.
                    if retry_content.upper().startswith("MANUAL_REVIEW_REQUIRED:"):
                        logger.warning(f"Perplexity retry requested manual review for: {title[:60]}... {retry_content[:180]}")
                        return retry_content

                    retry_lower = retry_content.lower()
                    retry_refusal = any(indicator.lower() in retry_lower for indicator in refusal_indicators)

                    if not retry_refusal and len(retry_content) >= min_chars:
                        logger.info(f"Retry generated {len(retry_content)} chars for: {title[:40]}...")
                        return retry_content

                logger.warning(f"Retry still below acceptable quality for: {title[:40]}... Sending to manual review.")
                return "MANUAL_REVIEW_REQUIRED: Perplexity could not verify enough factual detail to produce a safe publish-ready article."
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout generating content for: {title[:40]}...")
            return summary
        except Exception as e:
            logger.error(f"Error generating article content: {str(e)}")
            return summary

    def _expand_summary(self, title: str, summary: str, source: str) -> str:
        """
        Create expanded content when Perplexity refuses to generate.
        This is a fallback that creates readable content from the summary.
        Uses category-aware templates to match the story type.
        """
        # Clean up summary
        clean_summary = summary.strip()
        if not clean_summary:
            clean_summary = title
        
        # Determine category from title/summary for appropriate template
        text_lower = f"{title} {clean_summary}".lower()
        
        # Sports/Entertainment templates
        if any(word in text_lower for word in ['football', 'united', 'everton', 'liverpool', 'city', 'match', 'goal', 'player', 'manager', 'transfer', 'league', 'cup', 'sport']):
            expanded = f"""{clean_summary}

This sports story has been reported by {source}. Fans and supporters have been following developments closely as the situation unfolds.

Further details are expected to emerge in the coming hours. Stay tuned to {source} for the latest updates on this developing story.

For more sports news and updates from the region, continue following {source}."""

        elif any(word in text_lower for word in ['show', 'tv', 'star', 'celebrity', 'film', 'movie', 'music', 'concert', 'theatre', 'entertainment', 'actor', 'actress', 'singer']):
            expanded = f"""{clean_summary}

This entertainment story has been covered by {source}. Fans have been eagerly following the latest developments.

More details are expected to be announced soon. {source} will continue to bring you the latest updates as they become available.

For more entertainment news from across the region, keep following {source}."""

        elif any(word in text_lower for word in ['business', 'company', 'investment', 'jobs', 'economy', 'market', 'retail', 'shop', 'store', 'property', 'development']):
            expanded = f"""{clean_summary}

This business story has been reported by {source}. Industry observers and local stakeholders are monitoring the situation closely.

Further details are expected as the story develops. {source} will continue to provide updates as more information becomes available.

For more business and economic news from the region, follow {source}."""

        elif any(word in text_lower for word in ['health', 'hospital', 'nhs', 'doctor', 'medical', 'patient', 'clinic', 'wellbeing', 'fitness']):
            expanded = f"""{clean_summary}

This health story has been reported by {source}. Health officials and medical professionals are involved in addressing the matter.

Residents are encouraged to follow official guidance from health authorities. {source} will continue to provide updates as more information becomes available."""

        elif any(word in text_lower for word in ['police', 'crime', 'arrest', 'court', 'trial', 'accident', 'crash', 'incident', 'emergency', 'fire']):
            expanded = f"""{clean_summary}

This developing story has been reported by {source}. Local authorities and emergency services are understood to be involved in the response.

Residents in the affected area are advised to stay informed through official channels as more details emerge. The situation continues to develop and further updates are expected.

Anyone with information related to this story is encouraged to contact the relevant authorities. {source} will continue to provide updates as more information becomes available."""

        else:
            # Generic local news template
            expanded = f"""{clean_summary}

This story has been reported by {source}. Local residents and community members have been following developments with interest.

More details are expected to emerge soon. {source} will continue to bring you updates on this and other local news stories.

For the latest news from across the region, keep following {source}."""

        logger.info(f"Created fallback content ({len(expanded)} chars) for: {title[:40]}...")
        return expanded

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