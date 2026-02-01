import React, { useRef, useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const CategoryTabs = ({ categories, activeCategory, onCategoryChange }) => {
  const scrollRef = useRef(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(true);

  // Filter out 'all' from categories since we add it manually
  const filteredCategories = (categories || []).filter(cat => 
    cat.id !== 'all' && cat.name?.toLowerCase() !== 'all'
  );
  
  const allCategories = [
    { id: 'all', name: 'All News' },
    ...filteredCategories
  ];

  const checkScrollPosition = () => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
      setShowLeftArrow(scrollLeft > 10);
      setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  useEffect(() => {
    const scrollEl = scrollRef.current;
    if (scrollEl) {
      scrollEl.addEventListener('scroll', checkScrollPosition);
      checkScrollPosition();
      return () => scrollEl.removeEventListener('scroll', checkScrollPosition);
    }
  }, []);

  const scroll = (direction) => {
    if (scrollRef.current) {
      const scrollAmount = 150;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  return (
    <div className="sticky top-0 z-40 bg-white dark:bg-gray-900 shadow-sm" data-testid="category-tabs">
      <div className="relative">
        {/* Left scroll indicator - Desktop only */}
        {showLeftArrow && (
          <button
            onClick={() => scroll('left')}
            className="hidden sm:flex absolute left-0 top-0 bottom-0 z-10 items-center justify-center w-8 bg-gradient-to-r from-white dark:from-gray-900 to-transparent"
            aria-label="Scroll left"
          >
            <ChevronLeft className="h-5 w-5 text-gray-500" />
          </button>
        )}

        {/* Scrollable tabs */}
        <div
          ref={scrollRef}
          className="flex overflow-x-auto hide-scrollbar py-3 px-4 gap-2 scroll-smooth"
          style={{ WebkitOverflowScrolling: 'touch' }}
        >
          {allCategories.map((category) => {
            const isActive = activeCategory === category.id || 
              (activeCategory === 'all' && category.id === 'all') ||
              (category.name && activeCategory === category.name);
            
            return (
              <button
                key={category.id || category.name}
                onClick={() => onCategoryChange(category.id || category.name)}
                className={`
                  flex-shrink-0 px-4 py-2.5 rounded-full text-sm font-medium
                  touch-target transition-all duration-200
                  ${isActive
                    ? 'bg-[#1E3A8A] text-white shadow-md'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }
                `}
                data-testid={`category-${category.id || category.name}`}
              >
                {category.name}
              </button>
            );
          })}
        </div>

        {/* Right scroll indicator - Desktop only */}
        {showRightArrow && (
          <button
            onClick={() => scroll('right')}
            className="hidden sm:flex absolute right-0 top-0 bottom-0 z-10 items-center justify-center w-8 bg-gradient-to-l from-white dark:from-gray-900 to-transparent"
            aria-label="Scroll right"
          >
            <ChevronRight className="h-5 w-5 text-gray-500" />
          </button>
        )}
      </div>
    </div>
  );
};

export default CategoryTabs;
