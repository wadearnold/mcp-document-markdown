# Python Scripts for PDF Processing

This directory contains the Python scripts used by the MCP PDF Converter server.

## Files

- **`pdf_converter.py`** - Main PDF to Markdown conversion script
  - Combines multiple PDF processing libraries (PyMuPDF, pdfplumber, pypdf)
  - Handles text extraction, table preservation, and image extraction
  - Outputs structured markdown files

- **`pdf_analyzer.py`** - PDF structure analysis script
  - Analyzes PDF without converting
  - Returns metadata, page count, and structure information
  - Used by the `analyze_pdf_structure` MCP tool

## Development Workflow

### Editing Python Scripts

1. **Edit the Python files directly** in this directory
2. **Test your changes** without rebuilding the Go binary:
   ```bash
   make dev  # Runs server in development mode, loading Python from files
   ```

3. **Build the binary** when ready for production:
   ```bash
   make build  # Embeds Python scripts into the Go binary
   ```

### How It Works

- **Production**: Python scripts are embedded into the Go binary at compile time using Go's `embed` package
- **Development**: Set `PYTHON_SCRIPTS_DIR=./python` to load scripts from files instead of embedded data
- **Benefits**: 
  - Easy Python development with syntax highlighting
  - No need to rebuild for every Python change during development
  - Single binary distribution with embedded scripts

### Testing Python Changes

```bash
# Test with direct Python execution
python3 python/pdf_converter.py test.pdf ./output --preserve-tables

# Test with development server (loads from files)
make dev

# Test with production binary (embedded scripts)
make build && ./bin/mcp-pdf-server
```

### Python Dependencies

The scripts require these Python packages:
- `pypdf` - PDF structure and metadata
- `pdfplumber` - Table extraction
- `PyMuPDF` (fitz) - Text and image extraction
- `pandas` - Data processing
- `Pillow` - Image handling
- `tabulate` - Table formatting
- `markdown` - Markdown generation

Install with:
```bash
make install-python-deps
```

## Adding New Scripts

1. Create the new Python script in this directory
2. Add an embed directive in `python_embed.go`:
   ```go
   //go:embed python/your_script.py
   var yourScript string
   ```
3. Update `python_loader.go` if needed for development mode
4. Use the script in your Go code

## Important Notes

- **Do NOT delete `python_scripts.go`** until migration is complete
- Scripts are automatically embedded during `make build`
- Development mode requires Python scripts to be in this directory
- Production binary doesn't need Python files at runtime