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
        const subscribedEmail = email.trim().toLowerCase();
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

  if (compact) {
    return (
      <>
        <div
          id="subscribe"
          className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 shadow-sm"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-[#1E3A8A] flex items-center justify-center flex-shrink-0">
              <Mail className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">The Daily Brief</h3>
              <p className="text-sm text-slate-600 dark:text-gray-400">
                Top Cheshire stories on newsletter mornings — including weekend briefings
              </p>
            </div>
          </div>

          {!subscribed ? (
            <form onSubmit={handleSubscribe} className="mt-3 flex gap-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
                disabled={loading}
                className="flex-1 rounded-md border border-slate-300 dark:border-gray-700 bg-white dark:bg-slate-900 px-3 py-2 text-sm text-slate-900 dark:text-white placeholder:text-slate-500 dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-300 dark:focus:ring-blue-800 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={loading}
                className="rounded-md bg-[#1E3A8A] px-4 py-2 text-sm font-medium text-white hover:bg-[#1b357d] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Subscribe'}
              </button>
            </form>
          ) : (
            <div className="mt-3 rounded-md border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/30 px-3 py-2 flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              <span className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
                Subscribed! Check your email.
              </span>
            </div>
          )}

          {errorMessage && (
            <p className="text-red-600 dark:text-red-400 text-xs mt-2">{errorMessage}</p>
          )}

          <button
            onClick={() => setShowPreferences(true)}
            className="text-slate-500 hover:text-slate-700 dark:text-gray-400 dark:hover:text-gray-200 text-xs mt-3 flex items-center gap-1 underline"
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
                <p className="text-white/80 text-xs hidden sm:block">The Daily Brief — top stories on newsletter mornings</p>
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
