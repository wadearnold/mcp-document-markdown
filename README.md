# MCP Document to Markdown Converter

Transform PDFs and Word documents into AI-ready documentation that makes your assistant smarter. Extract clean, organized reference material from any document format that your AI agent can actually use.

## 📄 Supported Formats

- **PDF** (.pdf) - Technical specifications, API docs, research papers
- **Microsoft Word** (.docx) - Reports, documentation, proposals

## What This Does

Transform massive, complex documents (PDFs, Word docs) into AI-optimized documentation that enables intelligent agent workflows:

### 🎯 **The Agent Problem This Solves**
- **Large Documents = Agent Confusion**: 500+ page technical docs overwhelm AI context windows
- **Raw Document Text = Garbled Responses**: AI gets lost in unstructured extraction noise
- **No Structure = No Intelligence**: Agents can't navigate, cross-reference, or cite specific sections
- **Format Lock-in = Limited Knowledge**: Critical information trapped in PDFs, Word docs, and other formats

### 🚀 **The Intelligent Solution**

- **Smart Chunking**: Breaks content into LLM-optimized pieces (3.5K, 8K, 32K, 100K token variants)
- **Concept Mapping**: Extracts and defines domain-specific terminology and relationships  
- **Multi-Level Summaries**: Executive, technical, and detailed summaries for different contexts
- **Section Navigation**: Hierarchical structure with cross-references and precise citations
- **Table Intelligence**: Structured JSON + markdown tables for data analysis
- **Visual Context**: Extracts and catalogs images with descriptions
- **Cross-Reference Resolution**: Maps internal document relationships and dependencies

### ⚡ **Agent Workflow Benefits**

**Before**: *"I can't analyze that 500-page API specification PDF"*  
**After**: *"I've analyzed the Visa Token Services API v37r25d03 documentation. Based on section 5.2.1, here's the authentication flow..."*

**Before**: *"I can't read Word documents"*  
**After**: *"I've processed your compliance report. The key requirements from section 3.4 are..."*

✅ **Intelligent Navigation**: Agents know exactly where to find information  
✅ **Precise Citations**: References specific files and sections, not vague summaries  
✅ **Context Awareness**: Understands document structure, relationships, and terminology  
✅ **Multi-Document Intelligence**: Cross-references between multiple converted documents  
✅ **Token Optimization**: Every file sized perfectly for agent context windows

### 📁 **What Gets Generated (Agent-Optimized Structure)**

```
docs/your_document_name/
├── structure-overview.md     # Navigation map with previews
├── README.md                # Quick start guide  
├── sections/                # Individual content sections
│   ├── 01-introduction.md   
│   ├── 02-authentication.md
│   └── ...
├── chunked/                 # Token-optimized pieces
│   ├── small/               # 3.5K tokens (GPT-3.5)
│   ├── medium/              # 8K tokens (GPT-4)  
│   ├── large/               # 32K tokens (GPT-4-32K)
│   └── xlarge/              # 100K tokens (Claude-2)
├── summaries/               # Multi-level summaries
│   ├── executive-summary.md
│   ├── technical-summary.md
│   └── detailed-summary.md
├── concepts/                # Domain intelligence
│   ├── glossary.md         # Key terms & definitions
│   ├── concept-map.md      # Relationships & dependencies
│   └── terminology.json    # Structured terminology
├── tables/                  # Structured data
│   ├── table-001.md        # Human-readable
│   ├── table-001.json      # Machine-readable
│   └── tables-index.md     # All tables catalog
├── references/              # Cross-reference intelligence
│   ├── internal-links.md   # Document cross-references
│   └── external-refs.md    # External links & citations
└── images/                  # Visual context
    ├── extracted-images/    # Actual image files
    └── image-catalog.md     # Descriptions & context
```

**Result**: Your agent gets a complete knowledge base, not just converted text.

## Quick Start

### 1. Install the MCP Server

```bash
git clone https://github.com/wadearnold/mcp-document-markdown.git
cd mcp-document-markdown
make setup    # Installs dependencies and runs tests
```

