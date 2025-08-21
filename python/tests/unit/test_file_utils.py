"""
Unit tests for FileUtils utility
"""
import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.file_utils import FileUtils


class TestFileUtils(unittest.TestCase):
    """Test cases for FileUtils class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for tests
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_ensure_directory(self):
        """Test directory creation"""
        # Create new directory
        new_dir = self.test_dir / "new_directory"
        result = FileUtils.ensure_directory(new_dir)
        
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_dir.is_dir())
        self.assertEqual(result, new_dir)
        
        # Create nested directories
        nested_dir = self.test_dir / "level1" / "level2" / "level3"
        result = FileUtils.ensure_directory(nested_dir)
        
        self.assertTrue(nested_dir.exists())
        self.assertTrue(nested_dir.is_dir())
        
        # Existing directory should not raise error
        existing_result = FileUtils.ensure_directory(nested_dir)
        self.assertEqual(existing_result, nested_dir)
    
    def test_safe_filename(self):
        """Test safe filename generation"""
        # Basic unsafe characters
        unsafe = "Test/File:Name"
        safe = FileUtils.safe_filename(unsafe)
        self.assertEqual(safe, "Test_File_Name")
        
        # All unsafe characters
        unsafe = '<>:"/\\|?*'
        safe = FileUtils.safe_filename(unsafe)
        self.assertNotIn('<', safe)
        self.assertNotIn('>', safe)
        self.assertNotIn(':', safe)
        self.assertNotIn('"', safe)
        self.assertNotIn('/', safe)
        self.assertNotIn('\\', safe)
        self.assertNotIn('|', safe)
        self.assertNotIn('?', safe)
        self.assertNotIn('*', safe)
        
        # Long filename truncation
        long_name = "A" * 150
        safe = FileUtils.safe_filename(long_name)
        self.assertLessEqual(len(safe), 100)
        
        # Custom max length
        safe = FileUtils.safe_filename(long_name, max_length=50)
        self.assertLessEqual(len(safe), 50)
        
        # Already safe filename
        safe_name = "already_safe_filename"
        result = FileUtils.safe_filename(safe_name)
        self.assertEqual(result, safe_name)
        
        # Empty string
        safe = FileUtils.safe_filename("")
        self.assertEqual(safe, "")
        
        # Special characters and spaces
        unsafe = "API Endpoint: GET /users/{id}"
        safe = FileUtils.safe_filename(unsafe)
        expected = "API-Endpoint-GET-users-id"
        self.assertEqual(safe, expected)
    
    def test_write_read_json(self):
        """Test JSON file operations"""
        test_data = {
            "name": "Test Document",
            "pages": 10,
            "sections": ["intro", "main", "conclusion"],
            "metadata": {
                "author": "Test Author",
                "created": "2024-01-01"
            }
        }
        
        json_file = self.test_dir / "test.json"
        
        # Write JSON
        FileUtils.write_json(test_data, json_file)
        self.assertTrue(json_file.exists())
        
        # Read JSON
        read_data = FileUtils.read_json(json_file)
        self.assertEqual(read_data, test_data)
        
        # Test with custom indent
        FileUtils.write_json(test_data, json_file, indent=4)
        content = json_file.read_text()
        self.assertIn('    "name"', content)  # Check 4-space indent
    
    def test_write_read_markdown(self):
        """Test markdown file operations"""
        markdown_content = """# Test Document

This is a **test** markdown document with:

- List items
- More items

## Code Example

```python
def hello():
    print("Hello, world!")
```

