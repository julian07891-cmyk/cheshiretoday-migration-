# Cheshire Today - Product Requirements Document

## Project Overview
**Cheshire Today** is a local news aggregation website serving Cheshire and Northwest UK. The site curates news from trusted publishers (BBC, Sky, Guardian, Cheshire Live, Manchester Evening News) via RSS feeds and presents them in a clean, user-friendly interface.

## Current Architecture

### Tech Stack
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **News Sources**: RSS feeds from BBC, Sky, Guardian, Cheshire Live, Manchester Evening News, Warrington Guardian

### News Aggregator Model (Implemented Jan 2026)
The site operates as a **legal news aggregator**, NOT a content generator:
- Headlines and summaries from RSS feeds
- "Read Full Story" links to original publishers
- No AI content generation (saves cost, avoids legal issues)
- Publisher images from RSS feeds
- **Cost: £0/month for content**

## Features Implemented

### Core Features
- [x] News aggregation from multiple UK/local RSS feeds
- [x] Category filtering (All, Local News, UK News, Business, Health, Sports, Tech, Science, Entertainment, Education)
- [x] Breaking news ticker
- [x] "Read Full Story" buttons linking to original sources
- [x] Responsive design with dark mode
- [x] Weather widget (Cheshire)
- [x] "Most Read" section
- [x] Search functionality
- [x] Newsletter subscription with email digest
- [x] **Trending Topics** - Shows hot keywords from recent articles with click-to-search
- [x] **Smart Category Override** - Keyword-based system fixes miscategorized articles

### Admin Features
- [x] JWT-based authentication
- [x] Manual article import trigger
- [x] Content cleanup (duplicates, old articles)
- [x] Email digest trigger
- [x] **Facebook Manual Post Selection** (NEW - Jan 9, 2026)
  - Select specific articles to post to Facebook
  - "Post Now" button for immediate posting
- [x] **Facebook Post Scheduling** (NEW - Jan 9, 2026)
  - Full calendar view for scheduling posts days in advance
  - Time picker for precise scheduling
  - View pending scheduled posts
  - Cancel scheduled posts
  - Post history with status tracking
- [x] **Amazon Affiliate Product Management** (NEW - Jan 18, 2026)
  - Full CRUD interface to add/edit/delete affiliate products
  - Category assignment for contextual display
  - Active/inactive toggle for each product
  - Products display in article sidebars and footers
  - Automatic affiliate tag (cheshiretoday-21) appended to URLs
- [x] **Job Board Management** (NEW - Jan 23, 2026)
  - Full admin UI to create, edit, delete, activate/deactivate job listings
  - Featured job toggle for priority display
  - Public /jobs page with search, filters (location, category, type)
  - Job detail view with apply options (URL or email)
  - Stats dashboard (active, featured, inactive, total jobs)
  - **Public Job Submission** (/jobs/post) - Employers can submit jobs for review
  - **Approval Workflow** - Admin sees pending submissions, can approve/reject with one click
  - **Paid Job Listings with Stripe** - 3 packages: Standard £25, Featured £50, Premium £75
  - Stripe checkout integration for secure payments
  - Payment verification and auto-update of job status
  - **Email Notifications** - Automatic emails sent to employers on approval/rejection
- [x] **Facebook Hashtags** (NEW - Jan 10, 2026)
  - All posts include combination of category + location hashtags
  - Automatically generated from article title and category
- [x] **Facebook Analytics** (NEW - Jan 10, 2026)
  - Track engagement metrics (likes, comments, shares)
  - View top performing posts
  - Get insights and recommendations

### Monetization (Phase 1 - Implemented)
- [x] Google AdSense integration (ID: ca-pub-3403912630939928)
- [x] Sidebar ad placements (2 positions)
- [x] In-feed ad placement
- [x] Newsletter sponsor slot ready

## Pending Issues

### P0 - Critical
1. **Production Email Not Sending** - ✅ **RESOLVED**
   - SMTP configured and working (Office365: smtp.office365.com:587)
   - Authentication verified successful
   - Real subscribers: julian07891@yahoo.co.uk, news@cheshiretoday.co.uk
   - Email digest ready to send

2. **Facebook Duplicate Posts** - ✅ **RESOLVED (Jan 11, 2026)**
   - Auto-scheduler was posting same articles multiple times due to race condition
   - **Root cause**: Concurrent scheduler executions could all pass the lock check
   - **Fix implemented**: Atomic distributed lock using MongoDB `find_one_and_update`
   - Lock mechanism now prevents concurrent executions (tested with 5 concurrent requests)
   - Also includes 24-hour sliding window + title pattern matching for duplicate detection
   - Now checks `facebook_post_log` collection before posting

3. **Stripe Payment Button Stuck** - ✅ **RESOLVED (Jan 23, 2026)**