### 2. Get Configuration Paths

```bash
make run    # Shows command and args paths for your system
```

Copy the displayed paths for use in step 3.

### 3. Configure Your AI Assistant

Add the MCP server to your AI assistant using the paths from step 2. Choose your setup:

- 🔵 **[Claude Desktop](examples/claude-desktop.md)** - Anthropic's desktop app
- ⌨️ **[Claude Code](examples/claude-code.md)** - Anthropic's CLI tool  
- 🐙 **[GitHub Copilot](examples/github-copilot.md)** - GitHub's AI assistant
- 🎯 **[Cursor](examples/cursor.md)** - AI-powered code editor
- ⚙️ **[Generic MCP Setup](examples/generic-mcp.md)** - Other MCP clients

### 4. Convert Your First Document

Once configured, just ask your AI assistant:

**For PDFs:**
```
Convert the PDF at /path/to/my-documentation.pdf to markdown
```

**For Word Documents:**
```
Convert the Word document at /path/to/my-report.docx to markdown
```

Your AI will convert the document and create organized reference files it can use to help you.

### 5. Train Your AI Agent to Use the Documentation

After converting documents, **train your AI agent** to use the structured documentation effectively.

#### 📋 Get the Latest Agent Instructions:

**[→ AGENT_INSTRUCTIONS.md](https://github.com/wadearnold/mcp-document-markdown/blob/main/AGENT_INSTRUCTIONS.md)**

This file contains:
- ✅ **Copy-paste prompt** for your AI agent
- 🔧 **Customization guide** for your specific use case  
- 📚 **Explanation of the file structure** and how to navigate it
- 🔄 **Always up-to-date** with the latest converter features

## 🎯 Real-World Agent Use Cases

### 💳 **API Integration Projects**
**Problem**: "I need to integrate with Visa's Token Services API but the 285-page PDF is overwhelming"
**Solution**: Agent analyzes structured documentation, provides exact authentication steps, error codes, and implementation examples with precise file citations.

### 📋 **Compliance & Standards**
**Problem**: "Our team needs to understand GDPR requirements across 400+ pages of legal text"
**Solution**: Agent creates implementation checklists, cross-references related sections, and answers specific compliance questions with exact regulation citations.

### 🏗️ **Technical Architecture**
**Problem**: "I need to understand AWS's Well-Architected Framework across multiple 200+ page documents"
**Solution**: Agent builds cross-document knowledge, compares different architectural patterns, and provides implementation guidance citing specific sections.

### 🔬 **Research & Analysis**
**Problem**: "I need insights from 20+ academic papers, each 50+ pages long"
**Solution**: Agent synthesizes findings, identifies conflicting conclusions, and provides comprehensive analysis with precise source attribution.

### 🎯 **The Agent Intelligence Difference**

| **Without This Tool** | **With Agent Training** |
|---|---|
| *"I can't read PDFs"* | *"Based on section 4.2.1 of the API docs..."* |
| Generic, vague responses | Specific, cited, actionable answers |
| No cross-referencing | Intelligent multi-document analysis |
| Token limit errors | Perfect context window utilization |
| Manual PDF wrestling | Automated, structured intelligence |

## Two Workflows for Different Use Cases

Choose the workflow that matches your specific goal:

### 📁 Workflow 1: Reference Documentation (Direct Files)
**Goal**: Teach your AI assistant about a specific system or project

**Best for:**
- Creating reference material for a specific system/project
- When your AI needs to learn domain-specific terminology and concepts
- Building internal knowledge about APIs, frameworks, or tools
- Teaching your AI assistant about your project's architecture

```
PDF → Organized Markdown → Your AI learns the system → Answers questions with context
```

**Use cases:**
- API documentation for a service you're building with
- Technical specifications for a framework you're implementing
- Internal company documentation your AI needs to understand
- System architecture docs for a project you're working on

**Example**: 
```
Convert /path/to/stripe-api-docs.pdf to markdown, then help me integrate Stripe payments
```

**Result**: Your AI assistant gains knowledge about the specific system and can help you work with it using the converted documentation as reference material.

### 🔍 Workflow 2: Searchable Knowledge Base (RAG)
**Goal**: Enable semantic search across large document collections

**Best for:**
- Semantic search across large document collections
- Building chatbots or Q&A systems
- When you need to find information across hundreds of documents
- Customer support or help desk automation

```
PDF → Semantic Chunks → Vector Database → AI searches and finds relevant answers
```

**Use cases:**
- Company knowledge base with hundreds of policy documents
- Product documentation for customer support chatbots
- Research paper collections for academic search
- Legal document repositories for case research

**Example**:
```
Prepare /path/to/employee-handbook.pdf for RAG with vector database format chromadb
```

**Result**: The PDF content becomes searchable in a vector database, enabling your AI to find and retrieve relevant information automatically when users ask questions.

> **Note**: For RAG workflows, you don't need Step 4 (making your AI agent use the documentation) because the vector database MCP server handles the AI interaction automatically.

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


## Configuration

### Tool Parameters

#### PDF Tools

**PDF Conversion** (`convert_pdf`):
- `pdf_path` (required) - Path to your PDF
- `output_dir` (optional) - Where to save files (default: `./docs`)

**PDF Analysis** (`analyze_pdf_structure`):
- `pdf_path` (required) - Path to PDF to analyze

**RAG Preparation** (`prepare_pdf_for_rag`):
- `pdf_path` (required) - Path to your PDF  
- `vector_db_format` - Target database (`chromadb`, `pinecone`, `weaviate`, `qdrant`)
- `chunk_size` - Tokens per chunk (default: 768)
- `output_dir` - Where to save chunks (default: `./rag_output`)

#### Word Document Tools

**Word Conversion** (`convert_docx`):
- `docx_path` (required) - Path to your Word document (.docx)
- `output_dir` (optional) - Where to save files (default: `./docs`)

**Word Analysis** (`analyze_docx_structure`):
- `docx_path` (required) - Path to Word document to analyze

**Advanced Options** (available for both PDF and Word):
- `split_by_chapters` (default: true) - Organize by document structure
  - Enable: *"with chapter splitting"* or *"split by chapters"*
  - Disable: *"without chapter splitting"* or *"keep as single file"*
- `preserve_tables` (default: true) - Keep table formatting
  - Enable: *"preserve table formatting"* or *"keep tables structured"*
  - Disable: *"flatten tables to text"* or *"without table formatting"*
- `extract_images` (default: true) - Save referenced images
  - Enable: *"extract images"* or *"save images"*
  - Disable: *"without images"* or *"text only"*

## Examples

### PDF Examples

**Basic PDF Reference**
```
Convert the user manual at /docs/user-guide.pdf to markdown, then help me understand how to set up authentication
```

**API Documentation**  
```
Convert /docs/api-reference.pdf to markdown and help me write code that uses the user management endpoints
```

**Large PDF Processing**
```
Convert the 200-page technical specification at /specs/system-design.pdf to markdown with chapter splitting
```

### Word Document Examples

**Report Conversion**
```
Convert the compliance report at /docs/gdpr-compliance.docx to markdown
```

**Technical Documentation**
```
Convert /docs/architecture-design.docx to markdown and help me understand the system components
```

**Analysis Only**
```
Analyze the structure of /docs/proposal.docx without converting
```

### Custom Processing Options

**Without Images**
```
Convert /docs/report.pdf to markdown without images and flatten tables to text
```

**Quick Analysis**
```
Analyze the structure of /docs/specification.pdf
```

```
Convert /docs/manual.pdf to markdown without chapter splitting and preserve table formatting
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
- Python 3.8+

### Build from source
```bash
git clone https://github.com/wadearnold/mcp-document-markdown.git
cd mcp-document-markdown
make setup    # Installs dependencies and runs tests
```

### Run the server
```bash
make run    # Starts the Python MCP server and shows configuration paths
```

## License

Apache License 2.0
