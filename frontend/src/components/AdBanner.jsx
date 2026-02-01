import React, { useEffect } from 'react';

const AdBanner = ({ 
  slot, 
  format = 'auto', 
  responsive = true,
  style = {}
}) => {
  useEffect(() => {
    // Initialize ads after component mounts
    try {
      if (window.adsbygoogle && process.env.REACT_APP_ADSENSE_ID !== 'YOUR_ADSENSE_ID') {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      }
    } catch (err) {
      console.error('AdSense error:', err);
    }
  }, []);

  // Don't show ads if AdSense ID is not configured
  if (!process.env.REACT_APP_ADSENSE_ID || process.env.REACT_APP_ADSENSE_ID === 'YOUR_ADSENSE_ID') {
    return null; // Hide ads until configured
  }

  return (
    <div style={{ textAlign: 'center', margin: '20px 0', ...style }}>
      <ins 
        className="adsbygoogle"
        style={{ display: 'block' }}
        data-ad-client={process.env.REACT_APP_ADSENSE_ID}
        data-ad-slot={slot}
        data-ad-format={format}
        data-full-width-responsive={responsive.toString()}
      />
    </div>
  );
};

export default AdBanner;
