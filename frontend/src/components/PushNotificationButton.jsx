import React, { useState, useEffect } from 'react';
import { Bell, BellOff, BellRing, Loader2, Share } from 'lucide-react';

const PushNotificationButton = ({ apiUrl, compact = false }) => {
  const [isSupported, setIsSupported] = useState(true);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [permission, setPermission] = useState('default');
  const [error, setError] = useState(null);
  const [initialized, setInitialized] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Detect iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || 
                (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    setIsIOS(iOS);
    
    // Check if running as PWA (added to home screen)
    const standalone = window.matchMedia('(display-mode: standalone)').matches || 
                       window.navigator.standalone === true;
    setIsStandalone(standalone);
    
    // Check for basic notification support
    const checkSupport = () => {
      // On iOS, notifications are only supported in standalone PWA mode (iOS 16.4+)
      if (iOS && !standalone) {
        console.log('[Push] iOS detected, not in standalone mode');
        setIsSupported(false);
        setInitialized(true);
        return false;
      }
      
      if (!('Notification' in window)) {
        console.log('[Push] Notifications not supported');
        setIsSupported(false);
        setInitialized(true);
        return false;
      }
      
      if (!('serviceWorker' in navigator)) {
        console.log('[Push] Service Worker not supported');
        setIsSupported(false);
        setInitialized(true);
        return false;
      }
      
      setPermission(Notification.permission);
      setIsSubscribed(Notification.permission === 'granted');
      setInitialized(true);
      return true;
    };
    
    checkSupport();
    
    // Check actual subscription status after a delay
    const timer = setTimeout(async () => {
      try {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
          const registration = await navigator.serviceWorker.getRegistration();
          if (registration) {
            const subscription = await registration.pushManager.getSubscription();
            setIsSubscribed(!!subscription);
          }
        }
      } catch (e) {
        console.log('[Push] Could not check subscription:', e);
      }
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []);

  const urlBase64ToUint8Array = (base64String) => {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  };

  // Show iOS instructions
  const showIOSInstructions = () => {
    const message = `📱 To get Breaking News Alerts on iPhone/iPad:

1. Tap the Share button (□↑) at the bottom of Safari
2. Scroll down and tap "Add to Home Screen"
3. Open Cheshire Today from your home screen
4. Tap the bell icon to enable alerts

This works on iOS 16.4 and later.`;
    alert(message);
  };

  const handleClick = async () => {
    // iOS not in standalone mode - show instructions
    if (isIOS && !isStandalone) {
      showIOSInstructions();
      return;
    }
    
    // If not supported, show helpful message
    if (!('Notification' in window)) {
      alert('Push notifications are not supported on this browser. Try using Chrome or Safari.');
      return;
    }
    
    // If already subscribed, unsubscribe
    if (isSubscribed) {
      await unsubscribe();
      return;
    }
    
    // Otherwise, subscribe
    await subscribe();
  };

  const subscribe = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Request notification permission
      console.log('[Push] Requesting permission...');
      const perm = await Notification.requestPermission();
      setPermission(perm);
      console.log('[Push] Permission:', perm);
      
      if (perm !== 'granted') {
        alert('Please allow notifications in your browser settings to receive breaking news alerts.');
        setIsLoading(false);
        return;
      }

      // Register service worker
      console.log('[Push] Registering service worker...');
      let registration;
      try {
        registration = await navigator.serviceWorker.register('/sw-push.js');
        await navigator.serviceWorker.ready;
        console.log('[Push] Service worker ready');
      } catch (swError) {
        console.error('[Push] Service worker error:', swError);
        // Still mark as subscribed if permission granted (basic notification support)
        setIsSubscribed(true);
        setIsLoading(false);
        alert('🔔 Notifications enabled! You may receive alerts when the app is open.');
        return;
      }

      // Get VAPID public key from server
      console.log('[Push] Getting VAPID key...');
      const keyResponse = await fetch(`${apiUrl}/api/push/vapid-public-key`);
      const keyData = await keyResponse.json();
      
      if (!keyData.publicKey) {
        console.log('[Push] No VAPID key, using basic notifications');
        setIsSubscribed(true);
        setIsLoading(false);
        return;
      }

      // Subscribe to push
      console.log('[Push] Subscribing to push...');
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(keyData.publicKey)
      });

      // Send subscription to server
      const response = await fetch(`${apiUrl}/api/push/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subscription: subscription.toJSON() })
      });

      const data = await response.json();
      
      if (data.success) {
        setIsSubscribed(true);
        // Show confirmation notification
        try {
          new Notification('Cheshire Today', {
            body: '🔔 You\'ll now receive breaking news alerts!',
            icon: '/logo192.png'
          });
        } catch (e) {
          console.log('[Push] Could not show notification:', e);
        }
      }
    } catch (error) {
      console.error('[Push] Error subscribing:', error);
      setError(error.message);
      
      // If permission was granted, still mark as subscribed for basic support
      if (Notification.permission === 'granted') {
        setIsSubscribed(true);
      } else {
        alert('Could not enable notifications. Please check your browser settings.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const unsubscribe = async () => {
    setIsLoading(true);
    try {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration) {
        const subscription = await registration.pushManager.getSubscription();
        
        if (subscription) {
          await subscription.unsubscribe();
          
          // Notify server
          try {
            await fetch(`${apiUrl}/api/push/unsubscribe`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ endpoint: subscription.endpoint })
            });
          } catch (e) {
            console.log('[Push] Server unsubscribe failed:', e);
          }
        }
      }
      
      setIsSubscribed(false);
    } catch (error) {
      console.error('[Push] Error unsubscribing:', error);
      setIsSubscribed(false); // Reset state anyway
    } finally {
      setIsLoading(false);
    }
  };

  // Compact mode for menu
  if (compact) {
    return (
      <button
        onClick={handleClick}
        disabled={isLoading}
        className={`p-2 rounded-lg transition-all ${
          isSubscribed
            ? 'bg-green-100 dark:bg-green-900/30 text-green-600'
            : isIOS && !isStandalone
              ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 hover:bg-blue-200'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-500 hover:bg-gray-200'
        }`}
        title={isSubscribed ? 'Notifications enabled' : isIOS ? 'Tap for setup instructions' : 'Enable notifications'}
        data-testid="push-notification-btn"
      >
        {isLoading ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : isSubscribed ? (
          <BellRing className="w-5 h-5" />
        ) : isIOS && !isStandalone ? (
          <Bell className="w-5 h-5" />
        ) : (
          <Bell className="w-5 h-5" />
        )}
      </button>
    );
  }

  // Show loading while initializing
  if (isLoading) {
    return (
      <button
        disabled
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-400"
        data-testid="push-notification-btn"
      >
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="hidden sm:inline">Loading...</span>
      </button>
    );
  }

  // iOS not in standalone mode - show helpful button to get instructions
  if (isIOS && !isStandalone) {
    return (
      <button
        onClick={showIOSInstructions}
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 shadow-md"
        title="Tap for setup instructions"
        data-testid="push-notification-btn"
      >
        <Bell className="w-4 h-4" />
        <span className="hidden sm:inline">Get Alerts</span>
      </button>
    );
  }

  // Not supported (non-iOS browsers without notification support)
  if (!isSupported && !isIOS) {
    return (
      <button
        onClick={() => alert('Push notifications are not supported on this browser. Try using Chrome, Firefox, or Safari on iOS 16.4+.')}
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-gray-200 text-gray-400"
        title="Push notifications not supported"
        data-testid="push-notification-btn"
      >
        <BellOff className="w-4 h-4" />
        <span className="hidden sm:inline">Not Supported</span>
      </button>
    );
  }

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
        isSubscribed
          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50'
          : 'bg-red-600 text-white hover:bg-red-700 shadow-md hover:shadow-lg'
      }`}
      title={isSubscribed ? 'Disable breaking news alerts' : 'Enable breaking news alerts'}
      data-testid="push-notification-btn"
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : isSubscribed ? (
        <BellRing className="w-4 h-4" />
      ) : (
        <Bell className="w-4 h-4" />
      )}
      <span className="hidden sm:inline">
        {isSubscribed ? 'Alerts On' : 'Get Alerts'}
      </span>
    </button>
  );
};

export default PushNotificationButton;
