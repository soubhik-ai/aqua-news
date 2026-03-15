# Contributing to Aqua News

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/soubhik-ai/aqua-news.git
cd aqua-news

# Backend
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Frontend
cd frontend && npm install

# Copy example config
cp config/feeds.example.json config/feeds.json
```

## Running Tests

```bash
python -m pytest tests/ -v
cd frontend && npm run build
```

All PRs must pass the existing test suite. Add tests for new functionality.

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Make your changes in focused, atomic commits
3. Add or update tests as needed
4. Run the full test suite and ensure it passes
5. Update documentation if you changed behavior
6. Open a PR with a clear description of what and why

## What to Work On

- Check [open issues](https://github.com/soubhik-ai/aqua-news/issues) for things tagged `good first issue`
- See the [Roadmap](README.md#roadmap) for bigger features
- Bug fixes and test improvements are always welcome

## Code Style

- **Python**: Follow existing patterns. Type hints on function signatures. No unnecessary comments.
- **TypeScript/React**: Follow existing Tailwind + component patterns. Functional components only.
- Keep changes minimal and focused. Don't refactor unrelated code in the same PR.

## Adding a New Feed Source

If you want to add support for a new news source:

1. Test that the RSS feed URL works: `curl -s <url> | head -20`
2. Test that newspaper3k can extract articles from it
3. If the source has boilerplate that newspaper3k doesn't strip, add a pattern to `_BOILERPLATE_STRIPS` in `src/acquisition.py`
4. Add it to your local `config/feeds.json` and test the full pipeline

## Reporting Bugs

Open an issue with:
- What you expected vs what happened
- Steps to reproduce
- Python/Node version and OS

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be respectful.
