# Aqua News MCP Server

An [MCP](https://modelcontextprotocol.io) server that exposes Aqua News data to AI assistants like Claude.

## Tools

| Tool | Description |
|------|-------------|
| `get_stories` | Get today's story clusters, filter by category/region/min sources |
| `search_stories` | Search stories by keyword across titles, summaries, and sources |
| `get_bias_analysis` | Find the most polarizing, consensus, left-leaning, or right-leaning stories |

## Setup

### With Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aqua-news": {
      "command": "python",
      "args": ["path/to/aqua-news/mcp/server.py"],
      "env": {
        "AQUA_NEWS_URL": "https://storage.googleapis.com/YOUR_BUCKET/latest.json"
      }
    }
  }
}
```

### With Claude Code

```bash
claude mcp add aqua-news python /path/to/aqua-news/mcp/server.py
```

### Install dependencies

```bash
pip install -r mcp/requirements.txt
```

## Example Queries

Once connected, you can ask your AI assistant:

- "What are today's top stories?"
- "Search for stories about Iran"
- "Which stories have the widest bias spread?"
- "Show me finance stories from India"
- "What are the most left-leaning stories today?"
