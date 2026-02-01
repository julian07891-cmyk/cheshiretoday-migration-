import React from 'react';
import { TrendingUp, Eye } from 'lucide-react';

const MostReadSection = ({ articles, onArticleClick }) => {
  // Get most read articles (for now, we'll use the first 5 as they're typically most recent/popular)
  // In production, you'd track actual view counts
  const mostRead = articles.slice(0, 5);

  if (mostRead.length === 0) return null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center gap-2 mb-4 pb-4 border-b-2 border-red-500">
        <TrendingUp className="h-5 w-5 text-red-500" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Most Read</h2>
      </div>
      
      <div className="space-y-4">
        {mostRead.map((article, index) => (
          <div 
            key={article.id} 
            className="flex items-start gap-4 cursor-pointer group p-2 -mx-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            onClick={() => onArticleClick(article)}
          >
            {/* Rank Number */}
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
              index === 0 ? 'bg-red-500 text-white' :
              index === 1 ? 'bg-orange-500 text-white' :
              index === 2 ? 'bg-yellow-500 text-white' :
              'bg-gray-200 text-gray-600 dark:bg-gray-600 dark:text-gray-300'
            }`}>
              {index + 1}
            </div>
            
            {/* Article Info */}
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white line-clamp-2 group-hover:text-emerald-600 transition-colors">
                {article.title}
              </h3>
              <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400">
                <span className="bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                  {article.category}
                </span>
                <span className="flex items-center gap-1">
                  <Eye className="h-3 w-3" />
                  {/* Simulated view count based on position */}
                  {Math.floor(Math.random() * 500 + 200 * (5 - index))} reads
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MostReadSection;
