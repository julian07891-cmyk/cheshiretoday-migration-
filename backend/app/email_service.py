"""
Email Service for Cheshire Today Newsletter
Handles sending confirmation and newsletter emails via SMTP
Updated: January 2026 - New tiered email strategy with analytics tracking
"""

import smtplib
import os
import uuid
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.from_email = os.environ.get('SMTP_FROM_EMAIL')
        # Updated: From name is now "Editor at Cheshire Today"
        self.from_name = os.environ.get('SMTP_FROM_NAME', 'Editor at Cheshire Today')
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
        
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send an email via SMTP (supports Gmail, GoDaddy, etc.)"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Reply-To'] = self.reply_to
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email using appropriate method based on port
            if self.smtp_port == 465:
                # Use SMTP_SSL for port 465 (GoDaddy, etc.)
                import ssl
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=30) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # Use SMTP with STARTTLS for port 587 (Gmail, GoDaddy, etc.)
                import ssl
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP AUTHENTICATION FAILED for {to_email}: {str(e)}")
            logger.error(f"  -> Check SMTP_USER ({self.smtp_user}) and SMTP_PASSWORD are correct")
            logger.error(f"  -> For GoDaddy: Use your full email as username and email password")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP CONNECTION FAILED for {to_email}: {str(e)}")
            logger.error(f"  -> Check SMTP_HOST ({self.smtp_host}) and SMTP_PORT ({self.smtp_port})")
            logger.error(f"  -> GoDaddy SMTP: smtpout.secureserver.net (port 465 SSL or 587 TLS)")
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
        subject = "Welcome to Cheshire Today! 📰 Your Local News Awaits"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f3f4f6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <!-- Header with Logo -->
                <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); color: white; padding: 35px 25px; text-align: center; border-radius: 16px 16px 0 0;">
                    <a href="{self.base_url}" style="display: inline-block; margin-bottom: 15px;">
                        <img src="{self.base_url}/logo.png" alt="Cheshire Today" style="height: 80px; width: auto;" />
                    </a>
                    <h1 style="margin: 0 0 8px 0; font-size: 24px; font-weight: 600; color: #ffffff;">Welcome to the Family!</h1>
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
        
        return self._send_email(to_email, subject, html_content, text_content)
    
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
    
    def send_news_digest(self, to_emails: List[str], articles: List[dict], digest_time: str = "Daily", sponsor: dict = None) -> int:
        """
        DEPRECATED: This method is kept for backwards compatibility only.
        Use send_daily_brief() for the new tiered email system.
        
        Send news digest to multiple subscribers (OLD FORMAT - 3x daily)
        
        Args:
            to_emails: List of subscriber email addresses
            articles: List of article dictionaries
            digest_time: Time label for the digest (Morning, Midday, Evening, Daily, Test)
            sponsor: Optional sponsor info dict with keys: name, tagline, url, logo_url
        """
        logger.warning("DEPRECATED: send_news_digest() called - use send_daily_brief() instead")
        if not articles:
            logger.warning("No articles to send in digest")
            return 0
        
        # Format time labels
        time_labels = {
            "Morning": "☀️ Good Morning",
            "Midday": "🌤️ Midday Update", 
            "Evening": "🌙 Evening Roundup",
            "Daily": "📰 Cheshire Today Newsletter",
            "Test": "📰 Cheshire Today Newsletter"  # Test emails show same as Daily to subscribers
        }
        greeting = time_labels.get(digest_time, "📰 Cheshire Today Newsletter")
        
        subject = f"{greeting} - {len(articles)} Cheshire Stories | Cheshire Today"
        
        # Build sponsor section HTML if sponsor is provided
        sponsor_html = ""
        if sponsor and sponsor.get('name'):
            sponsor_html = f"""
            <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 2px solid #86efac; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
                <p style="color: #166534; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 10px 0;">Today's News Brought To You By</p>
                {f'<img src="{sponsor.get("logo_url")}" alt="{sponsor.get("name")}" style="max-height: 50px; margin-bottom: 10px;" />' if sponsor.get('logo_url') else ''}
                <h3 style="color: #047857; margin: 0 0 5px 0; font-size: 18px;">{sponsor.get('name')}</h3>
                <p style="color: #666; font-size: 14px; margin: 0 0 15px 0;">{sponsor.get('tagline', '')}</p>
                {f'<a href="{sponsor.get("url")}" style="display: inline-block; background: #047857; color: white; padding: 10px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Learn More</a>' if sponsor.get('url') else ''}
            </div>
            """
        
        # Build featured article (first article with larger display)
        featured_article = articles[0] if articles else None
        featured_html = ""
        if featured_article:
            article_id = featured_article.get('id', featured_article.get('_id', ''))
            article_url = f"{self.base_url}/article/{article_id}"
            # DEBUG: Log article URL generation
            logger.info(f"DIGEST DEBUG - Featured article: id={article_id}, url={article_url}, title={featured_article.get('title', '')[:40]}")
            image_url = featured_article.get('image', '')
            summary = featured_article.get('content', '')[:250]
            
            featured_html = f"""
            <div style="margin-bottom: 30px;">
                <p style="color: #1E3A8A; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;">⭐ Top Story</p>
                {f'<a href="{article_url}"><img src="{image_url}" alt="" style="width: 100%; height: 200px; object-fit: cover; border-radius: 12px; margin-bottom: 15px;" /></a>' if image_url else ''}
                <h2 style="color: #1E3A8A; margin: 0 0 10px 0; font-size: 22px; line-height: 1.3;">
                    <a href="{article_url}" style="color: #1E3A8A; text-decoration: none;">
                        {featured_article.get('title', 'Untitled')}
                    </a>
                </h2>
                <p style="color: #666; font-size: 13px; margin-bottom: 10px;">
                    {featured_article.get('category', 'News')} • {featured_article.get('author', 'Cheshire Today')}
                </p>
                <p style="color: #444; line-height: 1.6; font-size: 15px;">
                    {summary}...
                </p>
                <a href="{article_url}" style="display: inline-block; background: #1E3A8A; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 10px;">
                    Read Full Story →
                </a>
            </div>
            <hr style="border: none; border-top: 2px solid #e5e7eb; margin: 25px 0;" />
            """
        
        # Build remaining articles HTML (2-column grid style)
        articles_html = ""
        remaining_articles = articles[1:10] if len(articles) > 1 else []
        
        for i, article in enumerate(remaining_articles):
            article_id_val = article.get('id', article.get('_id', ''))
            article_url = f"{self.base_url}/article/{article_id_val}"
            # DEBUG: Log each article URL
            logger.info(f"DIGEST DEBUG - Article {i+2}: id={article_id_val}, url={article_url}, title={article.get('title', '')[:30]}")
            image_url = article.get('image', '')
            summary = article.get('content', '')[:120]
            
            articles_html += f"""
            <div style="margin-bottom: 25px; padding-bottom: 20px; border-bottom: 1px solid #e5e7eb;">
                <table cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                        {f'<td width="100" style="vertical-align: top; padding-right: 15px;"><a href="{article_url}"><img src="{image_url}" alt="" style="width: 100px; height: 75px; object-fit: cover; border-radius: 8px;" /></a></td>' if image_url else ''}
                        <td style="vertical-align: top;">
                            <p style="color: #1E3A8A; font-size: 11px; margin: 0 0 5px 0; text-transform: uppercase;">
                                {article.get('category', 'News')}
                            </p>
                            <h3 style="color: #333; margin: 0 0 8px 0; font-size: 16px; line-height: 1.3;">
                                <a href="{article_url}" style="color: #333; text-decoration: none;">
                                    {article.get('title', 'Untitled')}
                                </a>
                            </h3>
                            <p style="color: #666; font-size: 13px; margin: 0; line-height: 1.4;">
                                {summary}...
                            </p>
                        </td>
                    </tr>
                </table>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f3f4f6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); color: white; padding: 35px 25px; text-align: center; border-radius: 16px 16px 0 0;">
                    <a href="{self.base_url}" style="display: inline-block; margin-bottom: 20px; text-decoration: none;">
                        <img src="{self.base_url}/logo.png" alt="Cheshire Today" style="height: 80px; width: auto;" />
                    </a>
                    <a href="{self.base_url}" style="text-decoration: none; display: block;">
                        <h2 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 600; color: #ffffff;">Your Daily Cheshire News Awaits!</h2>
                        <p style="margin: 0; font-size: 14px; color: #E0E7FF; font-weight: 500;">{len(articles)} handpicked stories just for you</p>
                    </a>
                </div>
                
                <!-- Content -->
                <div style="background: #ffffff; padding: 30px 25px;">
                    {sponsor_html}
                    
                    {featured_html}
                    
                    <h3 style="color: #1E3A8A; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 20px;">
                        📋 More Stories
                    </h3>
                    
                    {articles_html}
                    
                    <!-- CTA Button -->
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px;">
                        <a href="{self.base_url}" style="display: inline-block; background: #1E3A8A; color: white; padding: 14px 35px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px;">
                            View All Stories →
                        </a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #1f2937; text-align: center; padding: 25px; color: #9ca3af; font-size: 12px; border-radius: 0 0 16px 16px;">
                    <p style="margin: 0 0 10px 0;">
                        <a href="{self.base_url}" style="color: #60a5fa; text-decoration: none;">Cheshire Today</a> • 
                        Your Local News Source
                    </p>
                    <p style="margin: 0; color: #6b7280;">
                        © 2026 Cheshire Today. All rights reserved.<br/>
                        <a href="{self.base_url}/privacy" style="color: #9ca3af;">Privacy Policy</a> • 
                        <a href="{self.base_url}/terms" style="color: #9ca3af;">Terms of Service</a>
                    </p>
                    <p style="margin: 15px 0 0 0; font-size: 11px; color: #6b7280;">
                        To unsubscribe, reply with "Unsubscribe" in the subject line.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send to each subscriber
        success_count = 0
        for email in to_emails:
            if self._send_email(email, subject, html_content):
                success_count += 1
        
        logger.info(f"News digest sent to {success_count}/{len(to_emails)} subscribers")
        return success_count

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
        subject = f"☀️ The Daily Brief | {today} | Cheshire Today"
        
        # Hero article (first article) with tracked URL
        hero = articles[0]
        hero_id = hero.get('id', hero.get('_id', ''))
        hero_url_original = f"{self.base_url}/article/{hero_id}"
        hero_url = self._get_tracked_url(tracking_id, hero_url_original)
        hero_image = hero.get('image', '')
        hero_summary = hero.get('content', '')[:200].strip()
        if hero_summary:
            hero_summary = hero_summary + '...'
        
        # Secondary headlines (next 3-5 articles) with tracked URLs AND IMAGES
        secondary_articles = articles[1:6]
        secondary_html = ""
        for article in secondary_articles:
            art_id = article.get('id', article.get('_id', ''))
            art_url_original = f"{self.base_url}/article/{art_id}"
            art_url = self._get_tracked_url(tracking_id, art_url_original)
            art_image = article.get('image', '')
            
            # Add thumbnail image if available
            image_html = ""
            if art_image:
                image_html = f'''
                    <td style="width: 80px; padding-right: 12px; vertical-align: top;">
                        <a href="{art_url}">
                            <img src="{art_image}" alt="" style="width: 80px; height: 60px; object-fit: cover; border-radius: 6px;" />
                        </a>
                    </td>
                '''
            
            secondary_html += f'''
            <tr>
                <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            {image_html}
                            <td style="vertical-align: top;">
                                <a href="{art_url}" style="color: #1E3A8A; text-decoration: none; font-size: 15px; font-weight: 600; line-height: 1.3;">
                                    {article.get('title', 'Untitled')}
                                </a>
                                <span style="color: #6b7280; font-size: 12px; display: block; margin-top: 4px;">
                                    {article.get('category', 'News')}
                                </span>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
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
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <!-- Header with Text Logo -->
                <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
                    <div style="font-size: 28px; font-weight: 800; letter-spacing: -1px; margin-bottom: 5px;">
                        CHESHIRE TODAY
                    </div>
                    <div style="font-size: 12px; letter-spacing: 2px; opacity: 0.9; margin-bottom: 15px;">
                        YOUR LOCAL NEWS
                    </div>
                    <div style="background: rgba(255,255,255,0.2); padding: 10px 20px; border-radius: 8px; display: inline-block;">
                        <h1 style="margin: 0; font-size: 22px; font-weight: 700;">☀️ The Daily Brief</h1>
                        <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.95;">{today}</p>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div style="background: #ffffff; padding: 25px; border-radius: 0 0 12px 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Hero Section -->
                    <div style="margin-bottom: 25px;">
                        {f'<a href="{hero_url}"><img src="{hero_image}" alt="" style="width: 100%; height: 220px; object-fit: cover; border-radius: 10px; margin-bottom: 15px;" /></a>' if hero_image else ''}
                        <h2 style="color: #1E3A8A; margin: 0 0 10px 0; font-size: 22px; line-height: 1.3;">
                            <a href="{hero_url}" style="color: #1E3A8A; text-decoration: none;">{hero.get('title', 'Top Story')}</a>
                        </h2>
                        <p style="color: #374151; font-size: 15px; margin: 0 0 15px 0; line-height: 1.6;">
                            {hero_summary}
                        </p>
                        <a href="{hero_url}" style="display: inline-block; background: #1E3A8A; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px;">
                            Read More →
                        </a>
                    </div>
                    
                    <!-- Secondary Headlines with Images -->
                    <div style="margin: 25px 0;">
                        <h3 style="color: #1f2937; font-size: 14px; margin: 0 0 15px 0; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #1E3A8A; padding-bottom: 8px;">
                            📰 More Headlines
                        </h3>
                        <table width="100%" cellpadding="0" cellspacing="0">
                            {secondary_html}
                        </table>
                    </div>
                    
                    {utility_html}
                    {community_html}
                    
                    <!-- Footer -->
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center;">
                        <p style="color: #6b7280; font-size: 12px; margin: 0 0 10px 0;">
                            You're receiving this because you subscribed to The Daily Brief.
                        </p>
                        <p style="margin: 0;">
                            <a href="{self.base_url}/newsletter/preferences" style="color: #3B82F6; font-size: 12px; text-decoration: none;">Manage Preferences</a>
                            &nbsp;|&nbsp;
                            <a href="{self.base_url}/unsubscribe" style="color: #3B82F6; font-size: 12px; text-decoration: none;">Unsubscribe</a>
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
        success_count = 0
        for email in to_emails:
            if self._send_email(email, subject, html_content):
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
                            <a href="{self.base_url}/newsletter/preferences" style="color: #dc2626;">Manage preferences</a>
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
            if self._send_email(email, subject, html_content):
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
        big_read_url_original = f"{self.base_url}/article/{big_read_id}"
        big_read_url = self._get_tracked_url(tracking_id, big_read_url_original)
        big_read_image = big_read.get('image', '')
        big_read_excerpt = big_read.get('content', '')[:300].strip() + '...'
        
        # ICYMI section with tracked URLs
        icymi_html = ""
        for i, article in enumerate(icymi_articles[:5], 1):
            art_id = article.get('id', article.get('_id', ''))
            art_url_original = f"{self.base_url}/article/{art_id}"
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
                            <a href="{self.base_url}/newsletter/preferences" style="color: #3B82F6; font-size: 12px; text-decoration: none;">Manage Preferences</a>
                            &nbsp;|&nbsp;
                            <a href="{self.base_url}/unsubscribe" style="color: #3B82F6; font-size: 12px; text-decoration: none;">Unsubscribe</a>
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
        
        success_count = 0
        for email in to_emails:
            if self._send_email(email, subject, html_content):
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
                        <a href="{self.base_url}/newsletter/preferences" style="display: inline-block; background: #1E3A8A; color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
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
            if self._send_email(email, subject, html_content):
                success_count += 1
        
        logger.info(f"Announcement email sent to {success_count}/{len(to_emails)} subscribers")
        return success_count


# Global email service instance
email_service = EmailService()
