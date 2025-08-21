"""
Unit tests for TokenCounter utility
"""
import unittest
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.token_counter import TokenCounter


class TestTokenCounter(unittest.TestCase):
    """Test cases for TokenCounter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.counter = TokenCounter()
    
    def test_initialization(self):
        """Test TokenCounter initialization"""
        self.assertIsInstance(self.counter, TokenCounter)
        self.assertIsNotNone(self.counter.encoding)
    
    def test_count_tokens_simple(self):
        """Test token counting for simple text"""
        # Basic text
        tokens = self.counter.count_tokens("Hello world")
        self.assertEqual(tokens, 2)
        
        # Empty string
        tokens = self.counter.count_tokens("")
        self.assertEqual(tokens, 0)
        
        # Single word
        tokens = self.counter.count_tokens("Hello")
        self.assertEqual(tokens, 1)
    
    def test_count_tokens_complex(self):
        """Test token counting for complex text"""
        # Technical text
        text = "The API endpoint returns JSON data with authentication tokens."
        tokens = self.counter.count_tokens(text)
        self.assertGreater(tokens, 8)  # Should be more than word count
        
        # Code snippet
        code = "def hello_world():\n    print('Hello, world!')"
        tokens = self.counter.count_tokens(code)
        self.assertGreater(tokens, 5)
    
    def test_count_tokens_markdown(self):
        """Test token counting for markdown text"""
        markdown = """# Header
        
This is a **bold** text with [links](http://example.com).

- List item 1
- List item 2

```python
print("Hello")
```
"""
        tokens = self.counter.count_tokens(markdown)
        self.assertGreater(tokens, 15)
    
    def test_estimate_tokens_from_chars(self):
        """Test token estimation from character count"""
        text = "Hello world! This is a test."
        char_count = len(text)
        estimated = self.counter.estimate_tokens_from_chars(char_count)
        actual = self.counter.count_tokens(text)
        
        # Estimation should be reasonably close (within 50% margin)
        self.assertLess(abs(estimated - actual), actual * 0.5)
    
    def test_recommend_model_for_tokens(self):
        """Test model recommendation based on token count"""
        # Small token count
        recommendation = self.counter.recommend_model_for_tokens(1000)
        self.assertIn('gpt-3.5', recommendation.lower())
        
        # Medium token count
        recommendation = self.counter.recommend_model_for_tokens(5000)
        self.assertIn('gpt-4', recommendation.lower())
        
        # Large token count
        recommendation = self.counter.recommend_model_for_tokens(50000)
        self.assertIn('claude', recommendation.lower())
        
        # Very large token count
        recommendation = self.counter.recommend_model_for_tokens(150000)
        self.assertIn('specialized', recommendation.lower())
    
    def test_get_token_breakdown(self):
        """Test detailed token breakdown"""
        text = "Hello world! This is a test with multiple sentences."
        breakdown = self.counter.get_token_breakdown(text)
        
        self.assertIn('total_tokens', breakdown)
        self.assertIn('estimated_words', breakdown)
        self.assertIn('characters', breakdown)
        self.assertIn('sentences', breakdown)
        
        self.assertGreater(breakdown['total_tokens'], 0)
        self.assertGreater(breakdown['estimated_words'], 0)
        self.assertGreater(breakdown['characters'], 0)
        self.assertGreater(breakdown['sentences'], 0)
    
    def test_count_tokens_batch(self):
        """Test batch token counting"""
        texts = [
            "Hello world",
            "This is a longer text with more content",
            "Short",
            ""
        ]
        
        results = self.counter.count_tokens_batch(texts)
        
        self.assertEqual(len(results), len(texts))
        self.assertEqual(results[0], 2)  # "Hello world"
        self.assertGreater(results[1], results[0])  # Longer text
        self.assertEqual(results[2], 1)  # "Short"
        self.assertEqual(results[3], 0)  # Empty string
    
    def test_count_tokens_by_section(self):
        """Test token counting by sections"""
        sections = [
            {'title': 'Introduction', 'content': 'This is the introduction.'},
            {'title': 'Main Content', 'content': 'This is the main content with more details.'},
            {'title': 'Conclusion', 'content': 'This is the conclusion.'}
        ]
        
        results = self.counter.count_tokens_by_section(sections)
        
        self.assertEqual(len(results), len(sections))
        for i, result in enumerate(results):
            self.assertIn('section_title', result)
            self.assertIn('content_tokens', result)
            self.assertIn('title_tokens', result)
            self.assertIn('total_tokens', result)
            self.assertEqual(result['section_title'], sections[i]['title'])
            self.assertGreater(result['total_tokens'], 0)
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # None input
        with self.assertRaises(TypeError):
            self.counter.count_tokens(None)
        
        # Non-string input
        tokens = self.counter.count_tokens(123)
        self.assertGreater(tokens, 0)  # Should convert to string
        
        # Very long text
        long_text = "word " * 10000
        tokens = self.counter.count_tokens(long_text)
        self.assertGreater(tokens, 5000)
    
    def test_special_characters(self):
        """Test handling of special characters and unicode"""
        # Unicode text
        unicode_text = "Hello 世界! café résumé naïve"
        tokens = self.counter.count_tokens(unicode_text)
        self.assertGreater(tokens, 5)
        
        # Special characters
        special_text = "!@#$%^&*()[]{}|;':\",./<>?"
        tokens = self.counter.count_tokens(special_text)
        self.assertGreater(tokens, 0)
        
        # Mixed content
        mixed_text = "API_KEY=abc123!@# user@domain.com"
        tokens = self.counter.count_tokens(mixed_text)
        self.assertGreater(tokens, 3)


if __name__ == '__main__':
    unittest.main()