4. **Affiliate Widgets Showing Duplicate Products** - ✅ **RESOLVED (Jan 24, 2026)**
   - "You Might Like" and "You Might Also Like" sections were showing the same products
   - **Root cause**: Each widget fetched and shuffled products independently, causing overlap
   - **Fix implemented**: Products now fetched and shuffled ONCE in parent component (ArticlePage/HomePage), then distinct slices passed to each widget via props
   - "You Might Like" receives first 2 products, "You Might Also Like" receives next 4 products
   - Both dedicated article page and homepage modal now have unique product sets
   - Test report: `/app/test_reports/iteration_7.json` - 100% frontend tests passed
   - "Pay & Submit Job" button was getting stuck on "Submitting..." state
   - **Root cause**: setSubmitting(false) in finally block was interrupting Stripe redirect
   - **Fix**: Proper error handling with button reset only on error, not on success
   - Added comprehensive console logging for debugging
   - Verified working with Stripe checkout redirect

4. **JSON-LD NewsArticle Schema** - ✅ **RESOLVED (Jan 15, 2026)**
   - Critical for Google News visibility and rich results
   - Schema dynamically injected via useEffect when article dialog opens
   - Includes: headline, publisher, datePublished, author, articleSection, keywords
   - Verified working in testing

4. **Related Articles Auto-Scroll Bug** - ✅ **RESOLVED (Jan 15, 2026)**
   - Persistent bug where clicking related article didn't scroll dialog to top
   - **Fix**: Double requestAnimationFrame pattern with scrollTo({top:0, behavior:'instant'})
   - Verified working - scroll position resets to 0 on click

### P1 - High Priority
1. **Production Environment Parity**
   - Changes in preview don't auto-deploy to production
   - User must manually deploy after each fix

2. **`www` Subdomain 405 Errors** - ⏳ **PENDING USER DNS CHANGE**
   - `www.cheshiretoday.co.uk/robots.txt` returns 405 error
   - User needs to update GoDaddy CNAME forwarding to redirect to `https://cheshiretoday.co.uk`
   - Affects AdSense verification and SEO crawling

3. **Mobile Admin Login** - ⏳ **USER VERIFICATION PENDING**
   - Fix implemented in AdminDashboard.jsx (loading states, input handling, autocomplete)
   - User needs to verify fix works on production

4. **Location Pages Fixed** - ✅ **RESOLVED (Jan 27, 2026)**
   - Location-specific pages (Macclesfield, Chester, Warrington, etc.) were showing empty or incorrect articles
   - **Root cause**: Existing articles in database were missing the `location` field + false positives (e.g., "chester" matching "manchester")
   - **Fix implemented**: 
     - Added word boundary matching to prevent false positives
     - Created `/api/admin/backfill-locations` endpoint to tag all existing articles
     - Added 10+ new location-specific RSS feeds (Nantwich, Congleton, Winsford, Middlewich, Ellesmere Port, Runcorn, Widnes, Alderley Edge)
     - Created "All Cheshire" page for general articles without specific town tags
   - All location pages now display correct content

5. **Affiliate Widget Text Visibility** - ✅ **RESOLVED (Jan 27, 2026)**
   - Improved text contrast in "You Might Like" and affiliate product sections
   - **Changes**: 
     - Product cards now use `dark:bg-gray-700` for better contrast (was gray-800)
     - Price text changed to amber color (`text-amber-600 dark:text-amber-400`) for better visibility
     - Star ratings improved with `dark:text-gray-300` for rating numbers
     - Sponsored badge improved with visible borders in dark mode
   - Files modified: `AffiliateWidgets.jsx`

6. **Auto Location Detection on Article Edit** - ✅ **RESOLVED (Jan 27, 2026)**
   - Articles now automatically assigned to location category when created or edited
   - **Implementation**:
     - Updated `/api/admin/articles` (POST) to auto-detect location from title/content
     - Updated `/api/admin/articles/{id}` (PUT) to re-detect location on save
     - Location tag automatically added to article tags
   - No manual backfill needed for new/edited articles

7. **View All Scroll Behavior** - ✅ **RESOLVED (Jan 29, 2026)**
   - "View All" buttons now scroll to the first article NOT shown on homepage
   - **Implementation**:
     - Added `pendingScrollRef` to track scroll target when category changes
     - Scroll triggers after articles load (not immediately on click)
     - Fixed `data-testid` on CompactArticleCard for reliable targeting
   - Test report: `/app/test_reports/iteration_11.json` - 100% tests passed

## Backlog / Future Tasks

### P1 - High Priority
- [ ] Add more RSS categories (Science, Entertainment, Education from BBC) - **COMPLETED Jan 5, 2026**
- [x] Refactor server.py into smaller modules (routes, services, scheduler) - **COMPLETED Jan 5, 2026**

### P2 - Medium Priority
- [x] Job board section for local employers - **COMPLETED Jan 23, 2026**
- [ ] Event listings for Cheshire events
- [ ] Premium membership option (ad-free)

### P3 - Nice to Have
- [ ] Local business directory
- [ ] User comments/discussion
- [ ] Push notifications for breaking news

