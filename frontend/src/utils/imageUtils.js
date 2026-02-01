/**
 * Image optimization utilities for better performance
 */

// Default fallback image
export const FALLBACK_IMAGE = 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&q=60&fit=crop&auto=format';

/**
 * Optimize image URL for better performance
 * @param {string} url - Original image URL
 * @param {Object} options - Optimization options
 * @param {number} options.width - Desired width (default: 400)
 * @param {number} options.quality - Image quality 1-100 (default: 75)
 * @param {boolean} options.webp - Force WebP format (default: true)
 * @returns {string} Optimized image URL
 */
export const optimizeImageUrl = (url, options = {}) => {
  const { width = 400, quality = 75, webp = true } = options;
  
  if (!url) return FALLBACK_IMAGE;
  
  // Unsplash images - add optimization parameters
  if (url.includes('unsplash.com')) {
    const baseUrl = url.split('?')[0];
    const format = webp ? '&fm=webp' : '';
    return `${baseUrl}?w=${width}&q=${quality}&fit=crop&auto=format${format}`;
  }
  
  // Already optimized URLs
  if (url.includes('w=') && url.includes('q=')) {
    return url;
  }
  
  return url;
};

/**
 * Get srcset for responsive images
 * @param {string} url - Original image URL
 * @param {number[]} widths - Array of widths for srcset
 * @returns {string} srcset string
 */
export const getImageSrcSet = (url, widths = [320, 640, 960, 1280]) => {
  if (!url || !url.includes('unsplash.com')) return '';
  
  const baseUrl = url.split('?')[0];
  return widths
    .map(w => `${baseUrl}?w=${w}&q=75&fit=crop&auto=format&fm=webp ${w}w`)
    .join(', ');
};

/**
 * Get image sizes attribute for responsive images
 * @param {string} type - 'hero' | 'card' | 'thumbnail'
 * @returns {string} sizes attribute value
 */
export const getImageSizes = (type = 'card') => {
  switch (type) {
    case 'hero':
      return '(max-width: 640px) 100vw, (max-width: 1024px) 100vw, 1200px';
    case 'card':
      return '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 400px';
    case 'thumbnail':
      return '(max-width: 640px) 128px, 160px';
    default:
      return '100vw';
  }
};

/**
 * Preload critical images
 * @param {string[]} urls - Array of image URLs to preload
 */
export const preloadImages = (urls) => {
  if (typeof window === 'undefined') return;
  
  urls.forEach(url => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = optimizeImageUrl(url, { width: 1200, quality: 75 });
    document.head.appendChild(link);
  });
};
