"""
Configuration module for the Books to Scrape scrapers.
Centralizes all scraping-related configuration settings and environment variables.
"""

import os
import logging
import logging.handlers
from typing import Dict, Any, List

# Try to load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is not available, continue without it
    pass


class ScraperConfig:
    """Configuration settings for the scraping system."""
    
    # Base URLs
    BASE_URL = "https://books.toscrape.com"
    CATALOGUE_URL = f"{BASE_URL}/catalogue"
    
    # Rate limiting and retry settings
    DEFAULT_RATE_LIMIT = float(os.getenv("SCRAPER_RATE_LIMIT", "1.0"))
    DEFAULT_MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    REQUEST_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "10"))
    RETRY_DELAY = float(os.getenv("SCRAPER_RETRY_DELAY", "2.0"))
    
    # User agent rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    ]
    
    # File paths and directories (relative to project root)
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    LOGS_DIR = os.path.join(DATA_DIR, "logs")
    CSV_DIR = os.path.join(DATA_DIR, "csv")
    JSON_DIR = os.path.join(DATA_DIR, "json")
    
    # Output file settings
    CSV_ENCODING = "utf-8"
    JSON_INDENT = 2
    
    # Scraping limits and defaults
    DEFAULT_MAX_PAGES = int(os.getenv("SCRAPER_MAX_PAGES", "0"))  # 0 means no limit
    MAX_CONCURRENT_REQUESTS = int(os.getenv("SCRAPER_MAX_CONCURRENT", "1"))
    BATCH_SIZE = int(os.getenv("SCRAPER_BATCH_SIZE", "10"))
    
    # Field mappings for data cleaning
    RATING_MAP = {
        'One': 1,
        'Two': 2,
        'Three': 3,
        'Four': 4,
        'Five': 5
    }
    
    # Request headers configuration
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    # Logging settings
    LOG_LEVEL = os.getenv("SCRAPER_LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Error handling
    MAX_CONSECUTIVE_ERRORS = int(os.getenv("SCRAPER_MAX_CONSECUTIVE_ERRORS", "5"))
    ERROR_SLEEP_TIME = float(os.getenv("SCRAPER_ERROR_SLEEP_TIME", "5.0"))
    
    # Data validation settings
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 500
    MIN_PRICE = 0.0
    MAX_PRICE = 10000.0
    
    @classmethod
    def get_headers(cls, user_agent_index: int = 0) -> Dict[str, str]:
        """
        Get HTTP headers for requests.
        
        Args:
            user_agent_index: Index of user agent to use
            
        Returns:
            Dictionary of HTTP headers
        """
        headers = cls.DEFAULT_HEADERS.copy()
        headers['User-Agent'] = cls.USER_AGENTS[user_agent_index % len(cls.USER_AGENTS)]
        return headers
    
    @classmethod
    def get_random_headers(cls) -> Dict[str, str]:
        """
        Get HTTP headers with random user agent.
        
        Returns:
            Dictionary of HTTP headers with random user agent
        """
        import random
        index = random.randint(0, len(cls.USER_AGENTS) - 1)
        return cls.get_headers(index)
    
    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        try:
            os.makedirs(cls.DATA_DIR, exist_ok=True)
            os.makedirs(cls.LOGS_DIR, exist_ok=True)
            os.makedirs(cls.CSV_DIR, exist_ok=True)
            os.makedirs(cls.JSON_DIR, exist_ok=True)
        except (OSError, PermissionError):
            # Can't create directories, likely in serverless environment
            pass
    
    @classmethod
    def validate_price(cls, price: float) -> bool:
        """
        Validate if price is within acceptable range.
        
        Args:
            price: Price to validate
            
        Returns:
            True if price is valid, False otherwise
        """
        return cls.MIN_PRICE <= price <= cls.MAX_PRICE
    
    @classmethod
    def validate_title(cls, title: str) -> bool:
        """
        Validate if title meets requirements.
        
        Args:
            title: Title to validate
            
        Returns:
            True if title is valid, False otherwise
        """
        return title and cls.MIN_TITLE_LENGTH <= len(title.strip()) <= cls.MAX_TITLE_LENGTH
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """
        Get a summary of current scraper configuration.
        
        Returns:
            Dictionary containing configuration summary
        """
        return {
            'base_url': cls.BASE_URL,
            'rate_limit': cls.DEFAULT_RATE_LIMIT,
            'max_retries': cls.DEFAULT_MAX_RETRIES,
            'timeout': cls.REQUEST_TIMEOUT,
            'max_pages': cls.DEFAULT_MAX_PAGES,
            'max_concurrent': cls.MAX_CONCURRENT_REQUESTS,
            'batch_size': cls.BATCH_SIZE,
            'data_dir': cls.DATA_DIR,
            'user_agents_count': len(cls.USER_AGENTS),
            'log_level': cls.LOG_LEVEL,
            'max_consecutive_errors': cls.MAX_CONSECUTIVE_ERRORS
        }


class ScraperLogger:
    """Enhanced logging system for scraping operations."""
    
    def __init__(self, name: str = "scrapbook_scraper", log_dir: str = None):
        """
        Initialize the scraper logger.
        
        Args:
            name: Logger name
            log_dir: Directory to store log files (defaults to ScraperConfig.LOGS_DIR)
        """
        self.name = name
        self.log_dir = log_dir or ScraperConfig.LOGS_DIR
        self.logger = logging.getLogger(name)
        self.setup_logger()
        
        # Performance tracking
        self.start_times = {}
        self.operation_stats = {}
    
    def setup_logger(self) -> None:
        """Set up logger with file and console handlers."""
        # Check if we're in a serverless/read-only environment
        is_serverless = os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or not self._can_write_to_dir()
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(getattr(logging, ScraperConfig.LOG_LEVEL.upper()))
        
        # Create formatters
        detailed_formatter = logging.Formatter(ScraperConfig.LOG_FORMAT)
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler (always available)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # Only add file handlers if not in serverless environment
        if not is_serverless:
            try:
                # Create log directory
                os.makedirs(self.log_dir, exist_ok=True)
                
                json_formatter = JsonScrapingFormatter()
                
                # File handler for detailed logs
                scraper_log_file = os.path.join(self.log_dir, f"{self.name}.log")
                file_handler = logging.handlers.RotatingFileHandler(
                    scraper_log_file,
                    maxBytes=ScraperConfig.LOG_MAX_BYTES,
                    backupCount=ScraperConfig.LOG_BACKUP_COUNT,
                    encoding='utf-8'
                )
                file_handler.setFormatter(detailed_formatter)
                file_handler.setLevel(logging.DEBUG)
                self.logger.addHandler(file_handler)
                
                # Error handler for critical issues
                error_log_file = os.path.join(self.log_dir, f"{self.name}_errors.log")
                error_handler = logging.handlers.RotatingFileHandler(
                    error_log_file,
                    maxBytes=ScraperConfig.LOG_MAX_BYTES // 2,
                    backupCount=3,
                    encoding='utf-8'
                )
                error_handler.setFormatter(detailed_formatter)
                error_handler.setLevel(logging.ERROR)
                self.logger.addHandler(error_handler)
                
                # Structured JSON handler for analysis
                json_log_file = os.path.join(self.log_dir, f"{self.name}_structured.jsonl")
                json_handler = JsonScrapingHandler(json_log_file)
                json_handler.setFormatter(json_formatter)
                json_handler.setLevel(logging.INFO)
                self.logger.addHandler(json_handler)
            except (OSError, PermissionError) as e:
                # If file logging fails, just log to console
                self.logger.warning(f"File logging disabled due to: {e}")
    
    def _can_write_to_dir(self) -> bool:
        """Check if we can write to the log directory."""
        try:
            test_file = os.path.join(self.log_dir, '.write_test')
            os.makedirs(self.log_dir, exist_ok=True)
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except (OSError, PermissionError):
            return False
    
    def log_scraping_start(self, operation: str, details: Dict[str, Any] = None) -> None:
        """
        Log the start of a scraping operation.
        
        Args:
            operation: Operation name
            details: Additional operation details
        """
        import time
        self.start_times[operation] = time.time()
        details = details or {}
        
        extra_data = {
            'event_type': 'scraping_start',
            'operation': operation,
            'details': details
        }
        
        self.logger.info(f"Started scraping operation: {operation}", extra=extra_data)
    
    def log_scraping_end(self, operation: str, success: bool = True, 
                        results: Dict[str, Any] = None, error: str = None) -> None:
        """
        Log the end of a scraping operation.
        
        Args:
            operation: Operation name
            success: Whether operation was successful
            results: Operation results
            error: Error message if failed
        """
        import time
        from datetime import datetime
        
        end_time = time.time()
        start_time = self.start_times.get(operation, end_time)
        duration = end_time - start_time
        
        # Update operation stats
        if operation not in self.operation_stats:
            self.operation_stats[operation] = {
                'count': 0,
                'total_duration': 0,
                'success_count': 0,
                'error_count': 0
            }
        
        stats = self.operation_stats[operation]
        stats['count'] += 1
        stats['total_duration'] += duration
        
        extra_data = {
            'event_type': 'scraping_end',
            'operation': operation,
            'success': success,
            'duration': duration,
            'results': results or {},
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            stats['success_count'] += 1
            self.logger.info(f"Completed scraping operation: {operation} in {duration:.2f}s", extra=extra_data)
        else:
            stats['error_count'] += 1
            self.logger.error(f"Failed scraping operation: {operation} after {duration:.2f}s - {error}", extra=extra_data)
        
        # Clean up start time
        if operation in self.start_times:
            del self.start_times[operation]
    
    def log_page_scraped(self, url: str, items_found: int, page_type: str = "page") -> None:
        """
        Log page scraping results.
        
        Args:
            url: URL that was scraped
            items_found: Number of items found on the page
            page_type: Type of page (e.g., 'category', 'book', 'listing')
        """
        extra_data = {
            'event_type': 'page_scraped',
            'url': url,
            'page_type': page_type,
            'items_found': items_found
        }
        
        self.logger.info(f"Scraped {page_type}: {url} - Found {items_found} items", extra=extra_data)
    
    def log_data_saved(self, filename: str, record_count: int, file_type: str = "csv") -> None:
        """
        Log data saving operations.
        
        Args:
            filename: Name of the saved file
            record_count: Number of records saved
            file_type: Type of file saved
        """
        extra_data = {
            'event_type': 'data_saved',
            'filename': filename,
            'record_count': record_count,
            'file_type': file_type
        }
        
        self.logger.info(f"Saved {record_count} records to {filename}", extra=extra_data)
    
    def log_error(self, operation: str, error: str, url: str = None, retry_count: int = 0):
        """
        Log scraping errors.
        
        Args:
            operation: Operation where error occurred
            error: Error message
            url: URL where error occurred (if applicable)
            retry_count: Current retry attempt
        """
        extra_data = {
            'event_type': 'scraping_error',
            'operation': operation,
            'error': error,
            'url': url,
            'retry_count': retry_count
        }
        
        self.logger.error(f"Scraping error in {operation}: {error} (retry: {retry_count})", extra=extra_data)
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all logged operations.
        
        Returns:
            Dictionary containing operation statistics
        """
        stats_summary = {}
        
        for operation, stats in self.operation_stats.items():
            avg_duration = stats['total_duration'] / stats['count'] if stats['count'] > 0 else 0
            success_rate = stats['success_count'] / stats['count'] if stats['count'] > 0 else 0
            
            stats_summary[operation] = {
                'total_runs': stats['count'],
                'successful_runs': stats['success_count'],
                'failed_runs': stats['error_count'],
                'success_rate': round(success_rate * 100, 2),
                'total_duration': round(stats['total_duration'], 2),
                'average_duration': round(avg_duration, 2)
            }
        
        return stats_summary


class JsonScrapingFormatter(logging.Formatter):
    """Custom JSON formatter for scraping logs."""
    
    def format(self, record):
        """Format log record as JSON."""
        import json
        from datetime import datetime
        
        log_obj = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add scraping-specific extra fields
        scraping_fields = [
            'event_type', 'operation', 'details', 'success', 'duration',
            'results', 'error', 'url', 'page_type', 'items_found',
            'filename', 'record_count', 'file_type', 'retry_count'
        ]
        
        for field in scraping_fields:
            if hasattr(record, field):
                log_obj[field] = getattr(record, field)
        
        return json.dumps(log_obj, ensure_ascii=False, default=str)


class JsonScrapingHandler(logging.Handler):
    """Custom handler for writing structured scraping logs to JSON file."""
    
    def __init__(self, filename: str):
        """Initialize JSON scraping handler."""
        super().__init__()
        self.filename = filename
        self.ensure_directory()
    
    def ensure_directory(self):
        """Ensure the log directory exists."""
        directory = os.path.dirname(self.filename)
        if directory:
            try:
                os.makedirs(directory, exist_ok=True)
            except (OSError, PermissionError):
                # Can't create directory, likely in serverless environment
                pass
    
    def emit(self, record):
        """Emit a log record to JSON file."""
        try:
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(self.format(record))
                f.write('\n')
        except (OSError, PermissionError):
            # Can't write to file, likely in serverless environment
            # Fall back to console logging
            print(f"LOG: {self.format(record)}")
        except Exception:
            self.handleError(record)


def setup_scraper_logging(name: str = "scrapbook_scraper") -> logging.Logger:
    """
    Set up and return a scraper logger.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    scraper_logger = ScraperLogger(name)
    return scraper_logger.logger


# Environment file template for scraping
SCRAPER_ENV_TEMPLATE = """# Scraper Configuration
SCRAPER_RATE_LIMIT=1.0
SCRAPER_MAX_RETRIES=3
SCRAPER_TIMEOUT=10
SCRAPER_RETRY_DELAY=2.0
SCRAPER_MAX_PAGES=0
SCRAPER_MAX_CONCURRENT=1
SCRAPER_BATCH_SIZE=10

# Error Handling
SCRAPER_MAX_CONSECUTIVE_ERRORS=5
SCRAPER_ERROR_SLEEP_TIME=5.0

# Logging Configuration
SCRAPER_LOG_LEVEL=INFO
"""


def create_scraper_env_file() -> None:
    """Create a sample .env file for scraper if it doesn't exist."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.scraper')
    
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(SCRAPER_ENV_TEMPLATE)
        print(f"Created sample scraper .env file at {env_path}")
    else:
        print(f"Scraper .env file already exists at {env_path}")


if __name__ == "__main__":
    # Create sample .env file for scraper
    create_scraper_env_file()
    
    # Create necessary directories
    ScraperConfig.create_directories()
    
    # Display configuration summary
    config = ScraperConfig.get_config_summary()
    
    print("Scraper Configuration Summary:")
    print("-" * 50)
    for key, value in config.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Test logging setup
    logger = setup_scraper_logging("test_scraper")
    logger.info("Scraper logging system initialized successfully")
