"""
Root entrypoint for Render.

Render starts: uvicorn server:app
Our FastAPI app is implemented in: backend/server.py
"""
from backend.server import app  # noqa: F401
