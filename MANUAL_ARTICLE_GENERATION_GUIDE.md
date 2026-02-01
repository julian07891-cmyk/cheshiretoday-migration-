# Manual Article Generation Guide

## 🎯 Overview
This guide explains how to manually trigger article generation on your Cheshire Today website.

**Important:** This application does NOT use IFTTT. IFTTT documentation was removed from the project. Instead, we have direct API endpoints for manual control.

---

## 📱 How to Manually Generate Articles

### Option 1: Using Browser Console (Easiest)

**Step 1:** Open your website
- Go to https://cheshiretoday.co.uk

**Step 2:** Open Developer Console
- Press `F12` on your keyboard
- Or right-click → "Inspect" → "Console" tab

**Step 3:** Run this command:
```javascript
fetch('https://cheshiretoday.co.uk/api/trigger-daily-generation', {
    method: 'POST'
})
.then(response => response.json())
.then(data => console.log('✅ Success:', data))
.catch(error => console.error('❌ Error:', error));
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Daily article generation triggered successfully"
}
```

---

### Option 2: Using curl Command

Open terminal and run:
```bash
curl -X POST https://cheshiretoday.co.uk/api/trigger-daily-generation
```

---

### Option 3: Import from RSS Feeds

If you want to import articles from specific RSS sources:

```javascript
fetch('https://cheshiretoday.co.uk/api/import-rss?max_per_source=5&use_ai=true', {
    method: 'POST'
})
.then(response => response.json())
.then(data => console.log('✅ RSS Import:', data));
```

**Parameters:**
- `max_per_source`: How many articles per RSS feed (1-10)
- `use_ai`: Use Perplexity AI to rewrite articles (true/false)
- `category`: Optional - filter by category (e.g., "Local News")

---

## ⏰ Automatic Generation Schedule

Articles are automatically generated **3 times per day**:
- **6:00 AM** - Morning update
- **12:00 PM** - Midday update
- **6:00 PM** - Evening update

You don't need to trigger manually unless you want articles immediately.

---

## 🔧 Available Endpoints

### Article Generation:
- `POST /api/trigger-daily-generation` - Generate new articles now

### RSS Management:
- `GET /api/rss-sources` - List all RSS feed sources
- `POST /api/import-rss` - Import articles from RSS feeds
- `GET /api/feed.xml` - View your site's RSS feed output

### Image Management:
- `POST /api/update-local-news-images` - Update Local News with Cheshire images
- `POST /api/reassign-all-images` - Fix duplicate images site-wide

---

## 📊 What Happens When You Trigger Generation

1. **Fetch RSS Feeds** - Pulls latest articles from 33+ UK news sources
2. **AI Processing** - Perplexity AI rewrites articles for Cheshire context
3. **Image Assignment** - Assigns unique, category-appropriate images
4. **Database Update** - Stores articles in MongoDB
5. **Auto Cleanup** - Removes articles older than 50 (keeps site fresh)

---

## ❌ IFTTT Information

**IFTTT is NOT integrated with this application.**

Previous documentation mentioned IFTTT, but it has been removed. The application uses:
- Direct API endpoints (as shown above)
- Scheduled automatic generation (3x daily)
- RSS feed integration for content sourcing

If you want to use IFTTT, you would need to:
1. Create an IFTTT account at ifttt.com
2. Set up a webhook applet
3. Point it to: `https://cheshiretoday.co.uk/api/trigger-daily-generation`
4. Configure it to send a POST request

**But this is optional** - the site already auto-generates articles 3 times daily!

---

## 🔍 Verify Articles Were Generated

After triggering, check:
```bash
curl https://cheshiretoday.co.uk/api/articles?limit=5
```

Or visit your website and refresh the page.

---

## ⚠️ Important Notes

### Rate Limits:
- Don't trigger more than once per hour
- Perplexity API has usage limits
- Each trigger generates ~10-15 new articles

### Cleanup:
- Old articles (beyond 50 most recent) are automatically deleted
- This keeps your site fresh and prevents database bloat

### Images:
- New articles automatically get unique images
- Local News articles get Cheshire-specific images
- If you see duplicates, run `/api/reassign-all-images`

---

## 🆘 Troubleshooting

### "Error 500" Response
- Check Perplexity API key in backend/.env
- Verify MongoDB is running
- Check backend service logs

### "No new articles"
- RSS feeds might not have new content
- AI might be rate-limited
- Check that generation actually ran successfully

### "Duplicate images"
- Run: `POST /api/reassign-all-images`
- This will fix any duplicates automatically

---

## 📞 Quick Reference

**Manual trigger (browser):**
```javascript
fetch('https://cheshiretoday.co.uk/api/trigger-daily-generation', {method: 'POST'})
.then(r => r.json()).then(console.log);
```

**Manual trigger (terminal):**
```bash
curl -X POST https://cheshiretoday.co.uk/api/trigger-daily-generation
```

**Fix duplicates:**
```bash
curl -X POST https://cheshiretoday.co.uk/api/reassign-all-images
```

**Update Local News images:**
```bash
curl -X POST https://cheshiretoday.co.uk/api/update-local-news-images
```

---

**Remember:** Articles auto-generate 3x daily, so manual triggering is rarely needed!
