import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, TrendingUp, ChevronRight } from 'lucide-react';
import { getApiUrl } from '../utils/api';

const BreakingNewsTicker = ({ onHeadlineClick }) => {
  const [headlines, setHeadlines] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const headlinesRef = useRef([]); // Keep a ref to persist headlines across renders

  useEffect(() => {
    fetchHeadlines();
    // Refresh headlines every 10 minutes
    const interval = setInterval(fetchHeadlines, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Always set up rotation since we always have at least fallback headlines
    const timer = setInterval(() => {
      setCurrentIndex((prev) => {
        const totalHeadlines = headlines.length > 0 ? headlines.length : 2; // fallback has 2
        return (prev + 1) % totalHeadlines;
      });
    }, 5000); // Change headline every 5 seconds
    return () => clearInterval(timer);
  }, [headlines.length]); // Only depend on length, not the full array

  const fetchHeadlines = async () => {
    try {
      // API base URL (backend Render service)
      const API_URL = getApiUrl();
      const response = await fetch(API_URL + "/api/trending-headlines");
      const data = await response.json();
      if (data.headlines && data.headlines.length > 0) {
        setHeadlines(data.headlines);
        headlinesRef.current = data.headlines; // Store in ref as backup
      } else if (headlinesRef.current.length > 0) {
        // If API returns empty but we have cached headlines, keep them
        setHeadlines(headlinesRef.current);
      }
    } catch (error) {
      console.error('Error fetching headlines:', error);
      // On error, keep existing headlines if we have any
      if (headlinesRef.current.length > 0 && headlines.length === 0) {
        setHeadlines(headlinesRef.current);
      }
    } finally {
      setLoading(false);
    }
  };

  // Static fallback headlines to always show something
  const fallbackHeadlines = [
    { headline: "Stay updated with the latest Cheshire news", category: "Local News", scope: "cheshire" },
    { headline: "Breaking stories from across the UK", category: "UK News", scope: "uk" }
  ];

  // Use fallback if no headlines loaded
  const displayHeadlines = headlines.length > 0 ? headlines : fallbackHeadlines;
  const currentHeadline = displayHeadlines[currentIndex % displayHeadlines.length];

  // Show loading state briefly
  if (loading) {
    return (
      <div className="bg-red-600 text-white py-2">
        <div className="container mx-auto px-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white text-red-600 px-3 py-1 rounded-full font-bold text-sm">
              <AlertCircle className="h-4 w-4" />
              BREAKING
            </div>
            <span className="text-white/80">Loading latest news...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-red-600 text-white py-2 shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex items-center gap-3">
          {/* Breaking label */}
          <div className="flex items-center gap-2 bg-white text-red-600 px-3 py-1 rounded-full font-bold text-sm whitespace-nowrap animate-pulse">
            <AlertCircle className="h-4 w-4" />
            BREAKING
          </div>
          
          {/* Headline text - now clickable */}
          <div 
            className="flex-1 overflow-hidden cursor-pointer hover:underline transition-all"
            onClick={() => onHeadlineClick && onHeadlineClick(currentHeadline)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && onHeadlineClick && onHeadlineClick(currentHeadline)}
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 flex-shrink-0" />
              <span className="font-medium truncate hover:text-red-100">{currentHeadline.headline}</span>
              <span className="text-red-200 text-sm whitespace-nowrap hidden sm:inline">| {currentHeadline.category}</span>
            </div>
          </div>
          
          {/* Navigation dots */}
          {displayHeadlines.length > 1 && (
            <div className="hidden sm:flex items-center gap-2">
              <div className="flex gap-1">
                {displayHeadlines.slice(0, 5).map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentIndex(idx)}
                    className={`w-2 h-2 rounded-full transition-all ${
                      idx === currentIndex % displayHeadlines.length ? 'bg-white scale-125' : 'bg-red-400 hover:bg-red-300'
                    }`}
                    aria-label={`Go to headline ${idx + 1}`}
                  />
                ))}
              </div>
              <ChevronRight 
                className="h-4 w-4 cursor-pointer hover:scale-110 transition-transform" 
                onClick={() => setCurrentIndex((prev) => (prev + 1) % displayHeadlines.length)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BreakingNewsTicker;
