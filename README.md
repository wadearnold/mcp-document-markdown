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
- `structured_tables` (default: true): Convert tables to structured JSON format with data type detection
- `generate_concept_map` (default: true): Generate concept map and glossary with technical terms and relationships
- `resolve_cross_references` (default: true): Detect and resolve cross-references to create navigable markdown links
- `generate_summaries` (default: true): Generate multi-level summaries for progressive disclosure and context optimization

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
├── tables/                         # Structured table data
│   ├── README.md                   # Tables index and processing guide
│   ├── table_01.md                 # Enhanced table with metadata
│   ├── table_01.json               # Structured JSON for LLM processing
│   └── table_02.md/.json           # Additional tables
├── concepts/                       # Concept map and glossary
│   ├── glossary.md                 # Human-readable technical glossary
│   ├── concept-map.md              # Network analysis and documentation
│   ├── concept-map.json            # Machine-readable concept relationships
│   ├── glossary.json               # Structured glossary for LLM processing
│   ├── visualization-data.json     # Graph visualization data
│   └── categories/                 # Category-specific glossaries
│       ├── index.md                # Category index
│       ├── api-concepts-glossary.md        # API terminology
│       ├── security-concepts-glossary.md   # Security terms
│       └── [category]-glossary.md          # Other domain glossaries
├── cross-references/               # Cross-reference resolution
│   ├── index.md                    # Navigation and cross-reference documentation
│   └── cross-references.json       # Machine-readable reference mapping
├── summaries/                      # Multi-level summaries
│   ├── index.md                    # Progressive disclosure index
│   ├── executive-summary.md        # Executive summary (~250 words)
│   ├── detailed-summary.md         # Detailed summary (~1000 words)
│   ├── complete-summary.md         # Complete summary (full context)
│   └── summaries-metadata.json     # Machine-readable summary metadata
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

# Disable structured tables
Convert the PDF at /path/to/document.pdf with structured_tables set to false

# Disable concept map generation
Convert the PDF at /path/to/document.pdf with generate_concept_map set to false

# Disable cross-reference resolution
Convert the PDF at /path/to/document.pdf with resolve_cross_references set to false

# Disable multi-level summaries
Convert the PDF at /path/to/document.pdf with generate_summaries set to false
```

#### Concept Map and Glossary Generation (NEW!)
Generate comprehensive concept maps and technical glossaries with relationship analysis:

```
docs/concepts/
├── glossary.md                 # Human-readable technical glossary
├── concept-map.md              # Network analysis and documentation  
├── concept-map.json            # Machine-readable concept relationships
├── glossary.json               # Structured glossary for LLM processing
├── visualization-data.json     # Graph visualization data
└── categories/                 # Category-specific glossaries
    ├── index.md                # Category index
    ├── api-concepts-glossary.md        # API terminology
    ├── security-concepts-glossary.md   # Security terms
    └── [category]-glossary.md          # Other domain glossaries
```

**Advanced Term Extraction:**
- **10 Technical Categories**: API, HTTP, security, database, programming, network, architecture, business, data, and process concepts
- **Frequency Analysis**: Importance scoring based on frequency, section types, and context relevance
- **Definition Extraction**: Automatic identification of concept definitions and explanations
- **Relationship Mapping**: Semantic clustering and hierarchical organization of related terms

**Concept Map Features:**
```json
{
  "nodes": [
    {
      "id": "authentication",
      "type": "concept",
      "category": "security_concepts",
      "importance": 8.5,
      "complexity": 7.2,
      "definitions": ["Process of verifying user identity..."],
      "related_terms": ["oauth", "jwt", "token"]
    }
  ],
  "edges": [
    {
      "source": "authentication",
      "target": "oauth", 
      "relationship_type": "implements",
      "strength": 0.85
    }
  ]
}
```

**Glossary Organization:**
- **Categorized Terms**: Organized by technical domain for targeted learning
- **Context Examples**: Real usage examples from the document for each term
- **Cross-References**: Links between related terms and concepts
- **Complexity Scoring**: Difficulty ratings to guide learning progression
- **Section Mapping**: Direct links to where terms are defined in the document

**LLM Integration Benefits:**
- **Vocabulary Building**: Comprehensive technical lexicon for domain understanding
- **Semantic Networks**: Relationship graphs for improved comprehension
- **Context Awareness**: Rich contextual information for accurate term usage
- **Knowledge Mapping**: Hierarchical concept organization for structured learning

**Control Options:**
Concept map generation is enabled by default but can be controlled:
```
# Enable concept map (default behavior)
Convert the PDF at /path/to/document.pdf to markdown

