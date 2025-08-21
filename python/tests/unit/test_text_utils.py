"""
Unit tests for TextUtils utility
"""
import unittest
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.text_utils import TextUtils


class TestTextUtils(unittest.TestCase):
    """Test cases for TextUtils class"""
    
    def test_is_header(self):
        """Test header detection"""
        # Markdown headers
        self.assertTrue(TextUtils.is_header("# Main Header"))
        self.assertTrue(TextUtils.is_header("## Sub Header"))
        self.assertTrue(TextUtils.is_header("### Sub Sub Header"))
        self.assertTrue(TextUtils.is_header("#### Level 4"))
        self.assertTrue(TextUtils.is_header("##### Level 5"))
        self.assertTrue(TextUtils.is_header("###### Level 6"))
        
        # Not headers
        self.assertFalse(TextUtils.is_header("This is normal text"))
        self.assertFalse(TextUtils.is_header("Just a # symbol in text"))
        self.assertFalse(TextUtils.is_header(""))
        self.assertFalse(TextUtils.is_header("####### Too many #"))
        
        # Edge cases
        self.assertTrue(TextUtils.is_header("#Header without space"))
        self.assertFalse(TextUtils.is_header(" # Indented header"))
    
    def test_determine_header_level(self):
        """Test header level determination"""
        self.assertEqual(TextUtils.determine_header_level("# Level 1"), 1)
        self.assertEqual(TextUtils.determine_header_level("## Level 2"), 2)
        self.assertEqual(TextUtils.determine_header_level("### Level 3"), 3)
        self.assertEqual(TextUtils.determine_header_level("#### Level 4"), 4)
        self.assertEqual(TextUtils.determine_header_level("##### Level 5"), 5)
        self.assertEqual(TextUtils.determine_header_level("###### Level 6"), 6)
        
        # Non-headers should return 0
        self.assertEqual(TextUtils.determine_header_level("Not a header"), 0)
        self.assertEqual(TextUtils.determine_header_level("####### Too many"), 0)
    
    def test_is_code_block_start(self):
        """Test code block start detection"""
        # With remaining lines
        remaining_lines = ["print('hello')", "return True", "```"]
        
        self.assertTrue(TextUtils.is_code_block_start("```python", remaining_lines))
        self.assertTrue(TextUtils.is_code_block_start("```", remaining_lines))
        self.assertTrue(TextUtils.is_code_block_start("```javascript", remaining_lines))
        
        # Without proper ending
        incomplete_lines = ["print('hello')", "return True"]
        self.assertFalse(TextUtils.is_code_block_start("```python", incomplete_lines))
        
        # Not code blocks
        self.assertFalse(TextUtils.is_code_block_start("Normal text", remaining_lines))
        self.assertFalse(TextUtils.is_code_block_start("``Two backticks", remaining_lines))
    
    def test_is_code_block_end(self):
        """Test code block end detection"""
        remaining_lines = ["", "Next paragraph"]
        
        self.assertTrue(TextUtils.is_code_block_end("```", remaining_lines))
        
        # Not code block ends
        self.assertFalse(TextUtils.is_code_block_end("```python", remaining_lines))
        self.assertFalse(TextUtils.is_code_block_end("Normal text", remaining_lines))
        self.assertFalse(TextUtils.is_code_block_end("``", remaining_lines))
    
    def test_detect_code_type(self):
        """Test code type detection"""
        remaining_lines = ["print('hello')", "def func():", "    pass"]
        
        # Explicit language
        self.assertEqual(TextUtils.detect_code_type("```python", remaining_lines), "python")
        self.assertEqual(TextUtils.detect_code_type("```javascript", remaining_lines), "javascript")
        self.assertEqual(TextUtils.detect_code_type("```bash", remaining_lines), "bash")
        
        # Auto-detection from content
        python_lines = ["def hello():", "    print('world')", "return True"]
        detected = TextUtils.detect_code_type("```", python_lines)
        self.assertEqual(detected, "python")
        
        js_lines = ["function hello() {", "    console.log('world');", "}"]
        detected = TextUtils.detect_code_type("```", js_lines)
        self.assertEqual(detected, "javascript")
        
        bash_lines = ["#!/bin/bash", "echo 'hello'", "ls -la"]
        detected = TextUtils.detect_code_type("```", bash_lines)
        self.assertEqual(detected, "bash")
        
        # Unknown type
        unknown_lines = ["unknown syntax here", "no patterns match"]
        detected = TextUtils.detect_code_type("```", unknown_lines)
        self.assertEqual(detected, "")
    
    def test_is_table_row(self):
        """Test table row detection"""
        # Valid table rows
        self.assertTrue(TextUtils.is_table_row("| Column 1 | Column 2 | Column 3 |"))
        self.assertTrue(TextUtils.is_table_row("|---|---|---|"))
        self.assertTrue(TextUtils.is_table_row("| Name | Age | City |"))
        
        # Invalid table rows
        self.assertFalse(TextUtils.is_table_row("Just a | pipe in text"))
        self.assertFalse(TextUtils.is_table_row("| Only one pipe"))
        self.assertFalse(TextUtils.is_table_row("No pipes at all"))
        self.assertFalse(TextUtils.is_table_row(""))
    
    def test_format_table_row(self):
        """Test table row formatting"""
        # Already well formatted
        row = "| Name | Age | City |"
        formatted = TextUtils.format_table_row(row)
        self.assertEqual(formatted, row)
        
        # Needs formatting
        messy_row = "|Name|Age|City|"
        formatted = TextUtils.format_table_row(messy_row)
        self.assertEqual(formatted, "| Name | Age | City |")
        
        # With extra spaces
        spaced_row = "|  Name  |  Age  |  City  |"
        formatted = TextUtils.format_table_row(spaced_row)
        self.assertEqual(formatted, "| Name | Age | City |")
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        # Remove extra whitespace
        messy_text = "  Hello    world  \n\n  with   extra   spaces  "
        cleaned = TextUtils.clean_text(messy_text)
        expected = "Hello world with extra spaces"
        self.assertEqual(cleaned, expected)
        
        # Handle special characters
        special_text = "Text\u00a0with\u2000special\u2028spaces"
        cleaned = TextUtils.clean_text(special_text)
        self.assertNotIn('\u00a0', cleaned)  # Non-breaking space
        self.assertNotIn('\u2000', cleaned)  # En quad
        
        # Empty and whitespace
        self.assertEqual(TextUtils.clean_text(""), "")
        self.assertEqual(TextUtils.clean_text("   "), "")
        self.assertEqual(TextUtils.clean_text("\n\n\n"), "")
    
    def test_split_into_sentences(self):
        """Test sentence splitting"""
        # Simple sentences
        text = "This is sentence one. This is sentence two. And this is three."
        sentences = TextUtils.split_into_sentences(text)
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "This is sentence one.")
        self.assertEqual(sentences[1], "This is sentence two.")
        self.assertEqual(sentences[2], "And this is three.")
        
        # Complex punctuation
        complex_text = "Dr. Smith went to the U.S.A. He said 'Hello!' Then he left..."
        sentences = TextUtils.split_into_sentences(complex_text)
        self.assertGreater(len(sentences), 1)
        
        # Empty text
        self.assertEqual(TextUtils.split_into_sentences(""), [])
        
        # Single sentence
        single = "Just one sentence"
        sentences = TextUtils.split_into_sentences(single)
        self.assertEqual(len(sentences), 1)
        self.assertEqual(sentences[0], single)
    
    def test_extract_urls(self):
        """Test URL extraction"""
        text = "Visit https://example.com or http://test.org for more info."
        urls = TextUtils.extract_urls(text)
        self.assertEqual(len(urls), 2)
        self.assertIn("https://example.com", urls)
        self.assertIn("http://test.org", urls)
        
        # No URLs
        no_urls = "This text has no URLs in it."
        urls = TextUtils.extract_urls(no_urls)
        self.assertEqual(len(urls), 0)
        
        # Complex URLs
        complex_text = "API endpoint: https://api.example.com/v1/users?page=1&limit=10"
        urls = TextUtils.extract_urls(complex_text)
        self.assertEqual(len(urls), 1)
        self.assertIn("https://api.example.com/v1/users?page=1&limit=10", urls)
    
    def test_extract_email_addresses(self):
        """Test email address extraction"""
        text = "Contact us at support@example.com or admin@test.org"
        emails = TextUtils.extract_email_addresses(text)
        self.assertEqual(len(emails), 2)
        self.assertIn("support@example.com", emails)
        self.assertIn("admin@test.org", emails)
        
        # No emails
        no_emails = "This text has no email addresses."
        emails = TextUtils.extract_email_addresses(no_emails)
        self.assertEqual(len(emails), 0)
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization"""
        # Multiple types of whitespace
        text = "Hello\t\tworld\n\nwith   various\r\nwhitespace"
        normalized = TextUtils.normalize_whitespace(text)
        expected = "Hello world with various whitespace"
        self.assertEqual(normalized, expected)
        
        # Preserve single spaces
        text = "Hello world"
        normalized = TextUtils.normalize_whitespace(text)
        self.assertEqual(normalized, text)
    
    def test_truncate_text(self):
        """Test text truncation"""
        text = "This is a long text that needs to be truncated"
        
        # Truncate to word boundary
        truncated = TextUtils.truncate_text(text, 20, word_boundary=True)
        self.assertLessEqual(len(truncated), 25)  # Allow for ellipsis
        self.assertTrue(truncated.endswith('...'))
        
        # Truncate exactly
        truncated = TextUtils.truncate_text(text, 20, word_boundary=False)
        self.assertEqual(len(truncated), 23)  # 20 + '...'
        
        # Text shorter than limit
        short_text = "Short"
        truncated = TextUtils.truncate_text(short_text, 20)
        self.assertEqual(truncated, short_text)
    
    def test_count_words(self):
        """Test word counting"""
        # Simple text
        self.assertEqual(TextUtils.count_words("Hello world"), 2)
        self.assertEqual(TextUtils.count_words("One"), 1)
        self.assertEqual(TextUtils.count_words(""), 0)
        
        # Complex text with punctuation
        text = "Hello, world! How are you today?"
        count = TextUtils.count_words(text)
        self.assertEqual(count, 6)
        
        # Text with multiple spaces
        spaced_text = "Hello    world    test"
        count = TextUtils.count_words(spaced_text)
        self.assertEqual(count, 3)
    
    def test_remove_markdown(self):
        """Test markdown removal"""
        markdown = """# Header
        
**Bold text** and *italic text*

- List item 1
- List item 2

[Link](http://example.com)

`code` and ```code block```
"""
        plain = TextUtils.remove_markdown(markdown)
        
        # Should not contain markdown syntax
        self.assertNotIn('#', plain)
        self.assertNotIn('**', plain)
        self.assertNotIn('*', plain)
        self.assertNotIn('[', plain)
        self.assertNotIn('](', plain)
        self.assertNotIn('`', plain)
        
        # Should contain the actual text
        self.assertIn('Header', plain)
        self.assertIn('Bold text', plain)
        self.assertIn('italic text', plain)
        self.assertIn('List item 1', plain)


if __name__ == '__main__':
    unittest.main()