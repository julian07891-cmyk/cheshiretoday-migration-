import React, { useState, useEffect } from 'react';
import { getApiUrl } from "../utils/api";
import { Clock } from 'lucide-react';

const RelatedArticles = ({ articleId, onArticleClick }) => {
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (articleId) {
      fetchRelatedArticles();
    }
  }, [articleId]);

  const fetchRelatedArticles = async () => {
    try {
      setLoading(true);
      const API_URL = getApiUrl();
      const response = await fetch(API_URL + "/api/related-articles/" + encodeURIComponent(articleId) + "?limit=4");
      const data = await response.json();
      setRelated(data);
    } catch (error) {
      console.error('Error fetching related articles:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', { 
      day: 'numeric', 
      month: 'short'
    });
  };

  if (loading) {
    return (
      <div className="mt-8 pt-8 border-t">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Related Articles</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-gray-200 h-24 rounded-lg mb-2"></div>
              <div className="bg-gray-200 h-4 rounded mb-1"></div>
              <div className="bg-gray-200 h-3 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (related.length === 0) {
    return null;
  }

  return (
    <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Related Articles</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {related.map((article) => (
          <div 
            key={article.id}
            onClick={() => onArticleClick(article)}
            className="cursor-pointer group"
          >
            <div className="relative overflow-hidden rounded-lg mb-2">
              <img
                src={article.image}
                alt={article.title}
                className="w-full h-24 object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div className="absolute top-2 left-2">
                <span className="bg-emerald-600 text-white text-xs px-2 py-0.5 rounded">
                  {article.category}
                </span>
              </div>
            </div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 line-clamp-2 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
              {article.title}
            </h4>
            <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 mt-1">
              <Clock className="h-3 w-3 mr-1" />
              {formatDate(article.publishedDate)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RelatedArticles;
