try:
    from ..utils.text_utils import TextUtils
    from ..utils.file_utils import FileUtils
except ImportError:
    # Handle running as script vs package
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.text_utils import TextUtils
    from utils.file_utils import FileUtils
"""
PDF text, image, and table extraction
"""
import fitz  # PyMuPDF
import pypdf
import pdfplumber
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import re


class PDFExtractor:
    """Handles PDF text, image, and table extraction using multiple libraries"""
    
    def __init__(self, pdf_path: str, output_dir: str, extract_images: bool = True):
        """
        Initialize PDF extractor
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Output directory for extracted content
            extract_images: Whether to extract images
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.extract_images = extract_images
        self.images_dir = self.output_dir / "images"
        
        if self.extract_images:
            FileUtils.ensure_directory(self.images_dir)
    
    def extract_all_content(self) -> Dict[str, Any]:
        """Extract all content from PDF using ULTIMATE approach"""
        # Import the ULTIMATE extractor
        try:
            from .pdf_extractor_ultimate import UltimatePDFExtractor
            
            # Use ULTIMATE extractor for best results
            ultimate_extractor = UltimatePDFExtractor(str(self.pdf_path), str(self.output_dir))
            ultimate_result = ultimate_extractor.extract()
            
            # Convert to expected format
            return {
                'text': ultimate_result['markdown'],
                'metadata': ultimate_result['metadata'],
                'tables': [{'markdown': ultimate_result['markdown']}],
                'fields': ultimate_result['fields'],
                'stats': ultimate_result['stats'],
                'quality_level': ultimate_result['stats']['quality_level'],
                'pages': [{'page_num': i+1, 'text': ''} for i in range(ultimate_result['metadata']['pages'])],
                'images': []
            }
            
        except ImportError:
            # Fallback to original method
            print("ULTIMATE extractor not available, using standard extraction")
            return self._extract_standard_method()
    
    def _extract_standard_method(self) -> Dict[str, Any]:
        """Original extraction method as fallback"""
        # Try PyMuPDF first for comprehensive extraction
        fitz_content = self.extract_with_pymupdf()
        
        # Extract tables with pdfplumber
        tables_content = self.extract_tables_with_pdfplumber()
        
        # Extract structure with pypdf
        structure = self.extract_structure_with_pypdf()
        
        # Combine all content
        combined_content = self.combine_content(fitz_content, tables_content, structure)
        
        return combined_content
    
    def extract_with_pymupdf(self) -> Dict[str, Any]:
        """Extract text and images using PyMuPDF"""
        content = {
            'text': '',
            'images': [],
            'pages': [],
            'metadata': {}
        }
        
        try:
            doc = fitz.open(self.pdf_path)
            
            # Extract metadata
            content['metadata'] = {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'page_count': len(doc)
            }
            
            full_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text
                page_text = page.get_text()
                full_text.append(page_text)
                
                content['pages'].append({
                    'page_num': page_num + 1,
                    'text': page_text,
                    'char_count': len(page_text)
                })
                
                # Extract images if requested
                if self.extract_images:
                    images = self.extract_images_from_page(page, page_num)
                    content['images'].extend(images)
            
            content['text'] = '\n\n'.join(full_text)
            doc.close()
            
        except Exception as e:
            print(f"PyMuPDF extraction failed: {e}")
            content = self.basic_extraction()
        
        return content
    
    def extract_images_from_page(self, page, page_num: int) -> List[Dict[str, Any]]:
        """Extract images from a page"""
        images = []
        
        try:
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    if pix.n - pix.alpha < 4:  # Skip if not RGB/RGBA
                        image_filename = f"page_{page_num + 1}_img_{img_index}.png"
                        image_path = self.images_dir / image_filename
                        pix.save(image_path)
                        
                        images.append({
                            'filename': image_filename,
                            'path': str(image_path),
                            'page': page_num + 1,
                            'index': img_index,
                            'width': pix.width,
                            'height': pix.height
                        })
                    
                    pix = None  # Free memory
                    
                except Exception as e:
                    print(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
        
        except Exception as e:
            print(f"Failed to get images from page {page_num + 1}: {e}")
        
        return images
    
    def extract_tables_with_pdfplumber(self) -> List[Dict[str, Any]]:
        """Extract tables using pdfplumber"""
        tables = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    
                    for table_index, table in enumerate(page_tables):
                        if table and len(table) > 1:  # Skip empty or single-row tables
                            tables.append({
                                'page': page_num,
                                'index': table_index,
                                'data': table,
                                'rows': len(table),
                                'cols': len(table[0]) if table else 0,
                                'markdown': self.table_to_markdown(table)
                            })
        
        except Exception as e:
            print(f"pdfplumber table extraction failed: {e}")
        
        return tables
    
    def table_to_markdown(self, table: List[List]) -> str:
        """Convert a table (list of lists) to markdown format"""
        if not table or not table[0]:
            return ""
        
        try:
            # Convert to DataFrame for better handling
            df = pd.DataFrame(table[1:], columns=table[0])
            
            # Clean up None values
            df = df.fillna('')
            
            # Convert to markdown
            markdown = df.to_markdown(index=False)
            return markdown
            
        except Exception:
            # Fallback to simple markdown conversion
            markdown_lines = []
            
            # Header
            if table:
                header = '| ' + ' | '.join(str(cell) if cell else '' for cell in table[0]) + ' |'
                separator = '|' + '|'.join(' --- ' for _ in table[0]) + '|'
                markdown_lines.extend([header, separator])
                
                # Data rows
                for row in table[1:]:
                    row_md = '| ' + ' | '.join(str(cell) if cell else '' for cell in row) + ' |'
                    markdown_lines.append(row_md)
            
            return '\n'.join(markdown_lines)
    
    def extract_structure_with_pypdf(self) -> Dict[str, Any]:
        """Extract document structure using pypdf"""
        structure = {
            'outline': [],
            'bookmarks': [],
            'metadata': {}
        }
        
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                
                # Extract metadata
                if reader.metadata:
                    structure['metadata'] = {
                        'title': reader.metadata.get('/Title', ''),
                        'author': reader.metadata.get('/Author', ''),
                        'subject': reader.metadata.get('/Subject', ''),
                        'creator': reader.metadata.get('/Creator', ''),
                        'producer': reader.metadata.get('/Producer', ''),
                    }
                
                # Extract outline/bookmarks
                if reader.outline:
                    structure['outline'] = self.process_outline(reader.outline)
        
        except Exception as e:
            print(f"pypdf structure extraction failed: {e}")
        
        return structure
    
    def process_outline(self, outline, level: int = 0) -> List[Dict[str, Any]]:
        """Process PDF outline/bookmarks"""
        processed = []
        
        for item in outline:
            if isinstance(item, list):
                # Nested outline items
                processed.extend(self.process_outline(item, level + 1))
            else:
                # Individual bookmark
                bookmark = {
                    'title': str(item.title) if hasattr(item, 'title') else str(item),
                    'level': level,
                    'page': item.page.idnum if hasattr(item, 'page') and item.page else None
                }
                processed.append(bookmark)
        
        return processed
    
    def combine_content(self, fitz_content: Dict, tables_content: List, structure: Dict) -> Dict[str, Any]:
        """Combine content from different sources into final result"""
        # Process the text to add structure
        structured_text = self.process_text_structure(fitz_content['text'])
        
        # Integrate tables into text
        text_with_tables = self.integrate_tables(structured_text, tables_content)
        
        return {
            'text': text_with_tables,
            'original_text': fitz_content['text'],
            'images': fitz_content['images'],
            'tables': tables_content,
            'pages': fitz_content['pages'],
            'structure': structure,
            'metadata': {**fitz_content['metadata'], **structure['metadata']},
            'stats': {
                'total_pages': len(fitz_content['pages']),
                'total_images': len(fitz_content['images']),
                'total_tables': len(tables_content),
                'total_chars': len(fitz_content['text']),
                'has_outline': bool(structure['outline'])
            }
        }
    
    def process_text_structure(self, text: str) -> str:
        """Identify headers, code blocks, lists, and structure in text"""
        lines = text.split('\n')
        processed_lines = []
        in_code_block = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            remaining_lines = lines[i+1:i+5]  # Look ahead 5 lines
            
            if not in_code_block:
                # Check for code block start
                if TextUtils.is_code_block_start(line, remaining_lines):
                    code_type = TextUtils.detect_code_type(line, remaining_lines)
                    processed_lines.append(f"```{code_type}")
                    in_code_block = True
                
                # Check for headers
                elif TextUtils.is_header(line):
                    level = TextUtils.determine_header_level(line)
                    header_markdown = '#' * level + ' ' + line.strip()
                    processed_lines.append(header_markdown)
                    i += 1
                    continue
                
                # Check for table rows
                elif TextUtils.is_table_row(line):
                    formatted_row = TextUtils.format_table_row(line)
                    processed_lines.append(formatted_row)
                    i += 1
                    continue
            
            else:
                # Check for code block end
                if TextUtils.is_code_block_end(line, remaining_lines):
                    processed_lines.append("```")
                    in_code_block = False
            
            # Add line as-is
            processed_lines.append(line)
            i += 1
        
        # Close code block if still open
        if in_code_block:
            processed_lines.append("```")
        
        return '\n'.join(processed_lines)
    
    def integrate_tables(self, text: str, tables: List[Dict]) -> str:
        """Integrate extracted tables into the text"""
        if not tables:
            return text
        
        # Simple integration - add tables at the end with references
        text_with_tables = text
        
        # Add table references in text
        for table in tables:
            table_ref = f"\n\n**Table {table['index'] + 1} (Page {table['page']}):**\n\n{table['markdown']}\n"
            text_with_tables += table_ref
        
        return text_with_tables
    
    def basic_extraction(self) -> Dict[str, Any]:
        """Fallback basic extraction method"""
        content = {
            'text': '',
            'images': [],
            'pages': [],
            'metadata': {},
            'stats': {'extraction_method': 'basic_fallback'}
        }
        
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                
                text_parts = []
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    text_parts.append(page_text)
                    
                    content['pages'].append({
                        'page_num': page_num + 1,
                        'text': page_text,
                        'char_count': len(page_text)
                    })
                
                content['text'] = '\n\n'.join(text_parts)
                content['metadata'] = {'page_count': len(reader.pages)}
        
        except Exception as e:
            print(f"Basic extraction also failed: {e}")
            content['text'] = f"Failed to extract text from {self.pdf_path}"
        
        return content