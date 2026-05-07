"""
Facebook Auto-Posting Service for Cheshire Today
Posts articles to Facebook Page using Graph API
Supports manual selection and scheduling of posts
"""
import os
import logging
import httpx
from datetime import datetime, timezone
from typing import List, Optional, Dict
from bson import ObjectId

logger = logging.getLogger(__name__)


class FacebookService:
    def __init__(self):
        self.user_access_token = os.environ.get('FACEBOOK_PAGE_ACCESS_TOKEN')
        self.page_id = os.environ.get('FACEBOOK_PAGE_ID')
        self.base_url = "https://graph.facebook.com/v18.0"
        # Always use production URL for Facebook posts
        self.site_url = 'https://cheshiretoday.co.uk'
        self._page_token = None  # Cached page token
    
    @property
    def is_configured(self) -> bool:
        """Check if Facebook credentials are configured"""
        return bool(self.user_access_token and self.page_id)
    
    async def get_page_token(self) -> Optional[str]:
        """Return a usable Page Access Token.

        FACEBOOK_PAGE_ACCESS_TOKEN may already be a Page token. If so, use it directly.
        If it is a User token, fall back to fetching the Page token from the Page edge.
        """
        if not self.user_access_token:
            return None

        # Render env tokens can be rotated; avoid reusing a stale cached token.
        self._page_token = None

        try:
            async with httpx.AsyncClient() as client:
                # First try to exchange the configured token for the actual Page token.
                response = await client.get(
                    f"{self.base_url}/{self.page_id}",
                    params={
                        "fields": "access_token",
                        "access_token": self.user_access_token
                    },
                    timeout=15.0
                )
                result = response.json()
                if "access_token" in result:
                    self._page_token = result["access_token"]
                    return self._page_token

                # Fallback: configured token may already be a Page token; verify direct access.
                direct_response = await client.get(
                    f"{self.base_url}/{self.page_id}",
                    params={
                        "fields": "id,name",
                        "access_token": self.user_access_token
                    },
                    timeout=15.0
                )
                direct_result = direct_response.json()
                if direct_result.get("id") == self.page_id and "error" not in direct_result:
                    self._page_token = self.user_access_token
                    return self._page_token
        except Exception as e:
            logger.error(f"Error getting page token: {e}")
        return None
    
    async def post_article(self, article: Dict) -> Dict:
        """
        Post a single article to Facebook Page ONLY (not personal profile)
        
        Args:
            article: Dict with id, title, content, image, source_url
            
        Returns:
            Dict with success status and post_id or error
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Facebook not configured. Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID"
            }
        
        # Get the PAGE token (not user token) to post only to page
        page_token = await self.get_page_token()
        if not page_token:
            return {
                "success": False,
                "error": "Could not get Page Access Token"
            }
        
        try:
            # Get article details
            title = article.get('title', 'Latest News')
            source = article.get('source', '')
            source_url = article.get('source_url', '')
            article_image = article.get('image', '')
            article_id = article.get('id', '')
            category = article.get('category', '')
            
            # Generate hashtags based on content
            hashtags = self._generate_hashtags(title, category, source)
            
            # Create a URL-safe search query from the title for fallback matching
            import urllib.parse
            title_query = urllib.parse.quote(title[:80])
            
            # Use search-based URL that works across environments
            article_url = f"{self.site_url}/search?q={title_query}"
            
            # Create post message with hashtags
            message = f"📰 {title}\n\n"
            message += f"👉 READ FULL STORY:\n{article_url}\n\n"
            if source and source_url:
                message += f"—\n📍 Original source: {source}\n{source_url}\n\n"
            elif source:
                message += f"—\n📍 via {source}\n\n"
            
            # Add hashtags at the end
            message += hashtags
            
            # Post to Facebook Page with image
            async with httpx.AsyncClient() as client:
                post_data = {
                    "message": message,
                    "access_token": page_token  # Use PAGE token, not user token
                }
                
                # If article has an image, post as photo with link in message
                if article_image and article_image.startswith('http'):
                    # Post as photo post for better engagement
                    response = await client.post(
                        f"{self.base_url}/{self.page_id}/photos",
                        data={
                            "url": article_image,
                            "caption": message,
                            "access_token": page_token
                        },
                        timeout=30.0
                    )
                else:
                    # Post as link post
                    post_data["link"] = article_url
                    response = await client.post(
                        f"{self.base_url}/{self.page_id}/feed",
                        data=post_data,
                        timeout=30.0
                    )
                
                result = response.json()
                
                if "id" in result:
                    logger.info(f"✅ Posted to Facebook: {title[:50]}... (Post ID: {result['id']})")
                    return {
                        "success": True,
                        "post_id": result["id"],
                        "article_title": title
                    }
                else:
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    logger.error(f"❌ Facebook post failed: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg
                    }
                    
        except Exception as e:
            logger.error(f"❌ Facebook posting error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def post_multiple_articles(self, articles: List[Dict], limit: int = 3) -> Dict:
        """
        Post multiple articles to Facebook Page
        Includes duplicate detection to avoid posting similar stories
        
        Args:
            articles: List of article dicts
            limit: Max number to post (default 3)
            
        Returns:
            Dict with results summary
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Facebook not configured",
                "posted": 0
            }
        
        # Filter out duplicate/similar articles
        unique_articles = self._filter_duplicates(articles)
        
        results = []
        posted_count = 0
        
        for article in unique_articles[:limit]:
            result = await self.post_article(article)
            results.append(result)
            if result.get("success"):
                posted_count += 1
        
        return {
            "success": posted_count > 0,
            "posted": posted_count,
            "total_attempted": min(len(unique_articles), limit),
            "results": results
        }
    
    def _generate_hashtags(self, title: str, category: str, source: str) -> str:
        """
        Generate relevant hashtags for Facebook posts.
        Combines category-based and location-based hashtags for maximum reach.
        
        Args:
            title: Article title
            category: Article category
            source: Article source
            
        Returns:
            String of hashtags (e.g., "#CheshireNews #LocalNews #Chester")
        """
        hashtags = set()
        title_lower = title.lower()
        
        # Always add core Cheshire hashtags
        hashtags.add("#CheshireToday")
        hashtags.add("#CheshireNews")
        
        # Category-based hashtags
        category_hashtags = {
            "Local News": ["#LocalNews", "#CheshireLife"],
            "UK News": ["#UKNews", "#BritishNews"],
            "Business": ["#Business", "#CheshireBusiness"],
            "Health": ["#Health", "#NHSNews", "#UKHealth"],
            "Sports": ["#Sports", "#CheshireSports"],
            "Tech": ["#Tech", "#TechNews"],
            "Weather": ["#UKWeather", "#CheshireWeather"],
            "Food": ["#FoodNews", "#CheshireFood"],
            "Events": ["#CheshireEvents", "#LocalEvents"],
            "Community": ["#Community", "#CheshireCommunity"],
            "Science": ["#Science", "#ScienceNews"],
            "Entertainment": ["#Entertainment", "#UKEntertainment"],
            "Education": ["#Education", "#UKEducation"],
        }
        
        if category in category_hashtags:
            for tag in category_hashtags[category]:
                hashtags.add(tag)
        
        # Location-based hashtags - check title for location mentions
        location_hashtags = {
            "chester": ["#Chester", "#ChesterNews"],
            "knutsford": ["#Knutsford", "#KnutsfordNews"],
            "wilmslow": ["#Wilmslow", "#WilmslowNews"],
            "alderley": ["#AlderleyEdge", "#AlderleyNews"],
            "macclesfield": ["#Macclesfield", "#MacclesfieldNews"],
            "warrington": ["#Warrington", "#WarringtonNews"],
            "crewe": ["#Crewe", "#CreweNews"],
            "northwich": ["#Northwich", "#NorthwichNews"],
            "nantwich": ["#Nantwich", "#NantwichNews"],
            "congleton": ["#Congleton"],
            "runcorn": ["#Runcorn"],
            "widnes": ["#Widnes"],
            "ellesmere port": ["#EllesmerePort"],
            "golden triangle": ["#GoldenTriangle", "#CheshireGoldenTriangle"],
        }
        
        for location, tags in location_hashtags.items():
            if location in title_lower:
                for tag in tags:
                    hashtags.add(tag)
        
        # Topic-based hashtags - check for common news topics
        topic_hashtags = {
            "police": ["#Police", "#Crime"],
            "crime": ["#Crime", "#UKCrime"],
            "hospital": ["#NHS", "#Hospital"],
            "school": ["#Schools", "#Education"],
            "council": ["#LocalCouncil", "#Council"],
            "traffic": ["#Traffic", "#Roads"],
            "weather": ["#Weather"],
            "flooding": ["#Flooding", "#UKFloods"],
            "fire": ["#Fire", "#Emergency"],
            "football": ["#Football", "#CheshireFootball"],
        }
        
        for topic, tags in topic_hashtags.items():
            if topic in title_lower:
                for tag in tags:
                    hashtags.add(tag)
        
        # Limit to 8 hashtags max for readability
        hashtag_list = list(hashtags)[:8]
        
        return " ".join(hashtag_list)
    
    def _filter_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """
        Filter out duplicate or very similar articles.
        Uses title similarity to detect duplicates.
        """
        unique = []
        seen_titles = set()
        seen_urls = set()
        
        for article in articles:
            title = article.get('title', '').lower().strip()
            source_url = article.get('source_url', '')
            
            # Skip if same source URL
            if source_url and source_url in seen_urls:
                logger.info(f"Skipping duplicate URL: {title[:40]}...")
                continue
            
            # Check for similar titles (first 5 significant words)
            title_words = [w for w in title.split() if len(w) > 3][:5]
            title_key = ' '.join(sorted(title_words))
            
            # Also check if title contains key parts of already seen titles
            is_duplicate = False
            for seen_title in seen_titles:
                # Check word overlap
                seen_words = set(seen_title.split())
                current_words = set(title_key.split())
                overlap = len(seen_words & current_words)
                
                # If more than 60% overlap, consider duplicate
                if overlap >= 3 or (len(current_words) > 0 and overlap / len(current_words) > 0.6):
                    is_duplicate = True
                    logger.info(f"Skipping similar article: {title[:40]}...")
                    break
            
            if is_duplicate:
                continue
            
            seen_titles.add(title_key)
            if source_url:
                seen_urls.add(source_url)
            unique.append(article)
        
        logger.info(f"Filtered {len(articles)} articles to {len(unique)} unique articles")
        return unique
    
    async def verify_token(self) -> Dict:
        """
        Verify the Facebook token is valid and get page info
        
        Returns:
            Dict with token status and page info
        """
        if not self.is_configured:
            return {
                "valid": False,
                "error": "Facebook credentials not configured"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                # Get page info to verify token works
                response = await client.get(
                    f"{self.base_url}/{self.page_id}",
                    params={
                        "fields": "name,id,fan_count,link",
                        "access_token": self.user_access_token
                    },
                    timeout=15.0
                )
                
                result = response.json()
                
                if "error" in result:
                    return {
                        "valid": False,
                        "error": result["error"].get("message", "Token invalid")
                    }
                
                return {
                    "valid": True,
                    "page_name": result.get("name"),
                    "page_id": result.get("id"),
                    "followers": result.get("fan_count"),
                    "page_url": result.get("link")
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def post_single_article_by_id(self, db, article_id: str) -> Dict:
        """
        Post a specific article by its ID.
        This is used for manual selection posting.
        
        Args:
            db: MongoDB database instance
            article_id: The article ID (string format of _id or uuid)
            
        Returns:
            Dict with success status
        """
        try:
            # Try to find article by _id (ObjectId) or by id field (UUID string)
            article = None
            
            # Try ObjectId first
            try:
                article = await db.articles.find_one({"_id": ObjectId(article_id)})
            except:
                pass
            
            # If not found, try by id field
            if not article:
                article = await db.articles.find_one({"id": article_id})
            
            if not article:
                return {
                    "success": False,
                    "error": f"Article not found: {article_id}"
                }
            
            # Convert ObjectId to string for the article dict
            article_dict = {
                "id": str(article.get("_id", article.get("id", ""))),
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "image": article.get("image", ""),
                "source": article.get("source", ""),
                "source_url": article.get("source_url", "")
            }
            
            # Post the article
            return await self.post_article(article_dict)
            
        except Exception as e:
            logger.error(f"Error posting article by ID: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def fetch_post_engagement(self, post_id: str) -> Dict:
        """
        Fetch engagement metrics for a specific Facebook post.
        Returns likes, comments, shares count.
        
        Args:
            post_id: Facebook post ID
            
        Returns:
            Dict with engagement metrics or error
        """
        if not self.is_configured:
            return {"success": False, "error": "Facebook not configured"}
        
        page_token = await self.get_page_token()
        if not page_token:
            return {"success": False, "error": "Could not get page token"}
        
        try:
            async with httpx.AsyncClient() as client:
                # Fetch post insights
                response = await client.get(
                    f"{self.base_url}/{post_id}",
                    params={
                        "fields": "reactions.summary(true),comments.summary(true),shares",
                        "access_token": page_token
                    },
                    timeout=15.0
                )
                
                result = response.json()
                
                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"].get("message", "Unknown error")
                    }
                
                # Extract metrics
                reactions = result.get("reactions", {}).get("summary", {}).get("total_count", 0)
                comments = result.get("comments", {}).get("summary", {}).get("total_count", 0)
                shares = result.get("shares", {}).get("count", 0) if result.get("shares") else 0
                
                # Calculate engagement score (weighted)
                engagement_score = reactions + (comments * 2) + (shares * 3)
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "reactions": reactions,
                    "comments": comments,
                    "shares": shares,
                    "engagement_score": engagement_score
                }
                
        except Exception as e:
            logger.error(f"Error fetching post engagement: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def fetch_recent_posts_engagement(self, limit: int = 20) -> Dict:
        """
        Fetch recent Facebook Page content first, then enrich each item with engagement.
        This avoids Facebook Graph dropping newer feed posts when engagement fields are requested
        directly on list edges.
        
        Args:
            limit: Number of recent items to fetch per Facebook edge
            
        Returns:
            Dict with list of posts and their engagement
        """
        if not self.is_configured:
            return {"success": False, "error": "Facebook not configured", "posts": []}
        
        page_token = await self.get_page_token()
        if not page_token:
            return {"success": False, "error": "Could not get page token", "posts": []}
        
        try:
            async with httpx.AsyncClient() as client:
                posts_by_key = {}
                errors = []

                edges = [
                    {
                        "name": "feed",
                        "fields": "id,message,created_time,permalink_url"
                    },
                    {
                        "name": "published_posts",
                        "fields": "id,message,created_time,permalink_url"
                    },
                    {
                        "name": "posts",
                        "fields": "id,message,created_time,permalink_url"
                    },
                    {
                        "name": "photos",
                        "fields": "id,name,created_time,permalink_url"
                    },
                    {
                        "name": "videos",
                        "fields": "id,description,created_time,permalink_url"
                    },
                    {
                        "name": "video_reels",
                        "fields": "id,description,created_time,permalink_url"
                    }
                ]

                for edge in edges:
                    response = await client.get(
                        f"{self.base_url}/{self.page_id}/{edge['name']}",
                        params={
                            "fields": edge["fields"],
                            "limit": limit,
                            "access_token": page_token
                        },
                        timeout=30.0
                    )
                    result = response.json()

                    if "error" in result:
                        errors.append(f"{edge['name']}: {result['error'].get('message', 'Unknown error')}")
                        logger.warning(f"Facebook analytics edge failed: {edge['name']}")
                        continue

                    for post in result.get("data", []):
                        post_id = post.get("id")
                        if not post_id:
                            continue

                        permalink_url = post.get("permalink_url")
                        dedupe_key = post_id
                        if permalink_url:
                            dedupe_key = (
                                permalink_url
                                .replace("https://www.facebook.com", "")
                                .replace("http://www.facebook.com", "")
                            )

                        if dedupe_key in posts_by_key:
                            continue

                        engagement_response = await client.get(
                            f"{self.base_url}/{post_id}",
                            params={
                                "fields": "reactions.summary(true),comments.summary(true),shares",
                                "access_token": page_token
                            },
                            timeout=15.0
                        )
                        engagement_result = engagement_response.json()
                        if "error" in engagement_result:
                            engagement_result = {}

                        reactions = engagement_result.get("reactions", {}).get("summary", {}).get("total_count", 0)
                        comments = engagement_result.get("comments", {}).get("summary", {}).get("total_count", 0)
                        shares = engagement_result.get("shares", {}).get("count", 0) if engagement_result.get("shares") else 0
                        engagement_score = reactions + (comments * 2) + (shares * 3)

                        message = post.get("message") or post.get("description") or post.get("name") or ""
                        title = ""
                        for line in message.split("\n"):
                            cleaned = line.strip().replace("📰", "").strip()
                            if cleaned:
                                title = cleaned
                                break

                        source_type = edge["name"]
                        if permalink_url and "/reel/" in permalink_url:
                            source_type = "reel"

                        posts_by_key[dedupe_key] = {
                            "post_id": post_id,
                            "source_type": source_type,
                            "title": title[:100] if title else "Unknown",
                            "message_preview": message[:150] + "..." if len(message) > 150 else message,
                            "created_time": post.get("created_time"),
                            "permalink_url": permalink_url,
                            "likes": reactions,
                            "reactions": reactions,
                            "comments": comments,
                            "shares": shares,
                            "engagement_score": engagement_score
                        }

                posts = list(posts_by_key.values())

                if not posts and errors:
                    return {
                        "success": False,
                        "error": "; ".join(errors[:3]),
                        "posts": []
                    }

                # Rank by engagement, but use freshness as the tie-breaker so zero-engagement lists stay current.
                posts.sort(
                    key=lambda x: (x.get("engagement_score", 0), x.get("created_time") or ""),
                    reverse=True
                )

                return {
                    "success": True,
                    "total_posts": len(posts),
                    "warnings": errors[:3],
                    "posts": posts
                }
                
        except Exception as e:
            logger.error(f"Error fetching recent posts engagement: {str(e)}")
            return {"success": False, "error": str(e), "posts": []}


# Singleton instance
facebook_service = FacebookService()
