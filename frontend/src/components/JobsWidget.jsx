import React from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, ArrowRight, MapPin, Mail } from 'lucide-react';
import { Button } from './ui/button';

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
  const handleClick = (e) => {
    e.preventDefault();
    const subscribeSection = document.getElementById('subscribe');
    if (subscribeSection) {
      subscribeSection.scrollIntoView({ behavior: 'smooth' });
    } else {
      // Scroll to bottom area where subscribe usually is
      window.scrollTo({ top: document.body.scrollHeight - 1000, behavior: 'smooth' });
    }
  };

  return (
    <a 
      href="#subscribe"
      onClick={handleClick}
      className="block my-4 group" 
      data-testid="subscribe-inline-banner"
    >
      <div className="flex items-center gap-4 p-4 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 hover:shadow-md transition-all">
        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center flex-shrink-0">
          <Mail className="h-6 w-6 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            The Daily Brief
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Top Cheshire stories at 7:30 AM every morning
          </p>
        </div>
        <ArrowRight className="h-5 w-5 text-blue-600 group-hover:translate-x-1 transition-transform flex-shrink-0" />
      </div>
    </a>
  );
};

export default JobsWidget;
