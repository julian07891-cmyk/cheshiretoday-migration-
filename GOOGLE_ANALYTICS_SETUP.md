# Google Analytics Setup - Cheshire Today

## Installation Complete ✅

Google Analytics (gtag.js) has been successfully added to your Cheshire Today website.

## Details

**Analytics ID:** G-Q1NZLJC50D

**Installation Location:** `/app/frontend/public/index.html`

**Script Added:**
```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-Q1NZLJC50D"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-Q1NZLJC50D');
</script>
```

## What's Tracking

Google Analytics will now track:

### Automatic Tracking
- **Page Views**: Every page visit and navigation
- **User Sessions**: Duration and engagement
- **Geographic Data**: Visitor location (country, city)
- **Device Info**: Desktop, mobile, tablet
- **Browser & OS**: Chrome, Safari, Firefox, etc.
- **Traffic Sources**: Direct, social, referral, organic search
- **User Demographics**: Age, gender, interests (when available)

### User Interactions
- Article views
- Category clicks
- Navigation patterns
- Time on site
- Bounce rate
- Exit pages

## Viewing Your Data

1. **Access Google Analytics Dashboard:**
   - Visit: https://analytics.google.com
   - Select your property (G-Q1NZLJC50D)

2. **Real-Time Reports:**
   - See active users on your site right now
   - View which pages they're visiting
   - Monitor traffic sources in real-time

3. **Audience Reports:**
   - User demographics
   - Geographic location
   - Technology (devices, browsers)
   - User behavior and engagement

4. **Acquisition Reports:**
   - How users find your site
   - Social media traffic
   - Search engine traffic
   - Referral sources

5. **Behavior Reports:**
   - Most popular articles
   - Most visited categories
   - User flow through the site
   - Page load times

## Advanced Tracking (Optional)

You can add custom event tracking for specific actions:

### Track Article Clicks
```javascript
gtag('event', 'article_click', {
  'article_title': 'Article Name',
  'article_category': 'Tech',
  'article_id': '12345'
});
```

### Track Category Changes
```javascript
gtag('event', 'category_filter', {
  'category': 'Health',
  'previous_category': 'All'
});
```

### Track Search Queries
```javascript
gtag('event', 'search', {
  'search_term': 'Cheshire news'
});
```

## Privacy Compliance

### GDPR & Cookie Consent
Consider adding a cookie consent banner if you have EU visitors:

**Recommended Cookie Consent Solutions:**
- Cookiebot
- OneTrust
- CookieYes
- Termly

### Privacy Policy
Update your privacy policy to mention:
- Use of Google Analytics
- Data collection and usage
- Cookie usage
- User rights (access, deletion)
- How to opt-out

### IP Anonymization (Optional)
For additional privacy, you can anonymize IP addresses:

```javascript
gtag('config', 'G-Q1NZLJC50D', {
  'anonymize_ip': true
});
```

## Testing Your Installation

### 1. Check in Real-Time Reports
- Visit your website: http://localhost:3000 (or your domain)
- Open Google Analytics Dashboard
- Go to: Reports > Real-time > Overview
- You should see yourself as an active user

### 2. Verify with Browser DevTools
- Open your website
- Press F12 (or right-click → Inspect)
- Go to Network tab
- Filter by "gtag" or "google-analytics"
- You should see requests to Google Analytics

### 3. Use Google Tag Assistant
- Install "Tag Assistant Legacy" Chrome extension
- Visit your website
- Click the extension icon
- Verify "Google Analytics" tag is firing

## Troubleshooting

### Not Seeing Data?

1. **Wait 24-48 hours**: Initial data can take time to appear
2. **Check Real-Time**: Use Real-Time reports to see immediate tracking
3. **Ad Blockers**: Some users have ad blockers that prevent tracking
4. **Browser Privacy Settings**: Enhanced privacy settings may block analytics

### Verification Steps

```bash
# Check if script is in HTML
curl https://cheshiretoday.co.uk | grep "gtag"

# Should return the Google tag script
```

## Performance Impact

**Minimal Impact:**
- Script loads asynchronously (`async` attribute)
- ~30KB additional download
- Does not block page rendering
- Cached after first load

## Cost

**Free:**
- Google Analytics is free for up to 10 million hits per month
- More than sufficient for most websites
- No credit card required

## Key Metrics to Monitor

### Daily
- Active users
- Page views
- Bounce rate
- Top articles

### Weekly
- User growth trends
- Traffic sources
- Popular categories
- Engagement metrics

### Monthly
- Month-over-month growth
- Geographic expansion
- Device trends
- Content performance

## Custom Dashboard Ideas

Create custom dashboards in Google Analytics for:

1. **Content Performance:**
   - Most read articles by category
   - Average time per article
   - Article engagement rates

2. **User Acquisition:**
   - Traffic source breakdown
   - Conversion rates
   - Referral sources

3. **User Behavior:**
   - Category preferences
   - Navigation patterns
   - User journey analysis

## Next Steps

1. **Set up Goals**: Track specific conversions or actions
2. **Create Custom Events**: Track article clicks, shares, etc.
3. **Set up Alerts**: Get notified of traffic spikes or issues
4. **Create Reports**: Schedule weekly/monthly reports via email
5. **Link Search Console**: Connect Google Search Console for SEO data

## Support

**Google Analytics Help:**
- https://support.google.com/analytics

**Documentation:**
- https://developers.google.com/analytics

**Community:**
- https://support.google.com/analytics/community

## Summary

✅ Google Analytics successfully installed
✅ Tracking ID: G-Q1NZLJC50D
✅ Automatic page view tracking enabled
✅ Ready to collect visitor data
✅ View reports at: https://analytics.google.com

Your Cheshire Today website is now equipped with professional analytics tracking to help you understand your audience and grow your readership!
