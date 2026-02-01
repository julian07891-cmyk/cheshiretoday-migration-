import React, { useEffect, useMemo } from 'react';
import { Clock, User } from 'lucide-react';
import { Badge } from './ui/badge';

const fallbackImage = 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1200&q=75&fit=crop&fm=webp';

// Optimized image URL - larger for hero, but compressed with WebP
const getOptimizedHeroUrl = (url) => {
  if (!url) return fallbackImage;
  if (url.includes('unsplash.com')) {
    const baseUrl = url.split('?')[0];
    return `${baseUrl}?w=1200&q=75&fit=crop&auto=format&fm=webp`;
  }
  return url;
};

const HeroArticle = ({ article, onClick }) => {
  const [imageError, setImageError] = React.useState(false);
  const [imageLoaded, setImageLoaded] = React.useState(false);
  
  // Memoize optimized URL
  const optimizedImageUrl = useMemo(() => 
    getOptimizedHeroUrl(article?.image), 
    [article?.image]
  );
  
  // Preload hero image for better LCP
  useEffect(() => {
    if (optimizedImageUrl && optimizedImageUrl !== fallbackImage) {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'image';
      link.href = optimizedImageUrl;
      link.fetchPriority = 'high';
      document.head.appendChild(link);
      return () => {
        if (link.parentNode) link.parentNode.removeChild(link);
      };
    }
  }, [optimizedImageUrl]);
  
  if (!article) return null;

  const handleImageError = () => {
    setImageError(true);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours < 24) {
      return `${diffHours}h ago`;
    }
    return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
  };

  return (
    <div 
      className="relative cursor-pointer group overflow-hidden rounded-lg shadow-lg"
      onClick={() => onClick(article)}
    >
      {/* Fixed aspect ratio container to prevent CLS */}
      <div className="relative w-full bg-gray-900" style={{ paddingBottom: '41.67%' /* 500/1200 = 41.67% */ }}>
        {/* Skeleton loader */}
        {!imageLoaded && (
          <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900 animate-pulse" />
        )}
        <img 
          src={imageError ? fallbackImage : optimizedImageUrl} 
          alt={article.title}
          onError={handleImageError}
          onLoad={() => setImageLoaded(true)}
          width="1200"
          height="500"
          fetchpriority="high"
          decoding="sync"
          className={`absolute inset-0 w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
        
        <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
          <div className="flex items-center gap-2 mb-4">
            <Badge className="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-3 py-1">
              BREAKING NEWS
            </Badge>
            {article.source && (
              <Badge variant="outline" className="bg-white/20 text-white border-white/40 text-xs">
                {article.source}
              </Badge>
            )}
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 leading-tight group-hover:text-emerald-400 transition-colors">
            {article.title}
          </h1>
          <p className="text-lg text-gray-200 mb-4 line-clamp-2">
            {article.content ? article.content.substring(0, 200) + '...' : ''}
          </p>
          <div className="flex items-center space-x-4 text-sm text-gray-300">
            <div className="flex items-center">
              <User className="h-4 w-4 mr-1" />
              {article.author || article.source}
            </div>
            <div className="flex items-center">
              <Clock className="h-4 w-4 mr-1" />
              {formatDate(article.publishedDate)}
            </div>
            <Badge variant="outline" className="bg-white/20 text-white border-white/40">
              {article.category}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(HeroArticle);