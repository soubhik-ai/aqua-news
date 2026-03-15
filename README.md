# aqua-news

Multi-source news aggregator that clusters stories from 28 RSS feeds, detects editorial bias, and presents summarized clusters through a mobile-first Streamlit dashboard.

## Architecture

```
RSS Feeds (28 sources)
       |
       v
 ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
 │ Acquisition  │────>│  Processing  │────>│   Analysis   │
 │  fetch +     │     │  TF-IDF +    │     │  lead pick + │
 │  clean text  │     │  DBSCAN      │     │  LexRank     │
 └─────────────┘     └──────────────┘     └──────────────┘
       |                                         |
       v                                         v
  cache/articles_                          GCS (latest.json)
  YYYY-MM-DD.json                                |
                                                 v
                                          ┌──────────────┐
                                          │  Streamlit   │
                                          │  Dashboard   │
                                          └──────────────┘
```

### Pipeline stages

1. **Acquisition** (`src/acquisition.py`) — Parses 28 RSS feeds in parallel (30 threads), extracts full article text via newspaper3k, deduplicates by URL, strips per-domain boilerplate (ET, News18), and rejects garbage/short articles (<300 chars).

2. **Processing** (`src/processing.py`) — Builds a TF-IDF matrix from article texts, computes pairwise cosine similarity, and clusters articles using DBSCAN (`eps = 1 - similarity_threshold`). Articles with >55% textual overlap are grouped together. Singletons are discarded.

3. **Analysis** (`src/analysis.py`) — For each cluster: picks the least-biased article as the lead (lowest `|bias_score|`), generates a 3-sentence extractive summary using LexRank, and computes bias distribution metrics (mean, std, range).

4. **Fetcher** (`src/fetcher.py`) — Orchestrates the pipeline. Caches fetched articles locally by date (`cache/articles_YYYY-MM-DD.json`) so feeds are scraped only once per day. Uploads final cluster JSON to GCS.

5. **Dashboard** (`src/app.py`) — Streamlit app that loads cached results from GCS (1hr TTL). Renders cluster cards with bias spectrum bar, expandable source links, share buttons, and region/category filters.

### Bias scoring

Each feed source has a manually assigned `bias_score` from -10 (far left) to +10 (far right). Current feeds range from -5 (The Guardian) to +4 (OpIndia). The dashboard visualizes these on a spectrum bar per cluster and selects the most centrist article as the lead.

## Project structure

```
src/
  acquisition.py    # RSS ingestion, text extraction, boilerplate filtering
  processing.py     # TF-IDF vectorization, DBSCAN clustering
  analysis.py       # Lead selection, LexRank summarization, bias metrics
  fetcher.py        # Daily pipeline orchestrator + GCS upload + local cache
  app.py            # Streamlit dashboard
config/
  feeds.json        # Feed URLs, bias scores, and pipeline settings
tests/
  test_acquisition.py
  test_processing.py
  test_analysis.py
  test_app_html.py
cache/              # Auto-created, holds daily article caches (gitignored)
Dockerfile          # Streamlit app container
Dockerfile.fetcher  # Fetcher pipeline container
docker-compose.yml  # Both services
```

## Setup

### Prerequisites

- Python 3.11+
- Google Cloud credentials (for GCS access)

### Local development

```bash
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Run the fetcher (scrapes feeds, clusters, uploads to GCS)
python src/fetcher.py

# Run the dashboard
streamlit run src/app.py --server.port=8501
```

### Docker

```bash
# Run the dashboard
docker compose up news-aggregator

# Run the fetcher once
docker compose run --rm fetcher
```

### Running tests

```bash
python -m pytest tests/ -v
```

## Configuration

All tunable parameters live in `config/feeds.json` under `settings`:

| Setting | Default | Description |
|---------|---------|-------------|
| `similarity_threshold` | 0.55 | Minimum cosine similarity to cluster articles together |
| `summary_sentences` | 3 | Number of sentences in each cluster summary |
| `min_document_frequency` | 2 | Minimum document frequency for TF-IDF vocabulary |
| `max_articles_per_feed` | 20 | Max articles to fetch per RSS feed |

### Adding or replacing feeds

Add an entry to the `feeds` array in `config/feeds.json`:

```json
{
  "url": "https://example.com/rss",
  "domain": "example.com",
  "region": "GLOBAL",
  "category": "general",
  "bias_score": 0
}
```

- **region**: `IN`, `HK`, or `GLOBAL`
- **category**: `general`, `finance`, `geopolitics`, `science`, `technology`, `culture`
- **bias_score**: -10 (far left) to +10 (far right)

If a source has site-specific boilerplate that newspaper3k doesn't strip, add a pattern to `_BOILERPLATE_STRIPS` in `src/acquisition.py`.

## Current feed sources (28)

| Region | Sources |
|--------|---------|
| **IN** (12) | NDTV, Times of India, Indian Express, News18, Economic Times, Livemint, NDTV Profit, Moneycontrol, OpIndia, IE Culture, News18 Culture |
| **HK** (4) | SCMP, HKFP, CNA, Asia Sentinel |
| **GLOBAL** (13) | BBC, Al Jazeera, NPR, DW, France24, The Guardian, Nature, Ars Technica, TechCrunch, The Verge, Wired, Yahoo Finance, Foreign Policy, Rest of World |
