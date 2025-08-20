# MCP PDF Converter

Transform any PDF into well-organized markdown files that work perfectly with Claude and other AI assistants. This MCP server intelligently splits documents by chapters, preserves tables and images, and creates a navigable structure that fits within context windows.

## What This Does

🔄 **PDF → Markdown**: Converts PDFs into clean, structured markdown files  
📚 **Smart Chapter Splitting**: Automatically detects and splits documents by chapters  
📊 **Table Preservation**: Maintains table formatting using multiple extraction methods  
🖼️ **Image Extraction**: Extracts and references images from PDFs  
🧩 **MCP Integration**: Works seamlessly with Claude Desktop, Claude Code, and other MCP clients  

## Quick Start

### 1. Add MCP Server Configuration

Choose your preferred method:

#### For Claude Desktop
Copy the configuration from [`examples/claude-desktop-config.json`](examples/claude-desktop-config.json):

```json
{
  "mcpServers": {
    "pdf-converter": {
      "command": "/usr/local/bin/mcp-pdf-server",
      "env": {
        "OUTPUT_DIR": "/Users/username/Documents/converted_pdfs"
      }
    }
  }
}
```

Add this to your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### For Claude Code
Copy the configuration from [`examples/claude-code-config.json`](examples/claude-code-config.json):

```json
{
  "mcpServers": {
    "pdf-converter": {
      "command": "go",
      "args": ["run", "."],
      "cwd": "/path/to/mcp-pdf-markdown",
      "env": {
        "OUTPUT_DIR": "./docs"
      }
    }
  }
}
```

**⚠️ Important**: Replace `"/path/to/mcp-pdf-markdown"` with the actual path where you cloned this repository:
- **macOS/Linux Example**: `"/Users/yourname/Documents/mcp-pdf-markdown"`
- **Windows Example**: `"C:\\Users\\yourname\\Documents\\mcp-pdf-markdown"`

The `cwd` (current working directory) tells Claude Code where to find the Go project files so it can run `go run .` from the correct location.

#### For Docker
First, build the Docker image and create the required directories:

```bash
# Build the image
docker build -t mcp-pdf-server .

# Create directories for PDF files and output
mkdir -p pdfs docs
```

Then copy the configuration from [`examples/docker-config.json`](examples/docker-config.json):

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

**How it works**: Place PDFs in the `./pdfs/` directory, and converted markdown files will appear in `./docs/`.

See the [`examples/README.md`](examples/README.md) for detailed setup instructions.

### 2. Install and Build

```bash
git clone https://github.com/wadearnold/mcp-pdf-markdown.git
cd mcp-pdf-markdown
make setup    # Installs Go and Python dependencies
make build    # Builds the server
```

For Claude Desktop, copy the binary to your PATH:
```bash
cp bin/mcp-pdf-server /usr/local/bin/
```

### 3. Start Converting PDFs

Once configured, you can use natural language prompts in your Claude conversation:

## Usage Examples

### Basic Conversion
```
Convert the PDF at /path/to/document.pdf to markdown
```

### With Custom Output Directory
```
Convert /path/to/manual.pdf and save the markdown files to ./my-docs/
```

### Analyze Before Converting
```
Analyze the structure of /path/to/report.pdf and tell me how many chapters it has
```

### Advanced Options
```
Convert /path/to/book.pdf with chapter splitting enabled, preserve all tables, and extract images
```

### Batch Processing
```
Convert all PDFs in /path/to/pdfs/ directory and organize them by filename
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