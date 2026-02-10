import React, { useState, useEffect, useRef } from 'react';
import { getApiUrl } from '../utils/api';
import { Search, X, Clock, TrendingUp, Loader2 } from 'lucide-react';
import { Input } from './ui/input';
import { Badge } from './ui/badge';

const API_URL = getApiUrl();

const MobileSearch = ({ open, onClose, onArticleSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const inputRef = useRef(null);

  useEffect(() => {
    // Load recent searches from localStorage
    const saved = localStorage.getItem('recent_searches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
    if (!open) {
      setQuery('');
      setResults([]);
    }
  }, [open]);

  useEffect(() => {
    const searchArticles = async () => {
      if (query.length < 2) {
        setResults([]);
        return;
      }

      setLoading(true);
      try {
        const response = await fetch(`${API_URL}/api/articles?search=${encodeURIComponent(query)}&limit=10`);
        const data = await response.json();
        setResults(data.articles || []);
      } catch (e) {
        console.error('Search failed:', e);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(searchArticles, 300);
    return () => clearTimeout(debounce);
  }, [query]);

  const handleSelect = (article) => {
    // Save to recent searches
    const newRecent = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5);
    setRecentSearches(newRecent);
    localStorage.setItem('recent_searches', JSON.stringify(newRecent));
    
    onArticleSelect(article);
    onClose();
  };

  const handleRecentSearch = (search) => {
    setQuery(search);
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem('recent_searches');
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] bg-white dark:bg-gray-900 md:hidden">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <Input
            ref={inputRef}
            type="text"
            placeholder="Search articles..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-10 pr-4 h-12 text-lg bg-gray-100 dark:bg-gray-800 border-0"
            data-testid="mobile-search-input"
          />
        </div>
        <button
          onClick={onClose}
          className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          data-testid="mobile-search-close"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      {/* Content */}
      <div className="overflow-y-auto h-[calc(100vh-80px)] pb-20">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-[#1E3A8A]" />
          </div>
        )}

        {/* Search Results */}
        {query.length >= 2 && results.length > 0 && (
          <div className="p-4">
            <p className="text-sm text-gray-500 mb-3">{results.length} results for &ldquo;{query}&rdquo;</p>
            <div className="space-y-3">
              {results.map((article) => (
                <button
                  key={article.id}
                  onClick={() => handleSelect(article)}
                  className="w-full flex gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  data-testid={`search-result-${article.id}`}
                >
                  {article.image && (
                    <img
                      src={article.image}
                      alt=""
                      className="w-20 h-16 object-cover rounded-lg flex-shrink-0"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <Badge className="bg-[#1E3A8A] text-white text-xs mb-1">
                      {article.category}
                    </Badge>
                    <h3 className="font-semibold text-gray-900 dark:text-white text-sm line-clamp-2">
                      {article.title}
                    </h3>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* No Results */}
        {query.length >= 2 && !loading && results.length === 0 && (
          <div className="text-center py-12">
            <Search className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No articles found for &ldquo;{query}&rdquo;</p>
            <p className="text-sm text-gray-400 mt-1">Try different keywords</p>
          </div>
        )}

        {/* Recent Searches & Trending */}
        {query.length < 2 && (
          <div className="p-4">
            {/* Recent Searches */}
            {recentSearches.length > 0 && (
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                    <Clock className="h-4 w-4" />
                    <span className="text-sm font-medium">Recent Searches</span>
                  </div>
                  <button
                    onClick={clearRecentSearches}
                    className="text-xs text-[#1E3A8A] hover:underline"
                  >
                    Clear
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {recentSearches.map((search, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleRecentSearch(search)}
                      className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-full text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                    >
                      {search}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Trending Topics */}
            <div>
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-3">
                <TrendingUp className="h-4 w-4" />
                <span className="text-sm font-medium">Trending Topics</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {['Cheshire', 'Local News', 'Sports', 'Business', 'Weather', 'Traffic'].map((topic) => (
                  <button
                    key={topic}
                    onClick={() => setQuery(topic)}
                    className="px-3 py-1.5 bg-[#1E3A8A]/10 text-[#1E3A8A] rounded-full text-sm hover:bg-[#1E3A8A]/20"
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MobileSearch;
