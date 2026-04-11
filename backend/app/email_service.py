from datetime import datetime, timezone, timedelta
"""
Email Service for Cheshire Today Newsletter
Handles sending confirmation and newsletter emails via SMTP
Updated: January 2026 - New tiered email strategy with analytics tracking
"""

import smtplib
import os
import uuid
import hashlib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Tuple
import logging
import httpx

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.smtp_enabled = (os.environ.get('SMTP_ENABLED', 'false').strip().lower() in ('1','true','yes','on'))
        self.resend_enabled = (os.environ.get('RESEND_ENABLED', 'false').strip().lower() in ('1','true','yes','on'))
        self.resend_api_key = os.environ.get('RESEND_API_KEY')
        self.from_email = os.environ.get('SMTP_FROM_EMAIL')
        self.resend_from_email = os.environ.get('RESEND_FROM_EMAIL')
        # Updated: From name is now "Editor at Cheshire Today"
        self.from_name = os.environ.get('SMTP_FROM_NAME', 'Editor at Cheshire Today')
        self.resend_from_name = os.environ.get('RESEND_FROM_NAME', self.from_name)
        # Reply-to address
        self.reply_to = 'news@cheshiretoday.co.uk'
        # ALWAYS use production URL for email links - hardcoded to prevent env var issues
        self.base_url = 'https://cheshiretoday.co.uk'
        # API URL for tracking endpoints
        self.api_url = 'https://cheshiretoday.co.uk/api'
    
    def _generate_tracking_id(self, email_type: str, recipient_email: str = None) -> str:
        """Generate a unique tracking ID for email analytics"""
        unique_str = f"{email_type}_{datetime.now().isoformat()}_{uuid.uuid4().hex[:8]}"
        if recipient_email:
            # Hash email for privacy
            email_hash = hashlib.sha256(recipient_email.encode()).hexdigest()[:8]
            unique_str += f"_{email_hash}"
        return unique_str
    
    def _get_tracking_pixel(self, tracking_id: str) -> str:
        """Generate HTML for invisible tracking pixel"""
        return f'<img src="{self.api_url}/email/track/open/{tracking_id}" width="1" height="1" alt="" style="display:none;border:0;height:1px;width:1px;" />'
    
    def _get_tracked_url(self, tracking_id: str, original_url: str) -> str:
        """Generate tracked URL that redirects through our tracking endpoint"""
        from urllib.parse import quote
        return f"{self.api_url}/email/track/click/{tracking_id}?url={quote(original_url, safe='')}"

    def _article_url(self, article: dict) -> str:
        """Build canonical article URL with slug."""
        article_id = article.get('id', article.get('_id', ''))
        raw_title = str(article.get('title') or 'article')
        slug = re.sub(r"[^a-z0-9]+", "-", raw_title.lower()).strip("-")
        slug = (slug[:80] if slug else "article")
        return f"{self.base_url}/article/{article_id}/{slug}"
        
    
    def _resend_from_header(self) -> str:
        from_email = self.resend_from_email or self.from_email
        from_name = self.resend_from_name or self.from_name
        return f"{from_name} <{from_email}>" if from_name else from_email

    def _send_resend_batch(self, batch_messages: List[dict]) -> int:
        """Send personalized emails via Resend batch API in chunks."""
        if not batch_messages:
            return 0
        if not getattr(self, "resend_enabled", False):
            logger.info("Resend disabled (RESEND_ENABLED not true) — skipping Resend batch send")
            return 0
        if not self.resend_api_key:
            logger.error("Resend not configured (RESEND_API_KEY missing)")
            return 0
        from_email = self.resend_from_email or self.from_email
        if not from_email:
            logger.error("Resend not configured (RESEND_FROM_EMAIL / SMTP_FROM_EMAIL missing)")
            return 0

        success_count = 0
        headers = {
            "Authorization": f"Bearer {self.resend_api_key}",
            "Content-Type": "application/json",
        }

        for i in range(0, len(batch_messages), 100):
            chunk = batch_messages[i:i+100]
            payload = []
            for item in chunk:
                email_payload = {
                    "from": self._resend_from_header(),
                    "to": [item["to"]],
                    "subject": item["subject"],
                    "html": item["html"],
                }
                if item.get("text") is not None:
                    email_payload["text"] = item["text"]
                if self.reply_to:
                    email_payload["reply_to"] = self.reply_to
                payload.append(email_payload)

            try:
                response = httpx.post(
                    "https://api.resend.com/emails/batch",
                    headers=headers,
                    json=payload,
                    timeout=60.0,
                )
                response.raise_for_status()
                success_count += len(chunk)
            except Exception as e:
                detail = ""
                try:
                    detail = response.text[:500]
                except Exception:
                    pass
                logger.error(f"Resend batch send failed for chunk {i // 100 + 1}: {str(e)} {detail}")

        return success_count


    def _send_email(self, to_email, subject, html_content, text_content=None):
        """Send an email via SMTP (supports Gmail, GoDaddy, etc.)"""
        import smtplib
        import ssl
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        if not getattr(self, 'smtp_enabled', False):
            logger.info('SMTP disabled (SMTP_ENABLED not true) — skipping send')
            # Marker used by callers/admin endpoints to explain why nothing was sent
            self.smtp_last_status = "SMTP_DISABLED"
            return False


        if not self.smtp_host or not self.smtp_port:
            logger.error("SMTP not configured (SMTP_HOST/SMTP_PORT missing)")
            return False
        if not self.smtp_user or not self.smtp_password:
            logger.error("SMTP not configured (SMTP_USER/SMTP_PASSWORD missing)")
            return False
        if not self.from_email:
            logger.error("SMTP not configured (SMTP_FROM_EMAIL missing)")
            return False

        # Build message (multipart/alternative)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        # Prefer plain text fallback if provided
        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        context = ssl.create_default_context()

        try:
            # Use SMTP_SSL for port 465 (GoDaddy, etc.)
            if int(self.smtp_port) == 465:
                with smtplib.SMTP_SSL(self.smtp_host, int(self.smtp_port), context=context, timeout=30) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.from_email, to_email, msg.as_string())
            else:
                # Use SMTP with STARTTLS for port 587 (Gmail, GoDaddy, etc.)
                with smtplib.SMTP(self.smtp_host, int(self.smtp_port), timeout=30) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.from_email, to_email, msg.as_string())

            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP AUTHENTICATION FAILED for {to_email}: {str(e)}")
            logger.error(f"  -> Check SMTP_USER ({self.smtp_user}) and SMTP_PASSWORD are correct")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP CONNECTION FAILED for {to_email}: {str(e)}")
            logger.error(f"  -> Check SMTP_HOST ({self.smtp_host}) and SMTP_PORT ({self.smtp_port})")
            logger.error("  -> GoDaddy SMTP: smtpout.secureserver.net (port 465 SSL or 587 TLS)")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"RECIPIENT REFUSED for {to_email}: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP ERROR for {to_email}: {type(e).__name__}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"UNEXPECTED ERROR sending to {to_email}: {type(e).__name__}: {str(e)}")
            return False

    def send_welcome_email(self, to_email: str) -> bool:
        """Send welcome/confirmation email to new subscriber"""
        subject = "Welcome to Cheshire Today — Your Daily Local & Business Brief"
        tracking_id = self._generate_tracking_id("welcome")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f3f4f6;">
            <div style="max-width: 680px; margin: 0 auto; padding: 20px;">
                <!-- Header with Logo -->
                <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); color: white; padding: 35px 25px; text-align: center; border-radius: 16px 16px 0 0;">
                    <a href="{self.base_url}" style="display: inline-block; margin-bottom: 15px;">
                        <img src="{self.base_url}/logo.png" alt="Cheshire Today" style="height: 80px; width: auto;" />
                    </a>
                    <h1 style="margin: 0 0 8px 0; font-size: 24px; font-weight: 600; color: #ffffff;">Welcome to Cheshire Today</h1>
                    <p style="margin: 0; font-size: 14px; color: #E0E7FF; font-weight: 500;">Your trusted source for Cheshire news</p>
                </div>
                
                <!-- Content -->
                <div style="background: #ffffff; padding: 30px 25px;">
                    <h2 style="color: #1E3A8A; margin: 0 0 15px 0; font-size: 20px;">Thank you for subscribing! 🎉</h2>
                    <p style="color: #444; font-size: 15px; margin-bottom: 20px;">
                        You're now part of the Cheshire Today community. We're thrilled to have you with us and can't wait to keep you informed about everything happening in our beautiful region.
                    </p>
                    
                    <div style="background: #f8fafc; border-radius: 12px; padding: 20px; margin: 25px 0;">
                        <h3 style="color: #1E3A8A; margin: 0 0 15px 0; font-size: 16px;">📬 What to expect:</h3>
                        <table cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td style="padding: 8px 0;">
                                    <span style="color: #3B82F6; font-weight: bold;">☀️ The Daily Brief</span>
                                    <span style="color: #666;"> — Top Cheshire stories every morning at 7:30 AM</span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0;">
                                    <span style="color: #3B82F6; font-weight: bold;">📰 Weekly Roundup</span>
                                    <span style="color: #666;"> — The week's best stories every Sunday at 9:00 AM</span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0;">
                                    <span style="color: #3B82F6; font-weight: bold;">🚨 Breaking News</span>
                                    <span style="color: #666;"> — Urgent alerts for major local stories</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-radius: 12px; padding: 20px; margin: 25px 0;">
                        <h3 style="color: #166534; margin: 0 0 10px 0; font-size: 16px;">🏠 We Cover:</h3>
                        <p style="color: #166534; margin: 0; font-size: 14px;">
                            <strong>Cheshire</strong> • Crewe • Macclesfield • Wilmslow • Chester • Warrington • Nantwich • Congleton • Northwich • Knutsford & more
                        </p>
                    </div>
                    
                    <p style="color: #444; font-size: 15px; margin-bottom: 25px;">
                        Your first Daily Brief will arrive tomorrow at 7:30 AM. In the meantime, why not explore our latest stories?
                    </p>
                    
                    <div style="text-align: center;">
                        <a href="{self.base_url}" style="display: inline-block; background: #1E3A8A; color: white; padding: 14px 35px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px;">
                            Read Latest News →
                        </a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #1f2937; color: #9ca3af; padding: 25px; text-align: center; border-radius: 0 0 16px 16px;">
                    <p style="margin: 0 0 10px 0; font-size: 13px;">
                        Follow us for breaking news and updates
                    </p>
                    <div style="margin: 15px 0;">
                        <a href="https://facebook.com/CheshireTodayUK" style="color: #9ca3af; text-decoration: none; margin: 0 10px;">Facebook</a>
                        <a href="https://twitter.com/CheshireTodayUK" style="color: #9ca3af; text-decoration: none; margin: 0 10px;">Twitter</a>
                    </div>
                    <p style="margin: 15px 0 0 0; font-size: 11px; color: #6b7280;">
                        © 2026 Cheshire Today. All rights reserved.<br>
                        To unsubscribe, reply to this email with "Unsubscribe" in the subject line.
                    </p>
                </div>
            
                    <div style="margin-top: 25px; padding-top: 18px; border-top: 1px solid #e5e7eb; text-align: center;">
                        <p style="margin: 0 0 8px 0; font-size: 12px; color: #6b7280;">
                            Manage your emails:
                            <a href="__PREFS_URL__" style="color: #2563eb; text-decoration: none; font-weight: 600;">Preferences</a>
                            &nbsp;·&nbsp;
                            <a href="__UNSUB_URL__" style="color: #2563eb; text-decoration: none; font-weight: 600;">Unsubscribe</a>
                        </p>
                        <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                            You’re receiving this because you subscribed to Cheshire Today.
                        </p>
                    </div>
