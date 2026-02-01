# Social Media Sharing - Logo & Preview Setup

## ✅ Configuration Complete!

Your Cheshire Today website now has proper social media preview cards configured. When you share links, they will display:
- Your logo image
- Website title: "Cheshire Today - Local News & Updates"
- Description: "Stay informed with the latest news from Cheshire and across the UK"

## What Was Added

### Open Graph Tags (Facebook, LinkedIn, WhatsApp)
```html
<meta property="og:type" content="website" />
<meta property="og:url" content="https://cheshiretoday.co.uk/" />
<meta property="og:title" content="Cheshire Today - Local News & Updates" />
<meta property="og:description" content="Stay informed with the latest news..." />
<meta property="og:image" content="https://cheshiretoday.co.uk/logo.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:site_name" content="Cheshire Today" />
```

### Twitter Card Tags (X/Twitter)
```html
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:url" content="https://cheshiretoday.co.uk/" />
<meta name="twitter:title" content="Cheshire Today - Local News & Updates" />
<meta name="twitter:description" content="Stay informed with the latest news..." />
<meta name="twitter:image" content="https://cheshiretoday.co.uk/logo.png" />
```

## How to Test

### Test on Facebook

**Option 1: Facebook Sharing Debugger (Best)**
1. Go to: https://developers.facebook.com/tools/debug/
2. Enter: `https://cheshiretoday.co.uk`
3. Click "Debug"
4. See preview of how it will look
5. Click "Scrape Again" if logo doesn't show

**Option 2: Actually Share**
1. Post on Facebook: `https://cheshiretoday.co.uk`
2. Logo should appear automatically
3. If not, wait 24 hours and try "Scrape Again" in debugger

### Test on Twitter/X

**Option 1: Twitter Card Validator**
1. Go to: https://cards-dev.twitter.com/validator
2. Enter: `https://cheshiretoday.co.uk`
3. Click "Preview card"
4. See how it looks on Twitter

**Option 2: Actually Tweet**
1. Create tweet with: `https://cheshiretoday.co.uk`
2. Logo preview should appear automatically
3. If not, check Twitter Card Validator

### Test on LinkedIn

**Option 1: LinkedIn Post Inspector**
1. Go to: https://www.linkedin.com/post-inspector/
2. Enter: `https://cheshiretoday.co.uk`
3. Click "Inspect"
4. See preview

**Option 2: Actually Share**
1. Create LinkedIn post with your URL
2. Logo should appear
3. If not, use Post Inspector to refresh

### Test on WhatsApp

1. Send link to yourself: `https://cheshiretoday.co.uk`
2. Logo preview should appear
3. WhatsApp uses Open Graph tags

### Test on Slack

1. Paste link in any Slack channel
2. Preview should unfurl automatically
3. Shows logo, title, description

## What Each Platform Shows

### Facebook
- **Image:** Your logo (1200x630px recommended)
- **Title:** Cheshire Today - Local News & Updates
- **Description:** Your description
- **URL:** cheshiretoday.co.uk
- **Large preview card**

### Twitter/X
- **Image:** Your logo
- **Title:** Cheshire Today - Local News & Updates  
- **Description:** Your description
- **Card type:** Large image (summary_large_image)

### LinkedIn
- **Image:** Your logo
- **Title:** Cheshire Today - Local News & Updates
- **Description:** Your description
- **Professional preview card**

### WhatsApp
- **Image:** Small logo thumbnail
- **Title:** Cheshire Today - Local News & Updates
- **Description:** First line of description

## Troubleshooting

### Logo Not Showing?

**Issue 1: Cache - Most Common**
Social media platforms cache previews for 24-48 hours.

**Solutions:**
1. Use platform debugger tools (listed above)
2. Click "Scrape Again" or "Refresh"
3. Wait 24-48 hours
4. Try sharing different URL (with ?v=2 at end)

**Issue 2: Image Size**
Your AI-generated logo is large (1.4MB). Social platforms prefer smaller images.

**Recommendation:**
- Optimal size: 1200x630px
- File size: Under 1MB
- Format: PNG or JPG

**Issue 3: Domain Not Live**
If using preview URL instead of cheshiretoday.co.uk, social platforms won't find the logo.

**Solution:**
- Ensure custom domain is fully configured
- Test: Open https://cheshiretoday.co.uk in browser
- Should show your site, not preview page

### Title or Description Wrong?

**Check meta tags:**
```bash
curl https://cheshiretoday.co.uk | grep "og:title"
```

Should show your title. If not, frontend might not have restarted.

### Different Preview on Different Platforms?

**Normal behavior:**
- Facebook: Uses og:image (can be large)
- Twitter: Uses twitter:image (prefers 2:1 ratio)
- LinkedIn: Uses og:image
- WhatsApp: Uses og:image (shows small thumbnail)

