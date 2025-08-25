"""
Microsoft Word document extractor using markitdown library
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from markitdown import MarkItDown
import re

try:
    from ..utils.file_utils import FileUtils
    from ..utils.text_utils import TextUtils
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.file_utils import FileUtils
    from utils.text_utils import TextUtils


class DocxExtractor:
    """Handles extraction of content from Microsoft Word documents"""
    
    def __init__(self):
        """Initialize the Word document extractor"""
        self.converter = MarkItDown()
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract content from a Word document
        
        Args:
            file_path: Path to the Word document
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Word document not found: {file_path}")
        
        if not file_path.suffix.lower() in ['.docx', '.doc']:
            raise ValueError(f"Not a Word document: {file_path}")
        
        print(f"📄 Extracting content from Word document: {file_path.name}")
        
        try:
            # Convert Word document to markdown
            result = self.converter.convert(str(file_path))
            markdown_content = result.text_content
            
            # Extract document structure
            extraction_result = {
                'success': True,
                'file_path': str(file_path),
                'file_name': file_path.name,
                'markdown_content': markdown_content,
                'sections': self._extract_sections(markdown_content),
                'tables': self._extract_tables(markdown_content),
                'images': self._extract_images(markdown_content),
                'metadata': self._extract_metadata(file_path, markdown_content),
                'raw_text': self._clean_text(markdown_content)
            }
            
            # Calculate statistics
            extraction_result['stats'] = {
                'total_characters': len(markdown_content),
                'total_words': len(markdown_content.split()),
                'total_sections': len(extraction_result['sections']),
                'total_tables': len(extraction_result['tables']),
                'total_images': len(extraction_result['images']),
                'has_toc': self._detect_toc(markdown_content)
            }
            
            print(f"✅ Successfully extracted: {extraction_result['stats']['total_words']:,} words, "
                  f"{extraction_result['stats']['total_sections']} sections")
            
            return extraction_result
            
        except Exception as e:
            print(f"❌ Error extracting Word document: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': str(file_path)
            }
    
    def _extract_sections(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Extract sections from markdown content"""
        sections = []
        
        # Split by headers (# ## ###)
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = markdown_content.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            header_match = re.match(header_pattern, line)
            
            if header_match:
                # Save previous section if exists
                if current_section:
                    current_section['content'] = '\n'.join(current_content).strip()
                    sections.append(current_section)
                    current_content = []
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2)
                current_section = {
                    'title': title,
                    'level': level,
                    'content': '',
                    'section_type': self._determine_section_type(title)
                }
            elif current_section:
                current_content.append(line)
            elif line.strip():  # Content before first header
                if not sections:
                    sections.append({
                        'title': 'Introduction',
                        'level': 1,
                        'content': '',
                        'section_type': 'introduction'
                    })
                    current_section = sections[0]
                current_content.append(line)
        
        # Save final section
        if current_section:
            current_section['content'] = '\n'.join(current_content).strip()
            if current_section not in sections:
                sections.append(current_section)
        
        return sections
    
    def _extract_tables(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Extract tables from markdown content"""
        tables = []
        
        # Find markdown tables (lines with |)
        lines = markdown_content.split('\n')
        in_table = False
        current_table_lines = []
        
        for line in lines:
            if '|' in line and not line.strip().startswith('```'):
                if not in_table:
                    in_table = True
                    current_table_lines = []
                current_table_lines.append(line)
            elif in_table and '|' not in line:
                # Table ended
                if len(current_table_lines) > 2:  # At least header, separator, one row
                    table_md = '\n'.join(current_table_lines)
                    tables.append({
                        'markdown': table_md,
                        'rows': len(current_table_lines) - 2,  # Exclude header and separator
                        'columns': table_md.split('\n')[0].count('|') - 1
                    })
                in_table = False
                current_table_lines = []
        
        # Don't forget last table if document ends with one
        if in_table and current_table_lines:
            if len(current_table_lines) > 2:
                table_md = '\n'.join(current_table_lines)
                tables.append({
                    'markdown': table_md,
                    'rows': len(current_table_lines) - 2,
                    'columns': table_md.split('\n')[0].count('|') - 1
                })
        
        return tables
    
    def _extract_images(self, markdown_content: str) -> List[Dict[str, str]]:
        """Extract image references from markdown content"""
        images = []
        
        # Find markdown images: ![alt](url)
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.findall(image_pattern, markdown_content)
        
        for alt_text, url in matches:
            images.append({
                'alt_text': alt_text,
                'url': url
            })
        
        return images
    
    def _extract_metadata(self, file_path: Path, markdown_content: str) -> Dict[str, Any]:
        """Extract metadata about the document"""
        return {
            'file_size': file_path.stat().st_size,
            'file_size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
            'extension': file_path.suffix.lower(),
            'estimated_pages': max(1, len(markdown_content) // 3000),  # Rough estimate
            'has_headers': bool(re.search(r'^#{1,6}\s+', markdown_content, re.MULTILINE)),
            'has_lists': bool(re.search(r'^[\*\-\+]\s+', markdown_content, re.MULTILINE)),
            'has_code_blocks': '```' in markdown_content
        }
    
    def _detect_toc(self, markdown_content: str) -> bool:
        """Detect if document has a table of contents"""
        toc_indicators = [
            'table of contents',
            'contents',
            'toc',
            'index'
        ]
        
        # Check first 1000 characters for TOC indicators
        content_start = markdown_content[:1000].lower()
        return any(indicator in content_start for indicator in toc_indicators)
    
    def _determine_section_type(self, title: str) -> str:
        """Determine the type of section based on title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['introduction', 'overview', 'summary', 'abstract']):
            return 'introduction'
        elif any(word in title_lower for word in ['conclusion', 'summary', 'final']):
            return 'conclusion'
        elif any(word in title_lower for word in ['method', 'approach', 'process']):
            return 'methodology'
        elif any(word in title_lower for word in ['result', 'finding', 'outcome']):
            return 'results'
        elif any(word in title_lower for word in ['reference', 'bibliography', 'citation']):
            return 'references'
        elif any(word in title_lower for word in ['appendix', 'annex', 'supplement']):
            return 'appendix'
        else:
            return 'content'
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove markdown formatting but keep the content
        cleaned = re.sub(r'#{1,6}\s+', '', text)  # Remove headers
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)  # Remove bold
        cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)  # Remove italic
        cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)  # Remove inline code
        cleaned = re.sub(r'!\[.*?\]\(.*?\)', '', cleaned)  # Remove images
        cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)  # Keep link text
        
        return TextUtils.normalize_whitespace(cleaned)


def main():
    """Test the Word document extractor"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python docx_extractor.py <path_to_docx>")
        sys.exit(1)
    
    docx_path = sys.argv[1]
    extractor = DocxExtractor()
    
    result = extractor.extract_from_file(docx_path)
    
    if result['success']:
        print(f"\n📊 Extraction Summary:")
        stats = result['stats']
        for key, value in stats.items():
            print(f"  • {key}: {value}")
        
        print(f"\n📑 Sections Found:")
        for section in result['sections'][:5]:  # Show first 5
            print(f"  • {section['title']} (Level {section['level']})")
        
        if result['tables']:
            print(f"\n📈 Tables Found: {len(result['tables'])}")
            for i, table in enumerate(result['tables'][:3], 1):
                print(f"  • Table {i}: {table['rows']} rows × {table['columns']} columns")
    else:
        print(f"❌ Extraction failed: {result['error']}")


if __name__ == "__main__":
    main()