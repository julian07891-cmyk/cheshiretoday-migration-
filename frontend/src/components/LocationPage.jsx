import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import { MapPin, Loader2, Clock, User, ArrowLeft } from 'lucide-react';
import NewsHeader from './NewsHeader';
import NewsFooter from './NewsFooter';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Toaster } from './ui/toaster';
import { categories } from '../mockData';

// Location metadata for SEO
const LOCATION_DATA = {
  'cheshire-general': {
    name: 'Cheshire',
    description: 'General news from across Cheshire that isn\'t specific to any particular town.',
    keywords: 'Cheshire news, Cheshire today, Cheshire local news, Cheshire region',
    image: '/cheshire-hero.jpg'
  },
  chester: {
    name: 'Chester',
    description: 'Latest news from Chester, Ellesmere Port, and surrounding areas in Cheshire.',
    keywords: 'Chester news, Chester local news, Ellesmere Port news, Chester today, Cheshire news',
    image: '/chester-hero.jpg'
  },
  warrington: {
    name: 'Warrington',
    description: 'Breaking news and updates from Warrington, Lymm, Runcorn, Widnes and the surrounding area.',
    keywords: 'Warrington news, Warrington local news, Lymm news, Runcorn news, Widnes news, Warrington today',
    image: '/warrington-hero.jpg'
  },
  crewe: {
    name: 'Crewe',
    description: 'Local news from Crewe, Nantwich, Sandbach and South Cheshire.',
    keywords: 'Crewe news, Nantwich news, Sandbach news, South Cheshire news',
    image: '/crewe-hero.jpg'
  },
  wirral: {
    name: 'Wirral',
    description: 'News and updates from across the Wirral Peninsula including Birkenhead and Wallasey.',
    keywords: 'Wirral news, Birkenhead news, Wallasey news, Wirral today, Merseyside news',
    image: '/wirral-hero.jpg'
  },
  macclesfield: {
    name: 'Macclesfield',
    description: 'Latest news from Macclesfield, Congleton, Bollington and East Cheshire.',
    keywords: 'Macclesfield news, Congleton news, Bollington news, East Cheshire news',
    image: '/macclesfield-hero.jpg'
  },
  wilmslow: {
    name: 'Wilmslow',
    description: 'Latest news from Wilmslow, Handforth, Styal and surrounding areas.',
    keywords: 'Wilmslow news, Handforth news, Styal news, Cheshire news',
    image: '/wilmslow-hero.jpg'
  },
  knutsford: {
    name: 'Knutsford',
    description: 'Local news from Knutsford, Tatton and the surrounding area.',
    keywords: 'Knutsford news, Tatton news, Cheshire news',
    image: '/knutsford-hero.jpg'
  },
  stockport: {
    name: 'Stockport',
    description: 'Breaking news and stories from Stockport, Cheadle, Bramhall and Greater Manchester.',
    keywords: 'Stockport news, Cheadle news, Bramhall news, Greater Manchester news',
    image: '/stockport-hero.jpg'
  },
  northwich: {
    name: 'Northwich',
    description: 'News from Northwich, Winsford, Middlewich and Mid Cheshire.',
    keywords: 'Northwich news, Winsford news, Middlewich news, Mid Cheshire news',
    image: '/northwich-hero.jpg'
  }
};

// Runtime URL detection - must work at runtime, not build time
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
    
    if (isLocalhost) {
      // In development, API is on port 8001
      return (process.env.REACT_APP_BACKEND_URL || window.location.origin);
    } else {
      // In production, API is on the same origin
      return window.location.origin;
    }
  }
  return '';
};

