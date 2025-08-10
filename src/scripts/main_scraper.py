"""
Main scraper orchestrator for the Books to Scrape project.
Coordinates all scraping activities and provides a unified interface.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the scripts directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from base_scraper import BaseScraper
from book_scraper import BookScraper
from category_scraper import CategoryScraper

# Import scraper configuration and logging
from src.config.Scrapper import ScraperConfig, setup_scraper_logging


# Initialize logging using the new scraper configuration
logger = setup_scraper_logging("scrapbook_main_scraper")


class ScrapingOrchestrator:
    """Main orchestrator for all scraping activities."""
    
    def __init__(self, rate_limit: float = None, max_retries: int = None):
        """
        Initialize the scraping orchestrator.
        
        Args:
            rate_limit: Delay between requests in seconds (uses config default if None)
            max_retries: Maximum number of retry attempts (uses config default if None)
        """
        # Use config defaults if not provided
        self.rate_limit = rate_limit or ScraperConfig.DEFAULT_RATE_LIMIT
        self.max_retries = max_retries or ScraperConfig.DEFAULT_MAX_RETRIES
        
        # Create directories
        ScraperConfig.create_directories()
        
        # Initialize scrapers
        self.book_scraper = BookScraper(self.rate_limit, self.max_retries)
        self.category_scraper = CategoryScraper(self.rate_limit, self.max_retries)
        
        # Ensure data directory exists (using config path)
        ScraperConfig.create_directories()
    
    def scrape_all_categories(self, save_results: bool = True) -> List[Dict[str, Any]]:
        """
        Scrape all category information.
        
        Args:
            save_results: Whether to save results to files
            
        Returns:
            List of category dictionaries
        """
        logger.info("=== Starting Category Scraping ===")
        
        categories = self.category_scraper.extract_categories()
        
        if not categories:
            logger.error("No categories found")
            return []
        
        # Ensure categories are stored in the scraper instance
        self.category_scraper.categories = categories
        
        # Validate category URLs
        validated_categories = self.category_scraper.validate_category_urls()
        
        # Get category statistics (after categories are properly set)
        stats = self.category_scraper.get_category_stats()
        
        if save_results:
            # Save categories using config paths
            timestamp = self.category_scraper.get_timestamp()
            categories_file = f"categories_{timestamp}.csv"
            validated_file = f"categories_validated_{timestamp}.csv"
            stats_file = f"category_stats_{timestamp}.json"
            
            # Save to CSV directory from config
            categories_path = os.path.join(ScraperConfig.CSV_DIR, categories_file)
            validated_path = os.path.join(ScraperConfig.CSV_DIR, validated_file)
            stats_path = os.path.join(ScraperConfig.JSON_DIR, stats_file)
            
            self.category_scraper.save_to_csv(categories_file, categories)
            self.category_scraper.save_to_csv(validated_file, validated_categories)
            
            # Save stats as JSON using config directory
            try:
                os.makedirs(ScraperConfig.JSON_DIR, exist_ok=True)
                with open(stats_path, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
            except (OSError, PermissionError):
                # Can't write files in serverless environment
                logger.warning("Unable to save stats file in serverless environment")
            
            logger.info(f"Category data saved to {categories_file}, {validated_file}, {stats_file}")
        
        logger.info("=== Category Scraping Completed ===")
        return validated_categories
    
    def scrape_all_books(self, 
                        extract_full_details: bool = True,
                        max_pages: Optional[int] = None,
                        save_results: bool = True) -> List[Dict[str, Any]]:
        """
        Scrape all books from the catalog.
        
        Args:
            extract_full_details: Whether to fetch full details for each book
            max_pages: Maximum number of pages to scrape
            save_results: Whether to save results to files
            
        Returns:
            List of book dictionaries
        """
        logger.info("=== Starting Complete Book Scraping ===")
        logger.info(f"Extract full details: {extract_full_details}")
        logger.info(f"Max pages: {max_pages or 'All'}")
        
        books = self.book_scraper.scrape_all_books(extract_full_details, max_pages)
        
        if not books:
            logger.error("No books found")
            return []
        
        if save_results:
            timestamp = self.book_scraper.get_timestamp()
            detail_suffix = "_detailed" if extract_full_details else "_basic"
            books_file = f"books{detail_suffix}_{timestamp}.csv"
            
            self.book_scraper.save_to_csv(books_file, books)
            self.book_scraper.save_to_json(books_file.replace('.csv', '.json'), books)
            
            logger.info(f"Book data saved to {books_file}")
        
        logger.info("=== Complete Book Scraping Completed ===")
        return books
    
    def scrape_books_by_category(self,
                                category_name: Optional[str] = None,
                                category_url: Optional[str] = None,
                                extract_full_details: bool = False,
                                save_results: bool = True) -> List[Dict[str, Any]]:
        """
        Scrape books from a specific category.
        
        Args:
            category_name: Name of the category to scrape
            category_url: Direct URL of the category to scrape
            extract_full_details: Whether to fetch full details for each book
            save_results: Whether to save results to files
            
        Returns:
            List of book dictionaries from the category
        """
        if not category_url:
            if not category_name:
                logger.error("Either category_name or category_url must be provided")
                return []
            
            # Find category URL by name
            categories = self.category_scraper.extract_categories()
            category_url = None
            for cat in categories:
                if cat['name'].lower() == category_name.lower():
                    category_url = cat['url']
                    break
            
            if not category_url:
                logger.error(f"Category '{category_name}' not found")
                return []
        
        logger.info(f"=== Starting Category Book Scraping: {category_name or category_url} ===")
        
        books = self.book_scraper.scrape_category(category_url, extract_full_details)
        
        if not books:
            logger.error("No books found in category")
            return []
        
        if save_results:
            timestamp = self.book_scraper.get_timestamp()
            detail_suffix = "_detailed" if extract_full_details else "_basic"
            safe_category_name = (category_name or "category").replace(" ", "_").lower()
            books_file = f"books_{safe_category_name}{detail_suffix}_{timestamp}.csv"
            
            self.book_scraper.save_to_csv(books_file, books)
            self.book_scraper.save_to_json(books_file.replace('.csv', '.json'), books)
            
            logger.info(f"Category book data saved to {books_file}")
        
        logger.info(f"=== Category Book Scraping Completed: {len(books)} books ===")
        return books
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive scraping report with statistics.
        
        Returns:
            Dictionary containing comprehensive statistics
        """
        logger.info("=== Generating Comprehensive Report ===")
        
        report = {
            'report_generated_at': datetime.now().isoformat(),
            'scraping_summary': {}
        }
        
        try:
            # Get category information
            logger.info("Analyzing categories...")
            categories = self.category_scraper.extract_categories()
            category_stats = self.category_scraper.get_category_stats()
            
            report['categories'] = {
                'total_categories': len(categories),
                'category_list': [cat['name'] for cat in categories],
                'statistics': category_stats
            }
            
            # Sample a few categories for detailed analysis
            logger.info("Sampling category details...")
            sample_categories = categories[:5] if len(categories) >= 5 else categories
            detailed_categories = []
            
            for cat in sample_categories:
                details = self.category_scraper.scrape_category_details(cat['url'])
                if details:
                    details['name'] = cat['name']
                    detailed_categories.append(details)
            
            report['category_samples'] = detailed_categories
            
            # Quick book sampling (first page only)
            logger.info("Sampling books from first page...")
            first_page_books = self.book_scraper.scrape_page(
                f"{self.book_scraper.BASE_URL}/catalogue/page-1.html",
                extract_full_details=False
            )
            
            if first_page_books:
                prices = [book['price'] for book in first_page_books if book.get('price', 0) > 0]
                ratings = [book['rating'] for book in first_page_books if book.get('rating', 0) > 0]
                
                report['book_samples'] = {
                    'sample_size': len(first_page_books),
                    'price_statistics': {
                        'min': min(prices) if prices else 0,
                        'max': max(prices) if prices else 0,
                        'avg': sum(prices) / len(prices) if prices else 0
                    },
                    'rating_statistics': {
                        'avg': sum(ratings) / len(ratings) if ratings else 0,
                        'distribution': {str(i): ratings.count(i) for i in range(1, 6)}
                    },
                    'sample_books': first_page_books[:5]  # First 5 books as examples
                }
            
            # Save report in json directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"comprehensive_report_{timestamp}.json"
            
            try:
                os.makedirs(ScraperConfig.JSON_DIR, exist_ok=True)
                report_path = os.path.join(ScraperConfig.JSON_DIR, report_file)
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
                
                logger.info(f"Comprehensive report saved to {report_file}")
            except (OSError, PermissionError):
                # Can't write files in serverless environment
                logger.warning("Unable to save comprehensive report in serverless environment")
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {str(e)}")
            report['error'] = str(e)
        
        logger.info("=== Comprehensive Report Completed ===")
        return report
    
    def run_full_scraping_pipeline(self,
                                  extract_full_details: bool = False,
                                  max_pages: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the complete scraping pipeline.
        
        Args:
            extract_full_details: Whether to fetch full details for each book
            max_pages: Maximum number of pages to scrape for books
            
        Returns:
            Dictionary containing all scraped data and statistics
        """
        logger.info("=== Starting Full Scraping Pipeline ===")
        
        pipeline_start = datetime.now()
        results = {
            'pipeline_started_at': pipeline_start.isoformat(),
            'parameters': {
                'extract_full_details': extract_full_details,
                'max_pages': max_pages,
                'rate_limit': self.rate_limit,
                'max_retries': self.max_retries
            }
        }
        
        try:
            # Step 1: Scrape categories
            logger.info("Step 1/3: Scraping categories...")
            categories = self.scrape_all_categories(save_results=True)
            results['categories'] = {
                'count': len(categories),
                'data': categories
            }
            
            # Step 2: Scrape all books
            logger.info("Step 2/3: Scraping books...")
            books = self.scrape_all_books(
                extract_full_details=extract_full_details,
                max_pages=max_pages,
                save_results=True
            )
            results['books'] = {
                'count': len(books),
                'data': books  # Return all book data, not just samples
            }
            
            # Step 3: Generate comprehensive report
            logger.info("Step 3/3: Generating report...")
            report = self.generate_comprehensive_report()
            results['report'] = report
            
            pipeline_end = datetime.now()
            duration = pipeline_end - pipeline_start
            
            results['pipeline_completed_at'] = pipeline_end.isoformat()
            results['duration_seconds'] = duration.total_seconds()
            results['success'] = True
            
            # Save pipeline results using config directory
            timestamp = pipeline_start.strftime("%Y%m%d_%H%M%S")
            pipeline_file = f"pipeline_results_{timestamp}.json"
            
            try:
                os.makedirs(ScraperConfig.JSON_DIR, exist_ok=True)
                pipeline_path = os.path.join(ScraperConfig.JSON_DIR, pipeline_file)
                with open(pipeline_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                
                logger.info(f"Pipeline results saved to {pipeline_file}")
            except (OSError, PermissionError):
                # Can't write files in serverless environment
                logger.warning("Unable to save pipeline results in serverless environment")
            
            logger.info(f"Pipeline results saved to {pipeline_file}")
            logger.info(f"=== Full Pipeline Completed Successfully in {duration.total_seconds():.2f} seconds ===")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            results['success'] = False
            results['error'] = str(e)
            results['pipeline_completed_at'] = datetime.now().isoformat()
        
        return results


def main():
    """Main function for command line interface."""
    parser = argparse.ArgumentParser(description="Books to Scrape Web Scraper")
    parser.add_argument('--mode', choices=['categories', 'books', 'category-books', 'full-pipeline', 'report'], default='full-pipeline', help='Scraping mode')
    parser.add_argument('--category', help='Category name for category-specific scraping')
    parser.add_argument('--full-details', action='store_true', default=True, help='Extract full book details (slower but more comprehensive)')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to scrape')
    parser.add_argument('--rate-limit', type=float, default=1.0, help='Rate limit between requests in seconds')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts for failed requests')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = ScrapingOrchestrator(
        rate_limit=args.rate_limit,
        max_retries=args.max_retries
    )
    
    try:
        if args.mode == 'categories':
            orchestrator.scrape_all_categories()
        elif args.mode == 'books':
            orchestrator.scrape_all_books(
                extract_full_details=args.full_details,
                max_pages=args.max_pages
            )
        elif args.mode == 'category-books':
            if not args.category:
                logger.error("--category is required for category-books mode")
                sys.exit(1)
            orchestrator.scrape_books_by_category(
                category_name=args.category,
                extract_full_details=args.full_details
            )
        elif args.mode == 'report':
            orchestrator.generate_comprehensive_report()
        elif args.mode == 'full-pipeline':
            orchestrator.run_full_scraping_pipeline(
                extract_full_details=args.full_details,
                max_pages=args.max_pages
            )
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
