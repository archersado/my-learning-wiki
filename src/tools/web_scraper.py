import requests
import feedparser
from pymongo import MongoClient
from datetime import datetime 
from bs4 import BeautifulSoup

from src.config.settings import AI_ENGINEERING_RESOURCES, RAW_DATA_DB_CONFIG

# Ensure src directory is in the Python path if running this script directly
# (This might not be necessary if running from project root or using a proper package structure)
# For example, if running src/tools/web_scraper.py directly, you might need:
# current_dir = os.path.dirname(__file__)
# src_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
# if src_dir not in sys.path:
#    sys.path.insert(0, src_dir)

class WebScraper:
    def __init__(self, contentExtractor=None):
        self.contentExtractor = contentExtractor
             
