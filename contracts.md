# Cheshire News - Full Stack Application Contracts

## Project Overview
**Cheshire News** is a fully functional news website that combines AI-powered content generation with RSS feed integration. The site features automatic article generation using Perplexity AI, RSS feed consumption from external sources, and RSS feed publication for subscribers.

## Technology Stack
- **Frontend:** React with shadcn/ui components, Tailwind CSS
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **AI Integration:** Perplexity AI (via API)
- **RSS Processing:** feedparser, feedgen, BeautifulSoup4

---

## Backend API Endpoints

### Articles API

#### 1. GET /api/articles
**Purpose:** Fetch all articles with optional filtering
**Query Parameters:**
- `skip`: Number of articles to skip (pagination) - default: 0
- `limit`: Maximum articles to return - default: 20
- `category`: Filter by category (Local News, Business, Events, Sports, Community)

**Response:**
```json
[
  {
    "id": "string",
    "title": "string",
    "content": "string",
    "category": "string",
    "author": "string",
    "publishedDate": "ISO 8601 datetime",
    "image": "URL",
    "tags": ["string"],
    "featured": boolean,
    "source": "string"
  }
]
```

#### 2. GET /api/articles/{article_id}
**Purpose:** Get a specific article by ID
**Response:** Single article object

#### 3. POST /api/generate-articles
**Purpose:** Manually trigger article generation
**Request Body:**
```json
{
  "count": 10,
  "include_uk_news": true
}
```

**Response:**
```json
{
  "success": true,
  "generated": 10,
  "cheshire_articles": 7,
  "uk_articles": 3
}
```

### RSS Integration API

#### 4. GET /api/rss-sources
**Purpose:** List available RSS feed sources
**Query Parameters:**
- `category`: Filter sources by category (optional)

**Response:**
```json
{
  "sources": [
    {
      "name": "BBC England",
      "url": "http://feeds.bbci.co.uk/news/england/rss.xml",
      "category": "Local News"
    }
  ],
  "count": 4
}
```

#### 5. POST /api/import-rss
**Purpose:** Import articles from external RSS feeds and process with Perplexity AI
**Query Parameters:**
- `category`: Filter sources by category (optional)
- `max_per_source`: Maximum articles per source (default: 3, max: 10)
- `use_ai`: Use Perplexity AI to rewrite articles (default: true)

**Response:**
```json
{
  "message": "Successfully imported 6 new articles",
  "imported_count": 6,
  "total_processed": 6,
  "sources_checked": 4,
  "ai_processed": true
}
```

**Processing:** 
- Fetches articles from external RSS feeds
- Uses Perplexity AI to rewrite content for Cheshire context
- Checks for duplicates before storing
- Takes 10-20 seconds due to AI processing

#### 6. GET /api/feed.xml
**Purpose:** Generate RSS feed from stored articles
**Query Parameters:**
- `category`: Filter by category (optional)
- `limit`: Maximum articles in feed (default: 20, max: 100)

**Response:** XML RSS 2.0 feed
**Content-Type:** application/rss+xml

---

## Database Schema (MongoDB)

### Articles Collection
```javascript
{
  _id: ObjectId,
  title: String (required),
  content: String (required),
  category: String (required), // Local News, Business, Events, Sports, Community
  author: String (default: "AI Journalist"),
  publishedDate: DateTime (required),
  created_at: DateTime (auto),
  updated_at: DateTime (auto),
  image: String (URL),
  tags: Array[String],
  featured: Boolean (default: false),
  source: String (e.g., "Perplexity AI", "BBC England"),
  source_url: String (original article URL, if imported),
  imported: Boolean (default: false),
  ai_processed: Boolean (default: false),
  scope: String // "cheshire" or "uk"
}
```

**Indexes:**
- `category` (ascending)
- `created_at` (descending)
- `tags` (ascending)
- `title + content` (text index for search)

---

## Frontend Components

### 1. Header.jsx
**Purpose:** Main site header with logo and branding
**Features:**
- Cheshire News branding with newspaper icon
- Current date display
- "Powered by AI" indicator

### 2. CategoryNav.jsx
**Purpose:** Category navigation bar
**Features:**
- Sticky navigation
- Category buttons with icons (Newspaper, MapPin, Briefcase, Calendar, Trophy, Users)
- Active category highlighting
- Responsive design

### 3. ArticleCard.jsx
**Purpose:** Display article in card format
**Features:**
- Featured article variant (large, gradient overlay)
- Regular article variant (grid layout)
- Image display
- Category badge
- Author and timestamp
- Tag display
- Click to open detail modal

