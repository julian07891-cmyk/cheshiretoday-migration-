"""
Facebook OAuth Service for Long-Lived Access Tokens
Handles the OAuth flow to obtain and refresh long-lived page access tokens.

SETUP REQUIRED:
1. Create a Facebook App at developers.facebook.com
2. Add the following permissions: pages_manage_posts, pages_read_engagement
3. Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in .env
4. Configure OAuth redirect URI in Facebook App settings
"""
import os
import httpx
import logging
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class FacebookOAuthService:
    def __init__(self):
        self.app_id = os.environ.get('FACEBOOK_APP_ID', '')
        self.app_secret = os.environ.get('FACEBOOK_APP_SECRET', '')
        self.page_id = os.environ.get('FACEBOOK_PAGE_ID', '')
        self.base_url = "https://graph.facebook.com/v18.0"
        
        # OAuth redirect URI - should match your app settings
        self.redirect_uri = os.environ.get(
            'FACEBOOK_OAUTH_REDIRECT_URI',
            'https://cheshiretoday.co.uk/api/facebook/oauth/callback'
        )
    
    @property
    def is_configured(self) -> bool:
        """Check if OAuth is configured"""
        return bool(self.app_id and self.app_secret)
    
    def get_authorization_url(self, state: str = "") -> str:
        """
        Get the Facebook OAuth authorization URL.
        User should be redirected here to authorize the app.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL string
        """
        if not self.is_configured:
            raise ValueError("Facebook OAuth not configured. Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET.")
        
        scopes = "pages_manage_posts,pages_read_engagement,pages_show_list"
        
        return (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.app_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scopes}"
            f"&state={state}"
            f"&response_type=code"
        )
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from Facebook callback
            
        Returns:
            Dict with access_token or error
        """
        if not self.is_configured:
            return {"success": False, "error": "Facebook OAuth not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/oauth/access_token",
                    params={
                        "client_id": self.app_id,
                        "redirect_uri": self.redirect_uri,
                        "client_secret": self.app_secret,
                        "code": code
                    },
                    timeout=30.0
                )
                
                result = response.json()
                
                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"].get("message", "Unknown error")
                    }
                
                # Got short-lived user access token
                user_token = result.get("access_token")
                
                if not user_token:
                    return {"success": False, "error": "No access token in response"}
                
                # Exchange for long-lived user token
                long_lived = await self.get_long_lived_user_token(user_token)
                
                if not long_lived.get("success"):
                    return long_lived
                
                # Get page access token
                page_token = await self.get_page_access_token(long_lived["access_token"])
                
                return page_token
                
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_long_lived_user_token(self, short_lived_token: str) -> Dict:
        """
        Exchange short-lived user token for long-lived token.
        Long-lived tokens last ~60 days.
        
        Args:
            short_lived_token: Short-lived user access token
            
        Returns:
            Dict with long-lived access_token or error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/oauth/access_token",
                    params={
                        "grant_type": "fb_exchange_token",
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "fb_exchange_token": short_lived_token
                    },
                    timeout=30.0
                )
                
                result = response.json()
                
                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"].get("message", "Unknown error")
                    }
                
                return {
                    "success": True,
                    "access_token": result.get("access_token"),
                    "token_type": result.get("token_type", "bearer"),
                    "expires_in": result.get("expires_in", 5184000)  # ~60 days
                }
                
        except Exception as e:
            logger.error(f"Error getting long-lived token: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_page_access_token(self, user_token: str) -> Dict:
        """
        Get page access token from user access token.
        Page tokens never expire if obtained from long-lived user token.
        
        Args:
            user_token: Long-lived user access token
            
        Returns:
            Dict with page access_token or error
        """
        if not self.page_id:
            return {"success": False, "error": "FACEBOOK_PAGE_ID not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me/accounts",
                    params={
                        "access_token": user_token,
                        "fields": "id,name,access_token"
                    },
                    timeout=30.0
                )
                
                result = response.json()
                
                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"].get("message", "Unknown error")
                    }
                
                # Find our page
                pages = result.get("data", [])
                page = next((p for p in pages if p.get("id") == self.page_id), None)
                
                if not page:
                    return {
                        "success": False,
                        "error": f"Page {self.page_id} not found in user's pages",
                        "available_pages": [{"id": p.get("id"), "name": p.get("name")} for p in pages]
                    }
                
                return {
                    "success": True,
                    "page_id": page.get("id"),
                    "page_name": page.get("name"),
                    "access_token": page.get("access_token"),
                    "never_expires": True
                }
                
        except Exception as e:
            logger.error(f"Error getting page access token: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def validate_token(self, token: str) -> Dict:
        """
        Validate an access token and check its expiration.
        
        Args:
            token: Access token to validate
            
        Returns:
            Dict with token info or error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/debug_token",
                    params={
                        "input_token": token,
                        "access_token": f"{self.app_id}|{self.app_secret}"
                    },
                    timeout=30.0
                )
                
                result = response.json()
                data = result.get("data", {})
                
                if data.get("error"):
                    return {
                        "success": False,
                        "valid": False,
                        "error": data["error"].get("message", "Token invalid")
                    }
                
                expires_at = data.get("expires_at", 0)
                is_valid = data.get("is_valid", False)
                
                return {
                    "success": True,
                    "valid": is_valid,
                    "app_id": data.get("app_id"),
                    "type": data.get("type"),
                    "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat() if expires_at else None,
                    "scopes": data.get("scopes", [])
                }
                
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return {"success": False, "error": str(e)}


# Singleton instance
facebook_oauth = FacebookOAuthService()
