# Aqua News MCP Server

An [MCP](https://modelcontextprotocol.io) server that lets AI assistants query your news data.

## Tools

| Tool | Description |
|------|-------------|
| `get_stories` | Get today's story clusters, filter by category/region/min sources |
| `search_stories` | Search stories by keyword across titles, summaries, and sources |
| `get_bias_analysis` | Find the most polarizing, consensus, left-leaning, or right-leaning stories |

## Setup

### 1. Run the fetcher to get data

```bash
# from the repo root
pip install -r requirements.txt
cp config/feeds.example.json config/feeds.json
python src/fetcher.py
```

This creates `cache/latest.json` which the MCP server reads automatically.

### 2. Install MCP dependencies

```bash
pip install -r mcp/requirements.txt
```

### 3. Connect to your AI assistant

**Claude Desktop** - add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aqua-news": {
      "command": "python",
      "args": ["/absolute/path/to/aqua-news/mcp/server.py"]
    }
  }
}
```

**Claude Code:**

```bash
claude mcp add aqua-news python /path/to/aqua-news/mcp/server.py
```

### Data sources (in priority order)

1. `AQUA_NEWS_URL` env var - any HTTP URL serving the cluster JSON
2. `GCS_BUCKET` env var - builds a GCS public URL
3. `cache/latest.json` - local file from running the fetcher

For local use you don't need any env vars. Just run the fetcher once and the MCP server picks it up.

## Example queries

Once connected, you can ask things like:

- "What are today's top stories?"
- "Search for stories about Iran"
- "Which stories have the widest bias spread?"
- "Show me finance stories from India"
