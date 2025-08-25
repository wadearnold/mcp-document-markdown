# Generic MCP Client Configuration

This guide shows how to configure the MCP Document Converter (PDF and Word support) with any MCP-compatible AI tool that isn't specifically covered in other guides.

## About MCP (Model Context Protocol)

The Model Context Protocol is an open standard that allows AI tools to connect to external data sources and tools. This document converter implements MCP to provide PDF and Word document conversion capabilities to any compatible AI client.

## Server Information

- **Protocol**: MCP (Model Context Protocol)
- **Transport**: stdio (standard input/output)
- **Tools Provided**:
  - `convert_pdf`: Convert PDFs to structured markdown
  - `convert_docx`: Convert Word documents to structured markdown
  - `analyze_pdf_structure`: Analyze PDF without conversion
  - `analyze_docx_structure`: Analyze Word document without conversion
  - `prepare_pdf_for_rag`: Prepare PDF content for vector databases

## Prerequisites

1. Setup the MCP server:
   ```bash
   cd /path/to/mcp-document-markdown
   make setup    # Install dependencies and run tests
   ```

2. Get configuration details:
   ```bash
   make run
   ```
   Copy the command and args paths shown for use in your MCP client configuration.

## Basic Configuration

Most MCP clients use a JSON configuration format. Use the paths from `make run`:

```json
{
  "mcpServers": {
    "document-markdown": {
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

Example with actual paths:
```json
{
  "mcpServers": {
    "document-markdown": {
      "command": "/Users/username/Documents/mcp-document-markdown/venv/bin/python",
      "args": ["/Users/username/Documents/mcp-document-markdown/mcp_document_markdown.py"],
      "env": {
        "OUTPUT_DIR": "./docs",
        "DEBUG": "false"
      }
    }
  }
}
```

## Configuration Options

### Command Options

**Using Python with full path:**
```json
{
  "command": "python3",
  "args": ["/path/to/mcp-document-markdown/mcp_document_markdown.py"]
}
```

**Using project virtual environment:**
```json
{
  "command": "/path/to/mcp-document-markdown/venv/bin/python",
  "args": ["/path/to/mcp-document-markdown/mcp_document_markdown.py"]
}
```

**Using Python directly from project directory:**
```json
{
  "command": "python3",
  "args": ["mcp_document_markdown.py"],
  "cwd": "/path/to/mcp-document-markdown"
}
```

### Environment Variables

```json
{
  "env": {
    "OUTPUT_DIR": "./docs",
    "PYTHON_PATH": "python3", 
    "MAX_FILE_SIZE": "100",
    "DEBUG": "false"
  }
}
```

- **`OUTPUT_DIR`**: Where to save converted files (default: `./docs`)
- **`PYTHON_PATH`**: Python interpreter (default: `python3`)
- **`MAX_FILE_SIZE`**: Maximum PDF size in MB (default: `100`)
- **`DEBUG`**: Enable debug logging (default: `false`)

## MCP Protocol Details

### Tools Available

1. **convert_pdf**
   ```json
   {
     "name": "convert_pdf",
     "arguments": {
       "pdf_path": "/path/to/file.pdf",
       "output_dir": "./docs",
       "split_by_chapters": true,
       "preserve_tables": true,
       "extract_images": true
     }
   }
   ```

2. **analyze_pdf_structure**
   ```json
   {
     "name": "analyze_pdf_structure", 
     "arguments": {
       "pdf_path": "/path/to/file.pdf"
     }
   }
   ```

### Server Lifecycle

- **Startup**: MCP client starts the server process when needed
- **Communication**: JSON-RPC over stdin/stdout
- **Shutdown**: Server stops when client disconnects

## Client-Specific Notes

### Configuration File Locations

Common locations for MCP configuration files:

- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- **VS Code Extensions**: Usually in workspace `.vscode/` or user settings
- **Custom Tools**: Check documentation for config file location

### Transport Types

This server uses **stdio transport**:
- Communicates via standard input/output
- Started as a subprocess by the MCP client
- No network configuration required

## Testing Your Configuration

1. **Test server directly:**
   ```bash
   echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python3 /path/to/mcp-document-markdown/mcp_document_markdown.py
   ```

2. **Expected response:**
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "result": {
       "tools": [
         {
           "name": "convert_pdf",
           "description": "Convert PDF files to organized markdown files"
         },
         {
           "name": "analyze_pdf_structure", 
           "description": "Analyze PDF structure without converting"
         }
       ]
     }
   }
   ```

## Common Issues

**Server not starting:**
- Check Python script exists: `ls -la /path/to/mcp-document-markdown/mcp_document_markdown.py`
- Verify dependencies installed (`make setup`)
- Check Python interpreter: `which python3`
- Check paths in configuration

**Tool not found:**
- Ensure proper MCP protocol handshake
- Verify client supports MCP stdio transport
- Check server logs for errors
- Test server manually: `python3 mcp_document_markdown.py`

**Python errors:**
- Verify Python dependencies: `python3 -c "import pypdf, pdfplumber, fitz"`
- Check `PYTHON_PATH` environment variable
- Ensure virtual environment is accessible

## Need Help?

1. Check if your AI tool supports MCP protocol
2. Look for MCP configuration documentation for your specific tool
3. Test the server directly using the commands above
4. Open an issue on GitHub with your configuration details

## MCP Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol)
- [Client Implementation Examples](https://github.com/modelcontextprotocol/servers)