</div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Cheshire Today! 📰
        
        Thank you for subscribing!
        
        You're now part of the Cheshire Today community. We're thrilled to have you with us!
        
        WHAT TO EXPECT:
        ☀️ The Daily Brief - Top Cheshire stories every morning at 7:30 AM
        📰 Weekly Roundup - The week's best stories every Sunday at 9:00 AM  
        🚨 Breaking News - Urgent alerts for major local stories
        
        WE COVER:
        Cheshire, Crewe, Macclesfield, Wilmslow, Chester, Warrington, Nantwich, Congleton, Northwich, Knutsford & more
        
        Your first Daily Brief will arrive tomorrow at 7:30 AM.
        
        Read Latest News: {self.base_url}
        
        ---
        Follow us: Facebook & Twitter @CheshireTodayUK
        To unsubscribe, reply with "Unsubscribe" in the subject line.
        © 2026 Cheshire Today. All rights reserved.
        """
        

        # Personalise + track footer links (one-click)
        from urllib.parse import quote
        prefs_url = f"{self.base_url}/newsletter/preferences?email={quote(to_email)}"
        unsub_url = f"{self.base_url}/unsubscribe?email={quote(to_email)}"
        tracked_prefs = self._get_tracked_url(tracking_id, prefs_url)
        tracked_unsub = self._get_tracked_url(tracking_id, unsub_url)
        html_content = html_content.replace("__PREFS_URL__", tracked_prefs).replace("__UNSUB_URL__", tracked_unsub)
        # Personalize prefs/unsub links per-recipient (one-click) + track
        from urllib.parse import quote
        tracking_id = self._generate_tracking_id("welcome")
        prefs_url = f"{self.base_url}/newsletter/preferences?email={quote(to_email)}"
        unsub_url = f"{self.base_url}/unsubscribe?email={quote(to_email)}"
        tracked_prefs = self._get_tracked_url(tracking_id, prefs_url)
        tracked_unsub = self._get_tracked_url(tracking_id, unsub_url)
        html_personal = html_content.replace("__PREFS_URL__", tracked_prefs).replace("__UNSUB_URL__", tracked_unsub)

        return self._send_email(to_email, subject, html_personal, text_content)

    def send_verification_code(self, to_email: str, name: str, code: str) -> bool:
        """Send email verification code for comment login"""
        subject = "🔐 Cheshire Today - Your Verification Code"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; text-align: center; }}
                .code {{ font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #1E3A8A; background: white; padding: 20px 40px; border-radius: 10px; display: inline-block; margin: 20px 0; border: 2px dashed #1E3A8A; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">🔐 Verification Code</h1>
                    <p style="margin: 10px 0 0 0;">Cheshire Today Comments</p>
                </div>
                <div class="content">
                    <p>Hi <strong>{name}</strong>!</p>
                    <p>Use this code to verify your email and start commenting:</p>
                    
                    <div class="code">{code}</div>
                    
                    <p style="color: #666; font-size: 14px;">This code expires in <strong>10 minutes</strong>.</p>
                    <p style="color: #666; font-size: 14px;">If you didn't request this, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2026 Cheshire Today. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {name}!
        
        Your Cheshire Today verification code is: {code}
        
        This code expires in 10 minutes.
        
        If you didn't request this, please ignore this email.
        
        ---
        © 2026 Cheshire Today. All rights reserved.
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_job_approved_email(self, to_email: str, contact_name: str, job_title: str, company: str) -> bool:
        """Send notification when a job listing is approved"""
        subject = f"✅ Your Job Listing is Now Live - {job_title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; margin-top: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #059669 0%, #0d9488 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">🎉 Great News!</h1>
                    <p style="color: #a7f3d0; margin: 10px 0 0 0;">Your job listing has been approved</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <p style="color: #374151; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                        Hi {contact_name},
                    </p>
                    
                    <p style="color: #374151; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                        Your job listing for <strong>{job_title}</strong> at <strong>{company}</strong> has been reviewed and approved. It's now live on the Cheshire Jobs board!
                    </p>
                    
                    <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                        <p style="margin: 0; color: #065f46; font-weight: 600;">{job_title}</p>
                        <p style="margin: 5px 0 0 0; color: #047857;">{company}</p>
                    </div>
                    
                    <p style="color: #374151; font-size: 16px; line-height: 1.6; margin: 0 0 25px 0;">
                        Your listing is now visible to thousands of job seekers across Cheshire. We hope you find the perfect candidate!
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.base_url}/jobs" style="display: inline-block; background: #059669; color: white; padding: 14px 35px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                            View Job Board →
                        </a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #1f2937; text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
                    <p style="margin: 0;">
                        <a href="{self.base_url}" style="color: #60a5fa; text-decoration: none;">Cheshire Today</a> • Cheshire Jobs
                    </p>
                    <p style="margin: 10px 0 0 0; color: #6b7280;">
                        © 2026 Cheshire Today. All rights reserved.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Hi {contact_name},

Great news! Your job listing for {job_title} at {company} has been approved and is now live on the Cheshire Jobs board.

View the job board: {self.base_url}/jobs

We hope you find the perfect candidate!

Best regards,
Cheshire Today Jobs Team
        """
        
        return self._send_email(to_email, subject, html_content, text_content)

    def send_job_rejected_email(self, to_email: str, contact_name: str, job_title: str, company: str, reason: str = None) -> bool:
        """Send notification when a job listing is rejected"""
        subject = f"Update on Your Job Listing - {job_title}"
        
        reason_text = reason if reason else "The listing did not meet our guidelines or contained incomplete information."
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; margin-top: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">Job Listing Update</h1>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <p style="color: #374151; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                        Hi {contact_name},
                    </p>
                    
                    <p style="color: #374151; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                        Thank you for submitting your job listing for <strong>{job_title}</strong> at <strong>{company}</strong>. Unfortunately, we were unable to approve it at this time.
                    </p>
                    
                    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                        <p style="margin: 0; color: #92400e; font-weight: 600;">Reason:</p>
                        <p style="margin: 5px 0 0 0; color: #a16207;">{reason_text}</p>
                    </div>
                    
                    <p style="color: #374151; font-size: 16px; line-height: 1.6; margin: 0 0 25px 0;">
                        You're welcome to submit a new listing with updated information. If you have any questions, please reply to this email.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.base_url}/jobs/post" style="display: inline-block; background: #059669; color: white; padding: 14px 35px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                            Submit New Listing →
                        </a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #1f2937; text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
                    <p style="margin: 0;">
                        <a href="{self.base_url}" style="color: #60a5fa; text-decoration: none;">Cheshire Today</a> • Cheshire Jobs
                    </p>
                    <p style="margin: 10px 0 0 0; color: #6b7280;">
                        © 2026 Cheshire Today. All rights reserved.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Hi {contact_name},