# Disable concept map generation
Convert the PDF at /path/to/document.pdf with generate_concept_map set to false
```

#### Cross-Reference Resolution (NEW!)
Automatically detect and resolve cross-references to create navigable, interconnected markdown documents:

```
docs/cross-references/
├── index.md                    # Navigation and cross-reference documentation
└── cross-references.json       # Machine-readable reference mapping
```

**Advanced Reference Detection:**
- **Page References**: "page 15", "see page 42", "(p. 23)" → Links to relevant sections
- **Figure References**: "Figure 3.1", "as shown in Figure 5" → Direct links with anchors
- **Table References**: "Table 2", "refer to Table 4.3" → Structured table navigation
- **Section References**: "see Section 2.1", "detailed in Chapter 5" → Cross-section linking
- **Equation References**: "Equation 7", "(Eq. 3.2)" → Mathematical content links
- **Code References**: "Listing 1", "Code Block 4" → Programming example navigation
- **Appendix References**: "Appendix A", "see Appendix C" → Supplementary content links
- **API References**: "GET /users", "POST /auth/login" → API endpoint documentation
- **Contextual References**: "above", "below", "previously mentioned" → Smart contextual linking

**Reference Resolution Features:**
```json
{
  "resolved_references": [
    {
      "original_text": "Figure 3.1",
      "link_text": "Figure 3.1",
      "link_url": "api-authentication.md#figure-3-1",
      "description": "Links to OAuth Flow Diagram",
      "confidence": 0.95,
      "source_section": "Authentication Methods"
    }
  ]
}
```

**Smart Link Generation:**
- **High-Confidence Linking**: Only references with ≥70% confidence are converted to avoid false positives
- **Contextual Accuracy**: Uses surrounding text and document structure for precise targeting
- **Anchor Generation**: Creates meaningful URL anchors for figures, tables, and sections
- **Fuzzy Matching**: Handles variations in reference styles and formatting
- **Alias Recognition**: Recognizes alternative names and acronyms for sections and concepts

**Navigation Benefits:**
- **Document Connectivity**: Transform isolated PDF sections into interconnected web of knowledge
- **LLM Navigation**: Enable AI models to follow logical document flow and relationships
- **Interactive Reading**: Create clickable references for improved user experience
- **Knowledge Mapping**: Build semantic connections between related content areas
- **Context Preservation**: Maintain document structure while enabling non-linear exploration

**Control Options:**
Cross-reference resolution is enabled by default but can be controlled:
```
# Enable cross-reference resolution (default behavior)
Convert the PDF at /path/to/document.pdf to markdown

# Disable cross-reference resolution
Convert the PDF at /path/to/document.pdf with resolve_cross_references set to false
```

#### Multi-Level Summaries (NEW!)
Generate progressive disclosure summaries optimized for different LLM context windows and use cases:

```
docs/summaries/
├── index.md                    # Progressive disclosure index
├── executive-summary.md        # Executive summary (~250 words)
├── detailed-summary.md         # Detailed summary (~1000 words)
├── complete-summary.md         # Complete summary (full context)
└── summaries-metadata.json     # Machine-readable summary metadata
```

**Three Summary Levels:**
- **🚀 Executive Summary (250 words)**: Quick decision making and initial understanding
- **📋 Detailed Summary (1000 words)**: Comprehensive understanding with key implementation details  
- **📖 Complete Summary (full context)**: Full context understanding with detailed navigation

**Advanced Document Analysis:**
- **Document Type Detection**: API documentation, technical manual, research paper, tutorial, legal document
- **Complexity Assessment**: Low/medium/high complexity scoring based on technical depth
- **Audience Detection**: Developers, business users, or general users based on content analysis
- **Priority Scoring**: Intelligent section prioritization for optimal content selection
- **Topic Extraction**: Key themes and concepts identification with frequency analysis

**Progressive Disclosure Features:**
```json
{
  "summary_levels": {
    "executive": {
      "word_count": 247,
      "target_audience": "executives",
      "reading_time": "1-2 minutes", 
      "optimization": "Quick overview for decision making"
    },
    "detailed": {
      "word_count": 987,
      "sections_covered": 8,
      "reading_time": "4-6 minutes",
      "optimization": "Comprehensive understanding with implementation details"
    },
    "complete": {
      "word_count": 2150,
      "sections_covered": 15,
      "reading_time": "10-15 minutes",
      "optimization": "Full context with navigation and statistics"
    }
  }
}
```

**Context Window Optimization:**
- **Limited Context (≤2K tokens)**: Use Executive Summary only
- **Medium Context (2K-5K tokens)**: Use Detailed Summary  
- **Large Context (≥5K tokens)**: Use Complete Summary
- **Progressive Analysis**: Start with Executive → Detailed → Complete as needed

**Intelligent Content Selection:**
- **Priority-Based**: Automatically selects most important sections based on content analysis
- **Audience-Specific**: Tailors tone and focus based on detected primary audience
- **Document-Aware**: Adapts summarization strategy based on document type (API docs, tutorials, etc.)
- **Complexity-Sensitive**: Adjusts detail level based on technical complexity assessment
- **Token-Conscious**: Precise token counting for optimal LLM context usage

**LLM Integration Benefits:**
- **Context Management**: Choose appropriate summary level based on available context window
- **Progressive Learning**: Enable drill-down exploration from high-level to detailed understanding
- **Decision Support**: Executive summaries enable quick project assessment and scoping
- **Implementation Planning**: Detailed summaries provide comprehensive technical review
- **Reference Documentation**: Complete summaries serve as navigable implementation guides

**Control Options:**
Multi-level summaries are enabled by default but can be controlled:
```
# Enable multi-level summaries (default behavior)
Convert the PDF at /path/to/document.pdf to markdown

