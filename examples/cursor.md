# Cursor Configuration

This guide shows how to configure the MCP PDF Converter with Cursor, the AI-powered code editor.

> **Note**: Cursor's MCP support may vary by version. This guide provides the general approach - check Cursor's official documentation for the latest MCP integration details.

## Prerequisites

1. Install Cursor (if not already installed)
2. Setup the MCP server:
   ```bash
   cd /path/to/mcp-pdf-markdown
   make setup
   ```

3. Get configuration details:
   ```bash
   make run
   ```
   Copy the command and args paths shown for use in the configuration below.

## Configuration

### Method 1: Cursor Settings

Add this configuration to your Cursor settings (`Cmd/Ctrl + ,` → Search "mcp") using the paths from `make run`:

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

**Note**: The `make run` command will show the complete paths specific to your system - simply copy and paste those values.

### Method 2: Workspace Configuration

Create `.cursor/settings.json` in your project root using the paths from `make run`:

```json
{
  "mcp.servers": {
    "pdf-markdown": {
      "command": "[COMMAND_FROM_MAKE_RUN]",
      "args": ["[ARGS_FROM_MAKE_RUN]"],
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

For project-specific setup, create `.vscode/settings.json` (Cursor uses VS Code format) using the paths from `make run`:

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
- Run `make run` to get the correct paths for your system
- Verify Python script exists: `ls -la /path/to/mcp-pdf-markdown/mcp_document_markdown.py`
- Verify Python interpreter: `which python3`
- Use the exact paths shown by `make run` in configuration

### Runtime Issues

**Python errors?**
- Check dependencies: `cd /path/to/mcp-pdf-markdown && make setup`
- Test server: `cd /path/to/mcp-pdf-markdown && make run`
- Verify virtual environment is working properly

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
echo '{"method": "tools/call", "params": {"name": "convert_pdf", "arguments": {"pdf_path": "./document.pdf"}}}' | python3 /path/to/mcp-pdf-markdown/mcp_document_markdown.py

# Then use Cursor to work with generated markdown files
```

### Script Integration
Create a script that Cursor can execute:

```bash
#!/bin/bash
# convert-pdf.sh
PDF_PATH="$1"
OUTPUT_DIR="${2:-./docs}"

echo "{\"method\": \"tools/call\", \"params\": {\"name\": \"convert_pdf\", \"arguments\": {\"pdf_path\": \"$PDF_PATH\", \"output_dir\": \"$OUTPUT_DIR\"}}}" | python3 /path/to/mcp-pdf-markdown/mcp_document_markdown.py
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
    "pdf-markdown": {
      "command": "[COMMAND_FROM_MAKE_RUN]",
      "args": ["[ARGS_FROM_MAKE_RUN]"],
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
    "pdf-markdown": {
      "command": "[COMMAND_FROM_MAKE_RUN]",
      "args": ["[ARGS_FROM_MAKE_RUN]"],
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
    "pdf-markdown": {
      "command": "[COMMAND_FROM_MAKE_RUN]",
      "args": ["[ARGS_FROM_MAKE_RUN]"],
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