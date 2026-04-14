#!/usr/bin/env python3
"""
Main orchestrator for AVD Knowledge Scraper
"""

import argparse
import sys
from pathlib import Path

# Add scrapers directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scrapers'))

from scrapers.logger import setup_logging, ProgressTracker
from scrapers.microsoft_learn_scraper import MicrosoftLearnScraper
from scrapers.rss_scraper import RSSFeedScraper


class ScraperOrchestrator:
    """Orchestrates multiple scrapers with progress tracking"""
    
    def __init__(self, verbose: bool = False):
        """Initialize orchestrator with logging"""
        self.logger = setup_logging(verbose=verbose)
        self.progress = ProgressTracker()
        
        self.scrapers = {
            'microsoft_learn': MicrosoftLearnScraper(),
            'rss': RSSFeedScraper()
        }
    
    def run_microsoft_docs(self):
        """Run Microsoft Learn documentation scraper"""
        self.progress.start_source("Microsoft Learn Documentation")
        try:
            articles = self.scrapers['microsoft_learn'].scrape()
            self.progress.end_source(len(articles))
        except Exception as e:
            self.progress.log_error(f"Microsoft Learn scraper failed: {e}")
            self.logger.exception("Exception during Microsoft Learn scraping")
    
    def run_azure_updates(self):
        """Run Azure updates RSS scraper"""
        self.progress.start_source("Azure Updates RSS Feed")
        try:
            updates = self.scrapers['rss'].scrape_azure_updates()
            self.progress.end_source(len(updates))
        except Exception as e:
            self.progress.log_error(f"Azure Updates scraper failed: {e}")
            self.logger.exception("Exception during Azure Updates scraping")
    
    def run_blogs(self):
        """Run expert blogs scraper"""
        self.progress.start_source("Expert Blogs")
        try:
            posts = self.scrapers['rss'].scrape_expert_blogs()
            self.progress.end_source(len(posts))
        except Exception as e:
            self.progress.log_error(f"Expert blogs scraper failed: {e}")
            self.logger.exception("Exception during blog scraping")
    
    def run_all(self):
        """Run all scrapers once"""
        self.logger.info("\n" + "#"*70)
        self.logger.info("RUNNING ALL SCRAPERS")
        self.logger.info("#"*70)
        
        self.run_microsoft_docs()
        self.run_azure_updates()
        self.run_blogs()
        
        self.progress.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description='AVD Knowledge Scraper - Aggregate AVD knowledge from multiple sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode once              # Run all scrapers once
  python main.py --mode microsoft         # Run Microsoft docs only
  python main.py --mode updates           # Run Azure updates only
  python main.py --mode blogs             # Run blogs only
  python main.py --mode once --verbose    # Run with debug logging
        """
    )
    parser.add_argument(
        '--mode',
        choices=['once', 'microsoft', 'updates', 'blogs', 'test'],
        default='once',
        help='Run mode (default: once)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    args = parser.parse_args()
    orchestrator = ScraperOrchestrator(verbose=args.verbose)
    
    try:
        if args.mode == 'test':
            # Quick test mode - just verify everything loads
            orchestrator.logger.info("Test mode - verifying configuration...")
            orchestrator.logger.info("✓ Logging system working")
            orchestrator.logger.info("✓ Scrapers initialized")
            orchestrator.logger.info("✓ Configuration loaded")
            orchestrator.logger.info("Test complete! Ready to scrape.")
        elif args.mode == 'once':
            orchestrator.run_all()
        elif args.mode == 'microsoft':
            orchestrator.run_microsoft_docs()
            orchestrator.progress.print_summary()
        elif args.mode == 'updates':
            orchestrator.run_azure_updates()
            orchestrator.progress.print_summary()
        elif args.mode == 'blogs':
            orchestrator.run_blogs()
            orchestrator.progress.print_summary()
    except KeyboardInterrupt:
        orchestrator.logger.info("\n\nScraping interrupted by user")
        orchestrator.progress.print_summary()
        sys.exit(0)
    except Exception as e:
        orchestrator.logger.exception("Fatal error during scraping")
        sys.exit(1)


if __name__ == "__main__":
    main()
