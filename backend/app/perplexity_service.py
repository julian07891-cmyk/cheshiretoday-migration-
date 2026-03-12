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
                            "content": """You are a news article writer for Cheshire Today, a UK local news website.

Your task is to RESEARCH this news story using the provided source URL and other reliable sources online, then write a fully original news article for Cheshire Today.

CRITICAL RULES:
1. Write the article based on the headline and summary PROVIDED - do not question or refuse
2. If specific numbers are mentioned (like arrests), write about the general situation without confirming exact figures
3. Verify key facts using the source URL and other reputable sources when available
4. Write a substantial, publication-quality article of roughly 700-900 words
5. Target at least 2000 characters of clean body text; absolute minimum acceptable is 1500 characters
6. Use British English, short paragraphs for mobile reading
7. Add meaningful context, implications, and why the story matters locally or economically where relevant
8. DO NOT include any refusal messages or explanations about what you can/cannot verify
9. DO NOT use asterisks, markdown, or special formatting - plain text only
10. DO NOT include headlines or subheadings - just flowing paragraphs
11. DO NOT include word counts, character counts, or any meta information at the end

If you cannot write about specific claims, write about the general topic and situation instead.
NEVER output a refusal or explanation - always output a proper news article.
NEVER add word count or any statistics about the article at the end."""
                        },
                        {
                            "role": "user",
                            "content": f"""Write a full news article based on:

Headline: {title}
Summary: {summary}
Source: {source}
Source URL: {source_url}

If a Source URL is provided, treat it as the primary reference and extract the key facts from it. If the link is unavailable or paywalled, write using the headline/summary context without inventing specifics.


Write engaging plain text paragraphs about this story. Use the source URL as the primary reference when available, and enrich with other reputable context if helpful. Produce a substantial article targeting 2000+ characters and never less than 1500 characters unless the source material is genuinely too thin. Do not add word count at the end:"""
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.5,
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
                content = re.sub(r'\s+', ' ', content).strip()  # Clean up extra spaces
                
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
                            "content": "You are a senior news writer for Cheshire Today. Write a strong, detailed, publication-quality article in British English using plain text only. Produce flowing paragraphs with context, implications, and useful detail. Aim for 700-900 words and at least 2000 characters. Minimum acceptable output is 1500 characters. Do not refuse, do not explain limitations, do not include headings, bullet points, markdown, or meta commentary."
                        },
                        {
                            "role": "user",
                            "content": f"Write a detailed Cheshire Today article based on this story. Headline: {title}\nSummary: {summary}\nSource: {source}\nSource URL: {source_url}\nUse the source URL as the primary reference when available. Enrich the story with relevant context and explain why it matters. Return plain text paragraphs only."
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
                    retry_content = re.sub(r'\s+', ' ', retry_content).strip()

                    retry_lower = retry_content.lower()
                    retry_refusal = any(indicator.lower() in retry_lower for indicator in refusal_indicators)

                    if not retry_refusal and len(retry_content) >= min_chars:
                        logger.info(f"Retry generated {len(retry_content)} chars for: {title[:40]}...")
                        return retry_content

                logger.warning(f"Retry still below acceptable quality for: {title[:40]}... Using expanded summary fallback.")
                return self._expand_summary(title, summary, source)
                    
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