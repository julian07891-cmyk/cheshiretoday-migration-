import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, ArrowRight, MapPin, Mail } from 'lucide-react';
import { Button } from './ui/button';
import { newsletterService } from '../services/api';
import NewsletterPreferences from './NewsletterPreferences';

// Compact widget for article sidebar/inline
export const JobsWidget = () => {
  return (
    <div className="rounded-xl overflow-hidden bg-gradient-to-br from-emerald-600 to-teal-600 shadow-md my-6">
      <div className="p-5">
        <div className="flex items-start gap-3 mb-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center flex-shrink-0">
            <Briefcase className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="font-bold text-white text-lg">Cheshire Jobs</h3>
            <p className="text-emerald-100 text-sm">Find local opportunities</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 text-emerald-100 text-xs mb-4">
          <MapPin className="h-3 w-3" />
          <span>Jobs across Cheshire • Free to post</span>
        </div>
        
        <div className="flex gap-2">
          <Link to="/jobs" className="flex-1">
            <Button 
              className="w-full bg-white text-emerald-700 hover:bg-emerald-50 font-medium h-9 text-sm"
              data-testid="jobs-widget-browse"
            >
              Browse Jobs
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </Link>
          <Link to="/jobs/post">
            <Button 
              variant="outline"
              className="border-white/50 text-white hover:bg-white/10 h-9 text-sm px-3"
              data-testid="jobs-widget-post"
            >
              Post
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

// Inline banner for within article content - Jobs
export const JobsInlineBanner = () => {
  return (
    <Link to="/jobs" className="block my-4 group" data-testid="jobs-inline-banner">
      <div className="flex items-center gap-4 p-4 rounded-lg bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border border-emerald-200 dark:border-emerald-800 hover:shadow-md transition-all">
        <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center flex-shrink-0">
          <Briefcase className="h-6 w-6 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-gray-900 dark:text-white group-hover:text-emerald-600 transition-colors">
            Looking for a job in Cheshire?
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Browse local job listings • Post for free
          </p>
        </div>
        <ArrowRight className="h-5 w-5 text-emerald-600 group-hover:translate-x-1 transition-transform flex-shrink-0" />
      </div>
    </Link>
  );
};

// Inline banner for within article content - Subscribe
export const SubscribeInlineBanner = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [subscribed, setSubscribed] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [showPreferences, setShowPreferences] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || loading) return;

    setLoading(true);
    setErrorMessage('');

    try {
      const cleanedEmail = (email || '').trim().toLowerCase();
      const response = await newsletterService.subscribe(cleanedEmail);
      if (response.success) {
        setEmail(cleanedEmail);
        setSubscribed(true);
        setShowPreferences(true);
        setTimeout(() => setSubscribed(false), 4000);
      } else {
        setErrorMessage('Please try again.');
      }
    } catch (error) {
      setErrorMessage('Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
    <div className="block my-4" data-testid="subscribe-inline-banner">
      <div className="rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50/80 dark:bg-blue-950/20 px-4 py-3">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center flex-shrink-0">
            <Mail className="h-5 w-5 text-white" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
              <div className="min-w-0">
                <h4 className="font-semibold text-gray-900 dark:text-white">
                  The Daily Brief
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Top Cheshire stories on newsletter mornings
                </p>
              </div>

              {!subscribed ? (
                <form onSubmit={handleSubmit} className="flex w-full lg:w-auto gap-2 lg:min-w-[420px]">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    required
                    disabled={loading}
                    className="flex-1 rounded-md border border-blue-200 dark:border-blue-800 bg-white dark:bg-slate-900 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-300 dark:focus:ring-blue-700 disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? '...' : 'Subscribe'}
                  </button>
                </form>
              ) : (
                <div className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                  Subscribed! Check your email.
                </div>
              )}
            </div>

            {errorMessage ? (
              <p className="mt-2 text-xs text-red-600 dark:text-red-400">{errorMessage}</p>
            ) : null}
          </div>
        </div>
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

export default JobsWidget;