## Key API Endpoints
- `GET /api/articles` - Fetch articles (with source_url, summary)
- `POST /api/admin/login` - Admin authentication
- `POST /api/admin/clear-and-refresh` - Import fresh RSS content
- `POST /api/send-digest` - Trigger email newsletter
- `GET /api/check-smtp-config` - Verify SMTP settings

## Key Files & Architecture

### Backend Structure (Refactored Jan 5, 2026)
```
/app/backend/
├── server.py              # Main FastAPI app (still the primary entry point)
├── config.py              # Configuration and environment variables
├── database.py            # MongoDB connection
├── routes/                # API route modules (ready for future migration)
│   └── __init__.py
├── services/              # Business logic services
│   ├── auth_service.py    # Admin token management
│   ├── article_service.py # Article generation logic (Gemini AI)
│   └── image_service.py   # UK-only image selection (300+ curated images)
├── models/                # Pydantic schemas
│   └── schemas.py         # Article, AdminLogin, Subscribe models
├── scheduler/             # Background tasks
│   └── tasks.py           # Cleanup, generation, email digest jobs
└── app/                   # Existing services
    ├── news_feed_service.py  # RSS feed fetching
    ├── email_service.py      # Email digest with sponsor support, verification codes
    └── perplexity_service.py # AI content generation (hybrid model)
```

### Frontend Files
- `/app/frontend/src/App.js` - Main React app
- `/app/frontend/src/components/CompactArticleCard.jsx` - Article cards with reading time
- `/app/frontend/src/components/CommentsSection.jsx` - Comments with email login
- `/app/frontend/src/components/NewsletterPreferences.jsx` - Newsletter category/frequency preferences
- `/app/frontend/src/components/SubscribeSection.jsx` - Newsletter subscribe with preferences link
- `/app/frontend/src/components/AdPlacement.jsx` - AdSense components

## Credentials
- **Admin**: news@cheshiretoday.co.uk / ningab-zipxur-8pibDi
- **AdSense ID**: ca-pub-3403912630939928

## Change Log

- **Jan 30, 2026**: View All Highlight & Digest Duplicate Fix
  - **ENHANCEMENT**: Visual highlight effect on scroll target
    - Green pulse animation with "NEW" badge on the first article users haven't seen
    - CSS animation (`highlightPulse`) with 2.5s duration
    - Article scrolls to center of viewport for better visibility
  - **BUGFIX**: Daily Brief duplicate send prevention
    - Added 1-hour cooldown check on manual digest trigger (`/api/send-digest`)
    - Fixed timezone handling for datetime comparison
    - Returns informative message with time since last send
  - **Files Modified**:
    - `frontend/src/App.js` - Added highlight class logic, changed to `block: 'center'`
    - `frontend/src/App.css` - Added `highlightPulse` animation and `.highlight-new-article` styles
    - `backend/server.py` - Added duplicate prevention to `/api/send-digest` endpoint

- **Jan 29, 2026**: View All Scroll-to-Next-Article Feature
  - **NEW FEATURE**: "View All" buttons now scroll to the first article NOT already shown on homepage
  - **Problem**: Users clicking "View All UK News" were shown articles they already saw on homepage
  - **Solution**: 
    - Added `pendingScrollRef` to track scroll target when category changes
    - New scroll effect triggers AFTER articles load, scrolling to article at index = homepage count
    - Fixed `CompactArticleCard` data-testid to include article ID for reliable targeting
  - **Behavior**:
    - UK News shows 2 articles on homepage → View All scrolls to article #3
    - Sports shows 2 articles → View All scrolls to article #3
    - Business, Health, Tech, Science, Entertainment all behave the same
    - Local News shows 4 articles → View All Cheshire scrolls to article #5
  - **Files Modified**:
    - `frontend/src/App.js` - handleCategoryChange, pendingScrollRef, scroll useEffect
    - `frontend/src/components/CompactArticleCard.jsx` - fixed data-testid attribute
  - **Test report**: `/app/test_reports/iteration_11.json` - 100% frontend tests passed

- **Jan 27, 2026**: SEO Improvements for Better Google Indexing
  - **NEW ENDPOINT**: `/api/seo/article/{article_id}` - Server-side rendered HTML with proper meta tags
    - Full article content for search engine crawlers
    - Proper canonical URLs, Open Graph, Twitter cards
    - JSON-LD structured data (NewsArticle schema)
    - Returns proper 404 for missing articles
  - **ROBOTS.TXT UPDATED**: Comprehensive configuration
    - Allows all article pages, location pages, category pages
    - Blocks admin, unsubscribe, preferences pages from indexing
    - Blocks tracking parameters (utm_, fbclid, gclid)
    - Includes both sitemaps
    - Googlebot-specific rules for faster crawling
  - **NOINDEX TAGS ADDED**: 
    - Admin Dashboard (`/admin`)
    - Unsubscribe Page (`/unsubscribe`)
    - Preferences Page (`/newsletter/preferences`)
  - **INDEX.HTML**: Added pre-rendering hint (`<meta name="fragment" content="!">`)
  - **Expected Impact**: Should resolve "113 pages discovered but not indexed" within 2-4 weeks
  - **3 pages with noindex**: Correctly configured for admin/preferences pages (expected behavior)

