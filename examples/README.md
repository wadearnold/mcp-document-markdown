# MCP PDF Converter Configuration Examples

This directory contains example configurations for using the MCP PDF Converter server with different Claude clients.

## Claude Code Configuration

**File:** `claude-code-config.json`

For Claude Code CLI, add this to your MCP configuration:

```json
{
  "mcpServers": {
    "pdf-converter": {
      "command": "go",
      "args": ["run", "."],
      "cwd": "/path/to/mcp-pdf-markdown",
      "env": {
        "OUTPUT_DIR": "./docs",
        "PYTHON_PATH": "python3",
        "DEBUG": "false"
      }
    }
  }
}
```

**Setup Instructions:**
1. Clone this repository to your local machine
2. Update the `cwd` path to point to your repository location
3. Run `make setup` in the repository directory to install dependencies
4. Add the configuration to your Claude Code MCP settings

## Claude Desktop Configuration

**File:** `claude-desktop-config.json`

For Claude Desktop app, add this to your configuration file:

```json
{
  "mcpServers": {
    "pdf-converter": {
      "command": "/usr/local/bin/mcp-pdf-server",
      "env": {
        "OUTPUT_DIR": "/Users/username/Documents/converted_pdfs",
        "PYTHON_PATH": "python3",
        "MAX_FILE_SIZE": "100",
        "DEBUG": "false"
      }
    }
  }
}
```

**Setup Instructions:**
1. Build the server: `make build`
2. Copy the binary to your PATH: `cp bin/mcp-pdf-server /usr/local/bin/`
3. Update the `OUTPUT_DIR` to your preferred location
4. Replace `username` with your actual username
5. Add the configuration to Claude Desktop's MCP settings

**Configuration File Locations:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

## Docker Configuration

**File:** `docker-config.json`

For running the server in Docker:

```json
{
  "mcpServers": {
    "pdf-converter": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-v", "./pdfs:/app/input", "-v", "./docs:/app/docs", "mcp-pdf-server"],
      "env": {
        "OUTPUT_DIR": "/app/docs"
      }
    }
  }
}
```

**Setup Instructions:**
1. Build the Docker image: `make docker-build` or `docker build -t mcp-pdf-server .`
2. Create directories for your PDFs and output: `mkdir -p pdfs docs`
3. Add the configuration to your MCP settings
4. Place PDFs in the `./pdfs/` directory
5. Converted markdown files will appear in `./docs/`

**How it works:**
- `./pdfs:/app/input` - Maps your local `pdfs` directory to the container's input
- `./docs:/app/docs` - Maps your local `docs` directory to the container's output
- Files are processed inside the container but results appear in your local filesystem

## Environment Variables

All configurations support these environment variables:

- **`OUTPUT_DIR`**: Directory where converted files will be saved (default: `./docs`)
- **`PYTHON_PATH`**: Path to Python interpreter (default: `python3`)
- **`MAX_FILE_SIZE`**: Maximum PDF size in MB (default: `100`)
- **`DEBUG`**: Enable debug logging (`true`/`false`, default: `false`)

## Usage Examples

Once configured, you can use the PDF converter in your Claude conversations:

```
Convert the PDF at /path/to/document.pdf and create a summary of each chapter
```

```
Analyze the structure of /path/to/manual.pdf without converting it
```

```
Convert /path/to/report.pdf to markdown with tables preserved and save to ./my-docs/
```

## Troubleshooting

1. **Command not found**: Ensure the binary path is correct and executable
2. **Python errors**: Verify Python dependencies are installed (`make setup`)
3. **Permission denied**: Check file permissions and directory access
4. **Docker issues**: Ensure Docker is running and image is built

For more detailed troubleshooting, see the main [README.md](../README.md#troubleshooting).