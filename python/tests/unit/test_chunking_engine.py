"""
Unit tests for ChunkingEngine processor
"""
import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from processors.chunking_engine import ChunkingEngine
from utils.token_counter import TokenCounter


class TestChunkingEngine(unittest.TestCase):
    """Test cases for ChunkingEngine class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.token_counter = TokenCounter()
        self.chunking_engine = ChunkingEngine(str(self.test_dir), self.token_counter)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test ChunkingEngine initialization"""
        self.assertIsInstance(self.chunking_engine, ChunkingEngine)
        self.assertEqual(self.chunking_engine.output_dir, self.test_dir)
        self.assertTrue(self.chunking_engine.chunked_dir.exists())
        
        # Check chunk sizes are defined
        self.assertIn('small', self.chunking_engine.chunk_sizes)
        self.assertIn('medium', self.chunking_engine.chunk_sizes)
        self.assertIn('large', self.chunking_engine.chunk_sizes)
        self.assertIn('xlarge', self.chunking_engine.chunk_sizes)
    
    def test_analyze_sections_for_chunking(self):
        """Test section analysis for chunking strategy"""
        sections = [
            {
                'title': 'Introduction',
                'content': 'This is a short introduction section.',
                'section_type': 'introduction'
            },
            {
                'title': 'API Endpoint',
                'content': 'This is a longer section with more detailed content about API endpoints and how to use them effectively.',
                'section_type': 'api_endpoint'
            }
        ]
        
        analysis = self.chunking_engine.analyze_sections_for_chunking(sections)
        
        self.assertEqual(len(analysis), 2)
        
        # Check analysis structure
        for item in analysis:
            self.assertIn('section_id', item)
            self.assertIn('title', item)
            self.assertIn('content', item)
            self.assertIn('tokens', item)
            self.assertIn('section_type', item)
            self.assertIn('chunking_strategy', item)
            self.assertIn('priority', item)
    
    def test_determine_chunking_strategy(self):
        """Test chunking strategy determination"""
        # Small content (no chunking needed)
        small_tokens = 1000
        strategy = self.chunking_engine.determine_chunking_strategy(small_tokens, 'content')
        
        self.assertFalse(strategy['needs_chunking'])
        self.assertIn('small', strategy['recommended_sizes'])
        self.assertIn('medium', strategy['recommended_sizes'])
        self.assertIn('large', strategy['recommended_sizes'])
        self.assertIn('xlarge', strategy['recommended_sizes'])
        
        # Large content (needs chunking)
        large_tokens = 100000
        strategy = self.chunking_engine.determine_chunking_strategy(large_tokens, 'content')
        
        self.assertTrue(strategy['needs_chunking'])
        self.assertEqual(strategy['approach'], 'semantic_split')
        
        # API endpoint (preserve structure)
        api_strategy = self.chunking_engine.determine_chunking_strategy(5000, 'api_endpoint')
        self.assertEqual(api_strategy['approach'], 'preserve_structure')
        
        # Table content (preserve rows)
        table_strategy = self.chunking_engine.determine_chunking_strategy(5000, 'table')
        self.assertEqual(table_strategy['approach'], 'preserve_rows')
    
    def test_get_section_priority(self):
        """Test section priority assignment"""
        # High priority sections
        self.assertEqual(self.chunking_engine.get_section_priority('introduction'), 10)
        self.assertEqual(self.chunking_engine.get_section_priority('summary'), 10)
        self.assertEqual(self.chunking_engine.get_section_priority('authentication'), 9)
        
        # Medium priority sections
        self.assertEqual(self.chunking_engine.get_section_priority('api_endpoint'), 8)
        self.assertEqual(self.chunking_engine.get_section_priority('examples'), 6)
        
        # Lower priority sections
        self.assertEqual(self.chunking_engine.get_section_priority('reference'), 5)
        self.assertEqual(self.chunking_engine.get_section_priority('appendix'), 3)
        
        # Default priority
        self.assertEqual(self.chunking_engine.get_section_priority('unknown_type'), 4)
    
    def test_split_content_semantically(self):
        """Test semantic content splitting"""
        content = """# First Section
        
This is content for the first section with some details.

## Subsection 1.1

More content here with additional information.

# Second Section

This is the second main section with different content.

## Subsection 2.1

Final subsection with concluding remarks.
"""
        
        chunks = self.chunking_engine.split_content_semantically(content, "Test Title")
        
        self.assertGreater(len(chunks), 1)
        
        # Each chunk should contain meaningful content
        for chunk in chunks:
            self.assertGreater(len(chunk.strip()), 0)
    
    def test_split_preserving_structure(self):
        """Test structure-preserving splitting"""
        content = """# API Endpoint

This endpoint allows you to retrieve user data.

```python
def get_user(user_id):
    response = api.get(f'/users/{user_id}')
    return response.json()
```

## Parameters

- user_id: The unique identifier for the user

## Response

The response includes user details in JSON format.
"""
        
        chunks = self.chunking_engine.split_preserving_structure(content, "API Endpoint")
        
        # Should not split inside code blocks
        combined = '\n'.join(chunks)
        self.assertIn('```python', combined)
        self.assertIn('```', combined)
        
        # Code block should be preserved in one chunk
        code_found = False
        for chunk in chunks:
            if '```python' in chunk and 'return response.json()' in chunk:
                code_found = True
                break
        self.assertTrue(code_found)
    
    def test_split_preserving_rows(self):
        """Test row-preserving splitting for tables"""
        content = """# Table Data

| Name | Age | City |
|------|-----|------|
| John | 25 | NYC |
| Jane | 30 | LA |
| Bob | 35 | Chicago |

This is some additional content after the table.

| Product | Price | Stock |
|---------|--------|-------|
| Widget A | $10 | 100 |
| Widget B | $15 | 50 |
"""
        
        chunks = self.chunking_engine.split_preserving_rows(content, "Table Data")
        
        # Tables should not be split
        combined = '\n'.join(chunks)
        self.assertIn('| Name | Age | City |', combined)
        self.assertIn('| Product | Price | Stock |', combined)
    
    def test_split_content_by_tokens(self):
        """Test token-based content splitting"""
        # Create content with known structure
        sentences = [
            "This is the first sentence.",
            "This is the second sentence with more content.",
            "Here is a third sentence for testing.",
            "A fourth sentence to ensure proper splitting.",
            "Finally, the fifth sentence completes the test."
        ]
        content = " ".join(sentences)
        
        chunks = self.chunking_engine.split_content_by_tokens(content, "Test Title")
        
        self.assertGreater(len(chunks), 0)
        
        # Each chunk should respect token limits
        for chunk in chunks:
            token_count = self.token_counter.count_tokens(chunk)
            # Should be reasonable size (allowing some flexibility)
            self.assertLessEqual(token_count, self.chunking_engine.chunk_sizes['medium'] * 1.2)
    
    def test_create_single_chunk_file(self):
        """Test single chunk file creation"""
        section_id = 1
        title = "Test Section"
        content = "This is test content for a single chunk file."
        size_name = "medium"
        plan_item = {
            'section_type': 'content',
            'priority': 5
        }
        
        chunk_file = self.chunking_engine.create_single_chunk_file(
            section_id, title, content, size_name, plan_item
        )
        
        self.assertTrue(chunk_file.exists())
        self.assertIn("01-Test-Section-medium.md", str(chunk_file))
        
        # Check file content
        file_content = chunk_file.read_text()
        self.assertIn("# Test Section", file_content)
        self.assertIn("This is test content", file_content)
        self.assertIn("Chunk**: 1 of 1", file_content)
        self.assertIn("Size**: medium", file_content)
    
    def test_create_chunk_file(self):
        """Test chunk file creation"""
        section_id = 2
        title = "Multi Chunk Section"
        content = "This is content for a multi-chunk file."
        size_name = "small"
        chunk_num = 2
        total_chunks = 3
        plan_item = {
            'section_type': 'api_endpoint',
            'priority': 8
        }
        
        chunk_file = self.chunking_engine.create_chunk_file(
            section_id, title, content, size_name, chunk_num, total_chunks, plan_item
        )
        
        self.assertTrue(chunk_file.exists())
        self.assertIn("02-Multi-Chunk-Section-chunk-2-small.md", str(chunk_file))
        
        # Check file content
        file_content = chunk_file.read_text()
        self.assertIn("# Multi Chunk Section", file_content)
        self.assertIn("Chunk**: 2 of 3", file_content)
        self.assertIn("Size**: small", file_content)
        self.assertIn("Section Type**: api_endpoint", file_content)
    
    def test_format_chunk_content(self):
        """Test chunk content formatting"""
        title = "Test Chunk"
        content = "This is the main content of the chunk."
        size_name = "medium"
        chunk_num = 1
        total_chunks = 2
        plan_item = {
            'section_type': 'examples',
            'priority': 6
        }
        
        formatted = self.chunking_engine.format_chunk_content(
            title, content, size_name, chunk_num, total_chunks, plan_item
        )
        
        # Check header information
        self.assertIn("# Test Chunk", formatted)
        self.assertIn("Chunk**: 1 of 2", formatted)
        self.assertIn("Size**: medium", formatted)
        self.assertIn("Section Type**: examples", formatted)
        self.assertIn("Processing Priority**: 6", formatted)
        self.assertIn("Generated**:", formatted)
        
        # Check content is included
        self.assertIn("This is the main content", formatted)
        
        # Check processing guidance is included
        self.assertIn("## Processing Guidance", formatted)
    
    def test_get_processing_guidance(self):
        """Test processing guidance generation"""
        # Test different size guidance
        small_guidance = self.chunking_engine.get_processing_guidance("small", "content", 1000)
        self.assertTrue(any("GPT-3.5" in g for g in small_guidance))
        
        medium_guidance = self.chunking_engine.get_processing_guidance("medium", "content", 5000)
        self.assertTrue(any("GPT-4" in g for g in medium_guidance))
        
        large_guidance = self.chunking_engine.get_processing_guidance("large", "content", 20000)
        self.assertTrue(any("GPT-4-32K" in g for g in large_guidance))
        
        xlarge_guidance = self.chunking_engine.get_processing_guidance("xlarge", "content", 80000)
        self.assertTrue(any("Claude-2" in g for g in xlarge_guidance))
        
        # Test section type guidance
        api_guidance = self.chunking_engine.get_processing_guidance("medium", "api_endpoint", 5000)
        self.assertTrue(any("API documentation" in g for g in api_guidance))
        
        auth_guidance = self.chunking_engine.get_processing_guidance("medium", "authentication", 3000)
        self.assertTrue(any("authentication info" in g for g in auth_guidance))
        
        # Test token-based guidance
        concise_guidance = self.chunking_engine.get_processing_guidance("small", "content", 500)
        self.assertTrue(any("Concise content" in g for g in concise_guidance))
        
        substantial_guidance = self.chunking_engine.get_processing_guidance("large", "content", 6000)
        self.assertTrue(any("Substantial content" in g for g in substantial_guidance))
    
    def test_process_sections_for_chunking_integration(self):
        """Test end-to-end section processing"""
        sections = [
            {
                'title': 'Getting Started',
                'content': 'This is a short getting started guide with basic information.',
                'section_type': 'introduction'
            },
            {
                'title': 'API Reference',
                'content': 'This is a much longer API reference section with detailed information about endpoints, parameters, authentication methods, and example responses. ' * 10,
                'section_type': 'api_endpoint'
            }
        ]
        
        created_files = self.chunking_engine.process_sections_for_chunking(sections)
        
        self.assertGreater(len(created_files), 0)
        
        # Check that files were actually created
        for file_path in created_files:
            file_obj = Path(file_path)
            self.assertTrue(file_obj.exists())
            
            # Check file has content
            content = file_obj.read_text()
            self.assertGreater(len(content), 0)
        
        # Should include manifest file
        manifest_files = [f for f in created_files if 'manifest' in f]
        self.assertGreater(len(manifest_files), 0)


if __name__ == '__main__':
    unittest.main()