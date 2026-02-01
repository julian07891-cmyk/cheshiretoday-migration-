"""
Unsplash API Service for Cheshire Today
Dynamically fetches images based on article content/keywords
"""

import os
import re
import httpx
import logging
import random
from typing import Optional, List, Dict, Any, Set
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def extract_unsplash_photo_id(url: str) -> str:
    """Extract the unique photo ID from an Unsplash URL, ignoring query params."""
    if not url:
        return ""
    match = re.search(r'photo-([a-zA-Z0-9_-]+)', url)
    if match:
        return f'unsplash:{match.group(0)}'
    # Fallback to base URL
    return url.split('?')[0]


def is_photo_used(url: str, used_photo_ids: Set[str]) -> bool:
    """Check if a photo ID is already in the used set."""
    photo_id = extract_unsplash_photo_id(url)
    return photo_id in used_photo_ids


class UnsplashService:
    """Service for fetching images from Unsplash API"""
    
    def __init__(self):
        self.access_key = os.environ.get('UNSPLASH_ACCESS_KEY')
        self.base_url = "https://api.unsplash.com"
        self.enabled = bool(self.access_key)
        
        if not self.enabled:
            logger.warning("UNSPLASH_ACCESS_KEY not found - Unsplash API disabled")
        else:
            logger.info("Unsplash API service initialized")
    
    async def search_image(
        self, 
        query: str, 
        orientation: str = "landscape",
        per_page: int = 5
    ) -> Optional[str]:
        """
        Search for an image on Unsplash and return the URL.
        Returns regular size image URL or None if not found.
        Prioritizes first result as it's usually most relevant.
        """
        if not self.enabled:
            return None
        
        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "orientation": orientation,
                "per_page": per_page,
                "client_id": self.access_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if results:
                        # Use first result - it's usually the most relevant
                        # Only use random if we want variety (e.g., for fallback queries)
                        photo = results[0]
                        image_url = photo["urls"]["regular"]
                        
                        # Add size parameters for consistent display
                        if "?" in image_url:
                            image_url += "&w=800&h=500&fit=crop"
                        else:
                            image_url += "?w=800&h=500&fit=crop"
                        
                        logger.info(f"Unsplash image found for '{query[:30]}': {image_url[-50:]}")
                        return image_url
                    else:
                        logger.warning(f"No Unsplash results for query: {query}")
                        return None
                        
                elif response.status_code == 401:
                    logger.error("Unsplash API: Invalid access key")
                    return None
                elif response.status_code == 403:
                    logger.warning("Unsplash API: Rate limit exceeded")
                    return None
                else:
                    logger.error(f"Unsplash API error: {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Unsplash API timeout")
            return None
        except Exception as e:
            logger.error(f"Unsplash API error: {str(e)}")
            return None
    
    def build_search_query(self, title: str, category: str, scope: str = "cheshire") -> str:
        """
        Build a content-aware search query that matches article context.
        PRIORITY: UK/British-specific images > Content keywords > Category defaults
        ALL queries include UK/British terms to ensure location-appropriate images.
        """
        title_lower = title.lower()
        
        # UK prefix for all searches to prioritize British content
        uk_prefix = "united kingdom british england "
        
        # CONTENT-FIRST MATCHING with UK focus
        
        # Health/Medical content - UK NHS focus
        if any(word in title_lower for word in ['nhs', 'hospital', 'doctor', 'nurse', 'patient', 'healthcare', 'medical', 'clinic', 'surgery', 'gp', 'ambulance', 'a&e', 'emergency', 'waiting list']):
            return 'NHS hospital british healthcare doctor ward england'
        
        if any(word in title_lower for word in ['mental health', 'wellbeing', 'therapy', 'counselling']):
            return 'mental health support therapy british'
        
        # Police/Crime content - UK police
        if any(word in title_lower for word in ['police', 'crime', 'arrest', 'missing', 'burglary', 'theft', 'investigation']):
            return 'british police officer UK law enforcement'
        
        # Property/Housing content - British houses
        if any(word in title_lower for word in ['property', 'house', 'housing', 'home', 'estate', 'mortgage', 'rent']):
            return 'british terraced houses england residential street'
        
        # Council/Planning/Budget content - UK council
        if any(word in title_lower for word in ['council', 'planning', 'development', 'regeneration', 'green belt', 'budget']):
            return 'british town hall council civic building england'
        
        # Election/Politics content - UK Parliament
        if any(word in title_lower for word in ['election', 'parliament', 'government', 'minister', 'mp', 'political', 'parties', 'vote', 'campaign']):
            return 'UK parliament westminster british politics london'
        
        # Football/Sports content - UK sports
        if any(word in title_lower for word in ['fc', 'football', 'soccer', 'match', 'league', 'united', 'city', 'striker', 'goal']):
            return 'english football stadium premier league soccer'
        
        if any(word in title_lower for word in ['rugby']):
            return 'english rugby stadium twickenham sport'
        
        if any(word in title_lower for word in ['cricket']):
            return 'england cricket lords sport match'
        
        if any(word in title_lower for word in ['golf', 'course']):
            return 'english golf course green fairway'
        
        # Business/Finance content - UK business
        if any(word in title_lower for word in ['business', 'company', 'investment', 'startup', 'entrepreneur', 'economy']):
            return 'london business office canary wharf city'
        
        if any(word in title_lower for word in ['bank', 'finance', 'stock', 'market', 'interest rate']):
            return 'city of london bank england finance'
        
        # Food/Restaurant content - British food
        if any(word in title_lower for word in ['restaurant', 'dining', 'food', 'chef', 'culinary', 'gastro']):
            return 'british restaurant dining english food'
        
        if any(word in title_lower for word in ['pub', 'inn', 'tavern', 'bar']):
            return 'english pub traditional british cozy'
        
        if any(word in title_lower for word in ['cafe', 'coffee', 'tea']):
            return 'british cafe tea room english'
        
        # Weather content - UK weather
        if any(word in title_lower for word in ['weather', 'rain', 'storm', 'flood']):
            return 'british weather rain england clouds'
        
        if any(word in title_lower for word in ['sun', 'warm', 'summer', 'heatwave']):
            return 'english summer countryside sunshine'
        
        if any(word in title_lower for word in ['snow', 'cold', 'winter', 'frost', 'ice']):
            return 'british winter snow england frost'
        
        # School/Education content - UK schools
        if any(word in title_lower for word in ['school', 'education', 'student', 'university', 'college', 'teacher']):
            return 'british school education england classroom'
        
        # Transport content - UK transport
        if any(word in title_lower for word in ['road', 'traffic', 'motorway', 'highway', 'a-road']):
            return 'british motorway road england traffic'
        
        if any(word in title_lower for word in ['train', 'rail', 'railway', 'station']):
            return 'british train railway station england'
        
        # Technology content
        if any(word in title_lower for word in ['tech', 'technology', 'digital', 'software', 'app', 'ai', 'computer']):
            return 'technology computer office london tech'
        
        # Community/Village content - English villages
        if any(word in title_lower for word in ['village', 'community', 'resident', 'neighbour', 'local']):
            return 'english village countryside cotswolds'
        
        # Christmas/Festive content
        if any(word in title_lower for word in ['christmas', 'festive', 'holiday', 'xmas', 'carol']):
            return 'british christmas festive lights'
        
        # CATEGORY DEFAULTS with UK focus - only used if no content match found
        category_terms = {
            'Local News': 'english village street countryside',
            'UK News': 'westminster parliament london british',
            'Business': 'london business office canary wharf',
            'Tech': 'technology computer office',
            'Health': 'hospital healthcare doctor nurse medical',
            'Sports': 'football stadium soccer england',
            'Weather': 'british weather countryside clouds',
            'Food': 'british restaurant food pub',
        }
        
        return category_terms.get(category, 'english village countryside')
    
    async def get_article_image(
        self, 
        title: str, 
        category: str, 
        content: str = "",
        scope: str = "cheshire",
        used_images: set = None
    ) -> Optional[str]:
        """
        Get an appropriate image for an article.
        Builds search query from title/category and fetches from Unsplash.
        Ensures no duplicate images by checking photo IDs (not full URLs).
        """
        if used_images is None:
            used_images = set()
        
        # Build optimized search query
        query = self.build_search_query(title, category, scope)
        
        logger.info(f"Searching Unsplash for: '{query}'")
        
        # Get unique image using photo ID comparison
        image_url = await self.search_unique_image(query, used_images)
        
        # If no results, try simpler category-based search
        if not image_url:
            fallback_queries = {
                'Local News': 'english village countryside',
                'UK News': 'united kingdom cityscape',
                'Business': 'modern office building',
                'Tech': 'technology computer',
                'Health': 'hospital healthcare',
                'Sports': 'sports stadium',
                'Weather': 'sky clouds landscape',
                'Food': 'restaurant food',
                'Community': 'community gathering people',
                'Events': 'festival celebration',
                'Finance': 'finance money',
                'Festive': 'christmas decorations',
            }
            
            fallback = fallback_queries.get(category, 'british landscape')
            logger.info(f"Trying fallback query: '{fallback}'")
            image_url = await self.search_unique_image(fallback, used_images)
        
        return image_url
    
    async def search_unique_image(self, query: str, used_photo_ids: set, per_page: int = 20) -> Optional[str]:
        """
        Search for an image that hasn't been used yet.
        CRITICAL: Compares photo IDs, not full URLs, to detect true duplicates.
        """
        if not self.enabled:
            return None
        
        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "orientation": "landscape",
                "per_page": per_page,
                "client_id": self.access_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    # Find first unused image by comparing photo IDs
                    for photo in results:
                        image_url = photo["urls"]["regular"]
                        if "?" in image_url:
                            image_url += "&w=800&h=500&fit=crop"
                        else:
                            image_url += "?w=800&h=500&fit=crop"
                        
                        # CRITICAL: Check by photo ID, not full URL
                        if not is_photo_used(image_url, used_photo_ids):
                            logger.info(f"Found unique Unsplash image: {image_url[-50:]}")
                            return image_url
                    
                    logger.warning(f"All {len(results)} Unsplash results already used for: {query[:30]}")
                    return None
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Unsplash search error: {str(e)}")
            return None


# Global instance
unsplash_service = UnsplashService()
