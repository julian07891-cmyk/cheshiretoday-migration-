"""
Real News Feed Service for Cheshire Today
Fetches actual news from BBC, Sky News, and other UK sources via RSS feeds
"""

import os
import re
import httpx
import logging
import asyncio
import feedparser
from bs4 import BeautifulSoup
import requests

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import uuid4
import xml.etree.ElementTree as ET
from html import unescape


# --- Full article extraction helpers (auto) ---
def _clean_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()

def _extract_readable_text_from_html(html: str) -> str:
    """Best-effort readable text extractor.
    - removes scripts/styles/nav/footer
    - prefers <article>, then <main>, then body
    - joins paragraph-like blocks
    """
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    # Remove common clutter blocks if present
    for sel in ["header", "footer", "nav", "aside"]:
        for tag in soup.select(sel):
            tag.decompose()

    root = soup.find("article") or soup.find("main") or soup.body or soup
    if not root:
        return ""

    parts = []
    for el in root.find_all(["p", "h2", "h3", "li"]):
        t = _clean_ws(el.get_text(" ", strip=True))
        if len(t) >= 40:
            parts.append(t)

    # Fallback: just text
    if not parts:
        t = _clean_ws(root.get_text(" ", strip=True))
        return t

    text = "\n\n".join(parts)
    return text

def _try_fetch_full_article_text(url: str, timeout: int = 12) -> str:
    """Fetch article HTML and extract readable text (returns '' on failure)."""
    if not url:
        return ""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (CheshireTodayBot/1.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari"
        }
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if not r.ok:
            return ""
        ct = (r.headers.get("content-type") or "").lower()
        if "text/html" not in ct and "<html" not in (r.text[:500].lower()):
            return ""
        return _extract_readable_text_from_html(r.text)
    except Exception:
        return ""
# --- end full article extraction helpers ---

# Alias for RSS category guard
def category_guard(cat: str) -> str:
    return _rss_category_guard(cat)


logger = logging.getLogger(__name__)

