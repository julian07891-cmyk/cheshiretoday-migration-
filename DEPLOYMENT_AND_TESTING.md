# Testing Facebook Integration After Deployment

## ⚠️ IMPORTANT: Test After Deployment

**Why?**
- Facebook Debugger checks your LIVE website at `cheshiretoday.co.uk`
- Changes made here are in development environment (localhost)
- You must deploy these changes to your live site first

---

## Step-by-Step Process

### Step 1: Deploy Your Changes ✅

You need to deploy the updated `/app/frontend/public/index.html` file that now includes:
```html
<meta property="fb:app_id" content="2091422248085004" />
```

**How to Deploy:**
- Use your current deployment method (Git push, FTP, deployment panel, etc.)
- Make sure the frontend build includes the updated index.html
- Wait for deployment to complete (usually 2-5 minutes)

### Step 2: Verify Deployment 🔍

Once deployed, check that the meta tag is live:

**Option A: View Page Source**
1. Go to your live site: `https://cheshiretoday.co.uk/`
2. Right-click → **View Page Source**
3. Search for `fb:app_id`
4. Should see: `<meta property="fb:app_id" content="2091422248085004" />`

**Option B: Use curl (if you have terminal access)**
```bash
curl -s https://cheshiretoday.co.uk/ | grep "fb:app_id"
```

### Step 3: Test with Facebook Debugger 🧪

**Only after deployment is verified:**

1. Go to: https://developers.facebook.com/tools/debug/
2. Enter: `https://cheshiretoday.co.uk/`
3. Click **Debug**
4. Check for errors

---

## If fb:app_id Error Still Appears

### Fix 1: Clear Facebook Cache
1. In Facebook Debugger, click **Scrape Again** button
2. This forces Facebook to fetch fresh data
3. Wait 10 seconds and check again

### Fix 2: Verify App Settings
1. Go to: https://developers.facebook.com/apps/
2. Select your "Cheshire Today" app (ID: 2091422248085004)
3. Go to **Settings → Basic**
4. Verify:
   - **App Domains**: `cheshiretoday.co.uk` (no https://, no www)
   - **Website URL**: `https://cheshiretoday.co.uk/`
   - **Privacy Policy URL**: Add a privacy page URL (required for live apps)
5. Save changes

### Fix 3: Make Sure App is Live
1. In your Facebook App dashboard
2. Top right corner should show **Live** (green)
3. If it shows **Development** (red), toggle it to Live
4. Confirm any prompts

### Fix 4: Check Meta Tag Format
The meta tag should be exactly like this:
```html
<meta property="fb:app_id" content="2091422248085004" />
```

**Common mistakes:**
- ❌ `name="fb:app_id"` (wrong - should be `property`)
- ❌ Missing quotes around the number
- ❌ App ID has typo

---

## Complete Testing Checklist

After deployment, test these:

### ✅ Homepage
- [ ] Go to: https://developers.facebook.com/tools/debug/
- [ ] Test: `https://cheshiretoday.co.uk/`
- [ ] No fb:app_id error
- [ ] Image loads (should show city/business image)
- [ ] Title shows: "Cheshire Today - Local News & Updates"
- [ ] Description appears

### ✅ Article Page
- [ ] Pick an article from your site
- [ ] Copy article URL (e.g., `https://cheshiretoday.co.uk/article/123abc`)
- [ ] Test in Facebook Debugger
- [ ] Article image appears
- [ ] Article title shows correctly
- [ ] No errors

### ✅ Actual Sharing
- [ ] Try posting article link on your Facebook page
- [ ] Image preview should appear automatically
- [ ] Title and description should be correct
- [ ] Click through works

---

## Troubleshooting Common Issues

### Issue: "Object at URL has og:type of 'website'. The property 'fb:app_id' requires an object of og:type 'article'."

**This is just a warning, not an error!**
- Facebook expects `og:type='article'` for article pages
- For homepage, `og:type='website'` is correct
- Safe to ignore for homepage
- Article pages should have `og:type='article'` (which we already do via React Helmet)

### Issue: "Can't Download File"

**Cause:** Facebook can't reach your website
**Solutions:**
1. Check website is actually live and accessible
2. Verify no firewall blocking Facebook's crawler
3. Make sure SSL certificate is valid (https works)
4. Wait a few minutes and try again

### Issue: Wrong Image Still Showing

**Cause:** Facebook has old cached data
**Solutions:**
1. Click **Scrape Again** in debugger
2. Wait 24 hours for cache to fully clear
3. Add a version parameter to image URL if needed

### Issue: Changes Not Appearing

**Cause:** Deployment didn't include the updated file
**Solutions:**
1. Clear browser cache and check live site source
2. Verify deployment was successful
3. Check if you're using CDN (might need cache purge)
4. Re-deploy if necessary

---

## Quick Test Commands

If you have terminal access to your live server:

**Check if meta tag is live:**
```bash
curl -s https://cheshiretoday.co.uk/ | grep -A 1 "fb:app_id"
```

**Check all Open Graph tags:**
```bash
curl -s https://cheshiretoday.co.uk/ | grep "og:" | head -10
```

**Check RSS feed:**
```bash
curl -s https://cheshiretoday.co.uk/api/feed.xml | head -30
```

---

## Expected Results After Deployment

### Facebook Debugger Should Show:

✅ **Open Graph Properties:**
- og:url: https://cheshiretoday.co.uk/
- og:type: website
- og:title: Cheshire Today - Local News & Updates
- og:description: Stay informed with the latest news...
- og:image: [Image URL]
- og:site_name: Cheshire Today
- og:locale: en_GB
- fb:app_id: 2091422248085004

✅ **No Errors:**
- No warnings about missing fb:app_id
- No "Can't Download File" errors
- No invalid meta tag errors

---

## Timeline

1. **Deploy changes**: 5-10 minutes
2. **Verify deployment**: 1 minute
3. **Test in debugger**: 2 minutes
4. **Clear Facebook cache if needed**: 1 minute
5. **Test actual sharing**: 2 minutes

**Total**: About 15-20 minutes

---

## Need Help?

**Deployment Issues:**
- Check with your hosting provider or deployment platform
- Verify files were uploaded correctly
- Check deployment logs for errors

**Facebook Issues:**
- Verify app is in Live mode
- Check app settings are correct
- Make sure website is publicly accessible

**Still stuck?**
- Share the error message from Facebook Debugger
- Check if website is accessible from different networks
- Verify SSL certificate is valid

---

## Summary

**DO THIS ORDER:**
1. ✅ Deploy changes (index.html with fb:app_id)
2. ✅ Verify on live site (view source)
3. ✅ Test with Facebook Debugger
4. ✅ Click "Scrape Again" if needed
5. ✅ Test actual sharing on Facebook

**Don't test before deployment** - Facebook checks the live site, not localhost!

Good luck! 🎉
