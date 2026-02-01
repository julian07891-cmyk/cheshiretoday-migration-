# Facebook Sharing Debug Checklist

## Current Issue
- fb:app_id error still appearing
- No image showing in shared link

---

## Step-by-Step Debugging

### 1. Verify Deployment ✅

**Check if changes are live:**
```bash
curl -s https://cheshiretoday.co.uk/ | grep -i "fb:app_id"
```

**Should see:**
```html
<meta property="fb:app_id" content="2091422248085004" />
```

If you don't see this, **the deployment hasn't completed yet** or the file wasn't included.

---

### 2. Test Image URL Directly 🖼️

Open this URL in your browser:
```
https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&h=630&fit=crop&auto=format
```

**Should show:** A city/business image

**If image doesn't load:**
- The URL might be blocked
- Try a different image URL

---

### 3. Facebook App Settings Check ⚙️

Go to: https://developers.facebook.com/apps/2091422248085004/settings/basic/

**Verify these settings:**

| Setting | Required Value |
|---------|---------------|
| App Domains | `cheshiretoday.co.uk` (NO https://, NO www) |
| Website URL | `https://cheshiretoday.co.uk` |
| App Status | **Live** (green toggle, NOT Development) |
| Privacy Policy URL | Must have a valid URL |

**How to check App Status:**
- Top right corner of Facebook App dashboard
- Should show green "Live" badge
- If red "Development", click to toggle to Live

**Why Privacy Policy matters:**
- Facebook requires this for Live apps
- If missing, app stays in Development mode
- Create a simple privacy page: `https://cheshiretoday.co.uk/privacy`

---

### 4. Clear ALL Facebook Caches 🧹

Facebook has multiple cache layers. Clear them all:

**A. Sharing Debugger**
1. Go to: https://developers.facebook.com/tools/debug/
2. Enter: `https://cheshiretoday.co.uk/`
3. Click **Debug**
4. Click **Scrape Again** (do this 2-3 times)
5. Wait 30 seconds between each scrape

**B. Clear Your Browser Cache**
1. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Or clear all browser cache

**C. Try Incognito/Private Window**
- Test in a fresh private browser window
- This ensures no local cache interference

---

### 5. Common Facebook Errors & Fixes

#### Error: "fb:app_id is missing"

**Possible causes:**
1. ❌ **App is in Development mode**
   - Fix: Toggle to "Live" in app dashboard
   
2. ❌ **Domain not added to App Domains**
   - Fix: Add `cheshiretoday.co.uk` in App Settings

3. ❌ **Meta tag has typo**
   - Fix: Should be `property="fb:app_id"` NOT `name="fb:app_id"`

4. ❌ **Changes not deployed**
   - Fix: Re-deploy and verify

#### Error: "Can't Download Image"

**Possible causes:**
1. ❌ **Image URL not accessible**
   - Test: Open image URL directly in browser
   - Fix: Use a different image if it doesn't load

2. ❌ **Image too small**
   - Minimum: 200x200 pixels
   - Recommended: 1200x630 pixels
   - Fix: Use larger image

3. ❌ **Image not HTTPS**
   - Fix: Use `https://` not `http://`

4. ❌ **Image format not supported**
   - Supported: JPG, PNG, GIF, WebP
   - Fix: Use standard format

#### Error: "Circular Redirect"

**Possible causes:**
1. ❌ **www vs non-www redirect loop**
   - Fix: Choose one (recommend non-www) and stick to it

2. ❌ **HTTP to HTTPS redirect issue**
   - Fix: Ensure proper SSL redirect in server config

---

### 6. Alternative Image Solutions

If Unsplash images aren't working, try these:

**Option A: Upload to Your Server**
1. Download a good quality image (1200x630)
2. Upload to: `/app/frontend/public/og-image.jpg`
3. Update meta tag: `content="https://cheshiretoday.co.uk/og-image.jpg"`
4. Re-deploy

**Option B: Use Different CDN**
Try this tested image:
```html
<meta property="og:image" content="https://picsum.photos/1200/630" />
```

**Option C: Use Your Own Article Image**
Pick an article with a good image, test with that URL

---

### 7. Test in Multiple Ways

**Test 1: Facebook Sharing Debugger**
- URL: https://developers.facebook.com/tools/debug/
- Input: `https://cheshiretoday.co.uk/`
- Result: Should show image preview

**Test 2: Actual Facebook Post**
1. Go to your Facebook page
2. Create new post
3. Paste: `https://cheshiretoday.co.uk/`
4. Wait 5-10 seconds
5. Image should appear automatically

**Test 3: Messenger**
1. Send link to yourself in Facebook Messenger
2. Link preview should show image

**Test 4: LinkedIn/Twitter**
- Test on other platforms to see if issue is Facebook-specific
- LinkedIn: https://www.linkedin.com/post-inspector/
- Twitter: Should work automatically

---

### 8. Check Server Headers

Facebook's crawler needs proper headers:

**Test your server:**
```bash
curl -I https://cheshiretoday.co.uk/
```

**Should see:**
```
HTTP/2 200
Content-Type: text/html
```

**Problems if you see:**
- `403 Forbidden` - Server blocking Facebook
- `500 Server Error` - Server misconfiguration
- `404 Not Found` - Site not accessible

---

### 9. Whitelist Facebook Crawler

If you have a firewall or security plugin:

**Facebook's User Agents:**
```
facebookexternalhit/1.1
Facebot
```

**Add to whitelist/allow list:**
- Firewall rules
- Cloudflare (if using)
- Security plugins
- Rate limiting exceptions

---

### 10. Wait Period

Sometimes Facebook just needs time:

**Timeline:**
- **Immediate**: Meta tags visible in debugger
- **5-10 minutes**: Image cache may need refresh
- **24 hours**: Full cache expiry
- **48 hours**: Complete propagation

**If nothing works after 48 hours:**
- Double-check all steps above
- Consider reaching out to Facebook Developer Support

---

## Quick Diagnostic Commands

If you have server access:

**Check meta tags:**
```bash
curl -s https://cheshiretoday.co.uk/ | grep -E "(fb:app_id|og:image)" | head -10
```

**Simulate Facebook crawler:**
```bash
curl -A "facebookexternalhit/1.1" -s https://cheshiretoday.co.uk/ | grep "og:image"
```

**Test image accessibility:**
```bash
curl -I "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&h=630&fit=crop"
```

---

## Still Not Working?

### Create a Test Page

Create a simple test HTML file to verify Facebook can see your content:

**File: test-og.html**
```html
<!DOCTYPE html>
<html>
<head>
    <meta property="fb:app_id" content="2091422248085004" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://cheshiretoday.co.uk/test-og.html" />
    <meta property="og:title" content="Test Page - Cheshire Today" />
    <meta property="og:description" content="This is a test page to verify Facebook Open Graph" />
    <meta property="og:image" content="https://picsum.photos/1200/630" />
</head>
<body>
    <h1>Test Page</h1>
    <p>If this shows an image in Facebook, your server is fine.</p>
</body>
</html>
```

Upload this file and test: `https://cheshiretoday.co.uk/test-og.html`

If THIS works but your main site doesn't, the issue is with your React app routing or build.

---

## React-Specific Issues

Since you're using React:

**Problem:** Facebook can't execute JavaScript
**Solution:** All OG tags must be in static HTML (/public/index.html)

**Verify:**
1. Check `/app/frontend/public/index.html` has all meta tags
2. Don't rely on React Helmet for initial share
3. Build your app: `yarn build`
4. Deploy the built files

---

## Contact Info

If all else fails:

**Facebook Developer Support:**
- https://developers.facebook.com/support/

**Provide them with:**
- Your App ID: 2091422248085004
- Your URL: https://cheshiretoday.co.uk/
- Screenshot of error from debugger
- What you've tried

---

## Success Checklist

Once working, you should see:

✅ No fb:app_id error in Facebook Debugger
✅ Image appears in debugger preview
✅ Title shows correctly
✅ Description appears
✅ When posting to Facebook, link preview appears automatically
✅ Image is clear and properly sized
✅ Clicking preview goes to your site

Good luck! 🍀