# UK News RSS Feed Sources
RSS_FEEDS = {

    # --- AI / Tech (extra) ---
    'techcrunch': {
        'url': 'https://techcrunch.com/feed/',
        'source': 'TechCrunch',
        'category': 'Tech',
        'priority': 3
    },
    'arxiv_cs_ai': {
        'url': 'https://export.arxiv.org/rss/cs.AI',
        'source': 'arXiv',
        'category': 'Tech',
        'priority': 3
    },
    'theregister_headlines': {
        'url': 'https://www.theregister.com/headlines.atom',
        'source': 'The Register',
        'category': 'Tech',
        'priority': 3
    },

    # --- Money (extra) ---
    'moneysavingexpert': {
        'url': 'https://www.moneysavingexpert.com/news/feeds/news.rss',
        'source': 'MoneySavingExpert',
        'category': 'Money',
        'priority': 3
    },

    # --- Tax (extra) ---
    'hmrc_atom': {
        'url': 'https://www.gov.uk/government/organisations/hm-revenue-customs.atom',
        'source': 'GOV.UK',
        'category': 'Tax',
        'priority': 3
    },
    'hm_treasury_atom': {
        'url': 'https://www.gov.uk/government/organisations/hm-treasury.atom',
        'source': 'GOV.UK',
        'category': 'Money',
        'priority': 3
    },
    'ons_atom_official': {
        'url': 'https://www.gov.uk/government/organisations/office-for-national-statistics.atom',
        'source': 'GOV.UK',
        'category': 'Money',
        'priority': 3
    },


    # BBC News Feeds
    'bbc_uk': {
        'url': 'https://feeds.bbci.co.uk/news/uk/rss.xml',
        'source': 'BBC News',
        'category': 'UK News',
        'priority': 1
    },
    'bbc_england': {
        'url': 'https://feeds.bbci.co.uk/news/england/rss.xml',
        'source': 'BBC News',
        'category': 'Local News',
        'priority': 1
    },
    'bbc_business': {
        'url': 'https://feeds.bbci.co.uk/news/business/rss.xml',
        'source': 'BBC News',
        'category': 'Business',
        'priority': 2
    },

    # Money / Personal Finance (UK)
    'guardian_money': {
        'url': 'https://www.theguardian.com/uk/money/rss',
        'source': 'The Guardian',
        'category': 'Money',
        'priority': 2
    },
    'ft_personal_finance': {
        'url': 'https://www.ft.com/personal-finance?format=rss',
        'source': 'Financial Times',
        'category': 'Money',
        'priority': 2
    },

    # Property / Housing (UK)
        # Tax (UK)
    'hmrc_tax': {
        'url': 'https://www.gov.uk/government/organisations/hm-revenue-customs.atom',
        'source': 'GOV.UK (HMRC)',
        'category': 'Tax',
        'priority': 2
    },

'guardian_housing': {
        'url': 'https://www.theguardian.com/housing-network/rss',
        'source': 'The Guardian',
        'category': 'Property',
        'priority': 2
    },
    'ft_property': {
        'url': 'https://www.ft.com/property-sector?format=rss',
        'source': 'Financial Times',
        'category': 'Property',
        'priority': 2
    },

    'bbc_technology': {
        'url': 'https://feeds.bbci.co.uk/news/technology/rss.xml',
        'source': 'BBC News',
        'category': 'Tech',
        'priority': 2
    },
    'bbc_health': {
        'url': 'https://feeds.bbci.co.uk/news/health/rss.xml',
        'source': 'BBC News',
        'category': 'Health',
        'priority': 2
    },
    'bbc_politics': {
        'url': 'https://feeds.bbci.co.uk/news/politics/rss.xml',
        'source': 'BBC News',
        'category': 'UK News',
        'priority': 1
    },
    
    # Sky News Feeds
    'sky_uk': {
        'url': 'https://feeds.skynews.com/feeds/rss/uk.xml',
        'source': 'Sky News',
        'category': 'UK News',
        'priority': 1
    },
    'sky_business': {
        'url': 'https://feeds.skynews.com/feeds/rss/business.xml',
        'source': 'Sky News',
        'category': 'Business',
        'priority': 2
    },
    'sky_technology': {
        'url': 'https://feeds.skynews.com/feeds/rss/technology.xml',
        'source': 'Sky News',
        'category': 'Tech',
        'priority': 2
    },
    
    # Science
    'bbc_science': {
        'url': 'https://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
        'source': 'BBC News',
        'category': 'Science',
        'priority': 2
    },
    'guardian_science': {
        'url': 'https://www.theguardian.com/science/rss',
        'source': 'The Guardian',
        'category': 'Science',
        'priority': 2
    },
    
    # Entertainment
    'bbc_entertainment': {
        'url': 'https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml',
        'source': 'BBC News',
        'category': 'Entertainment',
        'priority': 2
    },
    'sky_entertainment': {
        'url': 'https://feeds.skynews.com/feeds/rss/entertainment.xml',
        'source': 'Sky News',
        'category': 'Entertainment',
        'priority': 2
    },
    
    # Guardian UK
    'guardian_uk': {
        'url': 'https://www.theguardian.com/uk-news/rss',
        'source': 'The Guardian',
        'category': 'UK News',
        'priority': 1
    },
    
    # Sports
    'bbc_sport': {
        'url': 'https://feeds.bbci.co.uk/sport/rss.xml',
        'source': 'BBC Sport',
        'category': 'Sports',
        'priority': 2
    },
    'sky_sports': {
        'url': 'https://www.skysports.com/rss/12040',
        'source': 'Sky Sports',
        'category': 'Sports',
        'priority': 2
    },
    
    # ====================================
    # LOCAL CHESHIRE NEWS FEEDS (Priority)
    # ====================================
    'cheshire_live': {
        'url': 'https://www.cheshire-live.co.uk/news/?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,  # Highest priority for local news
        'is_local': True
    },
    'cheshire_live_chester': {
        'url': 'https://www.cheshire-live.co.uk/news/chester-cheshire-news/?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'chester'
    },
    'cheshire_live_crewe': {
        'url': 'https://www.cheshire-live.co.uk/all-about/crewe?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'crewe'
    },
    'cheshire_live_nantwich': {
        'url': 'https://www.cheshire-live.co.uk/all-about/nantwich?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'crewe'  # Nantwich is part of Crewe area
    },
    'cheshire_live_macclesfield': {
        'url': 'https://www.cheshire-live.co.uk/all-about/macclesfield?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'macclesfield'
    },
    'cheshire_live_congleton': {
        'url': 'https://www.cheshire-live.co.uk/all-about/congleton?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'macclesfield'  # Congleton is part of Macclesfield area
    },
    'cheshire_live_northwich': {
        'url': 'https://www.cheshire-live.co.uk/all-about/northwich?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'northwich'
    },
    'cheshire_live_winsford': {
        'url': 'https://www.cheshire-live.co.uk/all-about/winsford?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'northwich'  # Winsford is part of Northwich area
    },
    'cheshire_live_middlewich': {
        'url': 'https://www.cheshire-live.co.uk/all-about/middlewich?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'northwich'  # Middlewich is part of Northwich area
    },
    'cheshire_live_wilmslow': {
        'url': 'https://www.cheshire-live.co.uk/all-about/wilmslow?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'wilmslow'
    },
    'cheshire_live_alderley_edge': {
        'url': 'https://www.cheshire-live.co.uk/all-about/alderley-edge?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'wilmslow'  # Alderley Edge is part of Wilmslow area
    },
    'cheshire_live_knutsford': {
        'url': 'https://www.cheshire-live.co.uk/all-about/knutsford?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'knutsford'
    },
    'cheshire_live_ellesmere_port': {
        'url': 'https://www.cheshire-live.co.uk/all-about/ellesmere-port?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'chester'  # Ellesmere Port is part of Chester area
    },
    'cheshire_live_runcorn': {
        'url': 'https://www.cheshire-live.co.uk/all-about/runcorn?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'warrington'  # Runcorn is close to Warrington
    },
    'cheshire_live_widnes': {
        'url': 'https://www.cheshire-live.co.uk/all-about/widnes?service=rss',
        'source': 'Cheshire Live',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'warrington'  # Widnes is close to Warrington
    },
    'warrington_guardian': {
        'url': 'https://www.warringtonguardian.co.uk/news/rss/',
        'source': 'Warrington Guardian',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'warrington'
    },
    'chester_standard': {
        'url': 'https://www.chesterstandard.co.uk/news/rss/',
        'source': 'Chester Standard',
        'category': 'Local News',
        'priority': 0,
        'is_local': True,
        'location': 'chester'
    },
    # --- Business/Finance/Tech (extra via RSS sources expansion) ---
    'companies_house_atom': {
        'url': 'https://www.gov.uk/government/organisations/companies-house.atom',
        'source': 'GOV.UK',
        'category': 'Business',
        'priority': 3
    },
    'ons_atom': {
        'url': 'https://www.gov.uk/government/organisations/office-for-national-statistics.atom',
        'source': 'GOV.UK',
        'category': 'Business',
        'priority': 3
    },
    'gn_uk_startups_vc': {
        'url': 'https://news.google.com/rss/search?q=(UK%20startup%20OR%20startups%20OR%20venture%20capital%20OR%20VC%20OR%20funding%20OR%20seed%20round%20OR%20Series%20A)%20when%3A14d&hl=en-GB&gl=GB&ceid=GB%3Aen',
        'source': 'Google News',
        'category': 'Business',
        'priority': 3
    },
    'gn_uk_fintech_banking': {
        'url': 'https://news.google.com/rss/search?q=(UK%20fintech%20OR%20banking%20OR%20challenger%20bank%20OR%20payments)%20when%3A14d&hl=en-GB&gl=GB&ceid=GB%3Aen',
        'source': 'Google News',
        'category': 'Money',
        'priority': 3
    },
    'gn_uk_housing_property': {
        'url': 'https://news.google.com/rss/search?q=(UK%20housing%20OR%20property%20market%20OR%20house%20prices%20OR%20rent%20rents)%20when%3A14d&hl=en-GB&gl=GB&ceid=GB%3Aen',
        'source': 'Google News',
        'category': 'Property',
        'priority': 3
    },
    'gn_uk_energy_bills': {
        'url': 'https://news.google.com/rss/search?q=(UK%20energy%20bills%20OR%20tariffs%20OR%20Ofgem%20OR%20price%20cap)%20when%3A14d&hl=en-GB&gl=GB&ceid=GB%3Aen',
        'source': 'Google News',
        'category': 'Money',
        'priority': 3
    },
    'gn_uk_cybersecurity': {
        'url': 'https://news.google.com/rss/search?q=(UK%20cybersecurity%20OR%20ransomware%20OR%20data%20breach%20OR%20NCSC)%20when%3A14d&hl=en-GB&gl=GB&ceid=GB%3Aen',
        'source': 'Google News',
        'category': 'Tech',
        'priority': 3
    },
    'gn_uk_ai_regulation': {
        'url': 'https://news.google.com/rss/search?q=(UK%20AI%20regulation%20OR%20artificial%20intelligence%20policy%20OR%20DSIT)%20when%3A14d&hl=en-GB&gl=GB&ceid=GB%3Aen',
        'source': 'Google News',
        'category': 'Tech',
        'priority': 3
    },

    # --- GOV.UK org feeds (Business/Tech) ---
    'govuk_dbit_atom': {
        'url': 'https://www.gov.uk/government/organisations/department-for-business-and-trade.atom',
        'source': 'GOV.UK',
        'category': 'Business',
        'priority': 3
    },
    'govuk_dsit_atom': {
        'url': 'https://www.gov.uk/government/organisations/department-for-science-innovation-and-technology.atom',
        'source': 'GOV.UK',
        'category': 'Tech',
        'priority': 3
    },
    'govuk_cma_atom': {
        'url': 'https://www.gov.uk/government/organisations/competition-and-markets-authority.atom',
        'source': 'GOV.UK',
        'category': 'Business',
        'priority': 3
    },
    'govuk_insolvency_atom': {
        'url': 'https://www.gov.uk/government/organisations/insolvency-service.atom',
        'source': 'GOV.UK',
        'category': 'Business',
        'priority': 3
    },
    'govuk_ipo_atom': {
        'url': 'https://www.gov.uk/government/organisations/intellectual-property-office.atom',
        'source': 'GOV.UK',
        'category': 'Business',
        'priority': 3
    },

}

