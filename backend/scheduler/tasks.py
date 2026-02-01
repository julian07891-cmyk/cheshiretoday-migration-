"""
Scheduled background tasks for the news application.
"""
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


async def setup_scheduler(scheduler, db, daily_gen_func, digest_func, dup_remove_func, image_service):
    """
    Configure all scheduled jobs.
    This is called from server.py during startup.
    """
    from apscheduler.triggers.cron import CronTrigger
    
    # Article generation jobs
    scheduler.add_job(
        daily_gen_func,
        CronTrigger(hour=6, minute=0),
        id='morning_article_generation',
        name='Generate morning news articles',
        replace_existing=True,
        args=[12]
    )
    
    scheduler.add_job(
        daily_gen_func,
        CronTrigger(hour=12, minute=0),
        id='midday_article_generation',
        name='Generate midday news articles',
        replace_existing=True
    )
    
    scheduler.add_job(
        daily_gen_func,
        CronTrigger(hour=18, minute=0),
        id='evening_article_generation',
        name='Generate evening news articles',
        replace_existing=True
    )
    
    scheduler.add_job(
        daily_gen_func,
        CronTrigger(hour=15, minute=0),
        id='afternoon_article_generation',
        name='Generate afternoon news articles',
        replace_existing=True
    )
    
    # News digest email jobs
    scheduler.add_job(
        digest_func,
        CronTrigger(hour=6, minute=15),
        id='morning_news_digest',
        name='Send morning news digest',
        replace_existing=True,
        kwargs={'digest_time': 'Morning'}
    )
    
    scheduler.add_job(
        digest_func,
        CronTrigger(hour=12, minute=15),
        id='midday_news_digest',
        name='Send midday news digest',
        replace_existing=True,
        kwargs={'digest_time': 'Midday'}
    )
    
    scheduler.add_job(
        digest_func,
        CronTrigger(hour=18, minute=15),
        id='evening_news_digest',
        name='Send evening news digest',
        replace_existing=True,
        kwargs={'digest_time': 'Evening'}
    )
    
    scheduler.start()
    logger.info("Scheduler started. Articles: 6AM, 12PM, 3PM, 6PM. Digests: 6:15AM, 12:15PM, 6:15PM.")


