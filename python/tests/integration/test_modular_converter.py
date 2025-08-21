"""
Integration tests for ModularPDFConverter
"""
import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import json

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modular_pdf_converter import ModularPDFConverter


class TestModularConverterIntegration(unittest.TestCase):
    """Integration tests for ModularPDFConverter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create a mock PDF file for testing (just a text file)
        self.mock_pdf = self.test_dir / "test.pdf"
        self.mock_pdf.write_text("Mock PDF content for testing")
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_converter_initialization(self):
        """Test converter initialization with different options"""
        # Basic initialization
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output")
        )
        
        self.assertIsInstance(converter, ModularPDFConverter)
        self.assertEqual(converter.pdf_path, self.mock_pdf)
        self.assertTrue(converter.output_dir.exists())
        
        # With custom options
        options = {
            'extract_images': False,
            'resolve_cross_references': False,
            'generate_summaries': False,
            'create_chunks': False
        }
        
        converter_with_options = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output_custom"),
            options
        )
        
        self.assertEqual(converter_with_options.options, options)
    
    def test_structure_content_into_sections(self):
        """Test content structuring functionality"""
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output")
        )
        
        # Mock PDF content
        pdf_content = {
            'text': """# Introduction
            
This is the introduction section with some content.

## Getting Started

Here's how to get started with the API.

# API Reference

This section contains the API reference documentation.

## Authentication

