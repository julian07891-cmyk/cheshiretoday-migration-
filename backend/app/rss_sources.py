# RSS Feed Sources for Cheshire News - Comprehensive Coverage

# Define local source names for filtering
LOCAL_SOURCES = [
    "Chester Chronicle",
    "Manchester Evening News", 
    "Cheshire Live",
    "Wilmslow & Knutsford Guardian",
    "Wilmslow News",
    "Knutsford News", 
    "Alderley Edge News",
    "Macclesfield Express",
    "Warrington Guardian",
    "Crewe Chronicle",
    "Nantwich News",
    "Manchester Events",
    "Cheshire Events",
    "BBC England North West",
    "Manchester Business News",
]

# Define national source names
NATIONAL_SOURCES = [
    "BBC UK News",
    "BBC News",
    "The Guardian UK",
    "Sky News",
    "BBC Business",
    "Financial Times",
    "Business Weekly UK",
    "BBC Health",
    "NHS News",
    "BBC Tech",
    "Sky Tech",
    "BBC Weather",
    "Met Office",
    "BBC Science",
    "New Scientist",
    "Nature News",
    "BBC Entertainment",
    "Sky Entertainment",
    "Guardian Film",
    "BBC Education",
    "TES News",
    "Guardian Education",
    "BBC Sport",
    "Sky Sports",
]

CHESHIRE_RSS_SOURCES = [
    # Local News - Cheshire & Northwest
    {
        "name": "BBC England North West",
        "url": "http://feeds.bbci.co.uk/news/england/rss.xml",
        "category": "Local News",
        "is_local": True
    },
    {
        "name": "Chester Chronicle",
        "url": "https://www.chesterchronicle.co.uk/?service=rss",
        "category": "Local News",
        "is_local": True
    },
    {
        "name": "Manchester Evening News",
        "url": "https://www.manchestereveningnews.co.uk/?service=rss",
        "category": "Local News",
        "is_local": True
    },
    {
        "name": "Cheshire Live",
        "url": "https://www.cheshire-live.co.uk/?service=rss",
        "category": "Local News",
        "is_local": True
    },
    {
        "name": "Wilmslow & Knutsford Guardian",
        "url": "https://www.knutsfordguardian.co.uk/?service=rss",
        "category": "Local News",
        "is_local": True
    },
    {
        "name": "Wilmslow News",
        "url": "https://www.cheshire-live.co.uk/all-about/wilmslow?service=rss",
        "category": "Local News",
        "is_local": True
    },
    {
        "name": "Knutsford News",
        "url": "https://www.cheshire-live.co.uk/all-about/knutsford?service=rss",
        "category": "Local News",
        "is_local": True
    },
    {
        "name": "Alderley Edge News",
        "url": "https://www.cheshire-live.co.uk/all-about/alderley-edge?service=rss",
        "category": "Local News",
        "is_local": True
    },
    {
        "name": "Macclesfield Express",
        "url": "https://www.macclesfield-express.co.uk/?service=rss",
        "category": "Local News",
        "is_local": True
    },
    
    # UK News (National)
    {
        "name": "BBC UK News",
        "url": "http://feeds.bbci.co.uk/news/uk/rss.xml",
        "category": "UK News",
        "is_local": False
    },
    {
        "name": "The Guardian UK",
        "url": "https://www.theguardian.com/uk/rss",
        "category": "UK News",
        "is_local": False
    },
    
    # Business & Finance
    {
        "name": "BBC Business",
        "url": "http://feeds.bbci.co.uk/news/business/rss.xml",
        "category": "Business",
        "is_local": False
    },
    {
        "name": "Financial Times",
        "url": "https://www.ft.com/?format=rss",
        "category": "Finance",
        "is_local": False
    },
    {
        "name": "Business Weekly UK",
        "url": "https://www.businessweekly.co.uk/rss",
        "category": "Business",
        "is_local": False
    },
    {
        "name": "Manchester Business News",
        "url": "https://www.insider.co.uk/news/?service=rss",
        "category": "Business",
        "is_local": True
    },
    
    # Technology
    {
        "name": "BBC Technology",
        "url": "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "category": "Tech",
        "is_local": False
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "category": "Tech",
        "is_local": False
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "category": "Tech",
        "is_local": False
    },
    
    # Sports
    {
        "name": "BBC Sport",
        "url": "http://feeds.bbci.co.uk/sport/rss.xml",
        "category": "Sports",
        "is_local": False
    },
    {
        "name": "Sky Sports News",
        "url": "https://www.skysports.com/rss/12040",
        "category": "Sports",
        "is_local": False
    },
    {
        "name": "Manchester United News",
        "url": "https://www.manutd.com/en/news.rss",
        "category": "Sports",
        "is_local": True
    },
    {
        "name": "Manchester City News",
        "url": "https://www.mancity.com/news.rss",
        "category": "Sports",
        "is_local": True
    },
    
    # Health & Wellbeing
    {
        "name": "BBC Health",
        "url": "http://feeds.bbci.co.uk/news/health/rss.xml",
        "category": "Health",
        "is_local": False
    },
    {
        "name": "NHS News",
        "url": "https://www.nhs.uk/feeds/news.xml",
        "category": "Health",
        "is_local": False
    },
    
    # Community & Lifestyle
    {
        "name": "The Guardian Lifestyle",
        "url": "https://www.theguardian.com/uk/lifeandstyle/rss",
        "category": "Community",
        "is_local": False
    },
    
    # Food & Dining
    {
        "name": "BBC Food",
        "url": "http://feeds.bbci.co.uk/food/rss.xml",
        "category": "Food",
        "is_local": False
    },
    {
        "name": "Manchester Food & Drink",
        "url": "https://www.manchestereveningnews.co.uk/whats-on/food-drink-news/?service=rss",
        "category": "Food",
        "is_local": True
    },
    
    # Weather
    {
        "name": "Met Office North West",
        "url": "https://www.metoffice.gov.uk/public/data/PWSCache/WarningsRSS/Region/nw",
        "category": "Weather",
        "is_local": True
    },
    
    # Events & Entertainment
    {
        "name": "Manchester Events",
        "url": "https://www.manchestereveningnews.co.uk/whats-on/?service=rss",
        "category": "Events",
        "is_local": True
    },
    {
        "name": "Cheshire Events",
        "url": "https://www.cheshire-live.co.uk/whats-on/?service=rss",
        "category": "Events",
        "is_local": True
    },
    
    # Science
    {
        "name": "BBC Science",
        "url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "category": "Science",
        "is_local": False
    },
    {
        "name": "New Scientist",
        "url": "https://www.newscientist.com/feed/home/?cmpid=RSS",
        "category": "Science",
        "is_local": False
    },
    {
        "name": "Nature News",
        "url": "http://feeds.nature.com/nature/rss/current",
        "category": "Science",
        "is_local": False
    },
    
    # Entertainment
    {
        "name": "BBC Entertainment",
        "url": "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        "category": "Entertainment",
        "is_local": False
    },
    {
        "name": "Sky Entertainment",
        "url": "https://feeds.skynews.com/feeds/rss/entertainment.xml",
        "category": "Entertainment",
        "is_local": False
    },
    {
        "name": "Guardian Film",
        "url": "https://www.theguardian.com/film/rss",
        "category": "Entertainment",
        "is_local": False
    },
    
    # Education
    {
        "name": "BBC Education",
        "url": "http://feeds.bbci.co.uk/news/education/rss.xml",
        "category": "Education",
        "is_local": False
    },
    {
        "name": "TES News",
        "url": "https://www.tes.com/news/rss.xml",
        "category": "Education",
        "is_local": False
    },
    {
        "name": "Guardian Education",
        "url": "https://www.theguardian.com/education/rss",
        "category": "Education",
        "is_local": False
    },
]

