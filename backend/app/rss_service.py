import feedparser
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging
import requests
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class RSSService:
    """Service for consuming and processing RSS feeds"""
    
    def __init__(self, perplexity_api_key: str):
        self.perplexity_api_key = perplexity_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Cheshire News Aggregator/1.0'
        })
    
    def fetch_rss_feed(self, feed_url: str) -> Optional[feedparser.FeedParserDict]:
        """Fetch and parse RSS feed from URL"""
        try:
            logger.info(f"Fetching RSS feed from: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            return feed
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {str(e)}")
            return None
    
    def extract_text_from_html(self, html_content: str) -> str:
        """Extract plain text from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            return text
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {str(e)}")
            return html_content
    
    def summarize_with_perplexity(self, title: str, content: str, max_words: int = 300) -> Dict[str, str]:
        """Use Perplexity to rewrite and summarize article with Cheshire context"""
        try:
            # Create prompt for Perplexity
            prompt = f"""Rewrite the following news article for Cheshire News readers. 
            Make it relevant to Cheshire, North West England if possible. 
            Keep it factual and journalistic. Target length: {max_words} words.
            
            Original Title: {title}
            Original Content: {content[:2000]}
            
            Provide:
            1. A new compelling headline (keep it under 100 characters)
            2. A rewritten article body that's engaging and well-structured
            
            Format your response as:
            HEADLINE: [your headline here]
            CONTENT: [your rewritten content here]"""
            
            # Call Perplexity API
            response = self.session.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.perplexity_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.1-sonar-small-128k-online',
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are an expert journalist for Cheshire News, rewriting and localizing news stories for Cheshire readers.'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'max_tokens': 1000,
                    'temperature': 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_text = result['choices'][0]['message']['content']
                
                # Parse the response
                headline_match = re.search(r'HEADLINE:\s*(.+?)(?=\n|CONTENT:|$)', ai_text, re.IGNORECASE)
                content_match = re.search(r'CONTENT:\s*(.+)', ai_text, re.IGNORECASE | re.DOTALL)
                
                new_title = headline_match.group(1).strip() if headline_match else title
                new_content = content_match.group(1).strip() if content_match else ai_text
                
                # Remove citation numbers in square brackets [1], [2], etc.
                new_title = re.sub(r'\[\d+\]', '', new_title).strip()
                new_content = re.sub(r'\[\d+\]', '', new_content).strip()
                
                # Clean up any double spaces created by removing citations
                new_title = re.sub(r'\s+', ' ', new_title).strip()
                new_content = re.sub(r'\s+', ' ', new_content).strip()
                
                return {
                    'title': new_title,
                    'content': new_content
                }
            else:
                logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                return {'title': title, 'content': content[:max_words * 5]}
                
        except Exception as e:
            logger.error(f"Error using Perplexity for summarization: {str(e)}")
            return {'title': title, 'content': content[:max_words * 5]}
    
    def process_feed_entry(self, entry, source_name: str, category: str, use_ai: bool = True) -> Optional[Dict]:
        """Process a single RSS feed entry"""
        try:
            # Extract basic information
            title = entry.get('title', 'Untitled')
            link = entry.get('link', '')
            
            # Get content (try different fields)
            content = ''
            if 'content' in entry and len(entry.content) > 0:
                content = entry.content[0].value
            elif 'summary' in entry:
                content = entry.summary
            elif 'description' in entry:
                content = entry.description
            
            # Clean HTML from content
            content = self.extract_text_from_html(content)
            
            # Get published date
            published_date = None
            if 'published_parsed' in entry and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif 'updated_parsed' in entry and entry.updated_parsed:
                published_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            else:
                published_date = datetime.now(timezone.utc)
            
            # Use AI to rewrite if enabled
            if use_ai and content:
                ai_result = self.summarize_with_perplexity(title, content)
                title = ai_result['title']
                content = ai_result['content']
            
            return {
                'title': title,
                'content': content,
                'category': category,
                'source': source_name,
                'source_url': link,
                'published_date': published_date,
                'imported': True,
                'ai_processed': use_ai
            }
            
        except Exception as e:
            logger.error(f"Error processing feed entry: {str(e)}")
            return None
    
    def import_from_sources(self, sources: List[Dict], max_per_source: int = 5, use_ai: bool = True) -> List[Dict]:
        """Import articles from multiple RSS sources"""
        all_articles = []
        
        for source in sources:
            try:
                feed = self.fetch_rss_feed(source['url'])
                if not feed or not hasattr(feed, 'entries'):
                    continue
                
                logger.info(f"Processing {len(feed.entries)} entries from {source['name']}")
                
                # Process limited number of entries per source
                for entry in feed.entries[:max_per_source]:
                    article = self.process_feed_entry(
                        entry,
                        source['name'],
                        source['category'],
                        use_ai
                    )
                    if article:
                        all_articles.append(article)
                        
            except Exception as e:
                logger.error(f"Error importing from {source['name']}: {str(e)}")
                continue
        
        logger.info(f"Successfully imported {len(all_articles)} articles")
        return all_articles