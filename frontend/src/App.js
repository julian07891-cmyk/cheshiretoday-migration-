import React, { useState, useEffect, useRef, lazy, Suspense, useCallback, useMemo } from 'react';
import './App.css';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import { BrowserRouter, Routes, Route, useParams, useNavigate, Navigate, useLocation, Link } from 'react-router-dom';

// Critical components - load immediately
import NewsHeader from './components/NewsHeader';
import HeroArticle from './components/HeroArticle';
import CompactArticleCard from './components/CompactArticleCard';
import HomeSkeleton from './components/HomeSkeleton';

// Lazy load non-critical components to reduce initial bundle
const TrendingSidebar = lazy(() => import('./components/TrendingSidebar'));
const NewsFooter = lazy(() => import('./components/NewsFooter'));
const FestiveTheme = lazy(() => import('./components/FestiveTheme'));
const SubscribeSection = lazy(() => import('./components/SubscribeSection'));
const JobBoardBanner = lazy(() => import('./components/JobBoardBanner'));
const JobsWidget = lazy(() => import('./components/JobsWidget').then(m => ({ default: m.JobsWidget })));
const JobsInlineBanner = lazy(() => import('./components/JobsWidget').then(m => ({ default: m.JobsInlineBanner })));

// Import SubscribeInlineBanner directly (not lazy) to avoid loading issues
import { SubscribeInlineBanner } from './components/JobsWidget';
const BreakingNewsTicker = lazy(() => import('./components/BreakingNewsTicker'));
const RelatedArticles = lazy(() => import('./components/RelatedArticles'));
const AdminDashboard = lazy(() => import('./components/AdminDashboard'));
const NewsletterPopup = lazy(() => import('./components/NewsletterPopup'));
const SocialShare = lazy(() => import('./components/SocialShare'));
const PrivacyPolicy = lazy(() => import('./components/PrivacyPolicy'));
const TermsOfService = lazy(() => import('./components/TermsOfService'));
const AffiliateDisclosure = lazy(() => import('./components/AffiliateDisclosure'));
const MostReadWidget = lazy(() => import('./components/MostReadWidget'));
const PushNotificationButton = lazy(() => import('./components/PushNotificationButton'));
const ShareAlertsButton = lazy(() => import('./components/ShareAlertsButton'));
const BottomNav = lazy(() => import('./components/BottomNav'));
const CategoryTabs = lazy(() => import('./components/CategoryTabs'));
const CommentsSection = lazy(() => import('./components/CommentsSection'));
const NewsletterPreferences = lazy(() => import('./components/NewsletterPreferences'));
const JobBoard = lazy(() => import('./components/JobBoard'));
const PostJob = lazy(() => import('./components/PostJob'));
const PaymentSuccess = lazy(() => import('./components/PaymentSuccess'));
const MobileSearch = lazy(() => import('./components/MobileSearch'));
const MobileMenu = lazy(() => import('./components/MobileMenu'));
const UnsubscribePage = lazy(() => import('./components/UnsubscribePage'));
const PreferencesPage = lazy(() => import('./components/PreferencesPage'));

// Lazy load affiliate widgets
const AffiliateWidgetSidebar = lazy(() => import('./components/AffiliateWidgets').then(m => ({ default: m.AffiliateWidgetSidebar })));
const AffiliateWidgetInline = lazy(() => import('./components/AffiliateWidgets').then(m => ({ default: m.AffiliateWidgetInline })));
const AffiliateWidgetEndArticle = lazy(() => import('./components/AffiliateWidgets').then(m => ({ default: m.AffiliateWidgetEndArticle })));
const AffiliateWidgetMobile = lazy(() => import('./components/AffiliateWidgets').then(m => ({ default: m.AffiliateWidgetMobile })));

// Import product data for ArticlePage affiliate widget coordination
import { SAMPLE_PRODUCTS, fetchDatabaseProducts } from './components/AffiliateWidgets';

// Random promo widget for between article sections
const RandomPromoWidget = lazy(() => import('./components/RandomPromoWidget'));
import { PromoWidgetProvider } from './components/RandomPromoWidget';

import { ThemeProvider } from './contexts/ThemeContext';
import { categories } from './mockData';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './components/ui/dialog';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Clock, User, Share2, Loader2, Settings, BookOpen, MapPin, Briefcase, ExternalLink, ChevronRight } from 'lucide-react';
import { Button } from './components/ui/button';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';
import { articleService } from './services/api';
import LocationPage from './components/LocationPage';

// Loading fallback component
const LoadingFallback = () => <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded h-20 w-full"></div>;

// Get API URL at runtime
const getApiUrl = () => {
  return 'https://cheshiretoday-migration.onrender.com';
};


