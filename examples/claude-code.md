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

First, get the full absolute path to your binary:

```bash
cd /path/to/mcp-pdf-markdown
pwd  # This shows your full path, e.g., /Users/username/Documents/mcp-pdf-markdown
```

Then add the MCP server using the full absolute path:

```bash
claude mcp add pdf-markdown -- /Users/username/Documents/mcp-pdf-markdown/bin/mcp-pdf-markdown
```

**⚠️ Important**: You **must use the full absolute path** to the binary. Relative paths like `./bin/mcp-pdf-markdown` will fail because Claude Code runs from a different directory.

### With Environment Variables

```bash
claude mcp add pdf-markdown --env OUTPUT_DIR=./docs -- /path/to/mcp-pdf-markdown/bin/mcp-pdf-markdown
```

### Method 2: Manual Configuration

Create or edit your MCP configuration file with:

```json
{
  "mcpServers": {
    "pdf-markdown": {
      "command": "/path/to/mcp-pdf-markdown/bin/mcp-pdf-markdown",
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
claude mcp get pdf-markdown

# Remove the server
claude mcp remove pdf-markdown
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

- Claude Code automatically starts the `mcp-pdf-markdown` binary when needed
- Files are saved relative to your current working directory (defaults to `./docs`)
- You can override the output directory in prompts: *"Convert PDF to ./my-project/docs/"*
- Multiple projects can use the same MCP server with different output locations

## Troubleshooting

**Server not found?**
- Verify the binary exists: `ls -la /path/to/mcp-pdf-markdown/bin/mcp-pdf-markdown`
- **Always use absolute paths** - relative paths like `./bin/mcp-pdf-markdown` will fail
- Check the exact path with `pwd` when in the repository directory

**Permission errors?**
- Make binary executable: `chmod +x /path/to/mcp-pdf-markdown/bin/mcp-pdf-markdown`
- Check file permissions in the repository directory

**Python dependency errors?**
- Run `make setup` in the server directory
- Verify virtual environment: `./venv/bin/python -c "import pypdf"`

For more details, see the [Claude Code MCP documentation](https://docs.anthropic.com/en/docs/claude-code/mcp).