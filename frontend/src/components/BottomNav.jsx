import React from 'react';
import { Home, Newspaper, Search, Menu } from 'lucide-react';

const BottomNav = ({ activeTab, onTabChange, onSearchClick, onMenuClick }) => {
  const tabs = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'topics', label: 'Topics', icon: Newspaper },
    { id: 'search', label: 'Search', icon: Search },
    { id: 'menu', label: 'More', icon: Menu },
  ];

  return (
    <nav 
      className="md:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 z-50 shadow-lg"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0)' }}
      data-testid="bottom-nav"
    >
      <div className="flex items-center justify-around h-16">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          
          return (
            <button
              key={tab.id}
              onClick={() => {
                if (tab.id === 'search') {
                  onSearchClick?.();
                } else if (tab.id === 'menu') {
                  onMenuClick?.();
                } else {
                  onTabChange?.(tab.id);
                }
              }}
              className={`flex flex-col items-center justify-center w-full h-full touch-target transition-colors duration-200 ${
                isActive 
                  ? 'text-[#1E3A8A] dark:text-blue-400' 
                  : 'text-gray-500 dark:text-gray-400'
              }`}
              data-testid={`bottom-nav-${tab.id}`}
            >
              <Icon 
                className={`h-6 w-6 mb-1 transition-transform duration-200 ${
                  isActive ? 'scale-110' : ''
                }`} 
                strokeWidth={isActive ? 2.5 : 2}
              />
              <span className={`text-xs font-medium ${
                isActive ? 'font-semibold' : ''
              }`}>
                {tab.label}
              </span>
              {isActive && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-0.5 bg-[#1E3A8A] dark:bg-blue-400 rounded-full" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default BottomNav;
