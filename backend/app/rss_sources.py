# RSS Feed Sources for Cheshire Today
#
# Categories must match frontend: all | local | uk | business | health
#
# Note: Many publisher RSS feeds contain only short snippets.
# We will fetch the linked article pages to extract fuller text when needed.

CHESHIRE_RSS_SOURCES = [
    # Core local publishers (already proven to return RSS)
    {
        "name": "Cheshire Live",
        "url": "https://www.cheshire-live.co.uk/?service=rss",
        "category": "local"
    },
    {
        "name": "Liverpool Echo",
        "url": "https://www.liverpoolecho.co.uk/?service=rss",
        "category": "local"
    },

    # BBC regional / national
    {
        "name": "BBC England",
        "url": "http://feeds.bbci.co.uk/news/england/rss.xml",
        "category": "uk"
    },
    {
        "name": "BBC UK",
        "url": "http://feeds.bbci.co.uk/news/uk/rss.xml",
        "category": "uk"
    },

    # Town-focused discovery feeds (reliable). We scrape linked articles for full detail.
    {
        "name": "Google News: Macclesfield",
        "url": "https://news.google.com/rss/search?q=Macclesfield%20Cheshire%20when%3A14d&hl=en-GB&gl=GB&ceid=GB%3Aen",
        "category": "local"
    },
    {
        "name": "Google News: Wilmslow",
        "url": "https://news.google.com/rss/search?q=Wilmslow%20Cheshire%20when%3A14d&hl=en-GB&gl=GB&ceid=GB%3Aen",
        "category": "local"
    },
    {
        "name": "Google News: Knutsford",
        "url": "https://news.google.com/rss/search?q=Knutsford%20Cheshire%20when%3A14d&hl=en-GB&gl=GB&ceid=GB%3Aen",
        "category": "local"
    },
    {
        "name": "Google News: Cheshire East",
        "url": "https://news.google.com/rss/search?q=%22Cheshire%20East%22%20Council%20when%3A30d&hl=en-GB&gl=GB&ceid=GB%3Aen",
        "category": "local"
    },
    {
        "name": "Google News: Cheshire West & Chester",
        "url": "https://news.google.com/rss/search?q=%22Cheshire%20West%20and%20Chester%22%20Council%20when%3A30d&hl=en-GB&gl=GB&ceid=GB%3Aen",
        "category": "local"
    },

    # Business (optional - add only if it actually returns RSS in your environment)
    # If your earlier Insider test returns HTML, we keep it OFF for now.
]

ALL_RSS_SOURCES = CHESHIRE_RSS_SOURCES

def get_rss_sources():
    return ALL_RSS_SOURCES

def get_sources_by_category(category: str):
    if not category or category == "all":
        return ALL_RSS_SOURCES
    return [s for s in ALL_RSS_SOURCES if s.get("category") == category]
