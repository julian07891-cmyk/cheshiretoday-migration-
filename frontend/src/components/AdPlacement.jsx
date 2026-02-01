import React, { useEffect, useRef } from 'react';

/**
 * Ad Placement Component for Google AdSense
 * 
 * Usage:
 * 1. Get approved by Google AdSense
 * 2. Add your AdSense script to index.html
 * 3. Set REACT_APP_ADSENSE_ID in your .env file
 * 4. Create ad units in AdSense dashboard and use their slot IDs
 * 
 * Ad Slot Types:
 * - header: 728x90 leaderboard (desktop) / 320x50 mobile banner
 * - sidebar: 300x250 medium rectangle
 * - in-feed: native in-feed ad between articles
 * - footer: 728x90 leaderboard
 */

const AdPlacement = ({ 
  slot,
  type = 'sidebar', // header, sidebar, in-feed, footer
  className = ''
}) => {
  const adsenseId = process.env.REACT_APP_ADSENSE_ID;
  const adRef = useRef(null);
  const isAdLoaded = useRef(false);
  
  useEffect(() => {
    // Only initialize once per ad slot
    if (isAdLoaded.current) return;
    
    const initAd = () => {
      try {
        if (window.adsbygoogle && adsenseId && adsenseId !== 'YOUR_ADSENSE_ID' && adRef.current) {
          // Check if this ad unit already has content
          const adElement = adRef.current.querySelector('.adsbygoogle');
          if (adElement && !adElement.getAttribute('data-adsbygoogle-status')) {
            (window.adsbygoogle = window.adsbygoogle || []).push({});
            isAdLoaded.current = true;
          }
        }
      } catch (err) {
        // AdSense errors are common, don't spam console
        if (!err.message?.includes('adsbygoogle')) {
          console.error('AdSense initialization error:', err);
        }
      }
    };

    // Wait for AdSense script to be ready
    if (window.adsbygoogle) {
      // Small delay to ensure DOM is ready
      const timer = setTimeout(initAd, 100);
      return () => clearTimeout(timer);
    } else {
      // If script isn't loaded yet, wait for it
      const checkAdSense = setInterval(() => {
        if (window.adsbygoogle) {
          clearInterval(checkAdSense);
          initAd();
        }
      }, 200);
      
      // Stop checking after 5 seconds
      const timeout = setTimeout(() => clearInterval(checkAdSense), 5000);
      return () => {
        clearInterval(checkAdSense);
        clearTimeout(timeout);
      };
    }
  }, [adsenseId, slot]);

  // Show placeholder when AdSense is not configured
  const showPlaceholder = !adsenseId || adsenseId === 'YOUR_ADSENSE_ID';

  // Get dimensions based on ad type
  const getAdStyle = () => {
    switch (type) {
      case 'header':
        return { minHeight: '90px' };
      case 'sidebar':
        return { minHeight: '250px' };
      case 'in-feed':
        return { minHeight: '120px' };
      case 'footer':
        return { minHeight: '90px' };
      default:
        return { minHeight: '250px' };
    }
  };

  // Placeholder for when ads aren't configured
  if (showPlaceholder) {
    return (
      <div 
        className={`bg-gray-100 dark:bg-gray-800 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg flex items-center justify-center ${className}`}
        style={getAdStyle()}
        data-testid={`ad-placeholder-${type}`}
      >
        <div className="text-center p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Advertisement</p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
            Your ad here
          </p>
        </div>
      </div>
    );
  }

  // Real AdSense ad
  return (
    <div ref={adRef} className={`ad-container ${className}`} style={getAdStyle()}>
      <ins 
        className="adsbygoogle"
        style={{ display: 'block' }}
        data-ad-client={adsenseId}
        data-ad-slot={slot}
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </div>
  );
};

/**
 * Sidebar Ad Component - 300x250 Medium Rectangle
 */
export const SidebarAd = ({ slot, className = '' }) => (
  <div className={`bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm ${className}`}>
    <p className="text-xs text-gray-400 dark:text-gray-500 mb-2 uppercase tracking-wide">Sponsored</p>
    <AdPlacement slot={slot} type="sidebar" />
  </div>
);

/**
 * In-Feed Ad Component - Native ad between articles
 */
export const InFeedAd = ({ slot, className = '' }) => (
  <div className={`bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700 ${className}`}>
    <p className="text-xs text-gray-400 dark:text-gray-500 mb-2 uppercase tracking-wide">Sponsored Content</p>
    <AdPlacement slot={slot} type="in-feed" />
  </div>
);

/**
 * Header Banner Ad - 728x90 Leaderboard
 */
export const HeaderAd = ({ slot, className = '' }) => (
  <div className={`w-full flex justify-center py-2 bg-gray-50 dark:bg-gray-900 ${className}`}>
    <AdPlacement slot={slot} type="header" />
  </div>
);

/**
 * Footer Banner Ad - 728x90 Leaderboard
 */
export const FooterAd = ({ slot, className = '' }) => (
  <div className={`w-full flex justify-center py-4 bg-gray-100 dark:bg-gray-800 ${className}`}>
    <AdPlacement slot={slot} type="footer" />
  </div>
);

export default AdPlacement;
