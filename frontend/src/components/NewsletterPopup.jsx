import React, { useState, useEffect } from 'react';
import { X, Mail, Bell } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { newsletterService } from '../services/api';
import {
  NEWSLETTER_CREATED_ITEMS,
  NEWSLETTER_CREATED_LEAD,
  NEWSLETTER_CREATED_SUPPORT,
  NEWSLETTER_CREATED_TITLE,
  NEWSLETTER_EXISTING_MESSAGE,
  NEWSLETTER_SIGNUP_CONSENT,
} from '../constants/newsletterSignup';

const NewsletterPopup = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [errorMessage, setErrorMessage] = useState('');
  const [signupOutcome, setSignupOutcome] = useState('existing');
  const location = useLocation();

  useEffect(() => {
    // Check if user has already subscribed (permanent) or dismissed
    const subscribed = localStorage.getItem('newsletter_subscribed');
    const dismissed = localStorage.getItem('newsletter_popup_dismissed');
    
    // If subscribed or dismissed, never show again
    if (subscribed || dismissed) {
      return;
    }

    // Only show popup once - after 15 seconds on first visit
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 15000);

    return () => clearTimeout(timer);
  }, []); // Only run once on mount

  const handleDismiss = () => {
    setIsVisible(false);
    // Mark as dismissed permanently (or for 7 days)
    const sevenDaysFromNow = Date.now() + (7 * 24 * 60 * 60 * 1000);
    localStorage.setItem('newsletter_popup_dismissed', sevenDaysFromNow.toString());
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || status === 'loading') return;

    setStatus('loading');
    setErrorMessage('');

    try {
      const response = await newsletterService.subscribe(email, 'popup');
      if (response.success || response.message) {
        const outcome = response.outcome === 'created' ? 'created' : 'existing';
        setSignupOutcome(outcome);
        setStatus('success');
        if (outcome === 'created') {
          localStorage.setItem('newsletter_subscribed', 'true');
        }
      }
    } catch (error) {
      setStatus('error');
      setErrorMessage(error.response?.data?.detail || 'Failed to subscribe. Please try again.');
    }
  };

  if (!isVisible) return null;

  return (
    <>
      {/* Slide-in from bottom - Less intrusive */}
      <div 
        className="fixed bottom-4 right-4 z-[9999] w-full max-w-sm animate-slide-up"
        style={{
          animation: 'slideUp 0.3s ease-out'
        }}
      >
        <style>
          {`
            @keyframes slideUp {
              from {
                opacity: 0;
                transform: translateY(20px);
              }
              to {
                opacity: 1;
                transform: translateY(0);
              }
            }
          `}
        </style>
        <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
          {/* Compact Header */}
          <div className="bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-3 text-white relative">
            <button
              onClick={handleDismiss}
              className="absolute top-2 right-2 p-1 rounded-full hover:bg-white/20 transition-colors"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
            
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              <span className="font-semibold">Get Cheshire News Updates</span>
            </div>
          </div>

          {/* Content */}
          <div className="p-4">
            {status === 'success' ? (
              <div role="status" aria-live="polite" className="py-2">
                <div className="flex items-center justify-center gap-2 text-emerald-600">
                  <Mail className="h-5 w-5" />
                  <span className="font-semibold">
                    {signupOutcome === 'created'
                      ? NEWSLETTER_CREATED_TITLE
                      : NEWSLETTER_EXISTING_MESSAGE}
                  </span>
                </div>
                {signupOutcome === 'created' ? (
                  <div className="mt-3 text-left text-sm text-gray-700">
                    <p className="font-semibold">{NEWSLETTER_CREATED_LEAD}</p>
                    <ul className="mt-1 list-disc space-y-1 pl-5">
                      {NEWSLETTER_CREATED_ITEMS.map(item => <li key={item}>{item}</li>)}
                    </ul>
                    <p className="mt-3 text-xs text-gray-500">{NEWSLETTER_CREATED_SUPPORT}</p>
                  </div>
                ) : null}
                <div className="mt-4 flex flex-wrap justify-end gap-2">
                  <Button asChild variant="outline" className="h-9 text-sm">
                    <Link to="/newsletter/preferences">Manage preferences</Link>
                  </Button>
                  <Button onClick={handleDismiss} className="h-9 bg-emerald-600 text-sm text-white hover:bg-emerald-700">
                    Close
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-3">
                <p className="text-sm text-gray-600">
                  The Daily Brief — Top Cheshire stories on newsletter mornings
                </p>
                <div className="flex gap-2">
                  <Input
                    aria-label="Email address"
                    type="email"
                    placeholder="Your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="flex-1 h-10 text-sm"
                    required
                  />
                  <Button 
                    type="submit" 
                    className="h-10 px-4 bg-emerald-600 hover:bg-emerald-700 text-white text-sm"
                    disabled={status === 'loading'}
                  >
                    {status === 'loading' ? '...' : 'Subscribe'}
                  </Button>
                </div>
                {status === 'error' && (
                  <p role="alert" className="text-red-500 text-xs">{errorMessage}</p>
                )}
                <p className="text-xs text-gray-400 text-center">
                  {NEWSLETTER_SIGNUP_CONSENT}
                </p>
              </form>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default NewsletterPopup;
