"""
Pixabay API Service for Cheshire Today
Third free image source - excellent UK/British content
Completely free with no attribution required
"""

import os
import re
import httpx
import logging
import random
from typing import Optional, Set
from dotenv import load_dotenv

# Load .env from the backend directory
load_dotenv('/app/backend/.env')

logger = logging.getLogger(__name__)


def extract_pixabay_photo_id(url: str) -> str:
    """Extract the unique photo ID from a Pixabay URL."""
    if not url:
        return ""
    # Look for numeric ID (usually 5+ digits) in URL
    match = re.search(r'[_-](\d{5,})', url)
    if match:
        return f'pixabay:{match.group(1)}'
    # Fallback
    return url.split('?')[0]


def is_pixabay_photo_used(url: str, used_photo_ids: Set[str]) -> bool:
    """Check if a Pixabay photo ID is already in the used set."""
    photo_id = extract_pixabay_photo_id(url)
    return photo_id in used_photo_ids


class PixabayService:
    """Service for fetching images from Pixabay API - Free UK images"""
    
    def __init__(self):
        self.api_key = os.environ.get('PIXABAY_API_KEY')
        self.base_url = "https://pixabay.com/api/"  # Trailing slash required
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("PIXABAY_API_KEY not found - Pixabay API disabled")
        else:
            logger.info("Pixabay API service initialized")
    
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
            return 'hospital doctor nurse medical'
        
        # Police/Crime content - UK police
        if any(word in title_lower for word in ['police', 'crime', 'arrest', 'missing', 'burglary']):
            return 'police officer law'
        
        # Property/Housing content - British houses
        if any(word in title_lower for word in ['property', 'house', 'housing', 'home', 'estate']):
            return 'houses residential england'
        
        # Council/Planning/Budget content
        if any(word in title_lower for word in ['council', 'planning', 'development', 'budget']):
            return 'town hall council building'
        
        # Election/Politics content - UK Parliament
        if any(word in title_lower for word in ['election', 'parliament', 'government', 'political', 'parties', 'vote']):
            return 'parliament westminster london'
        
        # Football/Sports content
        if any(word in title_lower for word in ['fc', 'football', 'soccer', 'match', 'league']):
            return 'football stadium soccer'
        
        # Business content - UK business
        if any(word in title_lower for word in ['business', 'company', 'investment']):
            return 'business office london'
        
        # Food/Restaurant content
        if any(word in title_lower for word in ['restaurant', 'dining', 'food', 'chef']):
            return 'restaurant food dining'
        
        if any(word in title_lower for word in ['pub', 'inn', 'bar']):
            return 'pub english traditional'
        
        # Weather content
        if any(word in title_lower for word in ['weather', 'rain', 'storm']):
            return 'weather rain clouds england'
        
        # School/Education content
        if any(word in title_lower for word in ['school', 'education', 'student']):
            return 'school classroom education'
        
        # Tech content
        if any(word in title_lower for word in ['tech', 'technology', 'digital']):
            return 'technology computer office'
        
        # Village content
        if any(word in title_lower for word in ['village', 'community']):
            return 'village countryside england'
        
        # CATEGORY DEFAULTS with UK focus
        category_queries = {
            'Local News': 'village countryside england',
            'UK News': 'london city england',
            'Business': 'business office london',
            'Tech': 'technology computer office',
            'Health': 'hospital medical healthcare',
            'Sports': 'football stadium sport',
            'Weather': 'weather sky england',
            'Food': 'restaurant food dining',
        }
        
        return category_queries.get(category, 'countryside england')
    
    async def search_image(
        self, 
        query: str, 
        orientation: str = "horizontal",
        per_page: int = 20,
        used_photo_ids: set = None
    ) -> Optional[str]:
        """
        Search for an image on Pixabay and return the URL.
        Returns webformat image URL or None if not found.
        CRITICAL: Compares photo IDs (not full URLs) to detect true duplicates.
        """
        if not self.enabled:
            return None
        
        if used_photo_ids is None:
            used_photo_ids = set()
        
        try:
            params = {
                "key": self.api_key,
                "q": query,
                "orientation": orientation,
                "per_page": per_page,
                "image_type": "photo",
                "safesearch": "true",
                "editors_choice": "false",
                "min_width": 800,
                "min_height": 500
            }
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(self.base_url, params=params, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get("hits", [])
                    
                    if hits:
                        # Find first unused image by comparing photo IDs
                        for photo in hits:
                            image_url = photo.get("webformatURL", "")
                            # CRITICAL: Check by photo ID, not full URL
                            if image_url and not is_pixabay_photo_used(image_url, used_photo_ids):
                                logger.info(f"Pixabay unique image found for '{query[:30]}': {image_url[-50:]}")
                                return image_url
                        
                        logger.warning(f"All {len(hits)} Pixabay results already used for: {query[:30]}")
                        return None
                    
                    logger.warning(f"No Pixabay results for query: {query}")
                    return None
                        
                elif response.status_code == 429:
                    logger.warning("Pixabay API: Rate limit exceeded")
                    return None
                else:
                    logger.error(f"Pixabay API error: {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Pixabay API timeout")
            return None
        except Exception as e:
            logger.error(f"Pixabay API error: {str(e)}")
            return None
    
    async def get_article_image(
        self, 
        title: str, 
        category: str, 
        scope: str = "cheshire",
        used_images: set = None
    ) -> Optional[str]:
        """
        Get a UK-themed image for an article from Pixabay.
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
        
        # If first query fails or all images used, try simpler queries
        fallback_queries = [
            f"united kingdom england {category.lower()}",
            "british countryside village england",
            "england landscape rural"
        ]
        
        for fallback in fallback_queries:
            image_url = await self.search_image(fallback, used_photo_ids=used_images)
            if image_url:
                return image_url
        
        return None


# Global instance
pixabay_service = PixabayService()
