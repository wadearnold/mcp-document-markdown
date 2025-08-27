"""
Generic PDF Extractor - Works with any PDF document type
Automatically detects structure and extracts content without hardcoded assumptions
"""
import fitz
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import json


@dataclass
class ExtractedField:
    """Represents a field extracted from any document type"""
    name: str
    content: str = ""
    field_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'content': self.content,
            'type': self.field_type,
            'metadata': self.metadata
        }


class GenericPDFExtractor:
    """Generic PDF extractor that adapts to any document structure"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration for customization"""
        self.config = config or {}
        
        # Universal character encoding fixes
        self.char_fixes = {
            'ﬁ': 'fi', 'ﬂ': 'fl', ''': "'", ''': "'",
            '"': '"', '"': '"', '–': '-', '—': '--',
            '\xa0': ' ', '\u200b': '', '\ufeff': ''
        }
        
        # Generic patterns that work across document types
        self.camel_case_pattern = re.compile(r'^[a-z]+([A-Z][a-zA-Z0-9]*)*$')
        self.pascal_case_pattern = re.compile(r'^[A-Z][a-z]+([A-Z][a-zA-Z0-9]*)*$')
        self.requirement_pattern = re.compile(r'\((Required|Optional|Conditional|Mandatory|N\/A)\)', re.IGNORECASE)
        
        # Configurable bullet contexts (can be extended via config)
        self.bullet_indicators = self.config.get('bullet_indicators', [
            'following', 'includes', 'types', 'values', 'options',
            'one of', 'such as', 'examples', 'list'
        ])
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract content from any PDF file"""
        doc = fitz.open(pdf_path)
        
        # Extract raw text
        raw_text = ""
        for page in doc:
            raw_text += page.get_text()
        
        doc.close()
        
        # Process text generically
        processed_text = self.process_text(raw_text)
        
        # Auto-detect document structure
        structure = self.detect_document_structure(processed_text)
        
        # Extract fields based on detected structure
        fields = self.extract_fields(processed_text, structure)
        
        # Generate summary
        summary = self.generate_summary(processed_text, fields, structure)
        
        return {
            'raw_text': raw_text,
            'processed_text': processed_text,
            'structure': structure,
            'fields': [field.to_dict() for field in fields],
            'summary': summary,
            'metadata': {
                'total_fields': len(fields),
                'document_type': structure.get('document_type', 'unknown'),
                'has_tables': structure.get('has_tables', False),
                'has_lists': structure.get('has_lists', False)
            }
        }
    
    def process_text(self, text: str) -> str:
        """Generic text processing that works for any PDF"""
        # Fix character encoding issues
        for old, new in self.char_fixes.items():
            text = text.replace(old, new)
        
        # Fix split bullet patterns generically
        text = self._fix_split_bullets(text)
        
        # Convert potential bullet markers
        text = self._convert_bullet_markers(text)
        
        return text
    
    def _fix_split_bullets(self, text: str) -> str:
        """Fix split bullet patterns where marker and content are on separate lines"""
        lines = text.split('\n')
        rejoined_lines = []
        i = 0
        
        while i < len(lines):
            current_line = lines[i].strip()
            
            # Look for single character lines that might be bullet markers
            if (len(current_line) == 1 and 
                current_line in 'l•-*·‣▪▫' and 
                i + 1 < len(lines)):
                
                next_line = lines[i + 1].strip()
                if next_line and len(next_line) < 200:  # Reasonable content length
                    # Rejoin as single line
                    rejoined_lines.append(f"{current_line} {next_line}")
                    i += 2
                    continue
            
            rejoined_lines.append(lines[i])
            i += 1
        
        return '\n'.join(rejoined_lines)
    
    def _convert_bullet_markers(self, text: str) -> str:
        """Convert various bullet markers to standard bullets"""
        lines = text.split('\n')
        processed_lines = []
        
        for i, line in enumerate(lines):
            # Skip if already has standard bullet
            if '•' in line:
                processed_lines.append(line)
                continue
            
            # Check for bullet patterns
            stripped = line.strip()
            if self._should_convert_to_bullet(stripped, lines, i):
                # Convert various markers to standard bullet
                indent = len(line) - len(line.lstrip())
                content = stripped[1:].strip() if len(stripped) > 1 else ""
                if content:
                    processed_lines.append(' ' * indent + f'• {content}')
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _should_convert_to_bullet(self, line: str, context_lines: List[str], index: int) -> bool:
        """Determine if a line should be converted to a bullet point"""
        if not line or len(line) < 2:
            return False
        
        first_char = line[0]
        
        # Common bullet markers
        bullet_markers = ['l', '-', '*', '·', '‣', '▪', '▫']
        if first_char not in bullet_markers:
            return False
        
        # Must have space after marker
        if len(line) < 2 or line[1] != ' ':
            return False
        
        # Context analysis - look for bullet-suggesting patterns nearby
        context_window = 3
        start = max(0, index - context_window)
        end = min(len(context_lines), index + context_window + 1)
        
        context_text = ' '.join(context_lines[start:end]).lower()
        
        # Look for list indicators
        if any(indicator in context_text for indicator in self.bullet_indicators):
            return True
        
        # Look for multiple similar markers (suggesting a list)
        similar_markers = 0
        for i in range(start, end):
            if (i != index and 
                context_lines[i].strip().startswith(f'{first_char} ')):
                similar_markers += 1
        
        return similar_markers >= 1
    
    def detect_document_structure(self, text: str) -> Dict[str, Any]:
        """Auto-detect document structure without hardcoded assumptions"""
        lines = text.split('\n')
        structure = {
            'document_type': 'unknown',
            'has_tables': False,
            'has_lists': False,
            'sections': [],
            'field_patterns': [],
            'list_patterns': []
        }
        
        # Detect tables/structured data
        table_indicators = 0
        field_like_lines = 0
        bullet_lines = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # Look for table-like structures
            if '|' in line and line.count('|') > 2:
                table_indicators += 1
            
            # Look for field-like patterns (word: description)
            if ':' in line and len(line_stripped) < 200:
                parts = line_stripped.split(':', 1)
                if (len(parts) == 2 and 
                    len(parts[0]) < 50 and 
                    parts[0].replace(' ', '').isalnum()):
                    field_like_lines += 1
            
            # Look for bullet points
            if line_stripped.startswith('•'):
                bullet_lines += 1
            
            # Detect potential sections (short lines, often in caps or title case)
            if (len(line_stripped) < 60 and 
                line_stripped and 
                (line_stripped.isupper() or line_stripped.istitle()) and
                not line_stripped.startswith('•')):
                structure['sections'].append(line_stripped)
        
        # Classify document type based on patterns
        if table_indicators > 5:
            structure['document_type'] = 'tabular'
            structure['has_tables'] = True
        elif field_like_lines > 10:
            structure['document_type'] = 'structured_fields'
        elif bullet_lines > 5:
            structure['document_type'] = 'list_heavy'
            structure['has_lists'] = True
        else:
            structure['document_type'] = 'narrative'
        
        return structure
    
    def extract_fields(self, text: str, structure: Dict[str, Any]) -> List[ExtractedField]:
        """Extract fields based on detected document structure"""
        fields = []
        
        if structure['document_type'] == 'structured_fields':
            fields = self._extract_structured_fields(text)
        elif structure['document_type'] == 'tabular':
            fields = self._extract_table_fields(text)
        elif structure['document_type'] == 'list_heavy':
            fields = self._extract_list_items(text)
        else:
            fields = self._extract_generic_content(text)
        
        return fields
    
    def _extract_structured_fields(self, text: str) -> List[ExtractedField]:
        """Extract field-value pairs from structured text"""
        fields = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and len(line) < 500:  # Reasonable field length
                parts = line.split(':', 1)
                if len(parts) == 2:
                    field_name = parts[0].strip()
                    field_content = parts[1].strip()
                    
                    if field_name and field_content:
                        # Extract any requirement info
                        requirement_match = self.requirement_pattern.search(field_content)
                        metadata = {}
                        if requirement_match:
                            metadata['requirement'] = requirement_match.group(1)
                        
                        field = ExtractedField(
                            name=field_name,
                            content=field_content,
                            field_type=self._infer_field_type(field_content),
                            metadata=metadata
                        )
                        fields.append(field)
        
        return fields
    
    def _extract_table_fields(self, text: str) -> List[ExtractedField]:
        """Extract content from table-like structures"""
        fields = []
        lines = text.split('\n')
        
        for line in lines:
            if '|' in line and line.count('|') > 2:
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if len(cells) >= 2:
                    field = ExtractedField(
                        name=cells[0] if cells[0] else f"field_{len(fields)}",
                        content=' | '.join(cells[1:]),
                        field_type='table_row',
                        metadata={'cells': cells}
                    )
                    fields.append(field)
        
        return fields
    
    def _extract_list_items(self, text: str) -> List[ExtractedField]:
        """Extract bullet point items as fields"""
        fields = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('•'):
                content = line[1:].strip()
                if content:
                    field = ExtractedField(
                        name=f"item_{len(fields) + 1}",
                        content=content,
                        field_type='list_item',
                        metadata={'line_number': i + 1}
                    )
                    fields.append(field)
        
        return fields
    
    def _extract_generic_content(self, text: str) -> List[ExtractedField]:
        """Extract content from unstructured text"""
        fields = []
        
        # Look for any identifiable patterns
        lines = text.split('\n')
        current_section = "content"
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if line looks like a header/section
            if (len(line) < 100 and 
                (line.isupper() or line.istitle()) and
                not line.startswith(('•', '-', '*'))):
                current_section = line.lower().replace(' ', '_')
                continue
            
            # Add content as generic field
            if len(line) > 10:  # Skip very short lines
                field = ExtractedField(
                    name=f"{current_section}_{len(fields) + 1}",
                    content=line,
                    field_type='content',
                    metadata={'section': current_section, 'line_number': i + 1}
                )
                fields.append(field)
        
        return fields
    
    def _infer_field_type(self, content: str) -> str:
        """Infer field type from content without hardcoded values"""
        content_lower = content.lower()
        
        # Number patterns
        if re.match(r'^\d+$', content.strip()):
            return 'integer'
        elif re.match(r'^\d*\.\d+$', content.strip()):
            return 'float'
        
        # Boolean patterns
        if any(word in content_lower for word in ['true', 'false', 'yes', 'no']):
            return 'boolean'
        
        # Date patterns
        if re.search(r'\d{2,4}[-/]\d{1,2}[-/]\d{1,2}', content):
            return 'date'
        
        # Email pattern
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content):
            return 'email'
        
        # URL pattern
        if content.startswith(('http://', 'https://', 'www.')):
            return 'url'
        
        # Default to string
        return 'string'
    
    def generate_summary(self, text: str, fields: List[ExtractedField], structure: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the extracted content"""
        return {
            'total_characters': len(text),
            'total_lines': len(text.split('\n')),
            'total_fields': len(fields),
            'document_type': structure['document_type'],
            'field_types': {
                field_type: len([f for f in fields if f.field_type == field_type])
                for field_type in set(field.field_type for field in fields)
            },
            'sections_detected': len(structure.get('sections', [])),
            'has_structured_data': len(fields) > 0
        }


def extract_pdf(pdf_path: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Main entry point for generic PDF extraction"""
    extractor = GenericPDFExtractor(config)
    return extractor.extract_from_pdf(pdf_path)