import React, { useState } from 'react';
import { Share2, Copy, Check, Twitter, Facebook, MessageCircle } from 'lucide-react';

const ShareAlertsButton = ({ siteUrl = 'https://cheshiretoday.co.uk' }) => {
  const [copied, setCopied] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const shareText = "🔔 Get instant breaking news alerts from Cheshire Today! Enable push notifications to stay informed about what's happening in your area.";
  const shareUrl = siteUrl;

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(`${shareText}\n\n${shareUrl}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const shareToTwitter = () => {
    const tweetText = encodeURIComponent(`${shareText}`);
    const tweetUrl = encodeURIComponent(shareUrl);
    window.open(`https://twitter.com/intent/tweet?text=${tweetText}&url=${tweetUrl}`, '_blank');
  };

  const shareToFacebook = () => {
    const fbUrl = encodeURIComponent(shareUrl);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${fbUrl}&quote=${encodeURIComponent(shareText)}`, '_blank');
  };

  const shareToWhatsApp = () => {
    const waText = encodeURIComponent(`${shareText}\n\n${shareUrl}`);
    window.open(`https://wa.me/?text=${waText}`, '_blank');
  };

  const nativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Cheshire Today - Breaking News Alerts',
          text: shareText,
          url: shareUrl
        });
      } catch (err) {
        if (err.name !== 'AbortError') {
          setShowMenu(true);
        }
      }
    } else {
      setShowMenu(true);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={nativeShare}
        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg hover:from-emerald-600 hover:to-teal-600 transition-all shadow-md hover:shadow-lg text-sm font-medium"
        data-testid="share-alerts-btn"
      >
        <Share2 className="w-4 h-4" />
        <span>Share Alerts</span>
      </button>

      {showMenu && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setShowMenu(false)}
          />
          
          {/* Share Menu */}
          <div className="absolute right-0 top-full mt-2 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-3 z-50 min-w-[200px]">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 px-2">Share with friends</p>
            
            <button
              onClick={() => { shareToTwitter(); setShowMenu(false); }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-black flex items-center justify-center">
                <Twitter className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm text-gray-700 dark:text-gray-200">Twitter / X</span>
            </button>
            
            <button
              onClick={() => { shareToFacebook(); setShowMenu(false); }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                <Facebook className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm text-gray-700 dark:text-gray-200">Facebook</span>
            </button>
            
            <button
              onClick={() => { shareToWhatsApp(); setShowMenu(false); }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                <MessageCircle className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm text-gray-700 dark:text-gray-200">WhatsApp</span>
            </button>
            
            <div className="border-t border-gray-200 dark:border-gray-700 my-2" />
            
            <button
              onClick={() => { copyLink(); setShowMenu(false); }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                {copied ? (
                  <Check className="w-4 h-4 text-green-600" />
                ) : (
                  <Copy className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                )}
              </div>
              <span className="text-sm text-gray-700 dark:text-gray-200">
                {copied ? 'Copied!' : 'Copy Link'}
              </span>
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ShareAlertsButton;
