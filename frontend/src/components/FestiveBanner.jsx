import React, { useEffect, useState } from 'react';
import { Sparkles, Gift } from 'lucide-react';

const FestiveBanner = () => {
  const [isActive, setIsActive] = useState(false);
  const [daysUntilNewYear, setDaysUntilNewYear] = useState(0);

  useEffect(() => {
    const now = new Date();
    const endDate = new Date('2026-01-01T00:00:00');
    const newYear = new Date('2026-01-01T00:00:00');
    
    setIsActive(now < endDate);
    
    const diffTime = Math.abs(newYear - now);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    setDaysUntilNewYear(diffDays);
  }, []);

  if (!isActive) return null;

  return (
    <div className="bg-gradient-to-r from-red-700 via-green-700 to-red-700 text-white py-2 px-4 text-center relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent animate-shimmer"></div>
      </div>
      
      <div className="relative z-10 flex items-center justify-center gap-2 text-sm font-semibold">
        <Sparkles className="h-4 w-4 animate-pulse" />
        <span className="hidden sm:inline">🎄</span>
        <span>
          Season's Greetings! Merry Christmas & Happy New Year 2026
        </span>
        <span className="hidden sm:inline">🎅</span>
        <Gift className="h-4 w-4 animate-bounce" />
        {daysUntilNewYear > 0 && (
          <span className="ml-2 bg-white/20 px-2 py-0.5 rounded-full text-xs">
            {daysUntilNewYear} days to 2026
          </span>
        )}
      </div>

      <style>{`
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }

        .animate-shimmer {
          animation: shimmer 3s infinite;
        }
      `}</style>
    </div>
  );
};

export default FestiveBanner;