# Cheshire-related keywords for filtering local news
# Priority 1: Core Cheshire areas (Macclesfield, Wilmslow, Knutsford and surrounding)
CHESHIRE_PRIORITY_KEYWORDS = [
    'macclesfield', 'wilmslow', 'knutsford', 'alderley edge', 'prestbury',
    'poynton', 'bollington', 'disley', 'handforth', 'congleton', 'alsager',
    'sandbach', 'holmes chapel', 'chelford', 'mobberley', 'ashley',
    'styal', 'dean row', 'lindow', 'great warford', 'nether alderley'
]

# Priority 2: Wider Cheshire areas
CHESHIRE_SECONDARY_KEYWORDS = [
    'warrington', 'northwich', 'chester', 'crewe', 'nantwich',
    'ellesmere port', 'runcorn', 'widnes', 'winsford', 'middlewich',
    'frodsham', 'helsby', 'tarporley', 'tattenhall', 'malpas',
    'audlem', 'bunbury', 'kelsall', 'tarvin'
]

# All Cheshire keywords combined
CHESHIRE_KEYWORDS = [
    'cheshire', *CHESHIRE_PRIORITY_KEYWORDS, *CHESHIRE_SECONDARY_KEYWORDS,
    'north west', 'northwest england', 'manchester', 'liverpool',
    'merseyside', 'greater manchester'
]

# Priority locations in order - 1 article from each for the top 4 slots
# These are grouped by area with surrounding towns included
# First match wins - order matters for overlapping areas
PRIORITY_LOCATIONS = [
    {
        'name': 'macclesfield',
        'keywords': [
            'macclesfield', 'bollington', 'poynton', 'prestbury', 'disley', 
            'congleton', 'alsager', 'sandbach', 'holmes chapel', 'brereton',
            'goostrey', 'siddington', 'gawsworth', 'sutton', 'langley'
        ]
    },
    {
        'name': 'wilmslow',
        'keywords': [
            'wilmslow', 'handforth', 'styal', 'dean row', 'lindow', 
            'alderley edge', 'nether alderley', 'chelford', 'mobberley', 
            'ashley', 'hale barns', 'row of trees'
        ]
    },
    {
        'name': 'knutsford',
        'keywords': [
            'knutsford', 'great warford', 'tatton', 'rostherne', 'high legh', 
            'lower peover', 'over peover', 'plumley', 'tabley', 'mere', 'ollerton'
        ]
    },
    {
        'name': 'warrington',
        'keywords': [
            'warrington', 'lymm', 'grappenhall', 'stockton heath', 'appleton', 
            'culcheth', 'birchwood', 'padgate', 'woolston', 'penketh',
            # Surrounding towns that fall under Warrington area
            'runcorn', 'widnes', 'frodsham', 'helsby', 'moore', 'daresbury'
        ]
    },
    {
        'name': 'chester',
        'keywords': [
            'chester', 'hoole', 'upton', 'saltney', 'handbridge', 'boughton', 
            # Surrounding towns
            'ellesmere port', 'neston', 'parkgate', 'heswall', 'burton', 
            'tattenhall', 'farndon', 'malpas', 'tarvin', 'christleton',
            'waverton', 'guilden sutton', 'mickle trafford'
        ]
    },
    {
        'name': 'northwich',
        'keywords': [
            'northwich', 'winsford', 'middlewich', 'hartford', 'cuddington', 
            'davenham', 'lostock gralam', 'barnton', 'comberbach', 'great budworth',
            'rudheath', 'leftwich', 'sandiway', 'delamere'
        ]
    },
    {
        'name': 'crewe',
        'keywords': [
            'crewe', 'nantwich', 'audlem', 'shavington', 'haslington', 
            'wistaston', 'weston', 'wybunbury', 'willaston', 'stapeley',
            'hough', 'rope', 'woolstanwood'
        ]
    },
]

def get_article_priority_location(title: str, content: str = '') -> Optional[str]:
    """
    Get the specific priority location for an article.
    Returns the location name (e.g., 'macclesfield', 'wilmslow') or None if not a priority location.
    Uses word boundary matching to avoid false positives (e.g., 'chester' in 'manchester').
    """
    import re
    text = f"{title} {content}".lower(); cheshire_context = "cheshire" in text
    
    for location in PRIORITY_LOCATIONS:
        for keyword in location['keywords']:
            # Use word boundary regex to ensure exact word match
            # This prevents 'chester' matching 'manchester' or 'colchester'
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text) and cheshire_context:
                return location['name']
    return None

def is_priority_cheshire_article(title: str, content: str = '') -> bool:
    """Check if article is from priority Cheshire areas using word boundaries + Cheshire context."""
    import re
    text = f"{title} {content}".lower()
    cheshire_context = "cheshire" in text
    for keyword in CHESHIRE_PRIORITY_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text) and cheshire_context:
            return True
    return False

def is_secondary_cheshire_article(title: str, content: str = '') -> bool:
    """Check if article is from secondary Cheshire areas using word boundaries + Cheshire context."""
    import re
    text = f"{title} {content}".lower()
    cheshire_context = "cheshire" in text
    for keyword in CHESHIRE_SECONDARY_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text) and cheshire_context:
            return True
    return False

# Keyword-based category override rules
# If an article title/content contains these keywords, override its category
# More specific keywords should be used to avoid false positives

# Limit RSS categories to reduce noise + DB growth (monetisation-first)
ALLOWED_RSS_CATEGORIES = {"UK News", "Local News", "Business", "AI", "Tech", "Science", "Money", "Tax", "Property", "Property & Tax"}

def _rss_category_guard(cat: str) -> str:
    c = (cat or "").strip()
    return c if c in ALLOWED_RSS_CATEGORIES else "UK News"

