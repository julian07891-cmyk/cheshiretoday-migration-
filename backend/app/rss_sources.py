# RSS Feed Sources for Cheshire Today
#
# Categories must match frontend: all | local | uk | business | health
#
# Note: Many publisher RSS feeds contain only short snippets.
# We will fetch the linked article pages to extract fuller text when needed.

CHESHIRE_RSS_SOURCES = [
    {
        "name": 'Chester Standard',
        "url": 'https://www.chesterstandard.co.uk/news/rss/',
        "category": 'local'
    },

    {
        "name": 'Warrington Guardian',
        "url": 'https://www.warringtonguardian.co.uk/news/rss/',
        "category": 'local'
    },

    {
        "name": 'Cheshire Live',
        "url": 'https://www.cheshire-live.co.uk/?service=rss',
        "category": 'local'
    },
    # {
#         "name": 'Liverpool Echo',
#         "url": 'https://www.liverpoolecho.co.uk/?service=rss',
#         "category": 'local'
#     },
    # {        # DISABLED_FOR_RATIO
        # "name": 'BBC England',
        # "url": 'http://feeds.bbci.co.uk/news/england/rss.xml',        # "category": 'uk'    # },    # {
        # DISABLED_FOR_RATIO
        # "name": 'BBC UK',
        # "url": 'http://feeds.bbci.co.uk/news/uk/rss.xml',
        # "category": 'uk'
    # },
    # {
        # "name": 'Google News: Macclesfield',
        # "url": 'https://news.google.com/rss/search?q=Macclesfield%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        # "category": 'local'
    # },
    # {
        # "name": 'Google News: Wilmslow',
        # "url": 'https://news.google.com/rss/search?q=Wilmslow%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        # "category": 'local'
    # },
    # {
        # "name": 'Google News: Knutsford',
        # "url": 'https://news.google.com/rss/search?q=Knutsford%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        # "category": 'local'
    # },
    # {
        # "name": 'Google News: Cheshire East',
        # "url": 'https://news.google.com/rss/search?q=%22Cheshire%20East%22%20Council%20when%3A30d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        # "category": 'local'
    # },
    # {
        # "name": 'Google News: Cheshire West & Chester',
        # "url": 'https://news.google.com/rss/search?q=%22Cheshire%20West%20and%20Chester%22%20Council%20when%3A30d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        # "category": 'local'
    # },
    # {
        # "name": 'BBC Business',
        # "url": 'http://feeds.bbci.co.uk/news/business/rss.xml',
        # "category": 'business'
    # },
    # {
        # "name": 'Guardian Business',
        # "url": 'https://www.theguardian.com/uk/business/rss',
        # "category": 'business'
    # },
    # {
        # "name": 'Guardian Money',
        # "url": 'https://www.theguardian.com/money/rss',
        # "category": 'business'
    # },
    # {
        # "name": 'BBC Technology',
        # "url": 'http://feeds.bbci.co.uk/news/technology/rss.xml',
        # "category": 'business'
    # },
    # {
        # "name": 'Ars Technica',
        # "url": 'http://feeds.arstechnica.com/arstechnica/index',
        # "category": 'business'
    # },
    # {
        # DISABLED_FOR_RATIO
        # "name": 'Sky News UK',
        # "url": 'https://feeds.skynews.com/feeds/rss/uk.xml',
        # "category": 'uk'
    # },
    # {
        # "name": 'Sky News Business',
        # "url": 'https://feeds.skynews.com/feeds/rss/business.xml',
        # "category": 'business'
    # },
    # {
        # "name": 'The Guardian Technology',
        # "url": 'https://www.theguardian.com/uk/technology/rss',
        # "category": 'business'
    # },
    # {
        # DISABLED_FOR_RATIO
        # "name": 'The Guardian UK News',
        # "url": 'https://www.theguardian.com/uk-news/rss',
        # "category": 'uk'
    # },
    {
        "name": 'Google News: Crewe',
        "url": 'https://news.google.com/rss/search?q=Crewe%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        "category": 'local'
    },
    {
        "name": 'Google News: Chester',
        "url": 'https://news.google.com/rss/search?q=Chester%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        "category": 'local'
    },
    {
        "name": 'Google News: Warrington',
        "url": 'https://news.google.com/rss/search?q=Warrington%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        "category": 'local'
    },
    {
        "name": 'Google News: Northwich',
        "url": 'https://news.google.com/rss/search?q=Northwich%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        "category": 'local'
    },
    {
        "name": 'Google News: Nantwich',
        "url": 'https://news.google.com/rss/search?q=Nantwich%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        "category": 'local'
    },
    {
        "name": 'Google News: Congleton',
        "url": 'https://news.google.com/rss/search?q=Congleton%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        "category": 'local'
    },
    {
        "name": 'Google News: Winsford',
        "url": 'https://news.google.com/rss/search?q=Winsford%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        "category": 'local'
    },
    {
        "name": 'Google News: Ellesmere Port',
        "url": 'https://news.google.com/rss/search?q=Ellesmere%20Port%20Cheshire%20%28council%20OR%20planning%20OR%20consultation%20OR%20regeneration%20OR%20investment%20OR%20jobs%20OR%20business%20OR%20housing%20OR%20transport%20OR%20rail%20OR%20roadworks%20OR%20school%20OR%20nhs%20OR%20clinic%20OR%20gp%20OR%20festival%20OR%20opening%29%20when%3A14d%20-police%20-cctv%20-appeal%20-assault%20-death%20-dead%20-died%20-crash%20-collision%20-road%20-lane%20-closure%20-cordon%20-arrest%20-charged%20-court%20-trial%20-sentenced%20-jailed%20-burglary%20-robbery%20-stabbing%20-shooting%20-rape&hl=en-GB&gl=GB&ceid=GB%3Aen',
        "category": 'local'
    },
]

ALL_RSS_SOURCES = CHESHIRE_RSS_SOURCES

def get_rss_sources():
    return ALL_RSS_SOURCES

def get_sources_by_category(category: str):
    if not category or category == "all":
        return ALL_RSS_SOURCES
    return [s for s in ALL_RSS_SOURCES if s.get("category") == category]
