"""
Content-Aware Image Matching Service for Cheshire Today
Maps article content to appropriate UK-themed images
"""

import re
import logging
from typing import Optional, Set

logger = logging.getLogger(__name__)

# Comprehensive keyword to image mapping
# Each image is a verified Pexels image that matches the content
CONTENT_IMAGE_MAP = {
    # ===== SPORTS =====
    # Tennis
    'tennis': 'https://images.pexels.com/photos/209977/pexels-photo-209977.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'sabalenka': 'https://images.pexels.com/photos/209977/pexels-photo-209977.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'kyrgios': 'https://images.pexels.com/photos/209977/pexels-photo-209977.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'wimbledon': 'https://images.pexels.com/photos/209977/pexels-photo-209977.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'djokovic': 'https://images.pexels.com/photos/209977/pexels-photo-209977.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'nadal': 'https://images.pexels.com/photos/209977/pexels-photo-209977.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # Football (Soccer)
    'football': 'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'premier league': 'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'striker': 'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'watkins': 'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'calvert-lewin': 'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'world cup': 'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'carroll': 'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # Liverpool specific
    'liverpool': 'https://images.pexels.com/photos/47730/the-ball-stadion-horn-corner-47730.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'jota': 'https://images.pexels.com/photos/47730/the-ball-stadion-horn-corner-47730.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'anfield': 'https://images.pexels.com/photos/47730/the-ball-stadion-horn-corner-47730.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # Stadium
    'stadium': 'https://images.pexels.com/photos/274422/pexels-photo-274422.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # Cricket
    'cricket': 'https://images.pexels.com/photos/3628912/pexels-photo-3628912.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'ashes': 'https://images.pexels.com/photos/3628912/pexels-photo-3628912.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # ===== EMERGENCY/CRIME =====
    # Fire
    'fire': 'https://images.pexels.com/photos/266487/pexels-photo-266487.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'house fire': 'https://images.pexels.com/photos/266487/pexels-photo-266487.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'blaze': 'https://images.pexels.com/photos/266487/pexels-photo-266487.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'firefighter': 'https://images.pexels.com/photos/266487/pexels-photo-266487.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # Police/Crime
    'police': 'https://images.pexels.com/photos/532001/pexels-photo-532001.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'arrest': 'https://images.pexels.com/photos/5668473/pexels-photo-5668473.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'court': 'https://images.pexels.com/photos/5668473/pexels-photo-5668473.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'assault': 'https://images.pexels.com/photos/532001/pexels-photo-532001.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'murder': 'https://images.pexels.com/photos/532001/pexels-photo-532001.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'shooting': 'https://images.pexels.com/photos/532001/pexels-photo-532001.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # Death/Memorial
    'dies': 'https://images.pexels.com/photos/1266810/pexels-photo-1266810.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'died': 'https://images.pexels.com/photos/1266810/pexels-photo-1266810.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'death': 'https://images.pexels.com/photos/1266810/pexels-photo-1266810.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'tributes': 'https://images.pexels.com/photos/1266810/pexels-photo-1266810.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # Pub (for pub-related incidents)
    'pub': 'https://images.pexels.com/photos/3771097/pexels-photo-3771097.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'village pub': 'https://images.pexels.com/photos/3771097/pexels-photo-3771097.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # ===== VEHICLES/TRANSPORT =====
    # Cars/Tesla
    'tesla': 'https://images.pexels.com/photos/3729464/pexels-photo-3729464.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'self-driving': 'https://images.pexels.com/photos/3729464/pexels-photo-3729464.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'autonomous': 'https://images.pexels.com/photos/3729464/pexels-photo-3729464.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'electric car': 'https://images.pexels.com/photos/3729464/pexels-photo-3729464.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # ===== POLITICS/GOVERNMENT =====
    'parliament': 'https://images.pexels.com/photos/258117/pexels-photo-258117.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'westminster': 'https://images.pexels.com/photos/258117/pexels-photo-258117.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'government': 'https://images.pexels.com/photos/258117/pexels-photo-258117.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'starmer': 'https://images.pexels.com/photos/258117/pexels-photo-258117.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'tories': 'https://images.pexels.com/photos/258117/pexels-photo-258117.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'labour': 'https://images.pexels.com/photos/258117/pexels-photo-258117.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'deported': 'https://images.pexels.com/photos/672532/pexels-photo-672532.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # Church/Religion
    'archbishop': 'https://images.pexels.com/photos/208216/pexels-photo-208216.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'church': 'https://images.pexels.com/photos/208216/pexels-photo-208216.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'cathedral': 'https://images.pexels.com/photos/208216/pexels-photo-208216.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # ===== WEATHER =====
    'cold weather': 'https://images.pexels.com/photos/688660/pexels-photo-688660.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'snow': 'https://images.pexels.com/photos/688660/pexels-photo-688660.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'frost': 'https://images.pexels.com/photos/688660/pexels-photo-688660.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'winter': 'https://images.pexels.com/photos/688660/pexels-photo-688660.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'amber': 'https://images.pexels.com/photos/1431822/pexels-photo-1431822.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'storm': 'https://images.pexels.com/photos/1431822/pexels-photo-1431822.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'new year': 'https://images.pexels.com/photos/1684187/pexels-photo-1684187.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # ===== HEALTH =====
    'hospital': 'https://images.pexels.com/photos/236380/pexels-photo-236380.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'nhs': 'https://images.pexels.com/photos/236380/pexels-photo-236380.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'doctor': 'https://images.pexels.com/photos/263402/pexels-photo-263402.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'flu': 'https://images.pexels.com/photos/3873179/pexels-photo-3873179.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'cold': 'https://images.pexels.com/photos/3873179/pexels-photo-3873179.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'misophonia': 'https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'noise': 'https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'weight loss': 'https://images.pexels.com/photos/208512/pexels-photo-208512.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'wegovy': 'https://images.pexels.com/photos/208512/pexels-photo-208512.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # ===== TECH =====
    'tiktok': 'https://images.pexels.com/photos/5081926/pexels-photo-5081926.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'social media': 'https://images.pexels.com/photos/607812/pexels-photo-607812.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'instagram': 'https://images.pexels.com/photos/607812/pexels-photo-607812.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'facebook': 'https://images.pexels.com/photos/607812/pexels-photo-607812.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'visas': 'https://images.pexels.com/photos/1098460/pexels-photo-1098460.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'amazon': 'https://images.pexels.com/photos/4482900/pexels-photo-4482900.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'gaming': 'https://images.pexels.com/photos/442576/pexels-photo-442576.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'call of duty': 'https://images.pexels.com/photos/442576/pexels-photo-442576.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # ===== BUSINESS =====
    'boxing day': 'https://images.pexels.com/photos/5632399/pexels-photo-5632399.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'sales': 'https://images.pexels.com/photos/5632399/pexels-photo-5632399.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'shopping': 'https://images.pexels.com/photos/5632399/pexels-photo-5632399.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'pension': 'https://images.pexels.com/photos/3943716/pexels-photo-3943716.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'finance': 'https://images.pexels.com/photos/3943716/pexels-photo-3943716.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'business': 'https://images.pexels.com/photos/936722/pexels-photo-936722.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    
    # ===== LOCAL/UK =====
    'village': 'https://images.pexels.com/photos/1029599/pexels-photo-1029599.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'england': 'https://images.pexels.com/photos/1029599/pexels-photo-1029599.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'british': 'https://images.pexels.com/photos/672532/pexels-photo-672532.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    'london': 'https://images.pexels.com/photos/672532/pexels-photo-672532.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
}

