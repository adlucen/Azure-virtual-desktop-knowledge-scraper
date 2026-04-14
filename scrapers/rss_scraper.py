#!/usr/bin/env python3
"""
Scraper for RSS feeds (blogs, Azure updates)
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import feedparser
import html2text

from base_scraper import BaseScraper


class RSSFeedScraper(BaseScraper):
    """Scraper for RSS feeds from blogs and Azure updates"""
    
    def __init__(self, config_path: str = "config/scraper_config.yaml"):
        super().__init__(config_path)
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.body_width = 0
        self.logger = logging.getLogger(__name__)
    
    def scrape(self) -> List[Dict]:
        """Main scrape method - scrapes both Azure updates and blogs"""
        all_content = []
        all_content.extend(self.scrape_azure_updates())
        all_content.extend(self.scrape_expert_blogs())
        return all_content
    
    def scrape_azure_updates(self) -> List[Dict]:
        """Scrape Azure updates feed"""
        config = self.config['scraping_targets']['azure_updates']
        if not config['enabled']:
            self.logger.info("Azure updates scraping disabled")
            return []
        
        self.logger.info("Scraping Azure Updates RSS feed")
        all_updates = []
        
        for feed_url in config['rss_feeds']:
            self.logger.debug(f"Parsing feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                if self._is_relevant_update(entry, config['keywords']):
                    update = self._process_feed_entry(entry, 'Azure Updates')
                    all_updates.append(update)
                    self._save_update(update, config['output_dir'])
        
        self.logger.info(f"Azure updates scraped: {len(all_updates)}")
        return all_updates
    
    def scrape_expert_blogs(self) -> List[Dict]:
        """Scrape expert blog RSS feeds"""
        config = self.config['scraping_targets']['expert_blogs']
        if not config['enabled']:
            self.logger.info("Expert blogs scraping disabled")
            return []
        
        self.logger.info("Scraping expert blogs")
        all_posts = []
        
        for blog in config['blogs']:
            if blog.get('type') == 'linkedin':
                self.logger.info(f"Skipping {blog['name']} (LinkedIn requires different method)")
                continue
            
            if 'rss' not in blog:
                self.logger.warning(f"No RSS feed for {blog['name']}")
                continue
            
            self.logger.info(f"Scraping {blog['name']}")
            feed = feedparser.parse(blog['rss'])
            
            for entry in feed.entries[:20]:
                post = self._process_feed_entry(entry, blog['name'])
                all_posts.append(post)
                self._save_update(post, config['output_dir'], blog['name'])
        
        self.logger.info(f"Blog posts scraped: {len(all_posts)}")
        return all_posts
    
    def _is_relevant_update(self, entry, keywords: List[str]) -> bool:
        """Check if Azure update is relevant"""
        text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
        return any(keyword.lower() in text for keyword in keywords)
    
    def _process_feed_entry(self, entry, source_name: str) -> Dict:
        """Process RSS feed entry"""
        content = entry.get('content', [{}])[0].get('value', '') or entry.get('summary', '')
        
        if content:
            markdown_content = self.html_converter.handle(content)
        else:
            markdown_content = entry.get('summary', '')
        
        published = entry.get('published_parsed') or entry.get('updated_parsed')
        if published:
            published_date = datetime(*published[:6])
        else:
            published_date = datetime.now()
        
        full_content = f"# {entry.get('title', 'Untitled')}\n\n{markdown_content}"
        
        metadata = {
            'source': source_name,
            'url': entry.get('link', ''),
            'title': entry.get('title', 'Untitled'),
            'author': entry.get('author', 'Unknown'),
            'published': published_date,
            'scraped_at': datetime.now(),
            'category': self._categorize_feed_content(entry, source_name),
            'tags': self._extract_feed_tags(entry)
        }
        
        return {
            'title': entry.get('title', 'Untitled'),
            'content': full_content,
            'metadata': metadata,
            'url': entry.get('link', ''),
            'content_hash': self._generate_content_hash(full_content)
        }
    
    def _categorize_feed_content(self, entry, source: str) -> str:
        """Categorize feed content"""
        title = entry.get('title', '').lower()
        summary = entry.get('summary', '').lower()
        text = f"{title} {summary}"
        
        if 'azure updates' in source.lower():
            return 'Azure-Updates'
        
        if any(kw in text for kw in ['avd', 'azure virtual desktop', 'wvd']):
            return 'AVD-Blog'
        elif any(kw in text for kw in ['fslogix', 'profile']):
            return 'FSLogix-Blog'
        elif any(kw in text for kw in ['intune', 'endpoint']):
            return 'Intune-Blog'
        
        return 'General-Blog'
    
    def _extract_feed_tags(self, entry) -> List[str]:
        """Extract tags from feed entry"""
        tags = []
        
        if hasattr(entry, 'tags'):
            tags.extend([tag.get('term', '') for tag in entry.tags])
        
        if hasattr(entry, 'categories'):
            tags.extend(entry.categories)
        
        return [tag for tag in tags if tag]
    
    def _save_update(self, update: Dict, output_dir: str, subfolder: str = None):
        """Save feed entry to markdown file"""
        base_dir = Path(output_dir)
        
        if subfolder:
            save_dir = base_dir / self._sanitize_filename(subfolder)
        else:
            save_dir = base_dir / update['metadata']['category']
        
        timestamp = update['metadata']['published'].strftime('%Y%m%d')
        filename = f"{timestamp}_{self._sanitize_filename(update['title'])}.md"
        
        output_path = save_dir / filename
        
        self._save_markdown(
            content=update['content'],
            metadata=update['metadata'],
            output_path=output_path
        )
    
    def process_content(self, raw_content: str, url: str) -> Dict:
        """Required by base class - not used for RSS scraper"""
        return {}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    from logger import setup_logging
    setup_logging(verbose=True)
    
    scraper = RSSFeedScraper()
    scraper.scrape_azure_updates()
    scraper.scrape_expert_blogs()
