# Quick Reference

## Installation

```bash
# Windows
setup.bat

# Linux/macOS
./setup.sh
```

## Activation

```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

## Running

```bash
# All scrapers
python main.py --mode once

# Specific scrapers
python main.py --mode microsoft
python main.py --mode updates
python main.py --mode blogs

# With verbose logging
python main.py --mode once --verbose
```

## Output

- **Scraped files**: `output/` directory
- **Logs**: `logs/scraper_TIMESTAMP.log`
- **Categories**: AVD-General, AVD-Deployment, AVD-Troubleshooting, FSLogix, etc.

## Configuration

Edit `config/scraper_config.yaml` to:
- Enable/disable sources
- Change update frequency
- Adjust rate limiting
- Add keywords

## Common Issues

**"Python not found"**
- Install Python 3.9+ from python.org
- Check "Add to PATH" during installation

**"Module not found"**
- Activate virtual environment first
- Run: `pip install -r requirements.txt`

**No output files**
- Check `logs/` for errors
- Verify network connection
- Ensure sources are `enabled: true` in config

## Logs Location

```
logs/scraper_YYYYMMDD_HHMMSS.log
```

View latest:
```bash
# Linux/macOS
tail -f logs/scraper_*.log

# Windows
type logs\scraper_*.log
```

## Stop Scraping

Press `Ctrl+C` - Progress will be saved and summary shown.
