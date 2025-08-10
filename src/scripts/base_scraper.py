"""
Base scraper module for Books to Scrape website.
Provides common functionality and configuration for all scrapers.
"""

import csv
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaseScraper:
    """Base scraper class with common functionality for books.toscrape.com"""
    
    BASE_URL = "https://books.toscrape.com"
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    def __init__(self, rate_limit: float = 1.0, max_retries: int = 3):
        """
        Initialize the base scraper.
        
        Args:
            rate_limit: Delay between requests in seconds
            max_retries: Maximum number of retry attempts
        """
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.session = self._create_session()
        self.scraped_data = []
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy and headers."""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers
        session.headers.update({
            'User-Agent': self.USER_AGENTS[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def _rate_limit_delay(self):
        """Apply rate limiting delay between requests."""
        if self.rate_limit > 0:
            time.sleep(self.rate_limit)
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return BeautifulSoup object.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            self._rate_limit_delay()
            logger.info(f"Fetching: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            return soup
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            return None
    
    def extract_rating(self, rating_class: str) -> int:
        """
        Extract numeric rating from CSS class.
        
        Args:
            rating_class: CSS class containing rating info
            
        Returns:
            Rating as integer (1-5)
        """
        rating_map = {
            'One': 1,
            'Two': 2,
            'Three': 3,
            'Four': 4,
            'Five': 5
        }
        
        for word, rating in rating_map.items():
            if word in rating_class:
                return rating
        return 0
    
    def clean_price(self, price_text: str) -> float:
        """
        Clean and convert price text to float.
        
        Args:
            price_text: Raw price text
            
        Returns:
            Price as float
        """
        try:
            # Remove currency symbols and whitespace
            price_clean = price_text.replace('£', '').replace('$', '').strip()
            return float(price_clean)
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse price: {price_text}")
            return 0.0
    
    def save_to_csv(self, filename: str, data: List[Dict[str, Any]]) -> None:
        """
        Save scraped data to CSV file.
        
        Args:
            filename: Output CSV filename
            data: List of dictionaries containing book data
        """
        if not data:
            logger.warning("No data to save")
            return
        
        # Ensure CSV directory exists
        csv_dir = './data/csv'
        try:
            os.makedirs(csv_dir, exist_ok=True)
            filepath = os.path.join(csv_dir, filename)
        except (OSError, PermissionError):
            # Can't create directory, likely in serverless environment
            self.logger.warning("Unable to create CSV directory in serverless environment")
            return
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Data saved to {filepath} ({len(data)} records)")
            
        except IOError as e:
            logger.error(f"Error saving to CSV: {str(e)}")
    
    def save_to_json(self, filename: str, data: List[Dict[str, Any]]) -> None:
        """
        Save scraped data to JSON file.
        
        Args:
            filename: Output JSON filename
            data: List of dictionaries containing book data
        """
        if not data:
            logger.warning("No data to save")
            return
        
        # Ensure JSON directory exists
        json_dir = './data/json'
        try:
            os.makedirs(json_dir, exist_ok=True)
            filepath = os.path.join(json_dir, filename)
        except (OSError, PermissionError):
            # Can't create directory, likely in serverless environment
            self.logger.warning("Unable to create JSON directory in serverless environment")
            return
        
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Data saved to {filepath} ({len(data)} records)")
            
        except IOError as e:
            logger.error(f"Error saving to JSON: {str(e)}")
    
    def get_timestamp(self) -> str:
        """Get current timestamp for file naming."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def generate_filename(self, prefix: str, extension: str = 'csv') -> str:
        """
        Generate timestamped filename.
        
        Args:
            prefix: Filename prefix
            extension: File extension
            
        Returns:
            Timestamped filename
        """
        timestamp = self.get_timestamp()
        return f"{prefix}_{timestamp}.{extension}"
