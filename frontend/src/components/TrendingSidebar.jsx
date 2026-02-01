import React from 'react';
import { TrendingUp, Eye, Flame } from 'lucide-react';
import CompactArticleCard from './CompactArticleCard';
import WeatherWidget from './WeatherWidget';
import TrendingTopics from './TrendingTopics';

const TrendingSidebar = ({ articles, onArticleClick, onSearch }) => {
  // Simulated view counts for "Most Read" ranking
  const getViewCount = (index) => Math.floor(Math.random() * 300 + 400 * (5 - index));

  // Handle topic click - trigger search
  const handleTopicClick = (topic) => {
    if (onSearch) {
      onSearch(topic);
    }
  };

  return (
    <div className="space-y-6">
      {/* Weather Widget */}
      <WeatherWidget />

      {/* Trending Topics - NEW */}
      <TrendingTopics onTopicClick={handleTopicClick} />

      {/* Most Read / Trending Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center mb-4 pb-4 border-b-2 border-red-500">
          <Flame className="h-5 w-5 text-red-500 mr-2" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Most Read</h2>
        </div>
        <div className="space-y-4">
          {articles.slice(0, 5).map((article, index) => (
            <div 
              key={article.id} 
              className="flex items-start gap-3 cursor-pointer group p-2 -mx-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors" 
              onClick={() => onArticleClick(article)}
            >
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                index === 0 ? 'bg-red-500 text-white' :
                index === 1 ? 'bg-orange-500 text-white' :
                index === 2 ? 'bg-yellow-500 text-white' :
                'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'
              }`}>
                {index + 1}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-gray-900 dark:text-white line-clamp-2 group-hover:text-emerald-600 transition-colors">
                  {article.title}
                </h3>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400">
                  <Eye className="h-3 w-3" />
                  <span>{getViewCount(index)} reads</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Latest Updates */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center mb-4 pb-4 border-b-2 border-emerald-600">
          <TrendingUp className="h-5 w-5 text-emerald-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Latest Updates</h2>
        </div>
        <div className="space-y-4">
          {articles.slice(5, 10).map((article) => (
            <CompactArticleCard
              key={article.id}
              article={article}
              onClick={onArticleClick}
              horizontal={true}
            />
          ))}
        </div>
      </div>

      {/* Newsletter Promo */}
      <div className="bg-gradient-to-br from-emerald-600 to-emerald-800 rounded-lg shadow-md p-6 text-white">
        <h3 className="text-xl font-bold mb-2">Stay Informed</h3>
        <p className="text-sm text-emerald-100 mb-4">
          Get The Daily Brief — Top Cheshire stories at 7:30 AM
        </p>
        <button 
          onClick={() => {
            // Scroll to footer newsletter section
            const footer = document.querySelector('footer');
            if (footer) {
              footer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          }}
          className="w-full bg-white text-emerald-600 font-bold py-2 px-4 rounded hover:bg-gray-100 transition-colors"
        >
          Subscribe Now
        </button>
      </div>
    </div>
  );
};

export default TrendingSidebar;