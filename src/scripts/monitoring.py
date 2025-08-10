"""
Monitoring and logging utilities for the scraping system.
Provides structured logging, performance tracking, and error reporting.
"""

import json
import logging
import logging.handlers
import os
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any, Optional, List
from functools import wraps


class ScrapingLogger:
    """Enhanced logging system for scraping operations."""
    
    def __init__(self, name: str, log_dir: str = "../data/logs"):
        """
        Initialize the scraping logger.
        
        Args:
            name: Logger name
            log_dir: Directory to store log files
        """
        self.name = name
        self.log_dir = log_dir
        self.logger = logging.getLogger(name)
        self.setup_logger()
        
        # Performance tracking
        self.start_times = {}
        self.operation_stats = {}
    
    def setup_logger(self) -> None:
        """Set up logger with file and console handlers."""
        # Check if we're in a serverless/read-only environment
        is_serverless = os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME')
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(logging.INFO)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
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
                
                # File handler for detailed logs
                log_file = os.path.join(self.log_dir, f"{self.name}.log")
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
                )
                file_handler.setFormatter(detailed_formatter)
                file_handler.setLevel(logging.DEBUG)
                self.logger.addHandler(file_handler)
                
                # Error handler
                error_file = os.path.join(self.log_dir, f"{self.name}_errors.log")
                error_handler = logging.handlers.RotatingFileHandler(
                    error_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
                )
                error_handler.setFormatter(detailed_formatter)
                error_handler.setLevel(logging.ERROR)
                self.logger.addHandler(error_handler)
            except (OSError, PermissionError) as e:
                # If file logging fails, just log to console
                self.logger.warning(f"File logging disabled due to: {e}")
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)
        
        # Structured JSON handler for analysis
        json_file = os.path.join(self.log_dir, f"{self.name}_structured.jsonl")
        json_handler = JsonHandler(json_file)
        json_handler.setLevel(logging.INFO)
        self.logger.addHandler(json_handler)
    
    def log_scraping_start(self, operation: str, details: Dict[str, Any] = None) -> None:
        """
        Log the start of a scraping operation.
        
        Args:
            operation: Operation name
            details: Additional operation details
        """
        self.start_times[operation] = time.time()
        details = details or {}
        
        self.logger.info(f"Started {operation}", extra={
            'operation': operation,
            'event_type': 'operation_start',
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
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
        
        if success:
            stats['success_count'] += 1
            self.logger.info(f"Completed {operation} successfully in {duration:.2f}s", extra={
                'operation': operation,
                'event_type': 'operation_end',
                'success': True,
                'duration': duration,
                'results': results or {},
                'timestamp': datetime.now().isoformat()
            })
        else:
            stats['error_count'] += 1
            self.logger.error(f"Failed {operation} after {duration:.2f}s: {error}", extra={
                'operation': operation,
                'event_type': 'operation_end',
                'success': False,
                'duration': duration,
                'error': error,
                'timestamp': datetime.now().isoformat()
            })
        
        # Clean up start time
        if operation in self.start_times:
            del self.start_times[operation]
    
    def log_page_scraped(self, url: str, items_found: int, page_type: str = "page") -> None:
        """
        Log page scraping results.
        
        Args:
            url: URL that was scraped
            items_found: Number of items found on the page
            page_type: Type of page (e.g., 'category', 'book', 'page')
        """
        self.logger.info(f"Scraped {page_type}: {url} - Found {items_found} items", extra={
            'event_type': 'page_scraped',
            'url': url,
            'page_type': page_type,
            'items_found': items_found,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_data_saved(self, filename: str, record_count: int, file_type: str = "csv") -> None:
        """
        Log data saving operations.
        
        Args:
            filename: Name of the saved file
            record_count: Number of records saved
            file_type: Type of file saved
        """
        self.logger.info(f"Saved {record_count} records to {filename}", extra={
            'event_type': 'data_saved',
            'filename': filename,
            'record_count': record_count,
            'file_type': file_type,
            'timestamp': datetime.now().isoformat()
        })
    
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
    
    @contextmanager
    def log_operation(self, operation: str, details: Dict[str, Any] = None):
        """
        Context manager for logging operations.
        
        Args:
            operation: Operation name
            details: Additional operation details
        """
        self.log_scraping_start(operation, details)
        start_time = time.time()
        
        try:
            yield
            duration = time.time() - start_time
            self.log_scraping_end(operation, success=True, results={'duration': duration})
        except Exception as e:
            duration = time.time() - start_time
            self.log_scraping_end(operation, success=False, error=str(e))
            raise


class JsonHandler(logging.Handler):
    """Custom logging handler that outputs structured JSON logs."""
    
    def __init__(self, filename: str):
        """
        Initialize JSON handler.
        
        Args:
            filename: File to write JSON logs to
        """
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
        """
        Emit a log record as JSON.
        
        Args:
            record: Log record to emit
        """
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Add extra fields if present
            if hasattr(record, 'operation'):
                log_entry['operation'] = record.operation
            if hasattr(record, 'event_type'):
                log_entry['event_type'] = record.event_type
            if hasattr(record, 'details'):
                log_entry['details'] = record.details
            if hasattr(record, 'results'):
                log_entry['results'] = record.results
            if hasattr(record, 'url'):
                log_entry['url'] = record.url
            if hasattr(record, 'success'):
                log_entry['success'] = record.success
            if hasattr(record, 'duration'):
                log_entry['duration'] = record.duration
            
            with open(self.filename, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False, default=str)
                f.write('\n')
                
        except Exception:
            self.handleError(record)


def performance_monitor(operation_name: str = None):
    """
    Decorator to monitor function performance.
    
    Args:
        operation_name: Custom operation name for logging
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            logger = ScrapingLogger('performance_monitor')
            
            with logger.log_operation(op_name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


class PerformanceTracker:
    """Track and analyze scraping performance metrics."""
    
    def __init__(self):
        """Initialize the performance tracker."""
        self.metrics = {
            'requests': [],
            'pages_scraped': 0,
            'items_extracted': 0,
            'errors': [],
            'start_time': None,
            'end_time': None
        }
    
    def start_tracking(self):
        """Start performance tracking."""
        self.metrics['start_time'] = time.time()
    
    def stop_tracking(self):
        """Stop performance tracking."""
        self.metrics['end_time'] = time.time()
    
    def record_request(self, url: str, duration: float, status_code: int = 200):
        """
        Record a request for performance analysis.
        
        Args:
            url: URL that was requested
            duration: Request duration in seconds
            status_code: HTTP status code
        """
        self.metrics['requests'].append({
            'url': url,
            'duration': duration,
            'status_code': status_code,
            'timestamp': time.time()
        })
    
    def record_page_scraped(self, items_count: int):
        """
        Record a scraped page.
        
        Args:
            items_count: Number of items extracted from the page
        """
        self.metrics['pages_scraped'] += 1
        self.metrics['items_extracted'] += items_count
    
    def record_error(self, error: str, url: str = None):
        """
        Record an error for analysis.
        
        Args:
            error: Error message
            url: URL where error occurred
        """
        self.metrics['errors'].append({
            'error': error,
            'url': url,
            'timestamp': time.time()
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get performance summary.
        
        Returns:
            Dictionary containing performance metrics
        """
        total_duration = 0
        if self.metrics['start_time'] and self.metrics['end_time']:
            total_duration = self.metrics['end_time'] - self.metrics['start_time']
        
        requests = self.metrics['requests']
        request_durations = [req['duration'] for req in requests]
        
        summary = {
            'total_duration': total_duration,
            'pages_scraped': self.metrics['pages_scraped'],
            'items_extracted': self.metrics['items_extracted'],
            'total_requests': len(requests),
            'total_errors': len(self.metrics['errors']),
            'average_items_per_page': self.metrics['items_extracted'] / max(self.metrics['pages_scraped'], 1),
            'request_performance': {
                'avg_duration': sum(request_durations) / len(request_durations) if request_durations else 0,
                'min_duration': min(request_durations) if request_durations else 0,
                'max_duration': max(request_durations) if request_durations else 0,
                'requests_per_minute': len(requests) / (total_duration / 60) if total_duration > 0 else 0
            },
            'error_rate': len(self.metrics['errors']) / max(len(requests), 1) * 100
        }
        
        return summary
