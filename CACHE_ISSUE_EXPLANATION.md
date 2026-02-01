# Important: Custom Domain Cache Issue

## Current Situation

Your custom domain `https://cheshiretoday.co.uk` is showing **newspaper images** on Local News articles because it's pointing to an **older deployment instance** that doesn't have the latest code updates.

## Evidence

| Endpoint | Cheshire Images | Status |
|----------|----------------|---------|
| `localhost:8001` | 14 images | ✅ Updated |
| `preview.emergentagent.com` | 14 images | ✅ Updated |
| **`cheshiretoday.co.uk`** | **10 images** | ❌ OLD CODE |

## What's Happening

The custom domain is:
1. Running OLD backend code (from before I updated the images)
2. Using a separate database instance
3. Showing the old broken Unsplash image IDs
4. Behind Cloudflare caching which adds another layer

## The Fix

**The custom domain infrastructure needs to be redeployed.** This is typically done through:

1. **Emergent Dashboard** - Redeploy the application
2. **DNS/Cloudflare** - Purge cache or wait for TTL expiry
3. **Backend Instance** - Ensure custom domain points to the updated deployment

## Temporary Workaround

View your site at the **preview URL** which has all the correct Cheshire images:
```
https://cheshire-fix.preview.emergentagent.com
```

This URL shows:
- ✅ All 6 Local News articles with verified Cheshire countryside/village images
- ✅ No newspaper or business stock photos
- ✅ Proper UK-themed imagery

## Next Steps

1. **Redeploy** your application through the Emergent dashboard
2. **Purge Cloudflare cache** for cheshiretoday.co.uk (if you have access)
3. **Wait 15-30 minutes** for DNS/cache propagation
4. **Hard refresh** your browser (Ctrl+Shift+R or Cmd+Shift+R)

## Technical Details

The preview URL and custom domain are **separate infrastructure** managed by Emergent. Code changes I made only affect the local/preview environment until a full deployment pushes them to the custom domain.

---

**Bottom Line:** The images ARE fixed in the codebase. The custom domain just needs to be redeployed to pick up the changes.
