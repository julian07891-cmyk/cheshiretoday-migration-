"""
Pydantic schemas for request/response models.
"""
import uuid
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional


class Article(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: str
    author: str = "AI Journalist"
    publishedDate: str
    image: str
    tags: List[str] = []
    featured: bool = False
    source: str = "Perplexity AI"
    scope: str  # "cheshire" or "uk"


class GenerateArticlesRequest(BaseModel):
    count: int = 10
    include_uk_news: bool = True


class GenerateArticlesResponse(BaseModel):
    success: bool
    generated: int
    cheshire_articles: int
    uk_articles: int


class SubscribeRequest(BaseModel):
    email: EmailStr


class SubscribeResponse(BaseModel):
    success: bool
    message: str


class GenerateFromHeadlineRequest(BaseModel):
    headline: str
    category: str = "Local News"
    scope: str = "uk"


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str
    expires_in: int = 86400  # 24 hours in seconds


class HybridNewsRequest(BaseModel):
    cheshire_articles: int = 8
    uk_articles: int = 4
    use_perplexity: bool = True
