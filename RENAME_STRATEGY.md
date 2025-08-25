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
- ✅ Main server file: Renamed to `mcp_document_markdown.py` for consistency
- ✅ Configuration examples in `examples/` directory
- ✅ References in documentation

### 4. Documentation Updates Required

#### README.md
- ✅ Update title and description
- ✅ Add Word document examples
- ✅ Update feature list
- ✅ Add supported formats section

#### AGENT_INSTRUCTIONS.md
- ✅ Update references to support both PDFs and Word documents
- ✅ Add Word-specific guidance

#### Examples Directory
- ✅ Update all example configurations with new server name
- ✅ Add Word document conversion examples

### 5. Backward Compatibility Considerations

#### Option A: Breaking Change (Clean)
- Rename everything to `document-markdown`
- Users must update their configurations
- Clear messaging about the change

#### Option B: Graceful Migration (Recommended)
- Renamed to `mcp_document_markdown.py` for consistency
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
2. **Main File Name**: ✅ Renamed to `mcp_document_markdown.py` for consistency
3. **Tool Naming**: Keep separate `convert_pdf`/`convert_docx` or unified `convert_document`?
4. **Migration Path**: How long to maintain backward compatibility?

## Status: Ready for Repository Rename! 🎉

### ✅ **ALL PREPARATION TASKS COMPLETED**

**Phase 1**: ✅ Add Word support functionality
**Phase 2**: ✅ Update all documentation and examples  
**Phase 3**: ✅ Server renamed and tested

### What We've Accomplished:
- ✅ Server identity changed to `document-markdown`
- ✅ Main file renamed to `mcp_document_markdown.py`
- ✅ All documentation updated for multi-format support
- ✅ All example configurations use new server name
- ✅ README showcases document intelligence value proposition
- ✅ Agent training instructions support both PDF and Word
- ✅ All tests passing with renamed server
- ✅ Word document support fully implemented and tested

### Repository Rename Decision:

**Original Recommendation**: Keep `mcp-pdf-markdown` and wait for v2.0

**Current Status**: Ready to rename to `mcp-document-markdown` now because:
1. ✅ All breaking changes are complete and tested
2. ✅ Documentation accurately reflects multi-format capabilities  
3. ✅ Server architecture supports easy addition of new formats
4. ✅ Users will need to update configurations anyway (server name changed)
5. ✅ Clean break is better than maintaining legacy naming

### Next Step: GitHub Repository Rename
Ready to execute the repository rename process described in section 6.