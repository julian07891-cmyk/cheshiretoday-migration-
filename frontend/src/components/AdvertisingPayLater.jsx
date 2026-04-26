import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowLeft, Loader2, Megaphone, XCircle } from "lucide-react";
import { getApiUrl } from "../utils/api";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";

const AdvertisingPayLater = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState("starting");
  const [message, setMessage] = useState("Starting secure payment...");

  useEffect(() => {
    const startCheckout = async () => {
      if (!token) {
        setStatus("failed");
        setMessage("This payment link is missing a token. Please return to the advertising page or contact news@cheshiretoday.co.uk.");
        return;
      }

      try {
        const res = await fetch(`${getApiUrl()}/api/advertising/checkout/from-lead/${encodeURIComponent(token)}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ origin_url: window.location.origin }),
        });

        const data = await res.json();

        if (data?.checkout_url) {
          window.location.href = data.checkout_url;
          return;
        }

        setStatus("failed");
        setMessage(data?.detail || "Could not start secure payment. Please contact news@cheshiretoday.co.uk.");
      } catch (error) {
        setStatus("failed");
        setMessage("Could not start secure payment. Please contact news@cheshiretoday.co.uk.");
      }
    };

    startCheckout();
  }, [token]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md text-center">
        <CardContent className="pt-12 pb-8">
          {status === "starting" && (
            <>
              <div className="mx-auto w-20 h-20 bg-amber-100 dark:bg-amber-900 rounded-full flex items-center justify-center mb-6">
                <Loader2 className="h-10 w-10 text-amber-600 dark:text-amber-400 animate-spin" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                Opening Secure Payment
              </h1>
              <p className="text-gray-600 dark:text-gray-400">{message}</p>
            </>
          )}

          {status === "failed" && (
            <>
              <div className="mx-auto w-20 h-20 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center mb-6">
                <XCircle className="h-10 w-10 text-red-600 dark:text-red-400" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                Payment Link Issue
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-6">{message}</p>

              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link to="/advertise">
                  <Button className="bg-amber-600 hover:bg-amber-700 gap-2 w-full sm:w-auto">
                    <Megaphone className="h-4 w-4" />
                    Advertising
                  </Button>
                </Link>
                <Link to="/">
                  <Button variant="outline" className="gap-2 w-full sm:w-auto">
                    <ArrowLeft className="h-4 w-4" />
                    Back to News
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

export default AdvertisingPayLater;