# Disable summary generation
Convert the PDF at /path/to/document.pdf with generate_summaries set to false
```

#### Structured Table Conversion (NEW!)
Automatically converts tables to structured JSON format with intelligent data type detection:

```
docs/tables/
├── README.md                    # Tables index and processing guide
├── table_01.md                  # Enhanced markdown with metadata
├── table_01.json                # Structured JSON for LLM processing
└── table_02.md/.json            # Additional tables
```

**Advanced Data Type Detection:**
- **Numeric Values**: Automatic integer/float detection with summary statistics
- **Dates**: Recognition of common date formats (YYYY-MM-DD, MM/DD/YYYY, etc.)
- **URLs and Emails**: Automatic identification and classification
- **Boolean Values**: True/false, yes/no pattern recognition
- **Mixed Types**: Columns with multiple data types are analyzed and flagged

**Enhanced Table Documentation:**
Each table includes comprehensive metadata and analysis:
```markdown
---
title: Revenue Analysis Q4 2024
table_info:
  page: 15
  extracted_at: 2024-01-20T10:30:00
structure:
  rows: 12
  columns: 4
  column_names: ["Quarter", "Revenue", "Growth", "Region"]
data_types:
  "Revenue": {"integer": 12}
  "Growth": {"float": 12} 
  "Region": {"string": 12}
summary_stats:
  "Revenue": {"count": 12, "min": 150000, "max": 2500000, "avg": 875000}
---
```

**Processing Benefits:**
- **LLM Analysis**: Structured data ready for statistical analysis and insights
- **API Integration**: Direct JSON consumption for web applications
- **Data Visualization**: Clean, typed data for charts and graphs
- **Report Generation**: Automated summary statistics and data quality metrics
- **Machine Learning**: Properly formatted data for analysis pipelines

**Control Options:**
Structured table conversion is enabled by default but can be controlled:
```
# Enable structured tables (default behavior)
Convert the PDF at /path/to/document.pdf to markdown

# Disable structured tables
Convert the PDF at /path/to/document.pdf with structured_tables set to false
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
✅ **Structured Tables**: JSON conversion with data type detection and statistics
✅ **Workflow Optimization**: Processing notes guide LLMs on what to focus on
✅ **Batch API Processing**: Process related endpoints together for efficient integration
✅ **Code Generation Ready**: Complete endpoint info for automatic client generation
✅ **Cost Estimation**: Calculate API costs based on accurate token counts
✅ **Multi-Model Support**: Optimized chunks for GPT-3.5, GPT-4, GPT-4-32K, and Claude
✅ **Data Analysis Ready**: Structured table data for statistical analysis and visualization

Each file is optimized for LLM processing and includes:
- Clean markdown formatting with semantic structure
- Preserved table structure  
- Referenced images with context
- Comprehensive metadata for intelligent processing
- Semantic tags and processing guidance
- API endpoint extraction and classification
- Processing priority for workflow optimization

## 🔀 Two Workflows: Direct LLM vs RAG Pipeline

This MCP server provides **two distinct tools** for different use cases:

### Workflow A: Direct LLM Consumption (`convert_pdf`)
**Best for:** Interactive AI conversations, document analysis, code review
```
PDF → Organized Markdown Files → Feed to Claude/GPT-4 → Get Answers
```

