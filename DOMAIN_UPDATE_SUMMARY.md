# Domain Update Summary

## Issue
After forking the project, the domain changed from `cheshiretoday.co.uk` to `cheshire-today.preview.emergentagent.com`, but the old domain was hardcoded in multiple places.

## New Domain Configuration
- **Frontend URL**: https://cheshire-fix.preview.emergentagent.com
- **Backend URL**: https://cheshire-fix.preview.emergentagent.com/api

## Files Updated

### 1. Environment Variables (✅ Updated)
- **`/app/backend/.env`**
  - Updated `SITEMAP_BASE_URL` to new domain
  
- **`/app/frontend/.env`**
  - Added `REACT_APP_PUBLIC_URL` for dynamic domain usage

### 2. Frontend Components (✅ Updated)
- **`/app/frontend/src/App.js`**
  - Added `publicUrl` variable using `process.env.REACT_APP_PUBLIC_URL` with fallback to `window.location.origin`
  - Updated HomePage component meta tags to use `publicUrl`
  - Updated ArticlePage component meta tags to use `publicUrl`
  - Updated share URL functionality to use `publicUrl`

- **`/app/frontend/src/components/Header.js`**
  - Changed subdomain text from "cheshiretoday.co.uk" to "Local News & Updates"

### 3. Static Files (✅ Updated)
- **`/app/frontend/public/index.html`**
  - Updated page title (removed domain reference)
  
- **`/app/frontend/public/robots.txt`**
  - Updated sitemap URL to new domain

### 4. Backend (✅ Already Using Environment Variables)
The backend `/app/backend/server.py` was already correctly using:
- `os.environ.get('SITEMAP_BASE_URL')` for sitemap generation
- This now points to the new domain via the .env file

## How It Works Now

### Dynamic Domain Resolution
The application now uses environment variables for domain configuration:

1. **Frontend**: Uses `REACT_APP_PUBLIC_URL` from `.env` file
2. **Backend**: Uses `SITEMAP_BASE_URL` from `.env` file
3. **Fallback**: If env variable is missing, frontend falls back to `window.location.origin`

### Social Media Sharing
All social media meta tags (Open Graph, Twitter Card) now use the dynamic `publicUrl` variable:
- Article sharing: `${publicUrl}/article/${articleId}`
- Homepage sharing: `${publicUrl}`

### Sitemap
The sitemap at `/sitemap.xml` now uses the correct domain from the backend environment variable.

## Testing
✅ Backend API endpoint working with new domain
✅ Frontend loading correctly
✅ Domain displayed as "Local News & Updates" instead of old domain
✅ Environment variables properly configured

## Future Domain Changes
To change the domain in the future, simply update:
1. `/app/backend/.env` → `SITEMAP_BASE_URL`
2. `/app/frontend/.env` → `REACT_APP_PUBLIC_URL`
3. Restart both services: `sudo supervisorctl restart backend frontend`

No code changes required!
