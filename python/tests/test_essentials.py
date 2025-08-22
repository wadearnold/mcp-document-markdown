#!/usr/bin/env python3
"""
Essential functionality tests for the refactored Python MCP server
Tests the core functionality that users depend on.
"""
import unittest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import patch, Mock
import asyncio

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestEssentialFunctionality(unittest.TestCase):
    """Test essential functionality that users depend on"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create a simple mock PDF file
        self.mock_pdf = self.temp_path / "test.pdf"
        self.mock_pdf.write_bytes(b"%PDF-1.4\n%%EOF")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_all_critical_imports_work(self):
        """Test that all critical system imports work - this is the most important test"""
        try:
            # Test MCP server imports
            from mcp_pdf_markdown import handle_convert_pdf, handle_analyze_pdf, handle_prepare_rag
            
            # Test modular converter imports
            from modular_pdf_converter import ModularPDFConverter
            
            # Test utility imports
            from utils.token_counter import TokenCounter
            from utils.text_utils import TextUtils
            from utils.file_utils import FileUtils
            
            # Test processor imports
            from processors.pdf_extractor import PDFExtractor
            from processors.table_processor import TableProcessor
            from processors.chunking_engine import ChunkingEngine
            from processors.concept_mapper import ConceptMapper
            from processors.cross_referencer import CrossReferencer
            from processors.summary_generator import SummaryGenerator
            
            # Test PDF library imports
            import fitz  # PyMuPDF
            import pypdf
            import pdfplumber
            
            # Test data processing imports
            import pandas as pd
            import numpy as np
            
            # Test MCP library imports
            from mcp.server import Server
            from mcp.types import Tool, TextContent, CallToolResult
            
            # If we get here, all critical imports worked
            self.assertTrue(True, "All critical imports successful")
            
        except ImportError as e:
            self.fail(f"Critical import failed: {e}")
    
    def test_utility_classes_can_be_instantiated(self):
        """Test that utility classes can be created without errors"""
        try:
            from utils.token_counter import TokenCounter
            from utils.text_utils import TextUtils
            from utils.file_utils import FileUtils
            
            # Test TokenCounter
            token_counter = TokenCounter()
            self.assertIsNotNone(token_counter)
            
            # Test TextUtils (static methods)
            result = TextUtils.clean_text("test")
            self.assertEqual(result, "test")
            
            # Test FileUtils (static methods)
            FileUtils.ensure_directory(self.temp_path / "test_dir")
            self.assertTrue((self.temp_path / "test_dir").exists())
            
        except Exception as e:
            self.fail(f"Utility class instantiation failed: {e}")
    
    def test_modular_converter_can_be_created(self):
        """Test that the modular converter can be instantiated"""
        try:
            from modular_pdf_converter import ModularPDFConverter
            
            converter = ModularPDFConverter(
                str(self.mock_pdf),
                str(self.temp_path / "output"),
                {}
            )
            
            # Verify it has the expected components
            self.assertIsNotNone(converter.token_counter)
            self.assertIsNotNone(converter.pdf_extractor)
            self.assertIsNotNone(converter.table_processor)
            
        except Exception as e:
            self.fail(f"Modular converter creation failed: {e}")
    
    def test_processor_classes_can_be_created(self):
        """Test that processor classes can be instantiated"""
        try:
            from processors.pdf_extractor import PDFExtractor
            from processors.table_processor import TableProcessor
            from processors.chunking_engine import ChunkingEngine
            from processors.concept_mapper import ConceptMapper
            from processors.cross_referencer import CrossReferencer
            from processors.summary_generator import SummaryGenerator
            from utils.token_counter import TokenCounter
            
            token_counter = TokenCounter()
            output_dir = str(self.temp_path)
            
            # Test each processor can be created
            pdf_extractor = PDFExtractor(str(self.mock_pdf), output_dir)
            self.assertIsNotNone(pdf_extractor)
            
            table_processor = TableProcessor(output_dir, token_counter)
            self.assertIsNotNone(table_processor)
            
            chunking_engine = ChunkingEngine(output_dir, token_counter)
            self.assertIsNotNone(chunking_engine)
            
            concept_mapper = ConceptMapper(output_dir, token_counter)
            self.assertIsNotNone(concept_mapper)
            
            cross_referencer = CrossReferencer(output_dir)
            self.assertIsNotNone(cross_referencer)
            
            summary_generator = SummaryGenerator(output_dir, token_counter)
            self.assertIsNotNone(summary_generator)
            
        except Exception as e:
            self.fail(f"Processor class creation failed: {e}")
    
    @patch('modular_pdf_converter.ModularPDFConverter')
    def test_mcp_convert_handler_works(self, mock_converter_class):
        """Test that the MCP convert handler works with mocked converter"""
        try:
            from mcp_pdf_markdown import handle_convert_pdf
            
            # Set up mock
            mock_converter = Mock()
            mock_converter.convert.return_value = {
                'success': True,
                'output_files': ['test.md'],
                'processing_time_seconds': 1.0,
                'processing_stats': {
                    'pdf_extraction': {'pages': 1, 'images': 0, 'tables': 0},
                    'sections': 1
                }
            }
            mock_converter_class.return_value = mock_converter
            
            # Test the handler
            args = {'pdf_path': str(self.mock_pdf)}
            result = asyncio.run(handle_convert_pdf(args))
            
            # Verify result structure
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.content)
            self.assertGreater(len(result.content), 0)
            
        except Exception as e:
            self.fail(f"MCP convert handler failed: {e}")
    
    @patch('pdf_analyzer.analyze_pdf')
    def test_mcp_analyze_handler_works(self, mock_analyze):
        """Test that the MCP analyze handler works with mocked analyzer"""
        try:
            from mcp_pdf_markdown import handle_analyze_pdf
            
            # Set up mock
            mock_analyze.return_value = {
                'page_count': 1,
                'file_size_mb': 0.1
            }
            
            # Test the handler
            args = {'pdf_path': str(self.mock_pdf)}
            result = asyncio.run(handle_analyze_pdf(args))
            
            # Verify result structure
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.content)
            
        except Exception as e:
            self.fail(f"MCP analyze handler failed: {e}")
    
    @patch('mcp_pdf_markdown.PDFToRAGProcessor')
    def test_mcp_rag_handler_works(self, mock_processor_class):
        """Test that the MCP RAG handler works with mocked processor"""
        try:
            from mcp_pdf_markdown import handle_prepare_rag
            
            # Set up mock
            mock_processor = Mock()
            mock_processor.process.return_value = 5
            mock_processor_class.return_value = mock_processor
            
            # Test the handler
            args = {'pdf_path': str(self.mock_pdf)}
            result = asyncio.run(handle_prepare_rag(args))
            
            # Verify result structure
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.content)
            
        except Exception as e:
            self.fail(f"MCP RAG handler failed: {e}")


class TestLibraryCompatibility(unittest.TestCase):
    """Test that all required libraries are available and compatible"""
    
    def test_pdf_libraries(self):
        """Test PDF processing libraries"""
        try:
            import fitz
            import pypdf
            import pdfplumber
            
            # Test basic functionality
            self.assertTrue(hasattr(fitz, 'open'))
            self.assertTrue(hasattr(pypdf, 'PdfReader'))
            self.assertTrue(hasattr(pdfplumber, 'open'))
            
        except ImportError as e:
            self.fail(f"PDF library not available: {e}")
    
    def test_data_processing_libraries(self):
        """Test data processing libraries"""
        try:
            import pandas as pd
            import numpy as np
            
            # Test basic functionality
            df = pd.DataFrame({'test': [1, 2, 3]})
            self.assertEqual(len(df), 3)
            
            arr = np.array([1, 2, 3])
            self.assertEqual(len(arr), 3)
            
        except ImportError as e:
            self.fail(f"Data processing library not available: {e}")
    
    def test_mcp_library(self):
        """Test MCP library"""
        try:
            from mcp.server import Server
            from mcp.types import Tool, TextContent, CallToolResult
            
            # Test basic MCP server creation
            server = Server("test")
            self.assertIsNotNone(server)
            
        except ImportError as e:
            self.fail(f"MCP library not available: {e}")
    
    def test_optional_libraries(self):
        """Test optional libraries (should not fail if missing)"""
        try:
            import tiktoken
            tiktoken_available = True
        except ImportError:
            tiktoken_available = False
        
        # Just record the result, don't fail if missing
        if tiktoken_available:
            print("✅ tiktoken available for accurate token counting")
        else:
            print("ℹ️  tiktoken not available, will use approximation")


if __name__ == '__main__':
    # Run tests with more verbose output
    unittest.main(verbosity=2)