**Use this when you want to:**
- Have a conversation about a document with an AI assistant
- Navigate through chapters and sections manually
- Work with human-readable markdown files
- Leverage cross-references and summaries
- Process documents incrementally

**Example:**
```
Convert the PDF at /path/to/manual.pdf to markdown, then help me understand Chapter 3
```

### Workflow B: RAG/Vector Database Pipeline (`prepare_pdf_for_rag`)
**Best for:** Semantic search, knowledge bases, automated Q&A systems
```
PDF → Semantic Chunks → Vector Database → Similarity Search → Retrieved Context
```

**Use this when you want to:**
- Build a searchable knowledge base
- Enable semantic search across documents
- Create automated Q&A systems
- Scale to hundreds of documents
- Use with LangChain, LlamaIndex, or custom RAG pipelines

**Example:**
```
Prepare the PDF at /path/to/docs.pdf for RAG with vector database format chromadb
```

## 📚 RAG and Vector Database Integration

The `prepare_pdf_for_rag` tool creates optimized chunks for vector databases with rich metadata for hybrid search.

### What You Get with RAG Preparation

```
rag_output/
├── chunks.json                 # Semantic chunks with metadata
├── chromadb_format.json        # Ready for ChromaDB import
├── metadata.json               # Document-level metadata
└── import_instructions.md      # Complete import guide with code
```

### Chunk Structure
Each chunk is optimized for embedding models:
```json
{
  "chunk_id": "doc_abc123_chunk_0001",
  "text": "Semantic chunk content...",
  "metadata": {
    "doc_id": "abc123",
    "source_pages": [1, 2],
    "token_count": 487,
    "keywords": ["API", "authentication", "OAuth"],
    "quality_score": 0.92,
    "content_type": "technical"
  }
}
```

### Quick Import Examples

#### ChromaDB (Local Vector Database)
```python
import chromadb
import json
from chromadb.utils import embedding_functions

# Load prepared chunks
with open('chromadb_format.json', 'r') as f:
    data = json.load(f)

# Create ChromaDB client
client = chromadb.PersistentClient(path="./chroma_db")

# Create collection with OpenAI embeddings
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-api-key",
    model_name="text-embedding-ada-002"
)

collection = client.create_collection(
    name=data['collection_name'],
    embedding_function=openai_ef
)

# Add documents
collection.add(
    ids=data['ids'],
    documents=data['documents'],
    metadatas=data['metadatas']
)

# Query example
results = collection.query(
    query_texts=["How does authentication work?"],
    n_results=5
)
```

#### Pinecone (Cloud Vector Database)
```python
import pinecone
import json
from openai import OpenAI

# Initialize
pinecone.init(api_key="your-pinecone-key")
index = pinecone.Index("your-index")
openai_client = OpenAI(api_key="your-openai-key")

# Load prepared chunks
with open('pinecone_format.json', 'r') as f:
    data = json.load(f)

# Generate embeddings and upsert
for vector in data['vectors']:
    # Generate embedding
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=vector['metadata']['text']
    )
    vector['values'] = response.data[0].embedding
    
    # Upsert to Pinecone
    index.upsert(vectors=[vector], namespace=data['namespace'])

# Query example
query_embedding = openai_client.embeddings.create(
    model="text-embedding-ada-002",
    input="authentication process"
).data[0].embedding

results = index.query(
    vector=query_embedding,
    top_k=5,
    namespace=data['namespace'],
    include_metadata=True
)
```

#### Weaviate (Self-Hosted or Cloud)
```python
import weaviate
import json

# Connect to Weaviate
client = weaviate.Client(
    url="http://localhost:8080",
    additional_headers={"X-OpenAI-Api-Key": "your-key"}
)

# Load prepared chunks
with open('weaviate_format.json', 'r') as f:
    data = json.load(f)

# Create schema
client.schema.create_class({
    "class": "DocumentChunk",
    "vectorizer": "text2vec-openai",
    "properties": [
        {"name": "content", "dataType": ["text"]},
        {"name": "docId", "dataType": ["string"]},
        {"name": "sourcePages", "dataType": ["int[]"]},
        {"name": "keywords", "dataType": ["string[]"]},
    ]
})

# Import data
client.batch.configure(batch_size=100)
with client.batch as batch:
    for obj in data['objects']:
        batch.add_data_object(
            obj['properties'],
            class_name="DocumentChunk"
        )

# Query example
result = client.query.get(
    "DocumentChunk", 
    ["content", "sourcePages", "keywords"]
).with_near_text({
    "concepts": ["API authentication"]
}).with_limit(5).do()
```

