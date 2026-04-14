#!/usr/bin/env python3
"""
Base scraper class with common functionality
"""

import hashlib
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup


class BaseScraper(ABC):
    """Base class for all scrapers with common functionality"""
    
    def __init__(self, config_path: str = "config/scraper_config.yaml"):
        """Initialize scraper with configuration"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config['rate_limiting']['user_agent']
        })
        self.rate_limit_delay = 60 / self.config['rate_limiting']['requests_per_minute']
        self.last_request_time = 0
        
    def _load_config(self, config_path: str) -> Dict:
        """Load YAML configuration file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content with rate limiting and error handling"""
        self._rate_limit()
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            self.logger.debug(f"Fetched: {url}")
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _sanitize_filename(self, name: str, max_length: int = 100) -> str:
        """Sanitize string for use as filename.

        Caps at `max_length` chars (default 100) to stay under Windows'
        260-char MAX_PATH. Worst-case prefix+dir in this repo is ~60 chars
        (e.g. C:\\...\\output\\github\\AzurePowerShell-GH\\20260414_i9999_),
        leaving ~100 chars of title + `.md` with comfortable headroom.
        """
        sanitized = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
        # Collapse runs of underscores so truncation doesn't land mid-word-cluster
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')
        return sanitized.strip(' _').replace(' ', '_')[:max_length]
    
    def _create_frontmatter(self, metadata: Dict) -> str:
        """Create YAML frontmatter for markdown file"""
        frontmatter = ["---"]
        for key, value in metadata.items():
            if isinstance(value, list):
                frontmatter.append(f"{key}:")
                for item in value:
                    frontmatter.append(f"  - {item}")
            elif isinstance(value, datetime):
                frontmatter.append(f"{key}: {value.isoformat()}")
            else:
                if isinstance(value, str) and any(c in value for c in [':', '#', '"', "'"]):
                    value = f'"{value}"'
                frontmatter.append(f"{key}: {value}")
        frontmatter.append("---")
        frontmatter.append("")
        return "\n".join(frontmatter)
    
    def _save_markdown(self, content: str, metadata: Dict, output_path: Path):
        """Save content as markdown file with YAML frontmatter"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        frontmatter = self._create_frontmatter(metadata)
        full_content = f"{frontmatter}\n{content}"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        self.logger.info(f"Saved: {output_path}")
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        return urlparse(url).netloc
    
    @abstractmethod
    def scrape(self) -> List[Dict]:
        """Main scraping method - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def process_content(self, raw_content: str, url: str) -> Dict:
        """Process raw content into structured format - must be implemented"""
        pass
