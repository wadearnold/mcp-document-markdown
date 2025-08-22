# Modular PDF Converter - Python Implementation

This directory contains the modular Python implementation of the MCP PDF to Markdown converter.

## Architecture

The converter is built with a modular architecture for better maintainability and testing:

### Core Components

- **`modular_pdf_converter.py`** - Main orchestrator that coordinates all processing steps
- **`pdf_analyzer.py`** - Analyzes PDF structure and metadata
- **`pdf_to_rag.py`** - Prepares PDFs for RAG (Retrieval Augmented Generation) workflows

### Utility Modules (`utils/`)

- **`token_counter.py`** - Token counting for LLM context optimization
- **`text_utils.py`** - Text cleaning and processing utilities  
- **`file_utils.py`** - File system operations and path management

### Processing Modules (`processors/`)

- **`pdf_extractor.py`** - Multi-library PDF content extraction
- **`table_processor.py`** - Table detection, extraction and formatting
- **`chunking_engine.py`** - Intelligent text chunking for optimal context windows
- **`concept_mapper.py`** - Concept extraction and glossary generation
- **`cross_referencer.py`** - Reference resolution and linking
- **`summary_generator.py`** - Multi-level summary generation

## Testing

The test suite focuses on integration testing and import validation:

```bash
# Run all tests
make test

# Run tests directly
cd python && ../venv/bin/python -m unittest discover tests -v
```

### Test Structure

```
tests/
├── test_essentials.py     # Core functionality and integration tests
└── README.md              # Testing documentation
```

## Usage

### Via MCP Server

The primary way to use this system is through the MCP server:

```bash
# Start the server
make run

# The server provides these tools:
# - convert_pdf: Convert PDF to structured markdown
# - analyze_pdf_structure: Analyze PDF metadata and structure  
# - prepare_pdf_for_rag: Prepare PDF for vector database integration
```

### Direct Python Usage

You can also use the converter directly:

```bash
# Convert a PDF
python3 modular_pdf_converter.py input.pdf ./output/

# Analyze PDF structure
python3 pdf_analyzer.py input.pdf

# Prepare for RAG
python3 pdf_to_rag.py input.pdf --format chromadb
```

## Dependencies

All dependencies are managed through `requirements.txt`:

- **PDF Processing**: `pypdf`, `pdfplumber`, `PyMuPDF`
- **Data Processing**: `pandas`, `numpy`
- **MCP Server**: `mcp`
- **Optional**: `tiktoken` (for accurate token counting)

Install with:
```bash
make setup    # Installs dependencies and runs tests
```

## Key Features

- **Multi-library PDF extraction** for maximum compatibility
- **Intelligent table preservation** with multiple output formats
- **Token-aware chunking** for LLM context optimization
- **Concept mapping** with automatic glossary generation
- **Cross-reference resolution** for better document navigation
- **Multi-level summarization** (executive, detailed, complete)
- **RAG preparation** for vector database integration

## Output Structure

The converter creates well-organized documentation:

```
docs/
├── index.md                 # Main navigation
├── summary.md               # Document overview
├── sections/                # Content by chapter/topic
├── concepts/glossary.md     # Term definitions
├── summaries/               # Multi-level summaries
├── tables/                  # Structured data
└── images/                  # Extracted images
```

For RAG workflows:
```
rag_output/
├── chunks.json              # Semantic chunks with metadata
├── chromadb_format.json     # ChromaDB-ready format
├── pinecone_format.json     # Pinecone-ready format
└── import_instructions.md   # Setup guide
```