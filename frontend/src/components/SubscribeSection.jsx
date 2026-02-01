import React, { useState } from 'react';
import { Mail, CheckCircle, Loader2, Settings } from 'lucide-react';
import { newsletterService } from '../services/api';
import NewsletterPreferences from './NewsletterPreferences';

const SubscribeSection = ({ compact = false }) => {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [showPreferences, setShowPreferences] = useState(false);

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

  if (compact) {
    return (
      <>
        <div id="subscribe" className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-xl p-6 my-8 shadow-lg">
          <div className="flex items-center gap-3 mb-3">
            <Mail className="h-6 w-6 text-white" />
            <h3 className="text-xl font-bold text-white">Get the Latest News</h3>
          </div>
          <p className="text-white/90 text-sm mb-4">
            The Daily Brief — Top Cheshire stories at 7:30 AM
          </p>
          
          {!subscribed ? (
            <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
                disabled={loading}
                className="flex-1 px-4 py-2 rounded-lg text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-300 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={loading}
                className="bg-yellow-400 text-emerald-900 font-semibold px-6 py-2 rounded-lg hover:bg-yellow-300 transition-colors text-sm disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Subscribe'}
              </button>
            </form>
          ) : (
            <div className="bg-white/90 rounded-lg px-4 py-2 flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-600" />
              <span className="text-emerald-800 font-medium text-sm">Subscribed! Check your email.</span>
            </div>
          )}
          
          {errorMessage && (
            <p className="text-red-200 text-sm mt-2">{errorMessage}</p>
          )}
          
          <button
            onClick={() => setShowPreferences(true)}
            className="text-white/80 hover:text-white text-xs mt-3 flex items-center gap-1 underline"
          >
            <Settings className="h-3 w-3" />
            Customize preferences
          </button>
        </div>
        
        <NewsletterPreferences 
          open={showPreferences} 
          onOpenChange={setShowPreferences}
          email={email}
        />
      </>
    );
  }

  // Full-width version - Compact bar style
  return (
    <>
      <div id="subscribe" className="bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-600 py-4 my-6">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            {/* Left side - Icon and text */}
            <div className="flex items-center gap-3">
              <Mail className="h-6 w-6 text-white flex-shrink-0" />
              <div className="text-center md:text-left">
                <h3 className="text-lg font-bold text-white">Never Miss a Story</h3>
                <p className="text-white/80 text-xs hidden sm:block">The Daily Brief — Top stories at 7:30 AM</p>
              </div>
            </div>
            
            {/* Right side - Form */}
            {!subscribed ? (
              <form onSubmit={handleSubscribe} className="flex gap-2 w-full md:w-auto max-w-md">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  required
                  disabled={loading}
                  className="flex-1 px-4 py-2 rounded-full text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-300 disabled:opacity-50 min-w-0"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-yellow-400 text-emerald-900 font-bold px-5 py-2 rounded-full hover:bg-yellow-300 transition-colors shadow-md disabled:opacity-50 flex items-center justify-center gap-1 text-sm whitespace-nowrap"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Subscribe'}
                </button>
              </form>
            ) : (
              <div className="bg-white/90 rounded-full px-4 py-2 flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-emerald-600" />
                <span className="text-emerald-800 font-semibold text-sm">Subscribed! Check your email.</span>
              </div>
            )}
            
            {/* Customize link */}
            <button
              onClick={() => setShowPreferences(true)}
              className="text-white/70 hover:text-white text-xs flex items-center gap-1 underline"
            >
              <Settings className="h-3 w-3" />
              Customize
            </button>
          </div>
          
          {errorMessage && (
            <p className="text-red-200 text-xs mt-2 text-center">{errorMessage}</p>
          )}
        </div>
      </div>
      
      <NewsletterPreferences 
        open={showPreferences} 
        onOpenChange={setShowPreferences}
        email={email}
      />
    </>
  );
};

export default SubscribeSection;
