"""
Books to Scrape - Web Scraping Package

This package provides comprehensive web scraping functionality for books.toscrape.com,
including book data extraction, category analysis, and performance monitoring.

Main Components:
- BaseScraper: Core scraping functionality with rate limiting and retry logic
- BookScraper: Book-specific scraping and data extraction
- CategoryScraper: Category discovery and analysis
- ScrapingOrchestrator: Main coordinator for all scraping operations
- Monitoring: Performance tracking and structured logging
- Utils: Data processing, validation, and file operations
- Config: Configuration management and environment variables

Usage:
    from scripts.main_scraper import ScrapingOrchestrator
    
    orchestrator = ScrapingOrchestrator(rate_limit=1.0)
    books = orchestrator.scrape_all_books(max_pages=5)
    categories = orchestrator.scrape_all_categories()

For command line usage:
    python main_scraper.py --mode full-pipeline --max-pages 10
    
For examples:
    python examples.py
"""

__version__ = "1.0.0"
__author__ = "ScrapBook Project"
__description__ = "Web scraping system for books.toscrape.com"

# Import main classes for easy access
try:
    from .main_scraper import ScrapingOrchestrator
    from .book_scraper import BookScraper
    from .category_scraper import CategoryScraper
    from .base_scraper import BaseScraper
    from ..config.Scrapper import ScraperConfig
    from .monitoring import ScrapingLogger, PerformanceTracker
    from .utils.utils import DataValidator, DataProcessor, FileHandler
    
    __all__ = [
        'ScrapingOrchestrator',
        'BookScraper', 
        'CategoryScraper',
        'BaseScraper',
        'ScraperConfig',
        'ScrapingLogger',
        'PerformanceTracker',
        'DataValidator',
        'DataProcessor',
        'FileHandler'
    ]
    
except ImportError:
    # If dependencies aren't installed, provide a helpful message
    import sys
    print("Warning: Some dependencies are not installed.", file=sys.stderr)
    print("Run: pip install -r ../requirements.txt", file=sys.stderr)
    
    __all__ = []
