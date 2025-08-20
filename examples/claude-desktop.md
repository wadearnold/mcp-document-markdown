# Claude Desktop Configuration

This guide shows how to configure the MCP PDF Converter with Claude Desktop.

## Prerequisites

1. Build the MCP server:
   ```bash
   cd /path/to/mcp-pdf-markdown
   make setup
   make build
   ```

2. Copy the binary to your PATH:
   ```bash
   cp bin/mcp-pdf-server /usr/local/bin/
   ```

## Configuration

Add this configuration to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "pdf-converter": {
      "command": "/usr/local/bin/mcp-pdf-server",
      "env": {
        "OUTPUT_DIR": "./docs",
        "PYTHON_PATH": "python3",
        "MAX_FILE_SIZE": "100",
        "DEBUG": "false"
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
- Verify the binary exists: `ls -la /usr/local/bin/mcp-pdf-server`
- Check permissions: `chmod +x /usr/local/bin/mcp-pdf-server`

**Python errors?**
- Verify Python dependencies: `python3 -c "import pypdf, pdfplumber, fitz"`
- Reinstall if needed: `cd /path/to/mcp-pdf-markdown && make setup`

**Configuration not loading?**
- Restart Claude Desktop after adding the configuration
- Verify JSON syntax in the config file

## How It Works

- Claude Desktop automatically starts the `mcp-pdf-server` binary when needed
- Files are saved relative to your current working directory
- You can override the output directory in your prompts
- The server shuts down automatically when not in use