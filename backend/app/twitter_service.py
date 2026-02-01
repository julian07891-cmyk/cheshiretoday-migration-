"""
Twitter/X Service for Cheshire Today
Auto-posts articles to Twitter with hashtags and images
"""
import os
import logging
import tweepy
import tempfile
import httpx
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TwitterService:
    def __init__(self):
        self.api_key = os.environ.get('TWITTER_API_KEY')
        self.api_secret = os.environ.get('TWITTER_API_SECRET')
        self.access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
        self.client = None
        self.api_v1 = None  # For media uploads
        self._setup_client()
    
    def _setup_client(self):
        """Initialize Twitter API clients (v2 for tweets, v1.1 for media)"""
        if all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            try:
                # V2 Client for posting tweets
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )
                
                # V1.1 API for media uploads (required for images)
                auth = tweepy.OAuth1UserHandler(
                    self.api_key,
                    self.api_secret,
                    self.access_token,
                    self.access_token_secret
                )
                self.api_v1 = tweepy.API(auth)
                
                logger.info("✅ Twitter client initialized successfully (with media support)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Twitter client: {e}")
                self.client = None
                self.api_v1 = None
        else:
            logger.warning("⚠️ Twitter credentials not configured")
    
    @property
    def is_configured(self):
        return self.client is not None
    
    async def download_image(self, image_url):
        """Download image from URL and return temp file path"""
        try:
            if not image_url or image_url.startswith('data:'):
                return None
            
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=15, follow_redirects=True)
                if response.status_code == 200:
                    # Determine file extension
                    content_type = response.headers.get('content-type', '')
                    if 'png' in content_type:
                        ext = '.png'
                    elif 'gif' in content_type:
                        ext = '.gif'
                    else:
                        ext = '.jpg'
                    
                    # Save to temp file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                    temp_file.write(response.content)
                    temp_file.close()
                    return temp_file.name
        except Exception as e:
            logger.warning(f"Failed to download image: {e}")
        return None
    
    def upload_media(self, image_path):
        """Upload media to Twitter and return media_id"""
        try:
            if self.api_v1 and image_path:
                media = self.api_v1.media_upload(filename=image_path)
                return media.media_id
        except Exception as e:
            logger.warning(f"Failed to upload media to Twitter: {e}")
        return None
    
    def generate_hashtags(self, article):
        """Generate relevant hashtags for the article"""
        hashtags = ['#CheshireNews', '#CheshireToday']
        
        title = article.get('title', '').lower()
        category = article.get('category', '').lower()
        
        # Location-based hashtags
        locations = {
            'chester': '#Chester',
            'warrington': '#Warrington',
            'crewe': '#Crewe',
            'macclesfield': '#Macclesfield',
            'knutsford': '#Knutsford',
            'wilmslow': '#Wilmslow',
            'northwich': '#Northwich',
            'stockport': '#Stockport',
            'wirral': '#Wirral',
            'runcorn': '#Runcorn'
        }
        
        for loc, tag in locations.items():
            if loc in title:
                hashtags.append(tag)
                break
        
        # Category-based hashtags
        category_tags = {
            'local news': '#LocalNews',
            'uk news': '#UKNews',
            'sports': '#Sports #CheshireSport',
            'health': '#Health #NHS',
            'business': '#Business',
            'community': '#Community',
            'weather': '#Weather',
            'crime': '#Crime #Police'
        }
        
        for cat, tags in category_tags.items():
            if cat in category:
                hashtags.extend(tags.split())
                break
        
        # Topic-based hashtags from title
        if 'police' in title or 'crime' in title:
            hashtags.append('#CheshirePolice')
        if 'council' in title:
            hashtags.append('#LocalGov')
        if 'school' in title or 'education' in title:
            hashtags.append('#Education')
        if 'hospital' in title or 'nhs' in title:
            hashtags.append('#NHS')
        
        # Remove duplicates and limit to 5 hashtags (Twitter best practice)
        seen = set()
        unique_hashtags = []
        for tag in hashtags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_hashtags.append(tag)
        
        return unique_hashtags[:5]
    
    async def post_article(self, article):
        """Post a single article to Twitter with image"""
        if not self.is_configured:
            return {"success": False, "error": "Twitter not configured"}
        
        try:
            article_id = article.get('id', '')
            title = article.get('title', 'News from Cheshire Today')
            image_url = article.get('image', '')
            
            # Use search-based URL (same as Facebook) - works better with React SPA routing
            import urllib.parse
            title_query = urllib.parse.quote(title[:80])
            article_url = f"https://cheshiretoday.co.uk/search?q={title_query}"
            
            # Generate hashtags
            hashtags = self.generate_hashtags(article)
            hashtag_str = ' '.join(hashtags)
            
            # Twitter has 280 character limit
            # URL takes ~23 chars, leave room for hashtags
            max_title_length = 280 - 25 - len(hashtag_str) - 5  # 5 for spacing/newlines
            
            if len(title) > max_title_length:
                title = title[:max_title_length-3] + '...'
            
            # Compose tweet
            tweet_text = f"{title}\n\n{article_url}\n\n{hashtag_str}"
            
            # Try to upload image
            media_id = None
            temp_image_path = None
            
            if image_url and self.api_v1:
                temp_image_path = await self.download_image(image_url)
                if temp_image_path:
                    media_id = self.upload_media(temp_image_path)
                    # Clean up temp file
                    try:
                        os.unlink(temp_image_path)
                    except:
                        pass
            
            # Post to Twitter (with or without media)
            if media_id:
                response = self.client.create_tweet(text=tweet_text, media_ids=[media_id])
                logger.info(f"✅ Posted to Twitter with image: {title[:50]}...")
            else:
                response = self.client.create_tweet(text=tweet_text)
                logger.info(f"✅ Posted to Twitter (no image): {title[:50]}...")
            
            tweet_id = response.data['id']
            
            return {
                "success": True,
                "tweet_id": tweet_id,
                "article_title": title,
                "has_image": media_id is not None
            }
            
        except tweepy.TweepyException as e:
            error_msg = str(e)
            logger.error(f"❌ Twitter posting error: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            logger.error(f"❌ Unexpected Twitter error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def post_multiple_articles(self, articles, limit=3):
        """Post multiple articles to Twitter"""
        if not self.is_configured:
            return {"success": False, "error": "Twitter not configured", "posted": 0}
        
        results = []
        posted_count = 0
        
        for article in articles[:limit]:
            result = await self.post_article(article)
            results.append(result)
            if result.get("success"):
                posted_count += 1
        
        return {
            "success": posted_count > 0,
            "posted": posted_count,
            "results": results
        }

# Global instance
twitter_service = TwitterService()