**Your current config works for all platforms!**

## Customization Options

### Change Logo Image

**Option 1: Replace existing logo**
```bash
# Replace /app/frontend/public/logo.png with new image
# Must be absolute URL in production
```

**Option 2: Use different image for social sharing**
Create a social-specific image:
1. Design 1200x630px image with logo + text
2. Save as: `/app/frontend/public/social-preview.png`
3. Update meta tags to use: `https://cheshiretoday.co.uk/social-preview.png`

### Change Title/Description per Page

**For individual articles (future enhancement):**
```html
<meta property="og:title" content="Article Title Here" />
<meta property="og:description" content="Article excerpt..." />
<meta property="og:image" content="Article featured image URL" />
```

This would make each article share with its own title and image.

### Add Author Information

**For Twitter:**
```html
<meta name="twitter:creator" content="@CheshireToday" />
<meta name="twitter:site" content="@CheshireToday" />
```

Replace with your actual Twitter handle.

## Best Practices

### Image Guidelines

**Facebook:**
- Recommended: 1200 x 630px
- Minimum: 600 x 315px
- Aspect ratio: 1.91:1
- Max file size: 8MB

**Twitter:**
- Recommended: 1200 x 675px (for large card)
- Minimum: 300 x 157px
- Aspect ratio: 2:1
- Max file size: 5MB

**LinkedIn:**
- Recommended: 1200 x 627px
- Aspect ratio: 1.91:1
- Max file size: 5MB

**Your current logo works for all, but consider:**
- Creating 1200x630px optimized social image
- Include website name text
- Use brand colors (emerald green)
- Clear, readable even when small

### Text Guidelines

**Title:**
- Max 60-70 characters (for best display)
- Includes brand name
- Current: "Cheshire Today - Local News & Updates" ✅

**Description:**
- Max 155-160 characters
- Clear value proposition
- Call to action
- Current: Good length ✅

## Testing Checklist

Before sharing widely:

- [ ] Test on Facebook Debugger
- [ ] Test on Twitter Card Validator
- [ ] Test on LinkedIn Post Inspector
- [ ] Actually share on Facebook (private post)
- [ ] Actually tweet (public or private)
- [ ] Share in WhatsApp (personal chat)
- [ ] Share in Slack
- [ ] Check logo appears clearly
- [ ] Check title is correct
- [ ] Check description is correct
- [ ] Check URL is clickable

## Analytics Tracking

**Monitor social sharing:**

In Google Analytics:
1. Go to: Acquisition → Social
2. See: Which platforms drive traffic
3. Track: Social sharing impact

**Track sharing buttons (future feature):**
Add share buttons to articles to:
- Make sharing easier
- Track share counts
- Encourage viral spread

## Common Questions

**Q: Why doesn't my logo show immediately?**
A: Social platforms cache previews. Use debugger tools to force refresh, or wait 24-48 hours.

**Q: Can I use different images for different articles?**
A: Yes! Future enhancement - add dynamic Open Graph tags per article with article-specific images.

**Q: Does this work for all social media?**
A: Yes! Open Graph is standard across: Facebook, LinkedIn, WhatsApp, Slack, Discord, Reddit, Pinterest, and more.

**Q: Do I need Twitter account to show previews?**
A: No! Twitter Card tags work without account. But having @CheshireToday account helps for tracking.

**Q: How do I add share buttons?**
A: Future enhancement. Can add share buttons to each article for easy one-click sharing.

**Q: Will old shares update with new logo?**
A: No. Old shares are cached. New shares will show new logo. Can force refresh using debugger tools.

## Next Steps

### Immediate:
1. **Test all platforms** using validator tools
2. **Share on your social accounts**
3. **Ask friends to share**
4. **Monitor which platforms work best**

### This Week:
1. **Create Twitter account** (@CheshireToday)
2. **Create Facebook page** (Cheshire Today)
3. **Create LinkedIn page**
4. **Start sharing articles daily**

### This Month:
1. **Add share buttons** to articles
2. **Track social metrics** in Analytics
3. **Optimize preview image** if needed
4. **Build social following**

## Summary

✅ **Social sharing is now configured!**

**What you have:**
- Open Graph tags (Facebook, LinkedIn, WhatsApp)
- Twitter Card tags (Twitter/X)
- Logo image: https://cheshiretoday.co.uk/logo.png
- Title: Cheshire Today - Local News & Updates
- Description: Optimized for social sharing

**How to test:**
1. Facebook: https://developers.facebook.com/tools/debug/
2. Twitter: https://cards-dev.twitter.com/validator
3. LinkedIn: https://www.linkedin.com/post-inspector/

**When you share:** https://cheshiretoday.co.uk
- Your logo will appear
- Title and description show correctly
- Professional preview card displays

Start sharing your articles on social media to drive traffic! 🚀
