# MacBook Cache & Display Issues - Fix Guide

## Issue 1: Works on Phone, Not on MacBook

This is a **cache issue**! Your MacBook has old cached data.

---

## Quick Fixes for MacBook

### Fix 1: Hard Refresh (Try This First!) ⚡
1. Open the site on MacBook: `https://cheshiretoday.co.uk/`
2. **Hard refresh:**
   - **Safari**: `Cmd + Option + R`
   - **Chrome**: `Cmd + Shift + R`
   - **Firefox**: `Cmd + Shift + R`
3. If that doesn't work, try: `Cmd + Shift + Delete` to clear cache

### Fix 2: Clear Browser Cache Completely 🧹

**Chrome on Mac:**
1. Click **Chrome** menu → **Clear Browsing Data**
2. Time range: **All time**
3. Check: ✓ Cached images and files
4. Click **Clear data**
5. Restart Chrome

**Safari on Mac:**
1. Click **Safari** menu → **Preferences**
2. Go to **Advanced** tab
3. Check: ✓ Show Develop menu
4. Click **Develop** menu → **Empty Caches**
5. Or press: `Option + Cmd + E`
6. Restart Safari

**Firefox on Mac:**
1. Click **Firefox** menu → **Preferences**
2. Privacy & Security → **Cookies and Site Data**
3. Click **Clear Data**
4. Check: ✓ Cached Web Content
5. Click **Clear**

### Fix 3: Private/Incognito Window 🕵️
1. Open Private/Incognito window
2. Visit: `https://cheshiretoday.co.uk/`
3. Should work! (This proves it's a cache issue)

### Fix 4: Different Browser 🌐
- Try **Safari** if using Chrome
- Try **Chrome** if using Safari
- Try **Firefox**
- If works in another browser → cache issue in first browser

### Fix 5: DNS Cache (Advanced) 💻
Sometimes MacOS DNS cache causes issues:

```bash
# Open Terminal and run:
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

Enter your Mac password when prompted.

---

## Issue 2: Blue Square with "?" (Broken Images)

This means images aren't loading. Several possible causes:

### Cause A: Browser Extension Blocking Images
**Ad blockers or privacy extensions might block images**

**Check:**
1. Disable browser extensions temporarily
2. Refresh page
3. If images appear → one of your extensions was blocking them

**Common culprits:**
- AdBlock Plus
- uBlock Origin
- Privacy Badger
- Ghostery

**Fix:**
- Whitelist `cheshiretoday.co.uk`
- Whitelist `images.unsplash.com`

### Cause B: Safari Image Loading Settings

**Safari might have image loading disabled:**

1. **Safari** → **Preferences**
2. Go to **Websites** tab
3. Select **Auto-Play** or **Content Blockers**
4. Make sure images are allowed for your site

### Cause C: Network/VPN Issues

**If using VPN or corporate network:**
- Corporate networks sometimes block external images
- Try disabling VPN temporarily
- Try on different network (mobile hotspot)

### Cause D: Old Cached Broken Images

**Browser cached a 404 error:**

1. Open Chrome DevTools: `Cmd + Option + I`
2. Go to **Network** tab
3. Check "Disable cache" checkbox
4. Refresh page
5. Look for red/failed image requests

---

## Testing Images on MacBook

### Test 1: Open Image Directly
1. Copy an article image URL:
   ```
   https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&h=500&fit=crop
   ```
2. Paste in browser address bar
3. Press Enter
4. Should show the image

**If image doesn't show:**
- Your Mac/browser is blocking Unsplash
- Network/firewall issue

### Test 2: Check Browser Console
1. Open DevTools: `Cmd + Option + I`
2. Go to **Console** tab
3. Look for errors in red
4. Common errors:
   - `CORS error` → Need to fix headers
   - `404 Not Found` → Image URL broken
   - `net::ERR_BLOCKED_BY_CLIENT` → Extension blocking

### Test 3: Check Network Tab
1. Open DevTools: `Cmd + Option + I`
2. Go to **Network** tab
3. Filter by **Img**
4. Refresh page
5. Look for failed (red) image requests
6. Click failed request to see why it failed

---

## Fix Broken Images in Code

If some specific images are broken, we need to update the image URLs.

Let me check which articles have broken images and replace them.

---

## Common Symptoms & Solutions

### Symptom: All images broken on MacBook only
**Solution:** Clear browser cache (Fix 1-3 above)

### Symptom: Some images broken on all devices
**Solution:** Those specific image URLs are dead, need replacement

### Symptom: Images work in Incognito but not normal browser
**Solution:** Clear cache or disable extensions

### Symptom: Images show on mobile data but not WiFi
**Solution:** Network/firewall blocking Unsplash, try VPN

### Symptom: Blue square with ? on some articles
**Solution:** Those specific images need replacing

---

## Emergency Image Fix

If images keep breaking, we can host images locally:

**Option 1: Use Local Images**
1. Download images to `/app/frontend/public/images/`
2. Update article generation to use local paths
3. No dependency on external services

**Option 2: Use Different CDN**
- Pexels: https://www.pexels.com/
- Pixabay: https://pixabay.com/
- Your own image server

**Option 3: Fallback Image**
Add a default fallback when image fails to load.

---

## Quick Diagnostic

Run these checks:

**1. Test in Safari:**
- Safari treats cache differently than Chrome
- If works in Safari but not Chrome → Chrome cache issue

**2. Test with WiFi off:**
- Use mobile hotspot
- If works → network blocking issue

**3. Check Mac firewall:**
```bash
# Check if firewall is blocking
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

**4. Check Mac security settings:**
- System Preferences → Security & Privacy
- Check if any content filtering is enabled

---

## Recommended Steps (In Order)

Do these steps in order until it works:

1. ✅ Hard refresh: `Cmd + Shift + R`
2. ✅ Clear browser cache completely
3. ✅ Try Incognito/Private window
4. ✅ Try different browser
5. ✅ Disable browser extensions
6. ✅ Flush DNS cache (Terminal command above)
7. ✅ Restart Mac
8. ✅ Try different network

**Most likely:** Step 1-3 will fix it!

---

## Still Not Working?

**Share this info:**
1. Which browser? (Chrome/Safari/Firefox)
2. Browser version?
3. Any extensions installed?
4. Does it work in Incognito?
5. Does it work in different browser?
6. Screenshot of browser console errors

This will help me identify the exact issue!

---

## Prevention

**To avoid this in the future:**

1. **Clear cache regularly**
   - Chrome: `Cmd + Shift + Delete` weekly
   
2. **Use Incognito for testing**
   - Always test deploys in Incognito first
   
3. **Keep browser updated**
   - Outdated browsers cause weird issues

4. **Check extensions**
   - Some extensions break websites
   - Disable suspicious ones

Good luck! 🍀
