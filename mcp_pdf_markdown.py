#!/usr/bin/env python3
"""
MCP PDF to Markdown Server
Python-based Model Context Protocol server for PDF to Markdown conversion.
"""
import asyncio
import json
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import traceback

# Add the python directory to the path for module imports
sys.path.insert(0, str(Path(__file__).parent / "python"))

from modular_pdf_converter import ModularPDFConverter
from pdf_analyzer import analyze_pdf
from pdf_to_rag import PDFToRAGProcessor

# MCP imports
try:
    from mcp.server import Server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolResult,
        ListToolsResult,
    )
    import mcp.server.stdio
except ImportError:
    print("Error: MCP library not found. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the MCP server
app = Server("pdf-markdown")

@app.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools for PDF processing"""
    return ListToolsResult(
        tools=[
            Tool(
                name="convert_pdf",
                description="Convert PDF to organized markdown documentation with advanced features",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF file to convert"
                        },
                        "output_dir": {
                            "type": "string", 
                            "description": "Directory to save converted files (default: ./docs)",
                            "default": "./docs"
                        },
                        "split_by_chapters": {
                            "type": "boolean",
                            "description": "Organize content by document structure (default: true)",
                            "default": True
                        },
                        "preserve_tables": {
                            "type": "boolean", 
                            "description": "Keep table formatting (default: true)",
                            "default": True
                        },
                        "extract_images": {
                            "type": "boolean",
                            "description": "Extract and save referenced images (default: true)", 
                            "default": True
                        },
                        "generate_summaries": {
                            "type": "boolean",
                            "description": "Generate multi-level summaries (default: true)",
                            "default": True
                        },
                        "generate_concept_map": {
                            "type": "boolean",
                            "description": "Generate concept map and glossary (default: true)",
                            "default": True
                        },
                        "resolve_cross_references": {
                            "type": "boolean", 
                            "description": "Resolve cross-references and create links (default: true)",
                            "default": True
                        },
                        "structured_tables": {
                            "type": "boolean",
                            "description": "Convert tables to structured JSON (default: true)",
                            "default": True
                        },
                        "enable_chunking": {
                            "type": "boolean",
                            "description": "Enable smart chunking for LLM optimization (default: true)", 
                            "default": True
                        }
                    },
                    "required": ["pdf_path"]
                }
            ),
            Tool(
                name="analyze_pdf_structure",
                description="Analyze PDF structure and metadata without conversion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF file to analyze"
                        }
                    },
                    "required": ["pdf_path"]
                }
            ),
            Tool(
                name="prepare_pdf_for_rag", 
                description="Prepare PDF content for RAG (Retrieval Augmented Generation) with vector database formats",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF file to process"
                        },
                        "vector_db_format": {
                            "type": "string",
                            "description": "Target vector database format",
                            "enum": ["chromadb", "pinecone", "weaviate", "qdrant"],
                            "default": "chromadb"
                        },
                        "chunk_size": {
                            "type": "integer",
                            "description": "Target chunk size in tokens (default: 768)",
                            "default": 768
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Directory to save RAG files (default: ./rag_output)",
                            "default": "./rag_output"
                        }
                    },
                    "required": ["pdf_path"]
                }
            )
        ]
    )

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    try:
        if name == "convert_pdf":
            return await handle_convert_pdf(arguments)
        elif name == "analyze_pdf_structure":
            return await handle_analyze_pdf(arguments)
        elif name == "prepare_pdf_for_rag":
            return await handle_prepare_rag(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        logger.error(traceback.format_exc())
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ],
            isError=True
        )

async def handle_convert_pdf(args: Dict[str, Any]) -> CallToolResult:
    """Handle PDF to markdown conversion"""
    pdf_path = args["pdf_path"]
    output_dir = args.get("output_dir", "./docs")
    
    # Validate PDF file exists
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Build options from arguments
    options = {
        "split_by_chapters": args.get("split_by_chapters", True),
        "preserve_tables": args.get("preserve_tables", True), 
        "extract_images": args.get("extract_images", True),
        "generate_summaries": args.get("generate_summaries", True),
        "generate_concept_map": args.get("generate_concept_map", True),
        "resolve_cross_references": args.get("resolve_cross_references", True),
        "structured_tables": args.get("structured_tables", True),
        "enable_chunking": args.get("enable_chunking", True)
    }
    
    logger.info(f"Converting PDF: {pdf_path} to {output_dir}")
    
    # Run the modular converter
    converter = ModularPDFConverter(pdf_path, output_dir, options)
    result = converter.convert()
    
    if result.get("success"):
        message = f"✅ Successfully converted {Path(pdf_path).name}\n"
        message += f"📁 Output directory: {output_dir}\n"
        message += f"📄 Files created: {len(result.get('output_files', []))}\n"
        message += f"⏱️ Processing time: {result.get('processing_time_seconds', 0):.1f}s\n"
        
        if result.get('processing_stats'):
            stats = result['processing_stats']
            message += f"📊 Statistics:\n"
            if 'pdf_extraction' in stats:
                pdf_stats = stats['pdf_extraction']
                message += f"   • Pages: {pdf_stats.get('pages', 0)}\n"
                message += f"   • Images: {pdf_stats.get('images', 0)}\n" 
                message += f"   • Tables: {pdf_stats.get('tables', 0)}\n"
            if 'sections' in stats:
                message += f"   • Sections: {stats['sections']}\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=message)]
        )
    else:
        error_msg = f"❌ Conversion failed: {result.get('error', 'Unknown error')}"
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True
        )

async def handle_analyze_pdf(args: Dict[str, Any]) -> CallToolResult:
    """Handle PDF structure analysis"""
    pdf_path = args["pdf_path"]
    
    # Validate PDF file exists
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    logger.info(f"Analyzing PDF structure: {pdf_path}")
    
    # Run the analyzer
    analysis = analyze_pdf(pdf_path)
    
    # Format the analysis results
    message = f"📋 PDF Analysis: {Path(pdf_path).name}\n\n"
    message += f"📄 **Basic Info:**\n"
    message += f"   • Pages: {analysis.get('page_count', 0)}\n"
    message += f"   • File size: {analysis.get('file_size_mb', 0):.1f} MB\n"
    
    if analysis.get('metadata'):
        metadata = analysis['metadata']
        message += f"\n📝 **Metadata:**\n"
        if metadata.get('title'):
            message += f"   • Title: {metadata['title']}\n"
        if metadata.get('author'):
            message += f"   • Author: {metadata['author']}\n"
        if metadata.get('creation_date'):
            message += f"   • Created: {metadata['creation_date']}\n"
    
    if analysis.get('structure'):
        structure = analysis['structure']
        message += f"\n🏗️ **Structure:**\n"
        message += f"   • Images: {structure.get('images', 0)}\n"
        message += f"   • Tables: {structure.get('tables', 0)}\n"
        message += f"   • Text blocks: {structure.get('text_blocks', 0)}\n"
    
    return CallToolResult(
        content=[TextContent(type="text", text=message)]
    )

async def handle_prepare_rag(args: Dict[str, Any]) -> CallToolResult:
    """Handle RAG preparation"""
    pdf_path = args["pdf_path"]
    vector_db_format = args.get("vector_db_format", "chromadb")
    chunk_size = args.get("chunk_size", 768)
    output_dir = args.get("output_dir", "./rag_output")
    
    # Validate PDF file exists
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    logger.info(f"Preparing PDF for RAG: {pdf_path} -> {vector_db_format}")
    
    # Run RAG preparation
    processor = PDFToRAGProcessor(pdf_path, output_dir, vector_db_format, chunk_size)
    chunk_count = processor.process()
    
    result = {
        "success": True,
        "chunk_count": chunk_count,
        "avg_chunk_size": chunk_size,  # Approximation
        "output_files": [
            str(Path(output_dir) / "chunks.json"),
            str(Path(output_dir) / f"{vector_db_format}_format.json"),
            str(Path(output_dir) / "import_instructions.md")
        ]
    }
    
    if result.get("success"):
        message = f"✅ RAG preparation completed for {Path(pdf_path).name}\n"
        message += f"🗄️ Format: {vector_db_format}\n"
        message += f"📁 Output directory: {output_dir}\n"
        message += f"🧩 Chunks created: {result.get('chunk_count', 0)}\n"
        message += f"📏 Average chunk size: {result.get('avg_chunk_size', 0)} tokens\n"
        
        if result.get('output_files'):
            message += f"\n📄 **Files created:**\n"
            for file_path in result['output_files']:
                message += f"   • {Path(file_path).name}\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=message)]
        )
    else:
        error_msg = f"❌ RAG preparation failed: {result.get('error', 'Unknown error')}"
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True
        )

async def main():
    """Main entry point"""
    # Import here to avoid issues if mcp is not installed
    import mcp.server.stdio
    
    logger.info("Starting MCP PDF to Markdown server")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())