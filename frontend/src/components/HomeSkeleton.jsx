import React from 'react';

// Skeleton shimmer animation using Tailwind
const Shimmer = ({ className }) => (
  <div className={`animate-pulse bg-gray-200 dark:bg-gray-700 rounded ${className}`} />
);

// Hero article skeleton
const HeroSkeleton = () => (
  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
      <Shimmer className="h-64 lg:h-80" />
      <div className="p-6 space-y-4">
        <Shimmer className="h-6 w-24" />
        <Shimmer className="h-8 w-full" />
        <Shimmer className="h-8 w-3/4" />
        <Shimmer className="h-4 w-full" />
        <Shimmer className="h-4 w-full" />
        <Shimmer className="h-4 w-2/3" />
        <div className="flex items-center gap-4 pt-4">
          <Shimmer className="h-4 w-24" />
          <Shimmer className="h-4 w-32" />
        </div>
      </div>
    </div>
  </div>
);

// Compact article card skeleton
const ArticleCardSkeleton = () => (
  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
    <Shimmer className="h-44" />
    <div className="p-4 space-y-3">
      <Shimmer className="h-5 w-full" />
      <Shimmer className="h-5 w-3/4" />
      <div className="flex items-center gap-2">
        <Shimmer className="h-4 w-16" />
        <Shimmer className="h-4 w-24" />
      </div>
    </div>
  </div>
);

// Sidebar skeleton
const SidebarSkeleton = () => (
  <div className="space-y-6">
    {/* Newsletter skeleton */}
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 space-y-4">
      <Shimmer className="h-6 w-32" />
      <Shimmer className="h-4 w-full" />
      <Shimmer className="h-10 w-full" />
      <Shimmer className="h-10 w-full" />
    </div>
    {/* Trending skeleton */}
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 space-y-4">
      <Shimmer className="h-6 w-24" />
      {[1, 2, 3].map(i => (
        <div key={i} className="flex gap-3">
          <Shimmer className="h-16 w-20 flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Shimmer className="h-4 w-full" />
            <Shimmer className="h-4 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  </div>
);

// Full homepage skeleton
const HomeSkeleton = () => (
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
    {/* Header skeleton */}
    <header className="bg-white dark:bg-gray-800 shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Shimmer className="h-8 w-40" />
          <div className="hidden md:flex gap-4">
            <Shimmer className="h-8 w-20" />
            <Shimmer className="h-8 w-20" />
            <Shimmer className="h-8 w-20" />
          </div>
        </div>
      </div>
    </header>

    {/* Location bar skeleton */}
    <div className="bg-gray-100 dark:bg-gray-800 py-2">
      <div className="container mx-auto px-4">
        <div className="flex gap-2 overflow-hidden">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <Shimmer key={i} className="h-8 w-24 flex-shrink-0" />
          ))}
        </div>
      </div>
    </div>

    {/* Hero skeleton */}
    <div className="container mx-auto px-4 py-8">
      <HeroSkeleton />
    </div>

    {/* Main content skeleton */}
    <div className="container mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-8">
          {/* Section header */}
          <div className="flex items-center gap-2 pb-4 border-b-2 border-gray-200 dark:border-gray-700">
            <Shimmer className="h-6 w-6" />
            <Shimmer className="h-6 w-32" />
          </div>
          {/* Article grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => (
              <ArticleCardSkeleton key={i} />
            ))}
          </div>
        </div>

        {/* Sidebar */}
        <div className="hidden lg:block">
          <SidebarSkeleton />
        </div>
      </div>
    </div>
  </div>
);

export default HomeSkeleton;
