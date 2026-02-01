import React from 'react';
import { Share2, Facebook, Twitter, Linkedin, Mail, MessageCircle } from 'lucide-react';

const SocialShare = ({ article, url }) => {
  // Use the server-side share URL for proper Open Graph tags
  const articleId = article?.id;
  const shareUrl = articleId 
    ? `https://cheshiretoday.co.uk/api/share/${articleId}`
    : (url || window.location.href);
  
  // For native share and email, use the direct article URL
  const directUrl = articleId 
    ? `https://cheshiretoday.co.uk/article/${articleId}`
    : (url || window.location.href);
    
  const title = article?.title || 'Cheshire Today';
  const text = article?.content?.substring(0, 200) || 'Check out this article';

  const shareLinks = {
    // Facebook, Twitter, LinkedIn use the /api/share/ URL for proper meta tags
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(title)}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`,
    // WhatsApp and email use direct URL since they just share text
    whatsapp: `https://wa.me/?text=${encodeURIComponent(title + ' ' + directUrl)}`,
    email: `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(text + '\n\n' + directUrl)}`
  };

  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: title,
          text: text,
          url: directUrl
        });
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Share error:', err);
        }
      }
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* Native Share (Mobile) */}
      {navigator.share && (
        <button
          onClick={handleNativeShare}
          className="p-2 rounded-full hover:bg-gray-100 transition-colors"
          aria-label="Share"
        >
          <Share2 className="w-5 h-5 text-gray-600" />
        </button>
      )}

      {/* Facebook */}
      <a
        href={shareLinks.facebook}
        target="_blank"
        rel="noopener noreferrer"
        className="p-2 rounded-full hover:bg-blue-50 transition-colors"
        aria-label="Share on Facebook"
      >
        <Facebook className="w-5 h-5 text-blue-600" />
      </a>

      {/* Twitter */}
      <a
        href={shareLinks.twitter}
        target="_blank"
        rel="noopener noreferrer"
        className="p-2 rounded-full hover:bg-blue-50 transition-colors"
        aria-label="Share on Twitter"
      >
        <Twitter className="w-5 h-5 text-blue-400" />
      </a>

      {/* WhatsApp */}
      <a
        href={shareLinks.whatsapp}
        target="_blank"
        rel="noopener noreferrer"
        className="p-2 rounded-full hover:bg-green-50 transition-colors"
        aria-label="Share on WhatsApp"
      >
        <MessageCircle className="w-5 h-5 text-green-600" />
      </a>

      {/* LinkedIn */}
      <a
        href={shareLinks.linkedin}
        target="_blank"
        rel="noopener noreferrer"
        className="p-2 rounded-full hover:bg-blue-50 transition-colors"
        aria-label="Share on LinkedIn"
      >
        <Linkedin className="w-5 h-5 text-blue-700" />
      </a>

      {/* Email */}
      <a
        href={shareLinks.email}
        className="p-2 rounded-full hover:bg-gray-100 transition-colors"
        aria-label="Share via Email"
      >
        <Mail className="w-5 h-5 text-gray-600" />
      </a>
    </div>
  );
};

export default SocialShare;