# Category fallback images (used when no keyword match)
CATEGORY_FALLBACK_IMAGES = {
    'UK News': [
        'https://images.pexels.com/photos/672532/pexels-photo-672532.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
        'https://images.pexels.com/photos/258117/pexels-photo-258117.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
        'https://images.pexels.com/photos/460672/pexels-photo-460672.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    ],
    'Local News': [
        'https://images.pexels.com/photos/1029599/pexels-photo-1029599.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
        'https://images.pexels.com/photos/164338/pexels-photo-164338.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
        'https://images.pexels.com/photos/280221/pexels-photo-280221.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    ],
    'Business': [
        'https://images.pexels.com/photos/936722/pexels-photo-936722.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
        'https://images.pexels.com/photos/3943716/pexels-photo-3943716.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    ],
    'Health': [
        'https://images.pexels.com/photos/236380/pexels-photo-236380.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
        'https://images.pexels.com/photos/263402/pexels-photo-263402.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    ],
    'Sports': [
        'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
        'https://images.pexels.com/photos/274422/pexels-photo-274422.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    ],
    'Tech': [
        'https://images.pexels.com/photos/546819/pexels-photo-546819.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
        'https://images.pexels.com/photos/1181675/pexels-photo-1181675.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=500&w=800',
    ],
}


def get_content_matched_image(title: str, content: str, category: str, used_images: Set[str]) -> Optional[str]:
    """
    Get an image that matches the article content.
    
    Priority:
    1. Match specific keywords in title
    2. Match specific keywords in content
    3. Use category fallback
    
    Args:
        title: Article title
        content: Article content/description
        category: Article category
        used_images: Set of already used image URLs to avoid duplicates
    
    Returns:
        Image URL or None if all options exhausted
    """
    title_lower = title.lower()
    content_lower = content.lower() if content else ''
    full_text = f"{title_lower} {content_lower}"
    
    # Try to match keywords - check title first (more specific)
    for keyword, image_url in CONTENT_IMAGE_MAP.items():
        if keyword in title_lower:
            if image_url not in used_images:
                logger.info(f"Content match for '{title[:30]}...' on keyword '{keyword}'")
                return image_url
    
    # Try content keywords
    for keyword, image_url in CONTENT_IMAGE_MAP.items():
        if keyword in content_lower:
            if image_url not in used_images:
                logger.info(f"Content match for '{title[:30]}...' on content keyword '{keyword}'")
                return image_url
    
    # Fallback to category images
    fallback_images = CATEGORY_FALLBACK_IMAGES.get(category, CATEGORY_FALLBACK_IMAGES.get('UK News', []))
    for image_url in fallback_images:
        if image_url not in used_images:
            logger.info(f"Category fallback for '{title[:30]}...' -> {category}")
            return image_url
    
    logger.warning(f"No unique image found for '{title[:30]}...'")
    return None


# Global instance for tracking used images across imports
_used_images_tracker: Set[str] = set()


def reset_used_images():
    """Reset the used images tracker (call at start of new import batch)"""
    global _used_images_tracker
    _used_images_tracker = set()


def get_image_for_article(title: str, content: str, category: str) -> Optional[str]:
    """
    Get an image for an article, tracking used images globally.
    
    Args:
        title: Article title
        content: Article content
        category: Article category
    
    Returns:
        Image URL
    """
    global _used_images_tracker
    
    image = get_content_matched_image(title, content, category, _used_images_tracker)
    if image:
        _used_images_tracker.add(image)
    return image
