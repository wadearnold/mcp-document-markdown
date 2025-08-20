# MCP PDF Converter

Transform any PDF into well-organized markdown files that work perfectly with AI assistants. This MCP server intelligently splits documents by chapters, preserves tables and images, and creates a navigable structure that fits within context windows.

## Why This Matters for AI Assistants

When you share a PDF with AI assistants, several challenges arise that this tool solves:

**🔍 PDFs are Hard to Process**: PDFs contain complex formatting, embedded fonts, and layout information that makes text extraction unreliable. AI assistants can't easily parse tables, detect document structure, or extract meaningful content from raw PDF text.

**📏 Context Window Limitations**: A 100-page PDF typically exceeds most AI models' context window limits. Even if it fits, processing such large documents leads to:
- Reduced accuracy in responses
- Inability to focus on specific sections
- Higher costs and slower processing
- Loss of important details in long documents

**🎯 Machine-Readable Structure**: Markdown is the preferred format for most AI systems - they're designed to understand and work with structured markdown content. Converting PDFs to clean markdown means:
- **Better comprehension**: AI assistants can understand headers, lists, tables, and document hierarchy
- **Accurate code extraction**: Programming examples and technical content are properly formatted
- **Reliable references**: AI assistants can cite specific sections and maintain context across conversations

**📚 Chapter-Based Analysis**: By splitting documents into logical chapters, you can:
- Ask AI assistants to focus on specific sections without overwhelming context
- Process large documents incrementally 
- Maintain conversation context while exploring different parts
- Get more precise and relevant responses

**💡 The Result**: Instead of getting *"I can't read this PDF"* or confused responses from garbled text, AI assistants can provide accurate analysis, answer detailed questions, and help with complex tasks using properly structured content.

## What This Does

🔄 **PDF → Markdown**: Converts PDFs into clean, structured markdown files  
📚 **Smart Chapter Splitting**: Automatically detects and splits documents by chapters  
📊 **Table Preservation**: Maintains table formatting using multiple extraction methods  
🖼️ **Image Extraction**: Extracts and references images from PDFs  
🧩 **MCP Integration**: Works seamlessly with any AI tool that supports the Model Context Protocol  

## Usage Examples

Once configured, you can use natural language prompts to convert PDFs and then interact with the structured content:

### Convert and Analyze
```
Convert the PDF at /path/to/technical-manual.pdf to markdown, then summarize each chapter
```

### Work with Specific Sections  
```
Convert /path/to/research-paper.pdf and help me understand the methodology section
```

### Extract and Work with Code
```
Convert /path/to/programming-guide.pdf and show me all the Python code examples
```

### Process Large Documents
```
Convert /path/to/100-page-report.pdf with chapter splitting, then create an executive summary
```

### Table Analysis
```
Convert /path/to/financial-data.pdf and analyze the quarterly revenue tables
```

### Multi-Step Workflows
```
Convert /path/to/api-documentation.pdf, then help me write code that uses those APIs
```

**The Power**: After conversion, AI assistants can provide detailed analysis, answer specific questions, extract code examples, and work with complex data - all because the content is now in a structured, machine-readable format that fits within context windows.

## Quick Start

### 1. Install and Build the MCP Server

```bash
git clone https://github.com/wadearnold/mcp-pdf-markdown.git
cd mcp-pdf-markdown
make setup    # Installs Go and Python dependencies
make build    # Builds the server binary
```

### 2. Configure Your MCP Client

This server works with any AI tool that supports the Model Context Protocol (MCP). Choose your client:

**Supported MCP Clients:**
- 🔵 **[Claude Desktop](examples/claude-desktop.md)** - Anthropic's desktop application
- ⌨️ **[Claude Code](examples/claude-code.md)** - Anthropic's CLI tool  
- 🐙 **[GitHub Copilot](examples/github-copilot.md)** - GitHub's AI coding assistant
- 🎯 **[Cursor](examples/cursor.md)** - AI-powered code editor
- 🐳 **[Docker Deployment](examples/docker.md)** - Container-based setup
- ⚙️ **[Other MCP Clients](examples/generic-mcp.md)** - Generic configuration guide

Each guide provides step-by-step instructions for configuring the MCP server with that specific client.

### 3. Start Converting PDFs

Once configured, you can use natural language prompts to convert PDFs and work with the structured content. The server provides these tools:

- **`convert_pdf`**: Convert PDFs to structured markdown files
- **`analyze_pdf_structure`**: Analyze PDF structure without converting

