"""
Application configuration and environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# --- dotenv: only for local dev ---
IS_RENDER = bool(
    os.getenv("RENDER")
    or os.getenv("RENDER_SERVICE_ID")
    or os.getenv("RENDER_EXTERNAL_URL")
)
ROOT_DIR = Path(__file__).parent
if not IS_RENDER:
    load_dotenv(ROOT_DIR / '.env', override=False)
# Admin credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME') or os.getenv('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or os.getenv('ADMIN_PASS', 'changeme')

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# MongoDB
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']
