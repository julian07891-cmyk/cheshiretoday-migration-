# Google Search Console Setup - Cheshire Today

## Sitemap Successfully Created ✅

Your dynamic sitemap.xml is now available and ready to submit to Google Search Console.

## Sitemap Details

**Sitemap URL:** https://cheshiretoday.co.uk/sitemap.xml

**Current Content:**
- 1 Homepage
- 9 Category pages
- 15 Article pages
- **Total: 25 URLs**

**Update Frequency:**
- Automatically updates when new articles are generated
- Reflects current database content
- No manual maintenance required

## What's in the Sitemap

### Homepage (Priority: 1.0)
```
https://cheshiretoday.co.uk/
```

### Category Pages (Priority: 0.8)
```
https://cheshiretoday.co.uk/category/local-news
https://cheshiretoday.co.uk/category/uk-news
https://cheshiretoday.co.uk/category/community
https://cheshiretoday.co.uk/category/tech
https://cheshiretoday.co.uk/category/business
https://cheshiretoday.co.uk/category/finance
https://cheshiretoday.co.uk/category/health
https://cheshiretoday.co.uk/category/sports
https://cheshiretoday.co.uk/category/events
```

### Article Pages (Priority: 0.6)
All articles with their unique IDs and publication dates

## How to Submit to Google Search Console

### Step 1: Access Google Search Console

1. Go to: https://search.google.com/search-console
2. Sign in with your Google account
3. If first time, you'll need to verify ownership of your domain

### Step 2: Add Your Property

**Method A: Domain Property (Recommended)**
1. Click "Add Property"
2. Select "Domain" option
3. Enter: `cheshiretoday.co.uk`
4. You'll receive a TXT record to add to your DNS

**Method B: URL Prefix**
1. Click "Add Property"
2. Select "URL prefix" option
3. Enter: `https://cheshiretoday.co.uk`
4. Verify using one of the methods below

### Step 3: Verify Domain Ownership

Choose one verification method:

#### Option 1: HTML File Upload (Easiest)
1. Download the verification HTML file from Google
2. Upload to: `/app/frontend/public/`
3. Access at: `https://cheshiretoday.co.uk/google-verification-file.html`
4. Click "Verify" in Google Search Console

#### Option 2: HTML Meta Tag (Already Set Up!)
Since you have Google Analytics installed, you can verify via Google Analytics:
1. In Search Console, choose "Google Analytics" verification method
2. Must use the same Google account for both
3. Click "Verify"

#### Option 3: DNS TXT Record
1. Log into your domain registrar (where you bought cheshiretoday.co.uk)
2. Add TXT record provided by Google
3. Wait 10-30 minutes for DNS propagation
4. Click "Verify"

#### Option 4: Google Analytics Tag
1. Already installed: G-Q1NZLJC50D
2. Use same Google account
3. Click "Verify"

### Step 4: Submit Sitemap

Once verified:

1. In Google Search Console, click on your property
2. Go to **"Sitemaps"** (in left sidebar under "Indexing")
3. Enter sitemap URL: `sitemap.xml`
4. Click **"Submit"**

**Alternative full URL:**
```
https://cheshiretoday.co.uk/sitemap.xml
```

### Step 5: Wait for Processing

- Google will crawl your sitemap within 24-48 hours
- Check status in the Sitemaps section
- Status should change to "Success" with number of discovered pages

## Verification Steps

### Check Sitemap is Accessible

```bash
curl https://cheshiretoday.co.uk/sitemap.xml
```

Should return XML with all your URLs.

### Check robots.txt

```bash
curl https://cheshiretoday.co.uk/robots.txt
```

Should show:
```
User-agent: *
Allow: /

Sitemap: https://cheshiretoday.co.uk/sitemap.xml
```

### Validate Sitemap

Use online validators:
- https://www.xml-sitemaps.com/validate-xml-sitemap.html
- Paste: https://cheshiretoday.co.uk/sitemap.xml
- Should pass all validation tests

## Monitoring & Reports

### Check Sitemap Status

**Google Search Console → Sitemaps:**
- Submitted: Date you submitted
- Discovered: URLs found by Google
- Status: Success/Error
- Last read: When Google last accessed it

### Coverage Report

**Google Search Console → Coverage:**
- Valid pages indexed
- Pages with warnings
- Excluded pages
- Errors to fix

### Performance Report

**Google Search Console → Performance:**
- Total clicks
- Total impressions
- Average CTR (Click-Through Rate)
- Average position in search results

## Advanced Features

