import React, { useState, useEffect } from 'react';
import { TrendingUp, Eye, Flame } from 'lucide-react';

const MostReadWidget = ({ onArticleClick, apiUrl }) => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('today');

  const fetchMostRead = async (selectedPeriod) => {
    try {
      setLoading(true);
      const url = `${apiUrl}/api/articles/most-read?period=${selectedPeriod}&limit=5`;
      console.log('[MostRead] Fetching:', url);
      
      const response = await fetch(url);
      const data = await response.json();
      
      console.log('[MostRead] Response:', data);
      
      if (data.success && data.articles) {
        setArticles(data.articles);
      } else {
        setArticles([]);
      }
    } catch (error) {
      console.error('[MostRead] Error fetching:', error);
      setArticles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (apiUrl) {
      fetchMostRead(period);
    }
  }, [period, apiUrl]);

  const getPeriodLabel = () => {
    switch (period) {
      case 'today': return 'Today';
      case 'week': return 'This Week';
      case 'month': return 'This Month';
      default: return 'Today';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
            <Flame className="w-5 h-5 text-red-600 dark:text-red-400" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900 dark:text-white text-lg">Most Read</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">{getPeriodLabel()}</p>
          </div>
        </div>
        
        {/* Period Selector */}
        <div className="flex gap-1">
          {['today', 'week', 'month'].map((p) => (
            <button
              key={p}
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('[MostRead] Setting period to:', p);
                setPeriod(p);
              }}
              className={`px-2 py-1 text-xs rounded-md transition-colors cursor-pointer ${
                period === p
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
              data-testid={`most-read-period-${p}`}
            >
              {p === 'today' ? '24h' : p === 'week' ? '7d' : '30d'}
            </button>
          ))}
        </div>
      </div>

      {/* Articles List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="animate-pulse flex items-center gap-3">
              <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
              <div className="flex-1 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>
          ))}
        </div>
      ) : articles.length === 0 ? (
        <div className="text-center py-6 text-gray-500 dark:text-gray-400">
          <Eye className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No data yet</p>
          <p className="text-xs">Articles will appear here as readers engage</p>
        </div>
      ) : (
        <div className="space-y-2">
          {articles.map((article, index) => (
            <button
              key={article.id}
              onClick={() => onArticleClick && onArticleClick(article)}
              className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-left group"
              data-testid={`most-read-${index}`}
            >
              {/* Rank Badge */}
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                index === 0 
                  ? 'bg-gradient-to-br from-yellow-400 to-orange-500 text-white shadow-lg' 
                  : index === 1 
                  ? 'bg-gradient-to-br from-gray-300 to-gray-400 text-gray-800'
                  : index === 2
                  ? 'bg-gradient-to-br from-amber-600 to-amber-700 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
              }`}>
                {index + 1}
              </div>
              
              {/* Article Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors">
                  {article.title}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {article.category}
                  </span>
                  {article.views && (
                    <span className="text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
                      <Eye className="w-3 h-3" />
                      {article.views.toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
              
              {/* Trending indicator for top article */}
              {index === 0 && (
                <TrendingUp className="w-4 h-4 text-red-500 flex-shrink-0 animate-pulse" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default MostReadWidget;
