# Cursor Configuration

This guide shows how to configure the MCP PDF Converter with Cursor, the AI-powered code editor.

> **Note**: Cursor's MCP support may vary by version. This guide provides the general approach - check Cursor's official documentation for the latest MCP integration details.

## Prerequisites

1. Install Cursor (if not already installed)
2. Build the MCP server:
   ```bash
   cd /path/to/mcp-pdf-markdown
   make setup
   make build
   ```

3. Copy the binary to your PATH:
   ```bash
   cp bin/mcp-pdf-server /usr/local/bin/
   ```

## Configuration

### Method 1: Cursor Settings

Add this configuration to your Cursor settings (`Cmd/Ctrl + ,` → Search "mcp"):

```json
{
  "mcp.servers": {
    "pdf-converter": {
      "command": "/usr/local/bin/mcp-pdf-server",
      "env": {
        "OUTPUT_DIR": "./docs",
        "DEBUG": "false"
      }
    }
  }
}
```

### Method 2: Workspace Configuration

Create `.cursor/settings.json` in your project root:

```json
{
  "mcp.servers": {
    "pdf-converter": {
      "command": "/usr/local/bin/mcp-pdf-server",
      "env": {
        "OUTPUT_DIR": "./docs",
        "PYTHON_PATH": "python3",
        "MAX_FILE_SIZE": "100"
      }
    }
  }
}
```

### Method 3: Project-Specific Configuration

For project-specific setup, create `.vscode/settings.json` (Cursor uses VS Code format):

```json
{
  "mcp.servers": {
    "pdf-converter": {
      "command": "/usr/local/bin/mcp-pdf-server",
      "env": {
        "OUTPUT_DIR": "./docs"
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

Once configured, you can interact with Cursor using prompts like:

### Code Comments and Chat
```
// Convert the PDF at ./documents/api-guide.pdf to markdown
```

```
// Analyze the structure of ./manuals/user-guide.pdf and create a summary
```

### Chat Interface
```
Convert the PDF at ./reports/quarterly.pdf and help me extract the key financial data
```

```
Process ./pdfs/research-paper.pdf and create a structured summary of the findings
```

### Workflow Integration
```
Convert ./specifications/api-docs.pdf then help me implement the endpoints described
```

## File Explorer Integration

After conversion, Cursor will show the generated markdown files in your file explorer. You can:

1. **Navigate files**: Click on generated markdown files
2. **Preview content**: Use Cursor's markdown preview
3. **Edit and refine**: Modify converted content as needed
4. **AI assistance**: Ask Cursor to work with the converted content

## Troubleshooting

### Configuration Issues

**Settings not applied?**
- Restart Cursor after adding configuration
- Check for typos in JSON configuration
- Try both user and workspace settings

**Server not found?**
- Verify binary exists: `ls -la /usr/local/bin/mcp-pdf-server`
- Make binary executable: `chmod +x /usr/local/bin/mcp-pdf-server`
- Use absolute paths in configuration

### Runtime Issues

**Python errors?**
- Check dependencies: `cd /path/to/mcp-pdf-markdown && make setup`
- Verify Python path: `which python3`
- Test server: `echo '{"method": "tools/list"}' | /usr/local/bin/mcp-pdf-server`

**Permission errors?**
- Check file permissions in output directory
- Ensure Cursor has write access to `OUTPUT_DIR`
- Try running Cursor as administrator (if needed)

### MCP Protocol Issues

**Tools not available?**
- Check Cursor's MCP support documentation
- Verify your Cursor version supports MCP
- Try restarting Cursor with the configuration

## Cursor MCP Status

Cursor's MCP implementation may be in development. For current status:

1. Check [Cursor documentation](https://cursor.sh/docs)
2. Look for MCP-related updates and announcements
3. Join Cursor community forums for latest information

## Alternative Integration

If native MCP support isn't available in your Cursor version:

### CLI Workflow
```bash
# Convert PDF using the server
echo '{"method": "tools/call", "params": {"name": "convert_pdf", "arguments": {"pdf_path": "./document.pdf"}}}' | /usr/local/bin/mcp-pdf-server

# Then use Cursor to work with generated markdown files
```

### Script Integration
Create a script that Cursor can execute:

```bash
#!/bin/bash
# convert-pdf.sh
PDF_PATH="$1"
OUTPUT_DIR="${2:-./docs}"

echo "{\"method\": \"tools/call\", \"params\": {\"name\": \"convert_pdf\", \"arguments\": {\"pdf_path\": \"$PDF_PATH\", \"output_dir\": \"$OUTPUT_DIR\"}}}" | /usr/local/bin/mcp-pdf-server
```

Then in Cursor:
```bash
./convert-pdf.sh ./document.pdf ./my-docs
```

## Advanced Configuration

### Custom Output Directories per Project

```json
{
  "mcp.servers": {
    "pdf-converter": {
      "command": "/usr/local/bin/mcp-pdf-server",
      "env": {
        "OUTPUT_DIR": "./converted-docs",
        "DEBUG": "true"
      }
    }
  }
}
```

### Development vs Production Settings

**Development (.cursor/settings.json):**
```json
{
  "mcp.servers": {
    "pdf-converter": {
      "command": "./bin/mcp-pdf-server",
      "cwd": "/path/to/mcp-pdf-markdown",
      "env": {
        "DEBUG": "true"
      }
    }
  }
}
```

**Production (user settings):**
```json
{
  "mcp.servers": {
    "pdf-converter": {
      "command": "/usr/local/bin/mcp-pdf-server",
      "env": {
        "DEBUG": "false"
      }
    }
  }
}
```

## Need Help?

1. Check Cursor's official MCP documentation
2. Test the server with other MCP clients first
3. Use the [generic MCP configuration guide](generic-mcp.md)
4. Join the Cursor community for MCP-specific support