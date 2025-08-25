# Why I Built an MCP Server to Turn Documents into Agent-Ready Intelligence

The first open source payments library I ever created was [Moov ACH](https://github.com/moov-io/ach). I spent countless hours buried in the 480-page NACHA Operating Rules & Guidelines, studying every page, rule, and layout table to understand all the nuances of ACH processing. I literally had Appendix 3 printed out and highlighted with different colored highlighters to show what areas were different for each SEC code and what sections were shared across all Entry Detail records. It was time-consuming, tedious, and frankly mind-numbing work to figure out.

That's probably why most of modern fintech leverages our OSS projects today – nobody wants to spend months deciphering payment specs by hand!

## Five Years Later, Same Problem

Five years later, Moov is much different, except that we still deal with Word docs and PDFs prevailing when writing code to connect payment systems. Each update or new integrated service – from Visa to The Clearing House – still has all the relevant information highly organized in these documents. Unfortunately, these documents were built for HUMANS and not for computers... and really not for LLMs.

Whether it's the latest Visa Token Services API specification (285 pages of pure joy), network tokenization updates, or compliance documentation, the pattern is always the same: critical technical information locked away in formats that make our AI agents cry.

## The Breaking Point

Over the past six months, I've iterated on Python scripts and best practices to translate these documents into something that agents like Claude Code can easily ingest and reason with. What started as a simple "let me convert this PDF" script evolved into a sophisticated document processing pipeline.

The breaking point came when I was working on network token services integration. Here I was, once again highlighting and cross-referencing a massive technical specification, when I realized: *I'm doing the same tedious work I did five years ago with NACHA rules, just with different documents.*

That's when I decided to solve this problem once and for all.

## Introducing MCP Document-to-Markdown

This culminated into an MCP (Model Context Protocol) server that handles the tedious task of transforming human-readable documentation into AI-agent-ready intelligence. But this isn't just another PDF-to-text converter – it's a complete document intelligence system designed specifically for modern AI workflows.

### What Makes It Different

**Smart Chunking**: Automatically breaks content into LLM-optimized pieces (3.5K, 8K, 32K, 100K token variants) so your agents never hit context limits.

**Concept Mapping**: Extracts and defines domain-specific terminology. No more agents getting confused by "ACH" vs "Automated Clearing House" vs "Same Day ACH."

**Intelligent Structure**: Creates hierarchical navigation with cross-references and precise citations. Your agent can say "Based on section 5.2.1 of the API specification..." instead of vague references.

**Multi-Level Summaries**: Generates executive, technical, and detailed summaries for different contexts. Sometimes you need the 30-second version, sometimes you need every edge case.

**Table Intelligence**: Converts tables to both markdown and structured JSON. Because financial specs are full of rate tables, field definitions, and compliance matrices.

### The Agent Workflow Revolution

Before this tool:
- *"I can't analyze that 500-page API specification"*
- Generic, vague responses
- No cross-referencing capability  
- Manual PDF wrestling

After:
- *"I've analyzed the Visa Token Services API v37r25d03 documentation. Based on section 5.2.1, here's the authentication flow..."*
- Specific, cited, actionable answers
- Intelligent multi-document analysis
- Perfect context window utilization

## Supported Formats

Currently handles:
- **PDFs** (.pdf) - Technical specs, API documentation, compliance guides
- **Microsoft Word** (.docx) - Reports, proposals, internal documentation


## Real-World Impact

I hate to think how much time I would have saved when I was writing Moov ACH with this tool. Instead of weeks highlighting Appendix 3, I could have had my agent analyze the entire NACHA rulebook and immediately answer questions like:

- "What are the validation rules for CCD entries?"
- "How do return codes differ between PPD and WEB transactions?"  
- "What changed in the 2023 Operating Rules update?"

Alas, network token services just changed from ISO8583 to REST-ish, so never fear – mcp-document-markdown is here for the next generation of payment system integrations!

## Why Open Source This?

Nothing is better for software development than lots of edge cases, and financial documentation is basically edge cases all the way down. That's one of the reasons we open source so much code at Moov – the documents aren't always right, implementations vary, and the community finds bugs we'd never catch on our own.

More importantly, every developer who's ever stared at a massive technical specification and thought "there has to be a better way" deserves access to tools that make their AI agents actually useful for document analysis.

## Two Workflows for Different Use Cases

The MCP server supports two distinct workflows, each optimized for different scenarios:

### 📁 **Reference Documentation Workflow**
**Best for**: API specifications, technical documentation, system architecture guides

**How it works**: Convert documents into structured markdown files that your AI agent learns and references directly. Perfect when you need your agent to become an expert on a specific system or project.

**Example**: Converting Visa's Token Services API documentation so your agent can help you implement payment tokenization with precise section references.

### 🔍 **RAG Knowledge Base Workflow** 
**Best for**: Compliance documentation, policy collections, research paper libraries

**How it works**: Prepare documents for semantic search in vector databases like ChromaDB or Pinecone. Ideal for finding information across hundreds of documents or building Q&A systems.

**Example**: Processing GDPR compliance documents so your agent can instantly find relevant regulations when you ask "What are the data retention requirements for EU customers?"

## Get Started in 4 Steps

### 1. Clone and Setup
```bash
git clone https://github.com/wadearnold/mcp-document-markdown.git
cd mcp-document-markdown
make setup
```

### 2. Add to Your AI Agent
Connect the MCP server to your agent (Claude Code, Claude Desktop, etc.):
```bash
make run  # Shows exact configuration paths for your system
```
Then add to Claude Code:
```bash
claude mcp add document-markdown -- "/path/to/python" "/path/to/mcp_document_markdown.py"
```

### 3. Convert Your Documents
For specifications and technical docs:
```
Convert the PDF at /path/to/api-specification.pdf to markdown
```

For RAG/knowledge base setup:
```
Prepare /path/to/compliance-docs.pdf for RAG with vector database format chromadb
```

### 4. Train Your Agent
Crucial step: Tell your agent how to use the new structured documentation. The conversion creates files, but training creates intelligence.

**[→ Full setup guide and agent training instructions](https://github.com/wadearnold/mcp-document-markdown#quick-start)**

*This is test setup, not a tutorial – check the README for detailed configuration examples for different AI agents.*

### What do I get? 
```bash
 📋 DOCUMENTATION ANALYSIS COMPLETE

  I have successfully analyzed and memorized the Visa Token Services Issuer API Specifications documentation. Here is my comprehensive summary:

  🎯 Document Identity

  - Title: Visa Token Services Issuer API Specifications (REST JSON)
  - Version: V37r25d03
  - Type: Technical API documentation for financial services
  - Pages: 285 pages with 3 images and 38 structured tables
  - Generated Files: 2,019 organized markdown files

  📚 Key Topics Covered

  1. REST API Operations - Token provisioning, lifecycle management, inquiries
  2. Security & Encryption - JWE/JWS implementation, certificates, authentication
  3. Token Lifecycle Management - PAN replacement, token states, lifecycle actions
  4. Inbound APIs (To Visa) - Issuer-initiated operations and requests
  5. Outbound APIs (From Visa) - Visa-initiated notifications and responses
  6. Card Enrollment Hub (VCEH) - Push enrollment workflows and metadata updates
  7. Error Handling - Comprehensive error codes, response structures, business errors

  🔧 Technical Components

  - Chapters: 9 main chapters covering onboarding through performance targets
  - API Endpoints: Detailed specifications for inbound/outbound operations
  - Data Structures: Encrypted payload formats, device information, cardholder data
  - Sample Payloads: Request/response examples throughout documentation
  - Security Requirements: Certificate management, encryption protocols

  🚀 When to Reference This Documentation

  - Token-related operations in payment processing systems
  - Visa API integration questions and implementation
  - Security and encryption requirements for financial APIs
  - Error troubleshooting for Visa Token Service implementations
  - Card provisioning and lifecycle management queries

  📂 Navigation Structure

  - Primary Files: structure-overview.md, README.md
  - Content Directories: sections/ (384 files), chunked/ (LLM-optimized), tables/ (structured data)
  - Reference Materials: concepts/, summaries/, references/
  - Key Identifiers: Version V37r25d03, confidential Visa specifications
  ```

## The Future of Documentation-Driven Development

As AI agents become more sophisticated, the bottleneck isn't going to be the agents themselves – it's going to be getting them the right information in the right format. Technical documentation isn't going away, but our ability to make it useful for AI-assisted development is finally catching up.

Whether you're integrating payment systems, analyzing compliance requirements, or just trying to understand that massive API specification your vendor sent over, your agents deserve better than raw PDF text dumps.

They deserve intelligence. They deserve structure. They deserve documents that were designed for the future of software development.

**Ready to stop highlighting PDFs and start building?** Check out [mcp-document-markdown](https://github.com/wadearnold/mcp-document-markdown) and let your agents do what they do best – help you write better code.

---

*Wade Arnold is the founder of [Moov](https://moov.io), where he's spent the last five years building open source financial infrastructure. When he's not deciphering payment specifications or writing Go code, he's probably thinking about how to make complex financial systems more accessible to developers.*