### 4. RSSPanel.jsx
**Purpose:** RSS management interface
**Features:**
- RSS feed subscription section
  - Display RSS feed URL
  - Copy URL to clipboard
  - View feed button
- RSS import section
  - List available sources
  - Import articles button
  - Loading state during import
  - Success/error notifications
- Information cards about automatic content generation

### 5. App.js
**Purpose:** Main application component
**Features:**
- Article fetching from API
- Category filtering
- Article detail modal
- RSS management sheet (side panel)
- Floating RSS management button
- Loading and error states
- Article grid layout
- Featured article display

---

## Frontend-Backend Integration

### Article Fetching Flow
1. Frontend loads → useEffect triggers fetchArticles()
2. API call to `/api/articles?skip=0&limit=20&category={category}`
3. Response processed and stored in state
4. Articles rendered in grid layout

### RSS Import Flow
1. User clicks "Import Articles Now" in RSS Panel
2. POST request to `/api/import-rss?max_per_source=3&use_ai=true`
3. Backend:
   - Fetches RSS feeds from configured sources
   - Extracts article content
   - Sends to Perplexity AI for rewriting
   - Stores in MongoDB
4. Frontend receives success response
5. Re-fetches articles to display new imports
6. Shows success toast notification

### RSS Feed Generation Flow
1. User clicks "View Feed" button
2. Opens `/api/feed.xml` in new tab
3. Backend:
   - Queries MongoDB for articles
   - Generates RSS 2.0 XML using feedgen
   - Returns XML with proper content-type

---

## AI Integration (Perplexity)

### Automatic Article Generation
**Trigger:** Daily at 6:00 AM (APScheduler)
**Process:**
1. Select Cheshire-specific topics
2. Send prompt to Perplexity API (model: llama-3.1-sonar-small-128k-online)
3. Parse response for headline and content
4. Store in MongoDB with appropriate category and tags

### RSS Article Rewriting
**Trigger:** Manual import via RSS Panel
**Process:**
1. Fetch external RSS article
2. Clean HTML content
3. Send to Perplexity with prompt:
   - Rewrite for Cheshire audience
   - Keep factual and journalistic
   - Target 300 words
   - Provide headline and content
4. Parse AI response
5. Store rewritten article in MongoDB

---

## Environment Variables

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=cheshire_news
PERPLEXITY_API_KEY=pplx-xxxxx
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8001
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## Key Features

### ✅ Implemented
1. **Automatic Content Generation**
   - Daily article generation at 6:00 AM
   - Mix of Cheshire-focused and UK news
   - AI-powered with Perplexity

2. **RSS Feed Consumption**
   - Import from BBC, Chester Chronicle, Business Weekly, Sky Sports
   - AI rewriting for local context
   - Duplicate detection
   - Manual trigger via UI

3. **RSS Feed Publication**
   - Generate RSS 2.0 feed
   - Subscribe via standard RSS readers
   - Category filtering
   - Proper RSS metadata

4. **Article Management**
   - Category-based browsing
   - Featured article display
   - Article detail modal
   - Responsive grid layout

5. **Modern UI/UX**
   - shadcn/ui components
   - Emerald green color theme
   - Smooth transitions and animations
   - Mobile-responsive design
   - Floating action button for RSS management

---

## Data Flow Summary

```
External RSS Feeds
       ↓
   RSS Import API
       ↓
   Perplexity AI (rewrite)
       ↓
   MongoDB Storage
       ↓
   Articles API
       ↓
   React Frontend Display
       ↓
   Generated RSS Feed
       ↓
   RSS Readers/Subscribers
```

---

## Testing Results

### Backend Tests (100% Pass Rate)
- ✅ Article fetching and filtering
- ✅ Perplexity AI integration
- ✅ MongoDB operations
- ✅ RSS import with AI processing
- ✅ RSS feed generation
- ✅ Error handling
- ✅ Data quality verification

### Frontend Tests (100% Pass Rate)
- ✅ Homepage loading and navigation
- ✅ Category filtering
- ✅ RSS management panel
- ✅ RSS import functionality
- ✅ Article detail modal
- ✅ Responsive design

---

## Success Metrics

✅ **Functional Requirements Met:**
- Cheshire-focused news website ✓
- Automatic content generation with Perplexity AI ✓
- RSS feed consumption from external sources ✓
- AI rewriting for local context ✓
- RSS feed publication for subscribers ✓
- Category-based browsing ✓
- Responsive design ✓

✅ **Technical Requirements Met:**
- FastAPI backend ✓
- React frontend with shadcn/ui ✓
- MongoDB database ✓
- Perplexity AI integration ✓
- RSS processing (consume & generate) ✓
- Comprehensive error handling ✓
- Testing coverage ✓
