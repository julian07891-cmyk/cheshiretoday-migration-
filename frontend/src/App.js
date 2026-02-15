import React, {
  useState,
  useEffect,
  useRef,
  lazy,
  Suspense,
  useCallback,
  useMemo,
} from "react";
import "./App.css";
import { getApiUrl } from "./utils/api";
import { Helmet, HelmetProvider } from "react-helmet-async";
import {
  BrowserRouter,
  Routes,
  Route,
  useParams,
  useNavigate,
  Navigate,
  useLocation,
  Link,
} from "react-router-dom";
import ArticlePageV2 from "./pages/ArticlePageV2";

// Critical components - load immediately
import NewsHeader from "./components/NewsHeader";
import HeroArticle from "./components/HeroArticle";
import CompactArticleCard from "./components/CompactArticleCard";
import HomeSkeleton from "./components/HomeSkeleton";
import AdvertisePage from "./pages/AdvertisePage";
import HomePageV1 from "./pages/HomePageV1";


import SponsoredSidebarBlock from "./components/SponsoredSidebarBlock";

// Lazy load non-critical components to reduce initial bundle
const TrendingSidebar = lazy(() => import("./components/TrendingSidebar"));
const NewsFooter = lazy(() => import("./components/NewsFooter"));
const FestiveTheme = lazy(() => import("./components/FestiveTheme"));
const SubscribeSection = lazy(() => import("./components/SubscribeSection"));
const JobBoardBanner = lazy(() => import("./components/JobBoardBanner"));
const JobsWidget = lazy(() =>
  import("./components/JobsWidget").then((m) => ({ default: m.JobsWidget })),
);
const JobsInlineBanner = lazy(() =>
  import("./components/JobsWidget").then((m) => ({
    default: m.JobsInlineBanner,
  })),
);

// Import SubscribeInlineBanner directly (not lazy) to avoid loading issues
import { SubscribeInlineBanner } from "./components/JobsWidget";
const BreakingNewsTicker = lazy(
  () => import("./components/BreakingNewsTicker"),
);
const RelatedArticles = lazy(() => import("./components/RelatedArticles"));
const AdminDashboard = lazy(() => import("./components/AdminDashboard"));
const NewsletterPopup = lazy(() => import("./components/NewsletterPopup"));
const SocialShare = lazy(() => import("./components/SocialShare"));
const PrivacyPolicy = lazy(() => import("./components/PrivacyPolicy"));
const TermsOfService = lazy(() => import("./components/TermsOfService"));
const AffiliateDisclosure = lazy(
  () => import("./components/AffiliateDisclosure"),
);
const PushNotificationButton = lazy(
  () => import("./components/PushNotificationButton"),
);
const ShareAlertsButton = lazy(() => import("./components/ShareAlertsButton"));
const BottomNav = lazy(() => import("./components/BottomNav"));
const CategoryTabs = lazy(() => import("./components/CategoryTabs"));
const CommentsSection = lazy(() => import("./components/CommentsSection"));
const NewsletterPreferences = lazy(
  () => import("./components/NewsletterPreferences"),
);
const JobBoard = lazy(() => import("./components/JobBoard"));
const PostJob = lazy(() => import("./components/PostJob"));
const PaymentSuccess = lazy(() => import("./components/PaymentSuccess"));
const MobileSearch = lazy(() => import("./components/MobileSearch"));
const MobileMenu = lazy(() => import("./components/MobileMenu"));
const UnsubscribePage = lazy(() => import("./components/UnsubscribePage"));
const PreferencesPage = lazy(() => import("./components/PreferencesPage"));

// Lazy load affiliate widgets
const AffiliateWidgetSidebar = lazy(() =>
  import("./components/AffiliateWidgets").then((m) => ({
    default: m.AffiliateWidgetSidebar,
  })),
);
const AffiliateWidgetInline = lazy(() =>
  import("./components/AffiliateWidgets").then((m) => ({
    default: m.AffiliateWidgetInline,
  })),
);
const AffiliateWidgetEndArticle = lazy(() =>
  import("./components/AffiliateWidgets").then((m) => ({
    default: m.AffiliateWidgetEndArticle,
  })),
);
const AffiliateWidgetMobile = lazy(() =>
  import("./components/AffiliateWidgets").then((m) => ({
    default: m.AffiliateWidgetMobile,
  })),
);

// Import product data for ArticlePage affiliate widget coordination
import {
  SAMPLE_PRODUCTS,
  fetchDatabaseProducts,
} from "./components/AffiliateWidgets";

// Random promo widget for between article sections
const RandomPromoWidget = lazy(() => import("./components/RandomPromoWidget"));
import { PromoWidgetProvider } from "./components/RandomPromoWidget";

import { ThemeProvider } from "./contexts/ThemeContext";
import { categories } from "./mockData";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "./components/ui/dialog";
import { Badge } from "./components/ui/badge";
import { Separator } from "./components/ui/separator";
import {
  Clock,
  User,
  Share2,
  Loader2,
  Settings,
  BookOpen,
  MapPin,
  Briefcase,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import { Button } from "./components/ui/button";
import { toast } from "./hooks/use-toast";
import { Toaster } from "./components/ui/toaster";
import { articleService } from "./services/api";
import LocationPage from "./components/LocationPage";

// Loading fallback component
const LoadingFallback = () => (
  <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded h-20 w-full"></div>
);

// Admin route wrapper (keeps /admin stable in production)
const AdminPage = () => (
  <Suspense fallback={<LoadingFallback />}>
    <AdminDashboard />
  </Suspense>
);



// Valid location slugs
const VALID_LOCATIONS = [
  "cheshire-general",
  "chester",
  "warrington",
  "crewe",
  "wirral",
  "macclesfield",
  "wilmslow",
  "knutsford",
  "stockport",
  "northwich",
];

// Wrapper to validate location routes
const LocationRouteWrapper = () => {
  const { location } = useParams();
  if (VALID_LOCATIONS.includes(location?.toLowerCase())) {
    return <LocationPage />;
  }
  // If not a valid location, redirect to home
  return <Navigate to="/" replace />;
};

// Main App with Router
function App() {
  return (
    <ThemeProvider>
      <PromoWidgetProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<HomePageV1 />} />
            <Route path="/article/:articleId" element={<ArticlePageV2 categories={categories} />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route
              path="/jobs"
              element={
                <Suspense fallback={<LoadingFallback />}>
                  <JobBoard />
                </Suspense>
              }
            />
            <Route
              path="/jobs/post"
              element={
                <Suspense fallback={<LoadingFallback />}>
                  <PostJob />
                </Suspense>
              }
            />
            <Route
              path="/jobs/payment-success"
              element={
                <Suspense fallback={<LoadingFallback />}>
                  <PaymentSuccess />
                </Suspense>
              }
            />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/terms" element={<TermsOfService />} />
            <Route
              path="/affiliate-disclosure"
              element={<AffiliateDisclosure />}
            />
            <Route
              path="/unsubscribe"
              element={
                <Suspense fallback={<LoadingFallback />}>
                  <UnsubscribePage />
                </Suspense>
              }
            />
            <Route
              path="/newsletter/preferences"
              element={
                <Suspense fallback={<LoadingFallback />}>
                  <PreferencesPage />
                </Suspense>
              }
            />
            {/* Location-specific pages for Local SEO */}
            <Route path="/advertise" element={<AdvertisePage />} />
            <Route path="/:location" element={<LocationRouteWrapper />} />
          </Routes>
        </BrowserRouter>
      </PromoWidgetProvider>
    </ThemeProvider>
  );
}

export default App;