function HomePage() {
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState('all');
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [activeBottomTab, setActiveBottomTab] = useState('home');
  const [showMobileSearch, setShowMobileSearch] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showTopics, setShowTopics] = useState(false);
  const [showNewsletterPrefs, setShowNewsletterPrefs] = useState(false);
  const topicsRef = useRef(null);
  const categoryStartRef = useRef(null);
  
  // Store pending scroll target when "View All" is clicked
  const pendingScrollRef = useRef(null);

  // Track how many articles each category shows on homepage
  const HOMEPAGE_ARTICLE_COUNTS = {
    'Local News': 6,  // Cheshire News section
    'UK News': 4,
    'Business': 4
  };

  // Helper function to change category and scroll to first new article
  const handleCategoryChange = useCallback((category) => {
    // Store the scroll target - we'll scroll after articles load
    const homepageCount = HOMEPAGE_ARTICLE_COUNTS[category] || 0;
    pendingScrollRef.current = { category, articleIndex: homepageCount };
    
    // Change category (this triggers article fetch)
    setActiveCategory(category);
  }, []);

  // Close mobile menu when clicking outside

  // Fetch articles from API
  useEffect(() => {
    fetchArticles();
  }, [activeCategory]);

  // Scroll to target article AFTER loading completes
  useEffect(() => {
    if (!loading && pendingScrollRef.current) {
      const { category, articleIndex } = pendingScrollRef.current;
      
      // Only scroll if we're viewing the target category
      if (category === activeCategory && articleIndex > 0) {
        // Use delay to ensure DOM is fully rendered after loading
        setTimeout(() => {
          const articleCards = document.querySelectorAll(`[data-testid^="article-card-"]`);
          
          if (articleCards.length > articleIndex) {
            const targetArticle = articleCards[articleIndex];
            if (targetArticle) {
              // Scroll to center the article, accounting for header
              targetArticle.scrollIntoView({ behavior: 'smooth', block: 'center' });
              
              // Add highlight effect after scroll settles
              setTimeout(() => {
                targetArticle.classList.add('highlight-new-article');
                // Remove highlight after animation
                setTimeout(() => {
                  targetArticle.classList.remove('highlight-new-article');
                }, 2500);
              }, 600);
            }
          } else if (articleCards.length > 0) {
            // If target index doesn't exist, scroll to first article card
            articleCards[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
          } else {
            // No article cards, scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }
        }, 300);
      }
      
      // Clear the pending scroll target
      pendingScrollRef.current = null;
    }
  }, [loading, activeCategory]);

  const fetchArticles = async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch more articles for 'all' view to ensure we get articles from all categories
      const limit = activeCategory === 'all' ? 100 : 20;

      // When user opens Local News category, skip the homepage Local News items
      const offset = activeCategory === 'Local News'
        ? (HOMEPAGE_ARTICLE_COUNTS['Local News'] || 0)
        : 0;

      const fetchedArticles = await articleService.fetchArticles(
        activeCategory === 'all' ? null : activeCategory,
        offset,
        limit
      );
      setArticles(fetchedArticles);
    } catch (err) {
      setError('Failed to load articles. Please try again.');
      console.error('Error fetching articles:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle topic search from trending topics
  const handleTopicSearch = async (topic) => {
    try {
      setLoading(true);
      setSearchFilter(topic);
      const results = await articleService.searchArticles(topic);
      setArticles(results);
    } catch (err) {
      console.error('Error searching articles:', err);
    } finally {
      setLoading(false);
    }
  };

  // Clear search filter
  const clearSearchFilter = () => {
    setSearchFilter('');
    fetchArticles();
  };

  const filteredArticles = articles;
  
  // Priority locations in order - we want 1 article from each
  const PRIORITY_LOCATIONS = ['macclesfield', 'wilmslow', 'knutsford', 'warrington', 'chester', 'northwich', 'crewe'];
  
  // Build the priority Cheshire articles - prioritize RECENCY over location diversity
  // Shows newest Cheshire articles first, with location diversity as a secondary factor
  const buildPriorityCheshireArticles = () => {
    const selected = [];
    const usedIds = new Set();
    const usedLocations = new Set();
    
    // Get all Cheshire articles (priority + secondary + local news)
    const allCheshire = articles.filter(a => 
      a.is_priority_cheshire || a.is_secondary_cheshire || 
      (a.category === 'Local News' && a.priority_location)
    );
    
    // First, try to get the 5 most recent articles with location diversity
    // Take newest article, then next newest from different location, etc.
    for (const article of allCheshire) {
      if (selected.length >= 5) break;
      if (usedIds.has(article.id)) continue;
      
      const loc = article.priority_location;
      
      // If we have fewer than 3 articles, prioritize recency over location diversity
      // After 3 articles, try to get different locations if possible
      if (selected.length < 3 || !loc || !usedLocations.has(loc)) {
        selected.push(article);
        usedIds.add(article.id);
        if (loc) usedLocations.add(loc);
      }
    }
    
    // Fill remaining slots with any Cheshire articles (even duplicate locations)
    if (selected.length < 5) {
      for (const article of allCheshire) {
        if (selected.length >= 5) break;
        if (usedIds.has(article.id)) continue;
        selected.push(article);
        usedIds.add(article.id);
      }
    }
    
    // Last resort: add any Local News articles
    if (selected.length < 5) {
      const localNews = articles.filter(
        a => a.category === 'Local News' && !usedIds.has(a.id)
      );
      for (const article of localNews) {
        if (selected.length >= 5) break;
        selected.push(article);
        usedIds.add(article.id);
      }
    }
    
    return selected;
  };
  
  const priorityCheshireArticles = buildPriorityCheshireArticles();
  // Get secondary Cheshire articles (Warrington, Chester, Northwich etc) as fallback - not used in priority section
  const secondaryCheshireArticles = articles.filter(a => a.is_secondary_cheshire && !a.is_priority_cheshire);
  // Combine: priority first, then secondary (for any other use)
  const allCheshireArticles = [...priorityCheshireArticles, ...secondaryCheshireArticles];
  
  // Featured article is the first priority Cheshire article (typically Macclesfield)
  const featuredArticle = priorityCheshireArticles[0] || secondaryCheshireArticles[0] || articles.find(article => article.featured) || articles[0];
  
  // Get 4 articles for Cheshire section (excluding the featured/hero)
  const cheshireSectionArticles = priorityCheshireArticles.filter(a => a.id !== featuredArticle?.id).slice(0, 4);
  
  // For homepage (all categories), use category-based layout
  // For specific category, show all articles from that category
  const localNewsOffset = HOMEPAGE_ARTICLE_COUNTS['Local News'] || 0;

  const regularArticles = activeCategory === 'all'
    ? articles.filter(article => article !== featuredArticle)
    : activeCategory === 'Local News'
      ? articles.filter(a => a.category === 'Local News').slice(localNewsOffset)
      : articles.filter(article => article.category === activeCategory);

  const handleArticleClick = async (article) => {
    const articleId = article.id || article._id;
    
    // Navigate to the article page (SEO-friendly - proper URL for each article)
    if (articleId) {
      navigate(`/article/${articleId}`);
    }
  };

  // Handle breaking news headline click - navigate to article
  const handleHeadlineClick = async (headline) => {
    try {
      // If the headline has an articleId, navigate directly
      if (headline.articleId) {
        navigate(`/article/${headline.articleId}`);
        return;
      }
      
      // Fallback: Find by exact title match and navigate
      let matchingArticle = articles.find(article => 
        article.title === headline.headline
      );
      
      // If no exact match, try partial title match
      if (!matchingArticle) {
        const headlineLower = headline.headline.toLowerCase();
        matchingArticle = articles.find(article => 
          article.title.toLowerCase().includes(headlineLower.slice(0, 30)) ||
          headlineLower.includes(article.title.toLowerCase().slice(0, 30))
        );
      }
      
      if (matchingArticle) {
        const articleId = matchingArticle.id || matchingArticle._id;
        navigate(`/article/${articleId}`);
      } else {
        // Article not in current loaded set - show category
        handleCategoryChange(headline.category || 'all');
        toast({
          title: "📰 " + (headline.category || "News"),
          description: "Showing related articles",
        });
      }
    } catch (error) {
      console.error('Error handling headline click:', error);
      handleCategoryChange('all');
    }
  };

  // Use PUBLIC_URL if set, otherwise use current origin
  // This works correctly for both production (custom domain) and preview environments
  const envPublicUrl = process.env.REACT_APP_PUBLIC_URL;
  const publicUrl = envPublicUrl || (typeof window !== 'undefined' ? window.location.origin : '');

  const handleShare = async () => {
    // Share the homepage
    const shareUrl = publicUrl;
    
    const shareData = {
      title: 'Cheshire Today - Local News & Updates',
      text: 'Stay informed with the latest news from Cheshire and across the UK.',
      url: shareUrl
    };

    // Try native Web Share API first (works on mobile)
    if (navigator.share) {
      try {
        await navigator.share(shareData);
        toast({
          title: "Shared Successfully!",
          description: "Thank you for sharing this article!",
        });
      } catch (err) {
        // User cancelled the share or error occurred
        if (err.name !== 'AbortError') {
          // If share failed (not cancelled), fall back to clipboard
          fallbackCopyToClipboard(shareUrl);
        }
      }
    } else {
      // Fallback to clipboard for desktop browsers
      fallbackCopyToClipboard(shareUrl);
    }
  };

  const fallbackCopyToClipboard = (url) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url);
      toast({
        title: "Link Copied!",
        description: "Article link copied to clipboard - share it on social media!",
      });
    } else {
      toast({
        title: "Share Link",
        description: url,
      });
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', { 
      weekday: 'long',
      day: 'numeric', 
      month: 'long', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Calculate read time (average 200 words per minute)
  const calculateReadTime = (content) => {
    const words = content ? content.split(/\s+/).length : 0;
    const minutes = Math.ceil(words / 200);
    return minutes < 1 ? 1 : minutes;
  };

  return (
    <HelmetProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Festive Christmas & New Year Theme */}
        <FestiveTheme />
        
        {/* Dynamic Meta Tags for Social Sharing */}
        <Helmet>
          <>
            <title>Cheshire Today | Local News & Updates</title>
            <meta name="description" content="Cheshire Today - Your trusted source for local Cheshire news, UK updates, tech, finance, and more." />
            
            {/* Canonical URL for homepage */}
            <link rel="canonical" href="https://cheshiretoday.co.uk/" />
            
            {/* Open Graph / Facebook */}
            <meta property="og:type" content="website" />
            <meta property="og:url" content="https://cheshiretoday.co.uk/" />
            <meta property="og:title" content="Cheshire Today - Local News & Updates" />
            <meta property="og:description" content="Stay informed with the latest news from Cheshire and across the UK. Your trusted source for local stories." />
            <meta property="og:image" content="https://cheshiretoday.co.uk/social-share.jpg" />
            <meta property="og:site_name" content="Cheshire Today" />
            
            {/* Twitter Card */}
            <meta name="twitter:card" content="summary_large_image" />
            <meta name="twitter:url" content="https://cheshiretoday.co.uk/" />
            <meta name="twitter:title" content="Cheshire Today - Local News & Updates" />
            <meta name="twitter:description" content="Stay informed with the latest news from Cheshire and across the UK. Your trusted source for local stories." />
            <meta name="twitter:image" content="https://cheshiretoday.co.uk/social-share.jpg" />
          </>
        </Helmet>

        <NewsHeader 
          categories={categories}
          activeCategory={activeCategory}
          onCategoryChange={handleCategoryChange}
          onArticleClick={handleArticleClick}
        />
        
        {/* Mobile Category Tabs - Swipeable */}
        <div className="md:hidden">
          <CategoryTabs
            categories={categories}
            activeCategory={activeCategory}
            onCategoryChange={(cat) => {
              handleCategoryChange(cat);
              setActiveBottomTab('home');
              setShowTopics(false);
            }}
            expanded={showTopics}
          />
        </div>
        
        {/* Topics Expanded View - Show all categories when Topics is active */}
        {showTopics && (
          <div className="md:hidden bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Browse by Topic</h2>
            <div className="grid grid-cols-2 gap-3">
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => {
                    handleCategoryChange(category.id);
                    setShowTopics(false);
                    setActiveBottomTab('home');
                  }}
                  className={`p-4 rounded-xl text-left transition-all ${
                    activeCategory === category.id
                      ? 'bg-[#1E3A8A] text-white'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                  data-testid={`topic-${category.id}`}
                >
                  <span className="text-2xl mb-1 block">{category.icon || '📰'}</span>
                  <span className="font-semibold text-sm">{category.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Breaking News Ticker */}
        <Suspense fallback={<div className="h-10 bg-red-600 animate-pulse"></div>}>
          <BreakingNewsTicker onHeadlineClick={handleHeadlineClick} />
        </Suspense>
        
        {/* Local Areas Quick Links */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 py-2">
          <div className="container mx-auto px-4">
            {/* Mobile: Show Jobs and Alert Button prominently */}
            <div className="flex sm:hidden items-center justify-between mb-2 pb-2 border-b border-gray-100 dark:border-gray-700">
              <Link 
                to="/jobs" 
                className="flex items-center gap-1.5 bg-emerald-600 text-white px-3 py-1.5 rounded-full text-sm font-medium hover:bg-emerald-700 transition-colors"
              >
                <Briefcase className="h-4 w-4" />
                Jobs
              </Link>
              <div className="flex items-center gap-2">
                <Suspense fallback={null}>
                  <PushNotificationButton apiUrl={getApiUrl()} />
                  <ShareAlertsButton siteUrl="https://cheshiretoday.co.uk" />
                </Suspense>
              </div>
            </div>
            
            {/* Local areas row */}
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 sm:gap-3 overflow-x-auto scrollbar-hide flex-1">
                <span className="text-gray-500 dark:text-gray-400 text-sm font-medium whitespace-nowrap flex items-center gap-1">
                  <MapPin className="h-4 w-4" />
                  <span className="hidden sm:inline">Local:</span>
                </span>
                {[
                  { name: 'All Cheshire', slug: 'cheshire-general' },
                  { name: 'Macclesfield', slug: 'macclesfield' },
                  { name: 'Wilmslow', slug: 'wilmslow' },
                  { name: 'Knutsford', slug: 'knutsford' },
                  { name: 'Chester', slug: 'chester' },
                  { name: 'Warrington', slug: 'warrington' },
                  { name: 'Crewe', slug: 'crewe' },
                  { name: 'Northwich', slug: 'northwich' }
                ].map((area) => (
                  <a
                    key={area.slug}
                    href={`/${area.slug}`}
                    className="px-2 sm:px-3 py-1 text-xs sm:text-sm text-gray-600 dark:text-gray-300 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 rounded-full whitespace-nowrap transition-colors"
                  >
                    {area.name}
                  </a>
                ))}
              </div>
              
              {/* Push Notification Button - Desktop only (mobile shown above) */}
              <div className="hidden sm:flex items-center gap-2 flex-shrink-0">
                <Link 
                  to="/jobs"
                  className="flex items-center gap-1 px-3 py-1.5 bg-emerald-600 text-white text-sm font-medium rounded-full hover:bg-emerald-700 transition-colors"
                >
                  <Briefcase className="h-4 w-4" />
                  Jobs
                </Link>
                <PushNotificationButton apiUrl={getApiUrl()} />
                <ShareAlertsButton siteUrl="https://cheshiretoday.co.uk" />
              </div>
            </div>
          </div>
        </div>
      
      <main className="bg-gray-50 dark:bg-gray-900">
        {/* Error State */}
        {error && (
          <div className="container mx-auto px-4 py-8">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
              <p className="text-red-800 dark:text-red-200 mb-4">{error}</p>
              <Button onClick={fetchArticles} className="bg-emerald-600 hover:bg-emerald-700">
                Try Again
              </Button>
            </div>
          </div>
        )}

        {/* Loading State - Show skeleton instead of spinner for better FCP */}
        {loading && <HomeSkeleton />}

        {/* Main Content */}
        {!loading && !error && (
          <>
            {/* Search Filter Indicator */}
            {searchFilter && (
              <div className="container mx-auto px-4 pt-6">
                <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4 flex items-center justify-between">
                  <p className="text-emerald-800 dark:text-emerald-200">
                    Showing results for: <span className="font-bold">&ldquo;{searchFilter}&rdquo;</span>
                  </p>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={clearSearchFilter}
                    className="text-emerald-700 border-emerald-300 hover:bg-emerald-100 dark:text-emerald-300 dark:border-emerald-700 dark:hover:bg-emerald-900"
                    data-testid="clear-search-filter"
                  >
                    Clear Filter
                  </Button>
                </div>
              </div>
            )}

            {/* Hero Section */}
            {featuredArticle && !searchFilter && (
              <div className="container mx-auto px-4 py-8">
                <HeroArticle 
                  article={featuredArticle}
                  onClick={handleArticleClick}
                />
              </div>
            )}

            {/* Main Content Grid */}
            <div className="container mx-auto px-4 py-8">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Articles Column */}
                <div className="lg:col-span-2 space-y-8">
                  {/* Local News Section - 4 Articles First (1 from each location) */}
                  {activeCategory === 'all' && (
                    <section>
                      <div className="flex items-center justify-between mb-6 pb-4 border-b-2 border-[#1E3A8A]">
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                          <MapPin className="h-6 w-6 text-[#1E3A8A]" />
                          Local News
                        </h2>
                        <span className="text-sm text-gray-500 dark:text-gray-400">Macclesfield • Wilmslow • Knutsford & more</span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Show 4 priority Cheshire articles - 1 from each location */}
                        {cheshireSectionArticles.map((article, index) => (
                          <CompactArticleCard
                            key={article.id}
                            article={article}
                            onClick={handleArticleClick}
                            priority={index < 2}
                          />
                        ))}
                      </div>
                      <div className="mt-6 text-center">
                        <Link 
                          to="/cheshire-general" 
                          className="inline-flex items-center gap-2 px-6 py-2.5 bg-[#1E3A8A] hover:bg-[#16306f] text-white font-medium rounded-full transition-colors"
                        >
                          View All Local News
                          <ChevronRight className="h-4 w-4" />
                        </Link>
                      </div>
                    </section>
                  )}

                  {/* Random Promo #1 - After Cheshire News (every 2 sections) */}
                  {activeCategory === 'all' && (
                    <Suspense fallback={null}>
                      <RandomPromoWidget seed={1} />
                    </Suspense>
                  )}

                  {/* UK News Section - 2 Articles */}
                  {activeCategory === 'all' && (
                    <section>
                      <div className="flex items-center justify-between mb-6 pb-4 border-b-2 border-blue-600">
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">UK News</h2>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {regularArticles.filter(a => a.category === 'UK News').slice(0, 2).map((article) => (
                          <CompactArticleCard
                            key={article.id}
                            article={article}
                            onClick={handleArticleClick}
                          />
                        ))}
                      </div>
                      <div className="mt-6 text-center">
                        <button 
                          onClick={() => handleCategoryChange('UK News')}
                          className="inline-flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-full transition-colors"
                        >
                          View All UK News
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </div>
                    </section>
                  )}
                  {/* Business Section - 2 Articles */}
                  {activeCategory === 'all' && (
                    <section>
                      <div className="flex items-center justify-between mb-6 pb-4 border-b-2 border-amber-600">
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Business</h2>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {regularArticles.filter(a => a.category === 'Business').slice(0, 2).map((article) => (
                          <CompactArticleCard
                            key={article.id}
                            article={article}
                            onClick={handleArticleClick}
                          />
                        ))}
                      </div>
                      <div className="mt-6 text-center">
                        <button
                          onClick={() => handleCategoryChange('Business')}
                          className="inline-flex items-center gap-2 px-6 py-2.5 bg-amber-600 hover:bg-amber-700 text-white font-medium rounded-full transition-colors"
                        >
                          View All Business
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </div>
                    </section>
                  )}

                </div>

<div className="lg:col-span-1 space-y-6">
                  {/* Amazon Affiliate Widget - Top */}
                  <Suspense fallback={<LoadingFallback />}>
                    <AffiliateWidgetSidebar category={activeCategory !== 'all' ? activeCategory : 'default'} />
                  </Suspense>
                  
                  {/* Most Read Widget */}
                  <Suspense fallback={<LoadingFallback />}>
                    <MostReadWidget 
                      apiUrl={getApiUrl()}
                      onArticleClick={handleArticleClick}
                    />
                  </Suspense>
                  
                  <Suspense fallback={<LoadingFallback />}>
                    <TrendingSidebar 
                      articles={articles}
                      onArticleClick={handleArticleClick}
                      onSearch={handleTopicSearch}
                    />
                  </Suspense>
                  
                  {/* Amazon Affiliate Widget - Bottom */}
                  <Suspense fallback={<LoadingFallback />}>
                    <AffiliateWidgetSidebar category="Tech" />
                  </Suspense>
                </div>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Footer - Hidden on mobile when bottom nav is visible */}
      <div className="hidden md:block">
        <Suspense fallback={<div className="h-40 bg-gray-100 dark:bg-gray-800"></div>}>
          <NewsFooter />
        </Suspense>
      </div>
      
      {/* Mobile Footer - Simplified */}
      <div className="md:hidden pb-20">
        <Suspense fallback={null}>
          <NewsFooter />
        </Suspense>
      </div>

      {/* Mobile Bottom Navigation */}
      <Suspense fallback={null}>
        <BottomNav 
          activeTab={activeBottomTab}
          onTabChange={(tab) => {
            setActiveBottomTab(tab);
            if (tab === 'home') {
              setActiveCategory('all');
            setShowTopics(false);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          } else if (tab === 'topics') {
            setShowTopics(true);
            // Scroll to show topics at top
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }
        }}
        onSearchClick={() => setShowMobileSearch(true)}
        onMenuClick={() => setShowMobileMenu(true)}
      />
      </Suspense>

      {/* Mobile Search Overlay */}
      <Suspense fallback={null}>
        <MobileSearch
          open={showMobileSearch}
          onClose={() => setShowMobileSearch(false)}
          onArticleSelect={(article) => {
            setShowMobileSearch(false);
            const articleId = article.id || article._id;
            if (articleId) {
              navigate(`/article/${articleId}`);
            }
          }}
        />
      </Suspense>

      {/* Mobile Menu Overlay */}
      <Suspense fallback={null}>
        <MobileMenu
          open={showMobileMenu}
          onClose={() => setShowMobileMenu(false)}
          onNavigate={(page) => {
            setShowMobileMenu(false);
            if (page === 'subscribe') {
              setShowNewsletterPrefs(true);
            } else if (page === 'privacy') {
              window.location.href = '/privacy';
            } else if (page === 'terms') {
              window.location.href = '/terms';
            } else if (page === 'notifications') {
              // Trigger notification permission request
              if ('Notification' in window) {
                Notification.requestPermission();
              }
            }
          }}
      />
      </Suspense>

      {/* Newsletter Preferences Dialog */}
      <Suspense fallback={null}>
        <NewsletterPreferences
          open={showNewsletterPrefs}
          onOpenChange={setShowNewsletterPrefs}
        />
      </Suspense>

      {/* Article Detail Dialog removed - articles now open in dedicated pages */}

      <Toaster />
      <NewsletterPopup />
      </div>
    </HelmetProvider>
  );


}

// Article Page Component
function ArticlePage() {
  const { articleId } = useParams();
  const navigate = useNavigate();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // Affiliate products - fetched once and shared between widgets
  const [affiliateProducts, setAffiliateProducts] = useState({ inline: [], endArticle: [] });
  // Use PUBLIC_URL if set, otherwise use current origin
  const publicUrl = process.env.REACT_APP_PUBLIC_URL || (typeof window !== 'undefined' ? window.location.origin : '');

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        setLoading(true);
        const data = await articleService.fetchArticle(articleId);
        setArticle(data);
        setError(null);
      } catch (error) {
        console.error('Error fetching article:', error);
        // Show 404 page instead of redirecting (better for SEO)
        setError('Article not found');
        setArticle(null);
      } finally {
        setLoading(false);
      }
    };

    fetchArticle();
  }, [articleId]);

  // Fetch and distribute affiliate products once when article loads
  // This ensures "You Might Like" and "You Might Also Like" show DIFFERENT products
  useEffect(() => {
    if (!article) return;
    
    let mounted = true;
    
    const loadAffiliateProducts = async () => {
      const category = article.category || 'default';
      
      // Start with hardcoded products as base (guaranteed to have enough items)
      const categoryProducts = SAMPLE_PRODUCTS[category] || [];
      const defaultProducts = SAMPLE_PRODUCTS['default'] || [];
      let allProducts = [...categoryProducts, ...defaultProducts];
      
      // Try to add database products if available
      const dbData = await fetchDatabaseProducts();
      
      if (!mounted) return;
      
      if (dbData && dbData.products.length > 0) {
        const dbCategoryProducts = dbData.by_category[category] || [];
        const dbDefaultProducts = dbData.by_category['default'] || [];
        // Prepend database products so they're prioritized
        allProducts = [...dbCategoryProducts, ...dbDefaultProducts, ...allProducts];
      }
      
      // Remove duplicates by name
      const unique = allProducts.filter((product, index, self) => 
        index === self.findIndex(p => p.name === product.name)
      );
      
      // Shuffle once
      const shuffled = [...unique].sort(() => 0.5 - Math.random());
      
      // Split into non-overlapping sets:
      // - First 2 products for "You Might Like" (inline widget)
      // - Next 4 products for "You Might Also Like" (end article widget)
      setAffiliateProducts({
        inline: shuffled.slice(0, 2),
        endArticle: shuffled.slice(2, 6)
      });
    };
    
    loadAffiliateProducts();
    
    return () => { mounted = false; };
  }, [article]);

  // Show 404 page for missing articles
  if (error) {
    return (
      <HelmetProvider>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <Helmet>
            <title>Article Not Found | Cheshire Today</title>
            <meta name="robots" content="noindex, nofollow" />
          </Helmet>
          <NewsHeader 
            categories={categories}
            onCategoryChange={() => {}}
            activeCategory="all"
            onSearch={() => {}}
          />
          <main className="flex-1 flex items-center justify-center">
            <div className="text-center px-4">
              <h1 className="text-4xl font-bold text-gray-800 mb-4">Article Not Found</h1>
              <p className="text-gray-600 mb-6">Sorry, this article may have been removed or the link is incorrect.</p>
              <Button onClick={() => navigate('/')} data-testid="go-home-btn">
                Go to Homepage
              </Button>
            </div>
          </main>
          <NewsFooter />
        </div>
      </HelmetProvider>
    );
  }

  const handleShare = () => {
    const shareUrl = `${publicUrl}/article/${articleId}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(shareUrl);
      toast({
        title: "Link Copied!",
        description: "Article link copied to clipboard!",
      });
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', { 
      weekday: 'long',
      day: 'numeric', 
      month: 'long', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <HelmetProvider>
        <div className="min-h-screen bg-gray-50">
          <FestiveTheme />
          <NewsHeader 
            categories={categories}
            activeCategory="all"
            onCategoryChange={() => navigate('/')}
          />
          <div className="container mx-auto px-4 py-20">
            <div className="flex flex-col items-center justify-center">
              <Loader2 className="h-16 w-16 animate-spin text-emerald-600 mb-4" />
              <p className="text-lg text-gray-600">Loading article...</p>
            </div>
          </div>
          <Toaster />
        </div>
      </HelmetProvider>
    );
  }

  if (!article) {
    return null;
  }

  return (
    <HelmetProvider>
      <div className="min-h-screen bg-gray-50">
        <FestiveTheme />
        
        {/* Dynamic Meta Tags for This Article */}
        <Helmet>
          <title>{article.title} | Cheshire Today</title>
          <meta name="description" content={(article.content || '').substring(0, 160)} />
          
          <meta property="og:type" content="article" />
          <meta property="og:url" content={`${publicUrl}/article/${articleId}`} />
          <meta property="og:title" content={article.title} />
          <meta property="og:description" content={(article.content || '').substring(0, 200)} />
          <meta property="og:image" content={article.image} />
          <meta property="og:image:secure_url" content={article.image} />
          <meta property="og:image:width" content="1200" />
          <meta property="og:image:height" content="630" />
          
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:url" content={`${publicUrl}/article/${articleId}`} />
          <meta name="twitter:title" content={article.title} />
          <meta name="twitter:description" content={(article.content || '').substring(0, 200)} />
          <meta name="twitter:image" content={article.image} />
          
          {/* Structured Data - Schema.org NewsArticle */}
          <script type="application/ld+json">
            {JSON.stringify({
              "@context": "https://schema.org",
              "@type": "NewsArticle",
              "headline": article.title,
              "image": [article.image],
              "datePublished": article.publishedDate,
              "dateModified": article.publishedDate,
              "author": {
                "@type": "Person",
                "name": article.author || "Cheshire Today"
              },
              "publisher": {
                "@type": "Organization",
                "name": "Cheshire Today",
                "logo": {
                  "@type": "ImageObject",
                  "url": `${publicUrl}/logo.png`
                }
              },
              "description": (article.content || '').substring(0, 200),
              "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": `${publicUrl}/article/${articleId}`
              }
            })}
          </script>
        </Helmet>

        <NewsHeader 
          categories={categories}
          activeCategory="all"
          onCategoryChange={() => navigate('/')}
        />
        
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <Button 
              variant="outline" 
              onClick={() => navigate('/')}
              className="mb-6"
            >
              ← Back to Home
            </Button>

            <article className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="relative h-96">
                <img 
                  src={article.image} 
                  alt={article.title}
                  className="w-full h-full object-cover"
                  loading="eager"
                  fetchpriority="high"
                  decoding="async"
                  width="800"
                  height="384"
                />
                <Badge className="absolute top-4 left-4 bg-emerald-600 text-white">
                  {article.category}
                </Badge>
              </div>

              <div className="p-8">
                <h1 className="text-4xl font-bold text-gray-900 mb-4 leading-tight">
                  {article.title}
                </h1>

                <div className="flex items-center flex-wrap gap-4 text-sm text-gray-600 mb-6 pb-6 border-b">
                  <div className="flex items-center">
                    <User className="h-4 w-4 mr-2" />
                    <span className="font-medium">{article.author}</span>
                  </div>
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-2" />
                    {formatDate(article.publishedDate)}
                  </div>
                  {article.source && (
                    <div className="flex items-center">
                      <span className="text-gray-400">via</span>
                      {article.source_url ? (
                        <a 
                          href={article.source_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="ml-1 text-emerald-600 hover:text-emerald-700 hover:underline font-medium"
                          data-testid="article-source-link"
                        >
                          {article.source}
                        </a>
                      ) : (
                        <span className="ml-1 font-medium">{article.source}</span>
                      )}
                    </div>
                  )}
                </div>

                <div className="prose prose-lg max-w-none mb-8">
                  <p className="text-gray-800 text-lg md:text-xl leading-relaxed mb-4 whitespace-pre-wrap">
                    {article.content}
                  </p>
                </div>
                
                {/* In-Content Affiliate Widget - Uses pre-distributed products */}
                <Suspense fallback={null}>
                  <AffiliateWidgetInline category={article.category} title="You Might Like" products={affiliateProducts.inline} />
                </Suspense>

                {/* Jobs & Subscribe Banners - Above Tags/Source */}
                <div className="space-y-2 my-6">
                  <Suspense fallback={null}>
                    <JobsInlineBanner />
                  </Suspense>
                  <SubscribeInlineBanner />
                </div>

                <Separator className="my-6" />

                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex flex-wrap gap-2">
                    {article.tags && article.tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs text-gray-700 dark:text-gray-200 border-gray-400 dark:border-gray-500 bg-gray-100 dark:bg-gray-700 font-medium">
                        #{tag}
                      </Badge>
                    ))}
                  </div>
                  <Button 
                    variant="outline" 
                    onClick={handleShare}
                    className="hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-300"
                  >
                    <Share2 className="h-4 w-4 mr-2" />
                    Share Article
                  </Button>
                </div>

                {/* Related Articles */}
                <RelatedArticles 
                  articleId={articleId} 
                  onArticleClick={(article) => navigate(`/article/${article.id}`)} 
                />

                {/* Original Source Attribution - Legal Requirement */}
                {article.source_url && (
                  <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg" data-testid="source-attribution-box">
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      This article was originally published by <strong>{article.source}</strong>
                    </p>
                    <a 
                      href={article.source_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-emerald-600 hover:text-emerald-700 font-medium text-sm hover:underline"
                      data-testid="read-original-link"
                    >
                      <ExternalLink className="h-4 w-4 mr-1" />
                      Read the original article at {article.source}
                    </a>
                  </div>
                )}

                {/* You Might Also Like - Affiliate Products - Uses different products from inline widget */}
                <div className="mt-8">
                  <Suspense fallback={null}>
                    <AffiliateWidgetEndArticle category={article.category} products={affiliateProducts.endArticle} />
                  </Suspense>
                </div>
              </div>
            </article>
          </div>
        </main>

        <NewsFooter />
        <Toaster />
        <NewsletterPopup />
      </div>
    </HelmetProvider>
  );
}

