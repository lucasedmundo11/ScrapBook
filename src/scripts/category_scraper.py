"""
Category scraper module for extracting category information from books.toscrape.com.
Provides functionality to discover and scrape all available book categories.
"""

import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

from base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CategoryScraper(BaseScraper):
    """Scraper for extracting category information from books.toscrape.com"""
    
    def __init__(self, rate_limit: float = 1.0, max_retries: int = 3):
        """Initialize the category scraper."""
        super().__init__(rate_limit, max_retries)
        self.categories = []
    
    def extract_categories(self) -> List[Dict[str, Any]]:
        """
        Extract all categories from the main page sidebar.
        
        Returns:
            List of category dictionaries containing name, url, and book count
        """
        logger.info("Extracting categories from main page...")
        
        main_page_url = self.BASE_URL
        soup = self.fetch_page(main_page_url)
        
        if not soup:
            logger.error("Could not fetch main page for category extraction")
            return []
        
        categories = []
        
        # Find the category navigation sidebar
        category_nav = soup.find('div', class_='side_categories')
        if not category_nav:
            logger.error("Could not find category navigation")
            return []
        
        # Find all category links (skip the first "Books" link)
        category_links = category_nav.find_all('a')[1:]  # Skip "Books" parent category
        
        for link in category_links:
            try:
                category_data = {}
                
                # Category name and URL
                category_data['name'] = link.get_text().strip()
                category_data['url'] = urljoin(self.BASE_URL, link.get('href', ''))
                
                # Extract book count from text (format: "Category Name (count)")
                full_text = link.get_text().strip()
                if '(' in full_text and ')' in full_text:
                    count_text = full_text.split('(')[-1].replace(')', '').strip()
                    try:
                        category_data['book_count'] = int(count_text)
                    except ValueError:
                        category_data['book_count'] = 0
                else:
                    category_data['book_count'] = 0
                
                # Clean category name (remove count from name)
                clean_name = full_text.split('(')[0].strip()
                category_data['name'] = clean_name
                
                # Add metadata
                category_data['scraped_at'] = self.get_timestamp()
                
                categories.append(category_data)
                
            except Exception as e:
                logger.error(f"Error extracting category info: {str(e)}")
                continue
        
        logger.info(f"Found {len(categories)} categories")
        self.categories = categories
        return categories
    
    def get_category_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the discovered categories.
        
        Returns:
            Dictionary containing category statistics
        """
        if not self.categories:
            return {}
        
        total_categories = len(self.categories)
        total_books = sum(cat.get('book_count', 0) for cat in self.categories)
        avg_books_per_category = total_books / total_categories if total_categories > 0 else 0
        
        # Find categories with most and least books
        categories_with_counts = [cat for cat in self.categories if cat.get('book_count', 0) > 0]
        
        if categories_with_counts:
            most_books = max(categories_with_counts, key=lambda x: x['book_count'])
            least_books = min(categories_with_counts, key=lambda x: x['book_count'])
        else:
            most_books = least_books = None
        
        stats = {
            'total_categories': total_categories,
            'total_books_across_categories': total_books,
            'average_books_per_category': round(avg_books_per_category, 2),
            'category_with_most_books': most_books,
            'category_with_least_books': least_books,
            'scraped_at': self.get_timestamp()
        }
        
        return stats
    
    def validate_category_urls(self) -> List[Dict[str, Any]]:
        """
        Validate all category URLs by checking if they're accessible.
        
        Returns:
            List of categories with validation status
        """
        logger.info("Validating category URLs...")
        
        validated_categories = []
        
        for category in self.categories:
            category_copy = category.copy()
            url = category.get('url', '')
            
            if not url:
                category_copy['is_valid'] = False
                category_copy['error'] = 'No URL provided'
                validated_categories.append(category_copy)
                continue
            
            try:
                soup = self.fetch_page(url)
                if soup:
                    # Check if page has books or pagination
                    books = soup.find_all('article', class_='product_pod')
                    pagination = soup.find('li', class_='current') or soup.find('li', class_='next')
                    
                    if books or pagination:
                        category_copy['is_valid'] = True
                        category_copy['actual_book_count'] = len(books)
                        category_copy['has_pagination'] = bool(pagination)
                    else:
                        category_copy['is_valid'] = False
                        category_copy['error'] = 'No books found on category page'
                else:
                    category_copy['is_valid'] = False
                    category_copy['error'] = 'Could not fetch category page'
                    
            except Exception as e:
                category_copy['is_valid'] = False
                category_copy['error'] = str(e)
            
            validated_categories.append(category_copy)
            logger.info(f"Validated {category['name']}: {'✓' if category_copy['is_valid'] else '✗'}")
        
        return validated_categories
    
    def scrape_category_details(self, category_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific category.
        
        Args:
            category_url: URL of the category to analyze
            
        Returns:
            Dictionary containing detailed category information
        """
        soup = self.fetch_page(category_url)
        if not soup:
            return None
        
        try:
            category_details = {}
            
            # Category title from page
            title_element = soup.find('h1')
            category_details['title'] = title_element.get_text().strip() if title_element else 'Unknown'
            
            # Count books on first page
            books = soup.find_all('article', class_='product_pod')
            category_details['books_on_first_page'] = len(books)
            
            # Check pagination to get total pages
            pagination = soup.find('li', class_='current')
            if pagination:
                page_text = pagination.get_text().strip()
                import re
                match = re.search(r'Page \d+ of (\d+)', page_text)
                if match:
                    category_details['total_pages'] = int(match.group(1))
                else:
                    category_details['total_pages'] = 1
            else:
                category_details['total_pages'] = 1
            
            # Estimate total books (pages * books_per_page, except last page might have fewer)
            books_per_page = len(books)
            if category_details['total_pages'] > 1:
                estimated_books = (category_details['total_pages'] - 1) * books_per_page
                # We'd need to check the last page for exact count, but this is a good estimate
                category_details['estimated_total_books'] = f"{estimated_books}+"
            else:
                category_details['estimated_total_books'] = books_per_page
            
            # Extract price range from first page
            prices = []
            for book in books:
                price_element = book.find('p', class_='price_color')
                if price_element:
                    price = self.clean_price(price_element.get_text())
                    if price > 0:
                        prices.append(price)
            
            if prices:
                category_details['price_range'] = {
                    'min': min(prices),
                    'max': max(prices),
                    'avg': sum(prices) / len(prices)
                }
            
            # Extract ratings distribution from first page
            ratings = []
            for book in books:
                rating_element = book.find('p', class_=lambda x: x and 'star-rating' in x)
                if rating_element:
                    rating_class = ' '.join(rating_element.get('class', []))
                    rating = self.extract_rating(rating_class)
                    if rating > 0:
                        ratings.append(rating)
            
            if ratings:
                rating_counts = {i: ratings.count(i) for i in range(1, 6)}
                category_details['ratings_distribution'] = rating_counts
                category_details['average_rating'] = sum(ratings) / len(ratings)
            
            category_details['url'] = category_url
            category_details['scraped_at'] = self.get_timestamp()
            
            return category_details
            
        except Exception as e:
            logger.error(f"Error extracting category details from {category_url}: {str(e)}")
            return None