const LocationPage = () => {
  const { location } = useParams();
  const navigate = useNavigate();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [activeCategory, setActiveCategory] = useState('all');
  
  // Get API URL at component level for proper runtime detection
  const API_URL = getApiUrl();
  
  const locationData = LOCATION_DATA[location?.toLowerCase()] || {
    name: location,
    description: `Latest news from ${location}`,
    keywords: `${location} news, ${location} local news`
  };

  const publicUrl = process.env.REACT_APP_PUBLIC_URL || 'https://cheshiretoday.co.uk';

  // Handle article click - navigate to article page
  const handleArticleClick = (article) => {
    const articleId = article.id || article._id;
    if (articleId) {
      navigate(`/article/${articleId}`);
    }
  };

  useEffect(() => {
    fetchLocationArticles();
  }, [location]);

  const fetchLocationArticles = async () => {
    try {
      setLoading(true);
      const url = `${API_URL}/api/articles/location/${location}?limit=30`;
      console.log('Fetching location articles from:', url);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        console.error('Response not OK:', response.status, response.statusText);
        throw new Error('Location not found');
      }
      
      const data = await response.json();
      console.log('Location data received:', data);
      setArticles(data.articles || []);
      setTotalCount(data.total || 0);
    } catch (error) {
      console.error('Error fetching location articles:', error);
      setArticles([]);
    } finally {
      setLoading(false);
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

  // Structured data for local news
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": `${locationData.name} News - Cheshire Today`,
    "description": locationData.description,
    "url": `${publicUrl}/${location}`,
    "isPartOf": {
      "@type": "WebSite",
      "name": "Cheshire Today",
      "url": publicUrl
    },
    "about": {
      "@type": "Place",
      "name": locationData.name,
      "containedInPlace": {
        "@type": "AdministrativeArea",
        "name": "Cheshire"
      }
    }
  };

  if (loading) {
    return (
      <HelmetProvider>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-emerald-600 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">Loading {locationData.name} news...</p>
          </div>
        </div>
      </HelmetProvider>
    );
  }

  return (
    <HelmetProvider>
      <Helmet>
        <title>{`${locationData.name} News | Cheshire Today - Local News & Updates`}</title>
        <meta name="description" content={locationData.description} />
        <meta name="keywords" content={locationData.keywords} />
        <link rel="canonical" href={`${publicUrl}/${location}`} />
        
        {/* Open Graph */}
        <meta property="og:title" content={`${locationData.name} News | Cheshire Today`} />
        <meta property="og:description" content={locationData.description} />
        <meta property="og:url" content={`${publicUrl}/${location}`} />
        <meta property="og:type" content="website" />
        
        {/* Twitter */}
        <meta name="twitter:title" content={`${locationData.name} News | Cheshire Today`} />
        <meta name="twitter:description" content={locationData.description} />
      </Helmet>
      
      {/* Structured Data - rendered outside Helmet */}
      <script 
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      
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
          {/* Location Header */}
          <div className="mb-8">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/')}
              className="mb-4 text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to All News
            </Button>
            
            <div className="flex items-center gap-3 mb-2">
              <div className="h-12 w-12 bg-emerald-100 dark:bg-emerald-900 rounded-full flex items-center justify-center">
                <MapPin className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">
                  {locationData.name} News
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                  {totalCount} articles from {locationData.name} and surrounding areas
                </p>
              </div>
            </div>
            
            <p className="text-gray-700 dark:text-gray-300 mt-4 max-w-2xl">
              {locationData.description}
            </p>
          </div>

          {/* Articles Grid */}
          {articles.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
              <MapPin className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
                No articles found for {locationData.name}
              </h2>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                Check back soon for local news updates
              </p>
              <Button onClick={() => navigate('/')} className="bg-emerald-600 hover:bg-emerald-700">
                Browse All News
              </Button>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {articles.map((article) => (
                <article 
                  key={article.id}
                  onClick={() => handleArticleClick(article)}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
                  data-testid={`location-article-${article.id}`}
                >
                  <img 
                    src={article.image} 
                    alt={article.title}
                    className="w-full h-48 object-cover"
                  />
                  <div className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200 text-sm">
                        {article.category}
                      </Badge>
                      {article.is_local_source && (
                        <Badge variant="outline" className="text-blue-600 border-blue-600 text-sm">
                          <MapPin className="h-3 w-3 mr-1" />
                          Local
                        </Badge>
                      )}
                    </div>
                    <h2 className="text-lg md:text-xl font-semibold text-gray-900 dark:text-white line-clamp-2 mb-2">
                      {article.title}
                    </h2>
                    <div className="flex items-center gap-3 text-base text-gray-500 dark:text-gray-400">
                      <span>{article.source}</span>
                      <span>•</span>
                      <span>{new Date(article.publishedDate).toLocaleDateString('en-GB')}</span>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
          
          {/* Other Locations */}
          <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Explore Other Areas
            </h2>
            <div className="flex flex-wrap gap-3">
              {Object.entries(LOCATION_DATA)
                .filter(([key]) => key !== location?.toLowerCase())
                .map(([key, data]) => (
                  <Button
                    key={key}
                    variant="outline"
                    onClick={() => navigate(`/${key}`)}
                    className="flex items-center gap-2"
                  >
                    <MapPin className="h-4 w-4" />
                    {data.name}
                  </Button>
                ))}
            </div>
          </div>
        </main>
        
        <NewsFooter />
      </div>
      
      <Toaster />
    </HelmetProvider>
  );
};

export default LocationPage;
