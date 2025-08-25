#!/usr/bin/env python3
"""
Fixed MCP PDF to Markdown Server
"""
import asyncio
import json
import sys
import signal
import logging
from pathlib import Path
from typing import Any, Dict

# Add python directory to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

# MCP imports
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult, ListToolsResult
import mcp.server.stdio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the MCP server
app = Server("pdf-markdown")

@app.list_tools()
async def list_tools():
    """List available tools for PDF processing"""
    print("🔧 LIST_TOOLS CALLED - WORKING!", flush=True)
    return [
            Tool(
                name="convert_pdf",
                description="Convert PDF to organized markdown documentation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF file to convert"
                        },
                        "output_dir": {
                            "type": "string", 
                            "description": "Directory to save the converted files (default: ./docs)",
                            "default": "./docs"
                        },
                        "split_by_chapters": {
                            "type": "boolean",
                            "description": "Split output by document chapters/sections",
                            "default": True
                        },
                        "preserve_tables": {
                            "type": "boolean",
                            "description": "Preserve table formatting in markdown",
                            "default": True
                        },
                        "extract_images": {
                            "type": "boolean",
                            "description": "Extract and save images from PDF", 
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
                        "chunk_size_optimization": {
                            "type": "boolean",
                            "description": "Optimize chunks for LLM token windows (default: true)",
                            "default": True
                        }
                    },
                    "required": ["pdf_path"]
                }
            ),
            Tool(
                name="analyze_pdf_structure", 
                description="Analyze PDF structure without converting",
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
                description="Prepare PDF content for RAG workflows",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF file to process"
                        },
                        "vector_db_format": {
                            "type": "string",
                            "description": "Vector database format (chromadb, pinecone, weaviate, qdrant)",
                            "default": "chromadb"
                        },
                        "chunk_size": {
                            "type": "integer",
                            "description": "Target chunk size in tokens",
                            "default": 768
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Directory to save RAG-prepared files",
                            "default": "./rag_output"
                        }
                    },
                    "required": ["pdf_path"]
                }
            )
        ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    """Handle tool calls"""
    try:
        logger.info(f"Tool called: {name} with args: {arguments}")
        
        if name == "convert_pdf":
            return await handle_convert_pdf(arguments)
        elif name == "analyze_pdf_structure":
            return await handle_analyze_pdf(arguments)  
        elif name == "prepare_pdf_for_rag":
            return await handle_prepare_rag(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def handle_convert_pdf(args: Dict[str, Any]):
    """Handle PDF to markdown conversion"""
    try:
        from modular_pdf_converter import ModularPDFConverter
        from utils.file_utils import FileUtils
        
        pdf_path = args["pdf_path"]
        output_dir = args.get("output_dir", "./docs")
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        options = {
            "split_by_chapters": args.get("split_by_chapters", True),
            "preserve_tables": args.get("preserve_tables", True), 
            "extract_images": args.get("extract_images", True),
            "generate_summaries": args.get("generate_summaries", True),
            "generate_concept_map": args.get("generate_concept_map", True),
            "resolve_cross_references": args.get("resolve_cross_references", True),
            "structured_tables": args.get("structured_tables", True),
            "chunk_size_optimization": args.get("chunk_size_optimization", True),
        }
        
        logger.info(f"Converting PDF: {pdf_path} to {output_dir}")
        
        converter = ModularPDFConverter(pdf_path, output_dir, options)
        result = converter.convert()
        
        if result.get("success"):
            # Get actual file count from generated_files
            total_files = result.get('file_count', len(result.get('generated_files', [])))
            
            # Get the actual output path (with sanitized PDF folder name)
            pdf_folder_name = FileUtils.sanitize_folder_name(Path(pdf_path).name)
            actual_output_path = f"{output_dir}/{pdf_folder_name}"
            
            message = f"✅ Successfully converted {Path(pdf_path).name}\n"
            message += f"📁 Output directory: {actual_output_path}\n" 
            message += f"📄 Total files generated: {total_files:,}\n"
            message += f"⏱️  Processing time: {result.get('processing_time_seconds', 0):.1f}s\n\n"
            
            # Add brief final summary stats
            stats = result.get('processing_stats', {})
            if stats:
                message += "📊 Content Summary:\n"
                pdf_stats = stats.get('pdf_extraction', {})
                if pdf_stats:
                    message += f"   • {pdf_stats.get('pages', 0)} pages processed\n"
                    message += f"   • {pdf_stats.get('images', 0)} images extracted\n" 
                    message += f"   • {pdf_stats.get('tables', 0)} tables structured\n"
                if 'sections' in stats:
                    message += f"   • {stats['sections']} sections organized\n"
                    
                # Add critical agent training instructions
                message += f"\n🚨 **CRITICAL NEXT STEP - TRAIN YOUR AI AGENT:**\n"
                message += f"   \n"
                message += f"   Your PDF is converted, but your agent doesn't know how to use it yet!\n"
                message += f"   \n"
                message += f"   📋 **DO THIS NOW:**\n"
                message += f"   1. Open: https://github.com/wadearnold/mcp-pdf-markdown/blob/main/AGENT_INSTRUCTIONS.md\n"
                message += f"   2. Copy the training prompt from the 'Quick Start' section\n"
                message += f"   3. Replace [FOLDER_NAME] with: {pdf_folder_name}\n"
                message += f"   4. Paste the prompt to your AI agent immediately\n"
                message += f"   \n"
                message += f"   ⚠️  **Without this step, your agent won't know the documentation exists!**\n"
                message += f"   \n"
                message += f"   💡 **File Navigation Guide:**\n"
                message += f"   • `structure-overview.md` - Document map and navigation\n"
                message += f"   • `sections/` - Individual content sections  \n"
                message += f"   • `chunked/` - LLM-optimized content pieces\n"
                message += f"   • `tables/` - Structured data for analysis\n"
            
            return [TextContent(type="text", text=message)]
        else:
            error_msg = f"❌ Conversion failed: {result.get('error', 'Unknown error')}"
            return [TextContent(type="text", text=error_msg)]
        
    except Exception as e:
        logger.error(f"Convert PDF failed: {e}")
        raise

async def handle_analyze_pdf(args: Dict[str, Any]):
    """Handle PDF structure analysis"""
    try:
        from pdf_analyzer import analyze_pdf
        
        pdf_path = args["pdf_path"]
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        logger.info(f"Analyzing PDF structure: {pdf_path}")
        
        analysis = analyze_pdf(pdf_path)
        
        # Get file size
        file_size_mb = Path(pdf_path).stat().st_size / (1024 * 1024)
        
        message = f"📊 PDF Analysis: {Path(pdf_path).name}\n"
        message += f"Pages: {analysis.get('pages', 'unknown')}\n"
        message += f"Size: {file_size_mb:.2f} MB\n"
        message += f"Has TOC: {analysis.get('has_toc', False)}\n"
        message += f"Tables: {analysis.get('table_count', 0)}\n"
        message += f"Images: {analysis.get('image_count', 0)}"
        
        return [TextContent(type="text", text=message)]
        
    except Exception as e:
        logger.error(f"Analyze PDF failed: {e}")
        raise

async def handle_prepare_rag(args: Dict[str, Any]):
    """Handle RAG preparation"""
    try:
        from pdf_to_rag import PDFToRAGProcessor
        
        pdf_path = args["pdf_path"]
        vector_db_format = args.get("vector_db_format", "chromadb")
        chunk_size = args.get("chunk_size", 768)
        output_dir = args.get("output_dir", "./rag_output")
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        logger.info(f"Preparing PDF for RAG: {pdf_path} -> {vector_db_format}")
        
        processor = PDFToRAGProcessor(
            pdf_path,
            output_dir, 
            vector_db_format=vector_db_format,
            chunk_size=chunk_size
        )
        
        chunk_count = processor.process()
        
        message = f"🎯 RAG Preparation Complete\n"
        message += f"PDF: {Path(pdf_path).name}\n" 
        message += f"Format: {vector_db_format}\n"
        message += f"Chunks: {chunk_count}\n"
        message += f"Output: {output_dir}"
        
        return [TextContent(type="text", text=message)]
        
    except Exception as e:
        logger.error(f"RAG preparation failed: {e}")
        raise

async def main():
    """Main entry point"""
    logger.info("Starting MCP PDF-to-Markdown server (pdf-markdown)")
    print(f"🐍 Python executable: {sys.executable}", file=sys.stderr, flush=True)
    print(f"📁 Working directory: {Path.cwd()}", file=sys.stderr, flush=True)
    print(f"🛤️  Python path: {sys.path[:3]}...", file=sys.stderr, flush=True)
    
    # Add debugging for request handling
    original_run = app.run
    async def debug_run(*args, **kwargs):
        print(f"🔧 Server.run() called", file=sys.stderr, flush=True)
        return await original_run(*args, **kwargs)
    app.run = debug_run
    
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            print(f"📡 Starting stdio server", file=sys.stderr, flush=True)
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except asyncio.CancelledError:
        # This is expected when shutting down
        pass
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n👋 Server stopped by user", file=sys.stderr)
        return

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C without stack trace
        print("\n👋 Server stopped by user", file=sys.stderr)
        # Force immediate exit to prevent hanging
        import os
        os._exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        import os
        os._exit(1)