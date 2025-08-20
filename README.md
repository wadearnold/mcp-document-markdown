# MCP PDF Converter Server

A Model Context Protocol (MCP) server written in Go that converts PDF files into well-organized markdown files, optimized for use with Claude and other LLMs. The server intelligently splits documents by chapters, preserves tables and images, and creates a navigable structure that minimizes context window usage.

## Features

- **Intelligent Chapter Detection**: Automatically identifies and splits PDFs by chapters/sections
- **Table Preservation**: Maintains table formatting using multiple extraction methods
- **Image Extraction**: Extracts and references images from PDFs
- **Multiple Extraction Methods**: Combines PyMuPDF, pdfplumber, and pypdf for best results
- **Structured Output**: Creates numbered markdown files with a table of contents
- **MCP Protocol Support**: Full implementation of the MCP protocol for tool integration
- **Fallback Mechanisms**: Multiple extraction strategies ensure content is never lost

## Architecture

```
┌─────────────┐     MCP Protocol    ┌──────────────┐
│   Claude/   │◄──────────────────►│  MCP Server  │
│   Client    │                     │     (Go)     │
└─────────────┘                     └──────┬───────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │Python Scripts│
                                    │ (Conversion) │
                                    └──────┬───────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
            ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
            │   PyMuPDF    │      │  pdfplumber  │      │    pypdf     │
            │(Text+Images) │      │   (Tables)   │      │ (Structure)  │
            └──────────────┘      └──────────────┘      └──────────────┘
```

## Installation

### Prerequisites

- Go 1.21 or higher
- Python 3.8 or higher
- pip (Python package manager)

### Quick Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcp-pdf-server.git
cd mcp-pdf-server
```

2. Install dependencies:
```bash
make setup
```

This will install both Go and Python dependencies.

### Manual Installation

1. Install Go dependencies:
```bash
go mod download
```

2. Install Python dependencies:
```bash
pip install pypdf pdfplumber pymupdf pandas pillow tabulate markdown
```

3. Build the server:
```bash
go build -o bin/mcp-pdf-server .
```

### Docker Installation

```bash
# Build the Docker image
docker build -t mcp-pdf-server .

# Run with Docker Compose
docker-compose up
```

## Usage

### Starting the Server

```bash
# Run directly
./bin/mcp-pdf-server

# Or use make
make run

# Or with Docker
docker-compose up
```

### MCP Client Configuration

Add to your MCP client configuration (e.g., for Claude Desktop):

```json
{
  "mcpServers": {
    "pdf-converter": {
      "command": "/path/to/mcp-pdf-server",
      "env": {
        "OUTPUT_DIR": "./converted_docs"
      }
    }
  }
}
```

### Available Tools

#### 1. convert_pdf
Converts a PDF file to organized markdown files.

**Parameters:**
- `pdf_path` (required): Path to the PDF file
- `output_dir` (optional): Output directory for markdown files
- `split_by_chapters` (optional, default: true): Split into chapter files
- `preserve_tables` (optional, default: true): Preserve table formatting
- `extract_images` (optional, default: true): Extract and reference images

**Example Request:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "convert_pdf",
    "arguments": {
      "pdf_path": "/path/to/document.pdf",
      "output_dir": "./output",
      "split_by_chapters": true,
      "preserve_tables": true,
      "extract_images": true
    }
  }
}
```

#### 2. analyze_pdf_structure
Analyzes PDF structure without converting.

**Parameters:**
- `pdf_path` (required): Path to the PDF file

**Example Request:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "analyze_pdf_structure",
    "arguments": {
      "pdf_path": "/path/to/document.pdf"
    }
  }
}
```

## Output Structure

The converter creates the following structure:

```
output_dir/
├── 00_table_of_contents.md    # Navigation file
├── 01_introduction.md          # Chapter files
├── 02_chapter_name.md
├── 03_another_chapter.md
└── images/                     # Extracted images
    ├── page_1_img_0.png
    └── page_5_img_2.png
```

### Table of Contents Format

```markdown
# Table of Contents

