# Changelog

All notable changes to AVD Knowledge Scraper will be documented in this file.

## [1.0.0] - 2026-04-14

### Added
- Initial release
- Microsoft Learn documentation scraper
- Azure Updates RSS feed scraper
- Expert blogs RSS scraper (Christiaan Brinkhoff, Tom Hickling, Marcel Meurer, Nerdio)
- Real-time progress tracking with colored console output
- Comprehensive logging to file
- YAML-based configuration system
- Auto-categorization (AVD-General, Deployment, Troubleshooting, FSLogix, etc.)
- Markdown output with YAML frontmatter
- Content deduplication via SHA-256 hashing
- Rate limiting and robots.txt respect
- Windows and Linux setup scripts
- Detailed README and documentation

### Planned for Future Releases
- Reddit scraper (requires API credentials)
- GitHub scraper for repositories and issues
- Stack Overflow scraper
- Parallel/async scraping for performance
- Convert to LLM training formats (JSONL, Parquet)
- Scheduled continuous scraping mode
- Image OCR for architecture diagrams
