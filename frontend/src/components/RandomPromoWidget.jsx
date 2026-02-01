import React, { useMemo, useState, createContext, useContext } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, ArrowRight, Mail, ShoppingBag, Star, ExternalLink } from 'lucide-react';
import { Button } from './ui/button';

// Compact Jobs Banner - Fully Clickable
const JobsPromo = () => (
  <Link to="/jobs" className="block" data-testid="promo-jobs">
    <div className="rounded-xl overflow-hidden bg-gradient-to-r from-emerald-600 to-teal-600 shadow-md hover:shadow-lg transition-all hover:scale-[1.01] cursor-pointer">
      <div className="px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <Briefcase className="h-5 w-5 text-white" />
          </div>
          <div>
            <h4 className="font-semibold text-white">Cheshire Jobs</h4>
            <p className="text-emerald-100 text-sm">Find local opportunities near you</p>
          </div>
        </div>
        <Button size="sm" className="bg-white text-emerald-700 hover:bg-emerald-50 gap-1 pointer-events-none">
          Browse <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  </Link>
);

// Compact Subscribe Banner - Fully Clickable (scrolls to subscribe section)
const SubscribePromo = () => {
  const handleClick = (e) => {
    e.preventDefault();
    const subscribeSection = document.getElementById('subscribe');
    if (subscribeSection) {
      subscribeSection.scrollIntoView({ behavior: 'smooth' });
    } else {
      // If subscribe section not found, scroll to footer area where subscribe usually is
      window.scrollTo({ top: document.body.scrollHeight - 1000, behavior: 'smooth' });
    }
  };

  return (
    <a 
      href="#subscribe"
      onClick={handleClick}
      className="block rounded-xl overflow-hidden bg-gradient-to-r from-blue-600 to-indigo-600 shadow-md hover:shadow-lg transition-all hover:scale-[1.01] cursor-pointer" 
      data-testid="promo-subscribe"
    >
      <div className="px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <Mail className="h-5 w-5 text-white" />
          </div>
          <div>
            <h4 className="font-semibold text-white">The Daily Brief</h4>
            <p className="text-blue-100 text-sm">Top stories at 7:30 AM</p>
          </div>
        </div>
        <Button size="sm" className="bg-white text-blue-700 hover:bg-blue-50 gap-1 pointer-events-none">
          Subscribe <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </a>
  );
};

// Amazon Affiliate Banner - Opens Amazon deals in new tab
const AmazonAffiliatePromo = () => (
  <a 
    href="https://www.amazon.co.uk/deals?tag=cheshiretoday-21" 
    target="_blank" 
    rel="noopener noreferrer"
    className="block"
    data-testid="promo-amazon"
  >
    <div className="rounded-xl overflow-hidden bg-gradient-to-r from-amber-500 to-orange-500 shadow-md hover:shadow-lg transition-all hover:scale-[1.01] cursor-pointer">
      <div className="px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <ShoppingBag className="h-5 w-5 text-white" />
          </div>
          <div>
            <h4 className="font-semibold text-white flex items-center gap-1">
              <Star className="h-4 w-4 fill-yellow-300 text-yellow-300" />
              Today&apos;s Deals
            </h4>
            <p className="text-amber-100 text-sm">Shop top offers on Amazon</p>
          </div>
        </div>
        <Button size="sm" className="bg-white text-amber-700 hover:bg-amber-50 gap-1 pointer-events-none">
          Shop Now <ExternalLink className="h-4 w-4" />
        </Button>
      </div>
    </div>
  </a>
);

// Legacy Affiliate Promo (scrolls to top) - keeping for backwards compatibility
const AffiliatePromo = () => {
  const handleClick = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div 
      onClick={handleClick}
      className="rounded-xl overflow-hidden bg-gradient-to-r from-purple-600 to-pink-600 shadow-md hover:shadow-lg transition-all hover:scale-[1.01] cursor-pointer"
      data-testid="promo-affiliate"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
    >
      <div className="px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <Star className="h-5 w-5 text-white" />
          </div>
          <div>
            <h4 className="font-semibold text-white">Top Picks</h4>
            <p className="text-purple-100 text-sm">Handpicked deals for you</p>
          </div>
        </div>
        <Button size="sm" className="bg-white text-purple-700 hover:bg-purple-50 gap-1 pointer-events-none">
          View Deals <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

// Context to share shuffled widget order across all instances
const PromoContext = createContext(null);

// Provider component that shuffles widgets once per page load
export const PromoWidgetProvider = ({ children }) => {
  // Shuffle array using Fisher-Yates algorithm
  const shuffleArray = (array) => {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  };

  // Create a shuffled order of widgets that persists for this session
  const [widgetOrder] = useState(() => {
    const widgets = [JobsPromo, AmazonAffiliatePromo, SubscribePromo];
    // Create multiple cycles so we have enough for all positions
    return [...shuffleArray(widgets), ...shuffleArray(widgets), ...shuffleArray(widgets)];
  });

  return (
    <PromoContext.Provider value={widgetOrder}>
      {children}
    </PromoContext.Provider>
  );
};

// Random Promo Widget - picks widget based on position in shuffled order
// Each position gets a different widget, cycling through all 3 without immediate repeats
export const RandomPromoWidget = ({ seed = 0 }) => {
  const widgetOrder = useContext(PromoContext);
  
  // Fallback if not wrapped in provider
  const [fallbackOrder] = useState(() => {
    const widgets = [JobsPromo, AmazonAffiliatePromo, SubscribePromo];
    return [...widgets, ...widgets, ...widgets];
  });
  
  const order = widgetOrder || fallbackOrder;
  const WidgetComponent = order[seed % order.length];
  
  return (
    <div className="my-6">
      <WidgetComponent />
    </div>
  );
};

// Export individual components for direct use if needed
export { JobsPromo, SubscribePromo, AffiliatePromo, AmazonAffiliatePromo };

export default RandomPromoWidget;