async def cleanup_old_articles(db):
    """Remove articles older than 5 days."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=5)
        
        old_count = await db.articles.count_documents({
            'publishedDate': {'$lt': cutoff_date.isoformat()}
        })
        
        if old_count > 0:
            result = await db.articles.delete_many({
                'publishedDate': {'$lt': cutoff_date.isoformat()}
            })
            logger.info(f"🗑️ Cleaned up {result.deleted_count} articles older than 5 days")
        else:
            logger.info("✅ No old articles to clean up (all within 5 days)")
        
        # Safety cap at 100 articles
        total_count = await db.articles.count_documents({})
        if total_count > 100:
            articles = await db.articles.find({}, {'publishedDate': 1}).sort('publishedDate', -1).skip(100).limit(1).to_list(1)
            if articles:
                cutoff = articles[0]['publishedDate']
                result = await db.articles.delete_many({'publishedDate': {'$lt': cutoff}})
                logger.info(f"🗑️ Safety cap: removed {result.deleted_count} articles beyond 100 limit")
                
    except Exception as e:
        logger.error(f"Error cleaning up old articles: {str(e)}")


async def daily_article_generation(generate_articles_func, dup_remove_func, db, count: int = 12):
    """Generate new articles daily with fault tolerance."""
    try:
        logger.info(f"Starting daily article generation (target: {count})...")
        
        try:
            await generate_articles_func(count=count, include_uk_news=True)
        except Exception as gen_error:
            logger.error(f"Error during article generation (will retry): {str(gen_error)}")
        
        try:
            cleanup_result = await dup_remove_func()
            logger.info(f"Auto-cleanup after generation: removed {cleanup_result.get('total_removed', 0)} duplicates/short articles")
        except Exception as dup_error:
            logger.error(f"Error during duplicate removal: {str(dup_error)}")
        
        try:
            await cleanup_old_articles(db)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {str(cleanup_error)}")
        
        logger.info("Daily article generation process completed")
    except Exception as e:
        logger.error(f"Critical error in daily article generation: {str(e)}")


async def send_scheduled_news_digest(db, email_service, digest_time: str = "Daily"):
    """Send news digest email to all subscribers."""
    try:
        logger.info(f"📧 Starting {digest_time} news digest email send...")
        
        subscribers = await db.subscribers.find({}, {"_id": 0, "email": 1}).to_list(1000)
        if not subscribers:
            logger.info("No subscribers found - skipping digest email")
            return
        
        subscriber_emails = [s.get('email') for s in subscribers if s.get('email')]
        logger.info(f"Found {len(subscriber_emails)} subscribers")
        
        cutoff_time = datetime.utcnow() - timedelta(hours=8)
        
        recent_articles = await db.articles.find(
            {"created_at": {"$gte": cutoff_time}},
            {"_id": 0, "id": 1, "title": 1, "content": 1, "category": 1, "author": 1, "image": 1}
        ).sort("created_at", -1).limit(10).to_list(10)
        
        if not recent_articles:
            logger.info("No recent articles, using latest 10")
            recent_articles = await db.articles.find(
                {},
                {"_id": 0, "id": 1, "title": 1, "content": 1, "category": 1, "author": 1, "image": 1}
            ).sort("publishedDate", -1).limit(10).to_list(10)
        
        if not recent_articles:
            logger.warning("No articles available for digest")
            return
        
        logger.info(f"Sending digest with {len(recent_articles)} articles to {len(subscriber_emails)} subscribers")
        
        success_count = email_service.send_news_digest(
            to_emails=subscriber_emails,
            articles=recent_articles,
            digest_time=digest_time
        )
        
        logger.info(f"✅ {digest_time} digest sent to {success_count}/{len(subscriber_emails)} subscribers")
        
    except Exception as e:
        logger.error(f"Error sending {digest_time} news digest: {str(e)}")


async def auto_fix_duplicate_images(db, image_service):
    """AUTOMATIC image cleanup that runs on startup."""
    try:
        logger.info("Running automatic image cleanup and verification...")
        
        all_articles = await db.articles.find({}).to_list(1000)
        if not all_articles:
            logger.info("No articles found - skipping image cleanup")
            return
        
        RSS_IMAGE_DOMAINS = ['ichef.bbci.co.uk', 'i.guim.co.uk', 'e3.365dm.com', 'media.guim.co.uk']
        
        def is_rss_image(url):
            if not url:
                return False
            return any(domain in url for domain in RSS_IMAGE_DOMAINS)
        
        invalid_image_count = 0
        articles_with_invalid_images = []
        
        for article in all_articles:
            current_image = article.get('image')
            
            if is_rss_image(current_image):
                continue
            
            is_banned = False
            if current_image:
                for banned in image_service.BANNED_IMAGES:
                    if banned in current_image:
                        is_banned = True
                        break
            
            if current_image and (is_banned or current_image not in image_service.ALL_UNIQUE_IMAGES):
                articles_with_invalid_images.append(article)
        
        if articles_with_invalid_images:
            logger.info(f"Found {len(articles_with_invalid_images)} articles with banned/unverified stock images. Replacing...")
            
            used_images = set()
            for a in all_articles:
                img = a.get('image')
                if img:
                    if is_rss_image(img):
                        used_images.add(img)
                    elif img in image_service.ALL_UNIQUE_IMAGES and not any(b in img for b in image_service.BANNED_IMAGES):
                        used_images.add(img)
            
            for article in articles_with_invalid_images:
                new_image = image_service.select_unique_image(
                    article.get('category', 'Local News'), 
                    used_images, 
                    article.get('title', ''), 
                    article.get('content', '')
                )
                
                if new_image:
                    await db.articles.update_one(
                        {'_id': article['_id']},
                        {'$set': {'image': new_image}}
                    )
                    used_images.add(new_image)
                    article['image'] = new_image 
                    invalid_image_count += 1
                else:
                    logger.warning(f"Could not find replacement image for article {article['_id']}")

            logger.info(f"✅ Replaced {invalid_image_count} unverified/newspaper images (RSS images preserved)")
            
            all_articles = await db.articles.find({}).to_list(1000)

        image_usage = {}
        for article in all_articles:
            image = article.get('image')
            if image:
                if image not in image_usage:
                    image_usage[image] = []
                image_usage[image].append(article['_id'])
        
        articles_needing_images = []
        for image, article_ids in image_usage.items():
            if len(article_ids) > 1:
                for article_id in article_ids[1:]:
                    article = next(a for a in all_articles if a['_id'] == article_id)
                    articles_needing_images.append({
                        'id': article_id,
                        'category': article.get('category', 'Local News'),
                        'current_image': image,
                        'title': article.get('title', ''),
                        'content': article.get('content', '')
                    })
        
        if not articles_needing_images and invalid_image_count == 0:
            logger.info(f"✅ All {len(all_articles)} articles have unique, verified images - no cleanup needed")
            return
        
        if articles_needing_images:
            logger.warning(f"Found {len(articles_needing_images)} articles with duplicate images - fixing now...")
            
            used_images = {article.get('image') for article in all_articles if article.get('image')}
            
            fixed_count = 0
            for article_info in articles_needing_images:
                new_image = image_service.select_unique_image(
                    article_info['category'], 
                    used_images, 
                    article_info['title'], 
                    article_info['content']
                )
                
                if new_image:
                    await db.articles.update_one(
                        {'_id': article_info['id']},
                        {'$set': {'image': new_image}}
                    )
                    used_images.add(new_image)
                    fixed_count += 1
                    logger.info(f"Fixed duplicate: replaced {article_info['current_image'][-40:]} with {new_image[-40:]}")
                else:
                    logger.warning(f"Could not find unique image for article {article_info['id']}")
            
            logger.info(f"✅ Auto-fixed {fixed_count} duplicate images on startup")
        
    except Exception as e:
        logger.error(f"Error during auto duplicate image cleanup: {str(e)}")


async def auto_clean_duplicate_articles(db):
    """Automatically remove duplicate articles on startup."""
    try:
        articles = await db.articles.find({}).sort('publishedDate', -1).to_list(1000)
        
        seen_patterns = set()
        removed_count = 0
        
        for article in articles:
            title = article.get('title', '')
            words = title.split()[:5]
            pattern = ' '.join(words).lower()
            
            if pattern in seen_patterns:
                await db.articles.delete_one({'_id': article['_id']})
                removed_count += 1
            else:
                seen_patterns.add(pattern)
        
        if removed_count > 0:
            logger.info(f"✅ Auto-removed {removed_count} duplicate articles on startup")
        else:
            logger.info("✅ No duplicate articles to remove")
            
    except Exception as e:
        logger.error(f"Error during auto duplicate article cleanup: {str(e)}")
