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
        
        # Enhanced detection counters
        table_indicators = 0
        field_like_lines = 0
        bullet_lines = 0
        section_hierarchy_lines = 0
        
        # Generic table patterns (not format-specific)
        table_patterns = [
            r'Table\s+\d+',                    # "Table 1", "Table 2" 
            r'^\s*\|\s*[^|]+\s*\|',           # Pipe-separated rows
            r'^\s*\+-+\+',                     # ASCII table borders
            r'^\s*[A-Z][^:]+:\s*[A-Z]',       # Key: Value pairs (structured)
            r'^\s*\d+\.\s+\w+\s+\w+',         # Numbered list items with multiple columns
            r'^\s*[A-Z]{3,}\s+[A-Z]{3,}',     # Header-like ALL CAPS rows
        ]
        
        # Generic list patterns
        list_patterns = [
            r'^\s*[-*•]\s+',                   # Standard bullets
            r'^\s*\d+[.)]\s+',                 # Numbered lists
            r'^\s*[a-z][.)]\s+',               # Lettered lists
            r'^\s*[ivx]+[.)]\s+',              # Roman numerals
        ]
        
        # Generic section hierarchy patterns
        section_patterns = [
            r'^\s*(\d+)\.\s*([A-Z].*)',        # "1. Introduction"
            r'^\s*(\d+\.\d+)\s+([A-Z].*)',     # "1.1 Overview"
            r'^\s*(Chapter|Section)\s+(\d+)',   # "Chapter 1", "Section 2"
        ]
        
        for line in lines:
            line_stripped = line.strip()
            
            # Enhanced table detection
            if '|' in line and line.count('|') > 2:
                table_indicators += 1
            
            # Check generic table patterns
            for pattern in table_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    table_indicators += 1
                    break
            
            # Enhanced list detection
            if line_stripped.startswith('•'):
                bullet_lines += 1
            else:
                for pattern in list_patterns:
                    if re.search(pattern, line):
                        bullet_lines += 1
                        break
            
            # Section hierarchy detection
            for pattern in section_patterns:
                if re.search(pattern, line):
                    section_hierarchy_lines += 1
                    structure['sections'].append(line_stripped)
                    break
            
            # Look for field-like patterns (word: description)
            if ':' in line and len(line_stripped) < 200:
                parts = line_stripped.split(':', 1)
                if (len(parts) == 2 and 
                    len(parts[0]) < 50 and 
                    parts[0].replace(' ', '').replace('.', '').isalnum()):
                    field_like_lines += 1
            
            # Detect potential sections (short lines, often in caps or title case)
            if (len(line_stripped) < 60 and 
                line_stripped and 
                (line_stripped.isupper() or line_stripped.istitle()) and
                not line_stripped.startswith('•') and
                not any(re.search(p, line) for p in list_patterns)):
                if line_stripped not in structure['sections']:
                    structure['sections'].append(line_stripped)
        
        # Improved classification with multiple indicators
        total_lines = len([l for l in lines if l.strip()])
        
        # Calculate percentages for better classification
        table_percentage = (table_indicators / total_lines) * 100 if total_lines > 0 else 0
        field_percentage = (field_like_lines / total_lines) * 100 if total_lines > 0 else 0
        list_percentage = (bullet_lines / total_lines) * 100 if total_lines > 0 else 0
        
        # Classify document type based on patterns and thresholds
        if table_indicators > 3 or table_percentage > 2:  # Lowered threshold
            structure['document_type'] = 'structured_fields'
            structure['has_tables'] = True
        elif field_like_lines > 10 or field_percentage > 5:
            structure['document_type'] = 'structured_fields'
        elif bullet_lines > 5 or list_percentage > 3:
            structure['document_type'] = 'list_heavy'
            structure['has_lists'] = True
        elif section_hierarchy_lines > 3:
            structure['document_type'] = 'structured_fields'
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
        """Extract field-value pairs from structured text with enhanced relationship mapping"""
        fields = []
        lines = text.split('\n')
        
        # Generic cross-reference patterns
        cross_ref_patterns = [
            r'(see|refer|reference)\s+([A-Z]\w+|\d+\.\d+|Table\s+\d+|Section\s+\d+)',
            r'([A-Z]\w+\s+\d+)',  # "Table 1", "Figure 2"
            r'(Annex|Appendix)\s+([A-Z])',
        ]
        
        # Generic structured data patterns
        definition_patterns = [
            r'([A-Z][^:]+):\s*(.+)',           # "Field Name: Description"
            r'([A-Z]\w+)\s+([a-z]+\s+\d+)',    # "Format type 6"
            r'([A-Z0-9]{2,})\s*[-–]\s*(.+)',   # "CODE - Description"
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Standard colon-separated fields
            if ':' in line and len(line) < 500:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    field_name = parts[0].strip()
                    field_content = parts[1].strip()
                    
                    if field_name and field_content:
                        metadata = self._extract_field_metadata(field_content, lines, i)
                        
                        field = ExtractedField(
                            name=field_name,
                            content=field_content,
                            field_type=self._infer_field_type(field_content),
                            metadata=metadata
                        )
                        fields.append(field)
            
            # Enhanced pattern matching for structured data
            for pattern in definition_patterns:
                match = re.search(pattern, line)
                if match and len(line) < 300:
                    field_name = match.group(1).strip()
                    field_content = match.group(2).strip() if match.lastindex >= 2 else line
                    
                    if field_name and field_content and field_name != field_content:
                        metadata = self._extract_field_metadata(field_content, lines, i)
                        
                        field = ExtractedField(
                            name=field_name,
                            content=field_content,
                            field_type=self._infer_field_type(field_content),
                            metadata=metadata
                        )
                        fields.append(field)
                    break
        
        return fields
    
    def _extract_field_metadata(self, content: str, lines: List[str], line_index: int) -> Dict[str, Any]:
        """Extract metadata from field content and surrounding context"""
        metadata = {}
        
        # Extract requirement info
        requirement_match = self.requirement_pattern.search(content)
        if requirement_match:
            metadata['requirement'] = requirement_match.group(1)
        
        # Generic technical format patterns
        format_patterns = [
            (r'([a-zA-Z]+)\s*[\(\[]?(\d+)[\)\]]?', 'format_spec'),  # "string(20)", "int 4"
            (r'(string|integer|boolean|decimal|binary)', 'data_type'),
            (r'(required|optional|conditional|mandatory)', 'requirement'),
            (r'(\d+)\s*[-–to]\s*(\d+)', 'range'),  # "1-255", "0 to 100"
        ]
        
        for pattern, key in format_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if key == 'format_spec':
                    metadata['format_type'] = match.group(1)
                    metadata['format_size'] = match.group(2)
                elif key == 'range':
                    metadata['min_value'] = match.group(1)
                    metadata['max_value'] = match.group(2)
                else:
                    metadata[key] = match.group(1).lower()
        
        # Look for cross-references
        cross_ref_patterns = [
            r'(see|refer|reference)\s+([A-Z]\w+|\d+\.\d+|Table\s+\d+|Section\s+\d+)',
            r'([A-Z]\w+\s+\d+)',  # "Table 1", "Figure 2"
            r'(Annex|Appendix)\s+([A-Z])',
        ]
        
        cross_refs = []
        for pattern in cross_ref_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if match.lastindex >= 2:
                    cross_refs.append(f"{match.group(1)} {match.group(2)}")
                else:
                    cross_refs.append(match.group(0))
        
        if cross_refs:
            metadata['cross_references'] = cross_refs
        
        # Check surrounding context for additional information
        context_start = max(0, line_index - 2)
        context_end = min(len(lines), line_index + 3)
        context_lines = lines[context_start:context_end]
        context = ' '.join(line.strip() for line in context_lines if line.strip())
        
        # Look for section context
        section_match = re.search(r'(\d+\.\d+\s+[A-Z][^:]+)', context)
        if section_match:
            metadata['section'] = section_match.group(1).strip()
        
        return metadata
    
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