#### Qdrant (Self-Hosted or Cloud)
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import json
from openai import OpenAI

# Initialize clients
qdrant = QdrantClient("localhost", port=6333)
openai_client = OpenAI(api_key="your-key")

# Load prepared chunks
with open('qdrant_format.json', 'r') as f:
    data = json.load(f)

# Create collection
qdrant.recreate_collection(
    collection_name=data['collection_name'],
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# Generate embeddings and upload
points = []
for point in data['points']:
    # Generate embedding
    embedding = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=point['payload']['text']
    ).data[0].embedding
    
    points.append(PointStruct(
        id=point['id'],
        vector=embedding,
        payload=point['payload']
    ))

qdrant.upsert(
    collection_name=data['collection_name'],
    points=points
)

# Search example
query_vector = openai_client.embeddings.create(
    model="text-embedding-ada-002",
    input="How to authenticate API requests?"
).data[0].embedding

search_result = qdrant.search(
    collection_name=data['collection_name'],
    query_vector=query_vector,
    limit=5
)
```

### Integration with LangChain

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import json

# Load the prepared chunks
with open('chromadb_format.json', 'r') as f:
    data = json.load(f)

# Create vector store from prepared chunks
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_texts(
    texts=data['documents'],
    metadatas=data['metadatas'],
    embedding=embeddings,
    collection_name=data['collection_name']
)

# Create QA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(temperature=0),
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
)

# Query
response = qa_chain.run("What are the authentication requirements?")
```

### RAG Tool Parameters

The `prepare_pdf_for_rag` tool accepts:
- **`pdf_path`** (required): Path to the PDF file
- **`output_dir`**: Where to save chunks (default: `./rag_output`)
- **`chunk_size`**: Target tokens per chunk (default: 768)
- **`chunk_overlap`**: Token overlap between chunks (default: 128)
- **`vector_db_format`**: Target database format (`generic`, `pinecone`, `chromadb`, `weaviate`, `qdrant`)
- **`embedding_model`**: Target embedding model for optimization

### Best Practices for RAG

1. **Chunk Size**: 
   - 512-768 tokens for most embedding models
   - 256 tokens for dense retrieval
   - 1024 tokens for newer models like `text-embedding-3`

2. **Overlap Strategy**:
   - 10-20% overlap maintains context
   - Higher overlap for technical documents
   - Lower overlap for narrative content

3. **Metadata Usage**:
   - Filter by `quality_score` for better results
   - Use `keywords` for hybrid search
   - Track `source_pages` for citations

4. **Indexing Strategy**:
   - Separate namespaces/collections per document type
   - Use metadata filters for targeted search
   - Implement hybrid search (semantic + keyword)

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

### Working with Structured Table Data

```python
import json
import glob
import pandas as pd

# Load all structured tables
table_files = glob.glob('docs/tables/*.json')
all_tables = []
for file in table_files:
    with open(file) as f:
        table_data = json.load(f)
        all_tables.append(table_data)

# Analyze table structures
for table in all_tables:
    meta = table['metadata']
    print(f"Table: {meta['title']}")
    print(f"Size: {meta['structure']['rows']}x{meta['structure']['columns']}")
    print(f"Columns: {meta['structure']['column_names']}")
    
    # Check for numeric columns with statistics
    if meta['summary_stats']:
        print("Numeric columns with statistics:")
        for col, stats in meta['summary_stats'].items():
            print(f"  {col}: avg={stats['avg']:.2f}, range={stats['min']}-{stats['max']}")

# Convert table to pandas DataFrame for analysis
def load_table_as_dataframe(table_data):
    """Convert structured table data to pandas DataFrame"""
    rows = table_data['data']
    if not rows:
        return pd.DataFrame()
    
    # Create DataFrame from structured data
    df = pd.DataFrame(rows)
    
    # Apply data type conversion based on metadata
    data_types = table_data['metadata']['data_types']
    for col, type_info in data_types.items():
        if col in df.columns:
            primary_type = max(type_info.items(), key=lambda x: x[1])[0]
            if primary_type == 'integer':
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            elif primary_type == 'float':
                df[col] = pd.to_numeric(df[col], errors='coerce')
            elif primary_type == 'date':
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df

# Example: Load and analyze a specific table
if all_tables:
    first_table = all_tables[0]
    df = load_table_as_dataframe(first_table)
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Data types:\n{df.dtypes}")
    print(f"\nSample data:\n{df.head()}")
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
- **`structured_tables`** (default: true): Whether to convert tables to structured JSON format

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
