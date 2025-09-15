# quip-mcp
## Quick start

### Prerequisites
- python is installed
- uv is installed

### How to use
Configure the following json to your agentic coding IDE (e.g. Kiro, Claude Code, etc.) or mcp-supporting AI client (e.g. Amazon Q, Cherry Studio, etc.)
```json
{
  "mcpServers": {
    "quip-mcp": {
      "command": "uv",
      "args": [
      "run", 
      "--with", "markdownify",
      "--with", "mcp",
      "--with", "certifi",
      "--with", "beautifulsoup4",
      "--directory", "the path to quip-mcp（E.g.：D:/quip_mcp_server）",
      "python", "quip_mcp_server.py"
      ],
      "env": {
        "QUIP_ACCESS_TOKEN": "Input your quip access token（get one at https://quip.com/dev/token）",
        "QUIP_BASE_URL": "https://platform.quip.com"
      }
    }
  }
}
```