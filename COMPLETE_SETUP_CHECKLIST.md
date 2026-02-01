# Complete Setup Checklist - Cheshire Today

## 🎯 Overview
This is your complete, step-by-step setup guide. Follow each section in order for best results.

---

## ✅ STEP 1: Google AdSense Setup (Revenue: £100-500/month)

### Time Required: 15 minutes + 1-2 weeks approval

### A. Apply for AdSense

**1.1 - Visit AdSense**
```
Open browser: https://www.google.com/adsense
Click: "Get Started"
```

**1.2 - Sign In**
- Use your Google account (Gmail)
- If you don't have one, create a Google account first

**1.3 - Enter Website Details**
```
Website URL: https://cheshiretoday.co.uk
Email: your-email@gmail.com
Country: United Kingdom
```

**1.4 - Accept Terms**
- Read the terms and conditions
- Check "I accept" box
- Click "Start using AdSense"

**1.5 - Add Payment Information**
```
Account type: Individual (or Business if you have a company)
Name and address: Your details
Select: Direct bank transfer (BACS)
Add: Your UK bank account details
Tax information: Fill in as required
```

### B. Site Verification (Already Done!)

Your site already has the verification code in place. ✅

### C. Wait for Approval

- Google will review your site
- Typical wait: 1-2 weeks
- You'll receive email when approved
- If rejected, they'll tell you why

### D. After Approval - Add Your Publisher ID

**When approved, you'll get an email with your Publisher ID.**

**Format:** `ca-pub-1234567890123456`

**Add it to your site:**

**Step 1:** Connect to your server
```bash
cd /app/frontend
```

**Step 2:** Edit .env file
```bash
nano .env
```

**Step 3:** Find this line:
```
REACT_APP_ADSENSE_ID=ca-pub-0000000000000000
```

**Step 4:** Replace with your real ID:
```
REACT_APP_ADSENSE_ID=ca-pub-1234567890123456
```

**Step 5:** Save and restart
```bash
# Save file (Ctrl+O, Enter, Ctrl+X)
cd /app
sudo supervisorctl restart frontend
```

### E. Create Ad Units

**In your AdSense dashboard:**

**1. Go to:** Ads → By ad unit → "+ New ad unit"

**2. Create these 4 ad units:**

**Ad Unit 1: Header Banner**
```
Name: Cheshire-Header-Banner
Type: Display ad
Size: Responsive
Save and get code
Copy: Data-ad-slot="1234567890" (your actual number)
```

**Ad Unit 2: Sidebar**
```
Name: Cheshire-Sidebar
Type: Display ad
Size: Responsive (recommended: 300x600)
Save and get code
Copy: Data-ad-slot="0987654321"
```

**Ad Unit 3: In-Article**
```
Name: Cheshire-In-Article
Type: In-article
Automatic size
Save and get code
Copy: Data-ad-slot="5555555555"
```

**Ad Unit 4: Between Articles**
```
Name: Cheshire-Between-Articles
Type: Display ad
Size: Responsive (recommended: 300x250)
Save and get code
Copy: Data-ad-slot="7777777777"
```

**3. Keep these slot IDs** - you'll use them later when placing ads on your site.

---

## ✅ STEP 2: Google Analytics Access (Already Setup!)

### Time Required: 5 minutes

**Your Analytics is already tracking!** ✅

**Measurement ID:** `G-Q1NZLJC50D`

### Access Your Data:

**Step 1:** Visit https://analytics.google.com

**Step 2:** Sign in with your Google account
- Use the same account that created the property

**Step 3:** View your data
- Click on "Reports" in left menu
- See: Realtime, Users, Traffic sources

### What You Can See:

**Real-time:**
- Current visitors on site
- What pages they're viewing
- Where they're from

**Reports:**
- Daily/weekly/monthly traffic
- Popular articles
- Traffic sources (Google, Facebook, direct)
- Device types (mobile, desktop)
- Geographic location

### Pro Tip:
Check analytics daily to see what content performs best!

---

## ✅ STEP 3: Email Newsletter Setup (Revenue: Newsletter sponsorships)