CATEGORY_KEYWORD_OVERRIDES = {
    'Sports': [
        'football', 'rugby', 'cricket', 'tennis', 'golf', 'boxing', 'darts',
        'snooker', 'f1', 'formula 1', 'premier league', 'championship', 
        'champions league', 'uefa', 'fifa', 'world cup', 'olympics',
        'athletics', 'swimming', 'cycling', 'marathon', 'scored goal',
        'player signed', 'team manager', 'transfer window', 'injury update',
        'fa cup', 'league cup', 'playoff', 'relegation battle', 'promotion race',
        'manchester united', 'manchester city', 'liverpool fc', 'everton fc',
        'chester fc', 'macclesfield fc', 'warrington wolves', 'sale sharks'
    ],
    'Entertainment': [
        'celebrity news', 'actor reveals', 'actress says', 'film premiere', 'movie review',
        'cinema release', 'tv show', 'television series', 'netflix series', 'bbc iplayer',
        'strictly come dancing', 'x factor', 'britain\'s got talent', 'i\'m a celebrity',
        'eastenders spoiler', 'coronation street', 'emmerdale', 'hollyoaks',
        'concert tour', 'album release', 'grammy awards', 'brit awards', 'oscar nomination',
        'bafta winner', 'red carpet', 'film premiere', 'itv show', 'channel 4 documentary'
    ],
    'Science': [
        'scientific research', 'study finds', 'scientists discover', 'new discovery',
        'space mission', 'nasa announces', 'asteroid', 'planet discovered',
        'climate research', 'environmental study', 'species discovered',
        'dna research', 'genome study', 'medical breakthrough', 'physics research',
        'chemistry breakthrough', 'biology study', 'laboratory experiment',
        'archaeological dig', 'fossil discovery'
    ],
    'Education': [
        'school results', 'university admission', 'college funding', 'student protest',
        'teacher strike', 'ofsted report', 'gcse results', 'a-level results',
        'exam board', 'curriculum change', 'education minister', 'classroom shortage',
        'headteacher resigns', 'academy trust', 'sixth form college', 'nursery funding',
        'primary school ofsted', 'secondary school rating', 'grammar school debate',
        'scholarship programme', 'graduation ceremony'
    ],
    'Health': [
        'nhs crisis', 'nhs funding', 'hospital waiting', 'doctor shortage', 'nurse strike',
        'patient care', 'surgery cancelled', 'cancer treatment', 'diabetes care',
        'heart disease', 'mental health crisis', 'anxiety treatment', 'depression help',
        'therapy service', 'medical treatment', 'diagnosis delay', 'symptom checker',
        'vaccine rollout', 'vaccination programme', 'covid variant', 'flu outbreak',
        'infection control', 'a&e waiting', 'gp appointment', 'pharmacy closure',
        'prescription charge', 'waiting list crisis'
    ],
    'Tech': [
        'apple announces', 'apple releases', 'google launches', 'microsoft releases', 'amazon tech',
        'meta platform', 'facebook policy', 'twitter change', 'ai technology',
        'artificial intelligence', 'chatgpt update', 'robot technology', 'smartphone launch',
        'iphone release', 'iphone', 'android update', 'app store', 'software update',
        'cybersecurity breach', 'hacker attack', 'data breach', 'tech startup',
        'blockchain technology', 'cryptocurrency market', 'bitcoin price'
    ],
    'Money': [
        'inflation rate', 'interest rate decision', 'bank of england', 'budget announcement',
        'energy bills', 'energy price cap', 'ofgem', 'insurance', 'savings',
        'cost of living', 'interest rates', 'personal finance', 'household bills',
        'consumer spending', 'consumer confidence', 'mortgage rates', 'remortgage'
    ],
    'Tax': [
        'tax increase', 'tax bill', 'hmrc', 'self assessment', 'vat', 'national insurance',
        'tax return', 'fiscal drag', 'tax threshold', 'stamp duty', 'council tax'
    ],
    'Property': [
        'mortgage', 'mortgages', 'housing market', 'house prices', 'property market',
        'rent rises', 'rental market', 'landlord', 'tenant', 'housebuilding',
        'planning approval', 'affordable homes'
    ],
    'Business': [
        'stock market', 'ftse 100', 'shares tumble', 'investment fund', 'profit warning',
        'revenue growth', 'ceo resigns', 'company merger', 'acquisition deal',
        'bankruptcy filing', 'employment figures', 'unemployment rate',
        'job losses', 'redundancy plan', 'strike action', 'union dispute',
        'earnings', 'results', 'trading update', 'manufacturer', 'retailer',
        'supply chain', 'factory', 'startup funding', 'venture capital'
    ],
    'Weather': [
        'weather warning', 'storm warning', 'met office', 'snow forecast', 'flood warning',
        'heavy rain', 'strong winds', 'ice warning', 'thunderstorm', 'heatwave',
        'cold snap', 'weather alert', 'travel disruption due to weather'
    ]
}

# Categories that should NOT be overridden (preserve original RSS category)
PROTECTED_CATEGORIES = ['Weather', 'Local News']

# ============================================
# SPAM/PRODUCT/ADVERTISING FILTER
# Articles containing these patterns will be skipped
# ============================================
SPAM_KEYWORDS = [
    # Product reviews and deals
    'best deals', 'best prices', 'discount code', 'promo code', 'voucher code',
    'amazon deal', 'black friday', 'cyber monday', 'flash sale', 'limited offer',
    'buy now', 'shop now', 'order now', 'get yours', 'save money on',
    'cheapest price', 'price drop', 'on sale now', 'sale ends',
    'deal stack', 'deal alert', 'price slash', 'massive discount',
    
    # Product recommendations
    'best buys', 'top picks', 'must-have products', 'gift guide',
    'products we love', 'editor\'s choice products', 'sponsored products',
    'affiliate link', 'ad feature', 'paid partnership',
    'we earn a commission', 'affiliate commission',
    
    # Gadgets and tech products (advertising disguised as news)
    'gadget', 'reduced to £', 'reduced to $', 'now just £', 'now only £',
    'snapping up', 'shoppers snapping', 'shoppers rushing', 'flying off shelves',
    'selling fast', 'selling out fast', 'almost sold out',
    'argos deal', 'amazon shoppers', 'tesco shoppers', 'aldi shoppers',
    'asda shoppers', 'lidl shoppers', 'boots deal', 'currys deal',
    'blender', 'air fryer', 'vacuum cleaner', 'nutribullet', 'ninja',
    'dyson deal', 'shark deal', 'cheaper than', 'much cheaper',
    'fraction of the price', 'save over £', 'was £', 'now £',
    
    # Health/wellness products (usually ads)
    'cheaper than the osteopath', 'cheaper than physio', 'pain relief gadget',
    'massage gun', 'posture corrector', 'weight loss', 'fat burner',
    'miracle product', 'doctors hate', 'one weird trick',
    
    # Review articles that are essentially ads
    'review: best', 'best vacuum', 'best tv deals', 'best phone deals',
    'best laptop deals', 'best mattress', 'best air fryer', 'best coffee machine',
    'where to buy', 'buying guide', 'shopping guide',
    'kitchen gadget', 'home gadget', 'cleaning gadget',
    
    # Gambling/betting
    'free bet', 'betting odds', 'casino bonus', 'bet now', 'gambling offer',
    'free spins', 'bookmaker', 'odds boost',
    
    # Finance spam
    'claim your free', 'you could win', 'enter to win', 'giveaway alert',
    'exclusive offer', 'limited time only', 'act now', 'don\'t miss out',
    
    # Product launches that are basically ads
    'now available to buy', 'pre-order now', 'on sale today',
    'launches today', 'available now at',
    
    # Shopping/retail promotion language
    'shoppers are loving', 'customers are raving', 'rave reviews',
    'five-star reviews', '5-star reviews', 'highly rated',
    'i swear by this', 'game-changer product', 'life-changing gadget'
]

