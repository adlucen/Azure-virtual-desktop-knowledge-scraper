# AVD Knowledge Scraper

> **Automated knowledge aggregation for Azure Virtual Desktop administrators**

A comprehensive web scraping pipeline that aggregates Azure Virtual Desktop documentation, expert blogs, and community discussions into LLM-ready markdown files with YAML metadata.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

##  Purpose

Built for IT guys managing AVD deployments who need instant access to:
- Official Microsoft documentation and updates
- Expert blog posts and best practices
- Community troubleshooting discussions
- Real-world deployment patterns

Perfect for powering AI assistants, RAG systems, or searchable knowledge bases.

## Features

- **Multi-Source Scraping**: Microsoft Learn, Azure Updates, expert blogs (Christiaan Brinkhoff, Tom Hickling, Marcel Meurer, Nerdio)
- **Clean Markdown Output**: HTML-to-Markdown with YAML frontmatter containing rich metadata
- **Auto-Categorization**: AVD-General, Deployment, Troubleshooting, FSLogix, Security, etc.
- **Real-Time Progress**: Colored console output showing exactly what's happening
- **Deduplication**: SHA-256 hashing prevents duplicate content
- **LLM-Ready**: Use directly with any LLM or convert to instruction tuning/RAG formats

## Quick Start

### Prerequisites
- Python 3.9+
- Internet connection

### Installation

**Windows:**
```cmd
setup.bat
venv\Scripts\activate
python main.py --mode once
```

**Linux/macOS:**
```bash
./setup.sh
source venv/bin/activate
python main.py --mode once
```

First scrape takes 2-4 hours and creates ~1,000-2,000 documents.

## Output Structure

```
output/
├── microsoft_docs/
│   ├── AVD-General/
│   ├── AVD-Deployment/
│   ├── AVD-Troubleshooting/
│   ├── FSLogix/
│   └── Intune/
├── azure_updates/
└── blogs/
    ├── Christiaan_Brinkhoff/
    ├── Tom_Hickling/
    └── Nerdio/
```

### Example Output

```markdown
---
source: Microsoft Learn
url: https://learn.microsoft.com/azure/virtual-desktop/overview
title: What is Azure Virtual Desktop?
scraped_at: 2026-04-14T10:30:00
category: AVD-General
tags:
  - azure
  - virtual-desktop
  - vdi
---

# What is Azure Virtual Desktop?

Azure Virtual Desktop is a comprehensive desktop and app virtualization service...
```

##  Usage

### Basic Commands

```bash
# Run all scrapers once
python main.py --mode once

# Run specific scraper
python main.py --mode microsoft   # Microsoft docs only
python main.py --mode updates     # Azure updates only
python main.py --mode blogs       # Expert blogs only

# Verbose logging (see debug details)
python main.py --mode once --verbose
```

### What You'll See

Real-time colored output showing progress:

```
======================================================================
Starting: Microsoft Learn Documentation
======================================================================
13:30:52 | INFO     |    Saved: output/microsoft_docs/AVD-General/...
13:30:53 | INFO     |    Saved: output/microsoft_docs/AVD-Deployment/...
----------------------------------------------------------------------
✓ Completed: Microsoft Learn Documentation
  Documents: 127
  Duration: 1847.3s
======================================================================

 SCRAPING SUMMARY
======================================================================
Total Runtime: 7234.5s (120.6 minutes)
Documents Saved: 1,247
Successful Requests: 1,398
Failed Requests: 12
Success Rate: 99.1%
======================================================================
```

### Logs

All activity is logged to `logs/scraper_TIMESTAMP.log` for troubleshooting.

## Configuration

Edit `config/scraper_config.yaml`:

```yaml
microsoft_learn:
  enabled: true
  update_frequency: "weekly"
  depth: 3  # How deep to crawl

azure_updates:
  enabled: true
  keywords:
    - "AVD"
    - "FSLogix"
    - "Intune"

rate_limiting:
  requests_per_minute: 30
```

##  LLM Integration

### Direct Use (Simplest)

```python
from pathlib import Path
import yaml

def load_avd_knowledge(category="AVD-General"):
    docs = []
    for md_file in Path('output').rglob('*.md'):
        with open(md_file, encoding='utf-8') as f:
            content = f.read()
            if '---' in content:
                parts = content.split('---', 2)
                metadata = yaml.safe_load(parts[1])
                if category in metadata.get('category', ''):
                    docs.append(parts[2])  # Just the content
    return '\n\n'.join(docs[:5])

# Use in your LLM prompt
context = load_avd_knowledge("AVD-Troubleshooting")
prompt = f"Context:\n{context}\n\nQuestion: How do I fix session host connectivity?"
```

### RAG with Vector DB

```python
from langchain.document_loaders import DirectoryLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

# Load documents
loader = DirectoryLoader('output/', glob="**/*.md")
docs = loader.load()

# Create embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

# Build vector store
vectorstore = Chroma.from_documents(docs, embeddings)

# Query
results = vectorstore.similarity_search(
    "How do I troubleshoot AVD connectivity?", k=3
)
```

##  Expected Results

- **Initial scrape**: ~1,000-2,000 documents (5-10GB)
- **Monthly growth**: ~200-500 new documents
- **After 6 months**: ~4,000-6,000 documents (15-25GB)

##  Project Structure

```
avd-knowledge-scraper/
├── config/
│   └── scraper_config.yaml      # Main configuration
├── scrapers/
│   ├── base_scraper.py          # Base class
│   ├── logger.py                # Logging & progress tracking
│   ├── microsoft_learn_scraper.py
│   └── rss_scraper.py
├── output/                      # Scraped content (git-ignored)
├── logs/                        # Log files (git-ignored)
├── main.py                      # Main orchestrator
├── requirements.txt
├── setup.bat                    # Windows setup
├── setup.sh                     # Linux/macOS setup
└── README.md
```

##  Optional: Reddit Scraping

For Reddit discussions, get free API credentials:

1. Visit https://www.reddit.com/prefs/apps
2. Create a "script" application
3. Set environment variables:

**Windows:**
```cmd
set REDDIT_CLIENT_ID=your_id
set REDDIT_CLIENT_SECRET=your_secret
```

**Linux/macOS:**
```bash
export REDDIT_CLIENT_ID=your_id
export REDDIT_CLIENT_SECRET=your_secret
```

Then enable in `config/scraper_config.yaml`:
```yaml
reddit:
  enabled: true
  subreddits:
    - "AZURE"
    - "sysadmin"
```

##  Contributing

Contributions welcome! Ideas:
- Additional scrapers (Stack Overflow, GitHub, Tech Community)
- Parallel scraping for performance
- Image OCR for architecture diagrams
- Enhanced categorization logic

##  License

MIT License - See LICENSE file

##  Disclaimer

For personal/educational use only. Users must:
- Respect source website terms of service
- Honor robots.txt
- Not redistribute scraped content

##  Acknowledgments

Built for AVD administrators by AVD administrators. Thanks to:
- Microsoft Learn documentation team
- Expert bloggers: Christiaan Brinkhoff, Tom Hickling, Marcel Meurer, Nerdio
- Open source: BeautifulSoup, requests, feedparser

---
