# Claude Code Configuration

This guide shows how to configure the MCP PDF Converter with Claude Code CLI.

## Prerequisites

1. Install Claude Code CLI (if not already installed)
2. Setup the MCP server:
   ```bash
   cd /path/to/mcp-pdf-markdown
   make setup
   ```

3. Get configuration details:
   ```bash
   make run
   ```
   This will show you the exact command and args paths to use in the next step. Copy these values for configuration.

## Configuration

### Method 1: Using Claude Code CLI (Recommended)

Copy the Command and Args values from `make run` output and use them like this:

```bash
# Template (replace with your actual paths from 'make run'):
claude mcp add pdf-markdown -- "COMMAND_PATH" "ARGS_PATH"

# Real example:
claude mcp add pdf-markdown -- "/Users/username/Documents/mcp-pdf-markdown/venv/bin/python" "/Users/username/Documents/mcp-pdf-markdown/mcp_pdf_markdown.py"
```

**📋 Copy-Paste Steps:**
1. Run `make run` and copy the Command path
2. Copy the Args path  
3. Use both in quotes as shown above

**⚠️ Important**: Use quotes around the paths to handle spaces correctly.

### With Environment Variables

```bash
claude mcp add pdf-markdown --env OUTPUT_DIR=./docs -- "COMMAND_PATH" "ARGS_PATH"
```

### Method 2: Manual Configuration

Create or edit your MCP configuration file using the paths from `make run`:

```json
{
  "mcpServers": {
    "pdf-markdown": {
      "command": "[COMMAND_FROM_MAKE_RUN]",
      "args": ["[ARGS_FROM_MAKE_RUN]"],
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

- Claude Code automatically starts the Python MCP server when needed
- Files are saved relative to your current working directory (defaults to `./docs`)
- You can override the output directory in prompts: *"Convert PDF to ./my-project/docs/"*
- Multiple projects can use the same MCP server with different output locations

## Troubleshooting

**Server not found?**
- Verify the Python script exists: `ls -la /path/to/mcp-pdf-markdown/mcp_pdf_markdown.py`
- **Always use absolute paths** - relative paths will fail
- Check the exact path with `pwd` when in the repository directory

**Python errors?**
- Verify Python dependencies: `make setup`
- Test the server directly: `make run`

**Virtual environment errors?**
- Recreate virtual environment: `make clean && make setup`
- Test imports: `./venv/bin/python -c "import pypdf, pdfplumber, fitz, mcp"`

For more details, see the [Claude Code MCP documentation](https://docs.anthropic.com/en/docs/claude-code/mcp).