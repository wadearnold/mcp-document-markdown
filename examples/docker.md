# Docker Configuration

This guide shows how to run the MCP PDF Converter in Docker with any MCP-compatible AI tool.

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

### 2. Create Required Directories

```bash
mkdir -p pdfs docs
```

### 3. Test the Container

```bash
echo '{"method": "tools/list"}' | docker run --rm -i mcp-pdf-markdown
```

## Configuration

Add this configuration to your MCP client:

```json
{
  "mcpServers": {
    "pdf-markdown": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-v", "./pdfs:/app/input", "-v", "./docs:/app/docs", "mcp-pdf-markdown"],
      "env": {
        "OUTPUT_DIR": "/app/docs"
      }
    }
  }
}
```

## Directory Structure

```
your-project/
├── pdfs/           # Place PDF files here
├── docs/           # Converted markdown appears here
└── other-files...
```

## Usage Workflow

1. **Place PDFs**: Copy PDF files to the `./pdfs/` directory
2. **Convert**: Use your MCP client to convert PDFs
3. **Access Results**: Find converted markdown files in `./docs/`

**Example prompts:**
```
Convert the PDF at /app/input/manual.pdf to markdown
```

```
Analyze all PDFs in the input directory and create summaries
```

## Docker Compose (Alternative)

Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  mcp-pdf-markdown:
    build: .
    container_name: mcp-pdf-markdown-converter
    volumes:
      - ./pdfs:/app/input
      - ./docs:/app/docs
    environment:
      - OUTPUT_DIR=/app/docs
    stdin_open: true
    tty: true
```

Run with:
```bash
docker-compose up -d
```

## Environment Variables

- **`OUTPUT_DIR`**: Container output directory (default: `/app/docs`)
- **`PYTHON_PATH`**: Python interpreter path (default: `python3`)
- **`MAX_FILE_SIZE`**: Maximum PDF size in MB (default: `100`)
- **`DEBUG`**: Enable debug logging (default: `false`)

## Memory Configuration

For large PDFs, increase container memory:

```bash
docker run --rm -i -m 4g -v ./pdfs:/app/input -v ./docs:/app/docs mcp-pdf-markdown
```

Or in docker-compose.yml:
```yaml
services:
  mcp-pdf-markdown:
    # ... other config
    mem_limit: 4g
```

## Troubleshooting

**Container fails to start?**
- Check Docker is running: `docker info`
- Verify image exists: `docker images | grep mcp-pdf-markdown`
- Rebuild image: `docker build --no-cache -t mcp-pdf-markdown .`

**Volume mount issues?**
- Use absolute paths: `-v /full/path/to/pdfs:/app/input`
- Check directory permissions: `ls -la pdfs docs`
- Create directories first: `mkdir -p pdfs docs`

**Out of memory errors?**
- Increase memory limit: `docker run -m 4g ...`
- Process smaller PDFs or split large ones

**Python dependency errors?**
- Rebuild the Docker image to reinstall dependencies
- Check Dockerfile for correct Python packages