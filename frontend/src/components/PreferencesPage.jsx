import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { getApiUrl } from '../utils/api';
import { Helmet } from 'react-helmet-async';
import { Mail, Sun, Calendar, Zap, CheckCircle, AlertCircle, Loader2, ArrowLeft, Save } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';

const API_URL = getApiUrl();

const SUBSCRIPTION_TYPES = [
  { 
    id: 'daily_brief', 
    name: 'The Daily Brief', 
    description: 'Top Cheshire stories every morning',
    time: 'Newsletter mornings',
    icon: Sun,
    color: 'emerald'
  },
  { 
    id: 'weekly_roundup', 
    name: 'The Weekly Roundup', 
    description: 'Curated digest of the week\'s best content',
    time: 'Sunday morning',
    icon: Calendar,
    color: 'purple'
  },
  { 
    id: 'breaking_news', 
    name: 'Breaking News Alerts', 
    description: 'Urgent notifications for major incidents',
    time: 'As needed (rare)',
    icon: Zap,
    color: 'red'
  },
];

const PreferencesPage = () => {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get('email') || '');
  const [preferences, setPreferences] = useState({
    daily_brief: true,
    weekly_roundup: false,
    breaking_news: false,
  });
  const [loading, setLoading] = useState(false);
  const [loadingPrefs, setLoadingPrefs] = useState(false);
  const [status, setStatus] = useState(null); // 'success', 'error', 'not_found', null
  const [message, setMessage] = useState('');
  const [step, setStep] = useState('email'); // 'email' or 'preferences'
  const [originalPrefs, setOriginalPrefs] = useState(null);

  // If email is in URL params, fetch preferences
  useEffect(() => {
    const emailParam = searchParams.get('email');
    if (emailParam) {
      setEmail(emailParam);
      fetchPreferences(emailParam);
    }
  }, [searchParams]);

  const fetchPreferences = async (emailToFetch) => {
    setLoadingPrefs(true);
    setStatus(null);

    try {
      const response = await fetch(`${API_URL}/api/newsletter/preferences/${encodeURIComponent(emailToFetch)}`);
      const data = await response.json();

      if (data.found) {
        setPreferences(data.preferences);
        setOriginalPrefs(data.preferences);
        setStep('preferences');
      } else {
        setStatus('not_found');
        setMessage('This email is not subscribed to our newsletter.');
      }
    } catch (error) {
      console.error('Error fetching preferences:', error);
      setStatus('error');
      setMessage('Failed to load your preferences. Please try again.');
    } finally {
      setLoadingPrefs(false);
    }
  };

  const handleEmailSubmit = (e) => {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setStatus('error');
      setMessage('Please enter a valid email address.');
      return;
    }
    fetchPreferences(email.toLowerCase().trim());
  };

  const handleSavePreferences = async () => {
    setLoading(true);
    setStatus(null);

    try {
      const response = await fetch(`${API_URL}/api/newsletter/email-preferences`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.toLowerCase().trim(),
          ...preferences,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage('Your email preferences have been updated.');
        setOriginalPrefs(preferences);
      } else {
        setStatus('error');
        setMessage(data.detail || 'Failed to update preferences.');
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      setStatus('error');
      setMessage('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const togglePreference = (key) => {
    setPreferences((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
    setStatus(null); // Clear any status when user makes changes
  };

  const hasChanges = originalPrefs && (
    preferences.daily_brief !== originalPrefs.daily_brief ||
    preferences.weekly_roundup !== originalPrefs.weekly_roundup ||
    preferences.breaking_news !== originalPrefs.breaking_news
  );

  const getColorClasses = (color, enabled) => {
    if (!enabled) return 'bg-gray-100 dark:bg-gray-800 border-gray-200 dark:border-gray-700';
    
    const colors = {
      emerald: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800',
      purple: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800',
      red: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
    };
    return colors[color] || colors.emerald;
  };

  const getIconColorClasses = (color, enabled) => {
    if (!enabled) return 'text-gray-400';
    
    const colors = {
      emerald: 'text-emerald-600 dark:text-emerald-400',
      purple: 'text-purple-600 dark:text-purple-400',
      red: 'text-red-600 dark:text-red-400',
    };
    return colors[color] || colors.emerald;
  };

  return (
    
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      {/* SEO - Prevent indexing of preferences page */}
      <Helmet>
        <title>Email Preferences | Cheshire Today</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      
      <div className="max-w-lg w-full">
        {/* Back to Home */}
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 mb-6 text-sm"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Cheshire Today
        </Link>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
              <Mail className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Email Preferences
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Choose which emails you'd like to receive from Cheshire Today.
            </p>
          </div>

          {/* Status Messages */}
          {status === 'success' && (
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-green-800 dark:text-green-200 font-medium">Preferences Saved</p>
                <p className="text-green-700 dark:text-green-300 text-sm mt-1">{message}</p>
              </div>
            </div>
          )}

          {status === 'error' && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-800 dark:text-red-200 font-medium">Error</p>
                <p className="text-red-700 dark:text-red-300 text-sm mt-1">{message}</p>
              </div>
            </div>
          )}

          {status === 'not_found' && (
            <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-yellow-800 dark:text-yellow-200 font-medium">Not Found</p>
                <p className="text-yellow-700 dark:text-yellow-300 text-sm mt-1">{message}</p>
                <Link to="/" className="text-blue-600 hover:text-blue-700 text-sm mt-2 inline-block">
                  Subscribe to our newsletter →
                </Link>
              </div>
            </div>
          )}

          {/* Email Input Step */}
          {step === 'email' && status !== 'not_found' && (
            <form onSubmit={handleEmailSubmit} className="space-y-4">
              <div>
                <Label htmlFor="email" className="text-gray-700 dark:text-gray-300">
                  Enter your email to manage preferences
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="mt-1"
                  required
                  disabled={loadingPrefs}
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loadingPrefs}
              >
                {loadingPrefs ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Loading...
                  </>
                ) : (
                  'Find My Preferences'
                )}
              </Button>
            </form>
          )}

          {/* Preferences Step */}
          {step === 'preferences' && (
            <div className="space-y-4">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-4 pb-4 border-b dark:border-gray-700">
                Managing preferences for: <span className="font-medium text-gray-900 dark:text-white">{email}</span>
              </div>

              {SUBSCRIPTION_TYPES.map((sub) => {
                const Icon = sub.icon;
                const enabled = preferences[sub.id];
                
                return (
                  <div
                    key={sub.id}
                    className={`p-4 rounded-lg border-2 transition-all ${getColorClasses(sub.color, enabled)}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Icon className={`h-5 w-5 ${getIconColorClasses(sub.color, enabled)}`} />
                        <div>
                          <p className={`font-medium ${enabled ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}>
                            {sub.name}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {sub.description}
                          </p>
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                            {sub.time}
                          </p>
                        </div>
                      </div>
                      <Switch
                        checked={enabled}
                        onCheckedChange={() => togglePreference(sub.id)}
                        data-testid={`toggle-${sub.id}`}
                      />
                    </div>
                  </div>
                );
              })}

              {/* Save Button */}
              <Button
                onClick={handleSavePreferences}
                className="w-full mt-6"
                disabled={loading || !hasChanges}
                data-testid="save-preferences-button"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    {hasChanges ? 'Save Preferences' : 'No Changes to Save'}
                  </>
                )}
              </Button>

              {/* Unsubscribe Link */}
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 text-center">
                <Link
                  to={`/unsubscribe?email=${encodeURIComponent(email)}`}
                  className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm"
                >
                  Unsubscribe from all emails
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-500 dark:text-gray-500 mt-6">
          © {new Date().getFullYear()} Cheshire Today. All rights reserved.
        </p>
      </div>
    </div>
    
  );
};

export default PreferencesPage;
