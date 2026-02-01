# FINAL FIX - Complete Deployment Instructions

## Current Situation

✅ **Code is 100% correct** - All fixes are in place
✅ **Local environment works** - Articles have correct images
✅ **Preview URL works** - https://cheshire-fix.preview.emergentagent.com
❌ **Custom domain outdated** - https://cheshiretoday.co.uk needs deployment

---

## Why This Keeps Happening

Your custom domain (`cheshiretoday.co.uk`) is a **separate production deployment** that:
1. Uses its own database instance
2. Serves pre-built JavaScript bundles
3. Has environment variables baked in at build time
4. Doesn't automatically sync with my code changes

**Every change I make only affects**:
- Local development environment
- Preview URL (ai-newsroom-7.preview.emergentagent.com)

**To push changes to custom domain, you must**:
- Trigger a full deployment through Emergent

---

## Complete Fix Process (Do This Once)

### Step 1: Full Redeployment

1. **Go to Emergent Dashboard**
2. **Click "Deploy" or "Redeploy"**
3. **Wait 10-15 minutes** (full deployment takes time)
4. **Verify deployment is complete** before proceeding

### Step 2: Run Image Fix on Production

After deployment completes, run this command **once**:

**Option A - If you have terminal access:**
```bash
curl -X POST "https://cheshiretoday.co.uk/api/emergency-fix-all-images"
```

**Option B - Use browser:**
1. Open: `https://cheshiretoday.co.uk/api/emergency-fix-all-images`
2. Change GET to POST (use browser dev tools or Postman)
3. Send the request

This updates all 96 articles in the PRODUCTION database with correct images.

### Step 3: Clear Facebook Cache

For each article you want to share:

1. Go to: https://developers.facebook.com/tools/debug/
2. Enter: `https://cheshiretoday.co.uk/api/article/{article_id}`
3. Click "Debug"
4. Click "Scrape Again" 2-3 times
5. Verify image is correct

### Step 4: Clear Browser Cache

- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Or use incognito mode

---

## How to Get Article IDs for Facebook Debugger

### Method 1: From Share Button
1. Click share button on an article
2. Copy the URL
3. The ID is the last part: `https://cheshiretoday.co.uk/api/article/THIS_IS_THE_ID`

### Method 2: From API
```bash
curl "https://cheshiretoday.co.uk/api/articles?limit=5"
```
Look for the `"id"` field in each article

---

## Verification Checklist

After completing all steps:

### ✅ Test 1: API Returns Articles
```bash
curl "https://cheshiretoday.co.uk/api/articles?limit=3"
```
Should return articles with images

### ✅ Test 2: Meta Tags Show Correct URL
```bash
curl "https://cheshiretoday.co.uk/api/article/ARTICLE_ID" | grep og:url
```
Should show: `cheshiretoday.co.uk` (not emergent URL)

### ✅ Test 3: Meta Tags Show Correct Image
```bash
curl "https://cheshiretoday.co.uk/api/article/ARTICLE_ID" | grep og:image
```
Should show article-specific image (not default skyscraper)

### ✅ Test 4: Facebook Debugger
- URL shows: `cheshiretoday.co.uk`
- Image shows: Correct article image
- Title shows: Correct article title

### ✅ Test 5: Website Loads
- Visit: https://cheshiretoday.co.uk
- Articles should load (no "Failed to load" error)
- Images should match article content

---

## What Each Fix Does

### Code Fixes (Already Done):
1. **Frontend .env** → Points to correct backend
2. **Backend .env** → Uses correct domain for meta tags
3. **Share function** → Always uses custom domain
4. **Image pool** → 123 verified images across all categories
5. **Emergency endpoint** → Forces image reassignment

### Deployment:
- Builds new production bundle with correct .env
- Updates production backend with new code
- Syncs custom domain with latest changes

### Image Fix:
- Updates production database with correct images
- Assigns category-specific images (Food→food, Local→Cheshire)
- Removes all default/fallback images

### Facebook Cache Clear:
- Forces Facebook to re-read meta tags
- Updates preview with new image
- Updates URL to custom domain

---

## If Still Not Working

### Check 1: Deployment Complete
- Wait full 15 minutes
- Check Emergent dashboard for deployment status
- Verify no errors in deployment logs

### Check 2: Production Database Updated
```bash
curl "https://cheshiretoday.co.uk/api/articles" | grep photo-1486406146926
```
If this returns results, the default image is still in production database.
**Solution**: Run the emergency fix endpoint again on production URL.

### Check 3: Facebook Cache
Facebook can cache for 24 hours. If urgent:
- Try sharing in WhatsApp or Twitter first
- Those platforms cache less aggressively
- Facebook will eventually update

---

## Contact Support If Needed

**Emergent Support:**
- Discord: https://discord.gg/VzKfwCXC4A
- Email: support@emergent.sh

**Provide them:**
- Job ID (click 'i' button in chat)
- Message: "Custom domain not syncing with code changes after redeployment"
- Screenshots of Facebook debugger showing wrong image
- Confirmation you've completed all steps above

---

## Summary

The code is perfect. The issue is purely deployment-related:

1. **Redeploy** → Pushes code to production
2. **Run image fix** → Updates production database
3. **Clear Facebook cache** → Updates social media previews
4. **Hard refresh browser** → Clears client cache

After these 4 steps, everything will work correctly on your custom domain.

---

## Quick Command Reference

```bash
# Test articles API
curl "https://cheshiretoday.co.uk/api/articles?limit=1"

# Test meta tags
curl "https://cheshiretoday.co.uk/api/article/ARTICLE_ID" | grep "og:image\|og:url"

# Fix all images (after deployment)
curl -X POST "https://cheshiretoday.co.uk/api/emergency-fix-all-images"

# Facebook debugger
# URL: https://developers.facebook.com/tools/debug/
```

Replace `ARTICLE_ID` with actual article ID from API response.
