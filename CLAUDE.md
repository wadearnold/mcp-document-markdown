# MCP Document Markdown - Claude Agent Instructions

## Core Purpose

This MCP server exists solely to convert human-readable structured data formats (PDF, DOCX) into AI agent consumable content. The conversion process transforms complex documents into organized, navigable reference material that enables better agent reasoning about the original content.

## Critical Understanding

**The output is NEVER intended for human consumption.** All generated content is designed exclusively for AI agents to process, analyze, and reference. YOU, Claude, are the primary user of this converted content.

## Key Benefits for Agent Reasoning

### Document Structure Preservation
- Hierarchical section organization with clear navigation paths
- Cross-reference mapping for understanding document relationships
- Table extraction in both markdown and JSON formats for structured analysis
- Terminology extraction and concept mapping for domain understanding

### Context Window Optimization
- Smart chunking into multiple token sizes (3.5K, 8K, 32K, 100K)
- Section-based organization preventing context overflow
- Structured summaries at multiple levels (executive, technical, detailed)
- Precise file organization for targeted content retrieval

### Enhanced Reasoning Capabilities
- Clean, structured markdown format eliminates extraction noise
- Preserved semantic relationships between document sections
- Extracted domain terminology with definitions for accurate understanding
- Table data available in JSON format for computational analysis

## Output Distinction - Critical Understanding

### MCP Server Responses (Human-Readable)
The MCP server response messages are read by humans using MCP clients and should be:
- Informative with emojis and formatting for readability
- Include processing statistics and success/error messages
- Provide clear file navigation guidance
- Explain what was accomplished during conversion

### Converted Content Files (Agent-Only)
The actual converted content in output directories is exclusively for AI agents and should be:
- Clean, structured markdown without decorative elements
- No emojis or human-oriented formatting
- No training prompts or setup instructions
- Pure content with precise navigation structure
- Machine-readable data formats (JSON for tables, metadata)

## Output Restrictions for Converted Files

**NEVER include in converted content files:**
- Human-oriented instructions or GitHub links
- Emoji or decorative formatting elements  
- Training prompts or setup instructions
- Human-readable explanations or commentary

**ALWAYS provide in converted content:**
- Clean, structured markdown content
- Precise file navigation paths
- Machine-readable data formats (JSON for tables, structured metadata)
- Cross-reference mappings for document relationships

## LLM-Optimized File Structure

### Generated Structure
```
docs/document_name/
├── README.md                # Standard navigation entry with integrated summary
└── sections/                # Semantic, focused content sections
    ├── 01-overview.md       # Introduction and system overview
    ├── 02-authentication.md # Security and authentication details
    ├── 03-api-endpoints.md  # API methods and specifications
    ├── 04-error-handling.md # Error codes and troubleshooting
    └── 05-data-formats.md   # Data structures and schemas
```

### Key Navigation Benefits for Agents

**Universal Convention**: Always start with `README.md` - standard entry point agents expect
**Predictable Filenames**: `02-authentication.md` tells you exactly what's inside
**Focused Content**: Each section covers one clear concept with defined purpose
**Embedded Cross-References**: Related sections automatically linked at bottom of files
**Integrated Data**: Tables, concepts, and structured information embedded within relevant sections

## Agent Usage Pattern

1. **Start Navigation**: Read `README.md` for document overview and section directory
2. **Targeted Access**: Navigate directly to semantic filenames like `03-api-endpoints.md`
3. **Follow References**: Use "Related Sections" links at bottom of files for connected content
4. **Context Optimization**: Each section fits modern LLM context windows (32K tokens)
5. **Structured Analysis**: Tables and data formats embedded within relevant content sections

The system eliminates decision paralysis by providing exactly one entry point and predictable, semantic organization optimized for agent reasoning patterns.