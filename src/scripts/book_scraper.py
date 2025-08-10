"""
Book scraper module for extracting book data from books.toscrape.com.
Implements comprehensive book data extraction with pagination support.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

from base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BookScraper(BaseScraper):
    """Scraper for extracting book data from books.toscrape.com"""
    
    def __init__(self, rate_limit: float = 1.0, max_retries: int = 3):
        """Initialize the book scraper."""
        super().__init__(rate_limit, max_retries)
        self.books = []
        self.categories = set()
    
    def extract_book_details(self, book_element, page_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract detailed information from a book element.
        
        Args:
            book_element: BeautifulSoup element containing book info
            page_url: URL of the current page (for building absolute URLs)
            
        Returns:
            Dictionary containing book details or None if extraction fails
        """
        try:
            book_data = {}
            
            # Title
            title_element = book_element.find('h3').find('a')
            book_data['title'] = title_element.get('title', '').strip()
            
            # Book detail URL
            book_url = title_element.get('href', '')
            book_data['detail_url'] = urljoin(page_url, book_url)
            
            # Price
            price_element = book_element.find('p', class_='price_color')
            if price_element:
                book_data['price'] = self.clean_price(price_element.get_text())
            else:
                book_data['price'] = 0.0
            
            # Rating
            rating_element = book_element.find('p', class_=re.compile(r'star-rating'))
            if rating_element:
                rating_class = ' '.join(rating_element.get('class', []))
                book_data['rating'] = self.extract_rating(rating_class)
            else:
                book_data['rating'] = 0
            
            # Availability
            availability_element = book_element.find('p', class_='instock availability')
            if availability_element:
                book_data['availability'] = availability_element.get_text().strip()
            else:
                book_data['availability'] = 'Unknown'
            
            # Image URL
            img_element = book_element.find('div', class_='image_container').find('img')
            if img_element:
                img_src = img_element.get('src', '')
                book_data['image_url'] = urljoin(self.BASE_URL, img_src)
            else:
                book_data['image_url'] = ''
            
            # Add metadata
            book_data['scraped_at'] = self.get_timestamp()
            
            return book_data
            
        except Exception as e:
            logger.error(f"Error extracting book details: {str(e)}")
            return None
    
    def extract_book_full_details(self, book_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract full book details from the book's detail page.
        
        Args:
            book_url: URL of the book's detail page
            
        Returns:
            Dictionary containing detailed book information
        """
        try:
            soup = self.fetch_page(book_url)
            if not soup:
                return None
            
            book_data = {}
            
            # Title
            title_element = soup.find('h1')
            book_data['title'] = title_element.get_text().strip() if title_element else ''
            
            # Price
            price_element = soup.find('p', class_='price_color')
            book_data['price'] = self.clean_price(price_element.get_text()) if price_element else 0.0
            
            # Rating
            rating_element = soup.find('p', class_=re.compile(r'star-rating'))
            if rating_element:
                rating_class = ' '.join(rating_element.get('class', []))
                book_data['rating'] = self.extract_rating(rating_class)
            else:
                book_data['rating'] = 0
            
            # Availability
            availability_element = soup.find('p', class_='instock availability')
            book_data['availability'] = availability_element.get_text().strip() if availability_element else 'Unknown'
            
            # Category
            breadcrumb = soup.find('ul', class_='breadcrumb')
            if breadcrumb:
                category_links = breadcrumb.find_all('a')
                if len(category_links) >= 2:  # Skip "Home" link
                    book_data['category'] = category_links[-1].get_text().strip()
                else:
                    book_data['category'] = 'Unknown'
            else:
                book_data['category'] = 'Unknown'
            
            # Image URL
            img_element = soup.find('div', class_='item active').find('img') if soup.find('div', class_='item active') else None
            if img_element:
                book_data['image_url'] = urljoin(self.BASE_URL, img_element.get('src', ''))
            else:
                book_data['image_url'] = ''
            
            # Product information table
            product_info = {}
            table = soup.find('table', class_='table table-striped')
            if table:
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        key = cells[0].get_text().strip()
                        value = cells[1].get_text().strip()
                        product_info[key] = value
            
            book_data['product_info'] = product_info
            book_data['upc'] = product_info.get('UPC', '')
            book_data['product_type'] = product_info.get('Product Type', '')
            book_data['tax'] = self.clean_price(product_info.get('Tax', '0'))
            
            # Description
            description_element = soup.find('div', id='product_description')
            if description_element:
                description_p = description_element.find_next_sibling('p')
                book_data['description'] = description_p.get_text().strip() if description_p else ''
            else:
                book_data['description'] = ''
            
            # Add metadata
            book_data['detail_url'] = book_url
            book_data['scraped_at'] = self.get_timestamp()
            
            return book_data
            
        except Exception as e:
            logger.error(f"Error extracting full book details from {book_url}: {str(e)}")
            return None
    
    def scrape_page(self, page_url: str, extract_full_details: bool = False) -> List[Dict[str, Any]]:
        """
        Scrape all books from a single page.
        
        Args:
            page_url: URL of the page to scrape
            extract_full_details: Whether to fetch full details for each book
            
        Returns:
            List of book dictionaries
        """
        soup = self.fetch_page(page_url)
        if not soup:
            return []
        
        books = []
        book_elements = soup.find_all('article', class_='product_pod')
        
        logger.info(f"Found {len(book_elements)} books on page")
        
        for book_element in book_elements:
            if extract_full_details:
                # Get basic info first to extract detail URL
                basic_info = self.extract_book_details(book_element, page_url)
                if basic_info and basic_info.get('detail_url'):
                    # Fetch full details
                    full_details = self.extract_book_full_details(basic_info['detail_url'])
                    if full_details:
                        books.append(full_details)
                        self.categories.add(full_details.get('category', 'Unknown'))
            else:
                # Just get basic info
                book_info = self.extract_book_details(book_element, page_url)
                if book_info:
                    books.append(book_info)
        
        return books
    
    def get_total_pages(self, soup) -> int:
        """
        Extract total number of pages from pagination.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Total number of pages
        """
        try:
            pager = soup.find('li', class_='current')
            if pager:
                page_text = pager.get_text().strip()
                # Extract format like "Page 1 of 50"
                match = re.search(r'Page \d+ of (\d+)', page_text)
                if match:
                    return int(match.group(1))
            return 1
        except Exception as e:
            logger.error(f"Error extracting total pages: {str(e)}")
            return 1
    
    def scrape_all_books(self, extract_full_details: bool = False, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape all books from the entire catalog.
        
        Args:
            extract_full_details: Whether to fetch full details for each book
            max_pages: Maximum number of pages to scrape (None for all)
            
        Returns:
            List of all book dictionaries
        """
        logger.info("Starting comprehensive book scraping...")
        
        all_books = []
        base_url = f"{self.BASE_URL}/catalogue/page-{{}}.html"
        
        # Get first page to determine total pages
        first_page_url = f"{self.BASE_URL}/catalogue/page-1.html"
        first_soup = self.fetch_page(first_page_url)
        
        if not first_soup:
            logger.error("Could not fetch first page")
            return []
        
        total_pages = self.get_total_pages(first_soup)
        logger.info(f"Total pages to scrape: {total_pages}")
        
        if max_pages:
            total_pages = min(total_pages, max_pages)
            logger.info(f"Limited to {total_pages} pages")
        
        # Scrape first page (we already have the soup)
        page_books = []
        book_elements = first_soup.find_all('article', class_='product_pod')
        
        for book_element in book_elements:
            if extract_full_details:
                basic_info = self.extract_book_details(book_element, first_page_url)
                if basic_info and basic_info.get('detail_url'):
                    full_details = self.extract_book_full_details(basic_info['detail_url'])
                    if full_details:
                        page_books.append(full_details)
                        self.categories.add(full_details.get('category', 'Unknown'))
            else:
                book_info = self.extract_book_details(book_element, first_page_url)
                if book_info:
                    page_books.append(book_info)
        
        all_books.extend(page_books)
        logger.info(f"Page 1: Found {len(page_books)} books")
        
        # Scrape remaining pages
        for page_num in range(2, total_pages + 1):
            page_url = base_url.format(page_num)
            page_books = self.scrape_page(page_url, extract_full_details)
            all_books.extend(page_books)
            
            logger.info(f"Page {page_num}: Found {len(page_books)} books (Total: {len(all_books)})")
        
        logger.info(f"Scraping completed. Total books found: {len(all_books)}")
        logger.info(f"Categories discovered: {sorted(self.categories)}")
        
        return all_books
    
    def scrape_category(self, category_url: str, extract_full_details: bool = False) -> List[Dict[str, Any]]:
        """
        Scrape all books from a specific category.
        
        Args:
            category_url: URL of the category page
            extract_full_details: Whether to fetch full details for each book
            
        Returns:
            List of book dictionaries from the category
        """
        logger.info(f"Scraping category: {category_url}")
        
        all_books = []
        page_num = 1
        
        while True:
            if page_num == 1:
                page_url = category_url
            else:
                # Build pagination URL for category
                base_url = category_url.replace('.html', f'/page-{page_num}.html')
                page_url = base_url
            
            books = self.scrape_page(page_url, extract_full_details)
            
            if not books:
                break  # No more books found
            
            all_books.extend(books)
            logger.info(f"Category page {page_num}: Found {len(books)} books")
            page_num += 1
            
            # Check if there's a next page by looking for pagination
            soup = self.fetch_page(page_url)
            if not soup or not soup.find('li', class_='next'):
                break
        
        logger.info(f"Category scraping completed. Total books: {len(all_books)}")
        return all_books
