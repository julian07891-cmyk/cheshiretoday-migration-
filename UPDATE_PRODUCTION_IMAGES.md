# Production Image Update Guide

## 🎯 Purpose
This guide explains how to update Local News articles with Cheshire-specific images after deployment.

## 🔍 The Issue
- **Development database** (local): Has Cheshire images ✅
- **Production database** (deployed): Has generic images ❌

When you deploy, the code is updated but the production database articles remain unchanged.

## ✅ Solution: Call the Update Endpoint

### Step 1: Deploy Your Application
First, deploy the application normally. This will update the backend code with the new Cheshire image configuration.

### Step 2: Call the Update Endpoint

#### Using curl:
```bash
curl -X POST https://cheshiretoday.co.uk/api/update-local-news-images
```

#### Using your browser:
Open your browser's Developer Console (F12) and run:
```javascript
fetch('https://cheshiretoday.co.uk/api/update-local-news-images', {
    method: 'POST'
})
.then(response => response.json())
.then(data => console.log(data));
```

#### Expected Response:
```json
{
  "success": true,
  "message": "Successfully updated 7 Local News articles with Cheshire-specific images",
  "articles_updated": 7,
  "total_local_news": 7,
  "cheshire_images_available": 10,
  "sample_updates": [...]
}
```

### Step 3: Verify the Update
1. Visit https://cheshiretoday.co.uk
2. Look at Local News articles
3. Confirm they show Cheshire/UK village and countryside images

## 📋 What This Endpoint Does

### Safety Features:
- ✅ Only updates **Local News** category (leaves other categories untouched)
- ✅ Uses pre-configured Cheshire-specific images
- ✅ Handles cycling through images if there are more articles than images
- ✅ Returns detailed report of what was updated

### Cheshire Images Used:
1. English countryside villages
2. UK village streets
3. English countryside landscapes
4. English village houses
5. UK town centers
6. English high streets
7. UK countryside scenes
8. British buildings
9. UK village scenes
10. English town views

## 🔄 Alternative: Wait for Auto-Update

If you prefer not to call the endpoint, new articles will automatically have Cheshire images:
- Articles are generated **3 times daily** (6 AM, 12 PM, 6 PM)
- Old articles are cleaned up automatically
- Within **2-3 days**, all articles will naturally have Cheshire images

## 🆘 Troubleshooting

### "No articles updated"
- Check if there are Local News articles in the database
- Verify the endpoint URL is correct

### "Still seeing generic images"
- Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)
- Wait a few seconds for CDN to update
- Try in an incognito window

### "Error 404"
- Make sure you've deployed the latest code first
- Verify the backend service is running

## 📊 Monitoring

After calling the endpoint, you can verify by checking:
```bash
curl https://cheshiretoday.co.uk/api/articles?category=Local%20News&limit=5
```

Look for image URLs containing these Unsplash photo IDs:
- `1599974331560` - English countryside village
- `1590182844668` - UK village street
- `1584530782379` - English countryside
- `1542566604` - English village houses
- `1565008576549` - UK town center
- `1551918120` - English high street
- `1533837937449` - UK countryside
- `1513151233558` - British buildings
- `1576858574144` - UK village scene
- `1527489377706` - English town

## ✅ Success Criteria

All Local News articles should have:
- ✅ UK/Cheshire-specific imagery
- ✅ No generic international city images
- ✅ Appropriate local context images
- ✅ Unique images (no duplicates)

---

**Note:** This endpoint is safe to call multiple times. It will simply reassign Cheshire images each time.
