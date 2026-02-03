import React, { useState, useEffect, useRef, lazy, Suspense, useCallback, useMemo } from 'react';
import './App.css';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import { BrowserRouter, Routes, Route, useParams, useNavigate, Navigate, useLocation, Link } from 'react-router-dom';
import { loadHomeSchema } from './lib/loadHomeSchema';

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

// Loading fallback component
const LoadingFallback = () => <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded h-20 w-full"></div>;

// Get API URL at runtime
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
    return isLocalhost ? 'http://localhost:8001' : window.location.origin;
  }
  return '';
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
    'Local News': 4,  // Cheshire News section
    'UK News': 2,
    'Business': 2,
    'Health': 2,
    'Sports': 2,
    'Tech': 2,
    'Science': 2,
    'Entertainment': 2
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

  // Fetch articles from API// Article Page Component
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

import LocationPage from './components/LocationPage';

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