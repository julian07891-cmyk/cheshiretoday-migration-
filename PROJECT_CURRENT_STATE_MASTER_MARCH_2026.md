# Cheshire Today – Master Project State
Date: 7 March 2026

--------------------------------------------------
PROJECT OVERVIEW
--------------------------------------------------

Cheshire Today is a hybrid local economic intelligence platform combining:
- Local Cheshire news
- Business & finance coverage
- AI & technology authority
- UK economic and policy news

Stack:

Frontend: React (CRA)
Backend: FastAPI (Python)
Database: MongoDB
Hosting: Render
Domain: cheshiretoday.co.uk
SSL: Active for root and www

--------------------------------------------------
CURRENT LIVE SYSTEM STATUS
--------------------------------------------------

Database:

Total stored articles: 1202
Active articles: 44
Archived articles: 1158

Archive system preserves URLs so shared links remain valid.

Active category mix:

Local News: 18
Business: 12
UK News: 8
Tech: 6

Editorial balance:

Local ≈ 41%
Authority (Business + Tech) ≈ 41%
UK ≈ 18%

Target strategy:

40% Local
40% Authority
20% UK

System currently aligned with strategy.

--------------------------------------------------
CONTENT QUALITY
--------------------------------------------------

Minimum article length rule:

All active articles ≥ 1000 characters.

Previously:

21 short articles detected
21 regenerated via API
1 archived

Current status:

ACTIVE_UNDER_1000 = 0

--------------------------------------------------
HOMEPAGE SYSTEM
--------------------------------------------------

Homepage sections:

Hero
Top Stories
Latest
AI & Business
More Stories
Finance
Property

Features implemented:

Global dedupe
Topic caps
Editorial pool filtering
40/40/20 pillar balancing
Mobile responsive section limits

Mobile behaviour:

Sections collapse to 4 items
Show More toggle enabled

Desktop behaviour:

Larger feed display

Sidebar hidden on mobile to prevent repetition.

--------------------------------------------------
IMPORT SYSTEM
--------------------------------------------------

Hybrid RSS importer operational.

Sources include:

Cheshire Live
BBC
Liverpool Echo
Regional feeds
Google News regional queries

Import pipeline includes:

Duplicate title detection
Duplicate image prevention
Auto archive cleanup
Image reuse control
Hybrid AI rewrite option

Scheduled imports:

06:00
12:00
18:00

Target active pool:

55–70 articles.

--------------------------------------------------
ARCHIVE SYSTEM
--------------------------------------------------

Articles automatically archived when pool grows too large.

Archive protects:

existing URLs
SEO links
shared content.

--------------------------------------------------
DEPLOYMENT STATUS
--------------------------------------------------

Production hosting: Render

Frontend service deployed
Backend service deployed

Domain connected:

cheshiretoday.co.uk
www.cheshiretoday.co.uk

SSL active.

--------------------------------------------------
PROJECT WORKFLOW RULES
--------------------------------------------------

Development workflow:

Check current state before any modification.
Apply changes via terminal commands only.
No manual editing inside files.
One command per step.
Verify system state after each change.

Local verification method:

npm run build
npx serve -s build

Do NOT use npm start.

--------------------------------------------------
NEXT PHASE TASKS
--------------------------------------------------

1. Newsletter system

SMTP activation
Newsletter testing
Subject-line optimisation strategy

2. Monetisation

Affiliate blocks
Affiliate networks integration
Commerce guides system

3. AI content

Perplexity article generation tests
Evergreen article production

4. SEO improvements

Structured data
Schema markup
Internal linking optimisation

--------------------------------------------------
SYSTEM OPERATING MODE
--------------------------------------------------

Current recommendation:

Stop major structural changes.
Allow scheduled imports to run.
Maintain active pool between 55–70.
Focus on monetisation and growth.

--------------------------------------------------
END OF FILE
--------------------------------------------------
