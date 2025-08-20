# Claude Code Configuration

This guide shows how to configure the MCP PDF Converter with Claude Code CLI.

## Prerequisites

1. Install Claude Code CLI (if not already installed)
2. Build the MCP server:
   ```bash
   cd /path/to/mcp-pdf-markdown
   make setup
   make build
   ```

## Configuration

### Method 1: Using Claude Code CLI (Recommended)

Navigate to your MCP server directory and add it:

```bash
cd /path/to/mcp-pdf-markdown
claude mcp add pdf-converter -- ./bin/mcp-pdf-server
```

**⚠️ Important**: Replace `/path/to/mcp-pdf-markdown` with the actual path where you cloned this repository.

### With Environment Variables

```bash
claude mcp add pdf-converter --env OUTPUT_DIR=./docs -- ./bin/mcp-pdf-server
```

### Method 2: Manual Configuration

Create or edit your MCP configuration file with:

```json
{
  "mcpServers": {
    "pdf-converter": {
      "command": "/absolute/path/to/mcp-pdf-markdown/bin/mcp-pdf-server",
      "env": {
        "OUTPUT_DIR": "./docs"
      }
    }
  }
}
```

## Management Commands

```bash
# List configured MCP servers
claude mcp list

# Get server details
claude mcp get pdf-converter

# Remove the server
claude mcp remove pdf-converter
```

## Configuration Scopes

- **Local**: Private to current project
- **Project**: Shared via `.mcp.json` file
- **User**: Available across all projects

## Usage

Once configured, you can use these prompts in Claude Code:

```
Convert the PDF at ./documents/manual.pdf to markdown
```

```
Analyze the structure of ./pdfs/research-paper.pdf
```

```
Convert ./reports/quarterly.pdf and save to ./analysis/
```

## How It Works

- Claude Code automatically starts the `mcp-pdf-server` binary when needed
- Files are saved relative to your current working directory (defaults to `./docs`)
- You can override the output directory in prompts: *"Convert PDF to ./my-project/docs/"*
- Multiple projects can use the same MCP server with different output locations

## Troubleshooting

**Server not found?**
- Verify the binary path: `ls -la /path/to/mcp-pdf-markdown/bin/mcp-pdf-server`
- Use absolute paths in configuration

**Permission errors?**
- Make binary executable: `chmod +x ./bin/mcp-pdf-server`
- Check file permissions in the repository directory

**Python dependency errors?**
- Run `make setup` in the server directory
- Verify virtual environment: `./venv/bin/python -c "import pypdf"`

For more details, see the [Claude Code MCP documentation](https://docs.anthropic.com/en/docs/claude-code/mcp).