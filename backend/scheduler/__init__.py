"""
Scheduler module for background tasks.
"""
from .tasks import (
    setup_scheduler,
    cleanup_old_articles,
    daily_article_generation,
    send_scheduled_news_digest,
    auto_fix_duplicate_images,
    auto_clean_duplicate_articles,
)