- [Chapter 1: Introduction](01_introduction.md)
- [Chapter 2: Getting Started](02_getting_started.md)
- [Chapter 3: Advanced Topics](03_advanced_topics.md)
```

## Best Practices

### For Optimal Conversion

1. **PDF Quality**: Higher quality PDFs with proper text layers convert better
2. **Structured Documents**: PDFs with bookmarks/outlines produce better chapter splits
3. **Tables**: Documents with simple tables convert more accurately
4. **Images**: Vector graphics and high-resolution images extract better

### For Claude/LLM Usage

1. **Context Management**: Each chapter file is designed to fit within typical context windows
2. **Navigation**: Always reference the table of contents first
3. **Cross-References**: Files maintain relative links for easy navigation
4. **Metadata**: Important document metadata is preserved in markdown comments

### Handling Different PDF Types

#### Academic Papers
- Enable table preservation
- Extract images for figures and graphs
- May not need chapter splitting for shorter papers

#### Technical Manuals
- Use chapter splitting for navigation
- Preserve tables for specifications
- Extract images for diagrams

#### Books
- Always use chapter splitting
- Consider disabling image extraction for text-heavy books
- Review TOC for proper chapter detection

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
```bash
# Check Python packages
python3 -c "import pypdf, pdfplumber, fitz, pandas"

# Reinstall if needed
pip install --upgrade pypdf pdfplumber pymupdf pandas pillow
```

2. **Chapter Detection Issues**
- The server uses multiple patterns to detect chapters
- You can modify `chapterPatterns` in the Go code for custom formats

3. **Table Extraction Problems**
- Complex tables may need manual review
- Consider using the raw markdown output and manually formatting

4. **Memory Issues with Large PDFs**
- Process in batches using page ranges
- Increase Docker container memory limits
- Consider splitting the PDF first

### Debug Mode

Enable debug logging:
```bash
DEBUG=true ./bin/mcp-pdf-server
```

## Development

### Project Structure

```
mcp-pdf-server/
├── main.go                 # Main server implementation
├── python_scripts.go       # Embedded Python scripts
├── go.mod                  # Go dependencies
├── Dockerfile             # Container definition
├── docker-compose.yml     # Container orchestration
├── Makefile              # Build automation
└── README.md             # This file
```

### Testing

```bash
# Run tests
make test

# Test with a specific PDF
./bin/mcp-pdf-server test sample.pdf ./test_output
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Advanced Configuration

### Environment Variables

- `PYTHON_PATH`: Python interpreter path (default: `python3`)
- `OUTPUT_DIR`: Default output directory (default: `./converted_docs`)
- `MAX_FILE_SIZE`: Maximum PDF size in MB (default: `100`)
- `DEBUG`: Enable debug logging (default: `false`)

### Custom Extraction Rules

You can customize extraction behavior by modifying:

1. **Chapter Patterns**: Edit `chapterPatterns` in `splitIntoChapters()`
2. **Header Detection**: Modify `is_header()` in Python script
3. **Table Formatting**: Adjust `table_to_markdown()` method

## Performance Optimization

### For Large PDFs (>100MB)

1. Use Docker with increased memory:
```yaml
services:
  mcp-pdf-server:
    mem_limit: 4g
```

2. Process in chunks:
- Split PDF into smaller parts first
- Process each part separately
- Combine results

### For Batch Processing

1. Run multiple server instances
2. Use a queue system for job management
3. Implement caching for repeated conversions

## Integration Examples

### With Claude Desktop

1. Add to Claude's config:
```json
{
  "mcpServers": {
    "pdf": {
      "command": "/usr/local/bin/mcp-pdf-server"
    }
  }
}
```

2. Use in conversation:
```
"Convert the PDF at /docs/manual.pdf and create a summary of each chapter"
```

### With Custom Applications

```python
import json
import subprocess

def convert_pdf(pdf_path, output_dir):
    request = {
        "method": "tools/call",
        "params": {
            "name": "convert_pdf",
            "arguments": {
                "pdf_path": pdf_path,
                "output_dir": output_dir
            }
        }
    }
    
    # Send to MCP server
    result = subprocess.run(
        ["./mcp-pdf-server"],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    
    return json.loads(result.stdout)
```

## License

MIT License - See LICENSE file for details

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/mcp-pdf-server/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/mcp-pdf-server/discussions)

## Acknowledgments

- Built for the MCP ecosystem
- Inspired by successful PDF processing pipelines
- Uses best-in-class Python PDF libraries