# Titles starting with these patterns are likely product articles
SPAM_TITLE_PATTERNS = [
    r'^best \d+ ',           # "Best 10 vacuum cleaners..."
    r'^top \d+ ',            # "Top 5 phones to buy..."
    r'^\d+ best ',           # "10 best TVs..."
    r'^the \d+ best ',       # "The 5 best laptops..."
    r'^where to buy ',       # "Where to buy..."
    r'^how to get ',         # "How to get free..."
    r'deals:',               # "Amazon deals: ..."
    r'sale:',                # "Sale: ..."
    r'review:.*best',        # "Review: Best vacuum..."
    r'reduced to £\d+',      # "...reduced to £14..."
    r'now (just |only )?£\d+', # "now just £29"
    r'was £\d+.*now £\d+',   # "was £50 now £20"
    r'save (over )?£\d+',    # "save £30" or "save over £50"
    r'under £\d+',           # "under £20"
    r'from £\d+',            # "from £10"
    r'shoppers (are )?(rushing|snapping|loving)', # "shoppers rushing to buy"
    r'gadget.*(cheaper|pain|relief)', # gadget articles
]


def is_spam_or_product_article(title: str, content: str) -> bool:
    text = f"{title} {content}".lower()

    # --- CONTEXT-AWARE RETAIL FILTER ---

    retail_brands = [
        "amazon","argos","tesco","aldi","asda","boots","john lewis","currys",
        "new balance","nike","adidas","skechers"
    ]

    product_terms = [
        "trainer","trainers","shoe","shoes","sneaker","sneakers",
        "air fryer","blender","vacuum","coffee machine","gadget"
    ]

    retail_language = [
        "reduced","price cut","sale","discount","now only","now just",
        "was £","save £","save over","half price","limited time","shoppers"
    ]

    # Only remove if retail language AND product context both appear
    if any(b in text for b in retail_brands) and any(r in text for r in retail_language):
        return True

    if any(p in text for p in product_terms) and any(r in text for r in retail_language):
        return True

    # price + retail context pattern
    if re.search(r"(£[0-9]+.*(sale|discount))|((sale|discount).*£[0-9]+)", text):
        return True

    return False


    # price + promo patterns (e.g., "£30 sale", "reduced by 40%", "was £90 now £45")
    if re.search(r"(was\s*£\d+\s*.*now\s*£\d+)|((now|only|just)\s*£\d+)|(save\s*(over\s*)?£\d+)|(reduced\s*by\s*\d+%)|(\d+%\s*off)", text):
        return True

    title_lower = title.lower()
    
    # Check for spam keywords
    for keyword in SPAM_KEYWORDS:
        if keyword.lower() in text:
            return True
    
    # Check title patterns
    for pattern in SPAM_TITLE_PATTERNS:
        if re.search(pattern, title_lower):
            return True
    
    return False


def get_category_override(title: str, content: str, original_category: str = None) -> str:
    """
    Check if article should have its category overridden based on keywords.
    Returns the new category name or None if no override.
    
    Uses smarter matching:
    - Weather keywords take priority
    - Protected categories are not overridden
    - Requires more specific phrase matches
    """
    # Don't override protected categories
    if original_category in PROTECTED_CATEGORIES:
        return None
    
    text = f"{title} {content}".lower()
    
    # Check Weather first (highest priority) - storm/weather articles should stay as UK News/Local News
    weather_keywords = CATEGORY_KEYWORD_OVERRIDES.get('Weather', [])
    for keyword in weather_keywords:
        if keyword.lower() in text:
            # Weather articles should NOT be categorized as Education just because they mention schools
            return None  # Keep original category
    
    # Check each category's keywords
    for category, keywords in CATEGORY_KEYWORD_OVERRIDES.items():
        if category == 'Weather':
            continue  # Already handled
        match_count = 0
        for keyword in keywords:
            if keyword.lower() in text:
                match_count += 1
        if match_count >= 2:
            return category
    
    return None


def _flatten_feed_groups(feeds: dict) -> dict:
    """Normalize feeds so every value is a single feed config dict.
    If a value is a list of feed dicts, expand into synthetic keys.
    """
    if not isinstance(feeds, dict):
        return feeds
    flat = {}
    for k, v in feeds.items():
        if isinstance(v, dict):
            flat[k] = v
        elif isinstance(v, list):
            for idx, sub in enumerate(v):
                if isinstance(sub, dict):
                    flat[f"{k}__{idx}"] = sub
        # ignore anything else
    return flat