### Request Indexing for Individual Articles

1. Go to: Google Search Console → URL Inspection
2. Enter article URL
3. Click "Request Indexing"
4. Google will prioritize crawling that page

### Remove URLs

If you need to remove old articles:
1. Delete from database
2. They'll automatically disappear from sitemap
3. Use "Removals" tool in Search Console for immediate removal

### Set Geographic Targeting

**If targeting UK audience:**
1. Go to: Settings → Country
2. Set: "United Kingdom"
3. Helps with local search ranking

## SEO Best Practices

### Update Frequency

Your sitemap automatically updates with:
- **Daily**: Homepage and category pages
- **Weekly**: Article pages
- **On change**: When articles are added/removed

### Priority Guidelines

Set in sitemap (already configured):
- **1.0**: Homepage (most important)
- **0.8**: Category pages
- **0.6**: Article pages

### XML Sitemap Limits

Google's limits (you're well within):
- Max 50,000 URLs per sitemap
- Max 50MB uncompressed
- Current: 25 URLs (~5KB)

## Troubleshooting

### Sitemap Not Found

**Check:**
```bash
curl https://cheshiretoday.co.uk/sitemap.xml
```

**Common issues:**
- Domain not yet configured
- Backend not running
- CORS/firewall blocking

### Pages Not Being Indexed

**Possible reasons:**
1. **New site**: Can take 2-4 weeks for initial indexing
2. **Low quality content**: Ensure unique, valuable content
3. **No backlinks**: Get links from other sites
4. **Robots.txt blocking**: Check your robots.txt allows crawling

**Solutions:**
- Request indexing manually (URL Inspection tool)
- Share articles on social media
- Build backlinks from relevant sites

### Errors in Google Search Console

**Common errors:**
- **Server error (5xx)**: Backend might be down
- **Not found (404)**: URL structure mismatch
- **Redirect error**: Check URL redirects

## Integration with Google Analytics

Since both are set up:

1. **Link Search Console to Analytics:**
   - In Analytics: Admin → Property → Search Console Links
   - Link your Search Console property
   
2. **View Combined Reports:**
   - Analytics → Acquisition → Search Console
   - See queries, pages, countries, devices

## Next Steps

### Immediate Actions

1. ✅ Submit sitemap to Google Search Console
2. ✅ Verify domain ownership
3. ✅ Request indexing for homepage

### Ongoing Monitoring

1. **Weekly:** Check Search Console for errors
2. **Monthly:** Review performance reports
3. **Quarterly:** Analyze search queries and optimize content

### Content Optimization

Based on Search Console data:
1. Identify low-performing articles
2. Update with better keywords
3. Improve meta descriptions
4. Add internal links

## Mobile Optimization

**Google prioritizes mobile:**
- Your site is responsive (Tailwind CSS)
- Test: https://search.google.com/test/mobile-friendly
- Enter: https://cheshiretoday.co.uk

## Page Speed

**Check performance:**
- Tool: https://pagespeed.web.dev/
- Enter: https://cheshiretoday.co.uk
- Aim for: 90+ score

## Schema Markup (Future Enhancement)

Consider adding structured data:
- Article schema for news articles
- BreadcrumbList for navigation
- Organization schema for Cheshire Today

**Benefits:**
- Rich snippets in search results
- Better click-through rates
- Featured in Google News

## Expected Timeline

**Week 1:**
- Sitemap submitted ✅
- Google crawls sitemap
- Initial indexing begins

**Week 2-3:**
- More pages indexed
- Start appearing in search results
- Can see data in Search Console

**Month 1-3:**
- Full indexing complete
- Search rankings improve
- Organic traffic grows

**Month 3+:**
- Established presence
- Regular organic traffic
- Growing search visibility

## Support Resources

**Google Search Console Help:**
- https://support.google.com/webmasters

**SEO Best Practices:**
- https://developers.google.com/search/docs

**Sitemap Protocol:**
- https://www.sitemaps.org/

## Summary

✅ **Sitemap created:** https://cheshiretoday.co.uk/sitemap.xml
✅ **Dynamic updates:** Automatically reflects new articles
✅ **Robots.txt configured:** Guides search engines
✅ **25 URLs ready:** Homepage, categories, articles
✅ **SEO optimized:** Proper priorities and change frequencies

**Next Action:** Submit sitemap to Google Search Console following the steps above!

**Expected Outcome:** Your Cheshire Today articles will start appearing in Google search results within 2-4 weeks, driving organic traffic to your news site.
