"""
Article generation and content cleaning service.
"""
import os
import re
import logging
import asyncio
from typing import List, Optional, Set
from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv

# --- dotenv: only for local dev ---
IS_RENDER = bool(
    os.getenv("RENDER")
    or os.getenv("RENDER_SERVICE_ID")
    or os.getenv("RENDER_EXTERNAL_URL")
)
if not IS_RENDER:

from emergentintegrations.llm.chat import LlmChat, UserMessage

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
    load_dotenv(ROOT_DIR / '.env', override=False)
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

logger = logging.getLogger(__name__)


def get_gemini_chat(session_id: str, system_message: str) -> LlmChat:
    """Create a Gemini chat instance for article generation"""
    return LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system_message
    ).with_model("gemini", "gemini-2.5-flash")


def clean_article_content(text: str) -> str:
    """Clean article content by removing markdown formatting, AI thinking, and improving readability."""
    bad_patterns = [
        r'^THOUGHT:.*$',
        r'^I need to write.*$',
        r'^I will write.*$',
        r'^Let me write.*$',
        r'^Here is the article.*$',
        r'^Here\'s the article.*$',
        r'NO markdown formatting.*',
        r'Write naturally as a.*',
        r'words in plain text.*',
        r'Crucially,.*formatting.*',
        r'This means no bold.*',
    ]
    
    for pattern in bad_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'  +', ' ', text)
    
    return text.strip()


