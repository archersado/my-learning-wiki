from .base_agent import BaseAgent
# Assume tools are passed in __init__ or accessed globally/via context
from pymongo import MongoClient
import requests
import feedparser
import json
import os
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
from ..config.settings import RAW_DATA_DB_CONFIG, USE_LOCAL_STORAGE, LOCAL_PENDING_DIR

from langchain_core.messages import HumanMessage, ChatMessage, AIMessage

class ScrapingExpert(BaseAgent):
    def __init__(self, llm=None, tools=None):
        super().__init__(llm, tools, skip_db=USE_LOCAL_STORAGE)

    def process(self, state: dict) -> dict:
        """Scrapes information from the internet."""
        print("Scraping Expert is collecting information.")
        query = state.get("scrape_list", [])
        scraped_data = self.scrape(query)
        return { **state,  "scraped_data": scraped_data }
    

    def scrape(self, list):
        """Web scraping logic."""
        for feed_url in list:
            try:
                from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self.fetch_and_parse_rss, feed_url)
                    future.result(timeout=30)
            except Exception as e:
                print(f"Feed {feed_url}: SKIPPED — timed out or error ({e})")
    

    def get_article_content(self, url):
        """Fetches and extracts the main content from an article URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            cleaned_html = self._clean_html(response.text)
            return cleaned_html

        except Exception as e:
            print(f"Error fetching article content from {url}: {e}")
            return None
        
    
    def analyze_categories(self, content):
        """Analyze categories and return a list of categories."""
        prompt = f"""
        You are a content categorization expert. Your task is to analyze the given article content and identify the most relevant categories and keywords.

        Requirements:
        1. Analyze the main topics and themes of the article
        2. Identify 3-5 most relevant categories that best describe the content
        3. Categories should be specific and meaningful
        4. Return the categories as a comma-separated list
        5. Each category should be a single word or short phrase (2-3 words max)
        6. Categories should be in English and lowercase

        Example output format:
        technology, artificial intelligence, machine learning
        """
        input = f"""
            Article Content:
            {content}
        """

        messages = [AIMessage(content=prompt), HumanMessage(content=input)]

        # Use the LLM to analyze categories
        response = self.llm.invoke(messages)
        # Split the response into a list of categories and clean them
        categories = [cat.strip().lower() for cat in response.content.strip().split(',')]
        return categories

    def fetch_and_parse_rss(self, url):
        """Fetches and parses an RSS feed."""
        print(f"Fetching RSS feed from: {url}")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            feed = feedparser.parse(response.content)
            count = 0

            for entry in feed.entries:
                try:
                    title = entry.get('title', 'No Title')
                    link = entry.get('link', '')

                    # Step 1: Try to get content from RSS feed
                    content = entry.get('content', '')
                    if isinstance(content, list) and content:
                        first_item = content[0]
                        if isinstance(first_item, dict):
                            content = first_item.get('value', '')
                        else:
                            content = ''
                    elif isinstance(content, dict):
                        content = content.get('value', '')
                    elif isinstance(content, str):
                        pass  # content is already a string
                    else:
                        content = ''

                    # Step 2: If no content, try to get summary from RSS
                    if not content:
                        summary = entry.get('summary', '')
                        if isinstance(summary, str):
                            content = summary
                        elif isinstance(summary, list) and summary:
                            content = str(summary[0])
                        elif isinstance(summary, dict):
                            content = summary.get('value', '')
                        else:
                            content = str(summary) if summary else ''

                    # Step 3: If still no content, try to fetch full article page
                    if not content:
                        content = self.get_article_content(link)

                        # If content is still empty after all fallbacks, skip
                        if not content:
                            print(f"Skipping article '{title}': no content available after summary fallback")
                            continue

                    published = entry.get('published', entry.get('updated', ''))
                    if published:
                        try:
                            published_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z')
                        except ValueError:
                            try:
                                published_date = datetime.fromisoformat(published)
                            except ValueError:
                                published_date = datetime.now()
                    else:
                        published_date = datetime.now()
                    categories = [tag.get('term') or tag.get('label') or tag.get('value') for tag in entry.get('tags', []) if tag and isinstance(tag, dict)]
                    if not categories and feed.feed.get('tags'):
                        categories = [tag.get('term') or tag.get('label') or tag.get('value') for tag in feed.feed.get('tags', []) if tag and isinstance(tag, dict)]

                    # Skip LLM category analysis and abstract generation for speed
                    # These will be handled during wiki ingest
                    if not categories:
                        categories = ['uncategorized']

                    article_data = {
                        'source': url,
                        'title': title,
                        'content': content,
                        'link': link,
                        'published': published_date,
                        'categories': categories,
                        'abstract': '',
                        'ingestion_timestamp': datetime.now()
                    }

                    self._save_article(article_data)
                    count += 1
                    print(f"Processed article: {title}")
                except Exception as e:
                    print(f"Error processing article '{title}': {e}")
                    continue

            print(f"Feed {url}: processed {count}/{len(feed.entries)} articles")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching feed {url}: {e}")
            return []
        except Exception as e:
            print(f"Error parsing feed {url}: {e}")
            return []

    def _save_article(self, article):
        """Save article to local storage or MongoDB based on USE_LOCAL_STORAGE."""
        if not article:
            return
        if USE_LOCAL_STORAGE:
            self._save_article_local(article)
        else:
            self.insert_articles_to_mongodb(article)

    def _save_article_local(self, article):
        """Save article as JSON file in LOCAL_PENDING_DIR."""
        os.makedirs(LOCAL_PENDING_DIR, exist_ok=True)
        uid = hashlib.md5(article["title"].encode()).hexdigest()[:8]
        path = os.path.join(LOCAL_PENDING_DIR, f"{uid}.json")
        if os.path.exists(path):
            return  # already saved, skip
        article_copy = dict(article)
        article_copy["_id"] = uid
        article_copy["status"] = "pending"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(article_copy, f, ensure_ascii=False, default=str)

    def insert_articles_to_mongodb(self, article):
        """Connects to MongoDB and inserts or updates articles based on title."""
        if not article:
            print("No articles to insert.")
            return

        print(f"Attempting to connect to MongoDB at {RAW_DATA_DB_CONFIG['host']}:{RAW_DATA_DB_CONFIG['port']}")
        try:
            # Get the collection first
            collection = self.db_client.get_raw_data_collection()
            article['created_at'] = datetime.now()
            article['status'] = 'pending'
            # Use update_one with upsert=True to either update existing article or insert new one
            result = collection.update_one(
                {"title": article["title"]},  # Query to find matching title
                {"$set": article},  # Update with new article data
                upsert=True  # Insert if no match found
            )
            
            if result.upserted_id:
                print(f"Inserted new article: {article['title']}")
            else:
                print(f"Updated existing article: {article['title']}")

        except Exception as e:
            print(f"Error upserting article into MongoDB: {e}")


    def analyze_abstract(self, content: str) -> str:
        """Use LLM to extract core content from cleaned HTML."""
        # Truncate content if too long to avoid API limits
        if len(content) > 10000:
            content = content[:10000] + "..."

        prompt = """
        你是一个文章摘要生成器，根据原始的文章内容生成文章摘要

        Requirement:
        1. 识别原始的文章内容，提取核心内容和观点
        2. 以文本形式返回文章摘要内容
        3. 原始的文章内容可能有多种形式，包含 html 网页，markdown 文本等，需要从中识别核心内容，不能遗漏核心的观点
        4. 如果文章内容是英文的需要将摘要翻译成中文
        """
        input = f"""
            原生文章内容为
            {content}
        """

        messages = [AIMessage(content=prompt), HumanMessage(content=input)]

        # Use the LLM to extract content
        response = self.llm.invoke(messages)
        return response.content.strip()


    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content by removing unnecessary elements."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()

        main_content = soup.find('article') or soup.find('main') or soup.find('div', class_=['content', 'article', 'post'])
        if main_content:
            return str(main_content)
        return str(soup.get_text(separator=' ', strip=True))
    

    def _extract_content_with_llm(self, cleaned_html: str) -> str:
        """Use LLM to extract core content from cleaned HTML."""
        prompt = f"""
        You are a article content extractor, you can extract content from a HTML website. 

        Requirement:
        1. extract raw article content, do not summarize
        2. remove content unrelated to the article, such as advertisements, navigation elements
        3. remove link style or other markdown pattern
        4. return ony extracted content text
        """
        input = f"""
            input HTML Content:
            {cleaned_html}
        """

        messages = [AIMessage(content=prompt), HumanMessage(content=input)]

        # Use the LLM to extract content
        response = self.llm.invoke(messages)
        return response.content.strip()
