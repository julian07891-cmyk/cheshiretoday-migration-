# Cheshire Today - Daily Cost Analysis

## Daily News Updates Cost Breakdown

### Current Configuration
- **Daily Articles**: 8 articles per day
- **AI Model**: Perplexity Sonar (base model)
- **Article Length**: ~300-400 words per article
- **API Key**: Your own Perplexity API key

### Perplexity API Pricing (2025)

**Sonar Model (what you're using):**
- Input tokens: $1 per 1 million tokens
- Output tokens: $1 per 1 million tokens
- Request fee: ~$5 per 1,000 queries

### Estimated Token Usage Per Article

**Input (Prompt):**
- System message: ~50 tokens
- User prompt: ~150 tokens
- Total input: ~200 tokens per article

**Output (Generated Article):**
- 300-400 words ≈ 400-500 tokens
- Total output: ~450 tokens per article

**Total per article**: ~650 tokens (200 input + 450 output)

### Daily Cost Calculation

**Token Costs:**
- Daily tokens: 8 articles × 650 tokens = 5,200 tokens
- Input cost: (8 × 200) tokens = 1,600 tokens = $0.0016
- Output cost: (8 × 450) tokens = 3,600 tokens = $0.0036
- **Daily token cost: $0.0052** (approximately half a cent)

**Request Costs:**
- 8 requests per day
- Request fee: $5 per 1,000 requests
- Daily request cost: (8 ÷ 1,000) × $5 = $0.04
- **Daily request cost: $0.04** (4 cents)

### Total Daily Cost: ~$0.045 (4.5 cents)

### Monthly Cost Estimate

**30 days:**
- Token costs: $0.0052 × 30 = $0.156
- Request costs: $0.04 × 30 = $1.20
- **Monthly total: ~$1.36** (less than $1.50/month)

### Annual Cost Estimate

**365 days:**
- Token costs: $0.0052 × 365 = $1.90
- Request costs: $0.04 × 365 = $14.60
- **Annual total: ~$16.50** (less than $17/year)

## Logo Generation Cost (One-Time)

**AI-Generated Logo:**
- Service: OpenAI gpt-image-1 via Emergent LLM Key
- Cost: ~$0.04 (4 cents) - **ALREADY PAID**
- This was a one-time cost for logo generation

## Summary

### Daily Operating Costs
| Item | Cost |
|------|------|
| 8 AI Articles | $0.045/day |
| Logo (one-time) | $0.04 (paid) |

### Long-Term Costs
| Period | Cost |
|--------|------|
| Daily | $0.045 (~4.5 cents) |
| Weekly | $0.315 (~32 cents) |
| Monthly | $1.36 (~$1.40) |
| Annual | $16.50 (~$17) |

## Cost Optimization Tips

### Reduce Costs Further

1. **Generate Fewer Articles**
   - Change from 8 to 5 articles per day
   - Saves: ~$0.017/day (~$6/year)

2. **Longer Generation Interval**
   - Generate articles every 2-3 days instead of daily
   - Saves: 50-66% of daily costs

3. **Batch Processing**
   - Generate multiple articles in single requests (if possible)
   - May reduce request fees

4. **Article Length**
   - Reduce max_tokens from 1000 to 500
   - Shorter articles = lower token costs

## Cost Comparison

**Your Setup vs Alternatives:**
- ✅ **Your cost**: $1.36/month for automated, fresh content
- ❌ **Manual writing**: $50-100+ per article (if outsourced)
- ❌ **Content services**: $100-500/month for similar volume
- ❌ **Static website**: $0/month but no fresh content

## Value Proposition

**What You Get for $1.36/month:**
- 240 AI-generated news articles per month
- Automatic daily updates at 6 AM
- Mix of local Cheshire and UK news
- Coverage across 9 categories
- Professional, well-researched content
- Zero manual effort

**Cost per article**: $0.0057 (less than 1 cent per article!)

## Monitoring Your Usage

**Check Perplexity Dashboard:**
1. Visit https://www.perplexity.ai/api-platform
2. Go to "Usage" section
3. Monitor daily API calls and token usage
4. Set up billing alerts if needed

**Backend Logs:**
Monitor generation in real-time:
```bash
tail -f /var/log/supervisor/backend.err.log | grep "article"
```

## Billing Notes

- Perplexity charges your API key directly
- Costs appear on your Perplexity account
- Emergent LLM Key used only for logo (one-time)
- No recurring Emergent charges for article generation
- Your Perplexity account manages all article generation costs

## Adjusting Generation Schedule

To modify costs, edit `/app/backend/server.py`:

```python
# Current: 8 articles daily at 6 AM
await generate_articles(GenerateArticlesRequest(count=8, include_uk_news=True))

# Reduce to 5 articles to save ~35% ($0.50/month)
await generate_articles(GenerateArticlesRequest(count=5, include_uk_news=True))
```

Or change schedule to every 2 days:
```python
# In scheduler setup, change from:
CronTrigger(hour=6, minute=0)  # Daily

# To:
CronTrigger(day='*/2', hour=6, minute=0)  # Every 2 days
```

## Conclusion

Your Cheshire Today website costs approximately **$0.045 per day** or **$1.36 per month** for fully automated, AI-generated news content. This is incredibly cost-effective compared to traditional content creation methods, while maintaining quality and relevance.
