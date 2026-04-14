# Contributing to AVD Knowledge Scraper

Thank you for considering contributing! This project welcomes improvements from the AVD community.

## How to Contribute

### Reporting Bugs

Open an issue with:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Log file excerpt (from `logs/`)
- Python version and OS

### Suggesting Features

Open an issue describing:
- The feature and its use case
- Why it would benefit AVD administrators
- Potential implementation approach (optional)

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push and create a pull request

## Development Setup

```bash
git clone https://github.com/YourUsername/avd-knowledge-scraper.git
cd avd-knowledge-scraper
./setup.sh  # or setup.bat on Windows
source venv/bin/activate
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to classes and methods
- Keep functions focused and small

## Testing Your Changes

```bash
# Test individual scrapers
python -m scrapers.microsoft_learn_scraper
python -m scrapers.rss_scraper

# Test full run
python main.py --mode once --verbose
```

Check:
- No errors in console output
- Files created in `output/`
- Log file contains expected entries
- YAML frontmatter is valid

## Adding a New Scraper

1. Create new file in `scrapers/` (e.g., `stackoverflow_scraper.py`)
2. Inherit from `BaseScraper`
3. Implement `scrape()` and `process_content()` methods
4. Add configuration to `config/scraper_config.yaml`
5. Import and register in `main.py`
6. Update README with new source
7. Add tests

Example structure:

```python
from base_scraper import BaseScraper

class NewSourceScraper(BaseScraper):
    def __init__(self, config_path="config/scraper_config.yaml"):
        super().__init__(config_path)
        self.config_section = self.config['scraping_targets']['new_source']
        
    def scrape(self) -> List[Dict]:
        # Your scraping logic
        pass
        
    def process_content(self, raw_content: str, url: str) -> Dict:
        # Content processing
        pass
```

## Priority Areas for Contribution

- **Additional scrapers**: Stack Overflow, GitHub, Microsoft Tech Community
- **Performance**: Async/parallel scraping
- **Processing**: Convert to JSONL/Parquet for training
- **Features**: Scheduled mode, image OCR, video transcription
- **Documentation**: More examples, troubleshooting guides
- **Tests**: Unit and integration tests

## Questions?

Open a discussion or issue - we're happy to help!
