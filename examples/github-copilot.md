# GitHub Copilot Configuration

This guide shows how to configure the MCP PDF Converter with GitHub Copilot.

> **Note**: GitHub Copilot's MCP support may vary. This guide provides the general approach - check GitHub's official documentation for the latest MCP integration details.

## Prerequisites

1. Setup the MCP server:
   ```bash
   cd /path/to/mcp-pdf-markdown
   make setup
   ```

2. Get configuration details:
   ```bash
   make run
   ```
   Copy the command and args paths shown for use in the configuration below.

## Configuration

GitHub Copilot typically uses MCP configuration through VS Code or other supported editors.

### VS Code Extension Configuration

If using VS Code with GitHub Copilot, add this to your settings using the paths from `make run`:

```json
{
  "mcp.servers": {
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

**Note**: The `make run` command will show the complete paths specific to your system - simply copy and paste those values.

### Workspace Configuration

Create `.vscode/settings.json` in your project using the paths from `make run`:

```json
{
  "mcp.servers": {
    "pdf-markdown": {
      "command": "[COMMAND_FROM_MAKE_RUN]",
      "args": ["[ARGS_FROM_MAKE_RUN]"],
      "env": {
        "OUTPUT_DIR": "./docs",
        "DEBUG": "false"
      }
    }
  }
}
```

## Environment Variables

- **`OUTPUT_DIR`**: Where to save converted files (default: `./docs`)
- **`PYTHON_PATH`**: Python interpreter path (default: `python3`)
- **`MAX_FILE_SIZE`**: Maximum PDF size in MB (default: `100`)
- **`DEBUG`**: Enable debug logging (default: `false`)

## Usage

Once configured, you can use GitHub Copilot with prompts like:

```
// Convert the PDF at ./documents/manual.pdf to markdown
```

```
// Analyze the structure of ./reports/quarterly.pdf
```

```
// Convert ./pdfs/research.pdf and save to ./analysis/
```

## Alternative: CLI Integration

If GitHub Copilot doesn't directly support MCP, you can use the server as a CLI tool:

```bash
# Convert PDF directly
echo '{"method": "tools/call", "params": {"name": "convert_pdf", "arguments": {"pdf_path": "./document.pdf"}}}' | python3 /path/to/mcp-pdf-markdown/mcp_pdf_markdown.py

# Then use Copilot to work with the generated markdown files
```

## Troubleshooting

**Configuration not recognized?**
- Check if your version of GitHub Copilot supports MCP
- Verify VS Code extensions are up to date
- Try restarting VS Code after configuration changes

**Server not responding?**
- Test server directly: `cd /path/to/mcp-pdf-markdown && make run`
- Run `make run` to get the correct paths for your system
- Verify Python script exists: `ls -la /path/to/mcp-pdf-markdown/mcp_pdf_markdown.py`

**Python dependency errors?**
- Reinstall dependencies: `cd /path/to/mcp-pdf-markdown && make setup`
- Test with: `cd /path/to/mcp-pdf-markdown && make run`
- Verify virtual environment is working properly

## GitHub Copilot MCP Status

GitHub Copilot's MCP support is evolving. For the latest information:

1. Check [GitHub Copilot documentation](https://docs.github.com/en/copilot)
2. Look for MCP integration announcements
3. Consider using alternative MCP clients like Claude Desktop or Claude Code

## Fallback: Direct Integration

If MCP integration isn't available, you can still use this tool by:

1. Converting PDFs manually using the server
2. Using GitHub Copilot to work with the resulting markdown files
3. Creating scripts that integrate both tools

Example workflow:
```bash
# Convert PDF
make run PDF=./document.pdf

# Then use GitHub Copilot to analyze the markdown files in ./docs/
```

## Need Help?

- Check GitHub Copilot's official MCP documentation
- Test with other MCP clients first (Claude Desktop, Claude Code)
- Use the [generic MCP configuration guide](generic-mcp.md) as a reference