# Golden Triangle specific sources (Cheshire, Manchester, Liverpool area)
GOLDEN_TRIANGLE_SOURCES = [
    {
        "name": "Liverpool Echo",
        "url": "https://www.liverpoolecho.co.uk/?service=rss",
        "category": "Local News"
    },
    {
        "name": "North West Business Insider",
        "url": "https://www.insider.co.uk/news/north-west/?service=rss",
        "category": "Business"
    },
    {
        "name": "Greater Manchester News",
        "url": "https://www.manchestereveningnews.co.uk/news/greater-manchester-news/?service=rss",
        "category": "Local News"
    },
]

# Combine all sources
ALL_RSS_SOURCES = CHESHIRE_RSS_SOURCES + GOLDEN_TRIANGLE_SOURCES

def get_rss_sources():
    """Get all configured RSS sources"""
    return ALL_RSS_SOURCES

def get_sources_by_category(category):
    """Get RSS sources filtered by category"""
    if category == 'all':
        return ALL_RSS_SOURCES
    return [source for source in ALL_RSS_SOURCES if source['category'] == category]

def get_sources_by_region(region='all'):
    """Get RSS sources filtered by region"""
    if region == 'cheshire':
        return [s for s in ALL_RSS_SOURCES if 'cheshire' in s['name'].lower() or 'chester' in s['name'].lower()]
    elif region == 'manchester':
        return [s for s in ALL_RSS_SOURCES if 'manchester' in s['name'].lower()]
    elif region == 'golden_triangle':
        return GOLDEN_TRIANGLE_SOURCES
    return ALL_RSS_SOURCES

def get_category_list():
    """Get list of all available categories"""
    categories = set()
    for source in ALL_RSS_SOURCES:
        categories.add(source['category'])
    return sorted(list(categories))