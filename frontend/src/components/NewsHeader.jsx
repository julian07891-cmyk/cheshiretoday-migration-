import React, { useState, useEffect, useRef } from 'react';
import { Search, Menu, X, Loader2, Facebook } from 'lucide-react';
import { Button } from './ui/button';
import FestiveBanner from './FestiveBanner';
import WeatherWidget from './WeatherWidget';
import DarkModeToggle from './DarkModeToggle';
import { articleService } from '../services/api';
import { buildArticleUrl } from '../utils/articleUrl';
import { trackEvent } from '../utils/trackEvent';
import { LOCATION_HUBS } from "../config/publicHubs";

const FACEBOOK_PAGE_URL = 'https://www.facebook.com/865430919994962';

const NewsHeader = ({ onMenuClick, categories, activeCategory, onCategoryChange, onArticleClick }) => {
  // Top-nav should be minimal (homepage focus). Keep other categories available elsewhere.
  const NAV_CATEGORY_NAMES = new Set(['All','Local','UK','Business']);
const navCategories = (categories || []).filter(c => NAV_CATEGORY_NAMES.has(c.name));
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLocation, setSelectedLocation] = useState(() => {
    try {
      const allowed = new Set(LOCATION_HUBS.map(({ slug }) => slug));
      const seg = (window.location.pathname || '/').split('/').filter(Boolean)[0] || '';
      return allowed.has(seg) ? seg : '';
    } catch (e) {
      return '';
    }
  });
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchStatus, setSearchStatus] = useState('');
  const [isFestive, setIsFestive] = useState(false);
  const searchRef = useRef(null);
  const mobileSearchRef = useRef(null);
  const searchRequestIdRef = useRef(0);

  useEffect(() => {
    const now = new Date();
    const endDate = new Date('2026-01-01T00:00:00');
    setIsFestive(now < endDate);
  }, []);

  // Close search when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      const clickedDesktopSearch = searchRef.current && searchRef.current.contains(event.target);
      const clickedMobileSearch = mobileSearchRef.current && mobileSearchRef.current.contains(event.target);
      if (!clickedDesktopSearch && !clickedMobileSearch) {
        searchRequestIdRef.current += 1;
        setSearchOpen(false);
        setSearchResults([]);
        setSearchLoading(false);
        setSearchStatus('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Search functionality with debounce
  useEffect(() => {
    const requestId = ++searchRequestIdRef.current;
    let cancelled = false;

    if (searchQuery.length < 2) {
      setSearchResults([]);
      setSearchLoading(false);
      setSearchStatus('');
      return () => {
        cancelled = true;
      };
    }

    const delayDebounceFn = setTimeout(async () => {
      if (cancelled || requestId !== searchRequestIdRef.current) return;
      setSearchLoading(true);
      setSearchStatus('Searching…');
      try {
        const results = await articleService.searchArticles(searchQuery);
        if (cancelled || requestId !== searchRequestIdRef.current) return;

        const limitedResults = results.slice(0, 5);
        setSearchResults(limitedResults);
        setSearchStatus(
          limitedResults.length === 0
            ? 'No articles found'
            : `${limitedResults.length} search ${limitedResults.length === 1 ? 'result' : 'results'}`
        );
      } catch (error) {
        if (cancelled || requestId !== searchRequestIdRef.current) return;
        console.error('Search error:', error);
        setSearchResults([]);
        setSearchStatus('Search is unavailable. Please try again.');
      } finally {
        if (!cancelled && requestId === searchRequestIdRef.current) {
          setSearchLoading(false);
        }
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(delayDebounceFn);
    };
  }, [searchQuery]);

  const handleSearchResultClick = (event, article) => {
    const modifiedClick = event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
    if (modifiedClick || event.defaultPrevented || !onArticleClick) return;

    event.preventDefault();
    onArticleClick(article);
    setSearchOpen(false);
    setMobileMenuOpen(false);
    setSearchQuery('');
    setSearchResults([]);
    setSearchStatus('');
  };

  const handleSearchKeyDown = (event) => {
    if (event.key !== 'Escape' || !searchOpen) return;

    event.preventDefault();
    searchRequestIdRef.current += 1;
    setSearchOpen(false);
    setSearchResults([]);
    setSearchLoading(false);
    setSearchStatus('');
  };

  const handleSearchQueryChange = (event) => {
    setSearchQuery(event.target.value);
    setSearchOpen(true);
  };

  const isHomeCategory = (category) => {
    const id = String(category?.id || '').toLowerCase();
    const name = String(category?.name || '').toLowerCase();
    return id === 'all' || name === 'all' || name === 'all news' || name === 'home';
  };

  const getCategoryLabel = (category) => isHomeCategory(category) ? 'Home' : category.name;

  const handleCategoryClick = (category) => {
    if (isHomeCategory(category)) {
      if (onCategoryChange) {
        onCategoryChange(category.id);
      } else {
        window.location.href = '/';
      }

      if (window.location.pathname !== '/' && !onCategoryChange) {
        window.location.href = '/';
      }

      setMobileMenuOpen(false);
      return;
    }

    onCategoryChange && onCategoryChange(category.id);
    setMobileMenuOpen(false);
  };

  return (
    <>
      {/* Festive Banner */}
      {isFestive && <FestiveBanner />}
      {/* Top Bar - Hidden on mobile for cleaner look */}
      <div className="hidden sm:block bg-[#1E3A8A] text-white">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between py-2 text-xs">
            {/* Date - left */}
            <span>
              {new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
            </span>

            {/* Weather - center/right */}
            <div className="hidden md:block">
              <WeatherWidget compact />
            </div>
          </div>
        </div>
      </div>

      {/* Main Header - Simplified on mobile */}
      <header className="bg-slate-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40 backdrop-blur-md bg-white/95 dark:bg-gray-800/95">
        <p role="status" aria-live="polite" className="sr-only">
          {searchStatus}
        </p>
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between py-3 md:py-4">
            {/* Logo - Compact on mobile */}
            <a href="/" aria-label="Cheshire Today home" className="flex items-center space-x-2 md:space-x-3 min-w-0">
              <img
                src="/logo.png"
                alt="Cheshire Today"
                className="h-8 md:h-10 w-auto flex-shrink-0"
              />
              <div className="min-w-0">
                <h1 className="font-headline text-xl md:text-3xl font-bold text-[#1E3A8A] dark:text-white truncate">Cheshire Today</h1>
                <p className="hidden md:block text-sm font-medium text-slate-600 dark:text-gray-300 tracking-wide">Local · Business · Finance</p>
              </div>
            </a>

            {/* Desktop Search & Controls */}
            <div className="hidden md:flex items-center space-x-4">
              <div className="relative mr-2">
                <select
                  aria-label="Choose location"
                  value={selectedLocation}
                  onChange={(e) => {
                    const v = e.target.value;
                    setSelectedLocation(v);
                    if (!v) return;
                    window.location.href = "/" + v;
                  }}
                  className={`w-44 appearance-none pr-9 h-10 px-4 py-2 border border-slate-300/50 dark:border-gray-700 shadow-sm hover:border-slate-400/60 dark:hover:border-gray-500 transition-all rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent dark:bg-gray-700 ${selectedLocation ? "text-slate-900 dark:text-white" : "text-slate-400 dark:text-gray-400"}`}
                >
                  <option value="">Cheshire towns</option>
                  {LOCATION_HUBS.map(({ slug, name }) => (
                    <option key={slug} value={slug}>{name}</option>
                  ))}
                </select>
</div>
              <div className="relative" ref={searchRef}>
                <input
                  type="text"
                  aria-label="Search news"
                  placeholder="Search news..."
                  value={searchQuery}
                  onChange={handleSearchQueryChange}
                  onFocus={() => setSearchOpen(true)}
                  onKeyDown={handleSearchKeyDown}
                  className="w-64 h-10 px-4 py-2 border border-slate-300/50 dark:border-gray-700 shadow-sm hover:border-slate-400/60 dark:hover:border-gray-500 transition-all rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent dark:bg-gray-700 dark:text-white"
                />
                {searchLoading ? (
                  <Loader2 aria-hidden="true" className="absolute right-3 top-2.5 h-5 w-5 text-gray-400 animate-spin" />
                ) : (
                  <Search aria-hidden="true" className="absolute right-3 top-2.5 h-5 w-5 text-gray-400" />
                )}

                {/* Search Results Dropdown */}
                {searchOpen && searchResults.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-slate-50 dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden z-50">
                    {searchResults.map((article) => (
                      <a
                        key={article.id}
                        href={buildArticleUrl(article)}
                        onClick={(event) => handleSearchResultClick(event, article)}
                        className="flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-0"
                      >
                        <img
                          src={article.image}
                          alt={article.title}
                          className="w-12 h-12 object-cover rounded"
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
                            {article.title}
                          </h4>
                          <span className="text-xs text-[#1E3A8A] dark:text-blue-400">
                            {article.category}
                          </span>
                        </div>
                      </a>
                    ))}
                  </div>
                )}
                {searchOpen && !searchLoading && searchResults.length === 0 && searchStatus && (
                  <div aria-hidden="true" className="absolute top-full left-0 right-0 mt-2 bg-slate-50 dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-3 text-sm text-gray-700 dark:text-gray-200 z-50">
                    {searchStatus}
                  </div>
                )}
              </div>

              <a
                href={FACEBOOK_PAGE_URL}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Follow Cheshire Today on Facebook"
                onClick={() => trackEvent("social_click", { network: "facebook", placement: "header_desktop", destination: FACEBOOK_PAGE_URL })}
                className="h-10 w-10 rounded-full border border-slate-300/50 dark:border-gray-700 flex items-center justify-center text-[#1E3A8A] dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors"
              >
                <Facebook className="h-4 w-4" />
              </a>

              {/* Dark Mode Toggle */}
              <DarkModeToggle />
            </div>

            {/* Mobile Menu Button */}
            <div className="flex items-center gap-2 md:hidden">
              <a
                href={FACEBOOK_PAGE_URL}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Follow Cheshire Today on Facebook"
                onClick={() => trackEvent("social_click", { network: "facebook", placement: "header_mobile_icon", destination: FACEBOOK_PAGE_URL })}
                className="h-9 w-9 rounded-full border border-slate-300/50 dark:border-gray-700 flex items-center justify-center text-[#1E3A8A] dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors"
              >
                <Facebook className="h-4 w-4" />
              </a>
              <DarkModeToggle />
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="h-6 w-6 dark:text-white" /> : <Menu className="h-6 w-6 dark:text-white" />}
              </button>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:block border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-1 py-2 overflow-x-auto">
              {navCategories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => handleCategoryClick(category)}
                  className={`px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors ${
                    String(activeCategory).toLowerCase() === String(category.id).toLowerCase()
                      ? 'bg-[#1E3A8A] text-white rounded'
                      : 'text-gray-700 dark:text-gray-300 hover:text-[#1E3A8A] dark:hover:text-blue-400'
                  }`}
                >
                  {getCategoryLabel(category)}
                </button>
              ))}
            </div>
          </nav>

          {/* Mobile Category Bar - REMOVED, using new CategoryTabs component in App.js */}
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-800">
            <div className="container mx-auto px-4 py-4">
                            {/* Location selector (mobile) */}
              <div className="mb-3">
                <select
                  aria-label="Choose location (mobile)"
                  value={selectedLocation}
                  onChange={(e) => {
                    const v = e.target.value;
                    setSelectedLocation(v);
                    if (!v) return;
                    window.location.href = "/" + v;
                  }}
                  className={`w-44 appearance-none pr-9 h-10 px-4 py-2 border border-slate-300/50 dark:border-gray-700 shadow-sm hover:border-slate-400/60 dark:hover:border-gray-500 transition-all rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent dark:bg-gray-700 ${selectedLocation ? "text-slate-900 dark:text-white" : "text-slate-400 dark:text-gray-400"}`}
                >
                  <option value="">Cheshire towns</option>
                  {LOCATION_HUBS.map(({ slug, name }) => (
                    <option key={slug} value={slug}>{name}</option>
                  ))}
                </select>
              </div>

{/* Mobile Search */}
              <div className="relative mb-4" ref={mobileSearchRef}>
                <input
                  type="text"
                  aria-label="Search news"
                  placeholder="Search news..."
                  value={searchQuery}
                  onChange={handleSearchQueryChange}
                  onFocus={() => setSearchOpen(true)}
                  onKeyDown={handleSearchKeyDown}
                  className="w-full h-10 px-4 py-2 border border-slate-300/50 dark:border-gray-700 shadow-sm hover:border-slate-400/60 dark:hover:border-gray-500 transition-all rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent dark:bg-gray-700 dark:text-white"
                />
                {searchLoading ? (
                  <Loader2 aria-hidden="true" className="absolute right-3 top-2.5 h-5 w-5 text-gray-400 animate-spin" />
                ) : (
                  <Search aria-hidden="true" className="absolute right-3 top-2.5 h-5 w-5 text-gray-400" />
                )}

                {searchOpen && searchResults.length > 0 && (
                  <div className="mt-2 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden z-50">
                    {searchResults.map((article) => (
                      <a
                        key={article.id}
                        href={buildArticleUrl(article)}
                        onClick={(event) => handleSearchResultClick(event, article)}
                        className="flex w-full items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-0 text-left"
                      >
                        <img
                          src={article.image}
                          alt={article.title}
                          className="w-12 h-12 object-cover rounded flex-shrink-0"
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
                            {article.title}
                          </h4>
                          <span className="text-xs text-[#1E3A8A] dark:text-blue-400">
                            {article.category}
                          </span>
                        </div>
                      </a>
                    ))}
                  </div>
                )}
                {searchOpen && !searchLoading && searchResults.length === 0 && searchStatus && (
                  <div aria-hidden="true" className="mt-2 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-3 text-sm text-gray-700 dark:text-gray-200 z-50">
                    {searchStatus}
                  </div>
                )}
              </div>

              {/* Mobile Weather */}
              <div className="mb-4">
                <WeatherWidget compact />
              </div>

              <a
                href={FACEBOOK_PAGE_URL}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => trackEvent("social_click", { network: "facebook", placement: "mobile_menu", destination: FACEBOOK_PAGE_URL })}
                className="mb-4 flex items-center justify-center gap-2 rounded-full bg-[#1877F2] px-4 py-2 text-sm font-semibold text-white hover:bg-[#166FE5] transition-colors"
              >
                <Facebook className="h-4 w-4" />
                Follow us on Facebook
              </a>

              <div className="space-y-2">
                {navCategories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => handleCategoryClick(category)}
                    className={`block w-full text-left px-4 py-2 rounded transition-colors ${
                      String(activeCategory).toLowerCase() === String(category.id).toLowerCase()
                        ? 'bg-[#1E3A8A] text-white'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    {getCategoryLabel(category)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </header>
    </>
  );
};

export default NewsHeader;
