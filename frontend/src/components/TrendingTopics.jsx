import React, { useState, useEffect } from 'react';
import { TrendingUp, Hash, Flame } from 'lucide-react';

const TrendingTopics = ({ onTopicClick }) => {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const response = await fetch(`/api/trending-topics?limit=8`);
        if (!response.ok) throw new Error('Failed to fetch topics');
        const data = await response.json();
        setTopics(data.topics || []);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching trending topics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTopics();
    // Refresh every 5 minutes
    const interval = setInterval(fetchTopics, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [API_URL]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4" data-testid="trending-topics-loading">
        <div className="flex items-center mb-3 pb-3 border-b border-gray-200 dark:border-gray-700">
          <TrendingUp className="h-4 w-4 text-emerald-600 mr-2" />
          <h3 className="text-sm font-bold text-gray-900 dark:text-white">Trending in Cheshire — DEBUG</h3>
        </div>
        <div className="animate-pulse space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-6 bg-gray-200 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (error || topics.length === 0) {
    return null; // Don't show if no topics
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4" data-testid="trending-topics">
      <div className="flex items-center mb-3 pb-3 border-b-2 border-emerald-600">
        <TrendingUp className="h-4 w-4 text-emerald-600 mr-2" />
        <h3 className="text-sm font-bold text-gray-900 dark:text-white">Trending in Cheshire</h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {topics.map((topic, index) => (
          <button
            key={topic.topic}
            onClick={() => onTopicClick && onTopicClick(topic.topic)}
            className={`
              inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium
              transition-all duration-200 hover:scale-105
              ${topic.trending 
                ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white shadow-sm' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-emerald-100 dark:hover:bg-emerald-900'
              }
            `}
            data-testid={`topic-${topic.topic.toLowerCase()}`}
          >
            {topic.trending ? (
              <Flame className="h-3 w-3 mr-1" />
            ) : (
              <Hash className="h-3 w-3 mr-1 opacity-50" />
            )}
            {topic.topic}
            {topic.count > 2 && (
              <span className={`ml-1 text-xs ${topic.trending ? 'text-white/80' : 'text-gray-500 dark:text-gray-400'}`}>
                ({topic.count})
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export default TrendingTopics;
