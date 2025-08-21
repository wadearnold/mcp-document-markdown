# MCP PDF to Markdown Converter

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

### Organize for Optimal Context Usage
```
Convert the PDF at ./technical-document.pdf to markdown and organize it into sections for optimal context usage. Save the organized sections to my docs directory with proper table of contents and navigation.
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

- **`convert_pdf`**: Convert PDFs to structured markdown files with configurable options
- **`analyze_pdf_structure`**: Analyze PDF structure without converting

**Example usage in any MCP client:**
```
Convert the PDF at /path/to/document.pdf to markdown with chapter splitting
```

**Control chunking behavior:**
```
Convert /path/to/document.pdf with enable_chunking set to false
```

**Available Parameters:**
- `pdf_path` (required): Path to the PDF file
- `output_dir` (optional): Output directory for markdown files  
- `split_by_chapters` (default: true): Split document by chapters
- `preserve_tables` (default: true): Preserve table formatting
- `extract_images` (default: true): Extract and reference images
- `enable_chunking` (default: true): Enable smart chunking for optimal LLM context usage

## What You Get

The converter creates organized markdown files with LLM-optimized metadata:

```
docs/
├── sections/                       # Organized content sections
│   ├── 01-introduction.md         # With token counts & LLM fit
│   ├── 02-authentication.md       # Semantic type detection
│   └── 03-api-endpoints.md        # Smart chunking
├── chunked/                        # Smart chunks by token limits
│   ├── large-section-chunk-1-small.md    # 3.5K tokens (GPT-3.5)
│   ├── large-section-chunk-1-medium.md   # 7K tokens (GPT-4)
│   ├── large-section-chunk-1-large.md    # 30K tokens (GPT-4-32K)
│   ├── large-section-chunk-1-xlarge.md   # 95K tokens (Claude)
│   └── chunk-manifest.json               # Chunking metadata
├── api-endpoints/                  # Individual API endpoint files
│   ├── README.md                   # API index and processing guide
│   ├── 01-post-users-create.md    # POST /users endpoint
│   ├── 02-get-users-id.md         # GET /users/{id} endpoint
│   └── 03-delete-users-id.md      # DELETE /users/{id} endpoint
├── complete/
│   └── full-document.md           # Complete document
├── images/                        # Extracted images
│   ├── page_1_img_0.png
│   └── page_5_img_2.png
├── index.md                       # Navigation & TOC
├── summary.md                     # Document summary
├── metadata.json                  # Comprehensive metrics
└── llm-compatibility-report.md    # LLM processing guide
```

### 🎯 LLM Optimization Features (NEW!)

#### Advanced Semantic Detection
Each section is automatically classified with intelligent content analysis:
```markdown
---
title: API Authentication
section_type: authentication
processing_priority: critical
tokens: 2847
optimal_model: gpt-4
semantic_tags: ["authentication", "http-message"]
contains_code: true
api_endpoints_count: 3
extracted_endpoints: ["POST /auth/token", "GET /auth/verify"]
llm_processing_notes: ["Extract authentication mechanisms, required headers, and token formats"]
---
```

#### API Endpoint Extraction (NEW!)
Individual files created for each API endpoint with complete documentation:
```markdown
---
title: POST /users/{id}/update
method: POST
path: /users/{id}/update
endpoint_type: api_endpoint
tokens: 1847
optimal_model: gpt-4
has_parameters: true
has_request_body: true
authentication_required: true
---

# POST /users/{id}/update

## Parameters
| Name | Location | Type | Required |
|------|----------|------|----------|
| id   | path     | string | true   |

## Request Body
```json
{"name": "John", "email": "john@example.com"}
```

## Examples
### CURL
```curl
curl -X POST /users/123/update -H "Authorization: Bearer token"
```
```

#### Smart Chunking by Token Limits (NEW!)
Automatically splits large sections into optimal token-sized chunks for different LLM context windows:

```
docs/chunked/
├── large-section-chunk-1-small.md     # 3,500 tokens (GPT-3.5)
├── large-section-chunk-1-medium.md    # 7,000 tokens (GPT-4)  
├── large-section-chunk-1-large.md     # 30,000 tokens (GPT-4-32K)
├── large-section-chunk-1-xlarge.md    # 95,000 tokens (Claude)
└── chunk-manifest.json                # Chunking metadata
```

**Intelligent Boundary Detection:**
- Preserves complete headers and subsections
- Maintains paragraph integrity
- Splits at sentence boundaries when needed
- Includes cross-references between chunks

**Chunk Documentation:**
Each chunk includes comprehensive metadata for processing guidance:
```markdown
---
title: API Documentation - Part 1 of 3
original_section: API Endpoints  
chunk_number: 1
total_chunks: 3
token_limit: small
tokens: 3485
contains_api_endpoints: 5
processing_notes: ["Focus on authentication endpoints", "Contains OAuth flow"]
next_chunk: "api-documentation-chunk-2-small.md"
---
```

**Processing Guidance:**
- Chunks maintain logical coherence for LLM understanding
- Cross-references help LLMs understand document flow
- Token counts enable precise context window planning
- Processing notes guide LLM focus areas

**Control Options:**
Smart chunking is enabled by default but can be controlled:
```
# Enable chunking (default behavior)
Convert the PDF at /path/to/document.pdf to markdown

