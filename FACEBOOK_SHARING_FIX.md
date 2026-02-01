# Facebook Sharing Fix - Removing Emergent URLs

## Problem

When you share articles on Facebook, it shows `news-central-16-replaced...emergent.host` URL instead of `cheshiretoday.co.uk`.

## Root Cause

1. **Backend not updated on custom domain**: The production deployment has old `SITEMAP_BASE_URL` environment variable
2. **Facebook cache**: Facebook caches meta tags and won't update until you tell it to rescrape

---

## ✅ Code Fixes (Already Done)

1. **Backend .env** - Set `SITEMAP_BASE_URL="https://cheshiretoday.co.uk"`
2. **Frontend .env** - Set `REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk`
3. **Frontend App.js** - Share URLs now use `cheshiretoday.co.uk` only

**Verified**: Local backend returns correct meta tags:
```html
<meta property="og:url" content="https://cheshiretoday.co.uk/article/...">
```

---

## 🚨 Step 1: Redeploy Application

1. Go to **Emergent Dashboard**
2. Click **"Deploy"** or **"Redeploy"**
3. Wait 5-10 minutes for deployment to complete

This will push the updated backend with correct `SITEMAP_BASE_URL` to your custom domain.

---

## 🚨 Step 2: Clear Facebook Cache (CRITICAL)

After redeployment, Facebook will STILL show old URLs until you force it to rescrape.

### Use Facebook Sharing Debugger:

1. **Go to**: https://developers.facebook.com/tools/debug/

2. **Enter your article URL**:
   ```
   https://cheshiretoday.co.uk/api/article/{article_id}
   ```
   Example: `https://cheshiretoday.co.uk/api/article/6940f5707a28e43909ed4c72`

3. **Click "Debug"** button

4. **Click "Scrape Again"** button (may need to click 2-3 times)

5. **Verify**: The preview should now show:
   - ✅ URL: `https://cheshiretoday.co.uk/article/...`
   - ❌ NOT: `news-central-16-replaced...emergent.host`

### Important Notes:

- You need to do this for EACH article URL you've shared before
- New shares after redeployment will work automatically
- Facebook caches meta tags for 7-30 days, so rescraping is essential

---

## 🚨 Step 3: Verify Fix

After redeployment and Facebook cache clearing:

1. **Test meta tags directly**:
   ```bash
   curl https://cheshiretoday.co.uk/api/article/YOUR_ARTICLE_ID | grep og:url
   ```
   Should show: `https://cheshiretoday.co.uk/article/...`

2. **Share on Facebook**:
   - Use the native share button on your site
   - OR copy article URL and paste in Facebook
   - Preview should show `cheshiretoday.co.uk`

3. **Click shared link**:
   - Should open on cheshiretoday.co.uk (not emergent URL)

---

## Why This Happened

### Architecture:
- **Custom Domain**: Serves from production deployment with environment variables baked in
- **Preview URL**: Serves from development environment (updates immediately)

### The Issue:
1. Old deployment had `SITEMAP_BASE_URL` pointing to emergent URL
2. I updated the .env file in code
3. Custom domain still runs old deployment until you redeploy
4. Facebook cached the old meta tags

---

## Quick Reference

### URLs to Use:

✅ **Share URL** (for social media):
```
https://cheshiretoday.co.uk/api/article/{article_id}
```

✅ **User-facing URL** (for direct access):
```
https://cheshiretoday.co.uk/article/{article_id}
```

❌ **Never use**:
```
https://cheshire-fix.preview.emergentagent.com
https://news-central-16-replaced...emergent.host
```

---

## After Fix is Complete

✅ All new shares will use `cheshiretoday.co.uk`
✅ Meta tags will show correct URL
✅ Facebook/Twitter/LinkedIn will display proper preview
✅ Clicking shared links opens on your domain

---

## Testing Checklist

After redeployment and Facebook cache clear:

- [ ] Backend meta tags show cheshiretoday.co.uk (test with curl)
- [ ] Facebook debugger shows correct URL
- [ ] New Facebook share displays cheshiretoday.co.uk
- [ ] Clicking shared link opens on cheshiretoday.co.uk
- [ ] Article images display correctly
- [ ] No emergent URLs visible anywhere

---

## Support

If issues persist after following all steps:

**Facebook Sharing Debugger**: https://developers.facebook.com/tools/debug/
**Emergent Support Discord**: https://discord.gg/VzKfwCXC4A
**Emergent Support Email**: support@emergent.sh

Provide them:
- Job ID (click 'i' button in chat)
- Screenshot of Facebook debugger showing wrong URL
- Confirmation that you've redeployed and rescraped

---

## Technical Details

**Meta Tags Endpoint**: `/api/article/{article_id}`
- This endpoint serves server-rendered HTML with Open Graph meta tags
- Facebook, Twitter, LinkedIn crawlers read these tags
- Users get redirected to React app for actual viewing

**Environment Variables**:
- `SITEMAP_BASE_URL`: Used for meta tag URLs (backend)
- `REACT_APP_BACKEND_URL`: Used for API calls (frontend)
- `REACT_APP_PUBLIC_URL`: Used for share URLs (frontend)

**All three MUST be**: `https://cheshiretoday.co.uk`
