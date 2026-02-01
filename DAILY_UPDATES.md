# Cheshire Today - Daily News Updates

## Automatic Daily Article Generation

The website now automatically generates fresh news articles every day to keep content current and engaging.

## Schedule

- **Daily Generation Time**: 6:00 AM UTC
- **Articles Generated**: 8 new articles per day
  - ~5 Cheshire-focused articles (Local News, Business, Tech, Finance, Events, Sports, Community)
  - ~3 UK-wide articles (UK News, Tech, Finance, Business)

## Article Retention

- **Maximum Articles**: 50 articles kept in database
- **Cleanup**: When total exceeds 50, older articles are automatically removed
- **Strategy**: Keep the most recent 50 articles to ensure fresh content while managing database size

## How It Works

1. **Scheduled Task**: APScheduler runs a daily job at 6:00 AM
2. **Generation**: Perplexity AI generates 8 new articles about relevant topics
3. **Cleanup**: System removes articles beyond the 50-article limit
4. **Categories**: Articles distributed across all 9 categories

## Manual Trigger (Admin)

You can manually trigger article generation at any time using the API:

```bash
curl -X POST http://localhost:8001/api/trigger-daily-generation
```

This is useful for:
- Testing the generation system
- Creating fresh content outside the scheduled time
- Recovering from any generation failures

## Check Scheduler Status

View the scheduler status and next run time:

```bash
curl http://localhost:8001/api/scheduler-status
```

Response example:
```json
{
  "scheduler_running": true,
  "jobs": [
    {
      "id": "daily_article_generation",
      "name": "Generate daily news articles",
      "next_run_time": "2025-12-12T06:00:00+00:00"
    }
  ]
}
```

## Benefits

✅ **Fresh Content**: New articles every day keep readers engaged
✅ **Relevant News**: Topics automatically selected for Cheshire and UK news
✅ **Automated**: No manual intervention required
✅ **Resource Efficient**: Cleanup prevents database bloat
✅ **Flexible**: Manual trigger available when needed

## Technical Details

- **Library**: APScheduler (AsyncIO-compatible)
- **Trigger**: CronTrigger (hour=6, minute=0)
- **AI Service**: Perplexity API with "sonar" model
- **Database**: MongoDB with automatic cleanup
- **Timezone**: UTC (adjust if needed for local timezone)

## Customization

To change the schedule or article count, edit `/app/backend/server.py`:

- **Change time**: Modify `CronTrigger(hour=6, minute=0)` 
- **Change article count**: Modify `GenerateArticlesRequest(count=8)`
- **Change retention**: Modify the limit in `cleanup_old_articles()` function

## Monitoring

Check backend logs to monitor daily generation:
```bash
tail -f /var/log/supervisor/backend.err.log
```

Look for messages like:
- "Starting daily article generation..."
- "Daily article generation completed successfully"
- "Cleaned up X old articles"

## Troubleshooting

**If articles aren't generating:**
1. Check scheduler status via API endpoint
2. Verify backend logs for errors
3. Ensure Perplexity API key is valid
4. Check database connection
5. Try manual trigger to test generation

**If too many/few articles:**
- Adjust `count` parameter in daily generation function
- Modify retention limit in cleanup function
