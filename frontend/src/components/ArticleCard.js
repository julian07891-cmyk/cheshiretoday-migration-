import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Clock, User } from 'lucide-react';
import { useState } from 'react';

const ArticleCard = ({ article, onClick, featured = false }) => {
  const [imageError, setImageError] = useState(false);
  
  const fallbackImage = 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&h=500&fit=crop';
  
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
    return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  if (featured) {
    return (
      <Card 
        className="overflow-hidden cursor-pointer hover:shadow-xl transition-all duration-300 border-2 border-emerald-200"
        onClick={() => onClick(article)}
      >
        <div className="relative h-96">
          <img 
            src={imageError ? fallbackImage : article.image} 
            alt={article.title}
            onError={handleImageError}
            className="w-full h-full object-cover"
          />
          <div className="absolute top-4 left-4">
            <Badge className="bg-red-600 hover:bg-red-700 text-white font-semibold px-3 py-1">
              Featured Story
            </Badge>
          </div>
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-6">
            <Badge className="bg-emerald-600 text-white mb-3">
              {article.category}
            </Badge>
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-white mb-2 sm:mb-3 leading-tight">
              {article.title}
            </h2>
            <p className="text-gray-200 mb-4 line-clamp-2">
              {article.content.substring(0, 150)}...
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-300">
              <div className="flex items-center">
                <User className="h-4 w-4 mr-1" />
                {article.author}
              </div>
              <div className="flex items-center">
                <Clock className="h-4 w-4 mr-1" />
                {formatDate(article.publishedDate)}
              </div>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card 
      className="overflow-hidden cursor-pointer hover:shadow-lg transition-all duration-300 h-full flex flex-col"
      onClick={() => onClick(article)}
    >
      <div className="relative h-48">
        <img 
          src={imageError ? fallbackImage : article.image} 
          alt={article.title}
          onError={handleImageError}
          className="w-full h-full object-cover"
        />
        <div className="absolute top-3 left-3">
          <Badge className="bg-emerald-600 text-white">
            {article.category}
          </Badge>
        </div>
      </div>
      <CardHeader className="flex-1">
        <CardTitle className="text-xl hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors line-clamp-2">
          {article.title}
        </CardTitle>
        <CardDescription className="line-clamp-3 mt-2">
          {article.content.substring(0, 120)}...
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center">
            <User className="h-4 w-4 mr-1" />
            {article.author}
          </div>
          <div className="flex items-center">
            <Clock className="h-4 w-4 mr-1" />
            {formatDate(article.publishedDate)}
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {article.tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default ArticleCard;