### Time Required: 20 minutes

### Option A: Resend (Recommended - FREE for 3,000 emails/month)

**Step 1: Sign Up**
```
Visit: https://resend.com
Click: "Start Building"
Sign up with: Google or Email
```

**Step 2: Verify Your Email**
- Check your inbox
- Click verification link

**Step 3: Add Your Domain**
```
Dashboard → Domains → Add Domain
Enter: cheshiretoday.co.uk
```

**Step 4: Add DNS Records**

Resend will show you DNS records to add. You need to add these to your domain registrar:

**Where to add:** Your domain registrar (e.g., GoDaddy, Namecheap, Google Domains)

**Records to add:**
```
Type: TXT
Host: @
Value: [Resend will provide this]

Type: CNAME
Host: resend._domainkey
Value: [Resend will provide this]

Type: MX
Host: @
Value: [Resend will provide this]
```

**Step 5: Wait for Verification**
- DNS changes take 1-24 hours
- Resend will auto-verify
- You'll get email when ready

**Step 6: Get API Key**
```
Dashboard → API Keys → Create API Key
Name: Cheshire Today Newsletter
Permissions: Full Access (or Sending Access)
Click: Create
Copy the key (starts with: re_...)
```

**IMPORTANT:** Copy this key immediately! You can't see it again.

**Step 7: Add to Your Server**

```bash
cd /app/backend
nano .env
```

Add these lines:
```bash
RESEND_API_KEY=re_your_actual_key_here
RESEND_FROM_EMAIL=newsletter@cheshiretoday.co.uk
RESEND_FROM_NAME=Cheshire Today
```

Save and restart:
```bash
sudo supervisorctl restart backend
```

**Step 8: Install Resend Library**

```bash
cd /app/backend
pip install resend
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add resend email library"
```

### Option B: SendGrid (Alternative - FREE for 100 emails/day)

**Step 1: Sign Up**
```
Visit: https://sendgrid.com/free
Sign up for free account
```

**Step 2: Verify Email**
- Check inbox
- Click verification link

**Step 3: Create Sender Identity**
```
Settings → Sender Authentication → Get Started
Choose: Domain Authentication
Enter: cheshiretoday.co.uk
```

**Step 4: Add DNS Records**
(Similar to Resend - add records to your domain registrar)

**Step 5: Create API Key**
```
Settings → API Keys → Create API Key
Name: Cheshire Today
Access: Full Access
Copy the key (starts with: SG.)
```

**Step 6: Add to Server**
```bash
cd /app/backend
nano .env
```

Add:
```bash
SENDGRID_API_KEY=SG.your_actual_key_here
SENDGRID_FROM_EMAIL=newsletter@cheshiretoday.co.uk
```

**Step 7: Install SendGrid**
```bash
pip install sendgrid
pip freeze > requirements.txt
```

---

## ✅ STEP 4: Social Media Auto-Posting (Traffic Growth)

### Time Required: 15 minutes per platform

### A. Facebook Page Setup

**Step 1: Create Facebook Page**
```
Visit: https://www.facebook.com/pages/create
Category: News & Media Website
Name: Cheshire Today
Description: Your trusted source for local Cheshire news
```

**Step 2: Add Information**
```
Website: https://cheshiretoday.co.uk
Email: contact@cheshiretoday.co.uk
Location: Cheshire, UK
Add profile photo (your logo)
Add cover photo (Cheshire landscape)
```

**Step 3: Publish Your Page**

### B. Twitter/X Account

**Step 1: Create Account**
```
Visit: https://twitter.com/signup
Username: @CheshireToday (or CheshireTodayNews if taken)
Name: Cheshire Today
Bio: Local news from Cheshire, UK 📰 | Updates 3x daily
```

**Step 2: Customize Profile**
- Add profile picture (logo)
- Add header image (Cheshire banner)
- Add website link

### C. Auto-Posting with IFTTT (FREE)

**Step 1: Sign Up for IFTTT**
```
Visit: https://ifttt.com/join
Sign up: Free account
```

