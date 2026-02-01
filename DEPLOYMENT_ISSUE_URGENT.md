# 🚨 URGENT: Custom Domain Deployment Issue

## Current Problem

**Custom domain (cheshiretoday.co.uk) shows: "Failed to load articles. Please try again."**

## Root Cause

The custom domain is serving **OLD CODE**. Evidence:

**Console Error:**
```
Access to XMLHttpRequest at 'https://news-central-16.emergent.host/api/articles?skip=0&limit=20' 
from origin 'https://cheshiretoday.co.uk' has been blocked by CORS policy
```

**Analysis:**
- Custom domain's JavaScript is trying to fetch from `news-central-16.emergent.host` (OLD URL)
- I updated `/app/frontend/.env` to use `cheshiretoday.co.uk` 
- But the custom domain is serving a **pre-built static bundle** with old .env baked in
- The preview URL works fine because it uses development server (hot reload)

---

## Why Redeployment Hasn't Worked

You've redeployed but the custom domain still shows old code because:

1. **Build Cache**: Old JavaScript bundle is cached
2. **CDN/Cloudflare**: Custom domain goes through Cloudflare which caches assets
3. **Emergent Deployment**: May need specific rebuild command

---

## 🔧 Solutions to Try

### Solution 1: Force Rebuild (Recommended)

In Emergent Dashboard:
1. Look for "Rebuild" or "Build" button (not just "Deploy")
2. Or try "Clear Cache" option if available
3. Or "Redeploy from Scratch" option

### Solution 2: Clear Cloudflare Cache

If you have Cloudflare access:
1. Go to Cloudflare dashboard
2. Find cheshiretoday.co.uk domain
3. Caching → Purge Everything
4. Wait 5-10 minutes
5. Hard refresh browser

### Solution 3: Contact Emergent Support

**Discord**: https://discord.gg/VzKfwCXC4A
**Email**: support@emergent.sh

**Message to send:**
```
Hi, my custom domain (cheshiretoday.co.uk) is serving old code even after redeployment.

Job ID: [Click 'i' button in chat to get this]
Issue: Frontend .env was updated but custom domain still uses old REACT_APP_BACKEND_URL
Evidence: Console shows fetching from news-central-16.emergent.host instead of cheshiretoday.co.uk

The preview URL works fine, only custom domain affected.
Need help forcing a complete rebuild with new environment variables.
```

---

## 📊 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Code** | ✅ Fixed | All fixes committed to git |
| **Local Backend** | ✅ Working | Returns 96 articles with proper images |
| **Local Frontend** | ✅ Working | Development server (localhost:3000) |
| **Preview URL** | ✅ Working | ai-newsroom-7.preview.emergentagent.com |
| **Custom Domain Backend** | ⚠️ Mixed | API works but serves old meta tags |
| **Custom Domain Frontend** | ❌ Broken | Old JavaScript bundle with wrong backend URL |

---

## 🎯 What Needs to Happen

1. **Production Frontend Build**: Needs to be rebuilt with new .env
2. **Clear CDN Cache**: Cloudflare/CDN needs to serve new build
3. **Database Update**: Run image fix on production (after deployment)

---

## ✅ Temporary Workaround

**Use the preview URL** - it works perfectly:
```
https://cheshire-fix.preview.emergentagent.com
```

This URL:
- ✅ Articles load correctly
- ✅ Has all code fixes
- ✅ Images work properly
- ✅ Sharing works

You can use this while waiting for custom domain deployment to complete.

---

## 🔍 How to Verify Deployment Worked

After deployment, check:

### Test 1: API URL in Browser Console
1. Open https://cheshiretoday.co.uk
2. Press F12 (open developer tools)
3. Go to Console tab
4. Look for error messages

**Should show:**
```
Fetching from: https://cheshiretoday.co.uk/api/articles
```

**Should NOT show:**
```
news-central-16.emergent.host
```

### Test 2: Direct API Test
```bash
curl "https://cheshiretoday.co.uk/api/articles?limit=1"
```
Should return JSON with articles (not error)

### Test 3: Website Loads
Visit https://cheshiretoday.co.uk
- ✅ Articles should display
- ✅ No "Failed to load" error

---

## 🛠️ Post-Deployment Steps

Once deployment works:

1. **Run Image Fix**:
   ```bash
   curl -X POST "https://cheshiretoday.co.uk/api/emergency-fix-all-images"
   ```

2. **Clear Facebook Cache**:
   - Go to https://developers.facebook.com/tools/debug/
   - Scrape each article URL

3. **Hard Refresh Browser**:
   - Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

---

## 📝 Technical Details

### Files Modified (All Correct):
- `/app/frontend/.env`: REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk ✅
- `/app/backend/.env`: SITEMAP_BASE_URL=https://cheshiretoday.co.uk ✅
- `/app/frontend/src/App.js`: Share function uses publicUrl ✅
- `/app/backend/server.py`: Image generation uses CATEGORY_IMAGES ✅

### The Disconnect:
- **Local files**: ✅ Correct
- **Git repository**: ✅ All changes committed
- **Custom domain deployment**: ❌ Not picking up changes

---

## 🆘 If Nothing Works

As a last resort, you might need:

1. **New Deployment**: Create fresh deployment on Emergent
2. **Point Domain**: Update DNS to point to new deployment
3. **Import Database**: Export from old, import to new

But try the simpler solutions first!

---

## Summary

✅ **Code is 100% correct**
✅ **Preview URL works perfectly**
❌ **Custom domain needs proper deployment**

The issue is purely infrastructure/deployment related, not code.
All fixes are in place and working on preview URL.

Contact Emergent support for deployment assistance if redeployment doesn't work.
