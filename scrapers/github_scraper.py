#!/usr/bin/env python3
"""
Scraper for GitHub issues in AVD / Azure / FSLogix / Intune repos

Targets closed issues with discussion threads — the highest-signal source
for real-world troubleshooting and edge cases. Uses the GitHub REST API.

Auth: prefers `github.api_key` from config, falls back to GITHUB_TOKEN env
var, falls back to unauthenticated (60 req/hour limit).
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import html2text

from base_scraper import BaseScraper


class GitHubScraper(BaseScraper):
    """Scraper for closed issues in Azure/AVD-related GitHub repos."""

    API_BASE = "https://api.github.com"

    def __init__(self, config_path: str = "config/scraper_config.yaml"):
        super().__init__(config_path)
        self.config_section = self.config['scraping_targets']['github']
        self.html_converter = html2text.HTML2Text()
        self.html_converter.body_width = 0
        self.logger = logging.getLogger(__name__)

        token = self.config_section.get('api_key') or os.environ.get('GITHUB_TOKEN', '')
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
            self.logger.info("GitHub API authenticated (5000 req/hour)")
        else:
            self.logger.warning("GitHub API unauthenticated — 60 req/hour limit")

        self.session.headers.update({
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        })

    def scrape(self) -> List[Dict]:
        """Scrape issues from each configured repo."""
        if not self.config_section.get('enabled', False):
            self.logger.info("GitHub scraping disabled")
            return []

        all_issues = []
        for repo in self.config_section['repos']:
            self.logger.info(f"Fetching issues from {repo}")
            try:
                issues = self._scrape_repo(repo)
                all_issues.extend(issues)
            except Exception as e:
                self.logger.error(f"Failed repo {repo}: {e}")

        self.logger.info(f"Total issues scraped: {len(all_issues)}")
        return all_issues

    def _scrape_repo(self, repo: str) -> List[Dict]:
        """Fetch relevant issues for a single repo."""
        state = self.config_section.get('state', 'closed')
        labels = ','.join(self.config_section.get('labels_filter', []))
        per_page = 100
        max_issues = self.config_section.get('issues_per_repo', 100)
        min_comments = self.config_section.get('min_comments', 0)

        issues: List[Dict] = []
        page = 1

        while len(issues) < max_issues:
            params = {
                'state': state,
                'per_page': per_page,
                'page': page,
                'sort': 'comments',
                'direction': 'desc',
            }
            if labels:
                params['labels'] = labels

            self._rate_limit()
            resp = self.session.get(
                f"{self.API_BASE}/repos/{repo}/issues",
                params=params,
                timeout=30,
            )

            if resp.status_code == 403 and 'rate limit' in resp.text.lower():
                reset = int(resp.headers.get('X-RateLimit-Reset', time.time() + 60))
                wait = max(0, reset - int(time.time()))
                self.logger.warning(f"GitHub rate limited, sleeping {wait}s")
                time.sleep(wait + 1)
                continue

            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break

            for item in batch:
                # Skip PRs (GH API returns PRs as issues with a pull_request key)
                if item.get('pull_request'):
                    continue
                if item.get('comments', 0) < min_comments:
                    continue

                try:
                    record = self._build_issue_record(repo, item)
                    issues.append(record)
                    self._save_issue(record)
                except Exception as e:
                    self.logger.error(f"Issue {item.get('number')} failed: {e}")

                if len(issues) >= max_issues:
                    break

            if len(batch) < per_page:
                break
            page += 1

        return issues

    def _build_issue_record(self, repo: str, issue: Dict) -> Dict:
        """Build markdown record for an issue + its comments."""
        number = issue['number']
        comments = self._fetch_comments(repo, number)

        body_md = (issue.get('body') or '').strip()
        created = self._parse_iso(issue['created_at'])
        closed = self._parse_iso(issue.get('closed_at')) if issue.get('closed_at') else None

        content_parts = [
            f"# {issue['title']}",
            "",
            f"**Repo:** {repo}  ",
            f"**Issue:** #{number}  ",
            f"**State:** {issue['state']}  ",
            f"**Reporter:** {issue.get('user', {}).get('login', 'unknown')}  ",
            f"**Created:** {created.isoformat() if created else 'unknown'}  ",
            f"**Closed:** {closed.isoformat() if closed else 'open'}",
            "",
            "## Issue body",
            "",
            body_md or "_(no body)_",
            "",
        ]

        if comments:
            content_parts.extend(["## Discussion", ""])
            for c in comments:
                c_body = (c.get('body') or '').strip()
                c_user = c.get('user', {}).get('login', 'unknown')
                c_date = self._parse_iso(c.get('created_at', ''))
                content_parts.extend([
                    f"### Comment by {c_user} "
                    f"({c_date.isoformat() if c_date else 'unknown'})",
                    "",
                    c_body,
                    "",
                ])

        content = "\n".join(content_parts)
        labels_list = [l.get('name', '') for l in issue.get('labels', [])]

        metadata = {
            'source': 'GitHub Issues',
            'url': issue.get('html_url', ''),
            'title': issue['title'],
            'repo': repo,
            'issue_number': number,
            'issue_state': issue['state'],
            'labels': labels_list,
            'reporter': issue.get('user', {}).get('login', ''),
            'comments_count': issue.get('comments', 0),
            'created_at': created or datetime.now(),
            'closed_at': closed or '',
            'scraped_at': datetime.now(),
            'category': self._categorize(repo, labels_list),
        }

        return {
            'title': issue['title'],
            'content': content,
            'metadata': metadata,
            'url': issue.get('html_url', ''),
            'content_hash': self._generate_content_hash(content),
        }

    def _fetch_comments(self, repo: str, issue_number: int) -> List[Dict]:
        """Fetch comments for an issue (capped by config)."""
        max_comments = self.config_section.get('max_comments_per_issue', 20)
        self._rate_limit()
        resp = self.session.get(
            f"{self.API_BASE}/repos/{repo}/issues/{issue_number}/comments",
            params={'per_page': max_comments},
            timeout=30,
        )
        if resp.status_code >= 400:
            self.logger.warning(
                f"Failed to fetch comments for {repo}#{issue_number}: {resp.status_code}"
            )
            return []
        return resp.json()

    def _parse_iso(self, s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace('Z', '+00:00'))
        except ValueError:
            return None

    def _categorize(self, repo: str, labels: List[str]) -> str:
        """Category from repo + labels."""
        repo_lower = repo.lower()
        label_text = ' '.join(labels).lower()
        if 'fslogix' in repo_lower or 'fslogix' in label_text:
            return 'FSLogix-GH'
        if 'rds-templates' in repo_lower or 'virtual-desktop' in label_text or 'avd' in label_text:
            return 'AVD-GH'
        if 'intune' in repo_lower or 'intune' in label_text:
            return 'Intune-GH'
        if 'azure-powershell' in repo_lower:
            return 'AzurePowerShell-GH'
        if 'azure-docs' in repo_lower:
            return 'AzureDocs-GH'
        return 'General-GH'

    def _save_issue(self, record: Dict):
        """Save issue markdown."""
        output_dir = Path(self.config_section['output_dir'])
        category = record['metadata']['category']
        number = record['metadata']['issue_number']
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{timestamp}_i{number}_{self._sanitize_filename(record['title'])}.md"
        output_path = output_dir / category / filename
        self._save_markdown(record['content'], record['metadata'], output_path)

    def process_content(self, raw_content: str, url: str) -> Dict:
        """Required by base class — not used (we use API, not HTML scraping)."""
        return {}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from logger import setup_logging
    setup_logging(verbose=True)

    scraper = GitHubScraper()
    scraper.scrape()
