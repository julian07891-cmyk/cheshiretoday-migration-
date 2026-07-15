import React, { useState, useEffect, useCallback, useMemo, useRef, memo } from 'react';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import { 
  BarChart3, Users, FileText, Mail, RefreshCw, Trash2,
  Zap, 
  Send, Clock, AlertCircle, CheckCircle, Loader2, ArrowLeft,
  Newspaper, TrendingUp, Lock, LogOut, Facebook, Calendar as CalendarIcon,
  X, Check, Share2, Twitter, PlusCircle, Edit, Image as ImageIcon,
  Archive, RotateCcw, Filter, ChevronDown, ChevronRight, ShoppingBag,
  Star, ExternalLink, Link as LinkIcon, PoundSterling, Briefcase, MapPin, Building2,
  Sun, AlertTriangle, Bell, Search, Download, History, Eye, Trash, CheckSquare, Square
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { toast } from "../hooks/use-toast";
import { getApiUrl } from "../utils/api";
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Calendar } from './ui/calendar';
import { buildArticleUrl } from '../utils/articleUrl';

// Memoized stat card for performance
const StatCard = memo(({ title, value, icon: Icon, color }) => (
  <Card className="dark:bg-gray-800 dark:border-gray-700">
    <CardContent className="pt-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs sm:text-sm font-medium text-muted-foreground dark:text-gray-400">{title}</p>
          <p className="text-2xl sm:text-3xl font-bold text-foreground dark:text-white">{value}</p>
        </div>
        <div className={`h-10 w-10 sm:h-12 sm:w-12 ${color} rounded-full flex items-center justify-center`}>
          <Icon className="h-5 w-5 sm:h-6 sm:w-6" />
        </div>
      </div>
    </CardContent>
  </Card>
));

StatCard.displayName = 'StatCard';
// Token storage key
const TOKEN_KEY = 'cheshire_admin_token';