class NewsFeedService:
    """Service to fetch and parse real news from RSS feeds"""
    
    def __init__(self):
        self.feeds = RSS_FEEDS
        self.feeds = _flatten_feed_groups(self.feeds)
        self.timeout = 15.0
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean up text"""
        if not text:
            return ""
        # Unescape HTML entities
        text = unescape(text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _extract_image_from_item(self, item: ET.Element, namespaces: dict) -> Optional[str]:
        """Extract image URL from RSS item"""
        # Try media:content first
        media_content = item.find('.//media:content', namespaces)
        if media_content is not None:
            url = media_content.get('url')
            if url:
                return url
        
        # Try media:thumbnail
        media_thumb = item.find('.//media:thumbnail', namespaces)
        if media_thumb is not None:
            url = media_thumb.get('url')
            if url:
                return url
        
        # Try enclosure (more permissive - check URL for image extensions)
        enclosure = item.find('enclosure')
        if enclosure is not None:
            url = enclosure.get('url', '') or ''
            enc_type = enclosure.get('type', '') or ''
            enc_type = enc_type.lower()

            # Accept if type contains 'image' OR URL looks like an image
            looks_like_image = any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])
            known_img_hosts = any(h in url.lower() for h in ['i2-prod', 'ichef', 'guim', 'static', 'cdn'])

            if url and ('image' in enc_type or looks_like_image or known_img_hosts):
                return url

        # Try to find image in description
        description = item.find('description')
        if description is not None and description.text:
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description.text)
            if img_match:
                return img_match.group(1)
        
        return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse RSS date to ISO format"""
        if not date_str:
            return datetime.now(timezone.utc)
        
        # Common RSS date formats
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%d %b %Y %H:%M:%S %z',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        # Fallback to current time
        return datetime.now(timezone.utc)
    
    def _is_cheshire_related(self, title: str, description: str) -> bool:
        """Strict local check for genuine Cheshire civic/community relevance."""
        text = f"{title} {description}".lower()

        place_terms = [
            "cheshire", "warrington", "chester", "wilmslow", "knutsford",
            "macclesfield", "crewe", "nantwich", "northwich", "winsford",
            "congleton", "sandbach", "middlewich", "frodsham", "runcorn",
            "ellesmere port", "halton", "jodrell bank", "davesbury", "darebury"
        ]
        local_context_terms = [
            "council", "planning", "application", "approved", "refused", "scheme",
            "development", "homes", "housing", "school", "college", "community",
            "charity", "funding", "partnership", "road", "traffic", "m6", "m56",
            "station", "police", "court", "hospital", "nhs", "business park",
            "visitor attraction", "cafe", "restaurant", "shop", "town centre",
            "borough", "ward", "election", "committee", "consultation"
        ]
        non_local_noise = [
            "martin lewis", "hmrc", "tax-free", "energy price cap", "budget",
            "mortgage rate", "credit score", "iphone", "chatgpt", "anthropic",
            "dubai", "iran", "trump", "apple", "google", "microsoft"
        ]

        has_place = any(term in text for term in place_terms)
        has_context = any(term in text for term in local_context_terms)
        has_noise = any(term in text for term in non_local_noise)

        return has_place and has_context and not has_noise
    
    async def fetch_feed(self, feed_key: str) -> List[Dict[str, Any]]:
        """Fetch and parse a single RSS feed"""
        feed_config = self.feeds.get(feed_key)
        if not feed_config:
            logger.error(f"Unknown feed: {feed_key}")
            return []
        
        url = feed_config['url']
        source = feed_config['source']
        default_category = feed_config['category']
        is_local_source = feed_config.get('is_local', False)  # Get from feed config
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self.timeout, follow_redirects=True)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {feed_key}: HTTP {response.status_code}")
                    return []
                
                # Try XML parsing first, fallback to feedparser for malformed feeds
                articles = []
                use_feedparser = False
                
                try:
                    # Parse XML with ElementTree
                    root = ET.fromstring(response.content)
                    
                    # Define namespaces for media elements
                    namespaces = {
                        'media': 'http://search.yahoo.com/mrss/',
                        'dc': 'http://purl.org/dc/elements/1.1/',
                        'content': 'http://purl.org/rss/1.0/modules/content/'
                    }
                    
                    items = root.findall('.//item')

                    # -------- Atom (<feed><entry>) support (GOV.UK etc.) --------
                    # Atom feeds use a default namespace, so plain './/entry' will return 0.
                    ATOM_NS = 'http://www.w3.org/2005/Atom'
                    atom_entries = root.findall(f'.//{{{ATOM_NS}}}entry')
                    if not items and atom_entries:
                        for entry in atom_entries:
                            try:
                                t = entry.find(f'{{{ATOM_NS}}}title')
                                title = self._clean_html(t.text if t is not None else '')
                                if not title:
                                    continue

                                s = entry.find(f'{{{ATOM_NS}}}summary')
                                summary = self._clean_html(s.text if s is not None else '')

                                # Prefer alternate HTML link
                                link = ''
                                for l in entry.findall(f'{{{ATOM_NS}}}link'):
                                    rel = (l.attrib.get('rel') or '').lower()
                                    href = l.attrib.get('href') or ''
                                    if rel == 'alternate' and href:
                                        link = href
                                        break
                                    if not link and href:
                                        link = href

                                u = entry.find(f'{{{ATOM_NS}}}updated')
                                pub_date = (u.text if u is not None else '') or ''
                                pub_iso = self._parse_date(pub_date)

                                # GOV.UK Atom doesn't reliably provide images; keep empty and let later logic handle it
                                image = None

                                category = default_category
                                is_local = self._is_cheshire_related(title, summary)
                                if is_local and default_category not in ['Sports', 'Tech']:
                                    category = 'Local News'

                                override_category = get_category_override(title, summary, default_category)
                                if override_category:
                                    category = override_category

                                feed_location = self.feeds.get(feed_key, {}).get('location')
                                detected_location = get_article_priority_location(title, summary)
                                article_location = feed_location or detected_location

                                article = {
                                    'id': str(uuid4()),
                                    'title': title,
                                    'content': summary,
                                    'summary': summary[:200] + '...' if len(summary) > 200 else summary,
                                    'source': source,
                                    'source_url': link,
                                    'category': category,
                                    'image': image,
                                    'publishedDate': pub_iso,
                                    'author': source,
                                    'is_local_source': is_local_source,
                                    'is_local': bool(is_local),
                                    'priority_location': article_location,
                                }
                                articles.append(article)
                            except Exception:
                                continue

                        # If Atom parsing produced articles, skip RSS <item> parsing below
                        if articles:
                            return articles
                    # -------- end Atom support --------


                    # -------- end Atom support --------


                    # Atom fallback (e.g. GOV.UK org feeds) use <entry> not <item>
                    if not items:
                        atom_ns = {'atom': 'http://www.w3.org/2005/Atom'}
                        entries = root.findall('.//atom:entry', atom_ns) or root.findall('.//entry')
                        for entry in entries:
                            try:
                                title_elem = entry.find('atom:title', atom_ns) or entry.find('title')
                                title = self._clean_html(title_elem.text if title_elem is not None else '')
                                if not title:
                                    continue

                                summary_elem = entry.find('atom:summary', atom_ns) or entry.find('summary')
                                content_elem = entry.find('atom:content', atom_ns) or entry.find('content')
                                raw_desc = ""
                                if summary_elem is not None and getattr(summary_elem, "text", None):
                                    raw_desc = summary_elem.text or ""
                                elif content_elem is not None and getattr(content_elem, "text", None):
                                    raw_desc = content_elem.text or ""
                                description = self._clean_html(raw_desc)

                                # SPAM FILTER
                                if is_spam_or_product_article(title, description):
                                    logger.debug(f"Skipping spam/product article: {title[:50]}...")
                                    continue

                                # Atom link is usually <link rel="alternate" href="..."/>
                                link = ""
                                link_elem = entry.find("atom:link[@rel='alternate']", atom_ns) or entry.find("link[@rel='alternate']")
                                if link_elem is None:
                                    link_elem = entry.find("atom:link", atom_ns) or entry.find("link")
                                if link_elem is not None:
                                    link = (link_elem.attrib.get("href") or link_elem.text or "").strip()

                                updated_elem = entry.find('atom:updated', atom_ns) or entry.find('updated')
                                published_elem = entry.find('atom:published', atom_ns) or entry.find('published')
                                date_str = ""
                                if updated_elem is not None and getattr(updated_elem, "text", None):
                                    date_str = updated_elem.text or ""
                                elif published_elem is not None and getattr(published_elem, "text", None):
                                    date_str = published_elem.text or ""
                                pub_date = date_str

                                image = None  # GOV.UK Atom typically doesn't include images

                                category = default_category
                                is_local = self._is_cheshire_related(title, description)
                                if is_local and default_category not in ['Sports', 'Tech']:
                                    category = 'Local News'

                                override_category = get_category_override(title, description, default_category)
                                if override_category:
                                    category = override_category

                                feed_location = self.feeds.get(feed_key, {}).get('location')
                                detected_location = get_article_priority_location(title, description)
                                article_location = feed_location or detected_location

                                article = {
                                    'id': str(uuid4()),
                                    'title': title,
                                    'content': description,
                                    'summary': description[:200] + '...' if len(description) > 200 else description,
                                    'source': source,
                                    'source_url': link,
                                    'category': category,
                                    'image': image,
                                    'publishedDate': self._parse_date(pub_date),
                                    'author': source,
                                    'is_local_source': is_local_source,
                                    'tags': [],
                                    'scope': 'uk',
                                }
                                if article_location:
                                    article['priority_location'] = article_location

                                articles.append(article)
                            except Exception as e:
                                logger.debug(f"Atom parse error for {feed_key}: {e}")
                                continue

                        # Atom parsed -> return and skip RSS item loop
                    if articles:
                        return articles

                    for item in items:
                        try:
                            title_elem = item.find('title')
                            title = self._clean_html(title_elem.text if title_elem is not None else '')
                            
                            if not title:
                                continue
                            
                            desc_elem = item.find('description')
                            description = self._clean_html(desc_elem.text if desc_elem is not None else '')
                            
                            # SPAM FILTER: Skip product/advertising articles
                            if is_spam_or_product_article(title, description):
                                logger.debug(f"Skipping spam/product article: {title[:50]}...")
                                continue
                            
                            link_elem = item.find('link')
                            link = link_elem.text if link_elem is not None else ''
                            
                            pub_date_elem = item.find('pubDate')
                            pub_date = pub_date_elem.text if pub_date_elem is not None else ''
                            
                            image = self._extract_image_from_item(item, namespaces)
                            
                            # Determine category based on content
                            category = default_category
                            
                            # Check if it's Cheshire-related for local news boost
                            is_local = self._is_cheshire_related(title, description)
                            if is_local and default_category not in ['Sports', 'Tech']:
                                category = 'Local News'
                            
                            # Apply keyword-based category override
                            override_category = get_category_override(title, description, default_category)
                    
                            if override_category:
                                category = override_category
                            
                            # Get location from feed config or detect from content
                            feed_location = self.feeds.get(feed_key, {}).get('location')
                            detected_location = get_article_priority_location(title, description)
                            
                            article_location = feed_location or detected_location
                            
                            
                            article = {
                                'id': str(uuid4()),
                                'title': title,
                                                                'content': description,
                                'summary': description[:200] + '...' if len(description) > 200 else description,
                                'source': source,
                                'source_url': link,
                                'link': link,
                                'url': link,
                                'category': category_guard(category),
                                'image': image,
                                'publishedDate': self._parse_date(pub_date),
                                'author': source,
                                'is_real_news': True,
                                'is_cheshire_related': is_local,
                                'is_local_source': is_local_source,  # From feed config
                                'tags': [source, category_guard(category)],
                                'created_at': datetime.now(timezone.utc).isoformat()
                            }
                            
                            # Add location if found
                            if article_location:
                                article['location'] = article_location
                                article['tags'].append(article_location.capitalize())
                            
                            article.setdefault('source', source)
                            article.setdefault('summary', (locals().get('summary') or locals().get('description') or '').strip())
                            articles.append(article)
                            
                        except Exception as e:
                            logger.error(f"Error parsing item from {feed_key}: {str(e)}")
                            continue
                
                except ET.ParseError as xml_error:
                    # XML parsing failed - use feedparser as fallback (more resilient to malformed feeds)
                    logger.warning(f"XML parsing failed for {feed_key}, using feedparser fallback: {str(xml_error)}")
                    use_feedparser = True
                
                # Feedparser fallback for malformed XML feeds
                if use_feedparser:
                    articles = await self._parse_with_feedparser(response.content, feed_key, source, default_category, is_local_source)
                
                logger.info(f"Fetched {len(articles)} articles from {feed_key} ({source})")
                return articles
                
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching {feed_key}")
            return []
        except Exception as e:
            logger.error(f"Error fetching {feed_key}: {str(e)}")
            return []
    
    async def _parse_with_feedparser(self, content: bytes, feed_key: str, source: str, default_category: str, is_local_source: bool = False) -> List[Dict[str, Any]]:
        """Parse RSS feed using feedparser (resilient to malformed XML)"""
        articles = []
        try:
            # feedparser is synchronous but handles malformed feeds gracefully
            feed = feedparser.parse(content)
            
            for entry in feed.entries:
                try:
                    title = self._clean_html(getattr(entry, 'title', ''))
                    if not title:
                        continue
                    
                    description = self._clean_html(getattr(entry, 'summary', '') or getattr(entry, 'description', ''))
                    
                    # SPAM FILTER: Skip product/advertising articles
                    if is_spam_or_product_article(title, description):
                        logger.debug(f"Skipping spam/product article: {title[:50]}...")
                        continue
                    
                    link = getattr(entry, 'link', '')
                    
                    # Parse publication date
                    pub_date = ''
                    if hasattr(entry, 'published'):
                        pub_date = entry.published
                    elif hasattr(entry, 'updated'):
                        pub_date = entry.updated
                    
                    # Extract image from feedparser entry
                    image = self._extract_image_from_feedparser_entry(entry)
                    
                    # Determine category
                    category = default_category
                    is_local = self._is_cheshire_related(title, description)
                    if is_local and default_category not in ['Sports', 'Tech']:
                        category = 'Local News'
                    
                    # Apply keyword-based category override
                    override_category = get_category_override(title, description, default_category)
                    if override_category:
                        category = override_category

                    # Final classification guard:
                    # - only keep Local News for genuinely Cheshire-related items
                    # - preserve Sports when sports signals are present
                    text_l = f"{title} {description}".lower()
                    sport_terms = (
                        "fc", "united", "city", "rovers", "wanderers", "athletic", "benfica",
                        "wales", "scotland", "play-off", "playoff", "goal", "equaliser",
                        "manager", "coach", "stadium", "match", "fixture", "league", "cup"
                    )
                    if category == "UK News" and any(t in text_l for t in sport_terms):
                        category = "Sports"
                    if category == "Local News" and not is_local:
                        category = "UK News"
                    
                    article = {
                        'id': str(uuid4()),
                        'title': title,
                                                'content': description,
                        'summary': description[:200] + '...' if len(description) > 200 else description,
                        'source': source,
                        'source_url': link,
                        'link': link,
                        'url': link,
                                'category': category_guard(category),
                                'image': image,
                        'publishedDate': self._parse_date(pub_date),
                        'author': source,
                        'is_real_news': True,
                        'is_cheshire_related': is_local,
                        'is_local_source': is_local_source,  # From feed config
                        'tags': [source, category_guard(category)],
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Add location tag if article is about a specific Cheshire location
                    location = get_article_priority_location(title, description)
                    if location:
                        article['location'] = location
                        article['tags'].append(location.capitalize())
                    
                    article.setdefault('source', source)
                    article.setdefault('summary', (locals().get('summary') or locals().get('description') or '').strip())
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error parsing feedparser entry from {feed_key}: {str(e)}")
                    continue
            
            logger.info(f"Feedparser successfully parsed {len(articles)} articles from {feed_key}")
            
        except Exception as e:
            logger.error(f"Feedparser error for {feed_key}: {str(e)}")
        
        return articles
    
    def _extract_image_from_feedparser_entry(self, entry) -> Optional[str]:
        """Extract image URL from feedparser entry"""
        # Try media_content first
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                url = media.get('url', '')
                if url and ('image' in media.get('type', '') or any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])):
                    return url
        
        # Try media_thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            for thumb in entry.media_thumbnail:
                url = thumb.get('url', '')
                if url:
                    return url
        
        # Try enclosures
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                url = enclosure.get('href', '') or enclosure.get('url', '')
                enc_type = (enclosure.get('type', '') or '').lower()

                if not url:
                    continue

                lower_url = url.lower()

                if (
                    "image" in enc_type
                    or any(ext in lower_url for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"])
                    or any(domain in lower_url for domain in ["i2-prod", "ichef", "guim", "cdn"])
                ):
                    return url

        # Try to find image in summary/description
        summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
        if summary:
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
            if img_match:
                return img_match.group(1)

        return None
    
    async def fetch_all_feeds(self) -> List[Dict[str, Any]]:
        """Fetch articles from all configured RSS feeds"""
        all_articles = []
        
        # Fetch all feeds concurrently
        tasks = [self.fetch_feed(feed_key) for feed_key in self.feeds.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Feed fetch error: {str(result)}")
        
        # Sort by date (newest first)
        all_articles.sort(key=lambda x: x.get('publishedDate', ''), reverse=True)
        
        logger.info(f"Total articles fetched from all feeds: {len(all_articles)}")
        return all_articles
    
    async def fetch_category_feeds(self, category: str) -> List[Dict[str, Any]]:
        """Fetch articles for a specific category"""
        category_feeds = [
            feed_key for feed_key, config in self.feeds.items() 
            if config['category'] == category
        ]
        
        if not category_feeds:
            return []
        
        all_articles = []
        tasks = [self.fetch_feed(feed_key) for feed_key in category_feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
        
        all_articles.sort(key=lambda x: x.get('publishedDate', ''), reverse=True)
        return all_articles
    
    async def fetch_local_news(self) -> List[Dict[str, Any]]:
        """Fetch news that's relevant to Cheshire/North West - prioritizes local feeds"""
        all_local_articles = []
        
        # PRIORITY 1: Fetch from dedicated LOCAL Cheshire feeds
        local_feed_keys = [
            'cheshire_live',
            'cheshire_live_chester', 
            'warrington_guardian',
            'chester_standard',
        ]
        
        for feed_key in local_feed_keys:
            if feed_key in self.feeds:
                articles = await self.fetch_feed(feed_key)
                # Mark all articles from local feeds as Cheshire-related
                for article in articles:
                    article['is_cheshire_related'] = True
                    article['is_local_feed'] = True
                all_local_articles.extend(articles)
        
        logger.info(f"Fetched {len(all_local_articles)} articles from local Cheshire feeds")
        
        # PRIORITY 2: Also check national feeds for Cheshire mentions
        uk_articles = await self.fetch_feed('bbc_uk')
        england_articles = await self.fetch_feed('bbc_england')
        guardian_articles = await self.fetch_feed('guardian_uk')
        sky_articles = await self.fetch_feed('sky_uk')
        
        national_articles = uk_articles + england_articles + guardian_articles + sky_articles
        
        # Filter national feeds for Cheshire-related articles
        cheshire_from_national = [
            article for article in national_articles 
            if article.get('is_cheshire_related', False)
        ]
        
        # Combine: Local feeds first, then Cheshire mentions from national
        all_local_articles.extend(cheshire_from_national)
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        for article in all_local_articles:
            title = article.get('title', '').lower().strip()
            if title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        # Sort by date (newest first)
        unique_articles.sort(key=lambda x: x.get('publishedDate', ''), reverse=True)
        
        logger.info(f"Total unique local/Cheshire articles: {len(unique_articles)}")
        return unique_articles
    
    async def fetch_local_feeds_only(self) -> List[Dict[str, Any]]:
        """Fetch ONLY from dedicated local Cheshire newspaper feeds - PRIORITIZES CHESHIRE LIVE"""
        cheshire_live_articles = []
        other_local_articles = []
        
        # Fetch Cheshire Live feeds first (highest priority)
        for feed_key in ['cheshire_live', 'cheshire_live_chester']:
            if feed_key in self.feeds:
                articles = await self.fetch_feed(feed_key)
                for article in articles:
                    article['is_cheshire_related'] = True
                    article['is_local_feed'] = True
                    article['feed_priority'] = 0  # Highest priority
                cheshire_live_articles.extend(articles)
        
        # Fetch other local feeds
        for feed_key in ['warrington_guardian', 'chester_standard']:
            if feed_key in self.feeds:
                articles = await self.fetch_feed(feed_key)
                for article in articles:
                    article['is_cheshire_related'] = True
                    article['is_local_feed'] = True
                    article['feed_priority'] = 1  # Lower priority
                other_local_articles.extend(articles)
        
        # Remove duplicates from Cheshire Live articles
        seen_titles = set()
        unique_cheshire = []
        for article in cheshire_live_articles:
            title_lower = article.get('title', '').lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_cheshire.append(article)
        
        # Add other articles that aren't duplicates of Cheshire Live
        unique_others = []
        for article in other_local_articles:
            title_lower = article.get('title', '').lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_others.append(article)
        
        # Sort each group by date (newest first)
        unique_cheshire.sort(key=lambda x: x.get('publishedDate', ''), reverse=True)
        unique_others.sort(key=lambda x: x.get('publishedDate', ''), reverse=True)
        
        # CHESHIRE LIVE FIRST, then others
        all_articles = unique_cheshire + unique_others
        
        logger.info(f"Local feeds: {len(unique_cheshire)} Cheshire Live + {len(unique_others)} other = {len(all_articles)} total")
        return all_articles


# Global instance
news_feed_service = NewsFeedService()


def fetch_full_article_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Try common article containers
        selectors = [
            "article",
            ".article-body",
            ".story-body",
            ".entry-content",
            ".post-content",
            "#main-content"
        ]

        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                paragraphs = content.find_all("p")
                full_text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40)
                if len(full_text) > 300:
                    return full_text

        return None

    except Exception:
        return None