**Example usage in any MCP client:**
```
Convert the PDF at /path/to/document.pdf to markdown with chapter splitting
```

## What You Get

The converter creates organized markdown files:

```
docs/
├── 00_table_of_contents.md    # Navigation file with links
├── 01_introduction.md          # Chapter 1
├── 02_getting_started.md       # Chapter 2  
├── 03_advanced_topics.md       # Chapter 3
└── images/                     # Extracted images
    ├── page_1_img_0.png
    └── page_5_img_2.png
```

Each file is optimized for AI context windows and includes:
- Clean markdown formatting
- Preserved table structure
- Referenced images
- Metadata and cross-links

## Building the Server

### Prerequisites
- Go 1.21 or higher
- Python 3.8 or higher

### Build Options

#### Option 1: Quick Build (Recommended)
```bash
make setup    # Install all dependencies
make build    # Build the server
```

#### Option 2: Manual Build
```bash
go mod download
pip install pypdf pdfplumber pymupdf pandas pillow tabulate markdown
go build -o bin/mcp-pdf-server main.go python_scripts.go
```

#### Option 3: Docker Build
```bash
docker build -t mcp-pdf-server .
# or
make docker-build
```

### Testing Your Build
```bash
make test     # Run basic tests
# or test with a specific PDF
./bin/mcp-pdf-server test sample.pdf ./test_output
```

## Development

### Project Structure
```
mcp-pdf-markdown/
├── main.go                 # MCP server implementation
├── python_scripts.go       # Embedded PDF processing scripts
├── test_client.go          # Test client for development
├── examples/               # Configuration examples
├── Makefile               # Build automation
└── README.md              # This file
```

### Development Setup
```bash
git clone https://github.com/wadearnold/mcp-pdf-markdown.git
cd mcp-pdf-markdown
make setup                  # Install dependencies
make run                    # Run server in development mode
```

### Making Changes

1. **PDF Processing**: Modify the Python scripts in `python_scripts.go`
2. **MCP Protocol**: Edit the server logic in `main.go`
3. **Chapter Detection**: Customize patterns in the `splitIntoChapters()` function
4. **Testing**: Use `test_client.go` for interactive testing

### Testing Your Changes
```bash
make build-test            # Build test client
./bin/test-client interactive    # Interactive testing
```

### Adding New Features

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Add tests if applicable
5. Run `make test` to ensure everything works
6. Submit a pull request

## Configuration Options

### Environment Variables
- **`OUTPUT_DIR`**: Where to save converted files (default: `./docs`)
- **`PYTHON_PATH`**: Python interpreter path (default: `python3`)
- **`MAX_FILE_SIZE`**: Maximum PDF size in MB (default: `100`)
- **`DEBUG`**: Enable debug logging (default: `false`)

### Advanced Configuration
Create a `.env` file (see `.env.example`):
```bash
OUTPUT_DIR=./my-docs
DEBUG=true
MAX_FILE_SIZE=200
```

## Troubleshooting

### Common Issues

**Server not starting?**
```bash
make check-deps    # Check if all dependencies are installed
```

**Python errors?**
```bash
make setup         # Reinstall Python dependencies
```

**Permission denied?**
```bash
chmod +x bin/mcp-pdf-server
```

**Memory issues with large PDFs?**
- Increase `MAX_FILE_SIZE` environment variable
- Use Docker with more memory: `docker run -m 4g ...`
- Split large PDFs before processing

### Debug Mode
```bash
DEBUG=true ./bin/mcp-pdf-server
```

## Architecture

The server uses a hybrid approach:
- **Go**: Handles MCP protocol and server logic
- **Python**: Processes PDFs using multiple libraries (PyMuPDF, pdfplumber, pypdf)
- **Smart Fallbacks**: Multiple extraction methods ensure content is never lost

```
Claude ◄─── MCP Protocol ───► Go Server ───► Python Scripts ───► PDF Libraries
```

## Best Practices

### For Best Results
- Use PDFs with proper text layers (not scanned images)
- Documents with bookmarks/outlines work better for chapter detection
- Simple table layouts convert more accurately

### For Claude Integration
- Each chapter file fits within typical context windows
- Use the table of contents file for navigation
- Files include metadata for better AI understanding

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/wadearnold/mcp-pdf-markdown/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/wadearnold/mcp-pdf-markdown/discussions)
- 📖 **Examples**: Check the [`examples/`](examples/) directory for more configuration options

---

Built for the MCP ecosystem with ❤️