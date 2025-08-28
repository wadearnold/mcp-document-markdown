#!/usr/bin/env python3
"""
MCP Document to Markdown Server
Supports PDF and Microsoft Word documents
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
app = Server("document-markdown")

@app.list_tools()
async def list_tools():
    """List available tools for document processing"""
    print("🔧 LIST_TOOLS CALLED - WORKING!", flush=True)
    return [
            Tool(
                name="extract_pdf_content",
                description="Extract structured content from any PDF document (direct approach)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF file to extract content from"
                        },
                        "config": {
                            "type": "object",
                            "description": "Optional configuration for customizing extraction behavior",
                            "properties": {
                                "bullet_indicators": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Custom phrases that indicate bullet lists"
                                }
                            }
                        }
                    },
                    "required": ["pdf_path"]
                }
            ),
            Tool(
                name="convert_pdf",
                description="Convert PDF to LLM-optimized markdown with semantic navigation structure",
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
                        "preserve_tables": {
                            "type": "boolean",
                            "description": "Embed tables within sections as both markdown and JSON",
                            "default": True
                        },
                        "extract_images": {
                            "type": "boolean", 
                            "description": "Extract and reference images within relevant sections",
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
            ),
            Tool(
                name="convert_docx",
                description="Convert Word document to LLM-optimized markdown with semantic navigation structure",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "docx_path": {
                            "type": "string",
                            "description": "Path to the Word document (.docx) to convert"
                        },
                        "output_dir": {
                            "type": "string", 
                            "description": "Directory to save the converted files (default: ./docs)",
                            "default": "./docs"
                        },
                        "preserve_tables": {
                            "type": "boolean",
                            "description": "Embed tables within sections as both markdown and JSON",
                            "default": True
                        },
                        "extract_images": {
                            "type": "boolean",
                            "description": "Extract and reference images within relevant sections",
                            "default": True
                        }
                    },
                    "required": ["docx_path"]
                }
            ),
            Tool(
                name="extract_docx_content",
                description="Extract structured content from any Word document (direct approach)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "docx_path": {
                            "type": "string", 
                            "description": "Path to the Word document to extract content from"
                        },
                        "config": {
                            "type": "object",
                            "description": "Optional configuration for customizing extraction behavior",
                            "properties": {
                                "preserve_formatting": {
                                    "type": "boolean",
                                    "description": "Preserve document formatting during extraction",
                                    "default": True
                                }
                            }
                        }
                    },
                    "required": ["docx_path"]
                }
            ),
            Tool(
                name="analyze_docx_structure", 
                description="Analyze Word document structure without converting",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "docx_path": {
                            "type": "string",
                            "description": "Path to the Word document to analyze"
                        }
                    },
                    "required": ["docx_path"]
                }
            ),
            Tool(
                name="prepare_docx_for_rag",
                description="Prepare Word document content for RAG workflows",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "docx_path": {
                            "type": "string",
                            "description": "Path to the Word document to prepare for RAG"
                        },
                        "vector_db_format": {
                            "type": "string",
                            "description": "Target vector database format",
                            "enum": ["chromadb", "pinecone", "weaviate", "qdrant"],
                            "default": "chromadb"
                        },
                        "chunk_size": {
                            "type": "integer",
                            "description": "Target tokens per chunk for embedding",
                            "default": 768
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Directory to save RAG-ready files (default: ./rag_output)",
                            "default": "./rag_output"
                        }
                    },
                    "required": ["docx_path"]
                }
            )
        ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    """Handle tool calls"""
    try:
        logger.info(f"Tool called: {name} with args: {arguments}")
        
        if name == "extract_pdf_content":
            return await handle_extract_pdf_content(arguments)
        elif name == "convert_pdf":
            return await handle_convert_pdf(arguments)
        elif name == "analyze_pdf_structure":
            return await handle_analyze_pdf(arguments)  
        elif name == "prepare_pdf_for_rag":
            return await handle_prepare_rag(arguments)
        elif name == "extract_docx_content":
            return await handle_extract_docx_content(arguments)
        elif name == "convert_docx":
            return await handle_convert_docx(arguments)
        elif name == "analyze_docx_structure":
            return await handle_analyze_docx(arguments)
        elif name == "prepare_docx_for_rag":
            return await handle_prepare_docx_rag(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def handle_extract_pdf_content(args: Dict[str, Any]):
    """Handle generic PDF content extraction"""
    try:
        from processors.pdf_extractor import extract_pdf
        
        pdf_path = args["pdf_path"]
        config = args.get("config", {})
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting content from PDF: {pdf_path}")
        
        # Extract using generic approach
        results = extract_pdf(pdf_path, config)
        
        # Format output for MCP response
        output = []
        output.append(f"# PDF Content Extraction Results\n")
        output.append(f"**File:** {pdf_path}")
        output.append(f"**Document Type:** {results['metadata']['document_type']}")
        output.append(f"**Total Fields:** {results['metadata']['total_fields']}")
        output.append(f"**Total Lines:** {results['summary']['total_lines']}")
        output.append(f"**Has Tables:** {results['metadata']['has_tables']}")
        output.append(f"**Has Lists:** {results['metadata']['has_lists']}")
        
        # Field type distribution
        output.append(f"\n## Field Type Distribution")
        for field_type, count in results['summary']['field_types'].items():
            output.append(f"- **{field_type}:** {count}")
        
        # Show extracted fields
        output.append(f"\n## Extracted Fields ({len(results['fields'])} total)")
        
        for i, field in enumerate(results['fields'][:20]):  # Show first 20 fields
            output.append(f"\n### {i+1}. {field['name']}")
            output.append(f"**Type:** {field['type']}")
            if field['content']:
                # Truncate very long content
                content = field['content'][:300] + "..." if len(field['content']) > 300 else field['content']
                output.append(f"**Content:** {content}")
            if field['metadata']:
                output.append(f"**Metadata:** {field['metadata']}")
        
        if len(results['fields']) > 20:
            output.append(f"\n*... and {len(results['fields']) - 20} more fields*")
        
        # Show sections if detected
        if results['structure']['sections']:
            output.append(f"\n## Detected Sections ({len(results['structure']['sections'])})")
            for section in results['structure']['sections'][:10]:
                output.append(f"- {section}")
            if len(results['structure']['sections']) > 10:
                output.append(f"- *... and {len(results['structure']['sections']) - 10} more sections*")
        
        response_text = "\n".join(output)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text", 
                    text=response_text
                )
            ]
        )
        
    except Exception as e:
        logger.error(f"Error in PDF extraction: {str(e)}", exc_info=True)
        return CallToolResult(
            content=[
                TextContent(
                    type="text", 
                    text=f" Error extracting PDF content: {str(e)}"
                )
            ],
            isError=True
        )


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
            message += f"⏱️ Processing time: {result.get('processing_time_seconds', 0):.1f}s\n\n"
            
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
            
            
            # Agent navigation for LLM-optimized structure
            message += f"\n💡 **File Navigation:**\n"
            message += f"• `README.md` - Document overview and section directory\n"
            message += f"• `sections/` - Semantic sections with embedded tables and cross-references\n"
            
            # Critical next step for AI agent training
            message += f"\n🤖 **Next: Train Your AI Agent**\n"
            message += f"Visit https://github.com/wadearnold/mcp-document-markdown/blob/main/AGENT_INSTRUCTIONS.md\n"
            message += f"Copy the training prompt and replace [FOLDER_NAME] with: {actual_output_path.name}\n"
            
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
        
        message = f" 📊 PDF Analysis: {Path(pdf_path).name}\n"
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
        
        message = f" 🎯 RAG Preparation Complete\n"
        message += f"PDF: {Path(pdf_path).name}\n" 
        message += f"Format: {vector_db_format}\n"
        message += f"Chunks: {chunk_count}\n"
        message += f"Output: {output_dir}"
        
        return [TextContent(type="text", text=message)]
        
    except Exception as e:
        logger.error(f"RAG preparation failed: {e}")
        raise

async def handle_convert_docx(args: Dict[str, Any]):
    """Handle Word document to markdown conversion"""
    try:
        from modular_docx_converter import ModularDocxConverter
        from utils.file_utils import FileUtils
        
        docx_path = args["docx_path"]
        output_dir = args.get("output_dir", "./docs")
        
        if not Path(docx_path).exists():
            raise FileNotFoundError(f"Word document not found: {docx_path}")
        
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
        
        logger.info(f"Converting Word document: {docx_path} to {output_dir}")
        
        converter = ModularDocxConverter(docx_path, output_dir, options)
        result = converter.convert()
        
        if result.get("success"):
            # Get actual file count from generated_files
            total_files = result.get('file_count', len(result.get('generated_files', [])))
            
            # Get the actual output path (with sanitized folder name)
            docx_folder_name = FileUtils.sanitize_folder_name(Path(docx_path).name)
            actual_output_path = f"{output_dir}/{docx_folder_name}"
            
            message = f"✅ Successfully converted {Path(docx_path).name}\n"
            message += f"📁 Output directory: {actual_output_path}\n" 
            message += f"📄 Total files generated: {total_files:,}\n"
            message += f"⏱️ Processing time: {result.get('processing_time_seconds', 0):.1f}s\n\n"
            
            # Add brief final summary stats
            stats = result.get('processing_stats', {})
            if stats:
                message += "📊 Content Summary:\n"
                docx_stats = stats.get('docx_extraction', {})
                if docx_stats:
                    message += f"   • {docx_stats.get('total_words', 0):,} words processed\n"
                    message += f"   • {docx_stats.get('total_sections', 0)} sections found\n" 
                    message += f"   • {docx_stats.get('total_tables', 0)} tables structured\n"
                    message += f"   • {docx_stats.get('total_images', 0)} images referenced\n"
                if 'sections' in stats:
                    message += f"   • {stats['sections']} sections organized\n"
            
            # Add critical agent training instructions
            
            # Agent navigation for LLM-optimized structure
            message += f"\n💡 **File Navigation:**\n"
            message += f"• `README.md` - Document overview and section directory\n"
            message += f"• `sections/` - Semantic sections with embedded tables and cross-references\n"
            
            # Critical next step for AI agent training
            message += f"\n🤖 **Next: Train Your AI Agent**\n"
            message += f"Visit https://github.com/wadearnold/mcp-document-markdown/blob/main/AGENT_INSTRUCTIONS.md\n"
            message += f"Copy the training prompt and replace [FOLDER_NAME] with: {actual_output_path.name}\n"
            
            return [TextContent(type="text", text=message)]
        else:
            error_msg = f"❌ Conversion failed: {result.get('error', 'Unknown error')}"
            return [TextContent(type="text", text=error_msg)]
        
    except Exception as e:
        logger.error(f"Convert Word document failed: {e}")
        raise

async def handle_analyze_docx(args: Dict[str, Any]):
    """Handle Word document structure analysis"""
    try:
        from processors.docx_extractor import DocxExtractor
        
        docx_path = args["docx_path"]
        
        if not Path(docx_path).exists():
            raise FileNotFoundError(f"Word document not found: {docx_path}")
            
        logger.info(f"Analyzing Word document structure: {docx_path}")
        
        extractor = DocxExtractor()
        result = extractor.extract_from_file(docx_path)
        
        if result['success']:
            # Get file size
            file_size_mb = Path(docx_path).stat().st_size / (1024 * 1024)
            
            message = f" 📊 Word Document Analysis: {Path(docx_path).name}\n"
            message += f"Size: {file_size_mb:.2f} MB\n"
            message += f"Words: {result['stats'].get('total_words', 0):,}\n"
            message += f"Sections: {result['stats'].get('total_sections', 0)}\n"
            message += f"Tables: {result['stats'].get('total_tables', 0)}\n"
            message += f"Images: {result['stats'].get('total_images', 0)}\n"
            message += f"Has TOC: {result['stats'].get('has_toc', False)}"
        else:
            message = f" Analysis failed: {result.get('error', 'Unknown error')}"
        
        return [TextContent(type="text", text=message)]
        
    except Exception as e:
        logger.error(f"Analyze Word document failed: {e}")
        raise

async def handle_extract_docx_content(args: Dict[str, Any]):
    """Handle direct DOCX content extraction"""
    try:
        from processors.docx_extractor import DocxExtractor
        
        docx_path = args["docx_path"]
        config = args.get("config", {})
        
        if not Path(docx_path).exists():
            raise FileNotFoundError(f"Word document not found: {docx_path}")
        
        logger.info(f"Extracting content from Word document: {docx_path}")
        
        extractor = DocxExtractor()
        result = extractor.extract_from_file(docx_path)
        
        if result['success']:
            output = []
            output.append(f"# Word Document Content Extraction Results\n")
            output.append(f"**File:** {docx_path}")
            output.append(f"**Paragraphs:** {result.get('paragraph_count', 0)}")
            output.append(f"**Tables:** {result.get('table_count', 0)}")
            output.append(f"**Images:** {result.get('image_count', 0)}")
            
            # Show extracted content preview
            if result.get('content'):
                content_preview = result['content'][:1000] + "..." if len(result['content']) > 1000 else result['content']
                output.append(f"\n## Content Preview\n{content_preview}")
            
            response_text = "\n".join(output)
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", 
                        text=response_text
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f" Failed to extract content from Word document: {result.get('error', 'Unknown error')}"
                    )
                ]
            )
            
    except Exception as e:
        logger.error(f"Error in DOCX content extraction: {str(e)}", exc_info=True)
        return CallToolResult(
            content=[
                TextContent(
                    type="text", 
                    text=f" Error extracting Word document content: {str(e)}"
                )
            ]
        )


async def handle_prepare_docx_rag(args: Dict[str, Any]):
    """Handle preparing DOCX content for RAG workflows"""
    try:
        from pdf_to_rag import prepare_document_for_rag
        
        docx_path = args["docx_path"]
        vector_db_format = args.get("vector_db_format", "chromadb")
        chunk_size = args.get("chunk_size", 768)
        output_dir = args.get("output_dir", "./rag_output")
        
        if not Path(docx_path).exists():
            raise FileNotFoundError(f"Word document not found: {docx_path}")
        
        logger.info(f"Preparing Word document for RAG: {docx_path}")
        
        result = prepare_document_for_rag(
            docx_path,
            output_dir, 
            vector_db_format,
            chunk_size
        )
        
        message = f" Successfully prepared {Path(docx_path).name} for RAG\n"
        message += f" Output: {output_dir}\n"
        message += f" 🔗 Vector DB Format: {vector_db_format}\n"
        message += f" Chunk Size: {chunk_size} tokens\n"
        message += f" Files generated: {result.get('files_generated', 0)}\n\n"
        message += "Ready for import into your vector database!"
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=message
                )
            ]
        )
        
    except Exception as e:
        logger.error(f"Error in DOCX RAG preparation: {str(e)}", exc_info=True)
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f" Error preparing Word document for RAG: {str(e)}"
                )
            ]
        )


async def main():
    """Main entry point"""
    logger.info("Starting MCP Document-to-Markdown server (document-markdown)")
    print(f"🐍 Python executable: {sys.executable}", file=sys.stderr, flush=True)
    print(f" Working directory: {Path.cwd()}", file=sys.stderr, flush=True)
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