async def generate_article_with_gemini(
    topic: str, 
    scope: str, 
    category: str, 
    used_photo_ids: Set[str] = None, 
    retry_count: int = 0
) -> Optional[dict]:
    """Generate an article using Gemini 2.5 Flash."""
    max_retries = 3
    retry_delay = 2
    
    try:
        if used_photo_ids is None:
            used_photo_ids = set()
        
        if scope == "cheshire":
            prompt = f"""Write a professional news article about: {topic}

Location: Cheshire, UK (mention Knutsford, Wilmslow, Alderley Edge, Chester, or Macclesfield where relevant)

Requirements:
- 300-400 words
- Plain text only, no formatting symbols
- Professional journalistic style
- Include realistic quotes and details

Output format:
HEADLINE
[Your headline here]

ARTICLE
[Your article text here - 3-4 paragraphs]

Start writing the article now:"""
        else:
            prompt = f"""Write a professional news article about: {topic}

Location: United Kingdom

Requirements:
- 300-400 words
- Plain text only, no formatting symbols
- Professional journalistic style
- Include realistic quotes and details

Output format:
HEADLINE
[Your headline here]

ARTICLE
[Your article text here - 3-4 paragraphs]

Start writing the article now:"""
        
        chat = get_gemini_chat(
            session_id=f"article-gen-{uuid4()}",
            system_message="You are a professional British news journalist. Output ONLY the article content. Never output your thinking process, instructions, or meta-commentary. Write the headline and article directly without any preamble."
        )
        
        user_message = UserMessage(text=prompt)
        full_text = await chat.send_message(user_message)
        full_text = full_text.strip()
        
        bad_indicators = ['THOUGHT:', 'I need to write', 'I will write', 'Let me write', 
                         'Here is the article', 'Here\'s the article', 'NO markdown',
                         'words in plain text', 'Crucially,', 'This means no bold',
                         'Let\'s brainstorm', 'brainstorm some', 'Let me think', 'I should write',
                         'current/recent', 'Here are some', 'topics to write about']
        
        has_bad_content = any(indicator.lower() in full_text.lower() for indicator in bad_indicators)
        if has_bad_content:
            logger.warning("Detected AI reasoning in output, cleaning and retrying if needed...")
            if 'ARTICLE' in full_text:
                parts = full_text.split('ARTICLE', 1)
                if len(parts) > 1:
                    full_text = parts[1].strip()
            elif '\n\n' in full_text:
                paragraphs = full_text.split('\n\n')
                for i, para in enumerate(paragraphs):
                    if not any(ind.lower() in para.lower() for ind in bad_indicators):
                        full_text = '\n\n'.join(paragraphs[i:])
                        break
        
        if 'HEADLINE' in full_text and 'ARTICLE' in full_text:
            headline_match = re.search(r'HEADLINE\s*\n(.+?)(?=\n\s*ARTICLE|\n\n)', full_text, re.DOTALL)
            article_match = re.search(r'ARTICLE\s*\n(.+)', full_text, re.DOTALL)
            
            if headline_match and article_match:
                title = headline_match.group(1).strip()
                content = article_match.group(1).strip()
            else:
                lines = full_text.split('\n', 1)
                title = lines[0].strip()
                content = lines[1].strip() if len(lines) > 1 else full_text
        else:
            lines = full_text.split('\n', 1)
            title = lines[0].strip().replace('#', '').replace('**', '').strip()
            content = lines[1].strip() if len(lines) > 1 else full_text
        
        title = re.sub(r'^HEADLINE[:\s]*', '', title, flags=re.IGNORECASE).strip()
        content = re.sub(r'^ARTICLE[:\s]*', '', content, flags=re.IGNORECASE).strip()
        
        title = re.sub(r'\[\d+\]', '', title).strip()
        content = re.sub(r'\[\d+\]', '', content).strip()
        
        title = re.sub(r'\s+', ' ', title).strip()
        content = re.sub(r'\s+', ' ', content).strip()
        
        content = clean_article_content(content)
        title = clean_article_content(title)
        
        final_bad_check = ['THOUGHT:', 'I need to', 'I will ', 'Let me ', 'Here is', 'Here\'s', 
                          'words in plain', 'NO markdown', 'formatting symbols',
                          'Let\'s brainstorm', 'brainstorm', 'current/recent', 'topics to write']
        
        title_has_bad = any(ind.lower() in title.lower() for ind in final_bad_check)
        content_has_bad = any(ind.lower() in content[:200].lower() for ind in final_bad_check)
        
        if title_has_bad or content_has_bad:
            logger.error(f"Article still contains AI reasoning after cleaning. Title: {title[:50]}")
            if retry_count < max_retries:
                logger.info("Retrying article generation...")
                await asyncio.sleep(1)
                return await generate_article_with_gemini(topic, scope, category, used_photo_ids, retry_count + 1)
            return None
        
        if len(content) < 100:
            logger.warning(f"Article content too short ({len(content)} chars), retrying...")
            if retry_count < max_retries:
                await asyncio.sleep(1)
                return await generate_article_with_gemini(topic, scope, category, used_photo_ids, retry_count + 1)
            return None
        
        tags = []
        if scope == "cheshire":
            tags.append("cheshire")
        else:
            tags.append("uk")
        tags.append(category.lower().replace(' ', '-'))
        
        logger.info(f"Generated clean article: '{title[:40]}...' ({len(content)} chars)")
        
        return {
            'title': title,
            'content': content,
            'category': category,
            'tags': tags,
            'image': None
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating article (attempt {retry_count + 1}/{max_retries}): {error_msg}")
        
        if retry_count < max_retries and ("Connection" in error_msg or "500" in error_msg or "429" in error_msg):
            wait_time = retry_delay * (retry_count + 1)
            logger.info(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            return await generate_article_with_gemini(topic, scope, category, used_photo_ids, retry_count + 1)
        
        raise


async def fetch_trending_headlines_from_rss(news_feed_service, count: int = 5) -> List[dict]:
    """Fetch trending headlines from actual RSS feeds (FREE)."""
    try:
        logger.info("Fetching trending headlines from RSS feeds (FREE)...")
        
        all_articles = await news_feed_service.fetch_all_feeds()
        
        headlines = []
        seen_titles = set()
        
        for article in all_articles[:count * 3]:
            title = article.get('title', '').strip()
            if not title or title.lower() in seen_titles:
                continue
            
            is_local = article.get('is_cheshire_related', False)
            scope = 'cheshire' if is_local else 'uk'
            
            headlines.append({
                'headline': title,
                'category': article.get('category', 'UK News'),
                'scope': scope,
                'source': article.get('source', 'BBC News'),
                'source_url': article.get('source_url', '')
            })
            seen_titles.add(title.lower())
            
            if len(headlines) >= count:
                break
        
        logger.info(f"Retrieved {len(headlines)} trending headlines from RSS")
        return headlines
        
    except Exception as e:
        logger.error(f"Error fetching RSS headlines: {str(e)}")
        return []


async def fetch_trending_headlines(scope: str, count: int = 5) -> List[tuple]:
    """Fetch trending news headlines using Gemini."""
    try:
        logger.info(f"Fetching trending headlines for {scope}...")
        
        valid_categories = ["Local News", "UK News", "Business", "Health", "Sports", "Tech", "Weather", "Food"]
        valid_categories_str = ", ".join(valid_categories)
        
        if scope == "cheshire":
            prompt = f"""Identify the top {count} most important news stories in Cheshire, UK.
            Focus on Knutsford, Wilmslow, Alderley Edge, Macclesfield, and Chester.
            Assign each story a category from: [{valid_categories_str}].
            
            Return in this format (one per line):
            Headline | Category"""
        else:
            prompt = f"""Identify the top {count} most important news stories in the United Kingdom.
            Focus on major national developments.
            Assign each story a category from: [{valid_categories_str}].
            
            Return in this format (one per line):
            Headline | Category"""

        chat = get_gemini_chat(
            session_id=f"headlines-{scope}-{uuid4()}",
            system_message="You are a news editor. Return headlines in the exact format requested."
        )
        
        user_message = UserMessage(text=prompt)
        content = await chat.send_message(user_message)
        content = content.strip()
        
        lines = content.split('\n')
        
        topics = []
        for line in lines:
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    topic = parts[0].strip()
                    category = parts[1].strip()
                    if category not in valid_categories:
                        category = "Local News" if scope == "cheshire" else "UK News"
                    topics.append((topic, category))
        
        logger.info(f"Found {len(topics)} trending topics for {scope}")
        return topics
        
    except Exception as e:
        logger.error(f"Error fetching trending headlines: {str(e)}")
        return []
