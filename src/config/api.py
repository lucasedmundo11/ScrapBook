"""
Configuration module for the ScrapBook API.
Centralizes all API-related configuration settings and environment variables.
"""

import os
import logging
import logging.handlers
from datetime import timedelta
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class APIConfig:
    """Configuration settings for the API system."""
    
    # API Server settings
    API_HOST = os.getenv("API_HOST", "localhost")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_VERSION = "1.0.0"
    
    # JWT Authentication settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/books.db")
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    
    # Data directories (relative to project root)
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    DATA_CSV_DIR = os.path.join(DATA_DIR, "csv")
    DATA_JSON_DIR = os.path.join(DATA_DIR, "json")
    DATA_LOGS_DIR = os.path.join(DATA_DIR, "logs")
    
    # API Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")
    
    # CORS settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization"]
    
    # API Response settings
    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # File upload settings (for future use)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
    
    # Cache settings
    CACHE_TYPE = os.getenv("CACHE_TYPE", "simple")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))
    
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", JWT_SECRET_KEY)
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        try:
            os.makedirs(cls.DATA_DIR, exist_ok=True)
            os.makedirs(cls.DATA_CSV_DIR, exist_ok=True)
            os.makedirs(cls.DATA_JSON_DIR, exist_ok=True)
            os.makedirs(cls.DATA_LOGS_DIR, exist_ok=True)
            os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        except (OSError, PermissionError):
            # Can't create directories, likely in serverless environment
            pass
    
    @classmethod
    def get_jwt_expire_delta(cls) -> timedelta:
        """Get JWT token expiration delta."""
        return timedelta(minutes=cls.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    @classmethod
    def get_refresh_expire_delta(cls) -> timedelta:
        """Get JWT refresh token expiration delta."""
        return timedelta(days=cls.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """
        Get a summary of current API configuration.
        
        Returns:
            Dictionary containing configuration summary
        """
        return {
            'api_host': cls.API_HOST,
            'api_port': cls.API_PORT,
            'api_version': cls.API_VERSION,
            'jwt_expire_minutes': cls.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            'database_url': cls.DATABASE_URL,
            'data_dir': cls.DATA_DIR,
            'log_level': cls.LOG_LEVEL,
            'rate_limit_per_minute': cls.RATE_LIMIT_REQUESTS_PER_MINUTE,
            'default_page_size': cls.DEFAULT_PAGE_SIZE,
            'max_page_size': cls.MAX_PAGE_SIZE,
            'cors_origins': cls.CORS_ORIGINS
        }


class APILogger:
    """Enhanced logging system for API operations."""
    
    def __init__(self, name: str = "scrapbook_api", log_dir: str = None):
        """
        Initialize the API logger.
        
        Args:
            name: Logger name
            log_dir: Directory to store log files (defaults to APIConfig.DATA_LOGS_DIR)
        """
        self.name = name
        self.log_dir = log_dir or APIConfig.DATA_LOGS_DIR
        self.logger = logging.getLogger(name)
        self.setup_logger()
    
    def setup_logger(self) -> None:
        """Set up logger with file and console handlers."""
        # Check if we're in a serverless/read-only environment
        is_serverless = os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME')
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Set log level
        log_level = getattr(logging, APIConfig.API_LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Create formatters
        detailed_formatter = logging.Formatter(APIConfig.LOG_FORMAT)
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
                
                json_formatter = JsonLogFormatter()
                
                # File handler for all logs
                api_log_file = os.path.join(self.log_dir, f"{self.name}.log")
                file_handler = logging.handlers.RotatingFileHandler(
                    api_log_file,
                    maxBytes=APIConfig.LOG_MAX_BYTES,
                    backupCount=APIConfig.LOG_BACKUP_COUNT,
                    encoding='utf-8'
                )
                file_handler.setFormatter(detailed_formatter)
                file_handler.setLevel(logging.DEBUG)
                self.logger.addHandler(file_handler)
                
                # Error handler for critical issues
                error_log_file = os.path.join(self.log_dir, f"{self.name}_errors.log")
                error_handler = logging.handlers.RotatingFileHandler(
                    error_log_file,
                    maxBytes=APIConfig.LOG_MAX_BYTES // 2,
                    backupCount=3,
                    encoding='utf-8'
                )
                error_handler.setFormatter(detailed_formatter)
                error_handler.setLevel(logging.ERROR)
                self.logger.addHandler(error_handler)
                
                # JSON handler for structured logs
                json_log_file = os.path.join(self.log_dir, f"{self.name}_structured.jsonl")
                json_handler = JsonFileHandler(json_log_file)
                json_handler.setFormatter(json_formatter)
                json_handler.setLevel(logging.INFO)
                self.logger.addHandler(json_handler)
            except (OSError, PermissionError) as e:
                # If file logging fails, just log to console
                self.logger.warning(f"File logging disabled due to: {e}")
    
    def log_api_request(self, method: str, url: str, status_code: int, 
                       response_time: float, user_id: str = None, error: str = None):
        """
        Log API request details.
        
        Args:
            method: HTTP method
            url: Request URL
            status_code: Response status code
            response_time: Response time in seconds
            user_id: User identifier
            error: Error message if any
        """
        extra_data = {
            'event_type': 'api_request',
            'method': method,
            'url': url,
            'status_code': status_code,
            'response_time': response_time,
            'user_id': user_id,
            'error': error
        }
        
        if error:
            self.logger.error(f"API {method} {url} - {status_code} - {response_time:.3f}s - {error}", extra=extra_data)
        else:
            self.logger.info(f"API {method} {url} - {status_code} - {response_time:.3f}s", extra=extra_data)
    
    def log_database_operation(self, operation: str, table: str, duration: float, 
                             record_count: int = None, error: str = None):
        """
        Log database operations.
        
        Args:
            operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
            table: Table name
            duration: Operation duration in seconds
            record_count: Number of records affected
            error: Error message if any
        """
        extra_data = {
            'event_type': 'database_operation',
            'operation': operation,
            'table': table,
            'duration': duration,
            'record_count': record_count,
            'error': error
        }
        
        if error:
            self.logger.error(f"DB {operation} on {table} failed after {duration:.3f}s - {error}", extra=extra_data)
        else:
            self.logger.info(f"DB {operation} on {table} - {duration:.3f}s - {record_count} records", extra=extra_data)
    
    def log_authentication(self, username: str, success: bool, ip_address: str = None):
        """
        Log authentication attempts.
        
        Args:
            username: Username attempting authentication
            success: Whether authentication was successful
            ip_address: Client IP address
        """
        extra_data = {
            'event_type': 'authentication',
            'username': username,
            'success': success,
            'ip_address': ip_address
        }
        
        if success:
            self.logger.info(f"Successful login for user: {username} from {ip_address}", extra=extra_data)
        else:
            self.logger.warning(f"Failed login attempt for user: {username} from {ip_address}", extra=extra_data)


class JsonLogFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
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
        
        # Add extra fields if present
        extra_fields = [
            'event_type', 'method', 'url', 'status_code', 'response_time',
            'user_id', 'error', 'operation', 'table', 'duration', 
            'record_count', 'username', 'success', 'ip_address'
        ]
        
        for field in extra_fields:
            if hasattr(record, field):
                log_obj[field] = getattr(record, field)
        
        return json.dumps(log_obj, ensure_ascii=False, default=str)


class JsonFileHandler(logging.Handler):
    """Custom handler for writing JSON logs to file."""
    
    def __init__(self, filename: str):
        """Initialize JSON file handler."""
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


def setup_api_logging(name: str = "scrapbook_api") -> logging.Logger:
    """
    Set up and return an API logger.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    api_logger = APILogger(name)
    return api_logger.logger


# Environment file template for API
API_ENV_TEMPLATE = """# API Configuration
API_HOST=localhost
API_PORT=8000

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Configuration
DATABASE_URL=sqlite:///./data/books.db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_STORAGE_URI=memory://

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Pagination
DEFAULT_PAGE_SIZE=50
MAX_PAGE_SIZE=100

# Logging
LOG_LEVEL=INFO

# Cache
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300

# Security
SECRET_KEY=your-secret-key-change-this-in-production
SESSION_COOKIE_SECURE=False
"""


def create_api_env_file() -> None:
    """Create a sample .env file for API if it doesn't exist."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.api')
    
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(API_ENV_TEMPLATE)
        print(f"Created sample API .env file at {env_path}")
    else:
        print(f"API .env file already exists at {env_path}")


if __name__ == "__main__":
    # Create sample .env file for API
    create_api_env_file()
    
    # Create necessary directories
    APIConfig.create_directories()
    
    # Display configuration summary
    config = APIConfig.get_config_summary()
    
    print("API Configuration Summary:")
    print("-" * 50)
    for key, value in config.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Test logging setup
    logger = setup_api_logging("test_api")
    logger.info("API logging system initialized successfully")