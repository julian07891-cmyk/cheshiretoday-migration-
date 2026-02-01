# Social Media Sharing Guide for Cheshire Today

## How Sharing Works

When you click the "Share" button on any article, the app creates a share URL:
```
https://cheshiretoday.co.uk/article/{article_id}
```

This URL is specially designed to work with social media platforms like Facebook, Twitter, and LinkedIn.

## Behind the Scenes

### For Social Media Crawlers (Facebook, Twitter, etc.)
1. When Facebook visits `cheshiretoday.co.uk/article/{id}`
2. The backend serves SERVER-RENDERED HTML with complete meta tags:
   - Article title
   - Article description
   - Article image (full resolution)
   - Production domain URL
   - Facebook App ID

### For Regular Users
1. When a human clicks the link
2. JavaScript detects it's not a crawler
3. Redirects to the main React app
4. Article loads normally in the website

## Testing Your Shares

### Method 1: Facebook Sharing Debugger (Recommended)
1. Share any article using the share button
2. Copy the URL from the native share menu
3. Go to: https://developers.facebook.com/tools/debug/
4. Paste the URL
5. Click "Debug"
6. You should see:
   - ✅ Article title
   - ✅ Article image (unique to that article)
   - ✅ Article description
   - ✅ Domain: cheshiretoday.co.uk

### Method 2: Direct Testing
Test the endpoint directly:
```bash
curl https://cheshiretoday.co.uk/article/{article_id}
```

You should see HTML with meta tags like:
```html
<meta property="og:title" content="Your Article Title" />
<meta property="og:image" content="https://images.unsplash.com/..." />
<meta property="og:url" content="https://cheshiretoday.co.uk/article/{id}" />
```

## Common Issues & Solutions

### Issue 1: Facebook Shows Wrong Image
**Cause:** Facebook cached an old version
**Solution:** 
1. Use Facebook Sharing Debugger
2. Click "Scrape Again" button
3. Facebook will fetch fresh meta tags

### Issue 2: Seeing emergent.host URL
**Cause:** Browser redirect or old cache
**Solution:**
1. Clear browser cache
2. Hard refresh (Ctrl+F5)
3. Try in incognito mode
4. The share URL should be: cheshiretoday.co.uk/article/{id}

### Issue 3: Image Not Showing
**Cause:** Article doesn't have an image assigned
**Solution:** All 97 articles now have unique images - should not occur

## Mobile Native Share Menu

On smartphones, clicking "Share" opens your phone's native share menu with:
- ✅ Direct sharing to any app (WhatsApp, Twitter, Email, etc.)
- ✅ Clean URL: cheshiretoday.co.uk/article/{id}
- ✅ Article title and preview text included

## Desktop Sharing

On desktop browsers:
- ✅ URL copied to clipboard automatically
- ✅ Toast notification confirms copy
- ✅ Paste the URL anywhere to share

## For Developers

### Share URL Format
```javascript
const shareUrl = `${publicUrl}/article/${selectedArticle.id}`;
// Example: https://cheshiretoday.co.uk/article/693ff85ce036951c4180bd2f
```

### Backend Endpoint
- Route: `GET /article/{article_id}`
- Returns: Server-rendered HTML with Open Graph meta tags
- No `/api` prefix needed for social crawlers
- Registered at both `/article` and `/api/article` for flexibility

### Meta Tags Included
- og:type
- og:url
- og:title
- og:description
- og:image
- og:image:secure_url
- og:image:width
- og:image:height
- og:site_name
- fb:app_id
- twitter:card
- twitter:title
- twitter:description
- twitter:image

## Verification Checklist

Before reporting issues, verify:
- [ ] Deployed latest version
- [ ] Cleared browser cache
- [ ] Tested in Facebook Debugger
- [ ] Checked Share URL format (should be cheshiretoday.co.uk/article/{id})
- [ ] Confirmed article has an image in database
- [ ] Tried "Scrape Again" in Facebook Debugger

## Support

If issues persist after following this guide:
1. Check backend logs for errors
2. Verify article exists in database
3. Test backend endpoint directly
4. Check CORS configuration
5. Verify SSL certificate is valid