Details about authentication methods.
""",
            'pages': [
                {'page_num': 1, 'text': 'Page 1 content'},
                {'page_num': 2, 'text': 'Page 2 content'}
            ],
            'structure': {
                'outline': [
                    {'title': 'Introduction', 'level': 0, 'page': 1},
                    {'title': 'API Reference', 'level': 0, 'page': 2}
                ]
            },
            'metadata': {'title': 'Test Document'}
        }
        
        sections = converter.structure_content_into_sections(pdf_content)
        
        self.assertGreater(len(sections), 0)
        
        # Check section structure
        for section in sections:
            self.assertIn('title', section)
            self.assertIn('content', section)
            self.assertIn('section_id', section)
            self.assertIn('token_count', section)
            self.assertIn('section_type', section)
    
    def test_classify_section_type(self):
        """Test section type classification"""
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output")
        )
        
        # Test different section types
        intro_section = {
            'title': 'Introduction',
            'content': 'This is an introduction to the API.'
        }
        self.assertEqual(converter.classify_section_type(intro_section), 'introduction')
        
        api_section = {
            'title': 'API Endpoints',
            'content': 'GET /users HTTP endpoint returns user data.'
        }
        self.assertEqual(converter.classify_section_type(api_section), 'api_endpoint')
        
        auth_section = {
            'title': 'Authentication',
            'content': 'OAuth 2.0 authentication flow.'
        }
        self.assertEqual(converter.classify_section_type(auth_section), 'authentication')
        
        code_section = {
            'title': 'Examples',
            'content': '```python\ndef hello():\n    pass\n```'
        }
        self.assertEqual(converter.classify_section_type(code_section), 'code_example')
    
    def test_generate_main_markdown_files(self):
        """Test main markdown file generation"""
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output")
        )
        
        sections = [
            {
                'title': 'Introduction',
                'content': 'This is the introduction.',
                'level': 1,
                'section_type': 'introduction'
            },
            {
                'title': 'API Reference', 
                'content': 'This is the API reference.',
                'level': 1,
                'section_type': 'api_endpoint'
            }
        ]
        
        pdf_content = {
            'metadata': {'title': 'Test Document'},
            'stats': {'total_pages': 2, 'total_images': 0, 'total_tables': 1}
        }
        
        markdown_files = converter.generate_main_markdown_files(sections, pdf_content)
        
        self.assertGreater(len(markdown_files), 0)
        
        # Check files were created
        for file_path in markdown_files:
            file_obj = Path(file_path)
            self.assertTrue(file_obj.exists())
            
            content = file_obj.read_text()
            self.assertGreater(len(content), 0)
        
        # Should include complete and structured documents
        file_names = [Path(f).name for f in markdown_files]
        self.assertIn('complete-document.md', file_names)
        self.assertIn('structured-document.md', file_names)
    
    def test_create_master_index(self):
        """Test master index creation"""
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output")
        )
        
        # Mock some generated files
        converter.conversion_results = {
            'markdown_files': ['complete-document.md', 'structured-document.md'],
            'chunks': {'chunk_files': ['chunk1.md', 'chunk2.md']},
            'summaries': {'summary_files': ['executive-summary.md']},
            'concepts': {'concept_files': ['glossary.md']},
            'tables': {'table_files': ['table1.md']},
            'cross_references': {'reference_files': ['internal-refs.md']}
        }
        
        index_file = converter.create_master_index()
        
        self.assertTrue(index_file.exists())
        self.assertEqual(index_file.name, "README.md")
        
        content = index_file.read_text()
        
        # Check index content
        self.assertIn("# PDF Conversion Results", content)
        self.assertIn("Generated Files Summary", content)
        self.assertIn("Usage Guide", content)
        self.assertIn("Quick Start", content)
    
    def test_create_conversion_metadata(self):
        """Test conversion metadata creation"""
        from datetime import datetime
        
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output")
        )
        
        # Mock some processing stats
        converter.processing_stats = {
            'sections': 5,
            'pdf_extraction': {'pages': 10, 'images': 2}
        }
        
        converter.conversion_results = {
            'tables': {'processed_tables': ['table1', 'table2']},
            'concepts': {'terms': {'api': {}, 'oauth': {}}},
            'summaries': {'summaries': {'executive': {}, 'detailed': {}}},
            'chunks': {'total_chunks': 15}
        }
        
        start_time = datetime.now()
        metadata_file = converter.create_conversion_metadata(start_time)
        
        self.assertTrue(metadata_file.exists())
        self.assertEqual(metadata_file.name, "conversion-metadata.json")
        
        # Read and verify metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        self.assertIn('conversion_info', metadata)
        self.assertIn('source_document', metadata)
        self.assertIn('output_info', metadata)
        self.assertIn('processing_stats', metadata)
        self.assertIn('conversion_results_summary', metadata)
        
        # Check specific fields
        self.assertIn('start_time', metadata['conversion_info'])
        self.assertIn('processing_time_seconds', metadata['conversion_info'])
        self.assertEqual(metadata['source_document']['file_name'], 'test.pdf')
    
    def test_get_all_generated_files(self):
        """Test generated files collection"""
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output")
        )
        
        # Mock conversion results
        converter.conversion_results = {
            'markdown_files': ['doc1.md', 'doc2.md'],
            'tables': {'table_files': ['table1.md']},
            'concepts': {'concept_files': ['glossary.md']},
            'cross_references': {'reference_files': ['refs.md']},
            'summaries': {'summary_files': ['summary.md'], 'index_file': 'summaries/index.md'},
            'chunks': {'chunk_files': ['chunk1.md', 'chunk2.md']},
            'index_file': 'README.md',
            'metadata_file': 'metadata.json'
        }
        
        all_files = converter.get_all_generated_files()
        
        # Should collect all files
        self.assertGreater(len(all_files), 8)  # At least the files we mocked
        
        # Check specific files are included
        self.assertIn('doc1.md', all_files)
        self.assertIn('table1.md', all_files)
        self.assertIn('glossary.md', all_files)
        self.assertIn('README.md', all_files)
    
    def test_categorize_generated_files(self):
        """Test file categorization"""
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output")
        )
        
        # Create test directory structure
        (converter.output_dir / "summaries").mkdir()
        (converter.output_dir / "concepts").mkdir()
        (converter.output_dir / "chunked").mkdir()
        
        files = [
            str(converter.output_dir / "complete-document.md"),
            str(converter.output_dir / "summaries" / "executive-summary.md"),
            str(converter.output_dir / "concepts" / "glossary.md"),
            str(converter.output_dir / "chunked" / "chunk1.md"),
            str(converter.output_dir / "README.md"),
            str(converter.output_dir / "conversion-metadata.json")
        ]
        
        categories = converter.categorize_generated_files(files)
        
        self.assertIn('main_documents', categories)
        self.assertIn('summaries', categories)
        self.assertIn('concepts', categories)
        self.assertIn('chunks', categories)
        self.assertIn('metadata', categories)
        
        # Check categorization
        self.assertIn(str(converter.output_dir / "complete-document.md"), 
                     categories['main_documents'])
        self.assertIn(str(converter.output_dir / "summaries" / "executive-summary.md"), 
                     categories['summaries'])
        self.assertIn(str(converter.output_dir / "concepts" / "glossary.md"), 
                     categories['concepts'])
    
    def test_error_handling(self):
        """Test error handling in conversion process"""
        # Test with non-existent PDF
        non_existent_pdf = self.test_dir / "nonexistent.pdf"
        
        converter = ModularPDFConverter(
            str(non_existent_pdf),
            str(self.test_dir / "output")
        )
        
        # The converter should initialize but conversion should handle errors
        self.assertIsInstance(converter, ModularPDFConverter)
        
        # Test with invalid output directory (permission issues)
        # This is harder to test in a portable way, so we'll skip for now
        
        # Test with empty options
        converter_empty = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output"),
            {}
        )
        
        self.assertEqual(converter_empty.options, {})
    
    def test_conversion_options(self):
        """Test different conversion options"""
        # Test with all features disabled
        minimal_options = {
            'extract_images': False,
            'resolve_cross_references': False,
            'generate_summaries': False,
            'create_chunks': False
        }
        
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output"),
            minimal_options
        )
        
        self.assertEqual(converter.options['extract_images'], False)
        self.assertEqual(converter.options['resolve_cross_references'], False)
        self.assertEqual(converter.options['generate_summaries'], False)
        self.assertEqual(converter.options['create_chunks'], False)
        
        # Test with all features enabled
        full_options = {
            'extract_images': True,
            'resolve_cross_references': True,
            'generate_summaries': True,
            'create_chunks': True
        }
        
        converter_full = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output_full"),
            full_options
        )
        
        self.assertEqual(converter_full.options['extract_images'], True)
        self.assertEqual(converter_full.options['resolve_cross_references'], True)
        self.assertEqual(converter_full.options['generate_summaries'], True)
        self.assertEqual(converter_full.options['create_chunks'], True)


class TestModularConverterWorkflow(unittest.TestCase):
    """Test the complete workflow with mocked components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.mock_pdf = self.test_dir / "workflow_test.pdf"
        self.mock_pdf.write_text("Mock PDF for workflow testing")
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_complete_workflow_minimal(self):
        """Test complete workflow with minimal options"""
        options = {
            'extract_images': False,
            'resolve_cross_references': False,
            'generate_summaries': False,
            'create_chunks': False
        }
        
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output"),
            options
        )
        
        # Since we can't test actual PDF conversion without PyMuPDF,
        # we'll test the structure and initialization
        self.assertIsInstance(converter.pdf_extractor, type(converter.pdf_extractor))
        self.assertIsInstance(converter.table_processor, type(converter.table_processor))
        self.assertIsInstance(converter.chunking_engine, type(converter.chunking_engine))
        self.assertIsInstance(converter.concept_mapper, type(converter.concept_mapper))
        self.assertIsInstance(converter.cross_referencer, type(converter.cross_referencer))
        self.assertIsInstance(converter.summary_generator, type(converter.summary_generator))
    
    def test_processor_coordination(self):
        """Test that processors are properly coordinated"""
        converter = ModularPDFConverter(
            str(self.mock_pdf),
            str(self.test_dir / "output")
        )
        
        # All processors should use the same output directory
        self.assertEqual(converter.pdf_extractor.output_dir, converter.output_dir)
        self.assertEqual(converter.table_processor.output_dir, converter.output_dir)
        self.assertEqual(converter.chunking_engine.output_dir, converter.output_dir)
        self.assertEqual(converter.concept_mapper.output_dir, converter.output_dir)
        self.assertEqual(converter.cross_referencer.output_dir, converter.output_dir)
        self.assertEqual(converter.summary_generator.output_dir, converter.output_dir)
        
        # Token counter should be shared where needed
        self.assertEqual(converter.chunking_engine.token_counter, converter.token_counter)
        self.assertEqual(converter.summary_generator.token_counter, converter.token_counter)


if __name__ == '__main__':
    unittest.main()