# Disable chunking explicitly  
Convert the PDF at /path/to/document.pdf with enable_chunking set to false
```

#### Intelligent Section Types
- **api_endpoint**: HTTP methods, URLs, parameters
- **authentication**: OAuth, JWT, API keys, credentials  
- **request_response**: Payload structures, headers
- **data_models**: Schemas, field definitions
- **error_handling**: Status codes, error messages
- **code_examples**: Executable examples with language detection
- **security**: Encryption, certificates, security protocols
- And 8 more specialized types

The **metadata.json** provides:
- Token counts and LLM compatibility analysis
- Semantic classification and content analysis
- Processing priority and workflow guidance
- Extracted API endpoints and technical elements
- Optimal chunking recommendations

The **llm-compatibility-report.md** shows:
- Which sections fit in which LLM context windows
- Token distribution analysis
- Specific recommendations for each model
- Processing strategies based on document structure

### Benefits for LLM Processing

✅ **Semantic Understanding**: LLMs instantly know content type and purpose
✅ **API Endpoint Focus**: Individual files for each endpoint with complete context
✅ **Processing Priority**: Critical sections (authentication, APIs) identified first  
✅ **Context Window Management**: Precise token counts and model recommendations
✅ **Structured API Data**: Parameters, request/response formats, and examples extracted
✅ **Smart Chunking**: Automatic splitting for optimal context window utilization
✅ **Workflow Optimization**: Processing notes guide LLMs on what to focus on
✅ **Batch API Processing**: Process related endpoints together for efficient integration
✅ **Code Generation Ready**: Complete endpoint info for automatic client generation
✅ **Cost Estimation**: Calculate API costs based on accurate token counts
✅ **Multi-Model Support**: Optimized chunks for GPT-3.5, GPT-4, GPT-4-32K, and Claude

Each file is optimized for LLM processing and includes:
- Clean markdown formatting with semantic structure
- Preserved table structure  
- Referenced images with context
- Comprehensive metadata for intelligent processing
- Semantic tags and processing guidance
- API endpoint extraction and classification
- Processing priority for workflow optimization

## Building the Server

### Prerequisites
- Go 1.21 or higher
- Python 3.8 or higher
- Python dependencies (installed automatically via `make setup` or `pip install -r requirements.txt`)

### Build Options

#### Option 1: Quick Build (Recommended)
```bash
make setup    # Install all dependencies
make build    # Build the server
```

#### Option 2: Manual Build
```bash
go mod download
pip install -r requirements.txt
go build -o bin/mcp-pdf-markdown main.go python_embed.go python_loader.go
```

#### Option 3: Docker Build
```bash
docker build -t mcp-pdf-markdown .
# or
make docker-build
```

### Testing Your Build
```bash
make test     # Run basic tests
# or test with a specific PDF
./bin/mcp-pdf-markdown test sample.pdf ./test_output
```

## Development

### Project Structure
```
mcp-pdf-markdown/
├── main.go                 # MCP server implementation
├── python_embed.go         # Embeds Python scripts at compile time
├── python_loader.go        # Development mode Python loader
├── python/                 # Python scripts (editable)
│   ├── pdf_converter.py    # PDF to markdown conversion
│   ├── pdf_analyzer.py     # PDF structure analysis
│   └── README.md          # Python development guide
├── examples/               # Client configuration guides
├── Makefile               # Build automation
└── README.md              # This file
```

### Development Setup
```bash
git clone https://github.com/wadearnold/mcp-pdf-markdown.git
cd mcp-pdf-markdown
make setup                  # Install dependencies
make build                  # Build the server
```

### Python Script Development

The Python scripts are now in separate files for easy editing and optimization:

#### Development Workflow
```bash
# 1. Edit Python scripts with your favorite editor
vim python/pdf_converter.py

# 2. Test changes without rebuilding (loads Python from files)
make dev