const AdminDashboard = ({ onBack }) => {
  const [stats, setStats] = useState(null);
  const [subscribers, setSubscribers] = useState([]);
  const [articles, setArticles] = useState([]);
  const currentAdminArticleSearchRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Sub-tab navigation state
  const [articleSubTab, setArticleSubTab] = useState('all');
  const [subscriberSubTab, setSubscriberSubTab] = useState('active');
  const [jobSubTab, setJobSubTab] = useState('active');
  const [digestSubTab, setDigestSubTab] = useState('daily');
  
  // Confirmation dialog state
  const [confirmDialog, setConfirmDialog] = useState({
    open: false,
    title: '',
    description: '',
    action: null,
    variant: 'default', // 'default', 'destructive', 'warning'
    confirmText: 'Confirm',
    cancelText: 'Cancel'
  });
  
  // Bulk selection state
  const [selectedArticles, setSelectedArticles] = useState(new Set());
  const [selectedManualReviewArticles, setSelectedManualReviewArticles] = useState(new Set());
  const [selectedSubscribers, setSelectedSubscribers] = useState(new Set());
  const [selectedJobs, setSelectedJobs] = useState(new Set());
  
  // Search and filter state
  const [articleSearch, setArticleSearch] = useState('');
  const [subscriberSearch, setSubscriberSearch] = useState('');
  const [jobSearch, setJobSearch] = useState('');
  
  // Email history state
  const [emailHistory, setEmailHistory] = useState([]);

  // Advertising leads state
  const [advertiserLeads, setAdvertiserLeads] = useState([]);
  const [advertiserLeadsLoading, setAdvertiserLeadsLoading] = useState(false);
  const [sponsoredPlacements, setSponsoredPlacements] = useState([]);
  const [sponsoredPlacementsLoading, setSponsoredPlacementsLoading] = useState(false);
  const [sponsoredPlacementForm, setSponsoredPlacementForm] = useState({
    placement: "article_both",
    package_tier: "Local Starter",
    sponsor_name: "",
    title: "",
    description: "",
    target_url: "",
    image_url: "",
    cta_text: "Learn more",
    active: true,
    source_lead_id: "",
    campaign_id: ""
  });
  const [editingSponsoredPlacementSlug, setEditingSponsoredPlacementSlug] = useState("");
  
  // Email analytics state
  const [emailAnalytics, setEmailAnalytics] = useState(null);
  const [emailAnalyticsLoading, setEmailAnalyticsLoading] = useState(false);
  // Manual campaign email state
  const [campaignSubject, setCampaignSubject] = useState('Cheshire Today update');
  const [campaignHtml, setCampaignHtml] = useState('');
  const [campaignText, setCampaignText] = useState('');
  const [campaignTestEmail, setCampaignTestEmail] = useState('news@cheshiretoday.co.uk');

  
  // Activity log state
  const [activityLog, setActivityLog] = useState([]);
  
  // News import state
  const [importLoading, setImportLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [authChecking, setAuthChecking] = useState(true);

  // Facebook scheduling state
  const [schedulableArticles, setSchedulableArticles] = useState([]);
  
  // Facebook analytics state
  const [fbAnalytics, setFbAnalytics] = useState(null);
  const [fbInsights, setFbInsights] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  
  // Archive and article management state
  const [archivedArticles, setArchivedArticles] = useState([]);
  const [manualReviewArticles, setManualReviewArticles] = useState([]);
  const [articleStats, setArticleStats] = useState(null);
  const [dateFilter, setDateFilter] = useState({ start: '', end: '' });
  const [articlesPage, setArticlesPage] = useState(0);
  const [hasMoreArticles, setHasMoreArticles] = useState(true);
  
  // Smart content prioritization state
  const [smartArticles, setSmartArticles] = useState([]);
  const [smartLoading, setSmartLoading] = useState(false);
  
  // Push notification state
  const [pushStats, setPushStats] = useState(null);
  const [pushMilestones, setPushMilestones] = useState(null);

  // Job Board state
  const [jobs, setJobs] = useState([]);
  const [showAddJob, setShowAddJob] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [jobForm, setJobForm] = useState({
    title: '', company: '', location: 'Macclesfield', job_type: 'Full-time',
    salary: '', description: '', requirements: '', category: 'Other',
    apply_url: '', apply_email: ''
  });
  const [jobOptions, setJobOptions] = useState({ locations: [], categories: [], job_types: [] });

  // Manual Article Creation state
  const [showAddArticle, setShowAddArticle] = useState(false);
  const [editingArticle, setEditingArticle] = useState(null);
  const [articleForm, setArticleForm] = useState({
    title: '',
    summary: '',
    content: '',
    category: 'Local News',
    image: '',
    author: 'Cheshire Today',
    source: '',
    source_url: '',
    tags: '',
    featured: false,
    scope: 'cheshire'
  });
  const [articleSubmitting, setArticleSubmitting] = useState(false);

  // Affiliate Product Management state
  const [affiliateProducts, setAffiliateProducts] = useState([]);
  const [affiliateCategories, setAffiliateCategories] = useState([]);
  const [showAddAffiliate, setShowAddAffiliate] = useState(false);
  const [editingAffiliate, setEditingAffiliate] = useState(null);
  const [affiliateForm, setAffiliateForm] = useState({
    name: '',
    price: '',
    url: '',
    image: '',
    category: 'default',
    rating: 4.5,
    active: true
  });
  const [affiliateSubmitting, setAffiliateSubmitting] = useState(false);

  const CATEGORIES = [
    'Local News', 'UK News', 'Business', 'Tech', 'Sports', 
    'Health', 'Education'
  ];

  // Helper function to show confirmation dialog
  const showConfirmation = useCallback((options) => {
    return new Promise((resolve) => {
      setConfirmDialog({
        open: true,
        title: options.title || 'Confirm Action',
        description: options.description || 'Are you sure you want to proceed?',
        variant: options.variant || 'default',
        confirmText: options.confirmText || 'Confirm',
        cancelText: options.cancelText || 'Cancel',
        action: () => {
          setConfirmDialog(prev => ({ ...prev, open: false }));
          resolve(true);
        },
        onCancel: () => {
          setConfirmDialog(prev => ({ ...prev, open: false }));
          resolve(false);
        }
      });
    });
  }, []);

  // Helper function to log admin activity
  const logActivity = useCallback((action, details) => {
    const entry = {
      id: Date.now(),
      action,
      details,
      timestamp: new Date().toISOString(),
      user: 'Admin'
    };
    setActivityLog(prev => [entry, ...prev].slice(0, 100)); // Keep last 100 entries
  }, []);

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }, []);

  const fetchAdvertiserLeads = useCallback(async () => {
    setAdvertiserLeadsLoading(true);
    try {
      const res = await fetch(`${getApiUrl()}/api/admin/advertiser-leads?limit=100`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setAdvertiserLeads(data.leads || []);
      } else {
        toast({ title: "Failed to load advertising leads", variant: "destructive" });
      }
    } catch (error) {
      console.error("Error fetching advertiser leads:", error);
      toast({ title: "Error loading advertising leads", variant: "destructive" });
    } finally {
      setAdvertiserLeadsLoading(false);
    }
  }, [getAuthHeaders]);

  const fetchSponsoredPlacements = useCallback(async () => {
    setSponsoredPlacementsLoading(true);
    try {
      const res = await fetch(`${getApiUrl()}/api/admin/sponsored-placements?limit=100`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setSponsoredPlacements(data.placements || []);
      } else {
        toast({ title: "Failed to load sponsored placements", variant: "destructive" });
      }
    } catch (error) {
      console.error("Error fetching sponsored placements:", error);
      toast({ title: "Error loading sponsored placements", variant: "destructive" });
    } finally {
      setSponsoredPlacementsLoading(false);
    }
  }, [getAuthHeaders]);

  const sponsoredPlacementReport = React.useMemo(() => {
    const rows = Array.isArray(sponsoredPlacements) ? sponsoredPlacements : [];
    const now = Date.now();
    const active = rows.filter((placement) => placement.active && (!placement.ends_at || Date.parse(placement.ends_at) >= now)).length;
    const impressions = rows.reduce((sum, placement) => sum + Number(placement.impression_count || 0), 0);
    const clicks = rows.reduce((sum, placement) => sum + Number(placement.click_count || 0), 0);
    const ctr = impressions > 0 ? ((clicks / impressions) * 100).toFixed(2) : "0.00";
    return { active, impressions, clicks, ctr };
  }, [sponsoredPlacements]);

  const exportSponsoredPlacementsCsv = useCallback(() => {
    const rows = Array.isArray(sponsoredPlacements) ? sponsoredPlacements : [];
    if (rows.length === 0) {
      toast({ title: "No sponsored placements to export", variant: "destructive" });
      return;
    }

    const escapeCsv = (value) => `"${String(value ?? "").replace(/"/g, "\"\"")}"`;
    const headers = ["Sponsor", "Title", "Placement", "Package", "Status", "Starts", "Expires", "Impressions", "Clicks", "CTR", "Target URL", "Campaign ID", "Slug"];
    const lines = rows.map((placement) => {
      const impressions = Number(placement.impression_count || 0);
      const clicks = Number(placement.click_count || 0);
      const ctr = impressions > 0 ? ((clicks / impressions) * 100).toFixed(2) + "%" : "0.00%";
      const status = placement.ends_at && Date.parse(placement.ends_at) < Date.now() ? "expired" : placement.active ? "active" : "inactive";
      return [
        placement.sponsor_name,
        placement.title,
        placement.placement,
        placement.package_tier,
        status,
        placement.starts_at ? new Date(placement.starts_at).toLocaleDateString("en-GB") : "",
        placement.ends_at ? new Date(placement.ends_at).toLocaleDateString("en-GB") : "",
        impressions,
        clicks,
        ctr,
        placement.target_url,
        placement.campaign_id,
        placement.slug,
      ].map(escapeCsv).join(",");
    });

    const csv = [headers.map(escapeCsv).join(","), ...lines].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `cheshire-today-sponsored-placements-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    toast({ title: "Sponsored placements CSV exported" });
  }, [sponsoredPlacements]);

  const saveSponsoredPlacement = useCallback(async (event) => {
    event.preventDefault();

    const sponsorName = String(sponsoredPlacementForm.sponsor_name || "").trim();
    const placementChoice = String(sponsoredPlacementForm.placement || "both").trim();
    const packageTier = String(sponsoredPlacementForm.package_tier || "Local Starter").trim();
    const targetUrl = String(sponsoredPlacementForm.target_url || "").trim();

    if (!sponsorName || !sponsoredPlacementForm.title || !targetUrl) {
      toast({ title: "Sponsor name, advert title and target URL are required", variant: "destructive" });
      return;
    }

    if (!/^https?:\/\//i.test(targetUrl)) {
      toast({ title: "Target URL must start with http:// or https://", variant: "destructive" });
      return;
    }

    const isEditingPlacement = Boolean(editingSponsoredPlacementSlug);
    const placementGroups = {
      article_both: ["article_sidebar", "article_mobile"],
      homepage_both: ["homepage_sidebar", "homepage_mobile"],
    };
    const placementsToCreate = isEditingPlacement ? [placementChoice] : (placementGroups[placementChoice] || [placementChoice]);

    const rotationWeight = packageTier.includes("Partner") ? 4 : packageTier.includes("Featured") ? 2 : 1;
    const priority = packageTier.includes("Partner") ? 30 : packageTier.includes("Featured") ? 20 : 10;
    const slugBase = sponsorName
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 40) || "sponsored-advert";

    const timestamp = Date.now();
    const startsAt = new Date();
    const endsAt = new Date(startsAt.getTime() + (30 * 24 * 60 * 60 * 1000));
    const sourceLeadId = String(sponsoredPlacementForm.source_lead_id || "").trim();
    const campaignId = String(sponsoredPlacementForm.campaign_id || "").trim() || `${slugBase}-${timestamp}`;
    const payloads = placementsToCreate.map((placement, index) => ({
      slug: isEditingPlacement ? editingSponsoredPlacementSlug : `${slugBase}-${placement}-${timestamp}`,
      placement,
      campaign_id: campaignId,
      source_lead_id: sourceLeadId,
      notify_client_on_publish: Boolean(sourceLeadId) && index === placementsToCreate.length - 1,
      package_tier: packageTier,
      rotation_weight: rotationWeight,
      priority,
      sponsor_name: sponsorName,
      title: String(sponsoredPlacementForm.title || "").trim(),
      description: String(sponsoredPlacementForm.description || "").trim(),
      target_url: targetUrl,
      image_url: String(sponsoredPlacementForm.image_url || "").trim(),
      cta_text: String(sponsoredPlacementForm.cta_text || "Learn more").trim(),
      starts_at: startsAt.toISOString(),
      ends_at: endsAt.toISOString(),
      active: Boolean(sponsoredPlacementForm.active)
    }));

    try {
      for (const payload of payloads) {
        const res = await fetch(`${getApiUrl()}/api/admin/sponsored-placements/upsert`, {
          method: "POST",
          headers: {
            ...getAuthHeaders(),
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
      }

      toast({ title: isEditingPlacement ? "Sponsored placement updated" : (payloads.length > 1 ? "Desktop and mobile sponsored placements created" : "Sponsored placement created") });
      setEditingSponsoredPlacementSlug("");
      setSponsoredPlacementForm({
        placement: "article_both",
        package_tier: "Local Starter",
        sponsor_name: "",
        title: "",
        description: "",
        target_url: "",
        image_url: "",
        cta_text: "Learn more",
        active: true,
        source_lead_id: "",
        campaign_id: ""
      });
      fetchSponsoredPlacements();
    } catch (error) {
      console.error("Error saving sponsored placement:", error);
      toast({ title: "Failed to create sponsored placement", variant: "destructive" });
    }
  }, [editingSponsoredPlacementSlug, fetchSponsoredPlacements, getAuthHeaders, sponsoredPlacementForm]);


  const editSponsoredPlacement = useCallback((placement) => {
    if (!placement?.slug) return;

    setEditingSponsoredPlacementSlug(placement.slug);
    setSponsoredPlacementForm({
      placement: placement.placement || "article_sidebar",
      package_tier: placement.package_tier || "Local Starter",
      sponsor_name: placement.sponsor_name || "",
      title: placement.title || "",
      description: placement.description || "",
      target_url: placement.target_url || "",
      image_url: placement.image_url || "",
      cta_text: placement.cta_text || "Learn more",
      active: Boolean(placement.active),
      source_lead_id: placement.source_lead_id || "",
      campaign_id: placement.campaign_id || ""
    });

    toast({ title: "Sponsored placement loaded for editing" });
    setTimeout(() => {
      const form = document.getElementById("create-sponsored-placement");
      if (form) form.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }, []);

  const cancelSponsoredPlacementEdit = useCallback(() => {
    setEditingSponsoredPlacementSlug("");
    setSponsoredPlacementForm({
      placement: "article_both",
      package_tier: "Local Starter",
      sponsor_name: "",
      title: "",
      description: "",
      target_url: "",
      image_url: "",
      cta_text: "Learn more",
      active: true,
      source_lead_id: "",
      campaign_id: ""
    });
  }, []);

  const deleteSponsoredPlacement = useCallback(async (slug) => {
    if (!slug) return;

    try {
      const res = await fetch(`${getApiUrl()}/api/admin/sponsored-placements/${encodeURIComponent(slug)}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      toast({ title: "Sponsored placement deleted" });
      setSponsoredPlacements(prev => prev.filter(item => item.slug !== slug));
    } catch (error) {
      console.error("Error deleting sponsored placement:", error);
      toast({ title: "Failed to delete sponsored placement", variant: "destructive" });
    }
  }, [getAuthHeaders]);

  const buildAdvertiserLeadMailto = useCallback((lead) => {
    const business = String(lead?.business || lead?.name || "your business").trim();
    const tier = String(lead?.tier || lead?.package_tier || "selected package").trim();
    const price = String(lead?.package_price || "").trim();
    const area = String(lead?.target_area || "your chosen area").trim();
    const subject = `Cheshire Today advertising enquiry — ${business}`;
    const body = `Hi ${lead?.name || "there"},\n\nThanks for your advertising enquiry with Cheshire Today.\n\nPackage selected: ${tier}${price ? ` — ${price}` : ""}\nTarget area: ${area}\n\nTo prepare your advert, please send over:\n- Your preferred advert headline\n- Short advert message\n- Website, booking page or Facebook page link\n- Logo or image you would like us to use\n- Any offer, launch, event or service you want to promote\n\nOnce we have the details, we will review the advert for suitability before it goes live. Paid adverts are clearly labelled and can run in the agreed sponsored slots for the 30-day campaign period.\n\nKind regards,\nCheshire Today`;
    return `mailto:${lead?.email || ""}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  }, []);

  const prepareSponsoredPlacementFromLead = useCallback((lead) => {
    const business = String(lead?.business || lead?.name || "").trim();
    const website = String(lead?.website || "").trim();
    const tier = String(lead?.tier || lead?.package_tier || "Local Starter").trim();
    const message = String(lead?.message || "").trim();
    const safeWebsite = website && /^https?:\/\//i.test(website) ? website : website ? `https://${website}` : "";
    const isPartnerLead = /partner/i.test(tier);

    setSponsoredPlacementForm({
      placement: isPartnerLead ? "homepage_both" : "article_both",
      package_tier: tier || "Local Starter",
      sponsor_name: business,
      title: business ? `${business} — sponsored local business` : "",
      description: message,
      target_url: safeWebsite,
      image_url: "",
      cta_text: "Learn more",
      active: true,
      source_lead_id: lead?.id || "",
      campaign_id: ""
    });

    toast({ title: "Sponsored placement form filled from lead" });

    setTimeout(() => {
      const form = document.getElementById("create-sponsored-placement");
      if (form) form.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  }, []);

  const updateAdvertiserLeadStatus = useCallback(async (leadId, status) => {
    try {
      const res = await fetch(`${getApiUrl()}/api/admin/advertiser-leads/${leadId}/status`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ status })
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      if (data?.lead) {
        setAdvertiserLeads(prev => prev.map(lead => lead.id === leadId ? data.lead : lead));
      }

      toast({ title: `Lead marked as ${status}` });
    } catch (error) {
      console.error("Error updating advertiser lead:", error);
      toast({ title: "Failed to update advertising lead", variant: "destructive" });
    }
  }, [getAuthHeaders]);

  const deleteAdvertiserLead = useCallback(async (leadId) => {
    if (!leadId) return;

    try {
      const res = await fetch(`${getApiUrl()}/api/admin/advertiser-leads/${leadId}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      toast({ title: "Advertising lead deleted" });
      setAdvertiserLeads(prev => prev.filter(lead => lead.id !== leadId));
    } catch (error) {
      console.error("Error deleting advertiser lead:", error);
      toast({ title: "Failed to delete advertising lead", variant: "destructive" });
    }
  }, [getAuthHeaders]);

  // Fetch email history
  const fetchEmailHistory = useCallback(async () => {
    try {
      const res = await fetch(`${getApiUrl()}/api/digest-log?limit=50`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setEmailHistory(data.logs || []);
      }
    } catch (error) {
      console.error('Failed to fetch email history:', error);
    }
  }, [getAuthHeaders]);

  // Fetch email analytics
  const fetchEmailAnalytics = useCallback(async () => {
    setEmailAnalyticsLoading(true);
    try {
      const res = await fetch(`${getApiUrl()}/api/admin/email-analytics?days=30`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setEmailAnalytics(data);
      }
    } catch (error) {
      console.error('Failed to fetch email analytics:', error);
    } finally {
      setEmailAnalyticsLoading(false);
    }
  }, [getAuthHeaders]);

  // Check for existing token on mount
  useEffect(() => {
    checkExistingToken();
  }, []);

  const checkExistingToken = async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    console.log('[Admin] Checking existing token:', token ? 'Found (length: ' + token.length + ')' : 'None');
    
    if (token) {
      try {
        const apiUrl = getApiUrl();
        console.log('[Admin] Verifying token at:', apiUrl);
        
        const response = await fetch(`${apiUrl}/api/admin/verify`, {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: AbortSignal.timeout(10000) // Increased timeout
        });
        
        console.log('[Admin] Token verify status:', response.status);
        
        if (response.ok) {
          console.log('[Admin] Token valid, setting authenticated and fetching data');
          setIsAuthenticated(true);
          // Immediately fetch data with the valid token
          await fetchAllData(token);
        } else {
          console.log('[Admin] Token invalid (status:', response.status, '), clearing');
          localStorage.removeItem(TOKEN_KEY);
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.log('[Admin] Token check error:', error.name, error.message);
        // On network error, try to use cached token anyway
        if (error.name === 'TimeoutError' || error.name === 'AbortError') {
          console.log('[Admin] Timeout - attempting to use cached token');
          setIsAuthenticated(true);
          await fetchAllData(token);
        } else {
          localStorage.removeItem(TOKEN_KEY);
          setIsAuthenticated(false);
        }
      }
    }
    setAuthChecking(false);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Prevent double submission
    if (loginLoading) {
      console.log('[Admin] Login already in progress, skipping');
      return;
    }
    
    // Get values from multiple sources for maximum reliability
    const form = e.target;
    const usernameInput = form.querySelector('input[name="username"]');
    const passwordInput = form.querySelector('input[name="password"]');
    
    // Try multiple methods to get the values
    const loginUsername = (
      usernameInput?.value || 
      username || 
      ''
    ).toString().trim();
    
    const loginPassword = (
      passwordInput?.value || 
      password || 
      ''
    ).toString();
    
    console.log('[Admin] Login attempt - username:', loginUsername, 'has password:', loginPassword.length > 0);
    
    if (!loginUsername || !loginPassword) {
      toast({
        title: "❌ Missing Credentials",
        description: "Please enter both username and password",
        variant: "destructive"
      });
      return;
    }
    
    setLoginLoading(true);
    
    // Retry logic for network issues
    const maxRetries = 3;
    let lastError = null;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const apiUrl = getApiUrl();
        console.log(`[Admin] Login attempt ${attempt}/${maxRetries} to:`, apiUrl);
        
        const response = await fetch(`${apiUrl}/api/admin/login`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ 
            username: loginUsername, 
            password: loginPassword 
          }),
          signal: AbortSignal.timeout(20000) // 20 second timeout
        });
        
        console.log('[Admin] Login response status:', response.status);

        if (response.status === 401 || response.status === 403) {
          // read body once for message
          const raw = await response.text();
          let data = {};
          try { data = raw ? JSON.parse(raw) : {}; } catch { data = { message: raw }; }

          toast({
            title: "❌ Login Failed",
            description: data.detail || data.message || "Invalid username or password",
            variant: "destructive"
          });

          setLoginLoading(false);
          return; // IMPORTANT: stop here, no retries, no catch
        }

        if (!response.ok && response.status >= 500) {
          throw new Error(`Server error: ${response.status}`);
        }

        const raw = await response.text();
        let data = {};
        try {
          data = raw ? JSON.parse(raw) : {};
        } catch (err) {
          data = { success: false, message: raw };
        }
        console.log('[Admin] Login response:', data.success ? 'SUCCESS' : 'FAILED', data.token ? '(has token)' : '(no token)');
        
        if (response.ok && data.success && data.token) {
          // Store token first
          localStorage.setItem(TOKEN_KEY, data.token);
          console.log('[Admin] Token stored, length:', data.token.length);
          
          // Clear form
          setUsername('');
          setPassword('');
          if (usernameInput) usernameInput.value = '';
          if (passwordInput) passwordInput.value = '';
          
          // Set authenticated state
          setIsAuthenticated(true);
          
          toast({
            title: "✅ Login Successful",
            description: "Loading dashboard data..."
          });
          
          // CRITICAL: Wait for data fetch to complete
          console.log('[Admin] Starting data fetch...');
          await fetchAllData(data.token);
          console.log('[Admin] Data fetch complete');
          
          toast({
            title: "✅ Dashboard Ready",
            description: "Welcome to the admin dashboard"
          });
          
          setLoginLoading(false);
          return; // Success - exit
        } else {
          // Invalid credentials - don't retry
          console.log('[Admin] Login failed:', data.detail || data.message);
          toast({
            title: "❌ Login Failed",
            description: data.detail || data.message || "Invalid username or password",
            variant: "destructive"
          });
          setLoginLoading(false);
          return;
        }
      } catch (error) {
        lastError = error;
        console.error(`[Admin] Login attempt ${attempt} error:`, error.name, error.message);
        
        if (attempt < maxRetries) {
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        }
      }
    }
    
    // All retries failed
    toast({
      title: "Connection Error",
      description: lastError?.name === 'TimeoutError' 
        ? "Request timed out. Please check your connection." 
        : "Failed to connect to server after multiple attempts.",
      variant: "destructive"
    });
    setLoginLoading(false);
  };

  const handleLogout = async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    try {
      await fetch(`${getApiUrl()}/api/admin/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (error) {
      // Ignore logout errors
    }
    localStorage.removeItem(TOKEN_KEY);
    setIsAuthenticated(false);
    setStats(null);
    setSubscribers([]);
    setArticles([]);
    toast({
      title: "Logged Out",
      description: "You have been logged out successfully"
    });
  };

  // Remove the useEffect that re-fetches on isAuthenticated change
  // Login and checkExistingToken already handle data fetching
  // This was causing race conditions and duplicate fetches

  // Fetch Facebook data when Facebook tab is active
  useEffect(() => {
    if (isAuthenticated && activeTab === 'facebook') {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        fetchFacebookData(token);
      }
    }
  }, [isAuthenticated, activeTab]);

  const fetchAdminArticlesPage = async ({ page = 0, search = '', append = false, token = null } = {}) => {
    const authToken = (typeof token === "string" && token) ? token : localStorage.getItem(TOKEN_KEY);
    if (!authToken) return;

    const authHeaders = { 'Authorization': `Bearer ${authToken}` };
    const skip = page * 50;
    const params = new URLSearchParams({ skip: String(skip), limit: '50' });
    const trimmedSearch = String(search || '').trim();

    if (trimmedSearch) {
      params.set('search', trimmedSearch);
    }

    const response = await fetch(`${getApiUrl()}/api/admin/articles?${params.toString()}`, { headers: authHeaders });
    if (!response.ok) {
      throw new Error(`Failed to fetch admin articles (${response.status})`);
    }

    const data = await response.json();
    const newArticles = data.articles || [];
    const total = Number(data.total || 0);

    setArticles(prev => (append ? [...prev, ...newArticles] : newArticles));
    if (!append && page === 0) currentAdminArticleSearchRef.current = trimmedSearch;
    setArticlesPage(page);
    setHasMoreArticles(skip + newArticles.length < total);
  };

  useEffect(() => {
    if (!isAuthenticated || activeTab !== 'articles') return;

    const trimmedSearch = String(articleSearch || '').trim();
    if (articles.length > 0 && articlesPage === 0 && currentAdminArticleSearchRef.current === trimmedSearch) return;

    const timer = setTimeout(() => {
      fetchAdminArticlesPage({ page: 0, search: trimmedSearch }).catch((error) => {
        console.error('Error searching admin articles:', error);
      });
    }, 300);

    return () => clearTimeout(timer);
  }, [articleSearch, isAuthenticated, activeTab, articles.length, articlesPage]);

  const fetchAllData = async (token = null) => {
    const authToken = (typeof token === "string" && token) ? token : localStorage.getItem(TOKEN_KEY);
    if (!authToken) {
      console.log('[Admin] No token available for fetchAllData');
      return;
    }
    
    console.log('[Admin] fetchAllData starting with token length:', authToken.length);
    setLoading(true);
    const authHeaders = { 'Authorization': `Bearer ${authToken}` };
    const apiUrl = getApiUrl();
    
    try {
      console.log('[Admin] Fetching stats, subscribers, articles from:', apiUrl);
      
      const [statsRes, subscribersRes, articlesRes] = await Promise.all([
        fetch(`${apiUrl}/api/admin/stats`, { 
          headers: authHeaders,
          signal: AbortSignal.timeout(15000)
        }),
        fetch(`${apiUrl}/api/admin/subscribers`, { 
          headers: authHeaders,
          signal: AbortSignal.timeout(15000)
        }),
        fetch(`${apiUrl}/api/admin/articles?limit=50`, { 
          headers: authHeaders,
          signal: AbortSignal.timeout(15000)
        })
      ]);

      console.log('[Admin] Response status - stats:', statsRes.status, 'subscribers:', subscribersRes.status, 'articles:', articlesRes.status);

      if (statsRes.status === 401 || subscribersRes.status === 401 || articlesRes.status === 401) {
        console.log('[Admin] 401 Unauthorized - clearing token');
        localStorage.removeItem(TOKEN_KEY);
        setIsAuthenticated(false);
        toast({
          title: "Session Expired",
          description: "Please log in again",
          variant: "destructive"
        });
        return;
      }

      const statsData = await statsRes.json();
      const subscribersData = await subscribersRes.json();
      const articlesData = await articlesRes.json();

      console.log('[Admin] Data received - stats:', Object.keys(statsData).length, 'fields, subscribers:', (subscribersData.subscribers || []).length, ', articles:', (articlesData.articles || []).length);

      setStats(statsData);
      setSubscribers(subscribersData.subscribers || []);
      setArticles(articlesData.articles || []);
      setArticlesPage(0);
      setHasMoreArticles(((articlesData.total || 0) > ((articlesData.articles || []).length)));
      
      // Fetch jobs
      try {
        const jobsRes = await fetch(`${apiUrl}/api/admin/jobs`, { headers: authHeaders });
        const jobsData = await jobsRes.json();
        setJobs(jobsData.jobs || []);
        
        const optionsRes = await fetch(`${apiUrl}/api/jobs/meta/options`);
        const optionsData = await optionsRes.json();
        setJobOptions(optionsData);
      } catch (e) {
        console.log('[Admin] Jobs fetch error:', e);
      }
      
      console.log('[Admin] State updated successfully');
    } catch (error) {
      console.error('[Admin] Error fetching admin data:', error.name, error.message);
      toast({
        title: "Error Loading Data",
        description: error.name === 'TimeoutError' ? "Request timed out. Try refreshing." : "Failed to load dashboard data. Try refreshing.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchFacebookData = async (token = null) => {
    const authToken = (typeof token === "string" && token) ? token : localStorage.getItem(TOKEN_KEY);
    if (!authToken) return;
    
    const authHeaders = { 'Authorization': `Bearer ${authToken}` };
    
    try {
      const articlesRes = await fetch(`${getApiUrl()}/api/facebook/schedulable-articles?limit=20`, { headers: authHeaders });

      if (articlesRes.ok) {
        const articlesData = await articlesRes.json();
        setSchedulableArticles(articlesData.articles || []);
      }
    } catch (error) {
      console.error('Error fetching Facebook data:', error);
    }
  };

  const fetchFacebookAnalytics = async () => {
    const authHeaders = getAuthHeaders();
    setAnalyticsLoading(true);
    
    try {
      const [analyticsRes, insightsRes] = await Promise.all([
        fetch(`${getApiUrl()}/api/facebook/analytics`, { headers: authHeaders }),
        fetch(`${getApiUrl()}/api/facebook/analytics/insights`, { headers: authHeaders })
      ]);

      if (analyticsRes.ok) {
        const analyticsData = await analyticsRes.json();
        setFbAnalytics(analyticsData);
      }

      if (insightsRes.ok) {
        const insightsData = await insightsRes.json();
        setFbInsights(insightsData);
      }
    } catch (error) {
      console.error('Error fetching Facebook analytics:', error);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const fetchSmartArticles = async () => {
    const authHeaders = getAuthHeaders();
    setSmartLoading(true);
    
    try {
      const response = await fetch(`${getApiUrl()}/api/facebook/smart-articles?limit=10`, { headers: authHeaders });
      if (response.ok) {
        const data = await response.json();
        setSmartArticles(data.articles || []);
      }
    } catch (error) {
      console.error('Error fetching smart articles:', error);
    } finally {
      setSmartLoading(false);
    }
  };

  // Archive management functions
  const fetchArchivedArticles = async () => {
    const authHeaders = getAuthHeaders();
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/articles/archived`, { headers: authHeaders });
      if (response.ok) {
        const data = await response.json();
        setArchivedArticles(data.articles || []);
      }
    } catch (error) {
      console.error('Error fetching archived articles:', error);
    }
  };

  const fetchManualReviewArticles = async () => {
    const authHeaders = getAuthHeaders();
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/articles/manual-review?limit=100`, { headers: authHeaders });
      if (response.ok) {
        const data = await response.json();
        setManualReviewArticles(data.articles || []);
      }
    } catch (error) {
      console.error('Error fetching manual review articles:', error);
    }
  };

  const fetchArticleStats = async () => {
    const authHeaders = getAuthHeaders();
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/articles/stats`, { headers: authHeaders });
      if (response.ok) {
        const data = await response.json();
        setArticleStats(data);
      }
    } catch (error) {
      console.error('Error fetching article stats:', error);
    }
  };

  const handleArchiveArticle = async (articleId) => {
    setActionLoading(`archive-${articleId}`);
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/articles/${articleId}/archive`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      if (data.success) {
        toast({ title: "✅ Archived", description: "Article moved to archive" });
        fetchAllData();
        fetchArchivedArticles();
      } else {
        toast({ title: "❌ Error", description: data.detail || "Failed to archive", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "❌ Error", description: error.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleMoveToManualReview = async (articleId) => {
    setActionLoading(`manual-review-${articleId}`);
    try {
      const response = await fetch(
        `${getApiUrl()}/api/admin/articles/${articleId}/move-to-manual-review`,
        {
          method: 'POST',
          headers: getAuthHeaders()
        }
      );
      const data = await response.json();

      if (response.ok && data.success) {
        toast({
          title: "✅ Sent to Manual Review",
          description: "Article hidden from the public site and added to Manual Review"
        });
        fetchAllData();
        fetchManualReviewArticles();
        fetchArticleStats();
      } else {
        toast({
          title: "❌ Error",
          description: data.detail || "Failed to move article to Manual Review",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "❌ Error",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleAIReviewArticle = async (articleId) => {
    setActionLoading(`ai-review-${articleId}`);
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/articles/${articleId}/ai-review`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();

      if (response.ok && data.success) {
        const risk = data.review?.risk_level || 'unknown';
        const action = data.review?.recommended_action || 'reviewed';
        toast({
          title: "✅ ChatGPT review complete",
          description: `Risk: ${risk} · Action: ${action}`
        });
        fetchAllData();
      } else {
        toast({
          title: "❌ ChatGPT review failed",
          description: data.detail || "Failed to review article",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "❌ ChatGPT review failed",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleOpenAIRewriteDraft = async (article) => {
    const articleId = article?._id || article?.id;
    if (!articleId) {
      toast({
        title: "❌ OpenAI rewrite failed",
        description: "Article ID missing",
        variant: "destructive"
      });
      return;
    }

    setActionLoading(`openai-rewrite-${articleId}`);
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/articles/${articleId}/openai-rewrite-draft`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();

      if (response.ok && data.success && data.draft) {
        const draft = data.draft;
        setArticleForm({
          title: draft.title || article.title || '',
          summary: draft.summary || article.summary || '',
          content: draft.content || article.content || '',
          category: draft.category || article.category || 'Local News',
          image: article.image || '',
          author: article.author || 'Cheshire Today',
          source: article.source === 'Manual Entry' ? '' : (article.source || ''),
          source_url: article.source_url || article.sourceUrl || '',
          tags: Array.isArray(article.tags) ? article.tags.join(', ') : '',
          featured: article.featured || false,
          scope: article.scope || 'cheshire'
        });
        setEditingArticle(article);
        setShowAddArticle(true);
        toast({
          title: "✅ OpenAI draft ready",
          description: draft.editor_notes || "Review the draft, edit if needed, then press Update Article."
        });
      } else {
        toast({
          title: "❌ OpenAI rewrite failed",
          description: data.detail || "Failed to create rewrite draft",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "❌ OpenAI rewrite failed",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };


  const handleUnarchiveArticle = async (articleId) => {
    setActionLoading(`unarchive-${articleId}`);
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/articles/${articleId}/unarchive`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      if (data.success) {
        toast({ title: "✅ Restored", description: "Article restored from archive" });
        fetchAllData();
        fetchArchivedArticles();
      } else {
        toast({ title: "❌ Error", description: data.detail || "Failed to restore", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "❌ Error", description: error.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleBulkArchive = async (daysOld) => {
    if (!confirm(`Archive all articles older than ${daysOld} days?`)) return;
    setActionLoading('bulk-archive');
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/articles/bulk-archive?days_old=${daysOld}`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      if (data.success) {
        toast({ title: "✅ Bulk Archive Complete", description: data.message });
        fetchAllData();
        fetchArchivedArticles();
        fetchArticleStats();
      } else {
        toast({ title: "❌ Error", description: data.detail || "Failed to bulk archive", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "❌ Error", description: error.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  const loadMoreArticles = async () => {
    const newPage = articlesPage + 1;
    try {
      await fetchAdminArticlesPage({ page: newPage, search: articleSearch, append: true });
    } catch (error) {
      console.error('Error loading more articles:', error);
    }
  };

  const fetchPushStats = async () => {
    const authHeaders = getAuthHeaders();
    try {
      const [statsRes, milestonesRes] = await Promise.all([
        fetch(`${getApiUrl()}/api/push/stats`, { headers: authHeaders }),
        fetch(`${getApiUrl()}/api/push/milestones`, { headers: authHeaders })
      ]);
      
      if (statsRes.ok) {
        const data = await statsRes.json();
        setPushStats(data);
      }
      
      if (milestonesRes.ok) {
        const data = await milestonesRes.json();
        setPushMilestones(data);
      }
    } catch (error) {
      console.error('Error fetching push stats:', error);
    }
  };

  const sendBreakingNewsNotification = async (title) => {
    const authHeaders = getAuthHeaders();
    try {
      const response = await fetch(`${getApiUrl()}/api/push/send-breaking-news`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders },
        body: JSON.stringify({ title })
      });
      const data = await response.json();
      if (data.success) {
        toast({
          title: "📢 Notification Sent",
          description: `Sent to ${data.sent} subscribers`
        });
      } else {
        toast({
          title: "Failed",
          description: data.error || "Could not send notification",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error sending notification:', error);
    }
  };

  // Manual Article Creation/Edit functions
  const resetArticleForm = () => {
    setArticleForm({
      title: '',
      summary: '',
      content: '',
      category: 'Local News',
      image: '',
      author: 'Cheshire Today',
      source: '',
      source_url: '',
      tags: '',
      featured: false,
      scope: 'cheshire'
    });
    setEditingArticle(null);
  };

  const handleAddArticle = () => {
    resetArticleForm();
    setShowAddArticle(true);
  };

  const handleEditArticle = (article) => {
    setArticleForm({
      title: article.title || '',
      summary: article.summary || '',
      content: article.content || '',
      category: article.category || 'Local News',
      image: article.image || '',
      author: article.author || 'Cheshire Today',
      source: article.source === 'Manual Entry' ? '' : (article.source || ''),
      source_url: article.source_url || article.sourceUrl || '',
      tags: Array.isArray(article.tags) ? article.tags.join(', ') : '',
      featured: article.featured || false,
      scope: article.scope || 'cheshire'
    });
    setEditingArticle(article);
    setShowAddArticle(true);
  };

  const handleSubmitArticle = async (e) => {
    e.preventDefault();
    setArticleSubmitting(true);

    try {
      const url = editingArticle 
        ? `${getApiUrl()}/api/admin/articles/${editingArticle.id}`
        : `${getApiUrl()}/api/admin/articles`;
      
      const method = editingArticle ? 'PUT' : 'POST';
      
      const payload = {
        ...articleForm,
        tags: articleForm.tags.split(',').map(t => t.trim()).filter(t => t)
      };

      const response = await fetch(url, {
        method,
        headers: { 
          'Content-Type': 'application/json',
          ...getAuthHeaders() 
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (data.success) {
        toast({
          title: editingArticle ? "✅ Article Updated" : "✅ Article Created",
          description: editingArticle ? "Your changes have been saved" : "New article published successfully"
        });
        setShowAddArticle(false);
        const savedArticle = {
          ...(editingArticle || {}),
          ...(data.article || {}),
          ...payload,
          id: data.article?.id || editingArticle?.id,
          publishedDate: data.article?.publishedDate || editingArticle?.publishedDate || new Date().toISOString(),
          source: payload.source || editingArticle?.source || data.article?.source || "Manual Entry",
          source_url: payload.source_url ?? editingArticle?.source_url ?? editingArticle?.sourceUrl ?? data.article?.source_url ?? "",
          updated_at: new Date().toISOString()
        };
        setArticles(prev => [savedArticle, ...prev.filter(a => a.id !== savedArticle.id)]);
        fetchManualReviewArticles();
        if (data.restored_from_manual_review) {
          setManualReviewArticles(prev => prev.filter(a => a.id !== savedArticle.id));
          fetchArchivedArticles();
          fetchArticleStats();
          toast({
            title: "✅ Article Restored",
            description: "Manual review article was edited and restored to the live site"
          });
        }
        resetArticleForm();
      } else {
        throw new Error(data.detail || 'Failed to save article');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error.message || "Failed to save article",
        variant: "destructive"
      });
    } finally {
      setArticleSubmitting(false);
    }
  };

  // Affiliate Product Management functions
  const fetchAffiliateProducts = async () => {
    const authHeaders = getAuthHeaders();
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/affiliates?active_only=false`, { headers: authHeaders });
      if (response.ok) {
        const data = await response.json();
        setAffiliateProducts(data.products || []);
        setAffiliateCategories(data.categories || []);
      }
    } catch (error) {
      console.error('Error fetching affiliate products:', error);
    }
  };

  const resetAffiliateForm = () => {
    setAffiliateForm({
      name: '',
      price: '',
      url: '',
      image: '',
      category: 'default',
      rating: 4.5,
      active: true
    });
    setEditingAffiliate(null);
  };

  const handleAddAffiliate = () => {
    resetAffiliateForm();
    setShowAddAffiliate(true);
  };

  const handleEditAffiliate = (product) => {
    setAffiliateForm({
      name: product.name || '',
      price: product.price || '',
      url: product.url || '',
      image: product.image || '',
      category: product.category || 'default',
      rating: product.rating || 4.5,
      active: product.active !== false
    });
    setEditingAffiliate(product);
    setShowAddAffiliate(true);
  };

  const handleSubmitAffiliate = async (e) => {
    e.preventDefault();
    setAffiliateSubmitting(true);

    try {
      const url = editingAffiliate 
        ? `${getApiUrl()}/api/admin/affiliates/${editingAffiliate.id}`
        : `${getApiUrl()}/api/admin/affiliates`;
      
      const method = editingAffiliate ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 
          'Content-Type': 'application/json',
          ...getAuthHeaders() 
        },
        body: JSON.stringify(affiliateForm)
      });

      const data = await response.json();

      if (data.success) {
        toast({
          title: editingAffiliate ? "✅ Product Updated" : "✅ Product Created",
          description: editingAffiliate ? "Your changes have been saved" : "New affiliate product added"
        });
        setShowAddAffiliate(false);
        resetAffiliateForm();
        fetchAffiliateProducts();
      } else {
        throw new Error(data.detail || 'Failed to save product');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error.message || "Failed to save affiliate product",
        variant: "destructive"
      });
    } finally {
      setAffiliateSubmitting(false);
    }
  };

  const handleDeleteAffiliate = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this affiliate product?')) return;
    
    setActionLoading(`delete-affiliate-${productId}`);
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/affiliates/${productId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      
      const data = await response.json();
      if (data.success) {
        toast({
          title: "Product Deleted",
          description: "Affiliate product has been removed"
        });
        fetchAffiliateProducts();
      } else {
        throw new Error('Delete failed');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete affiliate product",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleAffiliateActive = async (product) => {
    setActionLoading(`toggle-affiliate-${product.id}`);
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/affiliates/${product.id}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          ...getAuthHeaders() 
        },
        body: JSON.stringify({ active: !product.active })
      });
      
      const data = await response.json();
      if (data.success) {
        toast({
          title: product.active ? "Product Deactivated" : "Product Activated",
          description: `"${product.name}" is now ${product.active ? 'hidden' : 'visible'} on the site`
        });
        fetchAffiliateProducts();
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update product status",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleGenerateArticles = async () => {
    setActionLoading('generate');
    try {
      const response = await fetch(`${getApiUrl()}/api/generate-articles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ count: 5, include_uk_news: true })
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "✅ Articles Generated",
          description: `Created ${data.generated} new articles (${data.cheshire_articles} Cheshire, ${data.uk_articles} UK)`
        });
        fetchAllData();
      } else {
        toast({
          title: "⚠️ Generation Limited",
          description: "No new articles generated - image pool may be exhausted",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate articles",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleSendDigest = async () => {
    setActionLoading('digest');
    try {
      const response = await fetch(`${getApiUrl()}/api/send-digest`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "📧 Daily Brief Sent",
          description: `Sent to ${data.emails_sent}/${data.subscribers} subscribers with ${data.articles} articles`
        });
      } else {
        toast({
          title: "Warning",
          description: data.message || "Could not send Daily Brief",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send Daily Brief",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handlePostToFacebook = async () => {
    setActionLoading('facebook');
    try {
      const response = await fetch(`${getApiUrl()}/api/facebook/trigger-scheduled`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "📘 Posted to Facebook",
          description: `Successfully posted ${data.posted} articles to your Facebook page`
        });
      } else {
        toast({
          title: "Facebook Post Failed",
          description: data.error || "Could not post to Facebook",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to post to Facebook",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handlePostToTwitter = async () => {
    setActionLoading('twitter');
    try {
      const response = await fetch(`${getApiUrl()}/api/twitter/trigger-scheduled`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "🐦 Posted to Twitter",
          description: `Successfully posted ${data.posted} article(s) to Twitter`
        });
      } else {
        toast({
          title: "Twitter Post Failed",
          description: data.error || data.message || "Could not post to Twitter",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to post to Twitter",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleCleanupDuplicates = async () => {
    if (!window.confirm('This will remove duplicate articles and articles with very short content. Continue?')) {
      return;
    }
    
    setActionLoading('cleanup');
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/remove-duplicates`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "🧹 Cleanup Complete",
          description: `Removed ${data.duplicates_removed} duplicates and ${data.short_articles_removed} short articles. ${data.remaining_articles} articles remaining.`
        });
        fetchAllData();
      } else {
        toast({
          title: "Warning",
          description: "Cleanup failed",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to cleanup duplicates",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleFixMismatchedContent = async () => {
    if (!window.confirm('This will fix articles with mismatched template content (e.g., entertainment articles with emergency services text). Continue?')) {
      return;
    }
    
    setActionLoading('fix-content');
    try {
      const response = await fetch(`${getApiUrl()}/api/fix-mismatched-content`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "📝 Content Fixed",
          description: `Fixed ${data.articles_fixed} articles with mismatched templates.`
        });
        if (data.articles_fixed > 0) {
          fetchAllData();
        }
      } else {
        toast({
          title: "Warning",
          description: "Content fix failed",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fix mismatched content",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRemoveProductArticles = async () => {
    if (!window.confirm('This will PERMANENTLY DELETE all product/gadget/shopping articles (NutriBullet, air fryers, deals, etc.). Continue?')) {
      return;
    }
    
    setActionLoading('remove-products');
    try {
      const response = await fetch(`${getApiUrl()}/api/remove-product-articles`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "🗑️ Products Removed",
          description: `Deleted ${data.articles_removed} product/gadget articles.`
        });
        if (data.articles_removed > 0) {
          fetchAllData();
        }
      } else {
        toast({
          title: "Warning",
          description: "Product removal failed",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove product articles",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleSyncRSS = async () => {
    if (!window.confirm('This will fetch the latest articles from all RSS feeds and import up to 10 new articles. Continue?')) {
      return;
    }
    
    setActionLoading('sync-rss');
    try {
      const response = await fetch(`${getApiUrl()}/api/sync-rss-now`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "📡 RSS Sync Complete",
          description: `Imported ${data.articles_imported} new articles from ${data.rss_articles_found} RSS items`
        });
        if (data.articles_imported > 0) {
          fetchAllData();
        }
      } else {
        toast({
          title: "Warning",
          description: "RSS sync failed",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to sync RSS feeds",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  // News Import Handlers
  const handleImportNews = async () => {
    setImportLoading(true);
    setImportResult(null);
    try {
      const response = await fetch(`${getApiUrl()}/api/import-hybrid-news`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem(TOKEN_KEY)}`
        },
        body: JSON.stringify({
          cheshire_articles: 8,
          uk_articles: 12,
          max_sports: 3,
          business_articles: 2,
          health_articles: 2,
          tech_articles: 2,
          entertainment_articles: 2,
          use_perplexity: true
        })
      });
      
      // Check if response is ok before trying to parse JSON
      if (!response.ok) {
        let errorMessage = 'Import failed';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      setImportResult(data);
      toast({
        title: "Import Complete",
        description: `Imported ${data.total_imported} articles successfully`
      });
      fetchAllData(); // Refresh stats
    } catch (error) {
      console.error('Import error:', error);
      toast({
        title: "Import Failed",
        description: error.message || 'An unexpected error occurred. Please try again.',
        variant: "destructive"
      });
    } finally {
      setImportLoading(false);
    }
  };

  const handleClearAndRefresh = async () => {
    const confirmed = await showConfirmation({
      title: 'Archive & Refresh All Articles',
      description: 'This will move ALL existing articles to the Archive and import fresh news from RSS feeds. Archived articles can be restored later. This action may take a few minutes.',
      variant: 'warning',
      confirmText: 'Archive & Refresh',
      cancelText: 'Cancel'
    });
    
    if (!confirmed) return;
    
    setImportLoading(true);
    setImportResult(null);
    logActivity('Archive & Refresh', 'Started archiving all articles and importing fresh news');
    
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/clear-and-refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem(TOKEN_KEY)}`
        }
      });
      
      // Check if response is ok before trying to parse JSON
      if (!response.ok) {
        let errorMessage = 'Archive and refresh failed';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      setImportResult(data);
      toast({
        title: "Archive & Refresh Complete",
        description: `Archived ${data.archived} articles and imported ${data.articles_imported} fresh articles`
      });
      fetchAllData(); // Refresh stats
    } catch (error) {
      console.error('Archive & Refresh error:', error);
      toast({
        title: "Refresh Failed",
        description: error.message || 'An unexpected error occurred. Please try again.',
        variant: "destructive"
      });
    } finally {
      setImportLoading(false);
    }
  };

  // Backfill Locations Handler - assigns location tags to articles based on content
  const [backfillLoading, setBackfillLoading] = useState(false);
  const handleBackfillLocations = async () => {
    const confirmed = await showConfirmation({
      title: 'Backfill Article Locations',
      description: 'This will scan all articles and automatically assign location tags (Chester, Warrington, Macclesfield, etc.) based on their content. Articles mentioning surrounding towns will also be tagged to their parent location.',
      variant: 'default',
      confirmText: 'Run Backfill',
      cancelText: 'Cancel'
    });
    
    if (!confirmed) return;
    
    setBackfillLoading(true);
    logActivity('Location Backfill', 'Started scanning articles for location tags');
    
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/backfill-locations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });
      
      if (!response.ok) {
        let errorMessage = 'Location backfill failed';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      const results = data.results || {};
      const locationCounts = results.location_counts || {};
      
      // Build location summary
      const locationSummary = Object.entries(locationCounts)
        .sort((a, b) => b[1] - a[1])
        .map(([loc, count]) => `${loc}: ${count}`)
        .join(', ');
      
      toast({
        title: "Location Backfill Complete",
        description: `Updated ${results.articles_updated + results.archived_updated} articles. Locations: ${locationSummary || 'None found'}`
      });
      
      logActivity('Location Backfill', `Completed: ${results.articles_updated} active + ${results.archived_updated} archived articles tagged`);
      fetchAllData(); // Refresh stats
    } catch (error) {
      console.error('Location backfill error:', error);
      toast({
        title: "Backfill Failed",
        description: error.message || 'An unexpected error occurred. Please try again.',
        variant: "destructive"
      });
    } finally {
      setBackfillLoading(false);
    }
  };

  // Breaking News Handler with confirmation
  const handleSendBreakingNews = async () => {
    const headline = document.getElementById('breaking-headline')?.value;
    const bulletsText = document.getElementById('breaking-bullets')?.value;
    const articleUrl = document.getElementById('breaking-url')?.value;
    
    if (!headline) {
      toast({ title: "Enter headline", description: "Please enter a headline", variant: "destructive" });
      return;
    }
    
    const bulletPoints = bulletsText?.split('\n').filter(b => b.trim()) || [];
    if (bulletPoints.length === 0) {
      toast({ title: "Enter details", description: "Please add at least one 'What we know' point", variant: "destructive" });
      return;
    }
    
    const confirmed = await showConfirmation({
      title: '🚨 Send Breaking News Alert',
      description: `This will send an URGENT alert to ALL subscribers with Breaking News enabled.\n\nHeadline: "${headline}"\n\nThis should only be used for genuine emergencies. Are you sure?`,
      variant: 'destructive',
      confirmText: 'Send Breaking News',
      cancelText: 'Cancel'
    });
    
    if (!confirmed) return;
    
    setActionLoading('breaking-news');
    logActivity('Breaking News', `Sent: ${headline}`);
    
    try {
      const res = await fetch(`${getApiUrl()}/api/send-breaking-news`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          headline,
          bullet_points: bulletPoints,
          article_url: articleUrl || null
        })
      });
      const data = await res.json();
      if (data.success) {
        toast({
          title: "🚨 Breaking News Sent",
          description: data.message
        });
        document.getElementById('breaking-headline').value = '';
        document.getElementById('breaking-bullets').value = '';
        document.getElementById('breaking-url').value = '';
      } else {
        toast({ title: "❌ Failed", description: data.detail || data.message, variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "❌ Error", description: error.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  // Announcement Email Handler with confirmation
  const handleSendAnnouncement = async () => {
    const confirmed = await showConfirmation({
      title: 'Send Migration Announcement',
      description: 'This will send a one-time announcement to ALL subscribers informing them about the new email schedule (Daily Brief, Weekly Roundup, Breaking News). All subscribers will be migrated to The Daily Brief by default.\n\nThis should only be done once. Are you sure?',
      variant: 'warning',
      confirmText: 'Send Announcement',
      cancelText: 'Cancel'
    });
    
    if (!confirmed) return;
    
    setActionLoading('announcement');
    logActivity('Announcement', 'Sent migration announcement to all subscribers');
    
    try {
      const res = await fetch(`${getApiUrl()}/api/send-announcement-email`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      if (data.success) {
        toast({
          title: "✅ Announcement Sent",
          description: data.message
        });
      } else {
        toast({ title: "❌ Failed", description: data.detail || data.message, variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "❌ Error", description: error.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  // Site Update Part 1 (Day 3 style) - broadcast tool (currently sends to ALL subscribers)
  const handleSendSiteUpdatePart1 = async () => {
    const confirmed = await showConfirmation({
      title: 'Send Site Update (Part 1)',
      description: "This will send Site Update (Part 1) to ALL subscribers. Continue?",
      variant: 'warning',
      confirmText: 'Send Part 1',
      cancelText: 'Cancel'
    });

    if (!confirmed) return;

    setActionLoading('site-update-part1');
    logActivity('Site Update Part 1', 'Sent Site Update (Part 1) to all subscribers');

    try {
      const res = await fetch(`${getApiUrl()}/api/send-site-update-part1`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      if (data.success) {
        toast({ title: "✅ Site Update (Part 1) Sent", description: data.message });
      } else {
        toast({ title: "❌ Failed", description: data.detail || data.message || "Failed to send", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "❌ Error", description: error.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  // Site Update Part 2 (Day 7 style) - broadcast tool (currently sends to ALL subscribers)
  const handleSendSiteUpdatePart2 = async () => {
    const confirmed = await showConfirmation({
      title: 'Send Site Update (Part 2)',
      description: "This will send Site Update (Part 2) to ALL subscribers. Continue?",
      variant: 'warning',
      confirmText: 'Send Part 2',
      cancelText: 'Cancel'
    });

    if (!confirmed) return;

    setActionLoading('site-update-part2');
    logActivity('Site Update Part 2', 'Sent Site Update (Part 2) to all subscribers');

    try {
      const res = await fetch(`${getApiUrl()}/api/send-site-update-part2`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      if (data.success) {
        toast({ title: "✅ Site Update (Part 2) Sent", description: data.message });
      } else {
        toast({ title: "❌ Failed", description: data.detail || data.message || "Failed to send", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "❌ Error", description: error.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };


  // Manual Campaign Email Handlers (test + send all)
  const handleCampaignSendTest = async () => {
    const confirmed = await showConfirmation({
      title: 'Send Test Campaign Email',
      description: `This will send a test email to: ${campaignTestEmail || 'your admin email'}. Continue?`,
      variant: 'warning',
      confirmText: 'Send Test',
      cancelText: 'Cancel'
    });
    if (!confirmed) return;

    setActionLoading('campaign-test');
    logActivity('Campaign Test', `Subject: ${campaignSubject}`);

    try {
      const res = await fetch(`${getApiUrl()}/api/admin/send-campaign-email`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject: campaignSubject,
          html: campaignHtml,
          text: campaignText,
          mode: 'test',
          test_email: campaignTestEmail
        })
      });
      const data = await res.json();
      if (data.success) {
        toast({ title: "✅ Test Sent", description: data.message });
      } else {
        toast({ title: "❌ Failed", description: data.detail || data.message, variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "❌ Error", description: error.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleCampaignSendAll = async () => {
    const confirmed = await showConfirmation({
      title: 'Send Campaign to ALL Subscribers',
      description: 'This will send your custom announcement to ALL subscribers. Make sure the content is final. Continue?',
      variant: 'destructive',
      confirmText: 'Send to All',
      cancelText: 'Cancel'
    });
    if (!confirmed) return;

    setActionLoading('campaign-all');
    logActivity('Campaign All', `Subject: ${campaignSubject}`);

    try {
      const res = await fetch(`${getApiUrl()}/api/admin/send-campaign-email`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject: campaignSubject,
          html: campaignHtml,
          text: campaignText,
          mode: 'all'
        })
      });
      const data = await res.json();
      if (data.success) {
        toast({ title: "✅ Campaign Sent", description: data.message });
        fetchEmailHistory();
        fetchEmailAnalytics();
      } else {
        toast({ title: "❌ Failed", description: data.detail || data.message, variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "❌ Error", description: error.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };


  // Job Board Handlers
  const handleCreateJob = async () => {
    if (!jobForm.title || !jobForm.company || !jobForm.description) {
      toast({ title: "Missing Fields", description: "Title, company and description are required", variant: "destructive" });
      return;
    }
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/jobs`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(jobForm)
      });
      const data = await response.json();
      if (data.success) {
        toast({ title: "✅ Job Posted", description: `${jobForm.title} has been added` });
        setShowAddJob(false);
        setJobForm({ title: '', company: '', location: 'Macclesfield', job_type: 'Full-time', salary: '', description: '', requirements: '', category: 'Other', apply_url: '', apply_email: '' });
        fetchAllData();
      }
    } catch (error) {
      toast({ title: "Error", description: "Failed to create job", variant: "destructive" });
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (!window.confirm('Delete this job listing?')) return;
    try {
      await fetch(`${getApiUrl()}/api/admin/jobs/${jobId}`, { method: 'DELETE', headers: getAuthHeaders() });
      toast({ title: "Deleted", description: "Job removed" });
      fetchAllData();
    } catch (error) {
      toast({ title: "Error", description: "Failed to delete job", variant: "destructive" });
    }
  };

  const handleToggleJobActive = async (jobId) => {
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/jobs/${jobId}/toggle`, { method: 'POST', headers: getAuthHeaders() });
      const data = await response.json();
      toast({ title: data.active ? "Activated" : "Deactivated", description: `Job is now ${data.active ? 'visible' : 'hidden'}` });
      fetchAllData();
    } catch (error) {
      toast({ title: "Error", description: "Failed to toggle job", variant: "destructive" });
    }
  };

  const handleToggleJobFeatured = async (jobId) => {
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/jobs/${jobId}/feature`, { method: 'POST', headers: getAuthHeaders() });
      const data = await response.json();
      toast({ title: data.featured ? "Featured" : "Unfeatured", description: `Job is now ${data.featured ? 'featured' : 'regular'}` });
      fetchAllData();
    } catch (error) {
      toast({ title: "Error", description: "Failed to feature job", variant: "destructive" });
    }
  };

  const handlePostSingleArticle = async (articleId) => {
    // Confirm before posting
    if (!window.confirm('Post this article to Facebook now?')) {
      return;
    }
    
    console.log('Posting article:', articleId);
    setActionLoading(`post-${articleId}`);
    
    try {
      const apiUrl = getApiUrl();
      const url = `${apiUrl}/api/facebook/post-single?article_id=${articleId}`;
      const headers = getAuthHeaders();
      
      console.log('POST URL:', url);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: headers
      });
      
      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);
      
      if (data.success) {
        toast({
          title: "✅ Posted to Facebook!",
          description: `${data.article_title?.substring(0, 40)}...`
        });
        alert('✅ Successfully posted to Facebook!\n\nPost ID: ' + data.post_id);
      } else {
        const errorMsg = data.error || data.message || "Could not post to Facebook";
        toast({
          title: "❌ Post Failed",
          description: errorMsg,
          variant: "destructive"
        });
        alert('❌ Failed to post:\n\n' + errorMsg);
      }
    } catch (error) {
      console.error('Post error:', error);
      toast({
        title: "Error",
        description: "Failed to post: " + error.message,
        variant: "destructive"
      });
      alert('❌ Error:\n\n' + error.message);
    } finally {
      setActionLoading(null);
    }
  };


  const handleForceLiveArticle = async (articleId) => {
    setActionLoading(`force-${articleId}`);
    try {
      const authHeaders = getAuthHeaders();
      const response = await fetch(`${getApiUrl()}/api/admin/articles/${articleId}/force-live`, {
        method: 'POST',
        headers: authHeaders
      });
      const data = await response.json();

      if (response.ok) {
        toast({
          title: data.force_live ? "🚀 Forced Live" : "↩️ Removed Force Live",
          description: data.message
        });
        fetchAllData(); // refresh admin data
      } else {
        toast({ title: "❌ Error", description: data.detail || "Failed", variant: "destructive" });
      }
    } catch (e) {
      toast({ title: "❌ Error", description: "Request failed", variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

const handleDeleteArticle = async (articleId) => {
    if (!window.confirm('Are you sure you want to delete this article?')) return;
    
    setActionLoading(`delete-article-${articleId}`);
    try {
      const response = await fetch(`${getApiUrl()}/api/articles/${articleId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        toast({
          title: "Article Deleted",
          description: "Article has been removed"
        });
        setArticles(articles.filter(a => a.id !== articleId));
        setManualReviewArticles(prev => prev.filter(a => a.id !== articleId));
        fetchManualReviewArticles();
        fetchArchivedArticles();
        fetchAllData();
      } else {
        throw new Error('Delete failed');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete article",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteSelectedManualReviewArticles = async () => {
    const selectedIds = Array.from(selectedManualReviewArticles);

    if (selectedIds.length === 0) return;

    const confirmed = await showConfirmation({
      title: `Delete ${selectedIds.length} Manual Review Articles`,
      description: `Move ${selectedIds.length} selected article(s) out of Manual Review and into the archive? Shared links will remain preserved.`,
      variant: 'destructive',
      confirmText: 'Delete Selected',
      cancelText: 'Cancel'
    });

    if (!confirmed) return;

    setActionLoading('delete-selected-manual-review');

    try {
      const results = await Promise.all(
        selectedIds.map(async (articleId) => {
          const response = await fetch(`${getApiUrl()}/api/articles/${articleId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
          });

          return {
            articleId,
            ok: response.ok
          };
        })
      );

      const deletedIds = new Set(
        results.filter(result => result.ok).map(result => result.articleId)
      );
      const failedCount = results.length - deletedIds.size;

      setManualReviewArticles(prev =>
        prev.filter(article => !deletedIds.has(article.id))
      );
      setSelectedManualReviewArticles(new Set());

      await Promise.all([
        fetchManualReviewArticles(),
        fetchArchivedArticles(),
        fetchArticleStats()
      ]);

      if (failedCount === 0) {
        toast({
          title: "✅ Articles Deleted",
          description: `${deletedIds.size} selected article(s) moved to the archive`
        });
      } else {
        toast({
          title: "⚠️ Bulk Delete Partly Completed",
          description: `${deletedIds.size} deleted, ${failedCount} failed`,
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "❌ Bulk Delete Failed",
        description: error.message || "Failed to delete selected articles",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteSubscriber = async (email) => {
    if (!window.confirm(`Remove subscriber ${email}?`)) return;
    
    setActionLoading(`delete-sub-${email}`);
    try {
      const response = await fetch(`${getApiUrl()}/api/admin/subscribers/${encodeURIComponent(email)}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        toast({
          title: "Subscriber Removed",
          description: `${email} has been unsubscribed`
        });
        setSubscribers(subscribers.filter(s => s.email !== email));
        fetchAllData();
      } else {
        throw new Error('Delete failed');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove subscriber",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', { 
      day: 'numeric', 
      month: 'short', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Show loading state while checking authentication
  if (authChecking) {
    return (
      <div className="min-h-screen bg-muted dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-muted-foreground dark:text-gray-400">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Show login form if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-muted dark:bg-gray-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md dark:bg-gray-800 dark:border-gray-700">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center">
              <Lock className="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
            </div>
            <CardTitle className="text-2xl dark:text-white">Admin Login</CardTitle>
            <CardDescription className="dark:text-gray-400">
              Enter your credentials to access the admin dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-muted-foreground dark:text-gray-300 mb-1">
                  Username / Email
                </label>
                <Input
                  type="text"
                  name="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username (e.g. admin)"
                  required
                  autoComplete="username"
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck="false"
                  className="w-full text-base dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  data-testid="admin-login-username"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-muted-foreground dark:text-gray-300 mb-1">
                  Password
                </label>
                <Input
                  type="password"
                  name="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  autoComplete="current-password"
                  className="w-full text-base dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  data-testid="admin-login-password"
                />
              </div>
              <Button 
                type="submit" 
                className="w-full bg-emerald-600 hover:bg-emerald-700 h-12 text-base"
                disabled={loginLoading}
                data-testid="admin-login-submit"
              >
                {loginLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Logging in...
                  </>
                ) : (
                  <>
                    <Lock className="mr-2 h-4 w-4" />
                    Login
                  </>
                )}
              </Button>
            </form>
            <div className="mt-4 text-center">
              <Button variant="ghost" onClick={onBack} className="text-muted-foreground">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Site
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-muted dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-muted-foreground dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <HelmetProvider>
    <div className="min-h-screen bg-muted dark:bg-gray-900">
      {/* SEO - Prevent indexing of admin pages */}
      <Helmet>
        <title>Admin Dashboard | Cheshire Today</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      
      {/* Header */}
      <div className="bg-card dark:bg-gray-800 border-b dark:border-gray-700 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-4 flex-wrap">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={onBack}
                className="flex items-center gap-2"
                data-testid="admin-back-button"
              >
                <ArrowLeft className="h-4 w-4" />
                <span className="hidden sm:inline">Back to Site</span>
              </Button>
              <div className="h-6 w-px bg-gray-300 hidden sm:block" />
              <h1 className="text-xl sm:text-2xl font-bold text-foreground dark:text-white flex items-center gap-2">
                <BarChart3 className="h-5 w-5 sm:h-6 sm:w-6 text-emerald-600" />
                <span className="hidden sm:inline">Admin Dashboard</span>
                <span className="sm:hidden">Admin</span>
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => fetchAllData()}
                className="flex items-center gap-2"
                data-testid="admin-refresh-button"
              >
                <RefreshCw className="h-4 w-4" />
                <span className="hidden sm:inline">Refresh</span>
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleLogout}
                className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                data-testid="admin-logout-button"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {/* Loading or Empty State Warning */}
        {!loading && stats && stats.articles?.total === 0 && articles.length === 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
            <div className="flex-1">
              <p className="font-medium text-yellow-800">Dashboard data may not have loaded correctly</p>
              <p className="text-sm text-yellow-700">Click the Refresh button above to reload data</p>
            </div>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => fetchAllData()}
              className="border-yellow-400 text-yellow-700 hover:bg-yellow-100"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        )}
        
        {/* Stats Cards - Using memoized components for speed */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard 
            title="Total Articles" 
            value={stats?.articles?.total || 0} 
            icon={FileText} 
            color="bg-emerald-100 text-emerald-600" 
          />
          <StatCard 
            title="Subscribers" 
            value={stats?.subscribers?.total || 0} 
            icon={Users} 
            color="bg-blue-100 text-blue-600" 
          />
          <StatCard 
            title="Categories" 
            value={Object.keys(stats?.articles?.by_category || {}).length} 
            icon={Newspaper} 
            color="bg-purple-100 text-purple-600" 
          />
          <Card className="dark:bg-gray-800 dark:border-gray-700">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm font-medium text-muted-foreground dark:text-gray-400">Last Article</p>
                  <p className="text-xs sm:text-sm font-medium text-foreground dark:text-white">
                    {formatDate(stats?.latest_article_date).split(',')[0]}
                  </p>
                </div>
                <div className="h-10 w-10 sm:h-12 sm:w-12 bg-orange-100 rounded-full flex items-center justify-center">
                  <Clock className="h-5 w-5 sm:h-6 sm:w-6 text-orange-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
            <CardDescription>Quick actions for content management</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-9 gap-2">
              {/* Add Article Button */}
              <Button 
                onClick={handleAddArticle}
                className="bg-blue-600 hover:bg-blue-700 h-12 flex items-center justify-center gap-2"
                data-testid="add-article-button"
              >
                <PlusCircle className="h-4 w-4" />
                <span>Add Article</span>
              </Button>

              <Button 
                onClick={handleGenerateArticles}
                disabled={actionLoading === 'generate'}
                className="bg-emerald-600 hover:bg-emerald-700 h-12 flex items-center justify-center gap-2"
                data-testid="generate-articles-button"
              >
                {actionLoading === 'generate' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <TrendingUp className="h-4 w-4" />
                )}
                <span>Generate</span>
              </Button>
              
              <Button 
                onClick={handleSendDigest}
                disabled={actionLoading === 'digest'}
                className="bg-orange-600 hover:bg-orange-700 h-12 flex items-center justify-center gap-2"
                data-testid="send-digest-button"
              >
                {actionLoading === 'digest' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Mail className="h-4 w-4" />
                )}
                <span>Daily Brief</span>
              </Button>
              
              <Button 
                onClick={handlePostToFacebook}
                disabled={actionLoading === 'facebook'}
                className="bg-blue-700 hover:bg-blue-800 h-12 flex items-center justify-center gap-2"
                data-testid="post-to-facebook-button"
              >
                {actionLoading === 'facebook' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Facebook className="h-4 w-4" />
                )}
                <span>Facebook</span>
              </Button>
              
              <Button 
                onClick={handlePostToTwitter}
                disabled={actionLoading === 'twitter'}
                className="bg-sky-500 hover:bg-sky-600 h-12 flex items-center justify-center gap-2"
                data-testid="post-to-twitter-button"
              >
                {actionLoading === 'twitter' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Twitter className="h-4 w-4" />
                )}
                <span>Twitter</span>
              </Button>
              
              <Button 
                onClick={handleCleanupDuplicates}
                disabled={actionLoading === 'cleanup'}
                className="bg-red-600 hover:bg-red-700 h-12 flex items-center justify-center gap-2"
                data-testid="cleanup-duplicates-button"
              >
                {actionLoading === 'cleanup' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                <span>Cleanup</span>
              </Button>
              
              <Button 
                onClick={handleFixMismatchedContent}
                disabled={actionLoading === 'fix-content'}
                className="bg-orange-500 hover:bg-orange-600 h-12 flex items-center justify-center gap-2"
                data-testid="fix-content-button"
              >
                {actionLoading === 'fix-content' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4" />
                )}
                <span>Fix Content</span>
              </Button>
              
              <Button 
                onClick={handleRemoveProductArticles}
                disabled={actionLoading === 'remove-products'}
                className="bg-purple-600 hover:bg-purple-700 h-12 flex items-center justify-center gap-2"
                data-testid="remove-products-button"
              >
                {actionLoading === 'remove-products' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ShoppingBag className="h-4 w-4" />
                )}
                <span>No Products</span>
              </Button>
              
              <Button 
                onClick={handleSyncRSS}
                disabled={actionLoading === 'sync-rss'}
                className="bg-cyan-600 hover:bg-cyan-700 h-12 flex items-center justify-center gap-2"
                data-testid="sync-rss-button"
              >
                {actionLoading === 'sync-rss' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                <span>Sync RSS</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Tabs - Improved Navigation */}
        <div className="bg-card dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 mb-4 p-1">
          <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
            <Button 
              variant={activeTab === 'overview' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('overview')}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'overview' ? 'bg-emerald-600 hover:bg-emerald-700 text-white' : 'text-foreground dark:text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-overview"
            >
              <BarChart3 className="h-4 w-4" />
              <span className="hidden xs:inline">Overview</span>
              <span className="xs:hidden">Home</span>
            </Button>
            <Button 
              variant={activeTab === 'articles' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('articles')}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'articles' ? 'bg-emerald-600 hover:bg-emerald-700 text-white' : 'text-foreground dark:text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-articles"
            >
              <FileText className="h-4 w-4" />
              <span>Articles</span>
              <Badge variant="secondary" className="ml-1 text-xs hidden sm:inline-flex">{articles.length}</Badge>
            </Button>
            <Button 
              variant={activeTab === 'subscribers' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('subscribers')}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'subscribers' ? 'bg-emerald-600 hover:bg-emerald-700 text-white' : 'text-foreground dark:text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-subscribers"
            >
              <Users className="h-4 w-4" />
              <span className="hidden sm:inline">Subscribers</span>
              <span className="sm:hidden">Subs</span>
              <Badge variant="secondary" className="ml-1 text-xs hidden sm:inline-flex">{subscribers.length}</Badge>
            </Button>
            <Button 
              variant={activeTab === 'newsimport' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('newsimport')}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'newsimport' ? '!bg-blue-600 hover:!bg-blue-700 !text-white' : '!text-foreground dark:!text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-newsimport"
            >
              <MapPin className="h-4 w-4" />
              <span className="hidden sm:inline">News Import</span>
              <span className="sm:hidden">Import</span>
            </Button>
            <Button 
              variant={activeTab === 'facebook' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('facebook')}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'facebook' ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'text-foreground dark:text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-facebook"
            >
              <Facebook className="h-4 w-4" />
              <span className="hidden sm:inline">Facebook</span>
              <span className="sm:hidden">FB</span>
            </Button>
            <Button 
              variant={activeTab === 'digest' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('digest')}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'digest' ? 'bg-orange-600 hover:bg-orange-700 text-white' : 'text-foreground dark:text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-digest"
            >
              <Mail className="h-4 w-4" />
              <span>Digest</span>
            </Button>
            <Button 
              variant={activeTab === 'analytics' ? 'default' : 'ghost'}
              onClick={() => {
                setActiveTab('analytics');
                if (!fbAnalytics) fetchFacebookAnalytics();
              }}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'analytics' ? 'bg-purple-600 hover:bg-purple-700 text-white' : 'text-foreground dark:text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-analytics"
            >
              <TrendingUp className="h-4 w-4" />
              <span className="hidden sm:inline">Analytics</span>
              <span className="sm:hidden">Stats</span>
            </Button>
            <Button 
              variant={activeTab === 'archive' ? 'default' : 'ghost'}
              onClick={() => {
                setActiveTab('archive');
                // Always fetch fresh archive data when clicking the tab
                fetchArchivedArticles();
                fetchManualReviewArticles();
                fetchArticleStats();
              }}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'archive' ? 'bg-gray-700 hover:bg-gray-800 text-white' : 'text-foreground dark:text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-archive"
            >
              <Archive className="h-4 w-4" />
              <span>Archive</span>
            </Button>
            <Button 
              variant={activeTab === 'affiliates' ? 'default' : 'ghost'}
              onClick={() => {
                setActiveTab('affiliates');
                if (affiliateProducts.length === 0) fetchAffiliateProducts();
              }}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'affiliates' ? 'bg-amber-600 hover:bg-amber-700 text-white' : 'text-foreground dark:text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-affiliates"
            >
              <ShoppingBag className="h-4 w-4" />
              <span className="hidden sm:inline">Affiliates</span>
              <span className="sm:hidden">Affil</span>
            </Button>
            <Button 
              variant={activeTab === 'advertising' ? 'default' : 'ghost'}
              onClick={() => {
                setActiveTab('advertising');
                fetchAdvertiserLeads();
                fetchSponsoredPlacements();
              }}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'advertising' ? 'bg-amber-600 hover:bg-amber-700 text-white' : 'text-foreground dark:text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-advertising"
            >
              <PoundSterling className="h-4 w-4" />
              <span className="hidden sm:inline">Advertising</span>
              <span className="sm:hidden">Ads</span>
              <Badge variant="secondary" className="ml-1 text-xs hidden sm:inline-flex">{advertiserLeads.length}</Badge>
            </Button>
            <Button 
              variant="ghost"
              onClick={() => setActiveTab('jobs')}
              size="sm"
              className={`flex items-center gap-2 min-w-fit ${activeTab === 'jobs' ? '!bg-emerald-600 hover:!bg-emerald-700 !text-white' : '!text-foreground dark:!text-gray-100 font-medium hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              data-testid="tab-jobs"
            >
              <Briefcase className="h-4 w-4" />
              <span>Jobs</span>
            </Button>
          </div>
          {/* Mobile scroll hint */}
          <p className="text-xs text-gray-400 text-center mt-1 sm:hidden">← Swipe for more tabs →</p>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <Card>
            <CardHeader>
              <CardTitle>Articles by Category</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(stats?.articles?.by_category || {}).map(([category, count]) => (
                  <div key={category} className="bg-muted rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-foreground">{count}</p>
                    <p className="text-sm text-muted-foreground">{category}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === 'articles' && (
          <div className="space-y-4">
            {/* Sub-tabs and Search Bar */}
            <Card>
              <CardContent className="pt-4">
                <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                  {/* Sub-tabs */}
                  <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
                    {[
                      { id: 'all', label: 'All', count: articles.length },
                      { id: 'local', label: 'Local News', count: articles.filter(a => a.category === 'Local News').length },
                      { id: 'uk', label: 'UK News', count: articles.filter(a => a.category === 'UK News').length },
                      { id: 'sports', label: 'Sports', count: articles.filter(a => a.category === 'Sports').length },
                    ].map(tab => (
                      <button
                        key={tab.id}
                        onClick={() => setArticleSubTab(tab.id)}
                        className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                          articleSubTab === tab.id 
                            ? 'bg-card dark:bg-gray-700 text-emerald-600 shadow-sm' 
                            : 'text-muted-foreground dark:text-gray-400 hover:text-foreground dark:hover:text-white'
                        }`}
                      >
                        {tab.label} ({tab.count})
                      </button>
                    ))}
                  </div>
                  
                  {/* Search and Bulk Actions */}
                  <div className="flex gap-2 w-full md:w-auto">
                    <div className="relative flex-1 md:w-64">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="Search articles..."
                        value={articleSearch}
                        onChange={(e) => setArticleSearch(e.target.value)}
                        className="pl-9 bg-card dark:bg-gray-700"
                      />
                    </div>
                    {selectedArticles.size > 0 && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          const confirmed = await showConfirmation({
                            title: `Archive ${selectedArticles.size} Articles`,
                            description: `Are you sure you want to archive ${selectedArticles.size} selected article(s)? They can be restored from the Archive tab.`,
                            variant: 'warning',
                            confirmText: 'Archive Selected',
                            cancelText: 'Cancel'
                          });
                          if (confirmed) {
                            // Bulk archive logic
                            toast({ title: "Bulk Archive", description: `Archiving ${selectedArticles.size} articles...` });
                            setSelectedArticles(new Set());
                          }
                        }}
                        className="text-amber-600 border-amber-300"
                      >
                        <Archive className="h-4 w-4 mr-1" />
                        Archive ({selectedArticles.size})
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Articles List */}
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Articles</CardTitle>
                    <CardDescription>Manage your news articles</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      if (selectedArticles.size === articles.length) {
                        setSelectedArticles(new Set());
                      } else {
                        setSelectedArticles(new Set(articles.map(a => a.id)));
                      }
                    }}
                    className="text-muted-foreground"
                  >
                    {selectedArticles.size === articles.length ? (
                      <><Square className="h-4 w-4 mr-1" /> Deselect All</>
                    ) : (
                      <><CheckSquare className="h-4 w-4 mr-1" /> Select All</>
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {articles
                    .filter(article => {
                      // Filter by sub-tab
                      if (articleSubTab === 'local' && article.category !== 'Local News') return false;
                      if (articleSubTab === 'uk' && article.category !== 'UK News') return false;
                      if (articleSubTab === 'sports' && article.category !== 'Sports') return false;
                      return true;
                    })
                    .map((article) => (
                    <div 
                      key={article._id || article.id} 
                      className={`flex items-center gap-4 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors border ${
                        selectedArticles.has(article.id) 
                          ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-300 dark:border-emerald-700' 
                          : 'bg-muted dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                      }`}
                      data-testid={`article-row-${article.id}`}
                    >
                      {/* Checkbox */}
                      <button
                        onClick={() => {
                          const newSelected = new Set(selectedArticles);
                          if (newSelected.has(article.id)) {
                            newSelected.delete(article.id);
                          } else {
                            newSelected.add(article.id);
                          }
                          setSelectedArticles(newSelected);
                        }}
                        className="flex-shrink-0"
                      >
                        {selectedArticles.has(article.id) ? (
                          <CheckSquare className="h-5 w-5 text-emerald-600" />
                        ) : (
                          <Square className="h-5 w-5 text-gray-400" />
                        )}
                      </button>
                      
                      <img 
                        src={article.image} 
                        alt={article.title}
                        className="w-16 h-16 object-cover rounded-lg flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-foreground dark:text-white truncate">{article.title}</h4>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          <Badge variant="secondary" className="text-xs">
                            {article.category}
                          </Badge>
                          <span className="text-xs text-muted-foreground dark:text-gray-400">
                            {formatDate(article.publishedDate)}
                          </span>
                          {article.ai_review_risk_level && (
                            <Badge
                              variant="outline"
                              className={`text-xs ${
                                article.ai_review_risk_level === 'high'
                                  ? 'border-red-300 text-red-700 bg-red-50'
                                  : article.ai_review_risk_level === 'medium'
                                    ? 'border-amber-300 text-amber-700 bg-amber-50'
                                    : 'border-emerald-300 text-emerald-700 bg-emerald-50'
                              }`}
                            >
                              AI: {article.ai_review_risk_level} · {article.ai_review_recommended_action || 'reviewed'}
                            </Badge>
                          )}
                          {article.view_count > 0 && (
                            <span className="text-xs text-muted-foreground dark:text-gray-400 flex items-center gap-1">
                              <Eye className="h-3 w-3" /> {article.view_count}
                            </span>
                          )}
                        </div>
                        {article.ai_review_result?.editor_notes && (
                          <p className="text-xs text-muted-foreground dark:text-gray-400 mt-1 line-clamp-2">
                            ChatGPT: {article.ai_review_result.editor_notes}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditArticle(article)}
                          className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 border-blue-200"
                          data-testid={`edit-article-${article.id}`}
                          title="Edit article"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleAIReviewArticle(article._id || article.id)}
                          disabled={actionLoading === `ai-review-${article.id}`}
                          className="text-purple-600 hover:text-purple-700 hover:bg-purple-50 border-purple-200"
                          title="Check with ChatGPT"
                        >
                          {actionLoading === `ai-review-${article.id}` ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <AlertCircle className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleForceLiveArticle(article.id)}
                          disabled={actionLoading === `force-${article.id}`}
                          className="text-green-600 hover:text-green-700 hover:bg-green-50 border-green-200"
                          title="Force show on homepage"
                        >
                          {actionLoading === `force-${article.id}` ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Zap className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async () => {
                            const confirmed = await showConfirmation({
                              title: 'Send Article to Manual Review',
                              description: `Move "${article.title}" out of the public site and into Manual Review for editing?`,
                              variant: 'warning',
                              confirmText: 'Send to Manual Review',
                              cancelText: 'Cancel'
                            });
                            if (confirmed) {
                              handleMoveToManualReview(
                                article.mongo_id || article._id || article.id
                              );
                            }
                          }}
                          disabled={actionLoading === `manual-review-${article.id}`}
                          className="text-amber-600 hover:text-amber-700 hover:bg-amber-50 border-amber-200"
                          title="Send article to Manual Review"
                          data-testid={`manual-review-article-${article.id}`}
                        >
                          {actionLoading === `manual-review-${article.id}` ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <AlertCircle className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async () => {
                            const confirmed = await showConfirmation({
                              title: 'Delete Article',
                              description: `Are you sure you want to permanently delete "${article.title}"? This action cannot be undone.`,
                              variant: 'destructive',
                              confirmText: 'Delete Permanently',
                              cancelText: 'Cancel'
                            });
                            if (confirmed) {
                              handleDeleteArticle(article.id);
                            }
                          }}
                          disabled={actionLoading === `delete-article-${article.id}`}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                          title="Delete article"
                          data-testid={`delete-article-${article.id}`}
                        >
                          {actionLoading === `delete-article-${article.id}` ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                {hasMoreArticles && articles.length >= 50 && (
                  <div className="pt-4 text-center">
                    <Button 
                      variant="outline" 
                      onClick={loadMoreArticles}
                      className="w-full"
                    >
                      <ChevronDown className="h-4 w-4 mr-2" />
                      Load More Articles
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
          </div>
        )}

        {activeTab === 'subscribers' && (
          <Card>
            <CardHeader>
              <CardTitle>Email Subscribers</CardTitle>
              <CardDescription>Manage newsletter subscribers</CardDescription>
            </CardHeader>
            <CardContent>
              {subscribers.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Mail className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p>No subscribers yet</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {subscribers.map((subscriber) => (
                    <div 
                      key={subscriber.email} 
                      className="flex items-center justify-between p-3 bg-muted rounded-lg"
                      data-testid={`subscriber-row-${subscriber.email}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Mail className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-foreground">{subscriber.email}</p>
                          <p className="text-xs text-muted-foreground">
                            Subscribed: {formatDate(subscriber.subscribed_at)}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteSubscriber(subscriber.email)}
                        disabled={actionLoading === `delete-sub-${subscriber.email}`}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        data-testid={`delete-subscriber-${subscriber.email}`}
                      >
                        {actionLoading === `delete-sub-${subscriber.email}` ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === 'facebook' && (
          <div className="space-y-6">

            {/* Smart Recommendations */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-purple-600" />
                      Smart Recommendations
                    </CardTitle>
                    <CardDescription>
                      AI-prioritized articles based on engagement potential
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchSmartArticles}
                    disabled={smartLoading}
                  >
                    {smartLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {smartLoading && smartArticles.length === 0 ? (
                  <div className="text-center py-6">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-purple-600" />
                    <p className="mt-2 text-muted-foreground">Analyzing articles...</p>
                  </div>
                ) : smartArticles.length === 0 ? (
                  <div className="text-center py-6 text-muted-foreground">
                    <TrendingUp className="h-10 w-10 mx-auto mb-2 text-gray-300" />
                    <p>Click refresh to get AI recommendations</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[350px] overflow-y-auto">
                    {smartArticles.slice(0, 5).map((article, index) => (
                      <div 
                        key={article._id || article.id}
                        className={`flex items-center gap-3 p-3 rounded-lg border ${
                          index === 0 ? 'bg-purple-50 border-purple-200' : 'bg-muted border-gray-100'
                        }`}
                      >
                        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                          index === 0 ? 'bg-purple-600 text-white' : 'bg-gray-200 text-muted-foreground'
                        }`}>
                          {article.score}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-foreground text-sm truncate">{article.title}</p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {article.reasons?.slice(0, 3).map((reason, i) => (
                              <span key={i} className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                                {reason}
                              </span>
                            ))}
                          </div>
                        </div>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handlePostSingleArticle(article.id)}
                          disabled={actionLoading === `post-${article.id}`}
                          className="bg-purple-600 hover:bg-purple-700"
                        >
                          {actionLoading === `post-${article.id}` ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Facebook className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Select Article to Post */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Share2 className="h-5 w-5 text-blue-600" />
                  Post to Facebook
                </CardTitle>
                <CardDescription>
                  Select an article to post now
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[400px] overflow-y-auto">
                  {schedulableArticles.map((article) => (
                    <div 
                      key={article._id} 
                      className="flex items-center gap-3 p-3 bg-muted rounded-lg hover:bg-gray-100 transition-colors"
                      data-testid={`fb-article-${article._id}`}
                    >
                      <img 
                        src={article.image} 
                        alt=""
                        className="w-14 h-14 object-cover rounded flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-foreground text-sm truncate">{article.title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="secondary" className="text-xs">
                            {article.category}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {article.source}
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-2 flex-shrink-0">
                        <Button
                          variant="default"
                          size="default"
                          onClick={() => handlePostSingleArticle(article._id)}
                          disabled={actionLoading === `post-${article._id}`}
                          className="bg-blue-600 hover:bg-blue-700 min-w-[44px] min-h-[44px] touch-manipulation"
                          data-testid={`post-now-${article._id}`}
                        >
                          {actionLoading === `post-${article._id}` ? (
                            <Loader2 className="h-5 w-5 animate-spin" />
                          ) : (
                            <Facebook className="h-5 w-5" />
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Digest Tab Content */}
        {activeTab === 'digest' && (
          <div className="space-y-6">
            {/* New Email Strategy Overview */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5 text-blue-600" />
                  Email Strategy (January 2026)
                </CardTitle>
                <CardDescription>
                  Quality over quantity - Daily Brief, Weekly Roundup, Breaking News Alerts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center border-2 border-blue-200 dark:border-blue-800">
                    <div className="h-10 w-10 bg-blue-100 dark:bg-blue-800 rounded-full flex items-center justify-center mx-auto mb-2">
                      <Sun className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <p className="font-bold text-blue-700 dark:text-blue-300">Morning</p>
                    <p className="text-sm text-blue-600 dark:text-blue-400">The Daily Brief</p>
                    <p className="text-xs text-muted-foreground dark:text-gray-400 mt-1">Every morning</p>
                  </div>
                  <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 text-center border-2 border-purple-200 dark:border-purple-800">
                    <div className="h-10 w-10 bg-purple-100 dark:bg-purple-800 rounded-full flex items-center justify-center mx-auto mb-2">
                      <CalendarIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <p className="font-bold text-purple-700 dark:text-purple-300">Sunday morning</p>
                    <p className="text-sm text-purple-600 dark:text-purple-400">Weekly Roundup</p>
                    <p className="text-xs text-muted-foreground dark:text-gray-400 mt-1">Every Sunday</p>
                  </div>
                  <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-center border-2 border-red-200 dark:border-red-800">
                    <div className="h-10 w-10 bg-red-100 dark:bg-red-800 rounded-full flex items-center justify-center mx-auto mb-2">
                      <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
                    </div>
                    <p className="font-bold text-red-700 dark:text-red-300">Manual</p>
                    <p className="text-sm text-red-600 dark:text-red-400">Breaking News</p>
                    <p className="text-xs text-muted-foreground dark:text-gray-400 mt-1">High priority only</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Test Digest Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Send className="h-5 w-5 text-amber-600" />
                  Test Daily Brief
                </CardTitle>
                <CardDescription>
                  Send a test email to yourself before sending to all subscribers
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                  <div className="flex gap-2">
                    <Input
                      type="text"
                      placeholder="your@email.com"
                      defaultValue="news@cheshiretoday.co.uk"
                      className="flex-1 bg-card dark:bg-gray-700 text-foreground dark:text-white"
                      id="test-digest-email"
                      data-testid="test-digest-email-input"
                    />
                    <Button
                      onClick={async () => {
                        const testEmail = document.getElementById('test-digest-email').value;
                        if (!testEmail) {
                          toast({ title: "Enter email", description: "Please enter an email address", variant: "destructive" });
                          return;
                        }
                        setActionLoading('test-digest');
                        try {
                          const res = await fetch(`${getApiUrl()}/api/send-digest-test?test_email=${encodeURIComponent(testEmail)}`, {
                            method: 'POST',
                            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
                          });
                          const data = await res.json();
                          if (data.success) {
                            toast({
                              title: "✅ Test Sent",
                              description: `Sent to ${testEmail}. Check your inbox!`
                            });
                          } else {
                            toast({ title: "❌ Failed", description: data.detail || "Failed to send", variant: "destructive" });
                          }
                        } catch (error) {
                          toast({ title: "❌ Error", description: error.message, variant: "destructive" });
                        } finally {
                          setActionLoading(null);
                        }
                      }}
                      disabled={actionLoading === 'test-digest'}
                      className="bg-amber-600 hover:bg-amber-700"
                      data-testid="send-test-digest-button"
                    >
                      {actionLoading === 'test-digest' ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Send className="h-4 w-4 mr-2" />
                          Send Test
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Breaking News Alert */}
            <Card className="border-2 border-red-200 dark:border-red-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-700 dark:text-red-400">
                  <AlertTriangle className="h-5 w-5" />
                  Send Breaking News Alert
                </CardTitle>
                <CardDescription>
                  Send urgent news alert to all Breaking News subscribers. Use sparingly!
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1 text-muted-foreground dark:text-gray-300">Headline</label>
                  <Input
                    id="breaking-headline"
                    placeholder="Major incident headline..."
                    className="bg-card dark:bg-gray-700 text-foreground dark:text-white"
                    data-testid="breaking-headline-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-muted-foreground dark:text-gray-300">What We Know (one point per line)</label>
                  <textarea
                    id="breaking-bullets"
                    rows={3}
                    placeholder="Police have confirmed an incident at...&#10;Road closures are in place on...&#10;Emergency services are on scene..."
                    className="w-full px-3 py-2 border rounded-md bg-card dark:bg-gray-700 text-foreground dark:text-white"
                    data-testid="breaking-bullets-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-muted-foreground dark:text-gray-300">Live Updates URL (optional)</label>
                  <Input
                    id="breaking-url"
                    placeholder="https://cheshiretoday.co.uk/article/..."
                    className="bg-card dark:bg-gray-700 text-foreground dark:text-white"
                    data-testid="breaking-url-input"
                  />
                </div>
                <Button
                  onClick={handleSendBreakingNews}
                  disabled={actionLoading === 'breaking-news'}
                  variant="destructive"
                  className="w-full"
                  data-testid="send-breaking-news-button"
                >
                  {actionLoading === 'breaking-news' ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 mr-2" />
                  )}
                  Send Breaking News Alert
                </Button>
              </CardContent>
            </Card>

            {/* Migration Announcement */}
            <Card className="border-2 border-emerald-200 dark:border-emerald-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                  <Bell className="h-5 w-5" />
                  Send Migration Announcement
                </CardTitle>
                <CardDescription>
                  One-time email to announce the new email strategy to all existing subscribers
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4 mb-4">
                  <p className="text-sm text-emerald-700 dark:text-emerald-300 mb-2">
                    <strong>Subject:</strong> We&apos;ve made some changes to Cheshire Today 📩
                  </p>
                  <p className="text-sm text-muted-foreground dark:text-gray-400">
                    This will inform all subscribers about the Daily Brief, Weekly Roundup, 
                    and Breaking News options. All subscribers will be automatically migrated to The Daily Brief.
                  </p>
                </div>
                <Button
                  onClick={handleSendAnnouncement}
                  disabled={actionLoading === 'announcement'}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  data-testid="send-announcement-button"
                >
                  {actionLoading === 'announcement' ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Bell className="h-4 w-4 mr-2" />
                  )}
                  Send Migration Announcement to All Subscribers
                </Button>
              </CardContent>
            </Card>

            {/* Site Update (Part 1) */}
            <Card className="border-2 border-sky-200 dark:border-sky-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sky-700 dark:text-sky-400">
                  <Mail className="h-5 w-5" />
                  Site Update (Part 1)
                </CardTitle>
                <CardDescription>
                  Broadcast update email (intended for “Day 3” message)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={handleSendSiteUpdatePart1}
                  disabled={actionLoading === 'site-update-part1'}
                  className="w-full bg-sky-600 hover:bg-sky-700"
                >
                  {actionLoading === 'site-update-part1' ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Mail className="h-4 w-4 mr-2" />
                  )}
                  Send Site Update (Part 1) to All Subscribers
                </Button>
              </CardContent>
            </Card>

            {/* Site Update (Part 2) */}
            <Card className="border-2 border-violet-200 dark:border-violet-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-violet-700 dark:text-violet-400">
                  <Mail className="h-5 w-5" />
                  Site Update (Part 2)
                </CardTitle>
                <CardDescription>
                  Broadcast update email (intended for “Day 7” message)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={handleSendSiteUpdatePart2}
                  disabled={actionLoading === 'site-update-part2'}
                  className="w-full bg-violet-600 hover:bg-violet-700"
                >
                  {actionLoading === 'site-update-part2' ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Mail className="h-4 w-4 mr-2" />
                  )}
                  Send Site Update (Part 2) to All Subscribers
                </Button>
              </CardContent>
            </Card>


            
            {/* Manual Campaign Email */}
            <Card className="border-2 border-blue-200 dark:border-blue-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-700 dark:text-blue-400">
                  <Mail className="h-5 w-5" />
                  Manual Campaign Email
                </CardTitle>
                <CardDescription>
                  Create and send a custom announcement. Supports placeholders: __PREFS_URL__ and __UNSUB_URL__.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-sm">Subject</Label>
                  <Input
                    value={campaignSubject}
                    onChange={(e) => setCampaignSubject(e.target.value)}
                    className="bg-card dark:bg-gray-700 text-foreground dark:text-white"
                    data-testid="campaign-subject-input"
                    placeholder="Subject line..."
                  />
                </div>

                <div>
                  <Label className="text-sm">Test email (for Send Test)</Label>
                  <Input
                    value={campaignTestEmail}
                    onChange={(e) => setCampaignTestEmail(e.target.value)}
                    className="bg-card dark:bg-gray-700 text-foreground dark:text-white"
                    data-testid="campaign-test-email-input"
                    placeholder="you@domain.com"
                  />
                </div>

                <div>
                  <Label className="text-sm">HTML content</Label>
                  <Textarea
                    value={campaignHtml}
                    onChange={(e) => setCampaignHtml(e.target.value)}
                    rows={8}
                    className="bg-card dark:bg-gray-700 text-foreground dark:text-white font-mono text-xs"
                    data-testid="campaign-html-input"
                    placeholder="<h1>Headline</h1><p>Body...</p>"
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    Tip: include __PREFS_URL__ and __UNSUB_URL__ somewhere near the footer.
                  </p>
                </div>

                <div>
                  <Label className="text-sm">Plain text fallback</Label>
                  <Textarea
                    value={campaignText}
                    onChange={(e) => setCampaignText(e.target.value)}
                    rows={6}
                    className="bg-card dark:bg-gray-700 text-foreground dark:text-white text-xs"
                    data-testid="campaign-text-input"
                    placeholder="Plain text version..."
                  />
                </div>

                <div className="flex flex-col sm:flex-row gap-2">
                  <Button
                    onClick={handleCampaignSendTest}
                    disabled={actionLoading === 'campaign-test' || !campaignSubject}
                    className="flex-1 bg-blue-600 hover:bg-blue-700"
                    data-testid="campaign-send-test-button"
                  >
                    {actionLoading === 'campaign-test' ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4 mr-2" />
                    )}
                    Send Test
                  </Button>

                  <Button
                    onClick={handleCampaignSendAll}
                    disabled={actionLoading === 'campaign-all' || !campaignSubject}
                    variant="destructive"
                    className="flex-1"
                    data-testid="campaign-send-all-button"
                  >
                    {actionLoading === 'campaign-all' ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 mr-2" />
                    )}
                    Send to All
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Email Analytics Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-indigo-600" />
                      Email Analytics
                    </CardTitle>
                    <CardDescription>
                      Track open rates, click rates, and subscriber engagement
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchEmailAnalytics}
                    disabled={emailAnalyticsLoading}
                    data-testid="refresh-email-analytics"
                  >
                    {emailAnalyticsLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {emailAnalyticsLoading && !emailAnalytics ? (
                  <div className="text-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-indigo-600" />
                    <p className="mt-2 text-muted-foreground">Loading email analytics...</p>
                  </div>
                ) : emailAnalytics?.success ? (
                  <div className="space-y-6">
                    {/* Summary Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-indigo-700 dark:text-indigo-300">{emailAnalytics.summary?.total_emails_sent || 0}</p>
                        <p className="text-sm text-indigo-600 dark:text-indigo-400">Emails Sent</p>
                        <p className="text-xs text-muted-foreground">(last 30 days)</p>
                      </div>
                      <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-emerald-700 dark:text-emerald-300">{emailAnalytics.summary?.open_rate || 0}%</p>
                        <p className="text-sm text-emerald-600 dark:text-emerald-400">Open Rate</p>
                        <p className="text-xs text-muted-foreground">{emailAnalytics.summary?.unique_openers || 0} unique opens</p>
                      </div>
                      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-blue-700 dark:text-blue-300">{emailAnalytics.summary?.click_rate || 0}%</p>
                        <p className="text-sm text-blue-600 dark:text-blue-400">Click Rate</p>
                        <p className="text-xs text-muted-foreground">{emailAnalytics.summary?.unique_clickers || 0} clicked</p>
                      </div>
                      <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-amber-700 dark:text-amber-300">{emailAnalytics.summary?.click_to_open_rate || 0}%</p>
                        <p className="text-sm text-amber-600 dark:text-amber-400">Click-to-Open</p>
                        <p className="text-xs text-muted-foreground">engagement quality</p>
                      </div>
                    </div>

                    {/* Email Type Breakdown */}
                    {emailAnalytics.by_type && Object.keys(emailAnalytics.by_type).length > 0 && (
                      <div className="bg-muted dark:bg-gray-800 rounded-lg p-4">
                        <h4 className="font-semibold text-muted-foreground dark:text-gray-300 mb-3">Breakdown by Type</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {Object.entries(emailAnalytics.by_type).map(([type, stats]) => (
                            <div key={type} className="bg-card dark:bg-gray-700 rounded-lg p-3 border dark:border-gray-600">
                              <p className="font-medium text-gray-800 dark:text-gray-200">{type}</p>
                              <div className="flex justify-between text-sm mt-1">
                                <span className="text-muted-foreground">Sent:</span>
                                <span className="font-semibold">{stats.sent}</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Delivered:</span>
                                <span className="font-semibold text-green-600">{stats.success}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recent Sends */}
                    {emailAnalytics.recent_sends?.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-muted-foreground dark:text-gray-300 mb-3">Recent Email Campaigns</h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead className="bg-gray-100 dark:bg-gray-700">
                              <tr>
                                <th className="px-3 py-2 text-left">Date</th>
                                <th className="px-3 py-2 text-left">Type</th>
                                <th className="px-3 py-2 text-center">Sent</th>
                                <th className="px-3 py-2 text-center">Opens</th>
                                <th className="px-3 py-2 text-center">Clicks</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y dark:divide-gray-600">
                              {emailAnalytics.recent_sends.slice(0, 5).map((send, idx) => (
                                <tr key={idx} className="hover:bg-muted dark:hover:bg-gray-700">
                                  <td className="px-3 py-2 text-muted-foreground dark:text-gray-400">
                                    {send.sent_at ? new Date(send.sent_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) : 'N/A'}
                                  </td>
                                  <td className="px-3 py-2">
                                    <Badge variant={send.type === 'BreakingNews' ? 'destructive' : send.type === 'WeeklyRoundup' ? 'secondary' : 'default'}>
                                      {send.type}
                                    </Badge>
                                  </td>
                                  <td className="px-3 py-2 text-center">{send.subscribers}</td>
                                  <td className="px-3 py-2 text-center text-emerald-600 font-medium">{send.opens}</td>
                                  <td className="px-3 py-2 text-center text-blue-600 font-medium">{send.clicks}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    <div className="text-center text-xs text-muted-foreground pt-2">
                      <p>Note: Analytics tracking is automatically enabled for all new emails.</p>
                      <p>Open tracking uses a 1x1 invisible pixel. Click tracking redirects through our server.</p>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <BarChart3 className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p>Click refresh to load email analytics</p>
                    <p className="text-xs mt-2">Track open rates, click rates, and engagement metrics</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Analytics Tab Content */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            {/* Summary Stats */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-purple-600" />
                      Facebook Analytics
                    </CardTitle>
                    <CardDescription>
                      Track your Facebook post performance
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchFacebookAnalytics}
                    disabled={analyticsLoading}
                    data-testid="refresh-analytics"
                  >
                    {analyticsLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {analyticsLoading && !fbAnalytics ? (
                  <div className="text-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-purple-600" />
                    <p className="mt-2 text-muted-foreground">Loading analytics...</p>
                  </div>
                ) : fbAnalytics?.success ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-purple-50 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-purple-700">{fbAnalytics.summary?.total_posts_analyzed || 0}</p>
                      <p className="text-sm text-purple-600">Facebook Items</p>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-blue-700">{fbAnalytics.summary?.total_likes || 0}</p>
                      <p className="text-sm text-blue-600">Total Reactions</p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-green-700">{fbAnalytics.summary?.total_comments || 0}</p>
                      <p className="text-sm text-green-600">Total Comments</p>
                    </div>
                    <div className="bg-orange-50 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-orange-700">{fbAnalytics.summary?.total_shares || 0}</p>
                      <p className="text-sm text-orange-600">Total Shares</p>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <BarChart3 className="h-10 w-10 mx-auto mb-2 text-gray-300" />
                    <p>{fbAnalytics?.error || "Click refresh to load analytics"}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Insights */}
            {fbInsights?.success && fbInsights.insights?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-green-600" />
                    Insights & Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {fbInsights.insights.map((insight, index) => (
                      <div 
                        key={index}
                        className="flex items-start gap-3 p-4 bg-muted rounded-lg"
                      >
                        <span className="text-2xl">{insight.icon}</span>
                        <div>
                          <h4 className="font-semibold text-foreground">{insight.title}</h4>
                          <p className="text-sm text-muted-foreground">{insight.description}</p>
                          {insight.recommendation && (
                            <p className="text-sm text-blue-600 mt-1">💡 {insight.recommendation}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Facebook Content Performance */}
            {fbAnalytics?.success && fbAnalytics.posts?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    Facebook Content Performance
                  </CardTitle>
                  <CardDescription>Feed posts, videos and Reels ranked by engagement score, with newest items shown first when scores are tied</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-[400px] overflow-y-auto">
                    {fbAnalytics.posts.slice(0, 10).map((post, index) => (
                      <div 
                        key={post.post_id}
                        className={`flex items-start gap-3 p-3 rounded-lg ${
                          index === 0 ? 'bg-yellow-50 border border-yellow-200' :
                          index < 3 ? 'bg-green-50' : 'bg-muted'
                        }`}
                      >
                        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                          index === 0 ? 'bg-yellow-400 text-yellow-900' :
                          index < 3 ? 'bg-green-400 text-white' : 'bg-gray-300 text-muted-foreground'
                        }`}>
                          {index + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <p className="font-medium text-foreground text-sm leading-snug">{post.title}</p>
                            {post.permalink_url && (
                              <a
                                href={post.permalink_url.startsWith('http') ? post.permalink_url : `https://www.facebook.com${post.permalink_url}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex-shrink-0 text-blue-600 hover:text-blue-800"
                                title="Open on Facebook"
                              >
                                <ExternalLink className="h-4 w-4" />
                              </a>
                            )}
                          </div>
                          <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-muted-foreground">
                            <Badge variant="outline" className="capitalize">
                              {(post.source_type || 'facebook').replace('_', ' ')}
                            </Badge>
                            <span>{formatDate(post.created_time)}</span>
                            <span>❤️ {post.reactions ?? post.likes ?? 0}</span>
                            <span>💬 {post.comments}</span>
                            <span>🔄 {post.shares}</span>
                            <span className="text-purple-600 font-medium">Score: {post.engagement_score}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Push Notifications Stats */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      🔔 Push Notifications
                    </CardTitle>
                    <CardDescription>
                      Send breaking news alerts to subscribers
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchPushStats}
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-blue-700">{pushStats?.active_subscriptions || 0}</p>
                    <p className="text-sm text-blue-600">Active Subscribers</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-green-700">{pushStats?.configured ? '✓' : '✗'}</p>
                    <p className="text-sm text-green-600">Push Configured</p>
                  </div>
                </div>
                
                {/* Milestone Progress */}
                {pushMilestones && pushMilestones.next_milestone && (
                  <div className="bg-purple-50 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-purple-700">Next Milestone: {pushMilestones.next_milestone}</span>
                      <span className="text-xs text-purple-600">{pushMilestones.subscribers_to_next} more needed</span>
                    </div>
                    <div className="w-full bg-purple-200 rounded-full h-2">
                      <div 
                        className="bg-purple-600 h-2 rounded-full transition-all"
                        style={{ 
                          width: `${Math.min(100, (pushMilestones.current_subscribers / pushMilestones.next_milestone) * 100)}%` 
                        }}
                      />
                    </div>
                    <p className="text-xs text-purple-600 mt-1 text-center">
                      {pushMilestones.current_subscribers} / {pushMilestones.next_milestone} subscribers
                    </p>
                  </div>
                )}
                
                {/* Quick send breaking news */}
                <div className="border-t pt-4 mt-4">
                  <p className="text-sm font-medium text-muted-foreground mb-2">Send Breaking News Alert</p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Breaking news headline..."
                      className="flex-1 px-3 py-2 border rounded-lg text-sm"
                      id="breaking-news-input"
                    />
                    <Button
                      onClick={() => {
                        const input = document.getElementById('breaking-news-input');
                        if (input.value) {
                          sendBreakingNewsNotification(input.value);
                          input.value = '';
                        }
                      }}
                      className="bg-red-600 hover:bg-red-700"
                    >
                      Send Alert
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Archive Tab Content */}
        {activeTab === 'archive' && (
          <div className="space-y-6">
            {/* Article Stats Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-muted-foreground" />
                  Article Storage Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                {articleStats ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-green-50 rounded-lg p-4 text-center">
                        <p className="text-2xl font-bold text-green-700">{articleStats.active || 0}</p>
                        <p className="text-sm text-green-600">Active Articles</p>
                      </div>
                      <div className="bg-gray-100 rounded-lg p-4 text-center">
                        <p className="text-2xl font-bold text-muted-foreground">{articleStats.archived || 0}</p>
                        <p className="text-sm text-muted-foreground">Archived</p>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-4 text-center">
                        <p className="text-2xl font-bold text-blue-700">{articleStats.total || 0}</p>
                        <p className="text-sm text-blue-600">Total Stored</p>
                      </div>
                      <div className="bg-purple-50 rounded-lg p-4 text-center">
                        <p className="text-xl font-bold text-purple-700">∞</p>
                        <p className="text-sm text-purple-600">No Limit</p>
                      </div>
                    </div>
                    
                    {articleStats.oldest_date && (
                      <div className="bg-muted rounded-lg p-3">
                        <p className="text-sm text-muted-foreground">
                          <strong>Date Range:</strong> {articleStats.oldest_date?.substring(0, 10)} to {articleStats.newest_date?.substring(0, 10)}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {articleStats.storage_note}
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto text-gray-400" />
                    <p className="text-sm text-muted-foreground mt-2">Loading stats...</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Bulk Archive Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Archive className="h-5 w-5 text-muted-foreground" />
                  Bulk Archive
                </CardTitle>
                <CardDescription>
                  Archive old articles to keep your active list clean
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3">
                  <Button
                    variant="outline"
                    onClick={() => handleBulkArchive(7)}
                    disabled={actionLoading === 'bulk-archive'}
                  >
                    {actionLoading === 'bulk-archive' ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    Archive 7+ days old
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleBulkArchive(14)}
                    disabled={actionLoading === 'bulk-archive'}
                  >
                    Archive 14+ days old
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleBulkArchive(30)}
                    disabled={actionLoading === 'bulk-archive'}
                  >
                    Archive 30+ days old
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Manual Review Articles List */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Manual Review Articles</CardTitle>
                    <CardDescription>
                      {manualReviewArticles.length} live articles hidden from public feeds until reviewed
                    </CardDescription>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (
                          manualReviewArticles.length > 0 &&
                          selectedManualReviewArticles.size === manualReviewArticles.length
                        ) {
                          setSelectedManualReviewArticles(new Set());
                        } else {
                          setSelectedManualReviewArticles(
                            new Set(manualReviewArticles.map(article => article.id))
                          );
                        }
                      }}
                      disabled={manualReviewArticles.length === 0}
                    >
                      {manualReviewArticles.length > 0 &&
                      selectedManualReviewArticles.size === manualReviewArticles.length ? (
                        <>
                          <Square className="h-4 w-4 mr-1" />
                          Deselect All
                        </>
                      ) : (
                        <>
                          <CheckSquare className="h-4 w-4 mr-1" />
                          Select All
                        </>
                      )}
                    </Button>

                    {selectedManualReviewArticles.size > 0 && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDeleteSelectedManualReviewArticles}
                        disabled={actionLoading === 'delete-selected-manual-review'}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                      >
                        {actionLoading === 'delete-selected-manual-review' ? (
                          <Loader2 className="h-4 w-4 animate-spin mr-1" />
                        ) : (
                          <Trash2 className="h-4 w-4 mr-1" />
                        )}
                        Delete Selected ({selectedManualReviewArticles.size})
                      </Button>
                    )}

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={fetchManualReviewArticles}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {manualReviewArticles.length === 0 ? (
                  <div className="text-center py-6 text-muted-foreground">
                    <CheckCircle className="h-10 w-10 mx-auto mb-2 text-green-400" />
                    <p>No live manual-review articles</p>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[360px] overflow-y-auto">
                    {manualReviewArticles.map((article) => (
                      <div
                        key={article.id}
                        className={`flex items-start gap-3 p-3 border rounded-lg ${
                          selectedManualReviewArticles.has(article.id)
                            ? 'bg-red-50 dark:bg-red-950/20 border-red-300 dark:border-red-800'
                            : 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800'
                        }`}
                      >
                        <button
                          type="button"
                          onClick={() => {
                            const nextSelected = new Set(selectedManualReviewArticles);
                            if (nextSelected.has(article.id)) {
                              nextSelected.delete(article.id);
                            } else {
                              nextSelected.add(article.id);
                            }
                            setSelectedManualReviewArticles(nextSelected);
                          }}
                          className="flex-shrink-0 mt-1"
                          aria-label={
                            selectedManualReviewArticles.has(article.id)
                              ? `Deselect ${article.title}`
                              : `Select ${article.title}`
                          }
                        >
                          {selectedManualReviewArticles.has(article.id) ? (
                            <CheckSquare className="h-5 w-5 text-red-600" />
                          ) : (
                            <Square className="h-5 w-5 text-gray-400" />
                          )}
                        </button>

                        {article.image && (
                          <img
                            src={article.image}
                            alt=""
                            className="w-16 h-12 object-cover rounded"
                          />
                        )}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-foreground line-clamp-2">{article.title}</h4>
                          <div className="flex flex-wrap gap-2 mt-1 text-xs text-muted-foreground">
                            <span>{article.category || 'Uncategorised'}</span>
                            <span>•</span>
                            <span>{article.source || 'Unknown source'}</span>
                            {article.location && (
                              <>
                                <span>•</span>
                                <span>{article.location}</span>
                              </>
                            )}
                          </div>
                          {article.ai_review_risk_level && (
                            <Badge
                              variant="outline"
                              className={`text-xs mt-2 ${
                                article.ai_review_risk_level === 'high'
                                  ? 'border-red-300 text-red-700 bg-red-50'
                                  : article.ai_review_risk_level === 'medium'
                                    ? 'border-amber-300 text-amber-700 bg-amber-50'
                                    : 'border-emerald-300 text-emerald-700 bg-emerald-50'
                              }`}
                            >
                              AI: {article.ai_review_risk_level} · {article.ai_review_recommended_action || 'reviewed'}
                            </Badge>
                          )}
                          {article.ai_review_result?.editor_notes && (
                            <p className="text-xs text-muted-foreground dark:text-gray-400 mt-1 line-clamp-2">
                              ChatGPT: {article.ai_review_result.editor_notes}
                            </p>
                          )}
                          {article.manual_review_reason && (
                            <p className="text-xs text-amber-700 dark:text-amber-300 mt-2 line-clamp-2">
                              {article.manual_review_reason}
                            </p>
                          )}
                          <div className="flex flex-wrap gap-2 mt-3">
                            {article.source_url && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => window.open(article.source_url, '_blank')}
                              >
                                Source
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEditArticle(article)}
                            >
                              Edit
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleOpenAIRewriteDraft(article)}
                              disabled={actionLoading === "openai-rewrite-" + (article._id || article.id)}
                              className="text-purple-600 hover:text-purple-700 hover:bg-purple-50 border-purple-200"
                              title="Rewrite with OpenAI and open draft editor"
                            >
                              {actionLoading === "openai-rewrite-" + (article._id || article.id) ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <AlertCircle className="h-4 w-4" />
                              )}
                              <span className="ml-1">Open AI</span>
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleArchiveArticle(article.id)}
                            >
                              Archive
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={async () => {
                                const confirmed = await showConfirmation({
                                  title: 'Delete Manual Review Article',
                                  description: `Move "${article.title}" to archive as admin_delete? Shared links will still be preserved.`,
                                  variant: 'destructive',
                                  confirmText: 'Delete',
                                  cancelText: 'Cancel'
                                });
                                if (confirmed) {
                                  handleDeleteArticle(article.id);
                                }
                              }}
                              disabled={actionLoading === `delete-article-${article.id}`}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                            >
                              {actionLoading === `delete-article-${article.id}` ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Archived Articles List */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Archived Articles</CardTitle>
                    <CardDescription>
                      {archivedArticles.length} articles in archive · Manual review is shown above for live hidden articles
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchArchivedArticles}
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {archivedArticles.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Archive className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p>No archived articles</p>
                    <p className="text-sm mt-1">Use bulk archive to move old articles here</p>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {archivedArticles.map((article) => (
                      <div 
                        key={article._id || article.id} 
                        className="flex items-center gap-3 p-3 bg-muted dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                        onClick={() => window.open(buildArticleUrl(article), '_blank')}
                        title="Click to view article"
                      >
                        {article.image && (
                          <img 
                            src={article.image} 
                            alt="" 
                            className="w-12 h-12 object-cover rounded"
                          />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-muted-foreground dark:text-gray-300 truncate text-sm">{article.title}</p>
                          <div className="flex items-center gap-2 mt-1 flex-wrap">
                            {article.archive_reason === 'needs_manual_review' && (
                              <Badge variant="destructive" className="text-xs">Needs manual review</Badge>
                            )}
                            <Badge variant="secondary" className="text-xs">{article.category}</Badge>
                            <span className="text-xs text-gray-400">{article.publishedDate?.substring(0, 10)}</span>
                            {article.archive_reason && article.archive_reason !== 'needs_manual_review' && (
                              <span className="text-xs text-gray-400">• {article.archive_reason}</span>
                            )}
                          </div>
                          {article.archive_reason === 'needs_manual_review' && (
                            <div className="mt-1 text-xs text-red-600 dark:text-red-400 line-clamp-2">
                              Triggered by: {(article.manual_review_hits || []).join(', ') || 'AI rewrite risk phrase'}
                            </div>
                          )}
                        </div>
                        {article.archive_reason === 'needs_manual_review' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => { e.stopPropagation(); handleEditArticle(article); }}
                            className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                            title="Edit manual review article"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => { e.stopPropagation(); handleAIReviewArticle(article._id || article.id); }}
                          disabled={actionLoading === "ai-review-" + (article._id || article.id)}
                          className="text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                          title="Check with ChatGPT"
                        >
                          {actionLoading === "ai-review-" + (article._id || article.id) ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <AlertCircle className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => { e.stopPropagation(); handleUnarchiveArticle(article._id || article.id); }}
                          disabled={actionLoading === `unarchive-${article.id}`}
                          className="text-green-600 hover:text-green-700 hover:bg-green-50"
                          title="Restore article"
                        >
                          {actionLoading === `unarchive-${article.id}` ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <RotateCcw className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Affiliates Tab */}
        {activeTab === 'affiliates' && (
          <div className="space-y-6">
            {/* Header Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <ShoppingBag className="h-5 w-5 text-amber-600" />
                      Amazon Affiliate Products
                    </CardTitle>
                    <CardDescription>
                      Manage affiliate products displayed on your site. Products appear in article sidebars and end-of-article sections.
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={fetchAffiliateProducts}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                    <Button 
                      onClick={handleAddAffiliate}
                      className="bg-amber-600 hover:bg-amber-700"
                      data-testid="add-affiliate-button"
                    >
                      <PlusCircle className="h-4 w-4 mr-2" />
                      Add Product
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="bg-amber-50 p-4 rounded-lg mb-4">
                  <div className="flex items-start gap-3">
                    <PoundSterling className="h-5 w-5 text-amber-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-amber-800">Amazon Associate ID: cheshiretoday-21</p>
                      <p className="text-sm text-amber-700 mt-1">
                        Products you add here will automatically use your affiliate tag. Add products by pasting any Amazon.co.uk product or search URL.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-green-700">{affiliateProducts.filter(p => p.active !== false).length}</p>
                    <p className="text-sm text-green-600">Active Products</p>
                  </div>
                  <div className="bg-gray-100 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-muted-foreground">{affiliateProducts.filter(p => p.active === false).length}</p>
                    <p className="text-sm text-muted-foreground">Inactive</p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-blue-700">{affiliateCategories.length}</p>
                    <p className="text-sm text-blue-600">Categories</p>
                  </div>
                  <div className="bg-amber-50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-amber-700">{affiliateProducts.length}</p>
                    <p className="text-sm text-amber-600">Total Products</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Products List */}
            <Card>
              <CardHeader>
                <CardTitle>All Products</CardTitle>
                <CardDescription>
                  {affiliateProducts.length} products • Click to edit
                </CardDescription>
              </CardHeader>
              <CardContent>
                {affiliateProducts.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <ShoppingBag className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p className="font-medium">No affiliate products yet</p>
                    <p className="text-sm mt-1">Click &quot;Add Product&quot; to create your first Amazon affiliate link</p>
                    <Button 
                      onClick={handleAddAffiliate}
                      className="mt-4 bg-amber-600 hover:bg-amber-700"
                    >
                      <PlusCircle className="h-4 w-4 mr-2" />
                      Add Your First Product
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[500px] overflow-y-auto">
                    {affiliateProducts.map((product) => (
                      <div 
                        key={product.id} 
                        className={`flex items-center gap-4 p-4 rounded-lg border transition-colors ${
                          product.active !== false 
                            ? 'bg-card border-gray-200 hover:bg-muted' 
                            : 'bg-muted border-gray-200 opacity-60'
                        }`}
                        data-testid={`affiliate-row-${product.id}`}
                      >
                        {/* Product Image */}
                        <div className="relative flex-shrink-0">
                          <img 
                            src={product.image} 
                            alt={product.name}
                            className="w-16 h-16 object-cover rounded-lg border"
                            onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1557821552-17105176677c?w=200'; }}
                          />
                          {product.active === false && (
                            <div className="absolute inset-0 bg-muted0/50 rounded-lg flex items-center justify-center">
                              <span className="text-white text-xs font-medium">OFF</span>
                            </div>
                          )}
                        </div>

                        {/* Product Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium text-foreground truncate">{product.name}</h4>
                            {product.active !== false && (
                              <Badge className="bg-green-100 text-green-700 text-xs">Active</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1">
                            <span className="text-lg font-bold text-amber-600">{product.price}</span>
                            <Badge variant="secondary" className="text-xs">{product.category}</Badge>
                            <div className="flex items-center gap-0.5">
                              <Star className="h-3 w-3 text-yellow-400 fill-yellow-400" />
                              <span className="text-xs text-muted-foreground">{product.rating}</span>
                            </div>
                          </div>
                          <a 
                            href={product.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline flex items-center gap-1 mt-1"
                          >
                            <ExternalLink className="h-3 w-3" />
                            View on Amazon
                          </a>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToggleAffiliateActive(product)}
                            disabled={actionLoading === `toggle-affiliate-${product.id}`}
                            className={product.active !== false 
                              ? "text-muted-foreground hover:text-muted-foreground" 
                              : "text-green-600 hover:text-green-700"
                            }
                            title={product.active !== false ? "Deactivate" : "Activate"}
                          >
                            {actionLoading === `toggle-affiliate-${product.id}` ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : product.active !== false ? (
                              <X className="h-4 w-4" />
                            ) : (
                              <Check className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditAffiliate(product)}
                            className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 border-blue-200"
                            title="Edit product"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteAffiliate(product.id)}
                            disabled={actionLoading === `delete-affiliate-${product.id}`}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                            title="Delete product"
                          >
                            {actionLoading === `delete-affiliate-${product.id}` ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Instructions Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LinkIcon className="h-5 w-5 text-muted-foreground" />
                  How It Works
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm text-muted-foreground">
                  <div className="flex gap-3">
                    <span className="bg-amber-100 text-amber-700 rounded-full w-6 h-6 flex items-center justify-center font-medium flex-shrink-0">1</span>
                    <p>Find a product on Amazon.co.uk you want to promote</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="bg-amber-100 text-amber-700 rounded-full w-6 h-6 flex items-center justify-center font-medium flex-shrink-0">2</span>
                    <p>Click &quot;Add Product&quot; and paste the Amazon URL (product page or search page)</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="bg-amber-100 text-amber-700 rounded-full w-6 h-6 flex items-center justify-center font-medium flex-shrink-0">3</span>
                    <p>Add a name, price, and image URL. Select a category to show with matching articles</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="bg-amber-100 text-amber-700 rounded-full w-6 h-6 flex items-center justify-center font-medium flex-shrink-0">4</span>
                    <p>Products automatically display in sidebars and article footers with your affiliate tag</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'advertising' && (
          <div className="space-y-6">
            <Card className="dark:bg-gray-800 dark:border-gray-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PoundSterling className="h-5 w-5 text-amber-600" />
                  Advertising Leads
                </CardTitle>
                <CardDescription>
                  Enquiries submitted through the /advertise page. Contact businesses from news@cheshiretoday.co.uk, then create sponsored placements after payment and review.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4 rounded-lg border border-amber-200 dark:border-amber-900/60 bg-amber-50 dark:bg-amber-950/20 p-4 text-sm text-gray-700 dark:text-gray-300">
                  <p className="font-bold text-gray-900 dark:text-white">After a lead converts</p>
                  <p className="mt-1">
                    Confirm payment, collect the advert title/message/link/image, review it for suitability, then create a sponsored placement. Active placements can appear in available homepage and article sponsored slots, including desktop and mobile placements.
                  </p>
                </div>

                <div id="create-sponsored-placement" className="mb-6 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
                  <h3 className="font-bold text-gray-900 dark:text-white mb-1">{editingSponsoredPlacementSlug ? "Edit Sponsored Placement" : "Create Sponsored Placement"}</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    {editingSponsoredPlacementSlug ? `Editing ${editingSponsoredPlacementSlug}. Save updates this existing advert without creating a duplicate.` : "Create a paid advert after payment and review. New sponsored placements run for 30 days automatically. Choose article or homepage slots below, including desktop + mobile pairs."}
                  </p>

                  <form onSubmit={saveSponsoredPlacement} className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <Label className="text-xs">Placement</Label>
                      <select
                        value={sponsoredPlacementForm.placement}
                        onChange={(e) => setSponsoredPlacementForm(prev => ({ ...prev, placement: e.target.value }))}
                        className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800"
                      >
                        <option value="article_both">Desktop + mobile article slots</option>
                        <option value="homepage_both">Desktop + mobile homepage slots</option>
                        <option value="article_sidebar">Desktop article sidebar only</option>
                        <option value="article_mobile">Mobile in-article card only</option>
                        <option value="homepage_sidebar">Desktop homepage sidebar only</option>
                        <option value="homepage_mobile">Mobile homepage card only</option>
                      </select>
                    </div>

                    <div>
                      <Label className="text-xs">Package</Label>
                      <select
                        value={sponsoredPlacementForm.package_tier}
                        onChange={(e) => setSponsoredPlacementForm(prev => ({ ...prev, package_tier: e.target.value }))}
                        className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800"
                      >
                        <option value="Local Starter">Local Starter — standard rotation</option>
                        <option value="Local Featured">Local Featured — stronger rotation</option>
                        <option value="Local Partner">Local Partner — priority rotation</option>
                      </select>
                    </div>

                    <div>
                      <Label className="text-xs">Sponsor / business name</Label>
                      <Input
                        value={sponsoredPlacementForm.sponsor_name}
                        onChange={(e) => setSponsoredPlacementForm(prev => ({ ...prev, sponsor_name: e.target.value }))}
                        placeholder="Business name"
                      />
                    </div>

                    <div>
                      <Label className="text-xs">Target URL</Label>
                      <Input
                        value={sponsoredPlacementForm.target_url}
                        onChange={(e) => setSponsoredPlacementForm(prev => ({ ...prev, target_url: e.target.value }))}
                        placeholder="https://example.com"
                      />
                    </div>

                    <div>
                      <Label className="text-xs">Advert title</Label>
                      <Input
                        value={sponsoredPlacementForm.title}
                        onChange={(e) => setSponsoredPlacementForm(prev => ({ ...prev, title: e.target.value }))}
                        placeholder="Advert headline"
                      />
                    </div>

                    <div>
                      <Label className="text-xs">CTA text</Label>
                      <Input
                        value={sponsoredPlacementForm.cta_text}
                        onChange={(e) => setSponsoredPlacementForm(prev => ({ ...prev, cta_text: e.target.value }))}
                        placeholder="Learn more"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <Label className="text-xs">Image URL optional</Label>
                      <Input
                        value={sponsoredPlacementForm.image_url}
                        onChange={(e) => setSponsoredPlacementForm(prev => ({ ...prev, image_url: e.target.value }))}
                        placeholder="https://example.com/image.jpg"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <Label className="text-xs">Advert message</Label>
                      <Textarea
                        value={sponsoredPlacementForm.description}
                        onChange={(e) => setSponsoredPlacementForm(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Short sponsored message shown on the advert card"
                      />
                    </div>

                    <div className="md:col-span-2 flex flex-col sm:flex-row justify-end gap-2">
                      {editingSponsoredPlacementSlug && (
                        <Button type="button" variant="outline" onClick={cancelSponsoredPlacementEdit}>
                          Cancel edit
                        </Button>
                      )}
                      <Button type="submit" className="bg-amber-600 hover:bg-amber-700 text-white">
                        {editingSponsoredPlacementSlug ? "Save advert changes" : "Create sponsored placement"}
                      </Button>
                    </div>
                  </form>
                </div>

                <div className="mb-6 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
                  <div className="flex items-center justify-between gap-3 mb-3">
                    <div>
                      <h3 className="font-bold text-gray-900 dark:text-white">Live Sponsored Placements</h3>
                      <p className="text-sm text-muted-foreground">Paid adverts available to display in sponsored slots. Expired placements are listed here but will not show publicly.</p>
                    </div>
                    <div className="flex flex-col sm:flex-row gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={exportSponsoredPlacementsCsv}
                        disabled={sponsoredPlacements.length === 0}
                      >
                        Export CSV
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={fetchSponsoredPlacements}
                        disabled={sponsoredPlacementsLoading}
                      >
                        {sponsoredPlacementsLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                        Refresh
                      </Button>
                    </div>
                  </div>

                  <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    <div className="rounded bg-muted/40 px-3 py-3">
                      <div className="text-muted-foreground">Active campaigns</div>
                      <div className="text-lg font-bold text-foreground">{sponsoredPlacementReport.active}</div>
                    </div>
                    <div className="rounded bg-muted/40 px-3 py-3">
                      <div className="text-muted-foreground">Impressions</div>
                      <div className="text-lg font-bold text-foreground">{sponsoredPlacementReport.impressions}</div>
                    </div>
                    <div className="rounded bg-muted/40 px-3 py-3">
                      <div className="text-muted-foreground">Clicks</div>
                      <div className="text-lg font-bold text-foreground">{sponsoredPlacementReport.clicks}</div>
                    </div>
                    <div className="rounded bg-muted/40 px-3 py-3">
                      <div className="text-muted-foreground">Average CTR</div>
                      <div className="text-lg font-bold text-foreground">{sponsoredPlacementReport.ctr}%</div>
                    </div>
                  </div>

                  {sponsoredPlacementsLoading ? (
                    <div className="flex items-center justify-center py-6">
                      <Loader2 className="h-5 w-5 animate-spin text-amber-600" />
                    </div>
                  ) : sponsoredPlacements.length === 0 ? (
                    <p className="rounded border border-dashed border-gray-300 dark:border-gray-700 p-4 text-sm text-muted-foreground">
                      No paid sponsored placements are active. Article pages will show the fallback “Advertise from £49/month” card.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {sponsoredPlacements.map((placement) => {
                        const impressions = Number(placement.impression_count || 0);
                        const clicks = Number(placement.click_count || 0);
                        const ctr = impressions > 0 ? ((clicks / impressions) * 100).toFixed(2) : "0.00";
                        const placementLabel = (
                          placement.placement === "homepage_sidebar" ? "Homepage desktop"
                          : placement.placement === "homepage_mobile" ? "Homepage mobile"
                          : placement.placement === "article_sidebar" ? "Article desktop"
                          : placement.placement === "article_mobile" ? "Article mobile"
                          : placement.placement
                        );
                        const statusVariant = (!placement.active || (placement.ends_at && Date.parse(placement.ends_at) < Date.now())) ? "secondary" : "default";
                        const statusLabel = placement.ends_at && Date.parse(placement.ends_at) < Date.now() ? "expired" : placement.active ? "active" : "inactive";

                        return (
                          <div key={placement.slug || placement.id} className="rounded border border-gray-200 dark:border-gray-700 p-3">
                            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                              <div className="min-w-0">
                                <div className="flex flex-wrap items-center gap-2">
                                  <p className="font-bold text-gray-900 dark:text-white">{placement.title}</p>
                                  <Badge variant={statusVariant}>{statusLabel}</Badge>
                                  <Badge variant="outline">{placementLabel}</Badge>
                                  {placement.package_tier && <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">{placement.package_tier}</Badge>}
                                </div>
                                <p className="mt-1 text-sm text-muted-foreground break-all">{placement.sponsor_name} · {placement.target_url}</p>
                                {placement.description && <p className="mt-2 text-sm text-gray-700 dark:text-gray-300">{placement.description}</p>}

                                <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                                  <div className="rounded bg-muted/40 px-2 py-2">
                                    <div className="text-muted-foreground">Impressions</div>
                                    <div className="font-semibold text-foreground">{impressions}</div>
                                  </div>
                                  <div className="rounded bg-muted/40 px-2 py-2">
                                    <div className="text-muted-foreground">Clicks</div>
                                    <div className="font-semibold text-foreground">{clicks}</div>
                                  </div>
                                  <div className="rounded bg-muted/40 px-2 py-2">
                                    <div className="text-muted-foreground">CTR</div>
                                    <div className="font-semibold text-foreground">{ctr}%</div>
                                  </div>
                                  <div className="rounded bg-muted/40 px-2 py-2">
                                    <div className="text-muted-foreground">Campaign</div>
                                    <div className="font-semibold text-foreground truncate">{placement.campaign_id || "—"}</div>
                                  </div>
                                </div>
                              </div>

                              <div className="flex flex-col items-start md:items-end gap-2 text-xs text-muted-foreground shrink-0">
                                <div>Weight: {placement.rotation_weight || "auto"}</div>
                                <div>Priority: {placement.priority || 0}</div>
                                {placement.starts_at && (
                                  <div>Starts: {new Date(placement.starts_at).toLocaleDateString("en-GB")}</div>
                                )}
                                {placement.ends_at && (
                                  <div>Expires: {new Date(placement.ends_at).toLocaleDateString("en-GB")}</div>
                                )}
                                <div className="flex flex-col gap-2 mt-1 w-full md:w-auto">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => editSponsoredPlacement(placement)}
                                  >
                                    Edit advert
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="destructive"
                                    onClick={() => deleteSponsoredPlacement(placement.slug)}
                                  >
                                    Delete advert
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                <div className="mb-4 rounded-lg border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50 dark:bg-emerald-950/20 p-4 text-sm text-gray-700 dark:text-gray-300">
                  <p className="font-bold text-gray-900 dark:text-white">Business Spotlight workflow</p>
                  <p className="mt-1">
                    Local Partner enquiries are treated as Business Spotlight leads. When a paid Local Partner lead is ready, “Create advert from lead” pre-fills the sponsored placement form with homepage desktop + mobile slots.
                  </p>
                </div>

                <div className="flex items-center justify-between gap-3 mb-4">
                  <div className="text-sm text-muted-foreground">
                    {advertiserLeads.length} lead{advertiserLeads.length === 1 ? "" : "s"} loaded
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={fetchAdvertiserLeads}
                    disabled={advertiserLeadsLoading}
                  >
                    {advertiserLeadsLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                    Refresh
                  </Button>
                </div>

                {advertiserLeadsLoading ? (
                  <div className="flex items-center justify-center py-10">
                    <Loader2 className="h-6 w-6 animate-spin text-amber-600" />
                  </div>
                ) : advertiserLeads.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-gray-300 dark:border-gray-700 p-8 text-center">
                    <p className="font-semibold text-gray-900 dark:text-white">No advertising leads yet</p>
                    <p className="mt-2 text-sm text-muted-foreground">
                      New enquiries from the Advertise page will appear here after businesses submit the form.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {advertiserLeads.map((lead) => (
                      <div key={lead.id} className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
                        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <h3 className="font-bold text-gray-900 dark:text-white">
                                {lead.business || lead.name || "Advertising enquiry"}
                              </h3>
                              <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
                                {lead.tier || "Package not selected"}
                              </Badge>
                              {/partner/i.test(String(lead.tier || lead.package_tier || "")) && (
                                <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200">
                                  Business Spotlight
                                </Badge>
                              )}
                              <Badge variant="outline">
                                {lead.status === "payment_pending" ? "checkout started, not paid" : lead.status === "paid_pending_review" ? "paid — needs review" : lead.status === "advert_live" ? "advert live" : lead.status === "renewal_due" ? "renewal due" : lead.status === "expired" ? "expired" : lead.status || "new"}
                              </Badge>
                            </div>
                            <p className="mt-1 text-sm text-muted-foreground">
                              {lead.name} · {lead.email}
                            </p>
                            {(lead.phone || lead.website || lead.target_area) && (
                              <p className="mt-1 text-sm text-muted-foreground">
                                {lead.phone ? `Phone: ${lead.phone} · ` : ""}
                                {lead.website ? `Website: ${lead.website} · ` : ""}
                                {lead.target_area ? `Area: ${lead.target_area}` : ""}
                              </p>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground md:text-right">
                            <div>{lead.package_price || ""}</div>
                            <div>{lead.created_at ? new Date(lead.created_at).toLocaleString("en-GB") : ""}</div>
                          </div>
                        </div>

                        {lead.message && (
                          <p className="mt-3 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                            {lead.message}
                          </p>
                        )}

                        {lead.status === "payment_pending" && (
                          <div className="mt-3 rounded-lg border border-amber-200 dark:border-amber-900/60 bg-amber-50 dark:bg-amber-950/20 p-3 text-sm text-amber-800 dark:text-amber-200">
                            <strong>Checkout started but not paid.</strong> Follow up if this is a real advertiser, or archive the lead if it was a test or abandoned checkout.
                          </div>
                        )}

                        <div className="mt-3 flex flex-wrap gap-2">
                          {lead.email && (
                            <a
                              href={buildAdvertiserLeadMailto(lead)}
                              className="inline-flex items-center rounded-md bg-amber-600 hover:bg-amber-700 text-white px-3 py-2 text-sm font-semibold"
                            >
                              Email advertiser
                            </a>
                          )}
                          {lead.website && (
                            <a
                              href={lead.website.startsWith("http") ? lead.website : `https://${lead.website}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center rounded-md border border-gray-300 dark:border-gray-700 px-3 py-2 text-sm font-semibold"
                            >
                              Open website
                            </a>
                          )}
                          {(lead.status === "paid_pending_review" || lead.payment_status === "paid") && (
                            <Button
                              size="sm"
                              className="bg-emerald-600 hover:bg-emerald-700 text-white"
                              onClick={() => prepareSponsoredPlacementFromLead(lead)}
                            >
                              Create advert from lead
                            </Button>
                          )}
                          <Button size="sm" variant="outline" onClick={() => updateAdvertiserLeadStatus(lead.id, "contacted")}>
                            Mark contacted
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => updateAdvertiserLeadStatus(lead.id, "converted")}>
                            Mark converted
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => updateAdvertiserLeadStatus(lead.id, "advert_live")}>
                            Mark advert live
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => updateAdvertiserLeadStatus(lead.id, "renewal_due")}>
                            Renewal due
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => updateAdvertiserLeadStatus(lead.id, "expired")}>
                            Mark expired
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => updateAdvertiserLeadStatus(lead.id, "declined")}>
                            Decline
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => updateAdvertiserLeadStatus(lead.id, "archived")}>
                            Archive
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => {
                              if (window.confirm("Delete this advertising lead permanently?")) {
                                deleteAdvertiserLead(lead.id);
                              }
                            }}
                          >
                            Delete lead
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Jobs Tab Content */}
        {activeTab === 'jobs' && (
          <div className="space-y-6">
            {/* Header Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Briefcase className="h-5 w-5 text-blue-600" />
                      Job Board Management
                    </CardTitle>
                    <CardDescription>
                      Manage job listings for the Cheshire Jobs board. Active jobs appear on the public /jobs page.
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchAllData()}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                    <Button 
                      onClick={() => setShowAddJob(true)}
                      className="bg-blue-600 hover:bg-blue-700"
                      data-testid="add-job-button"
                    >
                      <PlusCircle className="h-4 w-4 mr-2" />
                      Add Job
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                  <div className="bg-orange-50 dark:bg-orange-900/30 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-orange-700 dark:text-orange-400">{jobs.filter(j => j.status === 'pending').length}</p>
                    <p className="text-sm text-orange-600 dark:text-orange-500">Pending Review</p>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-green-700 dark:text-green-400">{jobs.filter(j => j.active !== false && j.status !== 'pending').length}</p>
                    <p className="text-sm text-green-600 dark:text-green-500">Active Jobs</p>
                  </div>
                  <div className="bg-yellow-50 dark:bg-yellow-900/30 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-yellow-700 dark:text-yellow-400">{jobs.filter(j => j.featured).length}</p>
                    <p className="text-sm text-yellow-600 dark:text-yellow-500">Featured</p>
                  </div>
                  <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-muted-foreground dark:text-gray-300">{jobs.filter(j => j.active === false && j.status !== 'pending').length}</p>
                    <p className="text-sm text-muted-foreground dark:text-gray-400">Inactive</p>
                  </div>
                  <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">{jobs.length}</p>
                    <p className="text-sm text-blue-600 dark:text-blue-500">Total Jobs</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Pending Submissions Alert */}
            {jobs.filter(j => j.status === 'pending').length > 0 && (
              <Card className="border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-orange-700 dark:text-orange-400">
                    <AlertCircle className="h-5 w-5" />
                    Pending Job Submissions ({jobs.filter(j => j.status === 'pending').length})
                  </CardTitle>
                  <CardDescription className="text-orange-600 dark:text-orange-500">
                    These jobs were submitted through the public form and need your approval
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {jobs.filter(j => j.status === 'pending').map((job) => (
                      <div 
                        key={job.id} 
                        className="flex items-center gap-4 p-4 rounded-lg border border-orange-200 dark:border-orange-800 bg-card dark:bg-gray-800"
                        data-testid={`pending-job-${job.id}`}
                      >
                        <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-white font-bold text-lg">
                          {job.company.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-foreground dark:text-white">{job.title}</h4>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground dark:text-gray-400">
                            <Building2 className="h-3 w-3" />
                            {job.company}
                            <span className="mx-1">•</span>
                            <MapPin className="h-3 w-3" />
                            {job.location}
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            Submitted by: {job.contact_name} ({job.contact_email})
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                            onClick={async () => {
                              try {
                                const response = await fetch(`${getApiUrl()}/api/admin/jobs/${job.id}/approve`, {
                                  method: 'POST',
                                  headers: getAuthHeaders()
                                });
                                const data = await response.json();
                                if (data.success) {
                                  toast({ 
                                    title: "✅ Approved", 
                                    description: data.email_sent ? `Approval email sent to ${job.contact_email}` : `Job is now live`
                                  });
                                  fetchAllData();
                                }
                              } catch (error) {
                                toast({ title: "Error", description: "Failed to approve", variant: "destructive" });
                              }
                            }}
                            data-testid={`approve-job-${job.id}`}
                          >
                            <Check className="h-4 w-4 mr-1" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-red-600 hover:text-red-700 border-red-300"
                            onClick={async () => {
                              const reason = window.prompt('Rejection reason (optional - will be sent to employer):');
                              if (reason === null) return; // User cancelled
                              try {
                                const response = await fetch(`${getApiUrl()}/api/admin/jobs/${job.id}/reject`, {
                                  method: 'POST',
                                  headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ reason: reason || null })
                                });
                                const data = await response.json();
                                if (data.success) {
                                  toast({ 
                                    title: "Rejected", 
                                    description: data.email_sent ? `Rejection email sent to ${job.contact_email}` : `Job rejected`
                                  });
                                  fetchAllData();
                                }
                              } catch (error) {
                                toast({ title: "Error", description: "Failed to reject", variant: "destructive" });
                              }
                            }}
                            data-testid={`reject-job-${job.id}`}
                          >
                            <X className="h-4 w-4 mr-1" />
                            Reject
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Jobs List */}
            <Card>
              <CardHeader>
                <CardTitle>All Job Listings</CardTitle>
                <CardDescription>
                  {jobs.filter(j => j.status !== 'pending').length} approved jobs • Click icons to manage
                </CardDescription>
              </CardHeader>
              <CardContent>
                {jobs.filter(j => j.status !== 'pending').length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Briefcase className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p className="font-medium">No job listings yet</p>
                    <p className="text-sm mt-1">Click &quot;Add Job&quot; to create your first job posting</p>
                    <Button 
                      onClick={() => setShowAddJob(true)}
                      className="mt-4 bg-blue-600 hover:bg-blue-700"
                    >
                      <PlusCircle className="h-4 w-4 mr-2" />
                      Add Your First Job
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[600px] overflow-y-auto">
                    {jobs.filter(j => j.status !== 'pending').map((job) => (
                      <div 
                        key={job.id} 
                        className={`flex items-center gap-4 p-4 rounded-lg border transition-colors ${
                          job.active !== false 
                            ? 'bg-card dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:bg-muted dark:hover:bg-gray-700' 
                            : 'bg-muted dark:bg-gray-900 border-gray-200 dark:border-gray-700 opacity-60'
                        }`}
                        data-testid={`job-row-${job.id}`}
                      >
                        {/* Job Icon */}
                        <div className={`relative flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-lg ${
                          job.featured ? 'bg-gradient-to-br from-yellow-500 to-amber-600' : 'bg-gradient-to-br from-blue-500 to-indigo-600'
                        }`}>
                          {job.company.charAt(0)}
                          {job.featured && (
                            <Star className="absolute -top-1 -right-1 h-4 w-4 text-yellow-400 fill-yellow-400" />
                          )}
                        </div>

                        {/* Job Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className="font-medium text-foreground dark:text-white truncate">{job.title}</h4>
                            {job.active !== false && (
                              <Badge className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 text-xs">Active</Badge>
                            )}
                            {job.featured && (
                              <Badge className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300 text-xs">Featured</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1 flex-wrap">
                            <span className="text-sm text-muted-foreground dark:text-gray-400 flex items-center gap-1">
                              <Building2 className="h-3 w-3" />
                              {job.company}
                            </span>
                            <span className="text-sm text-muted-foreground dark:text-gray-400 flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {job.location}
                            </span>
                            <Badge variant="secondary" className="text-xs">{job.job_type}</Badge>
                            {job.salary && (
                              <span className="text-sm font-medium text-green-600 dark:text-green-400">{job.salary}</span>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground dark:text-gray-400 mt-1">
                            {job.category} • Posted {formatDate(job.created_at)}
                          </p>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToggleJobFeatured(job.id)}
                            className={job.featured 
                              ? "text-yellow-600 hover:text-yellow-700 border-yellow-300" 
                              : "text-muted-foreground hover:text-yellow-600"
                            }
                            title={job.featured ? "Remove Featured" : "Make Featured"}
                          >
                            <Star className={`h-4 w-4 ${job.featured ? 'fill-yellow-400' : ''}`} />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToggleJobActive(job.id)}
                            className={job.active !== false 
                              ? "text-muted-foreground hover:text-muted-foreground" 
                              : "text-green-600 hover:text-green-700"
                            }
                            title={job.active !== false ? "Deactivate" : "Activate"}
                          >
                            {job.active !== false ? <X className="h-4 w-4" /> : <Check className="h-4 w-4" />}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setJobForm({
                                title: job.title || '',
                                company: job.company || '',
                                location: job.location || 'Macclesfield',
                                job_type: job.job_type || 'Full-time',
                                salary: job.salary || '',
                                description: job.description || '',
                                requirements: job.requirements || '',
                                category: job.category || 'Other',
                                apply_url: job.apply_url || '',
                                apply_email: job.apply_email || ''
                              });
                              setEditingJob(job);
                              setShowAddJob(true);
                            }}
                            className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 border-blue-200"
                            title="Edit job"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteJob(job.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                            title="Delete job"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Tips Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LinkIcon className="h-5 w-5 text-muted-foreground" />
                  Tips for Job Listings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm text-muted-foreground dark:text-gray-400">
                  <div className="flex gap-3">
                    <span className="bg-blue-100 text-blue-700 rounded-full w-6 h-6 flex items-center justify-center font-medium flex-shrink-0">1</span>
                    <p>Featured jobs appear at the top of the job board with special highlighting</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="bg-blue-100 text-blue-700 rounded-full w-6 h-6 flex items-center justify-center font-medium flex-shrink-0">2</span>
                    <p>Include salary information when possible - it increases applications by 30%</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="bg-blue-100 text-blue-700 rounded-full w-6 h-6 flex items-center justify-center font-medium flex-shrink-0">3</span>
                    <p>Deactivate jobs when positions are filled - you can reactivate them later</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* News Import Tab */}
        {activeTab === 'newsimport' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Newspaper className="h-5 w-5 text-emerald-600" />
                  News Import Controls
                </CardTitle>
                <CardDescription>
                  Import fresh news articles from RSS feeds and AI sources
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Import Options */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {/* Add New Articles */}
                  <Card className="border-2 border-emerald-200 dark:border-emerald-800">
                    <CardContent className="pt-6">
                      <div className="text-center space-y-4">
                        <div className="h-12 w-12 bg-emerald-100 dark:bg-emerald-900 rounded-full flex items-center justify-center mx-auto">
                          <PlusCircle className="h-6 w-6 text-emerald-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-foreground dark:text-white">Import New Articles</h3>
                          <p className="text-sm text-muted-foreground dark:text-gray-400 mt-1">
                            Add new articles without removing existing ones
                          </p>
                        </div>
                        <ul className="text-xs text-muted-foreground dark:text-gray-400 text-left space-y-1">
                                                    <li>• ~8 Cheshire/Local articles (authority-first)</li>
                          <li>• ~12 UK context articles (supporting coverage)</li>
                          <li>• 2 Business + 2 AI/Tech articles (pillar mix)</li>
                          <li>• Sports is capped (≤3) and not prioritised</li>
                        </ul>
                        <Button
                          onClick={handleImportNews}
                          disabled={importLoading}
                          className="w-full bg-emerald-600 hover:bg-emerald-700"
                          data-testid="import-news-btn"
                        >
                          {importLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Importing...
                            </>
                          ) : (
                            <>
                              <PlusCircle className="h-4 w-4 mr-2" />
                              Import New Articles
                            </>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Archive and Refresh */}
                  <Card className="border-2 border-amber-200 dark:border-amber-800">
                    <CardContent className="pt-6">
                      <div className="text-center space-y-4">
                        <div className="h-12 w-12 bg-amber-100 dark:bg-amber-900 rounded-full flex items-center justify-center mx-auto">
                          <Archive className="h-6 w-6 text-amber-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-foreground dark:text-white">Archive & Refresh</h3>
                          <p className="text-sm text-muted-foreground dark:text-gray-400 mt-1">
                            Move all articles to archive and import fresh news
                          </p>
                        </div>
                        <div className="bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg">
                          <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
                            <Archive className="h-3 w-3" />
                            Articles will be moved to Archive, not deleted
                          </p>
                        </div>
                        <Button
                          onClick={handleClearAndRefresh}
                          disabled={importLoading}
                          className="w-full bg-amber-600 hover:bg-amber-700"
                          data-testid="clear-refresh-btn"
                        >
                          {importLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Archiving...
                            </>
                          ) : (
                            <>
                              <Archive className="h-4 w-4 mr-2" />
                              Archive & Refresh All
                            </>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Backfill Locations */}
                  <Card className="border-2 border-blue-200 dark:border-blue-800">
                    <CardContent className="pt-6">
                      <div className="text-center space-y-4">
                        <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto">
                          <MapPin className="h-6 w-6 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-foreground dark:text-white">Backfill Locations</h3>
                          <p className="text-sm text-muted-foreground dark:text-gray-400 mt-1">
                            Auto-tag articles with location categories
                          </p>
                        </div>
                        <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                          <p className="text-xs text-blue-600 dark:text-blue-400 flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            Scans content for Chester, Warrington, Macclesfield, etc.
                          </p>
                        </div>
                        <Button
                          onClick={handleBackfillLocations}
                          disabled={backfillLoading}
                          className="w-full bg-blue-600 hover:bg-blue-700"
                          data-testid="backfill-locations-btn"
                        >
                          {backfillLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Scanning Articles...
                            </>
                          ) : (
                            <>
                              <MapPin className="h-4 w-4 mr-2" />
                              Run Location Backfill
                            </>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Import Results */}
                {importResult && (
                  <Card className="bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300">
                        <CheckCircle className="h-5 w-5" />
                        Import Results
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-300">{importResult.total_imported || importResult.articles_imported || 0}</p>
                          <p className="text-xs text-muted-foreground dark:text-gray-400">Total Imported</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{importResult.cheshire_articles || 0}</p>
                          <p className="text-xs text-muted-foreground dark:text-gray-400">Local/Cheshire</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">{importResult.uk_articles || 0}</p>
                          <p className="text-xs text-muted-foreground dark:text-gray-400">UK News</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-orange-700 dark:text-orange-300">{(importResult.business_articles || 0) + (importResult.tech_articles || 0)}</p>
                          <p className="text-xs text-muted-foreground dark:text-gray-400">Business + AI/Tech</p>
                        </div>
                      </div>
                                          </CardContent>
                  </Card>
                )}
              </CardContent>
            </Card>

            {/* RSS Sources Info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LinkIcon className="h-5 w-5 text-muted-foreground" />
                  News Sources
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <h4 className="font-medium text-foreground dark:text-white mb-2">Local Cheshire Sources</h4>
                    <ul className="space-y-1 text-muted-foreground dark:text-gray-400">
                      <li>• Cheshire Live (Macclesfield, Chester)</li>
                      <li>• Warrington Guardian</li>
                      <li>• Manchester Evening News</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-foreground dark:text-white mb-2">National UK Sources</h4>
                    <ul className="space-y-1 text-muted-foreground dark:text-gray-400">
                      <li>• BBC News (UK, Sports, Business)</li>
                      <li>• The Guardian (UK, Tech)</li>
                      <li>• Sky News (UK News)</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Add/Edit Job Dialog */}
      <Dialog open={showAddJob} onOpenChange={(open) => { 
        if (!open) { 
          setShowAddJob(false); 
          setEditingJob(null);
          setJobForm({ title: '', company: '', location: 'Macclesfield', job_type: 'Full-time', salary: '', description: '', requirements: '', category: 'Other', apply_url: '', apply_email: '' }); 
        } 
      }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {editingJob ? <Edit className="h-5 w-5" /> : <PlusCircle className="h-5 w-5" />}
              {editingJob ? 'Edit Job Listing' : 'Add New Job'}
            </DialogTitle>
            <DialogDescription>
              {editingJob ? 'Update the job details below' : 'Create a new job listing for the Cheshire Jobs board'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="job-title">Job Title *</Label>
                <Input
                  id="job-title"
                  value={jobForm.title}
                  onChange={(e) => setJobForm({...jobForm, title: e.target.value})}
                  placeholder="e.g. Software Developer"
                  data-testid="job-title-input"
                />
              </div>
              <div>
                <Label htmlFor="job-company">Company *</Label>
                <Input
                  id="job-company"
                  value={jobForm.company}
                  onChange={(e) => setJobForm({...jobForm, company: e.target.value})}
                  placeholder="e.g. Tech Corp Ltd"
                  data-testid="job-company-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="job-location">Location</Label>
                <Select value={jobForm.location} onValueChange={(val) => setJobForm({...jobForm, location: val})}>
                  <SelectTrigger data-testid="job-location-select">
                    <SelectValue placeholder="Select location" />
                  </SelectTrigger>
                  <SelectContent>
                    {(jobOptions.locations.length > 0 ? jobOptions.locations : ['Macclesfield', 'Chester', 'Crewe', 'Warrington', 'Wilmslow', 'Knutsford', 'Northwich', 'Congleton', 'Nantwich', 'Sandbach']).map(loc => (
                      <SelectItem key={loc} value={loc}>{loc}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="job-type">Job Type</Label>
                <Select value={jobForm.job_type} onValueChange={(val) => setJobForm({...jobForm, job_type: val})}>
                  <SelectTrigger data-testid="job-type-select">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {(jobOptions.job_types.length > 0 ? jobOptions.job_types : ['Full-time', 'Part-time', 'Contract', 'Temporary', 'Remote', 'Apprenticeship']).map(type => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="job-salary">Salary (optional)</Label>
                <Input
                  id="job-salary"
                  value={jobForm.salary}
                  onChange={(e) => setJobForm({...jobForm, salary: e.target.value})}
                  placeholder="e.g. £30,000 - £40,000"
                  data-testid="job-salary-input"
                />
              </div>
              <div>
                <Label htmlFor="job-category">Category</Label>
                <Select value={jobForm.category} onValueChange={(val) => setJobForm({...jobForm, category: val})}>
                  <SelectTrigger data-testid="job-category-select">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {(jobOptions.categories.length > 0 ? jobOptions.categories : ['IT & Technology', 'Healthcare', 'Education', 'Retail', 'Hospitality', 'Manufacturing', 'Finance', 'Construction', 'Transport', 'Other']).map(cat => (
                      <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="job-description">Job Description *</Label>
              <Textarea
                id="job-description"
                value={jobForm.description}
                onChange={(e) => setJobForm({...jobForm, description: e.target.value})}
                placeholder="Describe the role, responsibilities, and what makes this opportunity exciting..."
                rows={4}
                data-testid="job-description-input"
              />
            </div>

            <div>
              <Label htmlFor="job-requirements">Requirements (optional)</Label>
              <Textarea
                id="job-requirements"
                value={jobForm.requirements}
                onChange={(e) => setJobForm({...jobForm, requirements: e.target.value})}
                placeholder="List skills, qualifications, or experience required..."
                rows={3}
                data-testid="job-requirements-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="job-apply-url">Apply URL (optional)</Label>
                <Input
                  id="job-apply-url"
                  value={jobForm.apply_url}
                  onChange={(e) => setJobForm({...jobForm, apply_url: e.target.value})}
                  placeholder="https://..."
                  data-testid="job-apply-url-input"
                />
              </div>
              <div>
                <Label htmlFor="job-apply-email">Apply Email (optional)</Label>
                <Input
                  id="job-apply-email"
                  type="text"
                  value={jobForm.apply_email}
                  onChange={(e) => setJobForm({...jobForm, apply_email: e.target.value})}
                  placeholder="hr@company.com"
                  data-testid="job-apply-email-input"
                />
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2 mt-4">
            <Button variant="outline" onClick={() => { setShowAddJob(false); setEditingJob(null); }}>
              Cancel
            </Button>
            <Button 
              onClick={editingJob ? async () => {
                try {
                  const response = await fetch(`${getApiUrl()}/api/admin/jobs/${editingJob.id}`, {
                    method: 'PUT',
                    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
                    body: JSON.stringify(jobForm)
                  });
                  const data = await response.json();
                  if (data.success) {
                    toast({ title: "✅ Job Updated", description: `${jobForm.title} has been updated` });
                    setShowAddJob(false);
                    setEditingJob(null);
                    setJobForm({ title: '', company: '', location: 'Macclesfield', job_type: 'Full-time', salary: '', description: '', requirements: '', category: 'Other', apply_url: '', apply_email: '' });
                    fetchAllData();
                  }
                } catch (error) {
                  toast({ title: "Error", description: "Failed to update job", variant: "destructive" });
                }
              } : handleCreateJob}
              className="bg-blue-600 hover:bg-blue-700"
              data-testid="save-job-button"
            >
              {editingJob ? 'Update Job' : 'Create Job'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add/Edit Article Dialog */}
      <Dialog open={showAddArticle} onOpenChange={(open) => { if (!open) { setShowAddArticle(false); resetArticleForm(); } }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {editingArticle ? <Edit className="h-5 w-5" /> : <PlusCircle className="h-5 w-5" />}
              {editingArticle ? 'Edit Article' : 'Add New Article'}
            </DialogTitle>
            <DialogDescription>
              {editingArticle ? 'Update the article details below' : 'Create a new article manually'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmitArticle} className="space-y-4">
            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title">Title *</Label>
              <Input
                id="title"
                value={articleForm.title}
                onChange={(e) => setArticleForm({...articleForm, title: e.target.value})}
                placeholder="Enter article title"
                required
                data-testid="article-title-input"
              />
            </div>

            {/* Summary / short preview */}
            <div className="space-y-2">
              <Label htmlFor="summary">Short preview / intro</Label>
              <Textarea
                id="summary"
                value={articleForm.summary}
                onChange={(e) => setArticleForm({...articleForm, summary: e.target.value})}
                placeholder="This controls the short intro shown above Continue reading..."
                rows={3}
                data-testid="article-summary-input"
              />
              <p className="text-xs text-muted-foreground">
                Used as the visible intro below the headline and for article previews. Keep it around 1 sentence.
              </p>
            </div>

            {/* Content */}
            <div className="space-y-2">
              <Label htmlFor="content">Content *</Label>
              <Textarea
                id="content"
                value={articleForm.content}
                onChange={(e) => setArticleForm({...articleForm, content: e.target.value})}
                placeholder="Write your article content here..."
                required
                rows={8}
                data-testid="article-content-input"
              />
            </div>

            {/* Category and Author Row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="category">Category *</Label>
                <Select 
                  value={articleForm.category} 
                  onValueChange={(value) => setArticleForm({...articleForm, category: value})}
                >
                  <SelectTrigger data-testid="article-category-select">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map(cat => (
                      <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="author">Author</Label>
                <Input
                  id="author"
                  value={articleForm.author}
                  onChange={(e) => setArticleForm({...articleForm, author: e.target.value})}
                  placeholder="Author name"
                  data-testid="article-author-input"
                />
              </div>
            </div>

            {/* Source and Source URL */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="source">Source</Label>
                <Input
                  id="source"
                  value={articleForm.source}
                  onChange={(e) => setArticleForm({...articleForm, source: e.target.value})}
                  placeholder="e.g. Cheshire Live, BBC News"
                  data-testid="article-source-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="source_url">Source URL</Label>
                <Input
                  id="source_url"
                  value={articleForm.source_url}
                  onChange={(e) => setArticleForm({...articleForm, source_url: e.target.value})}
                  placeholder="https://example.com/original-story"
                  data-testid="article-source-url-input"
                />
              </div>
            </div>

            {/* Image URL */}
            <div className="space-y-2">
              <Label htmlFor="image" className="flex items-center gap-2">
                <ImageIcon className="h-4 w-4" />
                Image URL
              </Label>
              <Input
                id="image"
                value={articleForm.image}
                onChange={(e) => setArticleForm({...articleForm, image: e.target.value})}
                placeholder="https://example.com/image.jpg (optional)"
                data-testid="article-image-input"
              />
              {articleForm.image && (
                <div className="mt-2">
                  <img 
                    src={articleForm.image} 
                    alt="Preview" 
                    className="h-32 w-auto object-cover rounded-lg border"
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                </div>
              )}
            </div>

            {/* Tags */}
            <div className="space-y-2">
              <Label htmlFor="tags">Tags</Label>
              <Input
                id="tags"
                value={articleForm.tags}
                onChange={(e) => setArticleForm({...articleForm, tags: e.target.value})}
                placeholder="cheshire, local, news (comma separated)"
                data-testid="article-tags-input"
              />
            </div>

            {/* Featured Toggle */}
            <div className="flex items-center justify-between p-3 bg-muted dark:bg-gray-800 rounded-lg">
              <div>
                <Label htmlFor="featured" className="font-medium">Featured Article</Label>
                <p className="text-sm text-muted-foreground">Show this article prominently on the homepage</p>
              </div>
              <Switch
                id="featured"
                checked={articleForm.featured}
                onCheckedChange={(checked) => setArticleForm({...articleForm, featured: checked})}
                data-testid="article-featured-toggle"
              />
            </div>

            <DialogFooter className="gap-2 pt-4">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => { setShowAddArticle(false); resetArticleForm(); }}
              >
                Cancel
              </Button>
              <Button 
                type="submit"
                disabled={articleSubmitting || !articleForm.title || !articleForm.content}
                className="bg-blue-600 hover:bg-blue-700"
                data-testid="submit-article-button"
              >
                {articleSubmitting ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Check className="h-4 w-4 mr-2" />
                )}
                {editingArticle ? 'Update Article' : 'Publish Article'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Affiliate Product Dialog */}
      <Dialog open={showAddAffiliate} onOpenChange={(open) => { if (!open) { setShowAddAffiliate(false); resetAffiliateForm(); } }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShoppingBag className="h-5 w-5 text-amber-600" />
              {editingAffiliate ? 'Edit Affiliate Product' : 'Add Affiliate Product'}
            </DialogTitle>
            <DialogDescription>
              {editingAffiliate ? 'Update the product details below' : 'Add an Amazon product to display on your site'}
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmitAffiliate} className="space-y-4">
            {/* Product Name */}
            <div className="space-y-2">
              <Label htmlFor="affiliate-name">Product Name *</Label>
              <Input
                id="affiliate-name"
                value={affiliateForm.name}
                onChange={(e) => setAffiliateForm({...affiliateForm, name: e.target.value})}
                placeholder="e.g., Wireless Earbuds, Walking Boots"
                required
                data-testid="affiliate-name-input"
              />
            </div>

            {/* Amazon URL */}
            <div className="space-y-2">
              <Label htmlFor="affiliate-url">Amazon URL *</Label>
              <Input
                id="affiliate-url"
                value={affiliateForm.url}
                onChange={(e) => setAffiliateForm({...affiliateForm, url: e.target.value})}
                placeholder="https://www.amazon.co.uk/..."
                required
                data-testid="affiliate-url-input"
              />
              <p className="text-xs text-muted-foreground">Paste any Amazon.co.uk product or search URL. Your affiliate tag will be added automatically.</p>
            </div>

            {/* Price */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="affiliate-price">Price Display *</Label>
                <Input
                  id="affiliate-price"
                  value={affiliateForm.price}
                  onChange={(e) => setAffiliateForm({...affiliateForm, price: e.target.value})}
                  placeholder="From £19.99"
                  required
                  data-testid="affiliate-price-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="affiliate-rating">Rating</Label>
                <Input
                  id="affiliate-rating"
                  type="number"
                  step="0.1"
                  min="1"
                  max="5"
                  value={affiliateForm.rating}
                  onChange={(e) => setAffiliateForm({...affiliateForm, rating: parseFloat(e.target.value) || 4.5})}
                  data-testid="affiliate-rating-input"
                />
              </div>
            </div>

            {/* Image URL */}
            <div className="space-y-2">
              <Label htmlFor="affiliate-image">Product Image URL</Label>
              <Input
                id="affiliate-image"
                value={affiliateForm.image}
                onChange={(e) => setAffiliateForm({...affiliateForm, image: e.target.value})}
                placeholder="https://images.unsplash.com/..."
                data-testid="affiliate-image-input"
              />
              <p className="text-xs text-muted-foreground">Use Unsplash or another image source. Amazon images may not work directly.</p>
            </div>

            {/* Image Preview */}
            {affiliateForm.image && (
              <div className="flex justify-center">
                <img 
                  src={affiliateForm.image} 
                  alt="Preview" 
                  className="w-24 h-24 object-cover rounded-lg border"
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              </div>
            )}

            {/* Category */}
            <div className="space-y-2">
              <Label htmlFor="affiliate-category">Category</Label>
              <Select
                value={affiliateForm.category}
                onValueChange={(value) => setAffiliateForm({...affiliateForm, category: value})}
              >
                <SelectTrigger data-testid="affiliate-category-select">
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="default">Default (All Articles)</SelectItem>
                  {CATEGORIES.map(cat => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">Products show alongside articles in matching categories</p>
            </div>

            {/* Active Toggle */}
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div>
                <Label htmlFor="affiliate-active" className="font-medium">Active</Label>
                <p className="text-sm text-muted-foreground">Show this product on the site</p>
              </div>
              <Switch
                id="affiliate-active"
                checked={affiliateForm.active}
                onCheckedChange={(checked) => setAffiliateForm({...affiliateForm, active: checked})}
                data-testid="affiliate-active-toggle"
              />
            </div>

            <DialogFooter className="gap-2 pt-4">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => { setShowAddAffiliate(false); resetAffiliateForm(); }}
              >
                Cancel
              </Button>
              <Button 
                type="submit"
                disabled={affiliateSubmitting || !affiliateForm.name || !affiliateForm.url || !affiliateForm.price}
                className="bg-amber-600 hover:bg-amber-700"
                data-testid="submit-affiliate-button"
              >
                {affiliateSubmitting ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Check className="h-4 w-4 mr-2" />
                )}
                {editingAffiliate ? 'Update Product' : 'Add Product'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onOpenChange={(open) => !open && confirmDialog.onCancel?.()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className={`flex items-center gap-2 ${
              confirmDialog.variant === 'destructive' ? 'text-red-600' : 
              confirmDialog.variant === 'warning' ? 'text-amber-600' : 'text-foreground dark:text-white'
            }`}>
              {confirmDialog.variant === 'destructive' && <AlertTriangle className="h-5 w-5" />}
              {confirmDialog.variant === 'warning' && <AlertCircle className="h-5 w-5" />}
              {confirmDialog.variant === 'default' && <CheckCircle className="h-5 w-5 text-emerald-600" />}
              {confirmDialog.title}
            </DialogTitle>
            <DialogDescription className="text-muted-foreground dark:text-gray-400 pt-2">
              {confirmDialog.description}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => confirmDialog.onCancel?.()}
              className="flex-1"
            >
              {confirmDialog.cancelText}
            </Button>
            <Button 
              type="button"
              onClick={() => confirmDialog.action?.()}
              className={`flex-1 ${
                confirmDialog.variant === 'destructive' ? 'bg-red-600 hover:bg-red-700' : 
                confirmDialog.variant === 'warning' ? 'bg-amber-600 hover:bg-amber-700' : 
                'bg-emerald-600 hover:bg-emerald-700'
              }`}
            >
              {confirmDialog.confirmText}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
    </HelmetProvider>
  );
};

export default AdminDashboard;