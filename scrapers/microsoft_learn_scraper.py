#!/usr/bin/env python3
"""
Scraper for Microsoft Learn documentation
"""

import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import html2text

from base_scraper import BaseScraper


class MicrosoftLearnScraper(BaseScraper):
    """Scraper for Microsoft Learn documentation"""
    
    def __init__(self, config_path: str = "config/scraper_config.yaml"):
        super().__init__(config_path)
        self.config_section = self.config['scraping_targets']['microsoft_learn']
        self.visited_urls = set()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0
        self.logger = logging.getLogger(__name__)
        
    def scrape(self) -> List[Dict]:
        """Main scraping method for Microsoft Learn"""
        self.logger.info("Starting Microsoft Learn documentation scrape")
        all_articles = []
        
        for base_url in self.config_section['base_urls']:
            self.logger.info(f"Crawling: {base_url}")
            try:
                articles = self._crawl_documentation(base_url, depth=0)
                all_articles.extend(articles)
            except Exception as e:
                self.logger.error(f"Error crawling {base_url}: {e}")
        
        self.logger.info(f"Total articles scraped: {len(all_articles)}")
        return all_articles
    
    def _crawl_documentation(self, url: str, depth: int) -> List[Dict]:
        """Recursively crawl documentation pages"""
        if depth > self.config_section['depth'] or url in self.visited_urls:
            return []
        
        self.visited_urls.add(url)
        articles = []
        
        self.logger.debug(f"Crawling depth {depth}: {url}")
        raw_html = self._fetch_url(url)
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'lxml')
        
        # Process current page
        article = self.process_content(raw_html, url)
        if article:
            articles.append(article)
            self._save_article(article)
        
        # Find child pages
        if depth < self.config_section['depth']:
            links = self._extract_doc_links(soup, url)
            for link in links[:10]:  # Limit links per page to avoid overwhelming
                child_articles = self._crawl_documentation(link, depth + 1)
                articles.extend(child_articles)
        
        return articles
    
    def _extract_doc_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract relevant documentation links from page"""
        links = []
        base_path = urlparse(base_url).path.rstrip('/')
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)
            
            if (parsed.netloc == 'learn.microsoft.com' and
                parsed.path.startswith(base_path) and
                absolute_url not in self.visited_urls and
                not parsed.fragment):
                links.append(absolute_url)
        
        return list(set(links))
    
    def process_content(self, raw_html: str, url: str) -> Optional[Dict]:
        """Process Microsoft Learn page into structured format"""
        soup = BeautifulSoup(raw_html, 'lxml')
        
        # Extract main content
        main_content = soup.find('main') or soup.find('article')
        if not main_content:
            self.logger.warning(f"No main content found for {url}")
            return None
        
        # Remove noise
        for element in main_content.find_all(['nav', 'aside', 'footer']):
            element.decompose()
        
        # Extract title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "Untitled"
        
        # Extract metadata
        metadata = self._extract_metadata(soup, url, title)
        
        # Convert to markdown
        markdown_content = self.html_converter.handle(str(main_content))
        markdown_content = self._clean_markdown(markdown_content)
        
        return {
            'title': title,
            'content': markdown_content,
            'metadata': metadata,
            'url': url,
            'content_hash': self._generate_content_hash(markdown_content)
        }
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str, title: str) -> Dict:
        """Extract metadata from Microsoft Learn page"""
        metadata = {
            'source': 'Microsoft Learn',
            'url': url,
            'title': title,
            'scraped_at': datetime.now(),
            'category': self._categorize_content(url),
            'tags': []
        }
        
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta and keywords_meta.get('content'):
            metadata['tags'] = [k.strip() for k in keywords_meta['content'].split(',')]
        
        return metadata
    
    def _categorize_content(self, url: str) -> str:
        """Categorize content based on URL path"""
        path = urlparse(url).path.lower()
        
        if 'azure/virtual-desktop' in path:
            if 'troubleshoot' in path:
                return 'AVD-Troubleshooting'
            elif 'security' in path:
                return 'AVD-Security'
            elif 'deploy' in path or 'set-up' in path:
                return 'AVD-Deployment'
            return 'AVD-General'
        elif 'fslogix' in path:
            return 'FSLogix'
        elif 'windows-365' in path:
            return 'Windows365'
        elif 'intune' in path:
            return 'Intune'
        
        return 'General'
    
    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown content"""
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        markdown = re.sub(r'Skip to main content.*?\n', '', markdown, flags=re.IGNORECASE)
        return markdown.strip()
    
    def _save_article(self, article: Dict):
        """Save article to markdown file"""
        output_dir = Path(self.config_section['output_dir'])
        category = article['metadata']['category']
        
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{timestamp}_{self._sanitize_filename(article['title'])}.md"
        
        output_path = output_dir / category / filename
        
        self._save_markdown(
            content=article['content'],
            metadata=article['metadata'],
            output_path=output_path
        )


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    from logger import setup_logging
    setup_logging(verbose=True)
    
    scraper = MicrosoftLearnScraper()
    scraper.scrape()
