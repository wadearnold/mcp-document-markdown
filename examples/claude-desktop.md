# Claude Desktop Configuration

This guide shows how to configure the MCP Document Converter (PDF and Word support) with Claude Desktop.

## Prerequisites

1. Setup the Python MCP server:
   ```bash
   cd /path/to/mcp-document-markdown
   make setup
   ```

2. Get configuration details:
   ```bash
   make run
   ```
   Copy the command and args paths shown for use in the configuration below.

## Configuration

Add this configuration to your Claude Desktop config file using the paths from `make run`:

```json
{
  "mcpServers": {
    "document-markdown": {
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

### Alternative: Using System Python

If you prefer to use system Python instead of the virtual environment, you can use `python3` as the command, but the virtual environment (shown by `make run`) is recommended for dependency isolation.

## Configuration File Location

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## Environment Variables

- **`OUTPUT_DIR`**: Where to save converted files (default: `./docs`)
- **`PYTHON_PATH`**: Python interpreter path (default: `python3`)
- **`MAX_FILE_SIZE`**: Maximum PDF size in MB (default: `100`)
- **`DEBUG`**: Enable debug logging (default: `false`)

## Usage

Once configured, you can use these prompts in Claude Desktop:

```
Convert the PDF at /path/to/document.pdf to markdown
```

```
Analyze the structure of /path/to/manual.pdf and summarize each chapter
```

```
Convert /path/to/report.pdf and save to ./project-docs/
```

## Troubleshooting

**Server not starting?**
- Verify Python path: `which python3`
- Check script exists: `ls -la /path/to/mcp-document-markdown/mcp_document_markdown.py`
- Test directly: `cd /path/to/mcp-document-markdown && make run`

**Python errors?**
- Verify Python dependencies: `python3 -c "import pypdf, pdfplumber, fitz"`
- Reinstall if needed: `cd /path/to/mcp-document-markdown && make setup`

**Configuration not loading?**
- Restart Claude Desktop after adding the configuration
- Verify JSON syntax in the config file

## How It Works

- Claude Desktop automatically starts the Python MCP server when needed
- Files are saved relative to your current working directory
- You can override the output directory in your prompts
- The server shuts down automatically when not in use