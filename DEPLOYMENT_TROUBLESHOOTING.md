# Deployment Troubleshooting Guide - Web Not Updating

## Issue
Application deployed successfully but web interface is not showing the updated version.

---

## Common Causes & Solutions

### 1. Browser Cache (Most Common) 🔄
**Problem**: Your browser is showing the old cached version of the site.

**Solutions**:
- **Hard Refresh**: Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- **Clear Browser Cache**:
  - Chrome: Settings → Privacy and Security → Clear browsing data → Cached images and files
  - Firefox: Settings → Privacy & Security → Cookies and Site Data → Clear Data
  - Safari: Safari → Clear History → All History
- **Incognito/Private Mode**: Open the site in a private/incognito window
- **Different Browser**: Try opening the site in a different browser

### 2. Service Worker Cache 🔧
**Problem**: Service worker is serving old cached content.

**Solution**:
1. Open Developer Tools (F12)
2. Go to Application tab (Chrome) or Storage tab (Firefox)
3. Click on "Service Workers"
4. Click "Unregister" for your domain
5. Reload the page

### 3. CDN/Proxy Cache 🌐
**Problem**: Emergent's CDN or proxy is caching the old version.

**Solutions**:
- Wait 5-10 minutes for cache to expire
- Check if Emergent has a cache purge option in the dashboard
- Add a cache-busting query parameter: `https://your-site.com/?v=2`

### 4. Frontend Not Rebuilt 🏗️
**Problem**: Changes were made but frontend wasn't rebuilt for production.

**Check**:
```bash
# Check if build directory exists and is recent
ls -la /app/frontend/build/
```

**Solution (if needed)**:
```bash
# Rebuild the frontend
cd /app/frontend
yarn build

# Or use npm if that's what you're using
npm run build
```

### 5. Environment Variables Not Updated 🔐
**Problem**: Deployed environment has old environment variables.

**Check**:
- Verify `REACT_APP_BACKEND_URL` points to correct production URL
- Verify `REACT_APP_PUBLIC_URL` is set correctly

**Current Values**:
```
REACT_APP_BACKEND_URL=https://cheshire-fix.preview.emergentagent.com
REACT_APP_PUBLIC_URL=https://cheshire-fix.preview.emergentagent.com
```

**Note**: React apps bake environment variables into the build at build time, not runtime!

### 6. Build Cache Issue 🗂️
**Problem**: Webpack/build cache serving old content.

**Solution**:
```bash
cd /app/frontend
# Clear build cache
rm -rf node_modules/.cache
rm -rf build

# Clean install and rebuild
yarn install
yarn build
```

---

## Verification Steps

### Step 1: Check Deployed Version
1. Open your deployed site
2. Open Developer Tools (F12)
3. Go to Console tab
4. Look for any errors
5. Check Network tab to see what files are being loaded

### Step 2: Verify API Connection
Open Console and run:
```javascript
fetch(window.location.origin + '/api/articles?limit=1')
  .then(r => r.json())
  .then(d => console.log('API Working:', d))
  .catch(e => console.error('API Error:', e))
```

### Step 3: Check Build Version
Look at the HTML source:
- Right-click → View Page Source
- Check if the JavaScript bundle names include hashes (good sign of fresh build)
- Look for environment-specific configurations

### Step 4: Compare Local vs Deployed
1. Test the same URL locally: `http://localhost:3000`
2. Test the deployed URL: `https://cheshire-fix.preview.emergentagent.com`
3. Compare the behavior and console logs

---

## Emergency Fix: Force Complete Rebuild

If nothing else works, force a complete rebuild and redeploy:

```bash
# 1. Clean everything
cd /app/frontend
rm -rf node_modules
rm -rf build
rm -rf node_modules/.cache

# 2. Reinstall dependencies
yarn install

# 3. Rebuild production bundle
yarn build

# 4. Restart services
sudo supervisorctl restart frontend backend

# 5. Clear local browser cache
# Then hard refresh (Ctrl+Shift+R)
```

---

## Specific Issues for This Application

### Newsletter Subscription
**What changed**: Newsletter subscription backend and frontend implemented
**To verify**: 
1. Scroll to footer
2. Try subscribing with an email
3. Check if loading state appears
4. Check if success message shows

### Domain Update
**What changed**: Domain changed from `cheshiretoday.co.uk` to `cheshire-today.preview.emergentagent.com`
**To verify**:
1. Check header - should show "Local News & Updates" not old domain
2. Check RSS feed - should use new domain
3. Check social sharing URLs - should use new domain

### Image Fallback
**What changed**: Added fallback handlers for broken images
**To verify**:
1. Check if article images load
2. No broken image icons should appear

---

## Deployment-Specific Checks

### For Emergent Deployments:

1. **Check Deployment Status**:
   - Verify deployment completed successfully in Emergent dashboard
   - Check deployment logs for errors
   - Confirm all pods are running

2. **Check Environment Variables**:
   - Verify environment variables are set in deployment config
   - React variables must be set at BUILD time, not runtime

3. **Check Build Process**:
   - Emergent should run `yarn build` during deployment
   - Verify build completed without errors
   - Check build logs for warnings

4. **Check Service Endpoints**:
   - Backend: `https://cheshire-fix.preview.emergentagent.com/api/articles`
   - Frontend: `https://cheshire-fix.preview.emergentagent.com`
   - Health check: `https://cheshire-fix.preview.emergentagent.com/health`

---

## Quick Diagnostic Checklist

- [ ] Hard refresh browser (Ctrl+Shift+R)
- [ ] Clear browser cache completely
- [ ] Try incognito/private mode
- [ ] Try different browser
- [ ] Check browser console for errors
- [ ] Verify API endpoint is accessible
- [ ] Wait 10 minutes (CDN cache timeout)
- [ ] Check deployment logs for errors
- [ ] Verify environment variables are correct
- [ ] Confirm build completed successfully

---

## Still Not Working?

If you've tried all the above and the site still shows old content:

1. **Contact Emergent Support**:
   - Provide your app name/URL
   - Mention you've cleared browser cache
   - Ask them to purge CDN cache for your application

2. **Check Deployment Logs**:
   - Look for build errors
   - Check if deployment actually completed
   - Verify no rollback occurred

3. **Verify Network**:
   - Use `curl` to check raw response
   - Compare headers between local and deployed
   - Check if Content-Type headers are correct

---

## Prevention for Future Deployments

1. **Always clear cache after deployment**
2. **Use versioned asset names** (Webpack does this automatically)
3. **Set proper cache headers** for static assets
4. **Test in incognito mode** immediately after deployment
5. **Keep deployment logs** for debugging

---

**Last Updated**: December 15, 2025  
**For**: Cheshire News Application