Thank you for submitting your job listing for {job_title} at {company}. Unfortunately, we were unable to approve it at this time.

Reason: {reason_text}

You're welcome to submit a new listing with updated information at: {self.base_url}/jobs/post

If you have any questions, please reply to this email.

Best regards,
Cheshire Today Jobs Team
        """
        
        return self._send_email(to_email, subject, html_content, text_content)

    # ============================================
    # NEW EMAIL TEMPLATES (January 2026)
    # ============================================
    
    def send_daily_brief(self, to_emails: List[str], articles: List[dict], 
                         weather: dict = None, travel: dict = None, 
                         photo_of_day: dict = None) -> Tuple[int, str]:
        """
        Send The Daily Brief - Morning news digest at 07:30 AM
        
        Args:
            to_emails: List of subscriber email addresses
            articles: List of article dictionaries (hero + 3-5 secondary)
            weather: Weather data dict with keys: temp, condition, location
            travel: Travel updates dict with keys: m6_status, rail_status
            photo_of_day: Community photo dict with keys: image_url, caption, credit
            
        Returns:
            Tuple of (success_count, tracking_id)
        """
        if not articles:
            logger.warning("No articles for Daily Brief")
            return 0, None
        
        # Generate tracking ID for this send
        tracking_id = self._generate_tracking_id("daily_brief")
        
        today = datetime.now().strftime('%A, %d %B %Y')
        subject = f"📈 Cheshire Market & Local Briefing | {today} | Cheshire Today"
        
        # Hero article (first article) with tracked URL
        hero = articles[0]
        hero_id = hero.get('id', hero.get('_id', ''))
        hero_url_original = self._article_url(hero)
        hero_url = self._get_tracked_url(tracking_id, hero_url_original)
        hero_image = hero.get('image', '')
        hero_summary = hero.get('content', '')[:200].strip()
        if hero_summary:
            hero_summary = hero_summary + '...'
        
        
        # ================================
        # Secondary candidates (exclude hero)
        secondary_articles = articles[1:]

        # =====================================
        # Authority Segmentation (Cheshire Model)
        # Order priority: Local → Business/Finance → AI/Tech → National Context
        # =====================================

        local_articles = []
        business_articles = []
        tech_articles = []
        other_articles = []

        towns = [
            'crewe','macclesfield','wilmslow','chester',
            'warrington','nantwich','congleton','northwich',
            'knutsford','sandbach','middlewich','winsford','ellesmere port'
        ]


        def _is_banned_category(cat: str, title: str) -> bool:
            c = (cat or "").lower().strip()
            t = (title or "").lower().strip()

            banned_exact = {
                "sports","sport",
                "entertainment","showbiz","celebrity",
                "gaming","games"
            }
            if c in banned_exact:
                return True

            banned_contains = ["sport", "entertain", "showbiz", "celebrity", "gaming", "game"]
            if any(x in c for x in banned_contains):
                return True

            # Title-only noise filters (prevents AI/Tech being polluted by pop culture)
            title_banned = ["resident evil", "trailer", "review", "episode", "season", "netflix", "film", "movie", "music"]
            if any(x in t for x in title_banned):
                return True

            return False

        def _is_local(cat: str, title: str) -> bool:
            # Local must be truly Cheshire (do NOT infer from category/source alone)
            t = (title or "").lower()
            return ("cheshire" in t) or any(town in t for town in towns)

        def _is_business(cat: str, title: str = "") -> bool:
            # Business + Finance pillar (project aligned)
            c = (cat or "").lower()
            t = (title or "").lower()
            cat_keys = ['business','finance','economy','economic','property','housing','real estate']
            title_keys = ['budget','tax','hmrc','vat','council tax','interest rate','mortgage','inflation','wages','profits','revenue','funding','investment','shares','stock','bank','house price','rent']
            return any(k in c for k in cat_keys) or any(k in t for k in title_keys)

        def _is_tech(cat: str, title: str) -> bool:


            # AI & Tech pillar (strict). Prevents science/nature drifting into AI section.


            c = (cat or '').lower()


            t = (title or '').lower()


        


            # Strong AI/tech signals (allow even if category is messy)


            strong = [


                'openai','anthropic','chatgpt','gemini','deepmind','artificial intelligence',


                'machine learning','ml','llm','gpt','copilot',


                'nvidia','semiconductor','chip','gpu',


                'cyber','security','ransomware','hack','breach',


                'data centre','datacenter','cloud','saas','software','api'


            ]


        


            # Clear non-tech/nature/science terms that must NOT land in AI section


            nontech = [


                'fungal','seabird','woodland','marine','conservation','biodiversity',


                'climate','environment','wildlife','nature','charity says'


            ]


        


            has_strong = any(k in t for k in strong)


        


            # If it looks like nature/science, only allow if strong AI/tech keyword is present


            if any(x in t for x in nontech) or any(x in c for x in ['science','environment']):


                return has_strong


        


            # Category-driven tech (safe)


            if any(x in c for x in ['tech','technology','ai']):


                return True


        


            # Title-driven tech


            return has_strong


        
        # ===== FORCE CLEAN REBUCKETING (Project Pillar Enforcement) =====
        local_articles = []
        business_articles = []
        tech_articles = []
        other_articles = []

        for article in secondary_articles:
            cat = (article.get('category') or '').lower()
            title = (article.get('title') or '').lower()

            if _is_banned_category(cat, title):
                continue

            if _is_local(cat, title):
                local_articles.append(article)
            elif _is_tech(cat, title):
                tech_articles.append(article)
            elif _is_business(cat, title):
                business_articles.append(article)
            else:
                other_articles.append(article)

        
        # ===== FORCE BUCKET REVALIDATION (ensures strict helper logic applies) =====
        local_articles = [a for a in local_articles if _is_local((a.get('category') or '').lower(), (a.get('title') or '').lower())]
        business_articles = [a for a in business_articles if _is_business((a.get('category') or '').lower(), (a.get('title') or '').lower())]
        tech_articles = [a for a in tech_articles if _is_tech((a.get('category') or '').lower(), (a.get('title') or '').lower())]
        other_articles = [
            a for a in other_articles
            if not _is_banned_category((a.get('category') or '').lower(), (a.get('title') or '').lower())
        ]
# Promote into empty buckets (prevents weird “AI empty” / “Business empty” days)
        def _promote_into(bucket: str):
            nonlocal local_articles, business_articles, tech_articles, other_articles
            for a in list(other_articles):
                c = (a.get('category') or '').lower()
                t = (a.get('title') or '').lower()
                if _is_banned_category(c, t):
                    other_articles.remove(a)
                    continue

                if bucket == "tech" and _is_tech(c, t):
                    other_articles.remove(a)
                    tech_articles.insert(0, a)
                    return True
                if bucket == "business" and _is_business(c, t):
                    other_articles.remove(a)
                    business_articles.insert(0, a)
                    return True
                if bucket == "local" and _is_local(c, t):
                    other_articles.remove(a)
                    local_articles.insert(0, a)
                    return True
            return False

        if len(business_articles) == 0:
            _promote_into("business")
        if len(tech_articles) == 0:
            _promote_into("tech")

        # Section caps (match email layout)
        local_articles = local_articles[:3]
        business_articles = business_articles[:2]
        tech_articles = tech_articles[:1]
        other_articles = other_articles[:2]

        # ===== AI/TECH 48h Fallback =====
        if len(tech_articles) == 0:
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
                cursor = self.db.articles.find({"publishedDate": {"$gte": cutoff.isoformat()}}, {"_id": 1, "title": 1, "category": 1}).sort("publishedDate", -1).limit(20)
                for a in cursor:
                    cat = (a.get("category") or "").lower()
                    title = (a.get("title") or "").lower()
                    if _is_tech(cat, title) and (a not in local_articles) and (a not in business_articles):
                        tech_articles = [a]
                        break
            except Exception:
                pass

        # ===== REBUCKET VALIDATION (post-cap) =====
        _all = (local_articles + business_articles + tech_articles + other_articles)
        local_articles = []
        business_articles = []
        tech_articles = []
        other_articles = []

        for article in _all:
            cat = (article.get('category') or '').lower()
            title = (article.get('title') or '').lower()
            if _is_banned_category(cat, title):
                continue
            if _is_local(cat, title):
                local_articles.append(article)
            elif _is_tech(cat, title):
                tech_articles.append(article)
            elif _is_business(cat, title):
                business_articles.append(article)
            else:
                other_articles.append(article)

        # Re-apply caps after validation
        local_articles = local_articles[:3]
        business_articles = business_articles[:2]
        tech_articles = tech_articles[:1]
        other_articles = other_articles[:2]

        # =====================================
        # AI/Tech 48h Fallback (Mongo)
        # Ensures AI authority presence even on slow days
        # =====================================
        if len(tech_articles) == 0:
            try:
                
                cutoff = datetime.now(timezone.utc) - timedelta(hours=48)

                recent_candidates = []
                cursor = self.db.articles.find(
                    {"publishedDate": {"$gte": cutoff.isoformat()}},
                    {"_id": 1, "title": 1, "category": 1}
                ).sort("publishedDate", -1).limit(20)

                for a in cursor:
                    cat = (a.get("category") or "").lower()
                    title = (a.get("title") or "").lower()
                    if _is_tech(cat, title):
                        if (a not in local_articles) and (a not in business_articles):
                            tech_articles = [a]
                            break
            except Exception:
                # Fail silently — never break email rendering
                pass


        def build_section(title_label, emoji, section_articles):
            if not section_articles:
                return ""

            rows = ""
            for article in section_articles:
                art_id = article.get('id', article.get('_id', ''))
                art_url_original = self._article_url(article)
                art_url = self._get_tracked_url(tracking_id, art_url_original)

                rows += f'''
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">
                        <a href="{art_url}" style="color: #1E3A8A; text-decoration: none; font-size: 15px; font-weight: 600; line-height: 1.4;">
                            {article.get('title')}
                        </a>
                    </td>
                </tr>
                '''

            return f'''
            <div style="margin: 30px 0;">
                <div style="border-top:1px solid #e5e7eb; margin-top:30px; padding-top:20px;">
                <h3 style="color:#111827; font-size:12px; text-transform:uppercase; letter-spacing:1.5px; font-weight:700; margin:0 0 12px 0;">
                    {title_label.upper()}
                </h3>
                <table width="100%" cellpadding="0" cellspacing="0">
                    {rows}
                </table>
            </div>
            '''

        # Utility block (Weather, Travel, Fuel)
        utility_html = ""
        if weather or travel:
            utility_html = '''
            <div style="background: #f8fafc; border-radius: 12px; padding: 20px; margin: 25px 0;">
                <h3 style="color: #1E3A8A; font-size: 14px; margin: 0 0 15px 0; text-transform: uppercase; letter-spacing: 1px;">
                    📍 Cheshire At A Glance
                </h3>
                <table width="100%" cellpadding="0" cellspacing="0">
            '''
            
            if weather:
                utility_html += f'''
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">
                            <strong>🌤️ Weather:</strong> {weather.get('temp', 'N/A')}°C, {weather.get('condition', 'N/A')} in {weather.get('location', 'Cheshire')}
                        </td>
                    </tr>
                '''
            
            if travel:
                m6_status = travel.get('m6_status', 'No major incidents reported')
                rail_status = travel.get('rail_status', 'Services running normally')
                utility_html += f'''
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">
                            <strong>🚗 M6:</strong> {m6_status}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0;">
                            <strong>🚆 Rail:</strong> {rail_status}
                        </td>
                    </tr>
                '''
            
            utility_html += '''
                </table>
            </div>
            '''
        
        # Community block (Photo of the Day)
        community_html = ""
        if photo_of_day and photo_of_day.get('image_url'):
            community_html = f'''
            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 12px; padding: 20px; margin: 25px 0; text-align: center;">
                <h3 style="color: #92400e; font-size: 14px; margin: 0 0 15px 0; text-transform: uppercase; letter-spacing: 1px;">
                    📸 Photo of the Day
                </h3>
                <img src="{photo_of_day.get('image_url')}" alt="Photo of the Day" style="max-width: 100%; border-radius: 8px; margin-bottom: 10px;" />
                <p style="color: #78350f; font-size: 14px; margin: 0; font-style: italic;">
                    {photo_of_day.get('caption', '')}
                </p>
                <p style="color: #92400e; font-size: 12px; margin: 5px 0 0 0;">
                    📷 {photo_of_day.get('credit', 'Reader submission')}
                </p>
            </div>
            '''
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="color-scheme" content="light">
            <meta name="supported-color-schemes" content="light">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 0; background-color: #f3f4f6;">
            <div style="max-width: 680px; margin: 0 auto; padding: 20px;">
                <!-- Header with Text Logo -->
                <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
                    <div style="font-size: 28px; font-weight: 800; letter-spacing: -1px; margin-bottom: 5px;">
                        CHESHIRE TODAY
                    </div>
                    <div style="font-size: 12px; letter-spacing: 2px; opacity: 0.9; margin-bottom: 15px;">
                        Local · Business · Finance
                    </div>
                    <div style="background: rgba(255,255,255,0.2); padding: 10px 20px; border-radius: 8px; display: inline-block;">
                        <h1 style="margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.3px;">📈 Cheshire Market &amp; Local Briefing</h1>
                        <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.95;">{today}</p>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div style="background: #ffffff; padding: 25px; border-radius: 0 0 12px 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Hero Section -->
                    <div style="margin-bottom: 25px;">
                        {f'<a href="{hero_url}"><img src="{hero_image}" alt="" style="width: 100%; height: 280px; object-fit: cover; border-radius: 10px; margin-bottom: 15px;" /></a>' if hero_image else ''}
                        <h2 style="color: #1E3A8A; margin: 0 0 10px 0; font-size: 22px; line-height: 1.3;">
                            <a href="{hero_url}" style="color: #1E3A8A; text-decoration: none;">{hero.get('title', 'Top Story')}</a>
                        </h2>
                        <p style="color: #374151; font-size: 15px; margin: 0 0 15px 0; line-height: 1.6;">
                            {hero_summary}
                        </p>
                    </div>
                    
                    
                    {build_section("Local Developments", "📰", local_articles)}
                    {build_section("Business & Finance", "💼", business_articles)}
                    {build_section("AI & Technology", "🤖", tech_articles)}
                    {build_section("National Context", "🇬🇧", other_articles)}

                    
                    {utility_html}
                    {community_html}
                    
                    <!-- Footer -->
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center;">
                        <p style="color: #6b7280; font-size: 12px; margin: 0 0 10px 0;">
                            You're receiving this because you subscribed to The Daily Brief.
                        </p>
                        <p style="margin: 0;">
                            <a href="__PREFS_URL__" style="color: #3B82F6; font-size: 12px; text-decoration: none;">Manage Preferences</a>
                            &nbsp;|&nbsp;
                            <a href="__UNSUB_URL__" style="color: #3B82F6; font-size: 12px; text-decoration: none;">Unsubscribe</a>
                        </p>
                        <p style="color: #9ca3af; font-size: 11px; margin: 15px 0 0 0;">
                            © {datetime.now().year} Cheshire Today. All rights reserved.
                        </p>
                    </div>
                    <!-- Tracking Pixel -->
                    {self._get_tracking_pixel(tracking_id)}
                </div>
            </div>
        </body>
        </html>
        '''
        
        # Send to all subscribers with daily_brief preference
        batch_messages = []
        for email in to_emails:
            from urllib.parse import quote
            prefs_url = f"{self.base_url}/newsletter/preferences?email={quote(email)}"
            unsub_url = f"{self.base_url}/unsubscribe?email={quote(email)}"
            tracked_prefs = self._get_tracked_url(tracking_id, prefs_url)
            tracked_unsub = self._get_tracked_url(tracking_id, unsub_url)
            html_personal = html_content.replace("__PREFS_URL__", tracked_prefs).replace("__UNSUB_URL__", tracked_unsub)
            batch_messages.append({
                "to": email,
                "subject": subject,
                "html": html_personal,
                "text": None,
            })

        if getattr(self, "resend_enabled", False):
            success_count = self._send_resend_batch(batch_messages)
        else:
            success_count = 0
            for item in batch_messages:
                if self._send_email(item["to"], item["subject"], item["html"], item["text"]):
                    success_count += 1
        
        logger.info(f"Daily Brief sent to {success_count}/{len(to_emails)} subscribers (tracking: {tracking_id})")
        return success_count, tracking_id

    def send_breaking_news(self, to_emails: List[str], headline: str, 
                           bullet_points: List[str], article_url: str = None) -> Tuple[int, str]:
        """
        Send Breaking News Alert - High urgency, manual trigger only
        
        Args:
            to_emails: List of subscriber email addresses
            headline: Main breaking news headline
            bullet_points: List of "What we know" bullet points (max 5)
            article_url: URL to live updates page
            
        Returns:
            Tuple of (success_count, tracking_id)
        """
        if not headline:
            logger.warning("No headline for Breaking News alert")
            return 0, None
        
        # Generate tracking ID for this send
        tracking_id = self._generate_tracking_id("breaking_news")
        
        subject = f"🚨 BREAKING: {headline[:60]} | Cheshire Today"
        
        # Build bullet points HTML
        bullets_html = ""
        for point in bullet_points[:5]:
            bullets_html += f'''
            <tr>
                <td style="padding: 8px 0; padding-left: 20px; color: #1f2937; font-size: 15px;">
                    • {point}
                </td>
            </tr>
            '''
        
        # CTA button with tracking
        cta_html = ""
        if article_url:
            tracked_url = self._get_tracked_url(tracking_id, article_url)
            cta_html = f'''
            <div style="text-align: center; margin-top: 25px;">
                <a href="{tracked_url}" style="display: inline-block; background: #dc2626; color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">
                    Follow Live Updates →
                </a>
            </div>
            '''
        
        # Lightweight HTML template for fast loading
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #fef2f2;">
            <div style="max-width: 600px; margin: 0 auto; padding: 15px;">
                <!-- Red Alert Bar -->
                <div style="background: #dc2626; color: white; padding: 15px; text-align: center; border-radius: 8px 8px 0 0;">
                    <span style="font-size: 20px; font-weight: 800; letter-spacing: 2px;">
                        🚨 BREAKING NEWS ALERT
                    </span>
                </div>
                
                <!-- Content -->
                <div style="background: white; padding: 25px; border-radius: 0 0 8px 8px; border: 2px solid #dc2626; border-top: none;">
                    <!-- Headline -->
                    <h1 style="color: #1f2937; font-size: 26px; line-height: 1.3; margin: 0 0 20px 0; font-weight: 700;">
                        {headline}
                    </h1>
                    
                    <!-- What We Know -->
                    <div style="background: #fef2f2; padding: 15px; border-radius: 8px; border-left: 4px solid #dc2626;">
                        <h3 style="color: #991b1b; font-size: 13px; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 1px;">
                            What We Know:
                        </h3>
                        <table width="100%" cellpadding="0" cellspacing="0">
                            {bullets_html}
                        </table>
                    </div>
                    
                    {cta_html}
                    
                    <!-- Footer -->
                    <div style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
                        <p style="color: #6b7280; font-size: 11px; margin: 0;">
                            You received this alert because you're subscribed to Breaking News.
                            <a href="__PREFS_URL__" style="color: #dc2626;">Manage preferences</a>
                        </p>
                    </div>
                    <!-- Tracking Pixel -->
                    {self._get_tracking_pixel(tracking_id)}
                </div>
            </div>
        </body>
        </html>
        '''
        
        # Send to all subscribers with breaking_news preference
        success_count = 0
        for email in to_emails:
            # Personalize prefs/unsub links per-recipient (one-click)
            from urllib.parse import quote
            prefs_url = f"{self.base_url}/newsletter/preferences?email={quote(email)}"
            unsub_url = f"{self.base_url}/unsubscribe?email={quote(email)}"
            tracked_prefs = self._get_tracked_url(tracking_id, prefs_url)
            tracked_unsub = self._get_tracked_url(tracking_id, unsub_url)
            html_personal = html_content.replace("__PREFS_URL__", tracked_prefs).replace("__UNSUB_URL__", tracked_unsub)
            if self._send_email(email, subject, html_personal):
                success_count += 1
        
        logger.info(f"Breaking News alert sent to {success_count}/{len(to_emails)} subscribers (tracking: {tracking_id})")
        return success_count, tracking_id

    def send_weekly_roundup(self, to_emails: List[str], big_read: dict,
                            icymi_articles: List[dict], property_of_week: dict = None,
                            food_review: dict = None) -> Tuple[int, str]:
        """
        Send The Weekly Roundup - Sunday morning at 09:00 AM
        
        Args:
            to_emails: List of subscriber email addresses
            big_read: Featured article dict (week's best performer)
            icymi_articles: Top 5 trending articles for "In Case You Missed It"
            property_of_week: Property listing dict with keys: title, price, location, image_url, url
            food_review: Food/drink review dict with keys: title, venue, rating, image_url, url
            
        Returns:
            Tuple of (success_count, tracking_id)
        """
        if not big_read:
            logger.warning("No big read article for Weekly Roundup")
            return 0, None
        
        # Generate tracking ID for this send
        tracking_id = self._generate_tracking_id("weekly_roundup")
        
        today = datetime.now().strftime('%d %B %Y')
        subject = f"📰 The Weekly Roundup | Week of {today} | Cheshire Today"
        
        # Big Read section with tracked URL
        big_read_id = big_read.get('id', big_read.get('_id', ''))
        big_read_url_original = self._article_url(big_read)
        big_read_url = self._get_tracked_url(tracking_id, big_read_url_original)
        big_read_image = big_read.get('image', '')
        big_read_excerpt = big_read.get('content', '')[:300].strip() + '...'
        
        # ICYMI section with tracked URLs
        icymi_html = ""
        for i, article in enumerate(icymi_articles[:5], 1):
            art_id = article.get('id', article.get('_id', ''))
            art_url_original = self._article_url(article)
            art_url = self._get_tracked_url(tracking_id, art_url_original)
            icymi_html += f'''
            <tr>
                <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
                    <span style="background: #1E3A8A; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; margin-right: 10px;">
                        {i}
                    </span>
                    <a href="{art_url}" style="color: #1f2937; text-decoration: none; font-size: 15px; font-weight: 500;">
                        {article.get('title', 'Untitled')}
                    </a>
                </td>
            </tr>
            '''
        
        # Property of the Week
        property_html = ""
        if property_of_week and property_of_week.get('title'):
            property_url = self._get_tracked_url(tracking_id, property_of_week.get("url", "")) if property_of_week.get('url') else ""
            property_html = f'''
            <div style="background: #f0fdf4; border-radius: 12px; padding: 20px; margin: 25px 0;">
                <h3 style="color: #166534; font-size: 14px; margin: 0 0 15px 0; text-transform: uppercase; letter-spacing: 1px;">
                    🏠 Property of the Week
                </h3>
                {f'<img src="{property_of_week.get("image_url")}" alt="" style="width: 100%; height: 150px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;" />' if property_of_week.get('image_url') else ''}
                <h4 style="color: #1f2937; margin: 0 0 5px 0; font-size: 16px;">{property_of_week.get('title')}</h4>
                <p style="color: #166534; font-weight: 600; margin: 0 0 5px 0;">{property_of_week.get('price', 'Price on application')}</p>
                <p style="color: #6b7280; font-size: 13px; margin: 0 0 10px 0;">📍 {property_of_week.get('location', 'Cheshire')}</p>
                {f'<a href="{property_url}" style="color: #166534; font-size: 13px;">View Details →</a>' if property_url else ''}
            </div>
            '''
        
        # Food & Drink Review
        food_html = ""
        if food_review and food_review.get('title'):
            stars = '⭐' * int(food_review.get('rating', 4))
            food_html = f'''
            <div style="background: #fef3c7; border-radius: 12px; padding: 20px; margin: 25px 0;">
                <h3 style="color: #92400e; font-size: 14px; margin: 0 0 15px 0; text-transform: uppercase; letter-spacing: 1px;">
                    🍽️ Food & Drink
                </h3>
                {f'<img src="{food_review.get("image_url")}" alt="" style="width: 100%; height: 150px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;" />' if food_review.get('image_url') else ''}
                <h4 style="color: #1f2937; margin: 0 0 5px 0; font-size: 16px;">{food_review.get('title')}</h4>
                <p style="color: #92400e; margin: 0 0 5px 0;">{food_review.get('venue', '')}</p>
                <p style="margin: 0 0 10px 0;">{stars}</p>
                {f'<a href="{food_review.get("url")}" style="color: #92400e; font-size: 13px;">Read Review →</a>' if food_review.get('url') else ''}
            </div>
            '''
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Georgia, 'Times New Roman', serif; line-height: 1.7; color: #333; margin: 0; padding: 0; background-color: #f9fafb;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #1E3A8A 0%, #1e40af 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                    <img src="https://cheshiretoday.co.uk/logo-white.png" alt="Cheshire Today" style="height: 35px; margin-bottom: 15px;" onerror="this.style.display='none'" />
                    <h1 style="margin: 0; font-size: 28px; font-weight: 400; font-family: Georgia, serif;">The Weekly Roundup</h1>
                    <p style="margin: 8px 0 0 0; font-size: 14px; opacity: 0.9; font-family: sans-serif;">Your Sunday digest of Cheshire's best stories</p>
                </div>
                
                <!-- Content -->
                <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    
                    <!-- The Big Read -->
                    <div style="margin-bottom: 35px;">
                        <p style="color: #1E3A8A; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin: 0 0 15px 0; font-family: sans-serif;">
                            ✦ The Big Read
                        </p>
                        {f'<a href="{big_read_url}"><img src="{big_read_image}" alt="" style="width: 100%; height: 250px; object-fit: cover; border-radius: 10px; margin-bottom: 20px;" /></a>' if big_read_image else ''}
                        <h2 style="color: #1f2937; margin: 0 0 15px 0; font-size: 26px; line-height: 1.3; font-weight: 400;">
                            <a href="{big_read_url}" style="color: #1f2937; text-decoration: none;">{big_read.get('title', 'Featured Story')}</a>
                        </h2>
                        <p style="color: #4b5563; font-size: 16px; margin: 0 0 20px 0; line-height: 1.7;">
                            {big_read_excerpt}
                        </p>
                        <a href="{big_read_url}" style="display: inline-block; background: #1E3A8A; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px; font-family: sans-serif;">
                            Continue Reading
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 2px solid #e5e7eb; margin: 30px 0;" />
                    
                    <!-- ICYMI -->
                    <div style="margin: 30px 0;">
                        <h3 style="color: #1E3A8A; font-size: 14px; margin: 0 0 20px 0; text-transform: uppercase; letter-spacing: 2px; font-family: sans-serif;">
                            📌 In Case You Missed It
                        </h3>
                        <table width="100%" cellpadding="0" cellspacing="0" style="font-family: -apple-system, sans-serif;">
                            {icymi_html}
                        </table>
                    </div>
                    
                    {property_html}
                    {food_html}
                    
                    <!-- Footer -->
                    <div style="margin-top: 35px; padding-top: 25px; border-top: 2px solid #e5e7eb; text-align: center; font-family: sans-serif;">
                        <p style="color: #6b7280; font-size: 12px; margin: 0 0 10px 0;">
                            You're receiving The Weekly Roundup every Sunday.
                        </p>
                        <p style="margin: 0;">
                            <a href="__PREFS_URL__" style="color: #3B82F6; font-size: 12px; text-decoration: none;">Manage Preferences</a>
                            &nbsp;|&nbsp;
                            <a href="__UNSUB_URL__" style="color: #3B82F6; font-size: 12px; text-decoration: none;">Unsubscribe</a>
                        </p>
                        <p style="color: #9ca3af; font-size: 11px; margin: 15px 0 0 0;">
                            © {datetime.now().year} Cheshire Today. All rights reserved.
                        </p>
                    </div>
                    <!-- Tracking Pixel -->
                    {self._get_tracking_pixel(tracking_id)}
                </div>
            </div>
        </body>
        </html>
        '''
        
        batch_messages = []
        for email in to_emails:
            # Personalize prefs/unsub links per-recipient (one-click)
            from urllib.parse import quote
            prefs_url = f"{self.base_url}/newsletter/preferences?email={quote(email)}"
            unsub_url = f"{self.base_url}/unsubscribe?email={quote(email)}"
            tracked_prefs = self._get_tracked_url(tracking_id, prefs_url)
            tracked_unsub = self._get_tracked_url(tracking_id, unsub_url)
            html_personal = html_content.replace("__PREFS_URL__", tracked_prefs).replace("__UNSUB_URL__", tracked_unsub)
            batch_messages.append({
                "to": email,
                "subject": subject,
                "html": html_personal,
                "text": None,
            })

        if getattr(self, "resend_enabled", False):
            success_count = self._send_resend_batch(batch_messages)
        else:
            success_count = 0
            for item in batch_messages:
                if self._send_email(item["to"], item["subject"], item["html"], item["text"]):
                    success_count += 1
        
        logger.info(f"Weekly Roundup sent to {success_count}/{len(to_emails)} subscribers (tracking: {tracking_id})")
        return success_count, tracking_id

    def send_announcement_email(self, to_emails: List[str]) -> int:
        """
        Send one-time announcement email about the new email strategy.
        Announces migration to Daily Brief and provides preference link.
        """
        subject = "We've made some changes to Cheshire Today 📩"
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f3f4f6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); color: white; padding: 35px 25px; text-align: center; border-radius: 12px 12px 0 0;">
                    <img src="https://cheshiretoday.co.uk/logo-white.png" alt="Cheshire Today" style="height: 40px; margin-bottom: 15px;" onerror="this.style.display='none'" />
                    <h1 style="margin: 0; font-size: 26px; font-weight: 700;">A better way to stay informed</h1>
                </div>
                
                <!-- Content -->
                <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <p style="font-size: 16px; color: #4b5563; margin: 0 0 20px 0;">
                        Hello,
                    </p>
                    
                    <p style="font-size: 16px; color: #4b5563; margin: 0 0 20px 0;">
                        We're excited to share some changes to how we deliver Cheshire Today to your inbox. 
                        We've been listening to your feedback and are moving to a <strong>curated model</strong> 
                        that prioritises quality over quantity.
                    </p>
                    
                    <div style="background: #f0f9ff; border-left: 4px solid #3B82F6; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                        <h3 style="color: #1E3A8A; margin: 0 0 15px 0; font-size: 16px;">Here's what's new:</h3>
                        <ul style="color: #4b5563; margin: 0; padding-left: 20px;">
                            <li style="margin-bottom: 10px;"><strong>The Daily Brief</strong> — One email, every morning at 7:30 AM with the top Cheshire stories</li>
                            <li style="margin-bottom: 10px;"><strong>The Weekly Roundup</strong> — A Sunday digest of the week's best content</li>
                            <li style="margin-bottom: 0;"><strong>Breaking News Alerts</strong> — Rare, high-priority notifications only when it matters</li>
                        </ul>
                    </div>
                    
                    <p style="font-size: 16px; color: #4b5563; margin: 0 0 20px 0;">
                        <strong>You have been automatically moved to The Daily Brief</strong> (7:30 AM). 
                        This replaces our previous multiple-daily emails.
                    </p>
                    
                    <p style="font-size: 16px; color: #4b5563; margin: 0 0 25px 0;">
                        If you'd prefer to receive news only once a week, or only want Breaking News alerts, 
                        you can update your preferences at any time:
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="__PREFS_URL__" style="display: inline-block; background: #1E3A8A; color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                            Update My Preferences
                        </a>
                    </div>
                    
                    <p style="font-size: 16px; color: #4b5563; margin: 25px 0 0 0;">
                        Thank you for being part of the Cheshire Today community.
                    </p>
                    
                    <p style="font-size: 16px; color: #4b5563; margin: 15px 0 0 0;">
                        Best,<br/>
                        <strong>The Editor</strong><br/>
                        <span style="color: #6b7280;">Cheshire Today</span>
                    </p>
                    
                    <!-- Footer -->
                    <div style="margin-top: 35px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center;">
                        <p style="color: #9ca3af; font-size: 11px; margin: 0;">
                            © {datetime.now().year} Cheshire Today. All rights reserved.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        
        success_count = 0
        for email in to_emails:
            # Personalize prefs/unsub links per-recipient (one-click)
            from urllib.parse import quote
            prefs_url = f"{self.base_url}/newsletter/preferences?email={quote(email)}"
            unsub_url = f"{self.base_url}/unsubscribe?email={quote(email)}"
            tracked_prefs = self._get_tracked_url(tracking_id, prefs_url)
            tracked_unsub = self._get_tracked_url(tracking_id, unsub_url)
            html_personal = html_content.replace("__PREFS_URL__", tracked_prefs).replace("__UNSUB_URL__", tracked_unsub)
            if self._send_email(email, subject, html_personal):
                success_count += 1
        
        logger.info(f"Announcement email sent to {success_count}/{len(to_emails)} subscribers")
        return success_count


# Global email service instance

    def send_site_update_part1(self, to_emails: List[str]) -> int:
        """Send Site Update (Part 1) — calm authority announcement."""
        subject = "Cheshire Today is evolving — here’s what it means for you"
        tracking_id = self._generate_tracking_id("SiteUpdatePart1")

        html_content = f"""<html><body>
        <h2>Cheshire Today has evolved.</h2>
        <p>We’ve rebuilt the platform to focus more clearly on what truly affects life across Cheshire.</p>
        <p><strong>What this means for you:</strong></p>
        <ul>
          <li>Stronger focus on Cheshire business and economic impact</li>
          <li>Clearer reporting on finance, tax and policy changes</li>
          <li>More insight into AI and technology shaping the region</li>
          <li>Improved performance and reliability across all devices</li>
        </ul>
        <p>Update your preferences: __PREFS_URL__</p>
        <p>Unsubscribe: __UNSUB_URL__</p>
        {self._get_tracking_pixel(tracking_id)}
        </body></html>"""

        success_count = 0
        for email in to_emails:
            from urllib.parse import quote
            prefs_url = f"{self.base_url}/newsletter/preferences?email={quote(email)}"
            unsub_url = f"{self.base_url}/unsubscribe?email={quote(email)}"
            tracked_prefs = self._get_tracked_url(tracking_id, prefs_url)
            tracked_unsub = self._get_tracked_url(tracking_id, unsub_url)
            html_personal = html_content.replace("__PREFS_URL__", tracked_prefs).replace("__UNSUB_URL__", tracked_unsub)
            if self._send_email(email, subject, html_personal):
                success_count += 1

        logger.info(f"Site Update Part 1 sent to {success_count}/{len(to_emails)} subscribers (tracking: {tracking_id})")
        return success_count

    def send_site_update_part2(self, to_emails: List[str]) -> int:
        """Send Site Update (Part 2) — reinforcement email."""
        subject = "What’s new on Cheshire Today"
        tracking_id = self._generate_tracking_id("SiteUpdatePart2")

        html_content = f"""<html><body>
        <h2>What’s new on Cheshire Today</h2>
        <ul>
          <li>Deeper local business coverage</li>
          <li>Practical finance and tax explainers</li>
          <li>AI & technology guides relevant to Cheshire</li>
          <li>Clearer categorisation and improved reading experience</li>
        </ul>
        <p>If there’s a topic you’d like us to explore, reply to this email.</p>
        <p>Update your preferences: __PREFS_URL__</p>
        <p>Unsubscribe: __UNSUB_URL__</p>
        {self._get_tracking_pixel(tracking_id)}
        </body></html>"""

        success_count = 0
        for email in to_emails:
            from urllib.parse import quote
            prefs_url = f"{self.base_url}/newsletter/preferences?email={quote(email)}"
            unsub_url = f"{self.base_url}/unsubscribe?email={quote(email)}"
            tracked_prefs = self._get_tracked_url(tracking_id, prefs_url)
            tracked_unsub = self._get_tracked_url(tracking_id, unsub_url)
            html_personal = html_content.replace("__PREFS_URL__", tracked_prefs).replace("__UNSUB_URL__", tracked_unsub)
            if self._send_email(email, subject, html_personal):
                success_count += 1

        logger.info(f"Site Update Part 2 sent to {success_count}/{len(to_emails)} subscribers (tracking: {tracking_id})")
        return success_count

email_service = EmailService()