- **Jan 26, 2026**: Article Archival System - Preserve Old Article Links
  - **CRITICAL FIX**: Articles are now archived instead of permanently deleted
  - **Problem**: Facebook/social media links to deleted articles were returning "Article not found"
  - **Solution**: All article deletion operations now archive to `archived_articles` collection
  - **Modified Endpoints**:
    - `GET /api/articles/{article_id}` - Now searches both `articles` AND `archived_articles`
    - `GET /api/share/{article_id}` - Now searches archived articles for social media crawlers
    - `GET /api/article-meta/{article_id}` - Now includes archived articles
    - `DELETE /api/articles/{article_id}` - Now archives instead of deleting
    - `GET /api/admin/articles/archived` - Now returns articles from BOTH legacy (archived flag) AND new (archived_articles collection) systems
    - `GET /api/admin/articles/stats` - Now includes total archived count from both systems
    - `POST /api/admin/articles/{id}/unarchive` - Now can restore from both legacy and collection archives
  - **Admin Dashboard**: Archive tab now shows all 257 archived articles
  - **Duplicate Cleanup**: Now archives duplicates/short articles instead of permanent deletion
  - **Benefits**: All previously shared links will continue to work indefinitely
  - **Verified**: 257 archived articles accessible, public retrieval working

- **Jan 26, 2026**: Unsubscribe & Preferences Pages Fix
  - **BUGFIX**: Fixed backend startup failure (NameError: PreferencesUpdateRequest not defined)
    - Root cause: Class `PreferencesUpdateRequest` was used on line 2988 but defined later on line 3504
    - Fix: Moved Pydantic model definitions to top of file with other models
    - Also moved `UnsubscribeRequest` class to ensure all models are defined before use
  - **VERIFIED WORKING**: Public Unsubscribe Flow
    - `/unsubscribe` page loads correctly with email form
    - Submitting unsubscribe form works (POST `/api/newsletter/unsubscribe`)
    - Success message displayed to user
  - **VERIFIED WORKING**: Public Preferences Management Flow
    - `/newsletter/preferences` page loads correctly
    - Email lookup works (GET `/api/newsletter/preferences/{email}`)
    - Non-subscriber shows "not found" message
    - Valid subscriber shows toggle options (Daily Brief, Weekly Roundup, Breaking News)
    - Saving preferences works (POST `/api/newsletter/email-preferences`)
  - **Navigation Links Working**:
    - Unsubscribe page → Preferences page link works with email parameter
    - URL parameter handling auto-fills email and fetches preferences
  - Test report: `/app/test_reports/iteration_10.json` - 100% frontend tests passed (8/8 features)

- **Jan 15, 2026**: New Features - Comments, Newsletter Segmentation, Reading Time
  - **NEW FEATURE**: Reading Time Estimates on Article Cards
    - Shows "X min" or "X min read" based on article content word count
    - Calculation: Math.ceil(words / 200) with minimum 1 minute
    - Added to both vertical and horizontal card layouts
  - **NEW FEATURE**: Comments System with Email-Based Login
    - Users can comment after email verification (no password required)
    - 6-digit verification code sent to email (10 min expiry)
    - Session stored in localStorage for persistent login
    - Features: threaded replies, likes, delete own comments
    - New collections: `comment_users`, `comment_sessions`, `comments`, `comment_likes`
    - New endpoints: `/api/comments/register`, `/api/comments/verify`, `/api/comments`, `/api/comments/article/{id}`
  - **NEW FEATURE**: Newsletter Segmentation
    - Subscribers can choose categories: Local News, UK News, Business, Health, Sports, Tech, Science, Entertainment, Education
    - Frequency options: Daily Digest, Weekly Roundup, Breaking News Only
    - Preferences dialog accessible from subscribe section
    - New endpoints: `/api/newsletter/categories`, `/api/newsletter/preferences`
  - Test report: `/app/test_reports/iteration_5.json` - 100% tests passed (16/16)

- **Jan 15, 2026**: SEO Improvements & Bug Fixes
  - **NEW FEATURE**: JSON-LD NewsArticle Schema for Google News
    - Dynamic schema injection via useEffect when article dialog opens
    - Includes all required fields: headline, publisher, datePublished, author, articleSection, keywords
    - Direct DOM manipulation for reliability (react-helmet-async was unreliable for dynamic scripts)
    - Schema properly removed when dialog closes (cleanup in useEffect return)
  - **BUGFIX**: Related Articles Auto-Scroll (Persistent Bug)
    - Fixed bug where clicking related article didn't scroll dialog to top
    - Root cause: setTimeout-based approach wasn't waiting for DOM paint
    - Fix: Double requestAnimationFrame pattern ensures paint completion before scroll
    - Uses scrollTo({top:0, behavior:'instant'}) for immediate scroll
  - **Verified**: Google Tag Manager script correctly installed (GT-5NTCFMQM)
  - Test report: `/app/test_reports/iteration_4.json` - 100% frontend tests passed

