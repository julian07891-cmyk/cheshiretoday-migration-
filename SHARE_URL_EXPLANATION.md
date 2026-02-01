# Social Media Sharing - URL Explanation

## Current Behavior

### Share URL (What users copy/share)
```
https://cheshire-fix.preview.emergentagent.com/api/article/{article_id}
```

### Displayed URL (What users see on social media)
```
https://cheshiretoday.co.uk/article/{article_id}
```

## Why Two Different URLs?

### Technical Requirement
- Kubernetes ingress routes all non-`/api` paths to the frontend (React app)
- Only `/api/*` paths are routed to the backend
- Social media crawlers need SERVER-RENDERED meta tags (not JavaScript-generated)
- The backend endpoint `/api/article/{id}` serves these meta tags

### What Happens When You Share

1. **User clicks Share button** → Copies `preview.emergentagent.com/api/article/{id}`
2. **User pastes on Facebook/Twitter** → Facebook's crawler visits that URL
3. **Facebook reads meta tags** → Finds `og:url: cheshiretoday.co.uk/article/{id}`
4. **Facebook displays** → Shows the clean production domain URL
5. **User clicks link** → Redirected to main cheshiretoday.co.uk site

### Result
✅ Social media posts show: `cheshiretoday.co.uk/article/{id}`  
✅ Article-specific images display correctly  
✅ Clicking the link takes users to your website

## Alternative Solution (Requires Infrastructure Change)

To use production domain directly in share URLs, you would need:

1. **Configure Kubernetes Ingress** to route `/article/{id}` paths to backend (port 8001)
2. **Update DNS/CDN settings** if custom routing is needed
3. **Modify deployment configuration** to handle non-API backend endpoints

This requires infrastructure/DevOps changes beyond the application code.

## Current Implementation Benefits

✅ **Works immediately** - No infrastructure changes needed  
✅ **Article-specific images** - Each share shows correct image  
✅ **SEO-friendly** - og:url points to production domain  
✅ **User experience** - Social media displays production domain  

## Testing Confirmation

Test any article's share URL in [Facebook Debugger](https://developers.facebook.com/tools/debug/):
- The URL to test: `preview.emergentagent.com/api/article/{id}`
- The displayed og:url: `cheshiretoday.co.uk/article/{id}` ✅
- The displayed image: Article-specific unique image ✅
