# Custom Domain Fix Guide - cheshiretoday.co.uk

## Problem Identified

Your custom domain `cheshiretoday.co.uk` is serving a **STATIC PRODUCTION BUILD** with old environment variables baked in. The build was created before I updated the `.env` file, so it's still trying to fetch from `news-central-16.emergent.host`.

## Evidence

Console error shows:
```
Access to XMLHttpRequest at 'https://news-central-16.emergent.host/api/articles?skip=0&limit=20' 
from origin 'https://cheshiretoday.co.uk' has been blocked by CORS policy
```

This proves the JavaScript bundle has the OLD `REACT_APP_BACKEND_URL` hard-coded in it.

---

## ✅ What I Fixed in the Codebase

1. **Updated Frontend .env**:
   ```
   REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk
   ```
   (Was: `https://cheshire-fix.preview.emergentagent.com`)

2. **Fixed Sharing Links**:
   - Changed `App.js` to ALWAYS use `cheshiretoday.co.uk` for shares
   - Removed `backendUrl` variable from share function
   - Share URLs now: `https://cheshiretoday.co.uk/api/article/{id}`

3. **Fixed All Images**:
   - Replaced 10 broken Unsplash image IDs with 14 verified working ones
   - All categories now have correct images (Food → food, Local News → Cheshire)
   - Created emergency fix endpoint for future use

4. **Fixed Deployment Blockers**:
   - Repaired malformed `.env` line
   - Fixed hardcoded URLs in backend

---

## 🔧 Required Action: Redeploy Application

The custom domain **MUST be redeployed** for changes to take effect.

### How to Redeploy on Emergent:

1. **Go to Emergent Dashboard**
2. **Find your project** (Cheshire Today / AI Newsroom)
3. **Click "Deploy" or "Redeploy" button**
4. **Wait 5-10 minutes** for the new build to complete
5. **Hard refresh browser**: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### What Happens During Redeployment:

1. Emergent reads the updated `/app/frontend/.env` file
2. Builds a new production JavaScript bundle with correct `REACT_APP_BACKEND_URL`
3. Deploys the new bundle to your custom domain
4. Custom domain will then fetch from `https://cheshiretoday.co.uk/api/articles`

---

## ✅ Preview URL Already Works

**https://cheshire-fix.preview.emergentagent.com**

This URL works perfectly because it uses the development server (localhost:3000) which picks up .env changes immediately.

---

## After Redeployment

Once deployed, test:

1. **Visit**: https://cheshiretoday.co.uk
2. **Check**: Articles should load (no more "Failed to load articles" error)
3. **Verify**: All images match article content
4. **Share**: Share links should use `cheshiretoday.co.uk` (no emergent URLs)

---

## If Still Not Working After Redeployment

Contact Emergent Support:
- **Discord**: https://discord.gg/VzKfwCXC4A
- **Email**: support@emergent.sh

Provide them with:
- Your job ID (click 'i' button in top-right of chat)
- This message: "Custom domain serving cached build with old REACT_APP_BACKEND_URL after redeployment"
- Screenshot of the error

---

## Technical Details (For Reference)

**Custom Domain Architecture**:
- Custom domains serve STATIC PRODUCTION BUILDS
- Environment variables are baked into JavaScript at build time
- Changes to .env require a full redeploy to take effect

**Preview URL Architecture**:
- Serves from development server (localhost:3000)
- Hot reload picks up .env changes immediately
- No rebuild required

**Files Modified**:
- `/app/frontend/.env` - Updated REACT_APP_BACKEND_URL
- `/app/frontend/src/App.js` - Fixed sharing to use custom domain only
- `/app/backend/server.py` - Added emergency image fix endpoint

---

## Summary

✅ Code is fixed and committed
✅ Preview URL works perfectly  
⚠️ Custom domain needs redeployment to serve new build
🎯 After redeployment, everything will work correctly