[Link](http://example.com)
"""
        
        md_file = self.test_dir / "test.md"
        
        # Write markdown
        FileUtils.write_markdown(markdown_content, md_file)
        self.assertTrue(md_file.exists())
        
        # Read markdown
        read_content = FileUtils.read_markdown(md_file)
        self.assertEqual(read_content, markdown_content)
    
    def test_create_index_file(self):
        """Test index file creation"""
        items = [
            {
                "name": "Introduction",
                "description": "Getting started guide",
                "file": "intro.md"
            },
            {
                "name": "API Reference",
                "description": "Complete API documentation",
                "file": "api.md"
            },
            {
                "name": "Examples",
                "description": "Code examples and tutorials",
                "file": "examples.md"
            }
        ]
        
        index_file = FileUtils.create_index_file(self.test_dir, "Test Documentation", items)
        
        self.assertTrue(index_file.exists())
        self.assertEqual(index_file.name, "README.md")
        
        content = FileUtils.read_markdown(index_file)
        
        # Check content structure
        self.assertIn("# Test Documentation", content)
        self.assertIn("Total Items: 3", content)
        self.assertIn("## Contents", content)
        
        # Check each item is included
        for item in items:
            self.assertIn(item["name"], content)
            self.assertIn(item["description"], content)
            self.assertIn(item["file"], content)
    
    def test_get_file_stats(self):
        """Test file statistics"""
        # Create test file
        test_file = self.test_dir / "stats_test.txt"
        test_content = "Hello, world! This is test content."
        test_file.write_text(test_content)
        
        stats = FileUtils.get_file_stats(test_file)
        
        self.assertIn('size_bytes', stats)
        self.assertIn('size_kb', stats)
        self.assertIn('modified_time', stats)
        self.assertIn('created_time', stats)
        
        self.assertEqual(stats['size_bytes'], len(test_content))
        self.assertGreater(stats['size_kb'], 0)
        self.assertIsInstance(stats['modified_time'], str)
        self.assertIsInstance(stats['created_time'], str)
        
        # Non-existent file
        non_existent = self.test_dir / "does_not_exist.txt"
        stats = FileUtils.get_file_stats(non_existent)
        self.assertEqual(stats, {})
    
    def test_list_files_by_extension(self):
        """Test file listing by extension"""
        # Create test files with different extensions
        (self.test_dir / "test1.md").write_text("Markdown 1")
        (self.test_dir / "test2.md").write_text("Markdown 2")
        (self.test_dir / "test1.txt").write_text("Text 1")
        (self.test_dir / "test2.json").write_text("{}")
        
        # Test markdown files
        md_files = FileUtils.list_files_by_extension(self.test_dir, "md")
        self.assertEqual(len(md_files), 2)
        md_names = [f.name for f in md_files]
        self.assertIn("test1.md", md_names)
        self.assertIn("test2.md", md_names)
        
        # Test with dot prefix
        md_files_dot = FileUtils.list_files_by_extension(self.test_dir, ".md")
        self.assertEqual(len(md_files_dot), 2)
        
        # Test txt files
        txt_files = FileUtils.list_files_by_extension(self.test_dir, "txt")
        self.assertEqual(len(txt_files), 1)
        self.assertEqual(txt_files[0].name, "test1.txt")
        
        # Test non-existent extension
        xyz_files = FileUtils.list_files_by_extension(self.test_dir, "xyz")
        self.assertEqual(len(xyz_files), 0)
    
    def test_create_metadata_file(self):
        """Test metadata file creation"""
        metadata = {
            "document_title": "Test Document",
            "processing_time": 45.67,
            "sections": 5,
            "tables": 2
        }
        
        metadata_file = FileUtils.create_metadata_file(self.test_dir, metadata)
        
        self.assertTrue(metadata_file.exists())
        self.assertEqual(metadata_file.name, "metadata.json")
        
        # Read and verify metadata
        saved_metadata = FileUtils.read_json(metadata_file)
        
        # Check original metadata is preserved
        for key, value in metadata.items():
            self.assertEqual(saved_metadata[key], value)
        
        # Check added fields
        self.assertIn('generated_at', saved_metadata)
        self.assertIn('directory', saved_metadata)
        self.assertEqual(saved_metadata['directory'], str(self.test_dir))
    
    def test_file_operations_with_unicode(self):
        """Test file operations with unicode content"""
        unicode_content = "Hello 世界! café résumé naïve 🌍"
        unicode_file = self.test_dir / "unicode_test.md"
        
        # Write unicode content
        FileUtils.write_markdown(unicode_content, unicode_file)
        self.assertTrue(unicode_file.exists())
        
        # Read unicode content
        read_content = FileUtils.read_markdown(unicode_file)
        self.assertEqual(read_content, unicode_content)
        
        # JSON with unicode
        unicode_data = {
            "title": "文档标题",
            "description": "café résumé",
            "emoji": "🚀📄"
        }
        
        unicode_json = self.test_dir / "unicode.json"
        FileUtils.write_json(unicode_data, unicode_json)
        
        read_data = FileUtils.read_json(unicode_json)
        self.assertEqual(read_data, unicode_data)
    
    def test_safe_filename_edge_cases(self):
        """Test edge cases for safe filename generation"""
        # Only unsafe characters
        unsafe_only = "///:::**"
        safe = FileUtils.safe_filename(unsafe_only)
        self.assertNotEqual(safe, "")  # Should produce something
        
        # Mixed safe and unsafe
        mixed = "Good_Name-with:bad/chars"
        safe = FileUtils.safe_filename(mixed)
        self.assertIn("Good_Name", safe)
        self.assertIn("with", safe)
        self.assertNotIn(":", safe)
        self.assertNotIn("/", safe)
        
        # Unicode characters
        unicode_name = "файл_文件_🗂️"
        safe = FileUtils.safe_filename(unicode_name)
        # Should handle unicode gracefully (may remove or keep depending on implementation)
        self.assertIsInstance(safe, str)
        
        # Leading/trailing hyphens and underscores
        messy = "---file___name---"
        safe = FileUtils.safe_filename(messy)
        self.assertFalse(safe.startswith('-'))
        self.assertFalse(safe.endswith('-'))
    
    def test_error_handling(self):
        """Test error handling for file operations"""
        # Try to read non-existent JSON file
        with self.assertRaises(FileNotFoundError):
            FileUtils.read_json(self.test_dir / "nonexistent.json")
        
        # Try to read non-existent markdown file
        with self.assertRaises(FileNotFoundError):
            FileUtils.read_markdown(self.test_dir / "nonexistent.md")
        
        # Invalid JSON content
        invalid_json_file = self.test_dir / "invalid.json"
        invalid_json_file.write_text("{ invalid json content")
        
        with self.assertRaises(json.JSONDecodeError):
            FileUtils.read_json(invalid_json_file)


if __name__ == '__main__':
    unittest.main()