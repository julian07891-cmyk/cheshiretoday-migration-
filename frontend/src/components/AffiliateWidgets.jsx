import React from 'react';
import { ExternalLink, ShoppingBag, Star, TrendingUp } from 'lucide-react';
import { Badge } from './ui/badge';

// Affiliate configuration - Amazon Associates only
export const AFFILIATE_CONFIG = {
  amazon: {
    associateId: 'cheshiretoday-21', // ✅ ACTIVE
    marketplace: 'amazon.co.uk',
  }
};

// Generate Amazon affiliate link
export const getAmazonLink = (productUrl) => {
  const tag = AFFILIATE_CONFIG.amazon.associateId;
  if (productUrl.includes('amazon.co.uk')) {
    // Handle both product and search URLs
    const separator = productUrl.includes('?') ? '&' : '?';
    return `${productUrl}${separator}tag=${tag}`;
  }
  return productUrl;
};

// Sample products for different categories - Multiple products per category for rotation
// Products are randomly selected on each page load for variety
export const SAMPLE_PRODUCTS = {
  'Local News': [
    { name: 'Cheshire Books & Guides', price: 'From £8.99', image: 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=200', url: 'https://www.amazon.co.uk/s?k=cheshire+books+history', rating: 4.5 },
    { name: 'UK Road Atlas', price: 'From £6.99', image: 'https://images.unsplash.com/photo-1524578271613-d550eacf6090?w=200', url: 'https://www.amazon.co.uk/s?k=uk+road+atlas+map', rating: 4.6 },
    { name: 'Walking Boots', price: 'From £39.99', image: 'https://images.unsplash.com/photo-1551107696-a4b0c5a0d9a2?w=200', url: 'https://www.amazon.co.uk/s?k=walking+boots+waterproof', rating: 4.5 },
    { name: 'Binoculars', price: 'From £29.99', image: 'https://images.unsplash.com/photo-1502982720700-bfff97f2ecac?w=200', url: 'https://www.amazon.co.uk/s?k=binoculars+birdwatching', rating: 4.4 },
    { name: 'Outdoor Jacket', price: 'From £34.99', image: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=200', url: 'https://www.amazon.co.uk/s?k=waterproof+jacket+mens+womens', rating: 4.6 },
    { name: 'Thermos Flask', price: 'From £14.99', image: 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=200', url: 'https://www.amazon.co.uk/s?k=thermos+flask+hot+drinks', rating: 4.7 },
  ],
  'Sports': [
    { name: 'Footballs', price: 'From £10.00', image: 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=200', url: 'https://www.amazon.co.uk/s?k=football+size+5', rating: 4.5 },
    { name: 'Fitness Trackers', price: 'From £29.99', image: 'https://images.unsplash.com/photo-1576243345690-4e4b79b63288?w=200', url: 'https://www.amazon.co.uk/s?k=fitness+tracker', rating: 4.4 },
    { name: 'Running Shoes', price: 'From £39.99', image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200', url: 'https://www.amazon.co.uk/s?k=running+shoes+mens+womens', rating: 4.5 },
    { name: 'Resistance Bands', price: 'From £8.99', image: 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=200', url: 'https://www.amazon.co.uk/s?k=resistance+bands+set', rating: 4.6 },
    { name: 'Sports Water Bottle', price: 'From £9.99', image: 'https://images.unsplash.com/photo-1523362628745-0c100150b504?w=200', url: 'https://www.amazon.co.uk/s?k=sports+water+bottle', rating: 4.5 },
    { name: 'Gym Bag', price: 'From £15.99', image: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=200', url: 'https://www.amazon.co.uk/s?k=gym+bag+sports', rating: 4.4 },
    { name: 'Dumbbells Set', price: 'From £24.99', image: 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=200', url: 'https://www.amazon.co.uk/s?k=dumbbells+set+home', rating: 4.5 },
    { name: 'Yoga Mat', price: 'From £12.99', image: 'https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=200', url: 'https://www.amazon.co.uk/s?k=yoga+mat+non+slip', rating: 4.6 },
  ],
  'Tech': [
    { name: 'Smart Speakers', price: 'From £29.99', image: 'https://images.unsplash.com/photo-1543512214-318c7553f230?w=200', url: 'https://www.amazon.co.uk/s?k=echo+dot+alexa', rating: 4.7 },
    { name: 'Streaming Devices', price: 'From £29.99', image: 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=200', url: 'https://www.amazon.co.uk/s?k=fire+tv+stick', rating: 4.6 },
    { name: 'Wireless Earbuds', price: 'From £19.99', image: 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=200', url: 'https://www.amazon.co.uk/s?k=wireless+earbuds+bluetooth', rating: 4.4 },
    { name: 'Phone Cases', price: 'From £7.99', image: 'https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=200', url: 'https://www.amazon.co.uk/s?k=phone+case+protective', rating: 4.3 },
    { name: 'USB-C Cables', price: 'From £6.99', image: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=200', url: 'https://www.amazon.co.uk/s?k=usb+c+cable+fast+charging', rating: 4.5 },
    { name: 'Power Banks', price: 'From £15.99', image: 'https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=200', url: 'https://www.amazon.co.uk/s?k=power+bank+portable+charger', rating: 4.6 },
    { name: 'Tablet Stands', price: 'From £12.99', image: 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=200', url: 'https://www.amazon.co.uk/s?k=tablet+stand+adjustable', rating: 4.5 },
    { name: 'Webcams', price: 'From £24.99', image: 'https://images.unsplash.com/photo-1587826080692-f439cd0b70da?w=200', url: 'https://www.amazon.co.uk/s?k=webcam+hd+1080p', rating: 4.4 },
  ],
  'Health': [
    { name: 'Fitness Trackers', price: 'From £29.99', image: 'https://images.unsplash.com/photo-1576243345690-4e4b79b63288?w=200', url: 'https://www.amazon.co.uk/s?k=fitbit+fitness+tracker', rating: 4.4 },
    { name: 'Yoga Mats', price: 'From £12.99', image: 'https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=200', url: 'https://www.amazon.co.uk/s?k=yoga+mat+non+slip', rating: 4.5 },
    { name: 'Vitamins & Supplements', price: 'From £8.99', image: 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=200', url: 'https://www.amazon.co.uk/s?k=vitamins+supplements', rating: 4.5 },
    { name: 'Blood Pressure Monitor', price: 'From £19.99', image: 'https://images.unsplash.com/photo-1559757175-5700dde675bc?w=200', url: 'https://www.amazon.co.uk/s?k=blood+pressure+monitor+home', rating: 4.4 },
    { name: 'Electric Toothbrush', price: 'From £24.99', image: 'https://images.unsplash.com/photo-1559467278-020d6a30a42b?w=200', url: 'https://www.amazon.co.uk/s?k=electric+toothbrush', rating: 4.6 },
    { name: 'Sleep Masks', price: 'From £6.99', image: 'https://images.unsplash.com/photo-1531353826977-0941b4779a1c?w=200', url: 'https://www.amazon.co.uk/s?k=sleep+mask+eye+mask', rating: 4.4 },
    { name: 'Foam Rollers', price: 'From £14.99', image: 'https://images.unsplash.com/photo-1600881333168-2ef49b341f30?w=200', url: 'https://www.amazon.co.uk/s?k=foam+roller+muscle', rating: 4.5 },
  ],
  'Entertainment': [
    { name: 'Fire TV Devices', price: 'From £29.99', image: 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=200', url: 'https://www.amazon.co.uk/s?k=fire+tv+stick+4k', rating: 4.6 },
    { name: 'Echo Devices', price: 'From £29.99', image: 'https://images.unsplash.com/photo-1543512214-318c7553f230?w=200', url: 'https://www.amazon.co.uk/s?k=amazon+echo', rating: 4.7 },
    { name: 'Board Games', price: 'From £14.99', image: 'https://images.unsplash.com/photo-1611371805429-8b5c1b2c34ba?w=200', url: 'https://www.amazon.co.uk/s?k=board+games+family', rating: 4.5 },
    { name: 'Headphones', price: 'From £24.99', image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200', url: 'https://www.amazon.co.uk/s?k=headphones+wireless', rating: 4.5 },
    { name: 'Kindle E-Readers', price: 'From £84.99', image: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=200', url: 'https://www.amazon.co.uk/s?k=kindle+paperwhite', rating: 4.7 },
    { name: 'Gaming Accessories', price: 'From £19.99', image: 'https://images.unsplash.com/photo-1592840496694-26d035b52b48?w=200', url: 'https://www.amazon.co.uk/s?k=gaming+controller+accessories', rating: 4.4 },
  ],
  'UK News': [
    { name: 'Kindle E-Readers', price: 'From £84.99', image: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=200', url: 'https://www.amazon.co.uk/s?k=kindle+paperwhite', rating: 4.7 },
    { name: 'UK Travel Guides', price: 'From £9.99', image: 'https://images.unsplash.com/photo-1524578271613-d550eacf6090?w=200', url: 'https://www.amazon.co.uk/s?k=uk+travel+guide+book', rating: 4.6 },
    { name: 'Umbrellas', price: 'From £12.99', image: 'https://images.unsplash.com/photo-1534309466160-70b22cc6252c?w=200', url: 'https://www.amazon.co.uk/s?k=umbrella+windproof', rating: 4.4 },
    { name: 'Raincoats', price: 'From £24.99', image: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=200', url: 'https://www.amazon.co.uk/s?k=raincoat+waterproof', rating: 4.5 },
    { name: 'Travel Mugs', price: 'From £9.99', image: 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=200', url: 'https://www.amazon.co.uk/s?k=travel+mug+insulated', rating: 4.6 },
    { name: 'Newspapers & Magazines', price: 'From £2.99', image: 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=200', url: 'https://www.amazon.co.uk/s?k=newspaper+subscription', rating: 4.3 },
  ],
  'Business': [
    { name: 'Kindle E-Readers', price: 'From £84.99', image: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=200', url: 'https://www.amazon.co.uk/s?k=kindle+paperwhite', rating: 4.7 },
    { name: 'Power Banks', price: 'From £15.99', image: 'https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=200', url: 'https://www.amazon.co.uk/s?k=anker+power+bank', rating: 4.7 },
    { name: 'Laptop Bags', price: 'From £19.99', image: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=200', url: 'https://www.amazon.co.uk/s?k=laptop+bag+briefcase', rating: 4.5 },
    { name: 'Wireless Mouse', price: 'From £9.99', image: 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=200', url: 'https://www.amazon.co.uk/s?k=wireless+mouse+ergonomic', rating: 4.5 },
    { name: 'Desk Organisers', price: 'From £12.99', image: 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=200', url: 'https://www.amazon.co.uk/s?k=desk+organiser+office', rating: 4.4 },
    { name: 'Business Books', price: 'From £8.99', image: 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=200', url: 'https://www.amazon.co.uk/s?k=business+books+bestsellers', rating: 4.6 },
    { name: 'Noise-Cancelling Headphones', price: 'From £49.99', image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200', url: 'https://www.amazon.co.uk/s?k=noise+cancelling+headphones', rating: 4.5 },
  ],
  'Science': [
    { name: 'Science Books', price: 'From £9.99', image: 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=200', url: 'https://www.amazon.co.uk/s?k=science+books+popular', rating: 4.6 },
    { name: 'Telescopes', price: 'From £49.99', image: 'https://images.unsplash.com/photo-1502982720700-bfff97f2ecac?w=200', url: 'https://www.amazon.co.uk/s?k=telescope+astronomy', rating: 4.4 },
    { name: 'Microscopes', price: 'From £29.99', image: 'https://images.unsplash.com/photo-1516728778615-2d590ea1855e?w=200', url: 'https://www.amazon.co.uk/s?k=microscope+kids+educational', rating: 4.5 },
    { name: 'Science Kits', price: 'From £14.99', image: 'https://images.unsplash.com/photo-1567789884554-0b844b5e7c34?w=200', url: 'https://www.amazon.co.uk/s?k=science+kit+experiments', rating: 4.5 },
  ],
  'Education': [
    { name: 'Stationery Sets', price: 'From £8.99', image: 'https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?w=200', url: 'https://www.amazon.co.uk/s?k=stationery+set+school', rating: 4.5 },
    { name: 'Calculators', price: 'From £9.99', image: 'https://images.unsplash.com/photo-1564466809058-bf4114d55352?w=200', url: 'https://www.amazon.co.uk/s?k=scientific+calculator', rating: 4.6 },
    { name: 'Backpacks', price: 'From £19.99', image: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=200', url: 'https://www.amazon.co.uk/s?k=school+backpack', rating: 4.5 },
    { name: 'Kindle E-Readers', price: 'From £84.99', image: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=200', url: 'https://www.amazon.co.uk/s?k=kindle+paperwhite', rating: 4.7 },
    { name: 'Desk Lamps', price: 'From £14.99', image: 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=200', url: 'https://www.amazon.co.uk/s?k=desk+lamp+led+reading', rating: 4.5 },
  ],
  'default': [
    { name: 'Echo Smart Speakers', price: 'From £29.99', image: 'https://images.unsplash.com/photo-1543512214-318c7553f230?w=200', url: 'https://www.amazon.co.uk/s?k=amazon+echo+dot', rating: 4.7 },
    { name: 'Fire TV Streaming', price: 'From £29.99', image: 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=200', url: 'https://www.amazon.co.uk/s?k=fire+tv+stick', rating: 4.6 },
    { name: 'Kindle E-Readers', price: 'From £84.99', image: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=200', url: 'https://www.amazon.co.uk/s?k=kindle+paperwhite', rating: 4.7 },
    { name: 'Wireless Earbuds', price: 'From £19.99', image: 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=200', url: 'https://www.amazon.co.uk/s?k=wireless+earbuds', rating: 4.4 },
    { name: 'Power Banks', price: 'From £15.99', image: 'https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=200', url: 'https://www.amazon.co.uk/s?k=power+bank+portable', rating: 4.6 },
    { name: 'Phone Accessories', price: 'From £7.99', image: 'https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=200', url: 'https://www.amazon.co.uk/s?k=phone+accessories', rating: 4.4 },
    { name: 'Smart Home Devices', price: 'From £24.99', image: 'https://images.unsplash.com/photo-1558089687-f282ffcbc126?w=200', url: 'https://www.amazon.co.uk/s?k=smart+home+devices', rating: 4.5 },
    { name: 'Headphones', price: 'From £24.99', image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200', url: 'https://www.amazon.co.uk/s?k=headphones+bluetooth', rating: 4.5 },
  ]
};

// Helper function to randomly select products from a category
export const getRandomProducts = (category, count = 2, offset = 0) => {
  const products = SAMPLE_PRODUCTS[category] || SAMPLE_PRODUCTS['default'];
  const shuffled = [...products].sort(() => 0.5 - Math.random());
  // Skip 'offset' products and take 'count' products
  return shuffled.slice(offset, offset + count);
};

// Star rating component
const StarRating = ({ rating }) => {
  const fullStars = Math.floor(rating);
  const hasHalf = rating % 1 >= 0.5;
  
  return (
    <div className="flex items-center gap-0.5">
      {[...Array(5)].map((_, i) => (
        <Star
          key={i}
          className={`h-3 w-3 ${
            i < fullStars 
              ? 'text-yellow-400 fill-yellow-400' 
              : i === fullStars && hasHalf 
                ? 'text-yellow-400 fill-yellow-400/50'
                : 'text-gray-300 dark:text-gray-500'
          }`}
        />
      ))}
      <span className="text-xs text-gray-600 dark:text-gray-300 ml-1">{rating}</span>
    </div>
  );
};

// Single product card
export const ProductCard = ({ product, compact = false }) => {
  const affiliateUrl = getAmazonLink(product.url);
  
  if (compact) {
    return (
      <a
        href={affiliateUrl}
        target="_blank"
        rel="noopener noreferrer sponsored"
        className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        data-testid="affiliate-product-compact"
      >
        <img src={product.image} alt={product.name} className="w-12 h-12 object-cover rounded" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{product.name}</p>
          <p className="text-sm font-bold text-[#1E3A8A]">{product.price}</p>
        </div>
        <ExternalLink className="h-4 w-4 text-gray-400 flex-shrink-0" />
      </a>
    );
  }
  
  return (
    <a
      href={affiliateUrl}
      target="_blank"
      rel="noopener noreferrer sponsored"
      className="block bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow group"
      data-testid="affiliate-product-card"
    >
      <div className="aspect-square overflow-hidden bg-gray-100">
        <img 
          src={product.image} 
          alt={product.name} 
          className="w-full h-full object-cover group-hover:scale-105 transition-transform"
        />
      </div>
      <div className="p-3">
        <h4 className="font-medium text-gray-900 dark:text-white text-sm line-clamp-2 mb-1">
          {product.name}
        </h4>
        <StarRating rating={product.rating} />
        <div className="flex items-center justify-between mt-2">
          <span className="text-lg font-bold text-[#1E3A8A]">{product.price}</span>
          <span className="text-xs text-gray-500 flex items-center gap-1">
            View <ExternalLink className="h-3 w-3" />
          </span>
        </div>
      </div>
    </a>
  );
};

// Helper to fetch products from database - exported for use in parent components
export const fetchDatabaseProducts = async () => {
  try {
    const apiUrl = (
      process.env.REACT_APP_BACKEND_URL ||
      (typeof window !== 'undefined' ? window.location.origin : '')
    );
    
    const response = await fetch(`${apiUrl}/api/affiliates/public`);
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.products && data.products.length > 0) {
        return data;
      }
    }
    return null;
  } catch (error) {
    console.log('Using fallback affiliate products');
    return null;
  }
};

// Hook to get products (database or fallback)
const useAffiliateProducts = (category, count, offset = 0) => {
  const [products, setProducts] = React.useState([]);
  const [loaded, setLoaded] = React.useState(false);

  React.useEffect(() => {
    let mounted = true;
    
    const loadProducts = async () => {
      // Try database first
      const dbData = await fetchDatabaseProducts();
      
      if (!mounted) return;
      
      if (dbData && dbData.products.length > 0) {
        // Use database products
        const categoryProducts = dbData.by_category[category] || dbData.by_category['default'] || dbData.products;
        const shuffled = [...categoryProducts].sort(() => 0.5 - Math.random());
        // Skip 'offset' products and take 'count' products
        setProducts(shuffled.slice(offset, offset + count));
      } else {
        // Fallback to hardcoded products with offset support
        setProducts(getRandomProducts(category, count, offset));
      }
      setLoaded(true);
    };
    
    loadProducts();
    
    return () => { mounted = false; };
  }, [category, count, offset]);

  return { products, loaded };
};

// Enhanced Sidebar widget - Larger product cards with better visibility
export const AffiliateWidgetSidebar = ({ category = 'default' }) => {
  const { products, loaded } = useAffiliateProducts(category, 2);
  
  if (!loaded || products.length === 0) {
    return null;
  }
  
  return (
    <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-gray-800 dark:to-gray-900 rounded-xl border-2 border-amber-200 dark:border-amber-900/50 p-5 shadow-lg" data-testid="affiliate-sidebar">
      {/* Header with eye-catching design */}
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-amber-200 dark:border-gray-700">
        <div className="bg-amber-500 p-2 rounded-lg">
          <ShoppingBag className="h-5 w-5 text-white" />
        </div>
        <div>
          <h3 className="font-bold text-gray-900 dark:text-white text-lg">Top Picks</h3>
          <p className="text-xs text-amber-700 dark:text-amber-300">Handpicked for you</p>
        </div>
        <Badge className="ml-auto bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 text-xs">Ad</Badge>
      </div>
      
      {/* Large Product Cards */}
      <div className="space-y-4">
        {products.map((product, idx) => (
          <a
            key={idx}
            href={getAmazonLink(product.url)}
            target="_blank"
            rel="noopener noreferrer sponsored"
            className="block bg-white dark:bg-gray-700 rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 group"
          >
            {/* Large Image */}
            <div className="aspect-[4/3] overflow-hidden bg-gray-100 dark:bg-gray-600">
              <img 
                src={product.image} 
                alt={product.name} 
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
              />
            </div>
            
            {/* Product Info */}
            <div className="p-4 bg-white dark:bg-gray-700">
              <h4 className="font-semibold text-gray-900 dark:text-gray-50 text-base mb-2 line-clamp-2 group-hover:text-[#1E3A8A] dark:group-hover:text-blue-300 transition-colors">
                {product.name}
              </h4>
              <StarRating rating={product.rating} />
              <div className="flex items-center justify-between mt-3">
                <span className="text-xl font-bold text-amber-600 dark:text-amber-400">{product.price}</span>
                <span className="bg-[#1E3A8A] text-white text-xs px-3 py-1.5 rounded-full font-medium flex items-center gap-1 group-hover:bg-[#2d4a9e] transition-colors">
                  View Deal <ExternalLink className="h-3 w-3" />
                </span>
              </div>
            </div>
          </a>
        ))}
      </div>
      
      <p className="text-xs text-amber-700 dark:text-gray-300 mt-4 text-center">
        <a href="/affiliate-disclosure" className="hover:underline underline-offset-2">Affiliate links • We may earn commission</a>
      </p>
    </div>
  );
};

// In-article widget - Shows first 2 products
// Can receive products prop directly to avoid duplicate fetching
export const AffiliateWidgetInline = ({ category = 'default', title = 'You Might Like', products: propProducts = null }) => {
  const { products: fetchedProducts, loaded } = useAffiliateProducts(category, 4, 0); // Get first 4 products
  
  // Use prop products if provided, otherwise use fetched products
  const displayProducts = propProducts || fetchedProducts.slice(0, 2);
  
  // If using prop products, we don't need to wait for loaded state
  if (propProducts) {
    if (propProducts.length === 0) return null;
  } else {
    if (!loaded || displayProducts.length === 0) return null;
  }
  
  return (
    <div className="my-8 relative" data-testid="affiliate-inline">
      {/* Subtle separator */}
      <div className="absolute left-0 right-0 top-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-600 to-transparent"></div>
      
      <div className="pt-6 pb-2">
        {/* Native header - looks like editorial recommendation */}
        <div className="flex items-center gap-3 mb-5">
          <div className="flex items-center gap-2">
            <div className="w-1 h-6 bg-emerald-500 rounded-full"></div>
            <h4 className="font-bold text-gray-900 dark:text-white text-lg">{title}</h4>
          </div>
          <Badge variant="outline" className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600">Sponsored</Badge>
        </div>
        
        {/* Product Cards - Large and prominent */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {displayProducts.map((product, idx) => (
            <a
              key={idx}
              href={getAmazonLink(product.url)}
              target="_blank"
              rel="noopener noreferrer sponsored"
              className="flex gap-4 p-4 bg-white dark:bg-gray-700 rounded-xl border border-gray-200 dark:border-gray-600 hover:border-emerald-300 dark:hover:border-emerald-500 hover:shadow-lg transition-all duration-300 group"
            >
              {/* Product Image - Larger */}
              <div className="w-28 h-28 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-600">
                <img 
                  src={product.image} 
                  alt={product.name} 
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
              </div>
              
              {/* Product Details */}
              <div className="flex-1 flex flex-col justify-between py-1">
                <div>
                  <h5 className="font-semibold text-gray-900 dark:text-gray-50 text-base mb-1 group-hover:text-emerald-600 dark:group-hover:text-emerald-300 transition-colors line-clamp-2">
                    {product.name}
                  </h5>
                  <StarRating rating={product.rating} />
                </div>
                
                <div className="flex items-center justify-between mt-2">
                  <span className="text-lg font-bold text-amber-600 dark:text-amber-400">{product.price}</span>
                  <span className="text-sm text-[#1E3A8A] dark:text-blue-300 font-medium flex items-center gap-1 group-hover:underline underline-offset-2">
                    Shop now <ExternalLink className="h-3.5 w-3.5" />
                  </span>
                </div>
              </div>
            </a>
          ))}
        </div>
        
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-4 text-center">
          We may earn commission from purchases. <a href="/affiliate-disclosure" className="text-gray-600 dark:text-gray-300 hover:underline underline-offset-2">Learn more</a>
        </p>
      </div>
      
      {/* Subtle separator */}
      <div className="absolute left-0 right-0 bottom-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-600 to-transparent"></div>
    </div>
  );
};

// End of article widget - Shows DIFFERENT products from inline widget
// Can receive products prop directly to avoid duplicate fetching
export const AffiliateWidgetEndArticle = ({ category = 'default', products: propProducts = null }) => {
  const [products, setProducts] = React.useState([]);
  const [loaded, setLoaded] = React.useState(false);

  React.useEffect(() => {
    // If products are passed as props with items, use them directly
    if (propProducts && propProducts.length > 0) {
      setProducts(propProducts);
      setLoaded(true);
      return;
    }
    
    // If propProducts is explicitly an empty array (parent still loading), wait
    if (propProducts !== null && propProducts.length === 0) {
      // Parent is passing products but hasn't loaded yet
      return;
    }
    
    let mounted = true;
    
    const loadProducts = async () => {
      // Get products from database or fallback
      const dbData = await fetchDatabaseProducts();
      
      if (!mounted) return;
      
      let allProducts = [];
      
      if (dbData && dbData.products.length > 0) {
        const categoryProducts = dbData.by_category[category] || [];
        const defaultProducts = dbData.by_category['default'] || dbData.products;
        allProducts = [...categoryProducts, ...defaultProducts];
      } else {
        // Use hardcoded products
        const categoryProducts = SAMPLE_PRODUCTS[category] || [];
        const defaultProducts = SAMPLE_PRODUCTS['default'] || [];
        allProducts = [...categoryProducts, ...defaultProducts];
      }
      
      // Remove duplicates
      const unique = allProducts.filter((product, index, self) => 
        index === self.findIndex(p => p.name === product.name)
      );
      
      // Skip first 2 (used by "You Might Like") and take next 4
      // Use a different sorting to ensure variety
      const sorted = [...unique].sort((a, b) => a.name.localeCompare(b.name));
      const selectedProducts = sorted.length > 2 ? sorted.slice(2, 6) : sorted.slice(0, 4);
      
      setProducts(selectedProducts);
      setLoaded(true);
    };
    
    loadProducts();
    
    return () => { mounted = false; };
  }, [category, propProducts]);
  
  if (!loaded || products.length === 0) {
    return null;
  }
  
  return (
    <div className="mt-8 pt-8 border-t-2 border-gray-200 dark:border-gray-700" data-testid="affiliate-end-article">
      {/* Enhanced Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-gradient-to-r from-emerald-500 to-teal-500 p-2.5 rounded-xl">
          <ShoppingBag className="h-6 w-6 text-white" />
        </div>
        <div>
          <h3 className="font-bold text-gray-900 dark:text-white text-xl">You Might Also Like</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">Recommended products for you</p>
        </div>
        <Badge className="ml-auto bg-gray-100 dark:bg-gray-800 text-gray-500 text-xs">Sponsored</Badge>
      </div>
      
      {/* Large Product Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {products.map((product, idx) => (
          <a
            key={idx}
            href={getAmazonLink(product.url)}
            target="_blank"
            rel="noopener noreferrer sponsored"
            className="block bg-white dark:bg-gray-700 rounded-xl border border-gray-200 dark:border-gray-600 overflow-hidden hover:shadow-xl hover:border-emerald-300 dark:hover:border-emerald-500 transition-all duration-300 group"
          >
            {/* Larger Image */}
            <div className="aspect-square overflow-hidden bg-gray-100 dark:bg-gray-600">
              <img 
                src={product.image} 
                alt={product.name} 
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
              />
            </div>
            
            {/* Product Info */}
            <div className="p-4 bg-white dark:bg-gray-700">
              <h4 className="font-semibold text-gray-900 dark:text-gray-50 text-sm line-clamp-2 mb-2 min-h-[2.5rem] group-hover:text-emerald-600 dark:group-hover:text-emerald-300 transition-colors">
                {product.name}
              </h4>
              <StarRating rating={product.rating} />
              <div className="flex items-center justify-between mt-3">
                <span className="text-lg font-bold text-amber-600 dark:text-amber-400">{product.price}</span>
                <ExternalLink className="h-4 w-4 text-gray-400 dark:text-gray-300 group-hover:text-emerald-500 transition-colors" />
              </div>
            </div>
          </a>
        ))}
      </div>
      
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-5 text-center">
        We may earn commission from links on this page. <a href="/affiliate-disclosure" className="text-emerald-600 dark:text-emerald-400 hover:underline underline-offset-2">Affiliate disclosure</a>
      </p>
    </div>
  );
};

// Mobile-optimized affiliate banner - Shows prominently between sections on mobile
export const AffiliateWidgetMobile = ({ category = 'default' }) => {
  const { products, loaded } = useAffiliateProducts(category, 1);
  
  if (!loaded || products.length === 0) {
    return null;
  }
  
  const product = products[0];
  
  return (
    <div className="block lg:hidden my-6" data-testid="affiliate-mobile">
      <a
        href={getAmazonLink(product.url)}
        target="_blank"
        rel="noopener noreferrer sponsored"
        className="block bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 dark:from-gray-800 dark:via-gray-700 dark:to-gray-800 rounded-2xl border-2 border-amber-200 dark:border-amber-800/50 p-4 shadow-lg"
      >
        {/* Header */}
        <div className="flex items-center gap-2 mb-3">
          <div className="bg-amber-500 p-1.5 rounded-lg">
            <TrendingUp className="h-4 w-4 text-white" />
          </div>
          <span className="font-bold text-gray-900 dark:text-white text-sm">Featured Deal</span>
          <Badge className="ml-auto bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 text-xs">Ad</Badge>
        </div>
        
        {/* Product Card - Horizontal Layout */}
        <div className="flex gap-4 bg-white dark:bg-gray-700 rounded-xl p-3 shadow-md">
          {/* Large Image */}
          <div className="w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-600">
            <img 
              src={product.image} 
              alt={product.name} 
              className="w-full h-full object-cover"
            />
          </div>
          
          {/* Product Info */}
          <div className="flex-1 flex flex-col justify-between">
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-gray-50 text-sm line-clamp-2 mb-1">
                {product.name}
              </h4>
              <StarRating rating={product.rating} />
            </div>
            
            <div className="flex items-center justify-between mt-2">
              <span className="text-lg font-bold text-amber-600 dark:text-amber-400">{product.price}</span>
              <span className="bg-[#1E3A8A] text-white text-xs px-3 py-1.5 rounded-full font-medium flex items-center gap-1">
                Shop <ExternalLink className="h-3 w-3" />
              </span>
            </div>
          </div>
        </div>
        
        <p className="text-xs text-amber-700 dark:text-gray-300 mt-2 text-center">
          Affiliate link • We may earn commission
        </p>
      </a>
    </div>
  );
};

export default {
  ProductCard,
  AffiliateWidgetSidebar,
  AffiliateWidgetInline,
  AffiliateWidgetEndArticle,
  AffiliateWidgetMobile,
  AFFILIATE_CONFIG,
  getAmazonLink,
};
