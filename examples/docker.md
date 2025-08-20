# Docker Configuration

This guide shows how to run the MCP PDF-to-Markdown converter in Docker with any MCP-compatible AI tool.

## Prerequisites

- Docker installed and running
- An MCP-compatible AI tool (Claude Desktop, Claude Code, etc.)

## Setup

### 1. Build the Docker Image

```bash
cd /path/to/mcp-pdf-markdown
docker build -t mcp-pdf-markdown .
```

Or using Make:
```bash
make docker-build
```

### 2. Test the Container

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | docker run --rm -i mcp-pdf-markdown
```

You should see a JSON response listing the available tools.

## Configuration

Add this configuration to your MCP client:

```json
{
  "mcpServers": {
    "pdf-markdown": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "mcp-pdf-markdown"],
      "env": {
        "OUTPUT_DIR": "./docs"
      }
    }
  }
}
```

**Note**: The `OUTPUT_DIR` is relative to where your MCP client is running (not inside the container).

## How It Works

The MCP server running in Docker works exactly like the local binary:

1. **Your MCP client** (Claude Code, Claude Desktop, etc.) starts the Docker container
2. **You provide PDF paths** in your prompts to the AI assistant
3. **The MCP server** receives the PDF path via JSON-RPC, processes the file, and returns markdown
4. **Results are returned** as JSON-RPC responses to your AI client

**No volume mounts needed** - the server accesses files through the paths you provide in prompts.

## Usage Examples

Once configured, use the same prompts as with the local binary:

```
Convert the PDF at /Users/username/Documents/manual.pdf to markdown
```

```
Analyze the structure of ./reports/quarterly-report.pdf
```

```
Convert /path/to/research-paper.pdf and save the results to ./project-docs/
```

## Memory Configuration

For large PDFs, increase container memory:

```json
{
  "mcpServers": {
    "pdf-markdown": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-m", "4g", "mcp-pdf-markdown"]
    }
  }
}
```

## Environment Variables

- **`OUTPUT_DIR`**: Where to save converted files relative to your MCP client (default: `./docs`)
- **`PYTHON_PATH`**: Python interpreter path inside container (default: `python3`)
- **`MAX_FILE_SIZE`**: Maximum PDF size in MB (default: `100`)
- **`DEBUG`**: Enable debug logging (default: `false`)

## Troubleshooting

**Container fails to start?**
- Check Docker is running: `docker info`
- Verify image exists: `docker images | grep mcp-pdf-markdown`
- Rebuild image: `docker build --no-cache -t mcp-pdf-markdown .`

**MCP client can't connect?**
- Test container manually: `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | docker run --rm -i mcp-pdf-markdown`
- Check container logs for errors
- Ensure Docker daemon is accessible to your MCP client

**File access errors?**
- Ensure PDF paths in your prompts are accessible from your host machine
- Use absolute paths for PDFs: `/full/path/to/document.pdf`
- Check file permissions on the PDF files

**Out of memory errors?**
- Increase memory limit: add `-m 4g` to Docker args
- Process smaller PDFs or split large ones

**Python dependency errors?**
- Rebuild the Docker image to reinstall dependencies
- Check Dockerfile for correct Python packages

## Advantages of Docker Deployment

- **Isolated environment**: Dependencies contained in the image
- **Consistent execution**: Same Python environment across different systems  
- **Easy deployment**: No need to install Python dependencies on host
- **Memory management**: Can set specific memory limits for PDF processing

## Alternative: Docker Compose

If you prefer Docker Compose for easier management:

```yaml
version: '3.8'
services:
  mcp-pdf-markdown:
    build: .
    container_name: mcp-pdf-markdown-converter
    stdin_open: true
    tty: true
    mem_limit: 4g
```

Then configure your MCP client to use:
```bash
docker-compose run --rm mcp-pdf-markdown
```

## Need Help?

- Test the container directly first
- Check that your MCP client supports Docker-based servers
- Refer to the [generic MCP configuration guide](generic-mcp.md) for protocol details