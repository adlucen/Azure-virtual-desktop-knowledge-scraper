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
- **Real-Time Progress**: Console output showing exactly what's happening
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

Console output showing progress:

```
17:08:13 | INFO     | Total articles scraped: 52
17:08:13 | INFO     | ----------------------------------------------------------------------
17:08:13 | INFO     |   Completed: Microsoft Learn Documentation
17:08:13 | INFO     |   Documents: 52
17:08:13 | INFO     |   Duration: 138.4s
17:08:13 | INFO     | ======================================================================
17:08:13 | INFO     |
17:08:13 | INFO     | ======================================================================
17:08:13 | INFO     |  Starting: Azure Updates RSS Feed
17:08:13 | INFO     | ======================================================================
17:08:13 | INFO     | Scraping Azure Updates RSS feed
17:08:14 | INFO     | Azure updates scraped: 0
17:08:14 | INFO     | ----------------------------------------------------------------------
17:08:14 | INFO     |   Completed: Azure Updates RSS Feed
17:08:14 | INFO     |   Documents: 0
17:08:14 | INFO     |   Duration: 0.7s
17:08:14 | INFO     | ======================================================================
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

Contributions are welcomed and appreciated.

##  License

MIT License - See LICENSE file

##  Disclaimer

For personal/educational use only. In robots we trust.

##  Acknowledgments

Built for AVD administrators by an AVD administrator.

---
