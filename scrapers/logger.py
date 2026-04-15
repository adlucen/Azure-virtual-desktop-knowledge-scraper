#!/usr/bin/env python3
"""
Logging and progress tracking for AVD Knowledge Scraper
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Try to import colorama for Windows color support
try:
    import colorama
    colorama.init()
    COLORS_ENABLED = True
except ImportError:
    COLORS_ENABLED = False


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color-coded log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        if COLORS_ENABLED or sys.platform != 'win32':
            levelname_colored = (
                f"{self.COLORS.get(record.levelname, '')}"
                f"{record.levelname:8}"
                f"{self.COLORS['RESET']}"
            )
            record.levelname = levelname_colored
        return super().format(record)


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration with console and file output
    
    Args:
        verbose: If True, set to DEBUG level, otherwise INFO
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Default log file with timestamp
    if log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'scraper_{timestamp}.log'
    
    # Set log level
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers = []  # Clear existing handlers
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Startup message
    logger.info("="*70)
    logger.info("AVD Knowledge Scraper - Starting")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Verbosity: {'DEBUG' if verbose else 'INFO'}")
    logger.info("="*70)
    
    return logger


class ProgressTracker:
    """Track and display scraping progress in real-time"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'documents_saved': 0,
            'start_time': datetime.now()
        }
        self.current_source = None
        self.source_start = None
    
    def start_source(self, source_name: str):
        """Start tracking a new source"""
        self.current_source = source_name
        self.source_start = datetime.now()
        self.logger.info("")
        self.logger.info("="*70)
        self.logger.info(f"📥 Starting: {source_name}")
        self.logger.info("="*70)
    
    def end_source(self, doc_count: int = 0):
        """End tracking current source"""
        if self.source_start:
            duration = (datetime.now() - self.source_start).total_seconds()
            # Scrapers call BaseScraper._save_markdown() directly rather than
            # log_save(), so accumulate the source's count here to keep the
            # final summary accurate.
            self.stats['documents_saved'] += doc_count
            self.logger.info("-"*70)
            self.logger.info(f"✓ Completed: {self.current_source}")
            self.logger.info(f"  Documents: {doc_count}")
            self.logger.info(f"  Duration: {duration:.1f}s")
            self.logger.info("="*70)
    
    def log_fetch(self, url: str):
        """Log a successful fetch"""
        self.stats['total_requests'] += 1
        self.stats['successful_requests'] += 1
        # Only show in debug mode to avoid spam
        self.logger.debug(f"  → Fetched: {url}")
    
    def log_save(self, filepath: str):
        """Log a saved document"""
        self.stats['documents_saved'] += 1
        self.logger.info(f"  💾 Saved: {filepath}")
    
    def log_error(self, message: str, url: str = None):
        """Log an error"""
        self.stats['failed_requests'] += 1
        if url:
            self.logger.error(f"  ✗ Error with {url}: {message}")
        else:
            self.logger.error(f"  ✗ Error: {message}")
    
    def log_skip(self, reason: str):
        """Log a skipped item"""
        self.logger.debug(f"  ⊘ Skipped: {reason}")
    
    def print_summary(self):
        """Print final statistics"""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        
        self.logger.info("")
        self.logger.info("="*70)
        self.logger.info("📊 SCRAPING SUMMARY")
        self.logger.info("="*70)
        self.logger.info(f"Total Runtime: {duration:.1f}s ({duration/60:.1f} minutes)")
        self.logger.info(f"Documents Saved: {self.stats['documents_saved']}")
        self.logger.info(f"Successful Requests: {self.stats['successful_requests']}")
        self.logger.info(f"Failed Requests: {self.stats['failed_requests']}")
        
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            self.logger.info(f"Success Rate: {success_rate:.1f}%")
        
        self.logger.info("="*70)
        self.logger.info("✓ Scraping complete!")
        self.logger.info("="*70)
