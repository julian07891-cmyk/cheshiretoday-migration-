import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle, Loader2, XCircle, ArrowLeft, Briefcase, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    return process.env.REACT_APP_BACKEND_URL || window.location.origin;
  }
  return '';
};

const PaymentSuccess = () => {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const isFree = searchParams.get('free') === 'true';
  const [status, setStatus] = useState(isFree ? 'success' : 'checking');
  const [message, setMessage] = useState(isFree ? 'Your free job listing has been submitted for review!' : 'Verifying your payment...');
  const [attempts, setAttempts] = useState(0);

  useEffect(() => {
    // For free listings, show success immediately
    if (isFree) {
      return;
    }
    
    if (sessionId) {
      pollPaymentStatus();
    } else {
      setStatus('failed');
      setMessage('No payment session found. Please try again.');
    }
  }, [sessionId, isFree]);

  const pollPaymentStatus = async () => {
    const maxAttempts = 10;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setStatus('failed');
      setMessage('Payment verification timed out. Please check your email for confirmation or contact support.');
      return;
    }

    try {
      const response = await fetch(`${getApiUrl()}/api/jobs/payment-status/${sessionId}`);
      const data = await response.json();

      if (data.payment_status === 'paid' || data.status === 'completed') {
        setStatus('success');
        setMessage(data.message || 'Payment successful! Your job listing is now pending approval.');
        return;
      } else if (data.status === 'expired') {
        setStatus('expired');
        setMessage('Payment session expired. Please try again.');
        return;
      }

      // Continue polling
      setAttempts(prev => prev + 1);
      setTimeout(pollPaymentStatus, pollInterval);
    } catch (error) {
      console.error('Error checking payment status:', error);
      setAttempts(prev => prev + 1);
      setTimeout(pollPaymentStatus, pollInterval);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md text-center">
        <CardContent className="pt-12 pb-8">
          {status === 'checking' && (
            <>
              <div className="mx-auto w-20 h-20 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-6">
                <Loader2 className="h-10 w-10 text-blue-600 dark:text-blue-400 animate-spin" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                Verifying Payment
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                {message}
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="mx-auto w-20 h-20 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mb-6">
                <CheckCircle className="h-10 w-10 text-green-600 dark:text-green-400" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                Payment Successful!
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {message}
              </p>
              <div className="bg-amber-50 dark:bg-amber-900/30 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-center gap-2 text-amber-700 dark:text-amber-400">
                  <Clock className="h-5 w-5" />
                  <span className="font-medium">What happens next?</span>
                </div>
                <p className="text-sm text-amber-600 dark:text-amber-500 mt-2">
                  Our team will review your listing within 1-2 business days. 
                  You'll receive an email notification once it's approved and live.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link to="/jobs">
                  <Button variant="outline" className="gap-2 w-full sm:w-auto">
                    <Briefcase className="h-4 w-4" />
                    View Job Board
                  </Button>
                </Link>
                <Link to="/">
                  <Button className="bg-emerald-600 hover:bg-emerald-700 gap-2 w-full sm:w-auto">
                    <ArrowLeft className="h-4 w-4" />
                    Back to News
                  </Button>
                </Link>
              </div>
            </>
          )}

          {(status === 'failed' || status === 'expired') && (
            <>
              <div className="mx-auto w-20 h-20 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center mb-6">
                <XCircle className="h-10 w-10 text-red-600 dark:text-red-400" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                {status === 'expired' ? 'Session Expired' : 'Payment Issue'}
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {message}
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link to="/jobs/post">
                  <Button className="bg-emerald-600 hover:bg-emerald-700 gap-2 w-full sm:w-auto">
                    Try Again
                  </Button>
                </Link>
                <Link to="/jobs">
                  <Button variant="outline" className="gap-2 w-full sm:w-auto">
                    <Briefcase className="h-4 w-4" />
                    View Jobs
                  </Button>
                </Link>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentSuccess;
