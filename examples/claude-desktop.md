# Claude Desktop Configuration

This guide shows how to configure the MCP PDF Converter with Claude Desktop.

## Prerequisites

Setup the Python MCP server:
```bash
cd /path/to/mcp-pdf-markdown
make setup
```

## Configuration

Add this configuration to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "pdf-markdown": {
      "command": "python3",
      "args": ["/path/to/mcp-pdf-markdown/mcp_pdf_markdown.py"],
      "env": {
        "OUTPUT_DIR": "./docs"
      }
    }
  }
}
```

**Replace `/path/to/mcp-pdf-markdown`** with the actual path to your cloned repository.

### Using Virtual Environment (Recommended)

If you want to use the project's virtual environment:

```json
{
  "mcpServers": {
    "pdf-markdown": {
      "command": "/path/to/mcp-pdf-markdown/venv/bin/python",
      "args": ["/path/to/mcp-pdf-markdown/mcp_pdf_markdown.py"],
      "env": {
        "OUTPUT_DIR": "./docs"
      }
    }
  }
}
```

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
- Check script exists: `ls -la /path/to/mcp-pdf-markdown/mcp_pdf_markdown.py`
- Test directly: `cd /path/to/mcp-pdf-markdown && make run`

**Python errors?**
- Verify Python dependencies: `python3 -c "import pypdf, pdfplumber, fitz"`
- Reinstall if needed: `cd /path/to/mcp-pdf-markdown && make setup`

**Configuration not loading?**
- Restart Claude Desktop after adding the configuration
- Verify JSON syntax in the config file

## How It Works

- Claude Desktop automatically starts the Python MCP server when needed
- Files are saved relative to your current working directory
- You can override the output directory in your prompts
- The server shuts down automatically when not in use