# 3. Build final binary when satisfied (embeds Python scripts)
make build
```

#### Key Commands
- **`make dev`** - Run server in development mode (loads Python from `python/` directory)
- **`make build`** - Build production binary (embeds Python scripts)
- **`make run`** - Run the built server
- **`make clean`** - Clean build artifacts

#### How It Works
- **Development Mode**: Set `PYTHON_SCRIPTS_DIR=./python` to load scripts from files
- **Production Mode**: Python scripts are embedded into the Go binary at compile time
- **Benefits**: Edit Python with syntax highlighting, test without rebuilding, single binary distribution

### Making Changes

1. **Python PDF Processing**: Edit files in `python/` directory
   - `pdf_converter.py` - Main conversion logic
   - `pdf_analyzer.py` - PDF analysis logic
   
2. **MCP Protocol**: Edit the server logic in `main.go`

3. **Chapter Detection**: Customize patterns in `splitIntoChapters()` function in `main.go`

4. **Testing**: Use `test_client.go` for interactive testing

### Testing Your Changes
```bash
# Test Python changes in development mode
make dev

# Build and test production binary
make build && ./bin/mcp-pdf-markdown

# Run interactive test client
make build-test && ./bin/test-client interactive
```

### Adding New Features

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes (Python in `python/`, Go in main files)
4. Test thoroughly in development mode
5. Build and test production binary
6. Submit a pull request

## Using the Metadata

### Programmatic Access

The `metadata.json` file provides comprehensive metrics for automated processing:

```python
import json

with open('docs/metadata.json') as f:
    metadata = json.load(f)

# Check which sections fit in GPT-4
for section in metadata['sections']:
    if section['tokens'] <= 8192:
        print(f"Section {section['title']} fits in GPT-4")

# Get processing recommendations
print(metadata['recommendations']['optimal_chunk_size'])
print(metadata['recommendations']['processing_strategy'])
```

### LLM Compatibility Report

The human-readable `llm-compatibility-report.md` provides:
- Visual compatibility matrix for all major LLMs
- Token distribution charts
- Specific processing recommendations
- Section-by-section analysis

### Using Semantic Metadata for LLM Workflows

```python
import json
import yaml

# Load metadata
with open('docs/metadata.json') as f:
    metadata = json.load(f)

# Process by priority (critical first)
critical_sections = [s for s in metadata['sections'] if s.get('processing_priority') == 'critical']
for section in critical_sections:
    print(f"Processing {section['title']} - {section['section_type']}")
    
# Find all API endpoints
api_sections = [s for s in metadata['sections'] if s['section_type'] == 'api_endpoint']
for section in api_sections:
    endpoints = section.get('extracted_endpoints', [])
    print(f"Found {len(endpoints)} endpoints in {section['title']}")

# Process sections with code examples
code_sections = [s for s in metadata['sections'] if s.get('contains_code')]
print(f"Found {len(code_sections)} sections with executable code")

# Work with API endpoints
api_dir = 'docs/api-endpoints'
if os.path.exists(api_dir):
    endpoint_files = [f for f in os.listdir(api_dir) if f.endswith('.md') and f != 'README.md']
    print(f"Found {len(endpoint_files)} API endpoints")
    
    # Process endpoints by method
    for filename in endpoint_files:
        with open(f"{api_dir}/{filename}") as f:
            content = f.read()
            if 'method: POST' in content:
                print(f"Found POST endpoint: {filename}")
```

### API Endpoint Features

Each extracted API endpoint includes:

- **Complete Parameter Documentation**: Path and query parameters with types
- **Request/Response Examples**: JSON payloads and response formats
- **Authentication Requirements**: Bearer tokens, API keys, headers
- **HTTP Status Codes**: Success and error response codes
- **cURL Examples**: Ready-to-use command line examples
- **Token Counts**: For context window planning
- **Source Context**: Original documentation for reference

**API Index File** (`api-endpoints/README.md`) provides:
- Quick reference table of all endpoints
- Processing strategies for LLMs
- Categorization by HTTP method
- Batch processing recommendations

### Token Counting Accuracy

- **With tiktoken**: Exact token counts using OpenAI's tokenizer
- **Without tiktoken**: Approximation (~4 characters per token)
- Install tiktoken for best results: `pip install tiktoken`

## Configuration Options

### MCP Tool Parameters
The `convert_pdf` tool accepts these parameters:
- **`pdf_path`** (required): Path to the PDF file to convert
- **`output_dir`** (optional): Directory where markdown files will be saved
- **`split_by_chapters`** (default: true): Whether to split the document by chapters  
- **`preserve_tables`** (default: true): Whether to preserve table formatting
- **`extract_images`** (default: true): Whether to extract and reference images
- **`enable_chunking`** (default: true): Whether to enable smart chunking by token limits

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
chmod +x bin/mcp-pdf-markdown
```

**Memory issues with large PDFs?**
- Increase `MAX_FILE_SIZE` environment variable
- Use Docker with more memory: `docker run -m 4g ...`
- Split large PDFs before processing

### Debug Mode
```bash
DEBUG=true ./bin/mcp-pdf-markdown
```

## License

Apache License 2.0 - See [LICENSE](LICENSE) file for details.
