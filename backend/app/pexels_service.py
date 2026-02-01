"""
Pexels API Service for Cheshire Today
Provides additional UK-focused images alongside Unsplash
Free API with excellent British/UK content
"""

import os
import re
import httpx
import logging
import random
from typing import Optional, List, Set
from dotenv import load_dotenv

# Load .env from the backend directory
load_dotenv('/app/backend/.env')

logger = logging.getLogger(__name__)


def extract_pexels_photo_id(url: str) -> str:
    """Extract the unique photo ID from a Pexels URL."""
    if not url:
        return ""
    # Try /photos/XXXXX format
    match = re.search(r'/photos/(\d+)', url)
    if match:
        return f'pexels:{match.group(1)}'
    # Try pexels-photo-XXXXX format
    match = re.search(r'pexels-photo-(\d+)', url)
    if match:
        return f'pexels:{match.group(1)}'
    # Fallback
    return url.split('?')[0]


def is_pexels_photo_used(url: str, used_photo_ids: Set[str]) -> bool:
    """Check if a Pexels photo ID is already in the used set."""
    photo_id = extract_pexels_photo_id(url)
    return photo_id in used_photo_ids


class PexelsService:
    """Service for fetching images from Pexels API - Free UK images"""
    
    def __init__(self):
        self.api_key = os.environ.get('PEXELS_API_KEY')
        self.base_url = "https://api.pexels.com/v1"
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("PEXELS_API_KEY not found - Pexels API disabled")
        else:
            logger.info("Pexels API service initialized")
    
    def build_uk_search_query(self, title: str, category: str, scope: str = "cheshire") -> str:
        """
        Build a content-aware search query that matches article context.
        PRIORITY: UK/British-specific images > Content keywords > Category defaults
        ALL queries include UK/British terms.
        """
        title_lower = title.lower()
        
        # CONTENT-FIRST MATCHING with UK focus
        
        # Health/Medical content - UK NHS
        if any(word in title_lower for word in ['nhs', 'hospital', 'doctor', 'nurse', 'patient', 'healthcare', 'medical']):
            return 'NHS hospital british healthcare doctor'
        
        # Police/Crime content - UK police
        if any(word in title_lower for word in ['police', 'crime', 'arrest', 'missing', 'burglary', 'theft']):
            return 'british police officer UK law'
        
        # Property/Housing content - British houses
        if any(word in title_lower for word in ['property', 'house', 'housing', 'home', 'estate']):
            return 'british houses terraced england street'
        
        # Council/Planning/Budget content - UK council
        if any(word in title_lower for word in ['council', 'planning', 'development', 'regeneration', 'budget']):
            return 'british town hall council england'
        
        # Election/Politics content - UK Parliament
        if any(word in title_lower for word in ['election', 'parliament', 'government', 'minister', 'political', 'parties', 'vote']):
            return 'UK parliament westminster london politics'
        
        # Football/Sports content - UK sports
        if any(word in title_lower for word in ['fc', 'football', 'soccer', 'match', 'league']):
            return 'english football stadium soccer'
        
        # Business content - UK business
        if any(word in title_lower for word in ['business', 'company', 'investment', 'economy']):
            return 'london business office city canary wharf'
        
        # Food/Restaurant content - British food
        if any(word in title_lower for word in ['restaurant', 'dining', 'food', 'chef', 'culinary']):
            return 'british restaurant english food dining'
        
        if any(word in title_lower for word in ['pub', 'inn', 'bar']):
            return 'english pub traditional british'
        
        # Weather content - UK weather
        if any(word in title_lower for word in ['weather', 'rain', 'storm']):
            return 'british weather england rain clouds'
        
        # School/Education content - UK schools
        if any(word in title_lower for word in ['school', 'education', 'student']):
            return 'british school england education'
        
        # Tech content
        if any(word in title_lower for word in ['tech', 'technology', 'digital', 'software']):
            return 'london technology office startup'
        
        # Village/Community content - English villages
        if any(word in title_lower for word in ['village', 'community']):
            return 'english village countryside'
        
        # CATEGORY DEFAULTS with UK focus
        category_queries = {
            'Local News': 'english village street',
            'UK News': 'london parliament westminster',
            'Business': 'london business office',
            'Tech': 'technology computer office',
            'Health': 'hospital healthcare doctor nurse',
            'Sports': 'football stadium soccer',
            'Weather': 'weather clouds countryside',
            'Food': 'restaurant food pub',
        }
        
        return category_queries.get(category, 'english village countryside')
    
    async def search_image(
        self, 
        query: str, 
        orientation: str = "landscape",
        per_page: int = 20,
        used_photo_ids: set = None
    ) -> Optional[str]:
        """
        Search for an image on Pexels and return the URL.
        Returns medium size image URL or None if not found.
        CRITICAL: Compares photo IDs (not full URLs) to detect true duplicates.
        """
        if not self.enabled:
            return None
        
        if used_photo_ids is None:
            used_photo_ids = set()
        
        try:
            url = f"{self.base_url}/search"
            headers = {
                "Authorization": self.api_key
            }
            params = {
                "query": query,
                "orientation": orientation,
                "per_page": per_page,
                "size": "medium"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    photos = data.get("photos", [])
                    
                    if photos:
                        # Find first unused image by comparing photo IDs
                        for photo in photos:
                            image_url = photo["src"]["medium"]
                            # CRITICAL: Check by photo ID, not full URL
                            if not is_pexels_photo_used(image_url, used_photo_ids):
                                logger.info(f"Pexels unique image found for '{query[:30]}': {image_url[-50:]}")
                                return image_url
                        
                        logger.warning(f"All {len(photos)} Pexels results already used for: {query[:30]}")
                        return None
                    else:
                        logger.warning(f"No Pexels results for query: {query}")
                        return None
                        
                elif response.status_code == 401:
                    logger.error("Pexels API: Invalid API key")
                    return None
                elif response.status_code == 429:
                    logger.warning("Pexels API: Rate limit exceeded")
                    return None
                else:
                    logger.error(f"Pexels API error: {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Pexels API timeout")
            return None
        except Exception as e:
            logger.error(f"Pexels API error: {str(e)}")
            return None
    
    async def get_article_image(
        self, 
        title: str, 
        category: str, 
        scope: str = "cheshire",
        used_images: set = None
    ) -> Optional[str]:
        """
        Get a UK-themed image for an article from Pexels.
        CRITICAL: Uses photo ID comparison to prevent duplicates.
        """
        if not self.enabled:
            return None
        
        if used_images is None:
            used_images = set()
        
        # Build UK-focused query
        query = self.build_uk_search_query(title, category, scope)
        
        # Try to get a unique image
        image_url = await self.search_image(query, used_photo_ids=used_images)
        
        if image_url:
            return image_url
        
        # If first query fails or all images used, try category-only query
        fallback_query = f"united kingdom british {category.lower()} england"
        image_url = await self.search_image(fallback_query, used_photo_ids=used_images)
        
        return image_url


# Global instance
pexels_service = PexelsService()
