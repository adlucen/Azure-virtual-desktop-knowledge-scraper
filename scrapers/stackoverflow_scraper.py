#!/usr/bin/env python3
"""
Scraper for Stack Overflow Q&A threads via Stack Exchange API

Uses the public Stack Exchange API (no auth required for basic volume).
Optionally uses an API key for higher quotas — set in config under
`stack_overflow.api_key` or leave empty.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import html2text

from base_scraper import BaseScraper


class StackOverflowScraper(BaseScraper):
    """Scraper for Stack Overflow via Stack Exchange API."""

    API_BASE = "https://api.stackexchange.com/2.3"
    SITE = "stackoverflow"

    def __init__(self, config_path: str = "config/scraper_config.yaml"):
        super().__init__(config_path)
        self.config_section = self.config['scraping_targets']['stack_overflow']
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.body_width = 0
        self.logger = logging.getLogger(__name__)
        self.api_key = self.config_section.get('api_key', '') or None

    def scrape(self) -> List[Dict]:
        """Scrape top-voted questions for each configured tag."""
        if not self.config_section.get('enabled', False):
            self.logger.info("Stack Overflow scraping disabled")
            return []

        self.logger.info("Starting Stack Overflow scrape")
        all_qa = []

        for tag in self.config_section['tags']:
            self.logger.info(f"Fetching tag: {tag}")
            try:
                qa_pairs = self._scrape_tag(tag)
                all_qa.extend(qa_pairs)
            except Exception as e:
                self.logger.error(f"Error on tag {tag}: {e}")

        self.logger.info(f"Total Q&A pairs scraped: {len(all_qa)}")
        return all_qa

    def _scrape_tag(self, tag: str) -> List[Dict]:
        """Fetch questions for a single tag, then enrich with answers."""
        questions = self._fetch_questions(tag)
        qa_pairs = []

        for q in questions:
            try:
                answers = self._fetch_answers(q['question_id'])
                qa = self._build_qa_record(q, answers, tag)
                qa_pairs.append(qa)
                self._save_qa(qa)
            except Exception as e:
                self.logger.error(f"Failed to enrich question {q['question_id']}: {e}")

        return qa_pairs

    def _fetch_questions(self, tag: str) -> List[Dict]:
        """Fetch top questions for a tag, respecting score threshold."""
        questions: List[Dict] = []
        page = 1
        pagesize = 100
        max_questions = self.config_section.get('questions_per_tag', 50)
        min_score = self.config_section.get('min_score', 0)

        while len(questions) < max_questions:
            params = {
                'order': 'desc',
                'sort': 'votes',
                'tagged': tag,
                'site': self.SITE,
                'filter': 'withbody',
                'pagesize': pagesize,
                'page': page,
            }
            if self.api_key:
                params['key'] = self.api_key

            self._rate_limit()
            resp = self.session.get(f"{self.API_BASE}/questions", params=params, timeout=30)

            if resp.status_code in (429, 502):
                backoff = int(resp.headers.get('Retry-After', 10))
                self.logger.warning(f"Throttled ({resp.status_code}), sleeping {backoff}s")
                time.sleep(backoff)
                continue

            resp.raise_for_status()
            data = resp.json()

            if data.get('backoff'):
                self.logger.info(f"API backoff: {data['backoff']}s")
                time.sleep(data['backoff'])

            for item in data.get('items', []):
                if item.get('score', 0) < min_score:
                    continue
                questions.append(item)
                if len(questions) >= max_questions:
                    break

            if not data.get('has_more'):
                break
            page += 1

        return questions

    def _fetch_answers(self, question_id: int) -> List[Dict]:
        """Fetch top answers for a single question."""
        include_count = self.config_section.get('include_answers', 3)
        params = {
            'order': 'desc',
            'sort': 'votes',
            'site': self.SITE,
            'filter': 'withbody',
            'pagesize': include_count,
        }
        if self.api_key:
            params['key'] = self.api_key

        self._rate_limit()
        resp = self.session.get(
            f"{self.API_BASE}/questions/{question_id}/answers",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get('backoff'):
            time.sleep(data['backoff'])

        return data.get('items', [])

    def _build_qa_record(self, question: Dict, answers: List[Dict], tag: str) -> Dict:
        """Build the structured record for a Q&A pair."""
        q_body_md = self._html_to_md(question.get('body', ''))
        asked = datetime.fromtimestamp(question['creation_date'])

        content_parts = [
            f"# {question['title']}",
            "",
            "## Question",
            "",
            q_body_md,
            "",
            f"**Asked:** {asked.isoformat()}  ",
            f"**Score:** {question.get('score', 0)}  ",
            f"**Views:** {question.get('view_count', 0)}",
            "",
        ]

        accepted_id = question.get('accepted_answer_id')

        # Accepted answer first, then by score
        sorted_answers = sorted(
            answers,
            key=lambda a: (a.get('answer_id') != accepted_id, -a.get('score', 0)),
        )

        for i, ans in enumerate(sorted_answers):
            is_accepted = ans.get('answer_id') == accepted_id
            heading = "## Accepted Answer" if is_accepted else f"## Answer {i + 1}"
            ans_body = self._html_to_md(ans.get('body', ''))
            ans_date = datetime.fromtimestamp(ans.get('creation_date', 0))

            content_parts.extend([
                heading,
                "",
                ans_body,
                "",
                f"**Score:** {ans.get('score', 0)}, "
                f"**Answered:** {ans_date.isoformat()}",
                "",
            ])

        content = "\n".join(content_parts)

        metadata = {
            'source': 'Stack Overflow',
            'url': question.get('link', ''),
            'title': question['title'],
            'question_id': question['question_id'],
            'question_score': question.get('score', 0),
            'accepted_answer_id': accepted_id or '',
            'tags': question.get('tags', []),
            'asked_date': asked,
            'scraped_at': datetime.now(),
            'category': self._categorize(tag),
            'primary_tag': tag,
        }

        return {
            'title': question['title'],
            'content': content,
            'metadata': metadata,
            'url': question.get('link', ''),
            'content_hash': self._generate_content_hash(content),
        }

    def _html_to_md(self, html: str) -> str:
        """Convert Stack Overflow's HTML body to markdown."""
        if not html:
            return ""
        return self.html_converter.handle(html).strip()

    def _categorize(self, tag: str) -> str:
        """Rough category from primary tag."""
        t = tag.lower()
        if 'virtual-desktop' in t or 'avd' in t:
            return 'AVD-SO'
        if 'fslogix' in t:
            return 'FSLogix-SO'
        if 'intune' in t:
            return 'Intune-SO'
        if 'entra' in t or 'active-directory' in t:
            return 'Entra-SO'
        if 'graph' in t:
            return 'Graph-SO'
        return 'General-SO'

    def _save_qa(self, qa: Dict):
        """Save Q&A to markdown file."""
        output_dir = Path(self.config_section['output_dir'])
        category = qa['metadata']['category']
        timestamp = datetime.now().strftime('%Y%m%d')
        qid = qa['metadata']['question_id']
        filename = f"{timestamp}_q{qid}_{self._sanitize_filename(qa['title'])}.md"
        output_path = output_dir / category / filename
        self._save_markdown(qa['content'], qa['metadata'], output_path)

    def process_content(self, raw_content: str, url: str) -> Dict:
        """Required by base class — not used (we use API, not HTML scraping)."""
        return {}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from logger import setup_logging
    setup_logging(verbose=True)

    scraper = StackOverflowScraper()
    scraper.scrape()
