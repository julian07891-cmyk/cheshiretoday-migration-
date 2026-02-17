"""
Admin authentication service.
"""
import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, Header
from pathlib import Path
from dotenv import load_dotenv

# --- dotenv: only for local dev ---
IS_RENDER = bool(
    os.getenv("RENDER")
    or os.getenv("RENDER_SERVICE_ID")
    or os.getenv("RENDER_EXTERNAL_URL")
)
if not IS_RENDER:

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
    load_dotenv(ROOT_DIR / '.env', override=False)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME') or os.getenv('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or os.getenv('ADMIN_PASS', 'changeme')

# Simple token store (in production, use Redis or database)
admin_tokens = {}


def generate_admin_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


def verify_admin_token(token: str) -> bool:
    """Verify if a token is valid and not expired"""
    if token in admin_tokens:
        expiry = admin_tokens[token]
        if datetime.now(timezone.utc) < expiry:
            return True
        else:
            # Token expired, remove it
            del admin_tokens[token]
    return False


async def get_admin_auth(authorization: Optional[str] = Header(None)) -> bool:
    """Dependency to verify admin authentication"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract token from "Bearer <token>" format
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        if verify_admin_token(token):
            return True
    
    raise HTTPException(status_code=401, detail="Invalid or expired token")