// Admin Page Wrapper
function AdminPage() {
  const navigate = useNavigate();
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    }>
      <AdminDashboard onBack={() => navigate('/')} />
    </Suspense>
  );
}

// Search Page - Handles Facebook post links by searching for article by title
function SearchPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [activeCategory, setActiveCategory] = useState('all');
  const publicUrl = process.env.REACT_APP_PUBLIC_URL || (typeof window !== 'undefined' ? window.location.origin : '');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const query = params.get('q') || '';
    setSearchQuery(decodeURIComponent(query));
    
    if (query) {
      searchAndShowArticle(decodeURIComponent(query));
    } else {
      setLoading(false);
    }
  }, []);

  const searchAndShowArticle = async (query) => {
    try {
      setLoading(true);
      const articles = await articleService.searchArticles(query);
      setResults(articles);
      
      // If we found a matching article, navigate to it
      if (articles.length > 0) {
        // Find best match - prioritize exact title match
        const exactMatch = articles.find(a => 
          a.title?.toLowerCase().includes(query.toLowerCase().substring(0, 50))
        );
        const bestMatch = exactMatch || articles[0];
        // Navigate to the article page
        navigate(`/article/${bestMatch.id || bestMatch._id}`);
      }
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle article click - navigate to article page
  const handleArticleClick = (article) => {
    const articleId = article.id || article._id;
    if (articleId) {
      navigate(`/article/${articleId}`);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', { 
      weekday: 'long',
      day: 'numeric', 
      month: 'long', 
      year: 'numeric' 
    });
  };

  if (loading) {
    return (
      <HelmetProvider>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-emerald-600 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">Finding article...</p>
          </div>
        </div>
      </HelmetProvider>
    );
  }

  return (
    <HelmetProvider>
      <Helmet>
        <title>Search - Cheshire Today</title>
        <meta name="description" content={`Search results for: ${searchQuery}`} />
      </Helmet>
      
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <NewsHeader 
          categories={categories}
          activeCategory={activeCategory}
          onCategoryChange={(cat) => {
            setActiveCategory(cat);
            navigate('/');
          }}
          onArticleClick={handleArticleClick}
        />
        
        <main className="container mx-auto px-4 py-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            {results.length > 0 ? `Found ${results.length} article${results.length > 1 ? 's' : ''}` : 'No articles found'}
          </h1>
          
          {results.length === 0 && searchQuery && (
            <div className="text-center py-12">
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                No articles found matching &ldquo;{searchQuery}&rdquo;
              </p>
              <Button onClick={() => navigate('/')} className="bg-emerald-600 hover:bg-emerald-700">
                Browse All Articles
              </Button>
            </div>
          )}
          
          <div className="grid gap-4">
            {results.map((article) => (
              <div 
                key={article.id}
                onClick={() => handleArticleClick(article)}
                className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 cursor-pointer hover:shadow-lg transition-shadow flex gap-4"
              >
                <img 
                  src={article.image} 
                  alt={article.title}
                  className="w-24 h-24 object-cover rounded"
                />
                <div className="flex-1">
                  <Badge className="mb-2 bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
                    {article.category}
                  </Badge>
                  <h2 className="font-semibold text-gray-900 dark:text-white line-clamp-2">
                    {article.title}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {article.source} • {formatDate(article.publishedDate)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </main>
        
        <NewsFooter />
      </div>

      
      <Toaster />
    </HelmetProvider>
  );
}


// Valid location slugs
const VALID_LOCATIONS = ['cheshire-general', 'chester', 'warrington', 'crewe', 'wirral', 'macclesfield', 'wilmslow', 'knutsford', 'stockport', 'northwich'];

// Wrapper to validate location routes
const LocationRouteWrapper = () => {
  const { location } = useParams();
  if (VALID_LOCATIONS.includes(location?.toLowerCase())) {
    return <LocationPage />;
  }
  // If not a valid location, redirect to home
  return <Navigate to="/" replace />;
};

// Main App with Router
function App() {
  return (
    <ThemeProvider>
      <PromoWidgetProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/article/:articleId" element={<ArticlePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/jobs" element={<Suspense fallback={<LoadingFallback />}><JobBoard /></Suspense>} />
            <Route path="/jobs/post" element={<Suspense fallback={<LoadingFallback />}><PostJob /></Suspense>} />
            <Route path="/jobs/payment-success" element={<Suspense fallback={<LoadingFallback />}><PaymentSuccess /></Suspense>} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/terms" element={<TermsOfService />} />
            <Route path="/affiliate-disclosure" element={<AffiliateDisclosure />} />
            <Route path="/unsubscribe" element={<Suspense fallback={<LoadingFallback />}><UnsubscribePage /></Suspense>} />
            <Route path="/newsletter/preferences" element={<Suspense fallback={<LoadingFallback />}><PreferencesPage /></Suspense>} />
            {/* Location-specific pages for Local SEO */}
            <Route path="/:location" element={<LocationRouteWrapper />} />
          </Routes>
        </BrowserRouter>
      </PromoWidgetProvider>
    </ThemeProvider>
  );
}

export default App;