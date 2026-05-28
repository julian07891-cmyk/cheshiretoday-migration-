import React from 'react';
import { Mail, Settings, Facebook } from 'lucide-react';
import { Link } from 'react-router-dom';
import { newsletterService } from '../services/api';
import NewsletterPreferences from './NewsletterPreferences';
import { trackEvent } from '../utils/trackEvent';

const FACEBOOK_PAGE_URL = 'https://www.facebook.com/865430919994962';

const NewsFooter = () => {
  const currentYear = new Date().getFullYear();
  const [email, setEmail] = React.useState('');
  const [subscribed, setSubscribed] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState('');
  const [showPreferences, setShowPreferences] = React.useState(false);

  const footerLinks = {
    'Coverage': ['Local', 'Business', 'UK'],
    'Guides': ['AI & Tech', 'Finance'],
    'Company': ['Contact', 'Advertise']
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
      const cleanedEmail = (email || "").trim().replace(/\s+/g, "");
      setEmail(cleanedEmail);
      if (!cleanedEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanedEmail)) {
        setErrorMessage("Please enter a valid email address.");
        setLoading(false);
        setTimeout(() => setErrorMessage(""), 3000);
        return;
      }
      const response = await newsletterService.subscribe(cleanedEmail);

      if (response.success) {
        const subscribedEmail = cleanedEmail.toLowerCase();
        setEmail(subscribedEmail);
        setSubscribed(true);
        setShowPreferences(true);
        setTimeout(() => {
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
    <>
    <footer className="mt-12 border-t border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-900 text-neutral-700 dark:text-gray-200">
      {/* Newsletter Section */}
      <div className="border-t border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-slate-900 py-8">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Mail className="h-7 w-7 text-neutral-700 dark:text-slate-200" />
            </div>
            <h3 className="text-2xl font-bold text-neutral-900 dark:text-white mb-2">
              The Daily Brief
            </h3>
            <p className="text-neutral-600 dark:text-slate-300 mb-4 text-base">
              Top Cheshire stories delivered to your inbox on newsletter mornings
            </p>
            
            {!subscribed ? (
              <form onSubmit={handleSubscribe} noValidate className="flex flex-col sm:flex-row gap-2 max-w-xl mx-auto">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email address"
                  required
                  disabled={loading}
                  className="flex-1 px-4 py-2 rounded-full border border-[#E6E1D8] bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-4 focus:ring-slate-200 disabled:opacity-50 disabled:cursor-not-allowed dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-400 dark:focus:ring-slate-500/30"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-sky-700 text-white font-bold px-6 py-2 rounded-full hover:bg-sky-800 transition-colors whitespace-nowrap shadow disabled:opacity-50 disabled:cursor-not-allowed dark:bg-sky-600 dark:hover:bg-sky-500"
                >
                  {loading ? 'Subscribing...' : 'Subscribe Now'}
                </button>
              </form>
            ) : (
              <div className="border border-[#E6E1D8] bg-[#FBFAF7] rounded-full px-6 py-3 max-w-xl mx-auto dark:border-slate-700 dark:bg-slate-800">
                <p className="text-neutral-800 dark:text-slate-100 font-semibold flex items-center justify-center gap-2">
                  ✓ Thank you! Your subscription is confirmed!
                </p>
              </div>
            )}
            
            {errorMessage && (
              <div className="bg-[#FBFAF7] border border-red-300 rounded-full px-6 py-3 max-w-xl mx-auto mt-3 dark:bg-slate-800 dark:border-red-700">
                <p className="text-red-800 font-semibold text-center dark:text-red-200">
                  {errorMessage}
                </p>
              </div>
            )}
            
            <p className="text-neutral-500 dark:text-slate-500 dark:text-slate-500 dark:text-slate-400 text-xs mt-3">
              No spam, unsubscribe anytime. Weekly Roundup & Breaking News alerts also available.
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-10">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10 lg:gap-12 mb-8">
          {/* Logo & Description */}
          <div className="sm:col-span-2 lg:col-span-1">
            <h3 className="text-neutral-900 dark:text-white text-xl font-extrabold mb-3">Cheshire Today</h3>
            <p className="text-sm text-neutral-600 dark:text-slate-400 dark:text-slate-400 mb-4">
              Cheshire’s local economic intelligence platform covering local news, business, finance and AI & tech.
            </p>
            <a
              href={FACEBOOK_PAGE_URL}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackEvent("social_click", { network: "facebook", placement: "footer", destination: FACEBOOK_PAGE_URL })}
              className="inline-flex items-center gap-2 rounded-full bg-[#1877F2] px-4 py-2 text-sm font-semibold text-white hover:bg-[#166FE5] transition-colors"
              aria-label="Follow Cheshire Today on Facebook"
            >
              <Facebook className="h-4 w-4" />
              Follow us on Facebook
            </a>
          </div>

          {/* Footer Links */}
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h4 className="text-neutral-900 dark:text-white font-bold mb-3">{title}</h4>
              <ul className="space-y-2.5">
                {links.map((link) => {
                  // Map specific links to their routes
                  const linkMap = {
                    'Local': '/?category=Local',
                    'Business': '/?category=Business',
                    'UK': '/?category=UK',
                    'AI & Tech': '/?category=AI%20%26%20Tech',
                    'Finance': '/?category=Finance',
                    'Privacy': '/privacy',
                    'Terms': '/terms',
                    'Affiliates': '/affiliate-disclosure',
                    'Advertise': '/advertise',
                    'Contact': '/contact',
                  };
                  const href = linkMap[link];
                  
                  if (href) {
                    return (
                      <li key={link}>
                        <Link to={href} className="text-sm hover:text-emerald-500 dark:hover:text-emerald-400 transition-colors" onClick={() => { if (href === "/advertise") trackEvent("monetisation_click", { placement: "footer_advertise", destination: "/advertise" }); }}> 
                          {link}
                        </Link>
                      </li>
                    );
                  }
                  
                  return (
                    <li key={link}>
                      <span className="text-sm text-neutral-500 dark:text-slate-400">
                        {link}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        {/* Content Disclaimer */}
        <div className="border-t border-[#E6E1D8] pt-6 mt-8">
          <p className="text-[11px] text-neutral-500 dark:text-slate-500 dark:text-slate-500/80 text-center max-w-3xl mx-auto leading-relaxed">
            Cheshire Today publishes a mix of original, curated and RSS-sourced coverage. Where articles reference or summarise reporting from third-party publishers, copyright, images and trademarks remain with the original publisher. Use source links to access original reporting.
          </p>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-[#E6E1D8] dark:border-gray-800 pt-6 mt-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-neutral-600 dark:text-slate-400 dark:text-slate-400">
              © {currentYear} Cheshire Today. All rights reserved.
            </p>
            <div className="flex items-center space-x-4 flex-wrap justify-center">
              <Link to="/privacy" className="text-sm hover:text-emerald-500 dark:hover:text-emerald-400 transition-colors">Privacy Policy</Link>
              <Link to="/cookies" className="text-sm hover:text-emerald-500 dark:hover:text-emerald-400 transition-colors">Cookie Policy</Link>

              <span className="text-neutral-500 dark:text-slate-500 dark:text-slate-500">|</span>
              <Link to="/terms" className="text-sm hover:text-emerald-500 dark:hover:text-emerald-400 transition-colors">Terms of Service</Link>
              <span className="text-neutral-500 dark:text-slate-500 dark:text-slate-500">|</span>
              <Link to="/affiliate-disclosure" className="text-sm hover:text-emerald-500 dark:hover:text-emerald-400 transition-colors">Affiliate Disclosure</Link>
              <span className="text-neutral-500 dark:text-slate-500 dark:text-slate-500">|</span>
              <a href="mailto:news@cheshiretoday.co.uk" className="text-sm hover:text-emerald-500 dark:hover:text-emerald-400 transition-colors">Contact</a>
              <span className="text-neutral-500 dark:text-slate-500 dark:text-slate-500">|</span>
              <Link to="/admin" className="text-sm text-neutral-700 dark:text-gray-300 hover:text-emerald-500 dark:hover:text-emerald-400 transition-colors flex items-center gap-1">
                <Settings className="h-3 w-3" />
                Admin
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
    <NewsletterPreferences
      open={showPreferences}
      onOpenChange={setShowPreferences}
      email={email}
    />
    </>
  );
};

export default NewsFooter;
