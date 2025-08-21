"""
Text processing utilities
"""
import re
from typing import List, Dict, Tuple, Optional

class TextUtils:
    """Collection of text processing utilities"""
    
    @staticmethod
    def is_header(line: str) -> bool:
        """Detect if a line is likely a header"""
        line = line.strip()
        if not line:
            return False
        
        # Markdown headers
        if line.startswith('#'):
            return True
        
        # All caps (likely header if short)
        if line.isupper() and len(line) < 60:
            return True
        
        # Numbered sections
        if re.match(r'^\d+\.?\s+[A-Z]', line):
            return True
        
        # Common header patterns
        header_patterns = [
            r'^(?:Chapter|Section|Part)\s+\d+',
            r'^[A-Z][^.!?]*$',  # Single sentence, starts with capital
            r'^\d+\.\d+\s+[A-Z]',  # Numbered subsections
        ]
        
        return any(re.match(pattern, line) for pattern in header_patterns)
    
    @staticmethod
    def determine_header_level(line: str) -> int:
        """Determine the appropriate header level (1-6)"""
        line = line.strip()
        
        # Already markdown headers
        if line.startswith('#'):
            return min(6, line.count('#'))
        
        # Chapter level
        if re.match(r'^(?:Chapter|CHAPTER)\s+\d+', line):
            return 1
        
        # Section level  
        if re.match(r'^(?:Section|SECTION)\s+\d+', line):
            return 2
        
        # Numbered sections
        if re.match(r'^\d+\.\s+', line):
            return 2
        
        # Numbered subsections
        if re.match(r'^\d+\.\d+\s+', line):
            return 3
        
        # Default based on content
        if len(line) < 30:
            return 3
        elif len(line) < 50:
            return 4
        else:
            return 5
    
    @staticmethod
    def is_code_block_start(line: str, next_lines: List[str]) -> bool:
        """Detect start of code blocks"""
        line = line.strip()
        
        # Markdown code blocks
        if line.startswith('```'):
            return True
        
        # Indented code (4+ spaces)
        if line.startswith('    ') and line.strip():
            return True
        
        # Code indicators in line
        code_indicators = [
            'function', 'class', 'def ', 'var ', 'const ', 'let ',
            'import ', 'from ', '#include', 'using namespace',
            'public class', 'private class', 'interface '
        ]
        
        if any(indicator in line.lower() for indicator in code_indicators):
            return True
        
        # Check next few lines for code patterns
        for next_line in next_lines[:3]:
            if any(indicator in next_line.lower() for indicator in code_indicators):
                return True
        
        return False
    
    @staticmethod
    def is_code_block_end(line: str, next_lines: List[str]) -> bool:
        """Detect end of code blocks"""
        line = line.strip()
        
        # Markdown code block end
        if line.endswith('```'):
            return True
        
        # Empty line followed by non-indented text
        if not line and next_lines:
            next_line = next_lines[0].strip()
            if next_line and not next_line.startswith('    '):
                return True
        
        return False
    
    @staticmethod
    def detect_code_type(line: str, next_lines: List[str]) -> str:
        """Detect the type of code block"""
        content = line + ' ' + ' '.join(next_lines[:5])
        content = content.lower()
        
        if 'python' in content or any(x in content for x in ['def ', 'import ', 'from ']):
            return 'python'
        elif any(lang in content for lang in ['javascript', 'js', 'function', 'var ', 'const ', 'let ']):
            return 'javascript'
        elif any(lang in content for lang in ['java', 'public class', 'private class']):
            return 'java'
        elif any(lang in content for lang in ['c++', 'cpp', '#include', 'using namespace']):
            return 'cpp'
        elif 'json' in content or ('{' in content and '"' in content):
            return 'json'
        elif 'sql' in content or any(x in content for x in ['select ', 'from ', 'where ']):
            return 'sql'
        else:
            return 'text'
    
    @staticmethod
    def is_table_row(line: str) -> bool:
        """Detect if line is part of a table (conservative - let pdfplumber handle real tables)"""
        line = line.strip()
        if not line:
            return False
        
        # Markdown table syntax
        if '|' in line and line.count('|') >= 2:
            return True
        
        # Tab-separated values (conservative)
        if line.count('\t') >= 2:
            return True
        
        return False
    
    @staticmethod
    def format_table_row(line: str) -> str:
        """Format a line as a markdown table row"""
        line = line.strip()
        
        # Already formatted
        if line.startswith('|') and line.endswith('|'):
            return line
        
        # Tab-separated to markdown
        if '\t' in line:
            cells = line.split('\t')
            return '| ' + ' | '.join(cells) + ' |'
        
        # Space-separated (very conservative)
        if '  ' in line:  # Multiple spaces
            cells = re.split(r'\s{2,}', line)
            return '| ' + ' | '.join(cells) + ' |'
        
        return f"| {line} |"
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        
        # Fix common PDF extraction issues
        text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('"', '"').replace('"', '"')
        
        return text.strip()
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+|www\.[^\s<>"{}|\\^`[\]]+'
        return re.findall(url_pattern, text)
    
    @staticmethod
    def extract_email_addresses(text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be improved with spaCy/NLTK)
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> List[str]:
        """Extract potential keywords from text"""
        # Simple keyword extraction (can be improved with NLP libraries)
        words = re.findall(r'\b[A-Za-z]{%d,}\b' % min_length, text)
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
            'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy',
            'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'
        }
        
        keywords = [word.lower() for word in words if word.lower() not in stop_words]
        
        # Return unique keywords
        return list(set(keywords))