#!/usr/bin/env python3
"""
Scraper for Microsoft Tech Community blogs and discussion boards

Uses RSS for discovery, then optionally fetches each post's full HTML for
richer content (reply threads, code blocks) that RSS summaries drop.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import feedparser
import html2text
from bs4 import BeautifulSoup

from base_scraper import BaseScraper


class TechCommunityScraper(BaseScraper):
    """Scraper for Microsoft Tech Community boards."""

    def __init__(self, config_path: str = "config/scraper_config.yaml"):
        super().__init__(config_path)
        self.config_section = self.config['scraping_targets']['tech_community']
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.body_width = 0
        self.logger = logging.getLogger(__name__)

    def scrape(self) -> List[Dict]:
        """Scrape each configured board via RSS + per-post HTML enrichment."""
        if not self.config_section.get('enabled', False):
            self.logger.info("Tech Community scraping disabled")
            return []

        all_posts = []
        for board in self.config_section['boards']:
            self.logger.info(f"Scraping board: {board['name']}")
            try:
                posts = self._scrape_board(board)
                all_posts.extend(posts)
            except Exception as e:
                self.logger.error(f"Failed board {board['name']}: {e}")

        self.logger.info(f"Total Tech Community posts: {len(all_posts)}")
        return all_posts

    def _scrape_board(self, board: Dict) -> List[Dict]:
        """Scrape one board: RSS discovery + per-post HTML fetch."""
        max_posts = self.config_section.get('max_posts_per_board', 50)
        feed = feedparser.parse(board['rss'])

        posts = []
        for entry in feed.entries[:max_posts]:
            try:
                post = self._build_post_record(entry, board)
                if post:
                    posts.append(post)
                    self._save_post(post)
            except Exception as e:
                self.logger.error(f"Entry {entry.get('link', '?')} failed: {e}")

        return posts

    def _build_post_record(self, entry, board: Dict) -> Optional[Dict]:
        """Build post record from RSS entry + optional HTML enrichment."""
        url = entry.get('link', '')
        title = entry.get('title', 'Untitled')

        # Fallback: RSS summary
        summary_md = self.html_converter.handle(entry.get('summary', '')).strip()

        body_md = summary_md
        replies_md = ""

        if self.config_section.get('fetch_replies', False) and url:
            html = self._fetch_url(url)
            if html:
                full_body, replies = self._parse_post_html(html)
                if full_body:
                    body_md = full_body
                replies_md = replies

        published = entry.get('published_parsed') or entry.get('updated_parsed')
        pub_date = datetime(*published[:6]) if published else datetime.now()

        author = entry.get('author', 'Unknown')
        tags_list = (
            [t.get('term', '') for t in entry.tags]
            if hasattr(entry, 'tags') else []
        )

        content_parts = [
            f"# {title}",
            "",
            f"**Board:** {board['name']}  ",
            f"**Author:** {author}  ",
            f"**Published:** {pub_date.isoformat()}  ",
            f"**URL:** {url}",
            "",
            body_md,
        ]
        if replies_md:
            content_parts.extend(["", "## Replies", "", replies_md])

        content = "\n".join(content_parts)

        metadata = {
            'source': 'Microsoft Tech Community',
            'url': url,
            'title': title,
            'board': board['name'],
            'board_type': board.get('type', 'blog'),
            'author': author,
            'published': pub_date,
            'scraped_at': datetime.now(),
            'tags': [t for t in tags_list if t],
            'category': self._categorize(board),
        }

        return {
            'title': title,
            'content': content,
            'metadata': metadata,
            'url': url,
            'content_hash': self._generate_content_hash(content),
        }

    def _parse_post_html(self, html: str) -> Tuple[str, str]:
        """Extract post body + replies from Tech Community HTML.

        Tech Community runs on the Khoros Lithium platform; posts live in
        `.lia-message-body-content`, replies are `.lia-quilt-forum-message`.
        Selectors are best-effort — platform markup evolves periodically.
        """
        soup = BeautifulSoup(html, 'lxml')

        body_md = ""
        body_el = soup.select_one('.lia-message-body-content') or soup.select_one('article')
        if body_el:
            for el in body_el.find_all(['script', 'style', 'nav']):
                el.decompose()
            body_md = self.html_converter.handle(str(body_el)).strip()

        replies_md = ""
        reply_els = soup.select('.lia-quilt-forum-message')
        # First match is typically the OP; skip it
        for reply in reply_els[1:11]:
            author_el = reply.select_one('.lia-user-name-link')
            author = author_el.get_text(strip=True) if author_el else 'unknown'
            r_body_el = reply.select_one('.lia-message-body-content')
            if not r_body_el:
                continue
            reply_body = self.html_converter.handle(str(r_body_el)).strip()
            is_solution = bool(reply.select_one('.lia-panel-message-solution'))
            suffix = " (marked as solution)" if is_solution else ""
            replies_md += f"### Reply by {author}{suffix}\n\n{reply_body}\n\n"

        return body_md, replies_md

    def _categorize(self, board: Dict) -> str:
        name = board.get('name', '').lower()
        if 'virtual desktop' in name or 'avd' in name:
            return 'AVD-TC'
        if 'fslogix' in name:
            return 'FSLogix-TC'
        if 'intune' in name:
            return 'Intune-TC'
        if 'windows 365' in name:
            return 'Windows365-TC'
        return 'General-TC'

    def _save_post(self, record: Dict):
        output_dir = Path(self.config_section['output_dir'])
        category = record['metadata']['category']
        pub = record['metadata']['published']
        timestamp = (
            pub.strftime('%Y%m%d')
            if isinstance(pub, datetime)
            else datetime.now().strftime('%Y%m%d')
        )
        filename = f"{timestamp}_{self._sanitize_filename(record['title'])}.md"
        output_path = output_dir / category / filename
        self._save_markdown(record['content'], record['metadata'], output_path)

    def process_content(self, raw_content: str, url: str) -> Dict:
        """Required by base class — not used (handled per-post inline)."""
        return {}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from logger import setup_logging
    setup_logging(verbose=True)

    scraper = TechCommunityScraper()
    scraper.scrape()