**Step 2: Connect Facebook**
```
IFTTT → Services → Facebook Pages
Click: Connect
Authorize: Allow IFTTT access
Select: Your Cheshire Today page
```

**Step 3: Create RSS to Facebook Applet**

```
Click: Create
If This: RSS Feed
Trigger: New feed item
Feed URL: https://cheshiretoday.co.uk/api/feed.xml
Then That: Facebook Pages
Action: Create a link post
Page: Cheshire Today
Message: {{EntryTitle}}
Link: {{EntryUrl}}
Photo URL: Leave blank (will auto-fetch)
Click: Continue → Finish
```

**Step 4: Create RSS to Twitter Applet**

```
Click: Create
If This: RSS Feed
Trigger: New feed item
Feed URL: https://cheshiretoday.co.uk/api/feed.xml
Then That: Twitter
Action: Post a tweet
Tweet: {{EntryTitle}} {{EntryUrl}} #CheshireNews #LocalNews
Click: Continue → Finish
```

**Step 5: Enable Applets**
- Both should be "On" by default
- Check activity log to see posts

---

## ✅ STEP 5: Google Search Console (SEO)

### Time Required: 10 minutes

**Step 1: Add Property**
```
Visit: https://search.google.com/search-console
Click: Add Property
Choose: URL prefix
Enter: https://cheshiretoday.co.uk
```

**Step 2: Verify Ownership**

**Method 1: HTML Tag (Easiest)**
- Google will give you a meta tag
- Already in your site! ✅

**Method 2: DNS**
- Add TXT record to your domain
- Use if HTML tag doesn't work

**Step 3: Submit Sitemap**
```
In Search Console:
Click: Sitemaps (left menu)
Enter: https://cheshiretoday.co.uk/sitemap.xml
Click: Submit
```

**Step 4: Monitor**
- Check for crawl errors
- Monitor indexing status
- View search performance

---

## ✅ STEP 6: Local Business Outreach (Direct Ads Revenue)

### Time Required: 1-2 hours/week

### Target Businesses:

**Cheshire Estate Agents:**
- Gascoigne Halman
- David Lewis
- Wright Marshall
- Savills Wilmslow

**Restaurants & Pubs:**
- Local gastropubs
- Chester restaurants
- Knutsford cafes

**Car Dealerships:**
- Bentley Crewe
- Local used car dealers
- Auto repair shops

**Local Services:**
- Plumbers
- Electricians
- Landscapers
- Home improvement

### Outreach Template:

**Email Subject:** Advertise to Thousands of Local Cheshire Readers

**Email Body:**
```
Hi [Business Name],

I'm reaching out from Cheshire Today (cheshiretoday.co.uk), 
a growing local news website serving the Cheshire community.

We're now offering advertising opportunities to local businesses 
who want to reach engaged Cheshire residents.

Our Audience:
• Growing monthly visitors
• 3 daily content updates
• Focus on Cheshire & Golden Triangle area

Advertising Options:
• Display banner ads (from £100/month)
• Sponsored articles (from £150/article)
• Newsletter sponsorship (from £75/newsletter)

View details: https://cheshiretoday.co.uk/advertise

Would you be interested in a quick call to discuss how we can 
help [Business Name] reach more local customers?

Best regards,
[Your Name]
Cheshire Today
advertising@cheshiretoday.co.uk
```

### Follow-Up Plan:

**Day 1:** Send initial email
**Day 3:** Follow up if no response
**Day 7:** Final follow-up
**Move on** if still no response

**Target:** Contact 10-20 businesses per week

---

## ✅ STEP 7: Newsletter Campaign Setup

### Time Required: 30 minutes/week

### A. Create Newsletter Template

**Weekly Digest Structure:**

```
Subject: This Week in Cheshire - [Date]

Header:
- Cheshire Today logo
- "Your weekly digest of local news"

Content Sections:
1. Top Story of the Week
   - Featured image
   - Headline
   - Summary (2-3 sentences)
   - "Read More" link

2. Around Cheshire (5-6 articles)
   - Brief headlines with links
   
3. Coming Up Next Week
   - Events
   - What to watch for

4. Sponsored Section (if applicable)
   - Ad from local business

Footer:
- Unsubscribe link
- Contact info
- Social media links
```

