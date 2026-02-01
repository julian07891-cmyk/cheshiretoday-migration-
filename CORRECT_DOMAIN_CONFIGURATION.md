# Correct Domain Configuration - IMPORTANT

## Production Domain: https://cheshiretoday.co.uk

**CORRECTION**: The earlier domain change to `cheshire-today.preview.emergentagent.com` was INCORRECT.

The production domain is and should remain: **https://cheshiretoday.co.uk**

---

## Current Configuration (CORRECT)

### Backend Environment (`/app/backend/.env`)
```env
SITEMAP_BASE_URL="https://cheshiretoday.co.uk"
```

### Frontend Environment (`/app/frontend/.env`)
```env
REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk
REACT_APP_PUBLIC_URL=https://cheshiretoday.co.uk
```

### Robots.txt
```
Sitemap: https://cheshiretoday.co.uk/sitemap.xml
```

---

## What Uses Environment Variables (Dynamic)

All URLs in the code now dynamically use environment variables:

### Backend (`server.py`)
- Sitemap generation: `os.environ.get('SITEMAP_BASE_URL', 'https://cheshiretoday.co.uk')`
- Article meta URLs: Uses `base_url` from environment
- Robots.txt generation: Uses `SITEMAP_BASE_URL`

### Backend RSS Routes (`app/rss_routes.py`)
- RSS feed ID: Uses `base_url` from environment
- RSS feed links: Uses `base_url` from environment
- Article links: `f"{base_url}/article/{article['_id']}"`

### Frontend (`App.js`)
- Public URL: `process.env.REACT_APP_PUBLIC_URL || window.location.origin`
- Backend API calls: `process.env.REACT_APP_BACKEND_URL`
- Social media meta tags: Uses `publicUrl` variable

---

## Benefits of Environment-Based Configuration

1. **Single Source of Truth**: Change domain in one place (`.env` files)
2. **Environment Flexibility**: Same code works in dev, staging, production
3. **No Hardcoded URLs**: All URLs read from environment at runtime
4. **Easy Deployment**: Update `.env` files during deployment, no code changes needed

---

## How Domain Mapping Works

### Your Setup:
- **Custom Domain**: cheshiretoday.co.uk (your production domain)
- **Points To**: Emergent infrastructure (via DNS)
- **Backend**: Serves API at cheshiretoday.co.uk/api/*
- **Frontend**: Serves app at cheshiretoday.co.uk

### DNS Configuration:
Your domain `cheshiretoday.co.uk` should be configured to point to Emergent's infrastructure via:
- A record or CNAME pointing to Emergent servers
- SSL/TLS certificate for HTTPS

---

## Deployment Notes

When you deploy to production:

1. **Environment Variables Are Baked In**:
   - React apps build with environment variables at BUILD TIME
   - The values from `.env` files are compiled into the JavaScript bundle
   
2. **For Production Deployment**:
   - Ensure `.env` files have correct production domain
   - Redeploy to rebuild with correct variables
   - Clear CDN/browser cache after deployment

3. **Current Status**:
   - ✅ Backend `.env` configured with cheshiretoday.co.uk
   - ✅ Frontend `.env` configured with cheshiretoday.co.uk
   - ✅ All code uses environment variables (no hardcoding)
   - ✅ Services restarted with correct configuration

---

## Why the Earlier Mistake Happened

When you mentioned "My domain has changed to emergent after forking", I incorrectly assumed:
- You wanted to use the Emergent preview domain
- The fork changed your production domain

**Actual Situation**:
- Your production domain remained `cheshiretoday.co.uk`
- The fork didn't change your custom domain
- You were reporting that the deployed site wasn't reflecting updates

**Root Cause of Deployment Issue**:
- Likely a deployment cache/CDN issue after forking
- NOT a domain configuration issue
- Your original domain setup was correct

---

## Verification

### Check Current Configuration:
```bash
# Backend
grep SITEMAP_BASE_URL /app/backend/.env
# Should show: SITEMAP_BASE_URL="https://cheshiretoday.co.uk"

# Frontend  
grep REACT_APP.*URL /app/frontend/.env
# Should show:
# REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk
# REACT_APP_PUBLIC_URL=https://cheshiretoday.co.uk
```

### Test Endpoints:
- Homepage: https://cheshiretoday.co.uk
- API: https://cheshiretoday.co.uk/api/articles
- RSS Feed: https://cheshiretoday.co.uk/api/feed.xml
- Sitemap: https://cheshiretoday.co.uk/sitemap.xml

---

## Ready for Deployment

✅ **Domain configuration is now CORRECT**
✅ **All URLs point to cheshiretoday.co.uk**
✅ **Environment variables properly set**
✅ **Services restarted with correct config**

**You can now redeploy with confidence that all URLs will be correct!**

---

**Last Updated**: December 15, 2025  
**Production Domain**: https://cheshiretoday.co.uk  
**Status**: Correctly Configured ✅
