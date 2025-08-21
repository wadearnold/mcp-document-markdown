# MCP PDF to Markdown Converter

Transform PDFs into AI-ready documentation that makes your assistant smarter. Extract clean, organized reference material that your AI agent can actually use.

## What This Does

Convert any PDF into structured documentation that your AI assistant can understand and reference:

- **📄 PDF → 🤖 AI Reference**: Clean markdown files your AI can navigate and cite
- **🧠 Two Workflows**: Direct file reference OR vector database for RAG
- **⚡ Ready to Use**: Drop PDFs in, get organized docs out

## Why Your AI Needs This

**Before**: *"I can't read that PDF"* or confused responses from garbled text  
**After**: Your AI assistant provides accurate analysis, answers detailed questions, and references specific sections

## Quick Start

### 1. Install the MCP Server

**Option A: Standard Install**
```bash
git clone https://github.com/wadearnold/mcp-pdf-markdown.git
cd mcp-pdf-markdown
make setup    # Installs dependencies
make build    # Builds the server
```

**Option B: Docker (Alternative)**
```bash
git clone https://github.com/wadearnold/mcp-pdf-markdown.git
cd mcp-pdf-markdown
docker build -t mcp-pdf-markdown .
```

### 2. Configure Your AI Assistant

Add the MCP server to your AI assistant. Choose your setup:

- 🔵 **[Claude Desktop](examples/claude-desktop.md)** - Anthropic's desktop app
- ⌨️ **[Claude Code](examples/claude-code.md)** - Anthropic's CLI tool  
- 🐙 **[GitHub Copilot](examples/github-copilot.md)** - GitHub's AI assistant
- 🎯 **[Cursor](examples/cursor.md)** - AI-powered code editor
- ⚙️ **[Generic MCP Setup](examples/generic-mcp.md)** - Other MCP clients

### 3. Convert Your First PDF

Once configured, just ask your AI assistant:

```
Convert the PDF at /path/to/my-documentation.pdf to markdown
```

Your AI will convert the PDF and create organized reference files it can use to help you.

## Two Ways to Use This

### 📁 Workflow 1: Direct File Reference
**Best for**: Having conversations about documents, manual navigation, human-readable files

```
PDF → Organized Markdown → Your AI references specific sections
```

**Example**: 
```
Convert /path/to/api-docs.pdf to markdown, then help me understand the authentication section
```

**What you get**: Clean markdown files organized by chapter/section that your AI can read and reference.

### 🔍 Workflow 2: Vector Database (RAG)
**Best for**: Semantic search, knowledge bases, scaling to many documents

```
PDF → Semantic Chunks → Vector Database → AI searches and retrieves relevant info
```

**Example**:
```
Prepare /path/to/manual.pdf for RAG with vector database format chromadb
```

**What you get**: Optimized chunks ready for import into vector databases.

#### Vector Database Advantages Over Flat Files:
- **Semantic Search**: Find information by meaning, not just keywords
- **Scale**: Handle hundreds of documents efficiently  
- **Context**: AI gets the most relevant sections automatically
- **Speed**: Instant retrieval vs browsing through files

#### Setting Up Vector Databases:

**ChromaDB** (Local):
```
Prepare my-docs.pdf for RAG with vector database format chromadb
```
Then configure [Chroma MCP Server](https://github.com/chroma-core/chroma-mcp) and import the generated chunks.

**Pinecone** (Cloud):
```
Prepare my-docs.pdf for RAG with vector database format pinecone  
```
Then configure [Pinecone MCP Server](https://docs.pinecone.io/guides/operations/mcp-server) and import the generated data.

**To create embeddings**, tell your AI:
```
Generate embeddings for all the chunks in the chromadb_format.json file using OpenAI's text-embedding-ada-002 model and import them into the ChromaDB collection
```

## Making Your AI Agent Use the Documentation

After converting PDFs, **tell your AI agent to use the new documentation as reference**:

### Copy-Paste Prompt for Your Agent:

```
I've just converted PDF documentation into organized markdown files. Please update your working memory to reference these new docs as the definitive source for this project:

📁 **New Reference Documentation Location**: `./docs/` 

🔍 **Key Reference Files**:
- `index.md` - Main navigation and overview
- `summary.md` - Quick document summary  
- `sections/` - Organized content by chapter/topic
- `concepts/glossary.md` - Technical terms and definitions
- `summaries/` - Multi-level summaries (executive, detailed, complete)
- `cross-references/` - Links and connections between sections

⚡ **Instructions**: 
1. Use these docs as the primary reference for questions about [PROJECT/TOPIC NAME]
2. When I ask questions, search these files first before using general knowledge
3. Always cite specific sections when referencing information
4. Suggest relevant sections when I'm exploring topics

🎯 **Remember**: This documentation is now the definitive source for [PROJECT/TOPIC NAME]. Reference it actively and help me navigate it effectively.

Please confirm you understand and will use `./docs/` as the primary reference source going forward.
```

**Customize the prompt by**:
- Replace `[PROJECT/TOPIC NAME]` with your actual project name
- Update the path if you used a different output directory
- Add specific sections that are most important for your use case

## What You Actually Get

The MCP server creates organized documentation your AI can navigate:

```
docs/
├── index.md                    # Main navigation
├── summary.md                  # Document overview  
├── sections/                   # Content organized by topic
│   ├── 01-introduction.md
│   ├── 02-getting-started.md
│   └── 03-api-reference.md
├── concepts/                   # Technical definitions
│   └── glossary.md            # Terms your AI can reference
├── summaries/                  # Different detail levels
│   ├── executive-summary.md    # High-level overview
│   ├── detailed-summary.md     # Comprehensive summary
│   └── complete-summary.md     # Full context
├── tables/                     # Structured data
│   ├── table_01.md
│   └── table_01.json
└── images/                     # Extracted images
    └── diagrams/
```

**For RAG workflows**:
```
rag_output/
├── chunks.json                 # Semantic chunks with metadata
├── chromadb_format.json        # Ready for ChromaDB import
├── pinecone_format.json        # Ready for Pinecone import
└── import_instructions.md      # Complete setup guide
```

## Configuration

### Docker Setup
If you chose Docker installation, configure it as an alternative to Step 1:

**For Docker-based MCP client configs**, use:
```json
{
  "command": "docker",
  "args": ["run", "--rm", "-v", "/path/to/your/pdfs:/pdfs", "mcp-pdf-markdown"],
  "env": {}
}
```

**Note**: This runs a container per request. For better performance, consider running a persistent container.

### Tool Parameters

**Basic Conversion** (`convert_pdf`):
- `pdf_path` (required) - Path to your PDF
- `output_dir` (optional) - Where to save files (default: `./docs`)

**RAG Preparation** (`prepare_pdf_for_rag`):
- `pdf_path` (required) - Path to your PDF  
- `vector_db_format` - Target database (`chromadb`, `pinecone`, `weaviate`, `qdrant`)
- `chunk_size` - Tokens per chunk (default: 768)
- `output_dir` - Where to save chunks (default: `./rag_output`)

**Advanced Options** (optional):
- `split_by_chapters` (default: true) - Organize by document structure
- `preserve_tables` (default: true) - Keep table formatting
- `extract_images` (default: true) - Save referenced images

## Examples

### Basic Document Reference
```
Convert the user manual at /docs/user-guide.pdf to markdown, then help me understand how to set up authentication
```

### API Documentation  
```
Convert /docs/api-reference.pdf to markdown and help me write code that uses the user management endpoints
```

### Large Document Processing
```
Convert the 200-page technical specification at /specs/system-design.pdf to markdown with chapter splitting
```

### RAG Setup
```
Prepare /docs/knowledge-base.pdf for RAG with vector database format chromadb, then help me set up semantic search
```

## Troubleshooting

**Server won't start?**
```bash
make setup    # Reinstall dependencies
```

**PDF won't convert?**
- Check file permissions
- Verify PDF isn't password protected
- Ensure PDF is text-based (not scanned images)

**AI not using the docs?**
- Use the copy-paste prompt above to remind your AI about the new reference files
- Reference specific files by name: "Check the getting-started.md file"
- Ask your AI to "update your working memory" with the new documentation location

## Development

### Prerequisites
- Go 1.21+
- Python 3.8+

### Build from source
```bash
git clone https://github.com/wadearnold/mcp-pdf-markdown.git
cd mcp-pdf-markdown
make setup && make build
```

### Development mode
```bash
make dev    # Load Python scripts from files (no rebuild needed)
```

## License

Apache License 2.0