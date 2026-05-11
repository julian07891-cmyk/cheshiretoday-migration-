"""
Push Notification Service for Cheshire Today
Sends breaking news alerts via Web Push API
"""
import os
import json
import logging
from typing import List, Dict, Optional
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)


class PushNotificationService:
    def __init__(self):
        self.vapid_public_key = os.environ.get('VAPID_PUBLIC_KEY', '')
        self.vapid_private_key = os.environ.get('VAPID_PRIVATE_KEY', '')
        self.vapid_contact = os.environ.get('VAPID_CONTACT_EMAIL', 'news@cheshiretoday.co.uk')
    
    @property
    def is_configured(self) -> bool:
        """Check if VAPID keys are configured"""
        return bool(self.vapid_public_key and self.vapid_private_key)
    
    def get_vapid_public_key(self) -> str:
        """Get the public key for client-side subscription"""
        return self.vapid_public_key
    
    async def send_notification(
        self,
        subscription: Dict,
        title: str,
        body: str,
        url: str = "/",
        icon: str = "/logo192.png",
        tag: str = "news"
    ) -> Dict:
        """
        Send a push notification to a single subscription.
        
        Args:
            subscription: Push subscription object with endpoint, keys
            title: Notification title
            body: Notification body text
            url: URL to open when notification is clicked
            icon: Icon URL
            tag: Notification tag for grouping
            
        Returns:
            Dict with success status
        """
        if not self.is_configured:
            return {"success": False, "error": "Push notifications not configured"}
        
        try:
            payload = json.dumps({
                "title": title,
                "body": body,
                "url": url,
                "icon": icon,
                "tag": tag,
                "timestamp": int(__import__('time').time() * 1000)
            })
            
            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{self.vapid_contact}"
                }
            )
            
            logger.info(f"✅ Push notification sent: {title[:50]}")
            return {"success": True, "message": "Notification sent"}
            
        except WebPushException as e:
            logger.error(f"Push notification failed: {str(e)}")
            # If subscription is invalid (410 Gone), return special status
            if e.response and e.response.status_code == 410:
                return {"success": False, "error": "subscription_expired", "should_remove": True}
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Push notification error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_to_all(
        self,
        subscriptions: List[Dict],
        title: str,
        body: str,
        url: str = "/",
        icon: str = "/logo192.png",
        tag: str = "news"
    ) -> Dict:
        """
        Send push notification to all subscriptions.
        
        Args:
            subscriptions: List of subscription objects
            title: Notification title
            body: Notification body text
            url: URL to open when clicked
            icon: Icon URL
            tag: Notification tag
            
        Returns:
            Dict with success count and failures
        """
        if not self.is_configured:
            return {"success": False, "error": "Push notifications not configured", "sent": 0}
        
        sent_count = 0
        failed_count = 0
        expired_subscriptions = []
        
        for subscription in subscriptions:
            result = await self.send_notification(
                subscription=subscription,
                title=title,
                body=body,
                url=url,
                icon=icon,
                tag=tag
            )
            
            if result.get("success"):
                sent_count += 1
            else:
                failed_count += 1
                if result.get("should_remove"):
                    expired_subscriptions.append(subscription.get("endpoint"))
        
        logger.info(f"📢 Push broadcast: {sent_count} sent, {failed_count} failed, {len(expired_subscriptions)} expired")
        
        return {
            "success": sent_count > 0,
            "sent": sent_count,
            "failed": failed_count,
            "expired_endpoints": expired_subscriptions
        }
    
    async def send_breaking_news(
        self,
        subscriptions: List[Dict],
        article_title: str,
        article_id: str,
        category: str = "Breaking News"
    ) -> Dict:
        """
        Send a breaking news notification.
        
        Args:
            subscriptions: List of push subscriptions
            article_title: Article headline
            article_id: Article ID for the URL
            category: News category
            
        Returns:
            Dict with results
        """
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", str(article_title or "").lower()).strip("-")
        slug = slug[:80] if slug else "article"

        return await self.send_to_all(
            subscriptions=subscriptions,
            title=f"🔴 {category}",
            body=article_title,
            url=f"/article/{article_id}/{slug}",
            icon="/logo192.png",
            tag=f"breaking-{article_id}"
        )


# Singleton instance
push_service = PushNotificationService()