- **Jan 11, 2026**: Facebook Race Condition Fix (Critical Bug)
  - **CRITICAL BUGFIX**: Fixed race condition in Facebook scheduler lock mechanism
    - Root cause: Separate `find_one` + `update_one` operations allowed concurrent executions
    - All concurrent requests could read "no lock" and proceed to post duplicates
    - Fix: Implemented atomic distributed lock using MongoDB `find_one_and_update`
    - Lock mechanism now ensures only ONE process can post at a time
    - Tested with 5 concurrent requests - only 1 acquired lock, 4 were blocked
  - Updated both scheduled job (`scheduled_facebook_post`) and manual trigger endpoint (`/api/facebook/trigger-scheduled`)
  - Lock uses unique lock_id to verify ownership after atomic update

- **Jan 10, 2026**: Facebook Hashtags & Duplicate Prevention Fix
  - **NEW FEATURE**: Combination hashtags for all Facebook posts
    - Category-based hashtags (e.g., #LocalNews, #Health, #Sports)
    - Location-based hashtags (e.g., #Chester, #Knutsford, #Warrington, #Macclesfield)
    - Topic-based hashtags (e.g., #Police, #NHS, #Council)
    - Core hashtags always included (#CheshireToday, #CheshireNews)
    - Limited to 8 hashtags max per post for readability
  - **NEW FEATURE**: Facebook Analytics Dashboard
    - Track post engagement (likes, comments, shares)
    - View top performing posts ranked by engagement score
    - Insights and recommendations for better reach
    - New API endpoints:
      - `GET /api/facebook/analytics` - Get engagement metrics
      - `GET /api/facebook/analytics/insights` - Get actionable insights
    - New "Analytics" tab in Admin Dashboard
  - **NEW FEATURE**: Smart Content Prioritization
    - AI-powered article scoring based on engagement potential
    - Factors: category performance, location mentions, topic keywords, recency
    - `GET /api/facebook/smart-articles` endpoint returns scored recommendations
    - Smart Recommendations section in Admin Facebook tab
  - **NEW FEATURE**: Most Read Today Widget
    - Tracks article views with IP-based deduplication
    - Shows top 5 most read articles in sidebar
    - Period selector: 24h / 7d / 30d
    - `GET /api/articles/most-read` endpoint
    - `POST /api/articles/{id}/view` for tracking
  - **NEW FEATURE**: Push Notifications for Breaking News
    - Web Push API with VAPID authentication
    - "Get Alerts" button + "Share Alerts" button - **Prominent on mobile**
    - Admin can send breaking news alerts to all subscribers
    - Service worker for background notifications
    - **Subscriber Milestone Email Alerts** (NEW)
      - Auto-sends email at: 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000 subscribers
      - Milestone progress bar in Admin Analytics tab
      - Milestone tracking endpoint: `/api/push/milestones`
    - **Share Alerts Feature** (NEW)
      - Social sharing buttons: Twitter, Facebook, WhatsApp, Copy Link
      - Uses native share API on mobile for more options
      - Helps grow subscriber base organically
    - Endpoints: vapid-public-key, subscribe, unsubscribe, stats, send-breaking-news, milestones
  - **NEW FEATURE**: Facebook OAuth Flow (Credentials Added - Setup Pending)
    - Complete OAuth implementation for long-lived tokens
    - Endpoints: /api/facebook/oauth/status, authorize, callback, validate-token
    - Credentials configured: `FACEBOOK_APP_ID` and `FACEBOOK_APP_SECRET` ✅
    - **TODO**: Add redirect URI in Facebook App settings to enable
    - Will auto-exchange short-lived tokens for never-expiring page tokens
  - **BUGFIX**: Auto-scheduler duplicate prevention improved
    - Changed from "today start" to 24-hour sliding window
    - Now checks BOTH article_id AND title patterns to catch duplicates
    - Prevents same story being posted multiple times across day boundaries
  - **BUGFIX**: Route order fixed for /api/articles/most-read
  - Test files: 
    - `/app/tests/test_facebook_features.py` (18 tests)
    - `/app/tests/test_most_read_push_features.py` (22 tests)

- **Jan 23, 2026**: Stripe Payment Bug Fix & Currency Update
  - **CRITICAL BUGFIX**: Fixed "Pay & Submit Job" button stuck on "Submitting..."
    - Root cause: Inadequate error handling and setSubmitting(false) in finally block was interrupting redirect
    - Fix: Added comprehensive try/catch error handling, detailed console logging, removed finally block
    - Changed from `window.location.assign` to `window.location.href` for better compatibility
    - Button now resets on error only, not interrupting successful Stripe redirects
  - **ENHANCEMENT**: Changed all currency from $ (dollars) to £ (pounds)
    - Replaced DollarSign icon with PoundSterling icon in PostJob.jsx, JobBoard.jsx, AdminDashboard.jsx
    - All job package prices now display as £15, £29, £49
    - Salary field shows £ icon and GBP-formatted placeholder
  - Test report: `/app/test_reports/iteration_6.json` - 100% frontend tests passed

- **Jan 24, 2026**: Affiliate Widget Duplicate Products Bug Fix
  - **CRITICAL BUGFIX**: Fixed "You Might Like" and "You Might Also Like" showing same products
    - Root cause: Each widget independently fetched and shuffled products, causing overlap
    - Fix: Products now fetched and shuffled ONCE in parent component (ArticlePage or HomePage)
    - Parent passes distinct slices to each widget: inline gets first 2, end article gets next 4
    - Modified files: `App.js` (ArticlePage, HomePage), `AffiliateWidgets.jsx` (added products prop support)
  - Both dedicated article pages (/article/:id) and homepage modal now show unique product sets
  - Products randomize on each page load (shuffle behavior preserved)
  - Test report: `/app/test_reports/iteration_7.json` - 100% frontend tests passed (7/7 features)
  - Files modified:
    - `frontend/src/components/PostJob.jsx` - handlePayment fix, PoundSterling icon
    - `frontend/src/components/JobBoard.jsx` - PoundSterling icon
    - `frontend/src/components/AdminDashboard.jsx` - PoundSterling icon

- **Jan 25, 2026**: Comprehensive Email Strategy Overhaul
  - **MAJOR UPDATE**: Replaced 3x daily digest (6:15, 12:15, 18:15) with tiered email system
  - **New Email Schedule**:
    - **The Daily Brief**: 07:30 AM every morning - Top Cheshire stories
    - **The Weekly Roundup**: 09:00 AM every Sunday - Magazine-style digest
    - **Breaking News Alerts**: Manual trigger only - High priority incidents
  - **New Subscriber Preferences**:
    - `daily_brief` (default: true for new subscribers)
    - `weekly_roundup` (default: false)
    - `breaking_news` (default: false)
  - **New Email Templates** (3 distinct mobile-first designs):
    - Daily Brief: Hero image + headline, 3-5 secondary stories, Weather/Travel utility block
    - Breaking News: Red urgent header, "What We Know" bullet points, Live Updates CTA
    - Weekly Roundup: "The Big Read" feature, ICYMI top 5, Property/Food sections
  - **Admin Dashboard Updates**:
    - New Email Strategy overview showing 3 email types with schedule
    - Breaking News composer with headline, bullet points, and optional live URL
    - Migration Announcement button for one-time notification
    - Test Daily Brief button
  - **Sender Identity**: Updated to "Editor at Cheshire Today" with Reply-To: news@cheshiretoday.co.uk
  - **API Endpoints Added**:
    - `POST /api/send-breaking-news` - Manual breaking news trigger
    - `POST /api/send-announcement-email` - Migration announcement
    - `PUT /api/newsletter/email-preferences` - Update subscriber preferences
    - `GET /api/newsletter/email-preferences/{email}` - Get current preferences
  - Files modified:
    - `backend/app/email_service.py` - New templates (Daily Brief, Breaking News, Weekly Roundup, Announcement)
    - `backend/server.py` - New scheduler (07:30, Sunday 09:00), new endpoints, subscriber preferences
    - `frontend/src/components/AdminDashboard.jsx` - New Digest tab UI with Breaking News composer

- **Jan 25, 2026**: Email Strategy UI Update & Admin Dashboard Enhancements Testing
  - **COMPLETED TESTING**: Comprehensive frontend testing for Email Strategy UI and Admin Dashboard
  - **Fixed Issue**: SubscribeSection.jsx still had old '6 AM, 12 PM, 6 PM' text - updated to 'Daily Brief at 7:30 AM'
  - **Email Strategy UI Verified**:
    - NewsletterPopup shows 'The Daily Brief — Top Cheshire stories at 7:30 AM'
    - NewsFooter shows 'The Daily Brief' heading and '7:30 AM' schedule
    - NewsletterPreferences shows 3 options: Daily Brief, Weekly Roundup, Breaking News
    - SubscribeSection updated to show 'Daily Brief at 7:30 AM' (was 6 AM, 12 PM, 6 PM)
    - No remaining mentions of '3x daily digest' in subscriber-facing UI
  - **Admin Dashboard Features Verified**:
    - Articles tab: Sub-tabs for filtering by category (All, Local News, UK News, Sports, etc.)
    - Articles tab: Search functionality filters articles by title
    - Articles tab: Checkboxes for bulk selection with Select All/Deselect All
    - Articles tab: Archive Selected button with confirmation dialog
    - Digest tab: Email Strategy overview (Daily Brief 7:30 AM, Weekly Roundup Sunday, Breaking News)
    - Digest tab: Breaking News composer with headline, bullets, URL inputs
    - Digest tab: Send Breaking News button with confirmation dialog
    - News Import tab: Import and Archive & Refresh buttons
  - Test report: `/app/test_reports/iteration_8.json` - 100% frontend tests passed

- **Jan 25, 2026**: Email Analytics Tracking Feature
  - **NEW FEATURE**: Comprehensive email analytics tracking for subscriber engagement
  - **Tracking Capabilities**:
    - Open tracking: 1x1 transparent pixel embedded in all emails
    - Click tracking: Links redirected through tracking endpoint before final destination
    - Unique tracking ID generated for each email send
  - **Backend Endpoints**:
    - `GET /api/email/track/open/{tracking_id}` - Tracking pixel endpoint (returns 1x1 GIF)
    - `GET /api/email/track/click/{tracking_id}?url=` - Click tracking with redirect
    - `GET /api/admin/email-analytics?days=30` - Analytics dashboard data
    - `GET /api/admin/email-analytics/trends` - Trends over 30 days for charts
  - **Admin Dashboard UI**:
    - Email Analytics section in Digest tab
    - Summary stats: Emails Sent, Open Rate, Click Rate, Click-to-Open Rate
    - Breakdown by Type: Shows sent/delivered counts per email type
    - Recent Email Campaigns table: Date, Type, Sent, Opens, Clicks
  - **Modified Files**:
    - `backend/app/email_service.py` - Added tracking helpers, tracking pixels, tracked URLs
    - `backend/server.py` - New tracking and analytics endpoints
    - `frontend/src/components/AdminDashboard.jsx` - New Email Analytics UI section
  - **Database**:
    - New `email_analytics` collection stores open/click events per tracking_id
    - `digest_log` now includes `tracking_id` field for correlation

- **Jan 25, 2026**: Complete Email Strategy UI Audit & Fixes (Session 2)
  - **CRITICAL FIXES**: Found and fixed remaining old text references
  - **Files Fixed**:
    - `TrendingSidebar.jsx` - "Stay Informed" banner: changed "3 times daily" → "The Daily Brief — Top Cheshire stories at 7:30 AM"
    - `AdvertiseWithUs.jsx` - Changed "Updates 3 times daily" → "Daily news updates and breaking alerts"
  - **Backend Fixes**:
    - `/api/send-digest` - Now uses `send_daily_brief()` instead of old `send_news_digest()`
    - `/api/send-digest-test` - Updated to send Daily Brief format with tracking
    - Admin "Digest" button renamed to "Daily Brief"
  - **Complete UI Verification** (Test iteration_9.json - 100% pass):
    - ✅ TrendingSidebar shows "The Daily Brief — Top Cheshire stories at 7:30 AM"
    - ✅ NewsletterPopup shows correct Daily Brief messaging
    - ✅ NewsFooter shows correct schedule
    - ✅ SubscribeSection shows correct messaging
    - ✅ NewsletterPreferences shows 3 tier options
    - ✅ Admin Dashboard shows "Daily Brief" button
    - ✅ Admin Email Analytics section working
    - ✅ NO OLD TEXT PATTERNS FOUND (no "3 times daily", "3x daily", "6 AM", "12 PM", "6 PM")
  - Test report: `/app/test_reports/iteration_9.json` - 100% frontend tests passed

- **Jan 18, 2026**: Amazon Affiliate Product Management Feature
  - **NEW FEATURE**: Manual Affiliate Product Management
    - Full CRUD interface in Admin Dashboard under "Affiliates" tab
    - Add products with: name, Amazon URL, price, image URL, category, rating
    - Edit existing products inline
    - Activate/deactivate products without deletion
    - Delete products permanently
    - Products automatically show with your affiliate tag (cheshiretoday-21)
  - New MongoDB collection: `affiliate_products`
  - New API endpoints:
    - `GET /api/admin/affiliates` - Get all affiliate products (admin)
    - `POST /api/admin/affiliates` - Create new product
    - `PUT /api/admin/affiliates/{id}` - Update product
    - `DELETE /api/admin/affiliates/{id}` - Delete product
    - `GET /api/affiliates/public` - Public endpoint for frontend widgets
  - Frontend widget integration:
    - `AffiliateWidgets.jsx` now fetches products from database
    - Falls back to hardcoded products if database is empty
    - Products displayed in article sidebars and end-of-article sections
  - UI features:
    - Stats dashboard showing active/inactive/total products
    - "How It Works" instructions for adding products
    - Image preview in add/edit dialog

- **Jan 20, 2026**: Homepage Layout - Priority Cheshire Locations Feature
  - **NEW FEATURE**: Homepage displays 4 priority Cheshire articles from different locations
    - Hero article: First article from priority locations (typically Macclesfield)
    - Cheshire News section: 4 articles, 1 from each different location
    - Priority order: Macclesfield → Wilmslow → Knutsford → Warrington → Chester → Northwich → Crewe
    - Fallback logic: If a location has no articles, fills from next available location
    - Then fills with any `is_priority_cheshire` articles, then `is_secondary_cheshire`, then Local News
  - Backend changes (`news_feed_service.py`):
    - Added `PRIORITY_LOCATIONS` list with 7 location groups and their keywords
    - New function `get_article_priority_location()` returns specific location name
    - Each location has ~6-10 keyword variants (e.g., Macclesfield includes Bollington, Poynton, Congleton)
    - Fixed false positive: "mere" keyword removed to prevent "Ellesmere" matching Knutsford
    - Added Ellesmere Port to Chester keywords
  - Backend changes (`server.py`):
    - `/api/articles` endpoint now returns `priority_location` field for each article
  - Frontend changes (`App.js`):
    - `buildPriorityCheshireArticles()` function builds diversified article list
    - `cheshireSectionArticles` variable holds 4 articles for the section (excluding hero)
    - Section displays "Macclesfield • Wilmslow • Knutsford & more" subtitle

- **Jan 21, 2026**: Enhanced Affiliate Widget Display
  - **ENHANCED**: Sidebar Affiliate Widget (`AffiliateWidgetSidebar`)
    - Warm amber/gold gradient background for visibility
    - "Top Picks" header with "Handpicked for you" subtitle
    - Large product images (4:3 aspect ratio)
    - Prominent green pricing
    - Blue "View Deal" button with hover effects
    - Shadow and transform animations on hover
  - **NEW**: In-Content Affiliate Widget (`AffiliateWidgetInline`)
    - Appears after article content for high engagement
    - Green accent bar with "You Might Like" header
    - Large horizontal product cards with 112px images
    - Star ratings and "Shop now" links
    - Subtle separators top and bottom
  - **ENHANCED**: End-of-Article Widget (`AffiliateWidgetEndArticle`)
    - Gradient icon header (emerald to teal)
    - "Recommended products for you" subtitle
    - 4-column grid with larger square images
    - Enhanced hover states with scale and shadow
  - Files modified:
    - `frontend/src/components/AffiliateWidgets.jsx` - All three widgets redesigned
    - `frontend/src/App.js` - Added in-content widget placement after article content

- **Jan 21, 2026**: Admin Dashboard - Cleanup Duplicates Button
  - Added "Cleanup" button to Quick Actions (red button with trash icon)
  - One-click duplicate article removal
  - Shows confirmation dialog before cleanup
  - Toast notification with results (duplicates removed, short articles removed, remaining count)

- **Jan 21, 2026**: Article Delete Bug Fix
  - Fixed 500 error when deleting articles from admin dashboard
  - Delete endpoint now handles both MongoDB ObjectId and UUID formats
  - Articles with custom `id` field (UUID) can now be deleted

- **Jan 9, 2026**: Facebook Manual Posting & Scheduling Feature
  - Added new "Facebook" tab to Admin Dashboard with full article selection
  - Implemented "Post Now" button for immediate posting of selected articles
  - Implemented "Schedule" button with full calendar picker and time selection
  - Added scheduled posts queue with pending/history view
  - Backend scheduler checks every 5 minutes for due scheduled posts
  - New MongoDB collection: `scheduled_facebook_posts`
  - New API endpoints:
    - `GET /api/facebook/schedulable-articles` - Get articles for posting
    - `POST /api/facebook/post-single` - Post specific article immediately
    - `POST /api/facebook/schedule-post` - Schedule article for later
    - `GET /api/facebook/scheduled-posts` - View pending/history
    - `DELETE /api/facebook/scheduled-posts/{id}` - Cancel scheduled post
  - Mobile-responsive UI with compact buttons on small screens

- **Jan 5, 2026**: New Features + Cleanup
  - Added 3 new categories: Science, Entertainment, Education with 9 new RSS feeds
  - Implemented Trending Topics widget showing hot keywords from recent articles
  - Added keyword-based category override system (Sports, Entertainment, Science, Education, Health, Tech, Business keywords)
  - Deleted 4 old utility scripts: analyze_images.py, check_live_site.py, clean_citations.py, generate_logo.py

- **Jan 5, 2026**: Backend Refactoring
  - Created modular architecture with separate services, models, and scheduler modules
  - Extracted auth service (`services/auth_service.py`) - token management
  - Extracted image service (`services/image_service.py`) - UK-only image library (300+ curated images)
  - Extracted article service (`services/article_service.py`) - Gemini AI article generation
  - Extracted Pydantic models (`models/schemas.py`) - all request/response schemas
  - Extracted scheduler tasks (`scheduler/tasks.py`) - background cleanup, generation, email jobs
  - Original `server.py` remains functional as the main entry point
  - **Benefits**: Easier maintenance, faster feature additions, cleaner code organization

- **Jan 3, 2026**: Implemented News Aggregator Model + Phase 1 Monetization
  - Converted from AI content generation to RSS aggregation
  - Added "Read Full Story" buttons linking to original sources
  - Integrated Google AdSense with sidebar and in-feed placements
  - Added newsletter sponsor slot
  - Estimated cost savings: ~$7-10/month in AI API costs
