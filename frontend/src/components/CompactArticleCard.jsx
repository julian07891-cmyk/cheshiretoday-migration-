import React from 'react';
import { Clock, BookOpen } from 'lucide-react';
import { Badge } from './ui/badge';

const CompactArticleCard = ({ article, onClick, horizontal = false, priority = false }) => {
  const [imageError, setImageError] = React.useState(false);
  const [imageLoaded, setImageLoaded] = React.useState(false);
  
  // Calculate reading time (average 200 words per minute)
  const calculateReadTime = (content) => {
    if (!content) return 1;
    const words = content.split(/\s+/).length;
    const minutes = Math.ceil(words / 200);
    return minutes < 1 ? 1 : minutes;
  };

  const readTime = calculateReadTime(article.content);
  
  
  const displayCategory = (() => {
    const c = article.category || '';
    if (c === 'Local News') return 'Local';
    if (c === 'UK News') return 'UK';
    if (c === 'Tech' || c === 'Science') return 'AI & Tech';
    return c;
  })();
const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours < 1) {
      return 'Just now';
    }
    if (diffHours < 24) {
      return `${diffHours}h ago`;
    }
    return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
  };

  const handleImageError = () => {
    setImageError(true);
  };

  const fallbackImage = 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&q=60&fit=crop';

  // Optimized image URL with size parameters
  const getOptimizedImageUrl = (url, width = 400) => {
    if (!url) return fallbackImage;
    // For Unsplash images, add optimization parameters
    if (url.includes('unsplash.com')) {
      const baseUrl = url.split('?')[0];
      return `${baseUrl}?w=${width}&q=60&fit=crop&auto=format`;
    }
    return url;
  };

  if (horizontal) {
    return (
      <div 
        className="flex gap-4 cursor-pointer group hover:bg-gray-50 dark:hover:bg-gray-700 p-4 rounded-lg transition-colors touch-target min-h-[88px]"
        onClick={() => onClick(article)}
        data-testid={`article-card-${article.id}`}
      >
        <div className="relative w-28 h-20 md:w-32 md:h-24 flex-shrink-0 overflow-hidden rounded bg-gray-200 dark:bg-gray-700">
          {!imageLoaded && (
            <div className="absolute inset-0 bg-gray-200 dark:bg-gray-700 animate-pulse" />
          )}
          <img 
            src={imageError ? fallbackImage : getOptimizedImageUrl(article.image, 256)} 
            alt={article.title}
            onError={handleImageError}
            onLoad={() => setImageLoaded(true)}
            loading={priority ? "eager" : "lazy"}
            fetchpriority={priority ? "high" : "auto"}
            width="128"
            height="96"
            decoding="async"
            className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge className="bg-[#1E3A8A]/10 text-[#1E3A8A] dark:bg-blue-900 dark:text-blue-300 text-xs font-medium">
              {displayCategory}
            </Badge>
          </div>
          <h3 className="font-headline text-base md:text-lg font-semibold text-gray-900 dark:text-white line-clamp-2 group-hover:text-[#1E3A8A] dark:group-hover:text-blue-400 group-hover:underline underline-offset-2 transition-colors mb-1">
            {article.title}
          </h3>
          <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDate(article.publishedDate)}
            </span>
            <span className="flex items-center gap-1">
              <BookOpen className="h-3 w-3" />
              {readTime} min read
            </span>
            </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="cursor-pointer group relative bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-lg transition-all duration-300 touch-target"
      onClick={() => onClick(article)}
      data-testid={`article-card-${article.id}`}
    >
      <div className="relative h-44 md:h-48 overflow-hidden rounded-t-lg bg-gray-200 dark:bg-gray-700">
        {!imageLoaded && (
          <div className="absolute inset-0 bg-gray-200 dark:bg-gray-700 animate-pulse" />
        )}
        <img 
          src={imageError ? fallbackImage : getOptimizedImageUrl(article.image, 400)} 
          alt={article.title}
          onError={handleImageError}
          onLoad={() => setImageLoaded(true)}
          loading={priority ? "eager" : "lazy"}
          fetchpriority={priority ? "high" : "auto"}
          width="400"
          height="192"
          decoding="async"
          className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
        />
        <Badge className="absolute top-2 left-2 bg-[#1E3A8A] text-white text-xs font-medium">
          {displayCategory}
        </Badge>
      </div>
      
      <div className="p-4">
        <h3 className="font-headline text-lg md:text-xl font-semibold text-gray-900 dark:text-white line-clamp-2 group-hover:text-[#1E3A8A] dark:group-hover:text-blue-400 group-hover:underline underline-offset-2 transition-colors mb-2">
          {article.title}
        </h3>
        <p className="text-sm md:text-base text-gray-600 dark:text-gray-400 line-clamp-2 mb-3">
          {article.content ? article.content.substring(0, 120) + '...' : ''}
        </p>
        
        {/* Source and Date */}
        <div className="flex items-center justify-between text-xs md:text-sm text-gray-500 dark:text-gray-400">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {formatDate(article.publishedDate)}
            </span>
            <span className="flex items-center gap-1">
              <BookOpen className="h-4 w-4" />
              {readTime} min
            </span>
          </div>
          </div>
      </div>
    </div>
  );
};

export default React.memo(CompactArticleCard);