### B. Sending Schedule

**Option 1: Weekly Digest**
- Every Friday at 9 AM
- Summary of top stories

**Option 2: Daily Brief**
- Every morning at 7 AM
- Top 3 stories of the day

**Start with:** Weekly (easier to manage)

### C. Growing Your List

**Promotion Ideas:**
- Pop-up on website after 30 seconds
- Exit-intent pop-up
- Mention in social media posts
- QR codes for local events
- Include in "Advertise With Us" page

---

## 📊 QUICK REFERENCE - ALL ACCOUNTS

### Google Services:
```
AdSense: https://adsense.google.com
Analytics: https://analytics.google.com
Search Console: https://search.google.com/search-console
```

### Email Service:
```
Resend: https://resend.com/dashboard
OR
SendGrid: https://app.sendgrid.com
```

### Social Media:
```
Facebook: https://business.facebook.com
Twitter: https://twitter.com/home
IFTTT: https://ifttt.com/home
```

### Your Site:
```
Main Site: https://cheshiretoday.co.uk
Sitemap: https://cheshiretoday.co.uk/sitemap.xml
RSS Feed: https://cheshiretoday.co.uk/api/feed.xml
Advertise: https://cheshiretoday.co.uk/advertise (when routing added)
```

---

## 📋 IMPLEMENTATION TIMELINE

### Week 1:
- [ ] Apply for Google AdSense
- [ ] Access Google Analytics
- [ ] Set up Resend/SendGrid
- [ ] Create Facebook page

### Week 2:
- [ ] Create Twitter account
- [ ] Set up IFTTT auto-posting
- [ ] Submit to Google Search Console
- [ ] Contact first 10 businesses

### Week 3-4:
- [ ] Wait for AdSense approval
- [ ] Send first newsletter
- [ ] Continue business outreach
- [ ] Monitor analytics

### Month 2:
- [ ] Add AdSense Publisher ID
- [ ] Optimize ad placements
- [ ] Scale business outreach
- [ ] Grow newsletter list

---

## 🆘 WHO TO CONTACT FOR HELP

### Google AdSense Issues:
```
Help Center: https://support.google.com/adsense
Forum: https://support.google.com/adsense/community
Email: Through AdSense dashboard only
```

### Resend Support:
```
Docs: https://resend.com/docs
Email: support@resend.com
Discord: https://discord.gg/resend
```

### IFTTT Support:
```
Help: https://help.ifttt.com
Forum: https://help.ifttt.com/hc/en-us/community/topics
```

---

## ✅ COMPLETION CHECKLIST

### Essential (Do First):
- [ ] Applied for Google AdSense
- [ ] Accessing Google Analytics
- [ ] Email service configured (Resend/SendGrid)
- [ ] API key added to backend/.env

### Important (Do Soon):
- [ ] Facebook page created
- [ ] Twitter account created
- [ ] IFTTT auto-posting set up
- [ ] Google Search Console submitted

### Revenue Generation (Ongoing):
- [ ] First 10 businesses contacted
- [ ] First newsletter sent
- [ ] AdSense Publisher ID added (when approved)
- [ ] Ad placements optimized

---

## 🎯 EXPECTED RESULTS

### Week 1-2:
- Setup complete
- Accounts created
- Waiting for approvals

### Month 1:
- AdSense approved
- First revenue: £10-50
- Newsletter: 50-100 subscribers
- Traffic: Growing

### Month 3:
- AdSense: £50-150
- Direct ads: First sale
- Newsletter: 200-500 subscribers
- Total revenue: £100-400

### Month 6:
- AdSense: £150-300
- Direct ads: £500-1,000
- Newsletter sponsors: £200-300
- Total revenue: £850-1,600

---

**Everything you need is here. Follow step by step and you'll be monetized within weeks!** 🚀💰
