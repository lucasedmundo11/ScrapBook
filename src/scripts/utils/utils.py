"""
Utility functions for data processing, validation, and analysis.
Provides common functionality used across scraping modules.
"""

import csv
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse

# Import scraper config for logging setup
try:
    from ...config.Scrapper import setup_scraper_logging
except ImportError:
    # Fallback for when running from different contexts
    setup_scraper_logging = None

logger = logging.getLogger(__name__)


def setup_logging(name: str = "scrapbook_utils") -> logging.Logger:
    """
    Set up logging for utility functions.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    if setup_scraper_logging:
        return setup_scraper_logging(name)
    else:
        # Fallback basic logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(name)


class DataValidator:
    """Validates and cleans scraped data."""
    
    @staticmethod
    def validate_book_data(book_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean book data.
        
        Args:
            book_data: Dictionary containing book information
            
        Returns:
            Cleaned and validated book data
        """
        cleaned_data = book_data.copy()
        
        # Title validation
        title = cleaned_data.get('title', '').strip()
        if not title:
            logger.warning("Book has empty title")
            cleaned_data['title'] = 'Unknown Title'
        else:
            # Clean title (remove extra whitespace, special characters)
            cleaned_data['title'] = re.sub(r'\s+', ' ', title)
        
        # Price validation
        price = cleaned_data.get('price', 0)
        if isinstance(price, str):
            price = DataProcessor.clean_price(price)
        if price < 0:
            logger.warning(f"Invalid negative price: {price}")
            cleaned_data['price'] = 0.0
        cleaned_data['price'] = round(float(price), 2)
        
        # Rating validation
        rating = cleaned_data.get('rating', 0)
        if not isinstance(rating, int) or rating < 0 or rating > 5:
            logger.warning(f"Invalid rating: {rating}")
            cleaned_data['rating'] = 0
        
        # URL validation
        for url_field in ['detail_url', 'image_url']:
            url = cleaned_data.get(url_field, '')
            if url and not DataValidator.is_valid_url(url):
                logger.warning(f"Invalid {url_field}: {url}")
                cleaned_data[url_field] = ''
        
        # Category validation
        category = cleaned_data.get('category', '').strip()
        if category:
            cleaned_data['category'] = category.title()  # Capitalize properly
        else:
            cleaned_data['category'] = 'Unknown'
        
        # Availability validation
        availability = cleaned_data.get('availability', '').strip()
        cleaned_data['availability'] = availability if availability else 'Unknown'
        
        return cleaned_data
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if a URL is valid.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def validate_category_data(category_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean category data.
        
        Args:
            category_data: Dictionary containing category information
            
        Returns:
            Cleaned and validated category data
        """
        cleaned_data = category_data.copy()
        
        # Name validation
        name = cleaned_data.get('name', '').strip()
        if not name:
            logger.warning("Category has empty name")
            cleaned_data['name'] = 'Unknown Category'
        else:
            cleaned_data['name'] = name.title()
        
        # URL validation
        url = cleaned_data.get('url', '')
        if url and not DataValidator.is_valid_url(url):
            logger.warning(f"Invalid category URL: {url}")
            cleaned_data['url'] = ''
        
        # Book count validation
        book_count = cleaned_data.get('book_count', 0)
        if not isinstance(book_count, int) or book_count < 0:
            logger.warning(f"Invalid book count: {book_count}")
            cleaned_data['book_count'] = 0
        
        return cleaned_data


class DataProcessor:
    """Processes and transforms scraped data."""
    
    @staticmethod
    def clean_price(price_text: str) -> float:
        """
        Clean and convert price text to float.
        
        Args:
            price_text: Raw price text
            
        Returns:
            Price as float
        """
        try:
            if not price_text:
                return 0.0
            
            # Remove currency symbols and whitespace
            price_clean = re.sub(r'[£$€¥₹]', '', str(price_text))
            price_clean = re.sub(r'[^\d.]', '', price_clean)
            
            return float(price_clean) if price_clean else 0.0
            
        except (ValueError, TypeError):
            logger.warning(f"Could not parse price: {price_text}")
            return 0.0
    
    @staticmethod
    def extract_rating_from_class(css_class: str) -> int:
        """
        Extract numeric rating from CSS class.
        
        Args:
            css_class: CSS class string containing rating info
            
        Returns:
            Rating as integer (0-5)
        """
        rating_map = {
            'one': 1,
            'two': 2,
            'three': 3,
            'four': 4,
            'five': 5
        }
        
        css_lower = css_class.lower()
        for word, rating in rating_map.items():
            if word in css_lower:
                return rating
        return 0
    
    @staticmethod
    def standardize_availability(availability_text: str) -> str:
        """
        Standardize availability text.
        
        Args:
            availability_text: Raw availability text
            
        Returns:
            Standardized availability string
        """
        if not availability_text:
            return 'Unknown'
        
        text = availability_text.lower().strip()
        
        if 'in stock' in text:
            # Extract number if available
            match = re.search(r'(\d+)', text)
            if match:
                return f"In Stock ({match.group(1)} available)"
            return "In Stock"
        elif 'out of stock' in text:
            return "Out of Stock"
        else:
            return availability_text.strip()
    
    @staticmethod
    def extract_number_from_text(text: str) -> int:
        """
        Extract the first number from text.
        
        Args:
            text: Text containing numbers
            
        Returns:
            First number found, or 0 if none
        """
        match = re.search(r'(\d+)', str(text))
        return int(match.group(1)) if match else 0
    
    @staticmethod
    def calculate_statistics(books: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics from book data.
        
        Args:
            books: List of book dictionaries
            
        Returns:
            Dictionary containing statistics
        """
        if not books:
            return {}
        
        # Price statistics
        prices = [book.get('price', 0) for book in books if isinstance(book.get('price'), (int, float)) and book.get('price', 0) > 0]
        price_stats = {}
        if prices:
            price_stats = {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices),
                'median': sorted(prices)[len(prices) // 2],
                'total': sum(prices)
            }
        
        # Rating statistics
        ratings = [book.get('rating', 0) for book in books if isinstance(book.get('rating'), int) and book.get('rating', 0) > 0]
        rating_stats = {}
        if ratings:
            rating_counts = {i: ratings.count(i) for i in range(1, 6)}
            rating_stats = {
                'average': sum(ratings) / len(ratings),
                'distribution': rating_counts,
                'most_common': max(rating_counts, key=rating_counts.get),
                'total_rated': len(ratings)
            }
        
        # Category statistics
        categories = [book.get('category', 'Unknown') for book in books]
        category_counts = {}
        for category in categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Availability statistics
        availabilities = [book.get('availability', 'Unknown') for book in books]
        availability_counts = {}
        for availability in availabilities:
            availability_counts[availability] = availability_counts.get(availability, 0) + 1
        
        return {
            'total_books': len(books),
            'price_statistics': price_stats,
            'rating_statistics': rating_stats,
            'category_statistics': {
                'total_categories': len(category_counts),
                'distribution': category_counts,
                'most_popular': max(category_counts, key=category_counts.get) if category_counts else None
            },
            'availability_statistics': availability_counts,
            'calculated_at': datetime.now().isoformat()
        }


class FileHandler:
    """Handles file operations for scraped data."""
    
    @staticmethod
    def ensure_directory(directory: str) -> None:
        """
        Ensure directory exists, create if not.
        
        Args:
            directory: Directory path to create
        """
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            logger.error(f"Error creating directory {directory}: {e}")
    
    @staticmethod
    def save_to_csv(filepath: str, data: List[Dict[str, Any]], encoding: str = 'utf-8') -> bool:
        """
        Save data to CSV file.
        
        Args:
            filepath: Path to save CSV file
            data: List of dictionaries to save
            encoding: File encoding
            
        Returns:
            True if successful, False otherwise
        """
        if not data:
            logger.warning("No data to save to CSV")
            return False
        
        try:
            # Ensure directory exists
            FileHandler.ensure_directory(os.path.dirname(filepath))
            
            with open(filepath, 'w', newline='', encoding=encoding) as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Successfully saved {len(data)} records to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving CSV to {filepath}: {e}")
            return False
    
    @staticmethod
    def save_to_json(filepath: str, data: Any, indent: int = 2, encoding: str = 'utf-8') -> bool:
        """
        Save data to JSON file.
        
        Args:
            filepath: Path to save JSON file
            data: Data to save
            indent: JSON indentation
            encoding: File encoding
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            FileHandler.ensure_directory(os.path.dirname(filepath))
            
            with open(filepath, 'w', encoding=encoding) as jsonfile:
                json.dump(data, jsonfile, indent=indent, ensure_ascii=False, default=str)
            
            logger.info(f"Successfully saved data to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving JSON to {filepath}: {e}")
            return False
    
    @staticmethod
    def load_from_csv(filepath: str, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        Load data from CSV file.
        
        Args:
            filepath: Path to CSV file
            encoding: File encoding
            
        Returns:
            List of dictionaries loaded from CSV
        """
        try:
            data = []
            with open(filepath, 'r', encoding=encoding) as csvfile:
                reader = csv.DictReader(csvfile)
                data = list(reader)
            
            logger.info(f"Successfully loaded {len(data)} records from {filepath}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading CSV from {filepath}: {e}")
            return []
    
    @staticmethod
    def load_from_json(filepath: str, encoding: str = 'utf-8') -> Any:
        """
        Load data from JSON file.
        
        Args:
            filepath: Path to JSON file
            encoding: File encoding
            
        Returns:
            Data loaded from JSON file
        """
        try:
            with open(filepath, 'r', encoding=encoding) as jsonfile:
                data = json.load(jsonfile)
            
            logger.info(f"Successfully loaded data from {filepath}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading JSON from {filepath}: {e}")
            return None


class TimestampUtils:
    """Utilities for handling timestamps and date formatting."""
    
    @staticmethod
    def get_timestamp(format_string: str = "%Y%m%d_%H%M%S") -> str:
        """
        Get formatted timestamp.
        
        Args:
            format_string: strftime format string
            
        Returns:
            Formatted timestamp string
        """
        return datetime.now().strftime(format_string)
    
    @staticmethod
    def get_iso_timestamp() -> str:
        """
        Get ISO format timestamp.
        
        Returns:
            ISO format timestamp string
        """
        return datetime.now().isoformat()
    
    @staticmethod
    def generate_filename(prefix: str, extension: str = 'csv', include_timestamp: bool = True) -> str:
        """
        Generate filename with optional timestamp.
        
        Args:
            prefix: Filename prefix
            extension: File extension (without dot)
            include_timestamp: Whether to include timestamp
            
        Returns:
            Generated filename
        """
        if include_timestamp:
            timestamp = TimestampUtils.get_timestamp()
            return f"{prefix}_{timestamp}.{extension}"
        else:
            return f"{prefix}.{extension}"
