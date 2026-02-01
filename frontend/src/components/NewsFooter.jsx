import React from 'react';
import { Facebook, Twitter, Instagram, Youtube, Mail, Settings, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import { newsletterService } from '../services/api';

const NewsFooter = () => {
  const currentYear = new Date().getFullYear();
  const [email, setEmail] = React.useState('');
  const [subscribed, setSubscribed] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState('');

  const footerLinks = {
    'News': ['Local News', 'UK News', 'Business', 'Tech', 'Sports'],
    'More': ['Events', 'Community', 'Weather', 'Health', 'Food'],
    'About': ['About Us', 'Contact', 'Advertise', 'Terms', 'Privacy', 'Affiliates']
  };

  const localAreas = [
    { name: 'All Cheshire', slug: 'cheshire-general' },
    { name: 'Macclesfield', slug: 'macclesfield' },
    { name: 'Wilmslow', slug: 'wilmslow' },
    { name: 'Knutsford', slug: 'knutsford' },
    { name: 'Chester', slug: 'chester' },
    { name: 'Warrington', slug: 'warrington' },
    { name: 'Crewe', slug: 'crewe' },
    { name: 'Northwich', slug: 'northwich' }
  ];

  const handleSubscribe = async (e) => {
    e.preventDefault();
    if (!email) return;
    
    setLoading(true);
    setErrorMessage('');
    
    try {
      const response = await newsletterService.subscribe(email);
      if (response.success) {
        setSubscribed(true);
        setTimeout(() => {
          setEmail('');
          setSubscribed(false);
        }, 5000);
      }
    } catch (error) {
      setErrorMessage('Failed to subscribe. Please try again.');
      setTimeout(() => setErrorMessage(''), 3000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <footer className="bg-gray-900 text-gray-300 mt-12">
      {/* Newsletter Section */}
      <div className="bg-gradient-to-r from-emerald-700 to-emerald-600 py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Mail className="h-10 w-10 text-white" />
            </div>
            <h3 className="text-3xl font-bold text-white mb-3">
              The Daily Brief
            </h3>
            <p className="text-white/90 mb-6 text-lg">
              Top Cheshire stories delivered to your inbox every morning at 7:30 AM
            </p>
            
            {!subscribed ? (
              <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-3 max-w-xl mx-auto">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email address"
                  required
                  disabled={loading}
                  className="flex-1 px-6 py-3 rounded-full text-gray-900 focus:outline-none focus:ring-4 focus:ring-emerald-300 border-2 border-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-white text-emerald-700 font-bold px-8 py-3 rounded-full hover:bg-gray-100 transition-colors whitespace-nowrap shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Subscribing...' : 'Subscribe Now'}
                </button>
              </form>
            ) : (
              <div className="bg-white/90 backdrop-blur-sm border-2 border-emerald-300 rounded-full px-6 py-3 max-w-xl mx-auto shadow-lg">
                <p className="text-emerald-800 font-semibold flex items-center justify-center gap-2">
                  ✓ Thank you! Your subscription is confirmed!
                </p>
              </div>
            )}
            
            {errorMessage && (
              <div className="bg-red-100 border-2 border-red-400 rounded-full px-6 py-3 max-w-xl mx-auto mt-3">
                <p className="text-red-800 font-semibold text-center">
                  {errorMessage}
                </p>
              </div>
            )}
            
            <p className="text-white/80 text-sm mt-4">
              No spam, unsubscribe anytime. Weekly Roundup & Breaking News alerts also available.
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-12">
        {/* Local Areas Section */}
        <div className="mb-10 pb-8 border-b border-gray-800">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="h-5 w-5 text-emerald-400" />
            <h4 className="text-white font-bold text-lg">Local News by Area</h4>
          </div>
          <div className="flex flex-wrap gap-3">
            {localAreas.map((area) => (
              <Link
                key={area.slug}
                to={`/${area.slug}`}
                className="px-4 py-2 bg-gray-800 hover:bg-emerald-600 text-gray-300 hover:text-white rounded-full text-sm transition-colors flex items-center gap-1"
              >
                <MapPin className="h-3 w-3" />
                {area.name}
              </Link>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          {/* Logo & Description */}
          <div className="col-span-2 md:col-span-1">
            <h3 className="text-white text-2xl font-bold mb-4">Cheshire Today</h3>
            <p className="text-sm text-gray-400 mb-4">
              Your trusted source for local Cheshire news and updates.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="hover:text-emerald-400 transition-colors">
                <Facebook className="h-5 w-5" />
              </a>
              <a href="#" className="hover:text-emerald-400 transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="#" className="hover:text-emerald-400 transition-colors">
                <Instagram className="h-5 w-5" />
              </a>
              <a href="#" className="hover:text-emerald-400 transition-colors">
                <Youtube className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Footer Links */}
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h4 className="text-white font-bold mb-4">{title}</h4>
              <ul className="space-y-2">
                {links.map((link) => {
                  // Map specific links to their routes
                  const linkMap = {
                    'Privacy': '/privacy',
                    'Terms': '/terms',
                    'Affiliates': '/affiliate-disclosure',
                  };
                  const href = linkMap[link];
                  
                  if (href) {
                    return (
                      <li key={link}>
                        <Link to={href} className="text-sm hover:text-emerald-400 transition-colors">
                          {link}
                        </Link>
                      </li>
                    );
                  }
                  
                  return (
                    <li key={link}>
                      <a href="#" className="text-sm hover:text-emerald-400 transition-colors">
                        {link}
                      </a>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        {/* Content Disclaimer */}
        <div className="border-t border-gray-800 pt-6 mt-8">
          <p className="text-xs text-gray-500 text-center max-w-3xl mx-auto leading-relaxed">
            Cheshire Today aggregates news from public RSS feeds provided by publishers. All article content, images, and trademarks belong to their respective original publishers. Click the source links to read full stories on their official websites.
          </p>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-800 pt-6 mt-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-gray-400">
              © {currentYear} Cheshire Today. All rights reserved.
            </p>
            <div className="flex items-center space-x-4 flex-wrap justify-center">
              <Link to="/privacy" className="text-sm hover:text-emerald-400 transition-colors">Privacy Policy</Link>
              <span className="text-gray-600">|</span>
              <Link to="/terms" className="text-sm hover:text-emerald-400 transition-colors">Terms of Service</Link>
              <span className="text-gray-600">|</span>
              <Link to="/affiliate-disclosure" className="text-sm hover:text-emerald-400 transition-colors">Affiliate Disclosure</Link>
              <span className="text-gray-600">|</span>
              <a href="mailto:news@cheshiretoday.co.uk" className="text-sm hover:text-emerald-400 transition-colors">Contact</a>
              <span className="text-gray-600">|</span>
              <Link to="/admin" className="text-sm hover:text-emerald-400 transition-colors flex items-center gap-1">
                <Settings className="h-3 w-3" />
                Admin
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default NewsFooter;