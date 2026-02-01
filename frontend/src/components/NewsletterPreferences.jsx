import React, { useState, useEffect } from 'react';
import { Mail, Check, Sun, Calendar, Zap, Loader2, AlertTriangle } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from './ui/dialog';
import { toast } from '../hooks/use-toast';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// New tiered email subscription options (January 2026)
const SUBSCRIPTION_TYPES = [
  { 
    id: 'daily_brief', 
    name: 'The Daily Brief', 
    description: 'Top Cheshire stories every morning',
    time: '7:30 AM daily',
    icon: Sun,
    color: 'emerald',
    default: true
  },
  { 
    id: 'weekly_roundup', 
    name: 'The Weekly Roundup', 
    description: 'Curated digest of the week\'s best content',
    time: 'Sunday 9:00 AM',
    icon: Calendar,
    color: 'purple',
    default: false
  },
  { 
    id: 'breaking_news', 
    name: 'Breaking News Alerts', 
    description: 'Urgent notifications for major incidents',
    time: 'As needed (rare)',
    icon: Zap,
    color: 'red',
    default: false
  },
];

const NewsletterPreferences = ({ open, onOpenChange, email: initialEmail }) => {
  const [email, setEmail] = useState(initialEmail || '');
  const [preferences, setPreferences] = useState({
    daily_brief: true,
    weekly_roundup: false,
    breaking_news: false,
  });
  const [loading, setLoading] = useState(false);
  const [loadingPrefs, setLoadingPrefs] = useState(false);
  const [step, setStep] = useState('email'); // 'email' or 'preferences'
  const [isExisting, setIsExisting] = useState(false);

  // Reset when dialog closes
  useEffect(() => {
    if (!open) {
      setStep('email');
      setEmail(initialEmail || '');
      setPreferences({
        daily_brief: true,
        weekly_roundup: false,
        breaking_news: false,
      });
      setIsExisting(false);
    }
  }, [open, initialEmail]);

  // Load existing preferences when email is entered
  const loadPreferences = async (emailToLoad) => {
    if (!emailToLoad) return;
    
    setLoadingPrefs(true);
    try {
      const response = await fetch(`${API_URL}/api/newsletter/email-preferences/${encodeURIComponent(emailToLoad)}`);
      if (response.ok) {
        const data = await response.json();
        setPreferences({
          daily_brief: data.daily_brief ?? true,
          weekly_roundup: data.weekly_roundup ?? false,
          breaking_news: data.breaking_news ?? false,
        });
        setIsExisting(true);
      }
    } catch (e) {
      console.error('Failed to load preferences:', e);
      // If subscriber not found, use defaults
      setPreferences({
        daily_brief: true,
        weekly_roundup: false,
        breaking_news: false,
      });
    } finally {
      setLoadingPrefs(false);
    }
  };

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    
    await loadPreferences(email);
    setStep('preferences');
  };

  const handleToggle = (id) => {
    setPreferences(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const handleSavePreferences = async () => {
    // Ensure at least one option is selected
    if (!preferences.daily_brief && !preferences.weekly_roundup && !preferences.breaking_news) {
      toast({
        title: "Select at least one option",
        description: "Please choose at least one email type to receive.",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    
    try {
      if (isExisting) {
        // Update existing subscriber preferences
        const response = await fetch(`${API_URL}/api/newsletter/email-preferences`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email,
            ...preferences
          })
        });
        
        if (!response.ok) {
          throw new Error('Failed to update preferences');
        }
        
        toast({
          title: "Preferences Updated!",
          description: "Your email preferences have been saved.",
        });
      } else {
        // Subscribe new user
        const subscribeResponse = await fetch(`${API_URL}/api/subscribe`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email })
        });
        
        if (!subscribeResponse.ok) {
          const data = await subscribeResponse.json();
          throw new Error(data.detail || 'Failed to subscribe');
        }
        
        // Then update preferences
        await fetch(`${API_URL}/api/newsletter/email-preferences`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email,
            ...preferences
          })
        });
        
        toast({
          title: "Subscribed Successfully!",
          description: "Welcome to Cheshire Today!",
        });
      }
      
      onOpenChange(false);
    } catch (e) {
      toast({
        title: "Error",
        description: e.message || "Failed to save preferences. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const getColorClasses = (color, isActive) => {
    const colors = {
      emerald: isActive 
        ? 'bg-emerald-50 border-emerald-500 dark:bg-emerald-900/30 dark:border-emerald-500' 
        : 'bg-gray-50 border-gray-200 dark:bg-gray-800 dark:border-gray-700',
      purple: isActive 
        ? 'bg-purple-50 border-purple-500 dark:bg-purple-900/30 dark:border-purple-500' 
        : 'bg-gray-50 border-gray-200 dark:bg-gray-800 dark:border-gray-700',
      red: isActive 
        ? 'bg-red-50 border-red-500 dark:bg-red-900/30 dark:border-red-500' 
        : 'bg-gray-50 border-gray-200 dark:bg-gray-800 dark:border-gray-700',
    };
    return colors[color] || colors.emerald;
  };

  const getIconColorClasses = (color) => {
    const colors = {
      emerald: 'text-emerald-600 dark:text-emerald-400',
      purple: 'text-purple-600 dark:text-purple-400',
      red: 'text-red-600 dark:text-red-400',
    };
    return colors[color] || colors.emerald;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-emerald-600" />
            {step === 'email' ? 'Newsletter Preferences' : 'Choose Your Emails'}
          </DialogTitle>
          <DialogDescription>
            {step === 'email' 
              ? 'Enter your email to subscribe or manage your preferences'
              : isExisting ? 'Update which emails you receive' : 'Select the emails you want to receive'
            }
          </DialogDescription>
        </DialogHeader>

        {step === 'email' ? (
          <form onSubmit={handleEmailSubmit} className="space-y-4 mt-4">
            <div>
              <Label htmlFor="pref-email">Email Address</Label>
              <Input
                id="pref-email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="mt-1"
              />
            </div>
            <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700">
              Continue
            </Button>
          </form>
        ) : (
          <div className="space-y-4 mt-4">
            {loadingPrefs ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-emerald-600" />
              </div>
            ) : (
              <>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {isExisting 
                    ? `Managing preferences for ${email}`
                    : `Setting up preferences for ${email}`
                  }
                </p>

                {/* Email Options */}
                <div className="space-y-3">
                  {SUBSCRIPTION_TYPES.map((type) => {
                    const Icon = type.icon;
                    const isActive = preferences[type.id];
                    
                    return (
                      <div
                        key={type.id}
                        className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${getColorClasses(type.color, isActive)}`}
                        onClick={() => handleToggle(type.id)}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3">
                            <div className={`mt-0.5 ${getIconColorClasses(type.color)}`}>
                              <Icon className="h-5 w-5" />
                            </div>
                            <div>
                              <h4 className="font-semibold text-gray-900 dark:text-white">
                                {type.name}
                              </h4>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                {type.description}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                ⏰ {type.time}
                              </p>
                            </div>
                          </div>
                          <Switch
                            checked={isActive}
                            onCheckedChange={() => handleToggle(type.id)}
                            className="data-[state=checked]:bg-emerald-600"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Warning if nothing selected */}
                {!preferences.daily_brief && !preferences.weekly_roundup && !preferences.breaking_news && (
                  <div className="flex items-center gap-2 text-amber-600 text-sm bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg">
                    <AlertTriangle className="h-4 w-4" />
                    Please select at least one email type
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {step === 'preferences' && !loadingPrefs && (
          <DialogFooter className="mt-4 gap-2">
            <Button 
              variant="outline" 
              onClick={() => setStep('email')}
              disabled={loading}
            >
              Back
            </Button>
            <Button 
              onClick={handleSavePreferences}
              disabled={loading || (!preferences.daily_brief && !preferences.weekly_roundup && !preferences.breaking_news)}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  {isExisting ? 'Save Changes' : 'Subscribe'}
                </>
              )}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default NewsletterPreferences;
