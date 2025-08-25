# Repository Rename Strategy: pdf-markdown → document-markdown

## Overview
With the addition of Microsoft Word support, the repository name should reflect its multi-format capabilities.

## Proposed Changes

### 1. Repository Name
- **Current**: `mcp-pdf-markdown`
- **Proposed**: `mcp-document-markdown` or `mcp-doc-markdown`

### 2. MCP Server Name
- **Current**: `pdf-markdown`
- **Proposed**: `document-markdown` ✅ (Already updated in code)

### 3. File/Module Names to Update
- [ ] Main server file: Keep as `mcp_pdf_markdown.py` for backward compatibility OR rename to `mcp_document_markdown.py`
- [ ] Configuration examples in `examples/` directory
- [ ] References in documentation

### 4. Documentation Updates Required

#### README.md
- [ ] Update title and description
- [ ] Add Word document examples
- [ ] Update feature list
- [ ] Add supported formats section

#### AGENT_INSTRUCTIONS.md
- [ ] Update references to support both PDFs and Word documents
- [ ] Add Word-specific guidance

#### Examples Directory
- [ ] Update all example configurations with new server name
- [ ] Add Word document conversion examples

### 5. Backward Compatibility Considerations

#### Option A: Breaking Change (Clean)
- Rename everything to `document-markdown`
- Users must update their configurations
- Clear messaging about the change

#### Option B: Graceful Migration (Recommended)
- Keep `mcp_pdf_markdown.py` as the main file
- Server identifies as `document-markdown` internally
- Support both old and new tool names temporarily
- Add deprecation notices for PDF-only tools

### 6. GitHub Repository Rename Process

1. **Update Documentation First**
   - Merge Word support to main
   - Update all documentation with multi-format support
   - Add migration guide

2. **GitHub Settings**
   - Go to Settings → General
   - Rename repository to `mcp-document-markdown`
   - GitHub automatically creates redirects from old name

3. **Post-Rename Updates**
   - Update clone URLs in documentation
   - Update any CI/CD references
   - Notify users via README and releases

### 7. Supported Formats Roadmap

Current:
- ✅ PDF (.pdf)
- ✅ Word (.docx)

Future Considerations:
- [ ] PowerPoint (.pptx) - markitdown supports this
- [ ] Excel (.xlsx) - markitdown supports this  
- [ ] HTML (.html) - markitdown supports this
- [ ] Plain text (.txt, .md)
- [ ] RTF (.rtf)

### 8. Recommended Timeline

1. **Phase 1** (Current Branch)
   - ✅ Add Word support functionality
   - ✅ Update server name internally
   - Document the changes

2. **Phase 2** (Before Merge)
   - Update all documentation
   - Create migration guide
   - Test with both formats

3. **Phase 3** (After Merge)
   - Announce multi-format support
   - Consider repository rename
   - Plan additional format support

## Decision Points

1. **Repository Name**: Should we rename now or wait for more formats?
2. **Main File Name**: Keep `mcp_pdf_markdown.py` or rename to `mcp_document_markdown.py`?
3. **Tool Naming**: Keep separate `convert_pdf`/`convert_docx` or unified `convert_document`?
4. **Migration Path**: How long to maintain backward compatibility?

## Recommendation

Keep the current repository name for now (`mcp-pdf-markdown`) but:
1. Document that it supports multiple formats
2. Update README title to "MCP Document to Markdown Converter"
3. Keep separate tools for each format for clarity
4. Plan repository rename for v2.0 release with more formats