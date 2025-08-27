"""
ULTIMATE PDF Extractor - Production-ready with intelligent reconstruction
"""
import fitz
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class APIField:
    """Represents an API field with all attributes"""
    name: str
    requirement: str = ""
    description: str = ""
    format_spec: str = ""
    example: str = ""
    allowed_values: List[str] = None
    
    def __post_init__(self):
        if self.allowed_values is None:
            self.allowed_values = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'requirement': self.requirement,
            'description': self.description,
            'format': self.format_spec,
            'example': self.example,
            'values': self.allowed_values
        }


class IntelligentTextProcessor:
    """Intelligent text processing with context awareness"""
    
    def __init__(self):
        # Patterns for bullet detection
        self.bullet_contexts = [
            'following values', 'following apis', 'includes', 'types',
            'one of the following', 'it is one of', 'format: it is'
        ]
        
        # Field name patterns
        self.field_patterns = [
            re.compile(r'^[a-z]+([A-Z][a-zA-Z0-9]*)*$'),  # camelCase
            re.compile(r'^[A-Z][a-z]+([A-Z][a-zA-Z0-9]*)*$'),  # PascalCase
        ]
        
        # Requirement patterns
        self.req_pattern = re.compile(r'\((Required|Optional|Conditional)\)')
        
    def fix_encoding_and_bullets(self, text: str) -> str:
        """Fix encoding and convert bullets intelligently"""
        # Standard character fixes
        char_fixes = {
            'ﬁ': 'fi', 'ﬂ': 'fl', ''': "'", ''': "'",
            '"': '"', '"': '"', '–': '-', '—': '--',
            '\xa0': ' ', '\u200b': '', '\ufeff': ''
        }
        
        for old, new in char_fixes.items():
            text = text.replace(old, new)
        
        # First, fix the split bullet lines (l\nContent -> l Content)
        text = self._rejoin_split_bullets(text)
        
        # Enhanced bullet conversion with multiple strategies
        lines = text.split('\n')
        processed_lines = []
        
        for i, line in enumerate(lines):
            original_line = line
            
            # Skip lines that already have proper bullets
            if '•' in line:
                processed_lines.append(line)
                continue
            
            # Strategy 1: Convert 'l ' based on context and content
            if line.strip().startswith('l '):
                should_convert = self._should_convert_l_bullet(line, lines, i)
                if should_convert:
                    # Preserve indentation
                    indent = len(line) - len(line.lstrip())
                    line = ' ' * indent + line.lstrip().replace('l ', '• ', 1)
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _rejoin_split_bullets(self, text: str) -> str:
        """Rejoin split bullet lines where 'l' is on one line and content on next"""
        lines = text.split('\n')
        rejoined_lines = []
        i = 0
        
        while i < len(lines):
            current_line = lines[i].strip()
            
            # If current line is just 'l' and next line has content
            if current_line == 'l' and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith('l') and len(next_line) < 100:
                    # Rejoin as 'l content'
                    rejoined_lines.append(f"l {next_line}")
                    i += 2  # Skip both lines
                    continue
            
            rejoined_lines.append(lines[i])
            i += 1
        
        return '\n'.join(rejoined_lines)
    
    def _should_convert_l_bullet(self, line: str, lines: List[str], index: int) -> bool:
        """Determine if an 'l ' should be converted to bullet"""
        content = line.strip()[2:].strip()  # Content after 'l '
        
        if not content:
            return False
        
        # Strategy 1: Check preceding lines for bullet context
        context_found = self._has_bullet_context(lines, index)
        
        # Strategy 2: Content pattern analysis
        content_suggests_bullet = self._content_suggests_bullet(content)
        
        # Strategy 3: Structural analysis (indentation, surrounding lines)
        structural_bullet = self._structural_analysis_suggests_bullet(lines, index)
        
        return context_found or content_suggests_bullet or structural_bullet
    
    def _has_bullet_context(self, lines: List[str], index: int) -> bool:
        """Check if preceding lines suggest bullet context"""
        # Check previous 3 lines for bullet indicators
        for i in range(max(0, index - 3), index):
            line_lower = lines[i].lower()
            
            # Strong bullet context indicators
            strong_indicators = [
                'following values', 'following apis', 'one of the following',
                'it is one of', 'format: it is one of', 'values are:',
                'this is a required field in the following apis:',
                'populated when available in the following apis:',
                'can be used only in the following apis:'
            ]
            
            if any(indicator in line_lower for indicator in strong_indicators):
                return True
            
            # Line ending with colon suggests list follows
            if line_lower.strip().endswith(':') and len(line_lower.strip()) > 10:
                return True
        
        return False
    
    def _content_suggests_bullet(self, content: str) -> bool:
        """Analyze content to determine if it looks like a bullet item"""
        content_lower = content.lower()
        
        # Generic patterns that suggest bullet content (no hardcoded values)
        
        # Check for single uppercase words (likely enum values)
        first_word = content.split()[0] if content.split() else ''
        if first_word.isupper() and len(first_word) > 2:
            return True
        
        # Check for common status/state words
        status_patterns = ['active', 'inactive', 'enabled', 'disabled', 'yes', 'no', 'true', 'false']
        if any(content_lower.startswith(pattern) for pattern in status_patterns):
            return True
        
        # Check for boolean values
        if content_lower.startswith(('true—', 'false—', 'true ', 'false ')):
            return True
        
        # Check for numeric codes (00, 10, 11, etc.)
        if content[:2].isdigit() and (len(content) == 2 or content[2] in ' —-'):
            return True
        
        # Check for single uppercase word (likely enum value)
        first_word = content.split()[0] if content.split() else ''
        if first_word.isupper() and len(first_word) > 2:
            return True
        
        return False
    
    def _structural_analysis_suggests_bullet(self, lines: List[str], index: int) -> bool:
        """Analyze structure around line to determine if it's a bullet"""
        # Look for patterns like multiple consecutive 'l ' lines
        consecutive_l_count = 0
        
        # Count consecutive 'l ' lines around current position
        start = max(0, index - 2)
        end = min(len(lines), index + 3)
        
        for i in range(start, end):
            if lines[i].strip().startswith('l '):
                consecutive_l_count += 1
        
        # If we have multiple 'l ' lines close together, they're likely bullets
        if consecutive_l_count >= 2:
            return True
        
        # Check if previous line is also an 'l ' (continuing list)
        if index > 0 and lines[index - 1].strip().startswith('l '):
            return True
        
        # Check if next line is also an 'l ' (starting list)
        if index < len(lines) - 1 and lines[index + 1].strip().startswith('l '):
            return True
        
        return False
    
    def is_section_header(self, line: str) -> bool:
        """Check if line is a section header"""
        line = line.strip()
        # Generic header patterns (no hardcoded section names)
        # Look for title-case patterns, short lines, or common header words
        if len(line) < 60 and line.istitle():
            return True
        if 'Chapter' in line or 'Section' in line:
            return True
        # Common header words
        header_words = ['Information', 'Data', 'Configuration', 'Settings', 'Field', 'Description']
        return any(word in line for word in header_words)
    
    def is_field_name(self, text: str) -> bool:
        """Check if text is likely a field name"""
        if not text or len(text) > 50:
            return False
        
        text = text.strip()
        
        # Never treat bullet points as field names
        if text.startswith('l ') or text.startswith('• '):
            return False
        
        # Field names should not contain spaces (except after 'l ' which we handled above)
        if ' ' in text:
            return False
        
        return any(pattern.match(text) for pattern in self.field_patterns)
    
    def extract_requirement(self, text: str) -> Tuple[str, str]:
        """Extract requirement and clean text"""
        match = self.req_pattern.search(text)
        if match:
            req = match.group(1)
            clean_text = text.replace(match.group(0), '').strip()
            return req, clean_text
        return "", text


class SmartFieldExtractor:
    """Smart extraction of field-description pairs"""
    
    def __init__(self):
        self.processor = IntelligentTextProcessor()
    
    def extract_fields_from_text(self, text: str) -> List[APIField]:
        """Extract all fields from text with intelligent parsing"""
        text = self.processor.fix_encoding_and_bullets(text)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        fields = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip headers and metadata
            if self.should_skip_line(line):
                i += 1
                continue
            
            # Look for field-description pattern
            if self.processor.is_field_name(line):
                field = self.extract_single_field(lines, i)
                if field:
                    fields.append(field['field'])
                    i = field['next_index']
                else:
                    i += 1
            else:
                i += 1
        
        return fields
    
    def should_skip_line(self, line: str) -> bool:
        """Check if line should be skipped"""
        skip_patterns = [
            'Confidential', 'Proprietary', 'Copyright', 'All rights reserved',
            'Field', 'Description', 'Page ', 'Document'
        ]
        return any(pattern in line for pattern in skip_patterns)
    
    def extract_single_field(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Extract a single field with all its attributes"""
        if start_idx >= len(lines):
            return None
        
        field = APIField(name=lines[start_idx])
        i = start_idx + 1
        description_parts = []
        in_values_section = False
        
        while i < len(lines):
            line = lines[i]
            
            # Stop if we hit another field
            if self.processor.is_field_name(line) and i > start_idx + 1:
                break
            
            # Stop on section headers
            if self.processor.is_section_header(line):
                break
            
            # Parse requirement
            if not field.requirement:
                req, clean_line = self.processor.extract_requirement(line)
                if req:
                    field.requirement = req
                    line = clean_line
            
            # Parse format specification
            if line.startswith('Format:'):
                field.format_spec = line[7:].strip()
            
            # Parse example
            elif line.startswith('Example:'):
                field.example = line[8:].strip()
            
            # Check for values section
            elif any(indicator in line.lower() for indicator in [
                'following values', 'one of the following', 'it is one of', 
                'format: it is one of', 'following apis', 'values are'
            ]):
                in_values_section = True
                description_parts.append(line)
            
            # Parse bullet point values (both • and l patterns)
            elif (line.startswith('• ') or line.startswith('l ')) and in_values_section:
                value = line[2:].strip()
                # Clean up value (remove descriptions after —)
                if '—' in value:
                    value = value.split('—')[0].strip()
                if value:
                    field.allowed_values.append(value)
            
            # Regular description
            else:
                description_parts.append(line)
                # Continue values section for bullet patterns
                if not (line.startswith('•') or line.startswith('l ')):
                    in_values_section = False
            
            i += 1
        
        # Clean up description
        field.description = ' '.join(description_parts)
        field.description = re.sub(r'\s+', ' ', field.description).strip()
        
        # Remove format from description if it was extracted separately
        if field.format_spec:
            field.description = re.sub(r'Format:.*$', '', field.description, flags=re.IGNORECASE).strip()
        
        return {'field': field, 'next_index': i}


class MarkdownGenerator:
    """Generate clean, professional markdown optimized for LLM consumption"""
    
    def create_field_table(self, fields: List[APIField]) -> str:
        """Create a professional field table optimized for LLM understanding"""
        if not fields:
            return ""
        
        lines = [
            "| Field | Type | Required | Description | Format | Example | Values |",
            "|-------|------|----------|-------------|--------|---------|--------|"
        ]
        
        for field in fields:
            # Clean requirement text for LLM consumption
            req_text = field.requirement if field.requirement else ""
            
            # Determine field type from format or values
            field_type = self._determine_field_type(field)
            
            # Clean description (remove redundant format/example info)
            clean_desc = self._clean_description(field.description, field.format_spec, field.example)
            
            # Format values list
            values_cell = ""
            if field.allowed_values:
                if len(field.allowed_values) <= 3:
                    values_cell = ", ".join(f"`{v}`" for v in field.allowed_values)
                else:
                    values_cell = f"{len(field.allowed_values)} options: " + ", ".join(f"`{v}`" for v in field.allowed_values[:2]) + "..."
            
            # Build row
            lines.append(f"| `{field.name}` | {field_type} | {req_text} | {clean_desc} | {field.format_spec} | {field.example} | {values_cell} |")
        
        return "\n".join(lines)
    
    def _determine_field_type(self, field: APIField) -> str:
        """Determine field type from format and values"""
        if field.allowed_values:
            if len(field.allowed_values) <= 5:
                return "enum"
            else:
                return "string"
        
        format_lower = field.format_spec.lower() if field.format_spec else ""
        desc_lower = field.description.lower() if field.description else ""
        
        if any(word in format_lower or word in desc_lower for word in ["number", "numeric", "digit"]):
            return "number"
        elif any(word in format_lower or word in desc_lower for word in ["boolean", "true", "false"]):
            return "boolean"
        elif any(word in format_lower or word in desc_lower for word in ["date", "time", "timestamp"]):
            return "datetime"
        elif any(word in format_lower or word in desc_lower for word in ["array", "list"]):
            return "array"
        elif any(word in format_lower or word in desc_lower for word in ["object", "json"]):
            return "object"
        else:
            return "string"
    
    def _clean_description(self, description: str, format_spec: str, example: str) -> str:
        """Clean description by removing redundant format/example info"""
        if not description:
            return ""
        
        cleaned = description
        
        # Remove format info if it's specified separately
        if format_spec:
            cleaned = re.sub(rf"Format:\s*{re.escape(format_spec)}", "", cleaned, flags=re.IGNORECASE)
        
        # Remove example info if it's specified separately  
        if example:
            cleaned = re.sub(rf"Example:\s*{re.escape(example)}", "", cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def create_document(self, title: str, sections: Dict[str, List[APIField]], metadata: Dict[str, Any] = None) -> str:
        """Create complete markdown document optimized for LLM consumption"""
        lines = [
            f"# {title}",
            "",
        ]
        
        # Add structured metadata for LLM context
        if metadata:
            lines.extend([
                "## Document Metadata",
                "",
                f"- **Source**: {metadata.get('source', 'PDF Document')}",
                f"- **Pages**: {metadata.get('pages', 'Unknown')}",
                f"- **Extraction Method**: {metadata.get('extraction_method', 'ULTIMATE')}",
                f"- **Field Count**: {sum(len(fields) for fields in sections.values())}",
                f"- **Sections**: {len(sections)}",
                "",
                "---",
                ""
            ])
        
        # Add semantic summary for LLM understanding
        lines.extend([
            "## Document Summary",
            "",
            "This document contains API field definitions with structured information including:",
            "",
            "- **Field Names**: API parameter identifiers",
            "- **Requirements**: Whether fields are Required, Optional, or Conditional", 
            "- **Data Types**: Inferred from format specifications and allowed values",
            "- **Descriptions**: Functional explanations of each field",
            "- **Format Specifications**: Expected data formats and constraints",
            "- **Examples**: Sample values for implementation guidance",
            "- **Allowed Values**: Enumerated options where applicable",
            "",
            "---",
            ""
        ])
        
        # Table of contents with field counts
        lines.extend([
            "## Table of Contents",
            ""
        ])
        
        for i, (section_name, fields) in enumerate(sections.items(), 1):
            field_count = len(fields)
            anchor = section_name.lower().replace(' ', '-').replace('(', '').replace(')', '')
            lines.append(f"{i}. [{section_name}](#{anchor}) ({field_count} fields)")
        
        lines.extend(["", "---", ""])
        
        # Enhanced sections with context
        for section_name, fields in sections.items():
            lines.extend([
                f"## {section_name}",
                "",
                f"This section contains {len(fields)} field(s) related to {section_name.lower()}.",
                "",
                self.create_field_table(fields),
                "",
                "---",
                ""
            ])
        
        # Add footer with extraction stats
        req_fields = sum(1 for fields in sections.values() for field in fields if field.requirement == "Required")
        opt_fields = sum(1 for fields in sections.values() for field in fields if field.requirement == "Optional")
        cond_fields = sum(1 for fields in sections.values() for field in fields if field.requirement == "Conditional")
        
        lines.extend([
            "## Field Statistics",
            "",
            f"- **Total Fields**: {sum(len(fields) for fields in sections.values())}",
            f"- **Required Fields**: {req_fields}",
            f"- **Optional Fields**: {opt_fields}", 
            f"- **Conditional Fields**: {cond_fields}",
            "",
            "*Generated by ULTIMATE PDF Extractor - Optimized for LLM consumption*"
        ])
        
        return "\n".join(lines)
    
    def generate_json_schema(self, sections: Dict[str, List[APIField]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON schema for LLM-friendly API understanding"""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": metadata.get('title', 'API Documentation'),
            "description": f"API schema extracted from {metadata.get('source', 'PDF document')}",
            "properties": {},
            "required": []
        }
        
        for section_name, fields in sections.items():
            for field in fields:
                prop = {
                    "description": field.description,
                    "x-section": section_name
                }
                
                # Add type based on our inference
                field_type = self._determine_field_type(field)
                
                if field_type == "enum" and field.allowed_values:
                    prop["type"] = "string"
                    prop["enum"] = field.allowed_values
                elif field_type == "number":
                    prop["type"] = "number"
                elif field_type == "boolean":
                    prop["type"] = "boolean"
                elif field_type == "array":
                    prop["type"] = "array"
                elif field_type == "object":
                    prop["type"] = "object"
                else:
                    prop["type"] = "string"
                
                # Add format if available
                if field.format_spec:
                    prop["format"] = field.format_spec
                
                # Add example if available
                if field.example:
                    prop["example"] = field.example
                
                # Add to schema
                schema["properties"][field.name] = prop
                
                # Add to required if necessary
                if field.requirement == "Required":
                    schema["required"].append(field.name)
        
        return schema


class UltimatePDFExtractor:
    """The ultimate PDF extractor - production ready"""
    
    def __init__(self, pdf_path: str, output_dir: str):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.field_extractor = SmartFieldExtractor()
        self.markdown_generator = MarkdownGenerator()
    
    def extract(self) -> Dict[str, Any]:
        """Main extraction method"""
        print("🚀 Starting ULTIMATE PDF extraction...")
        
        # Extract content
        with fitz.open(self.pdf_path) as doc:
            # Get metadata
            metadata = self.extract_metadata(doc)
            
            # Process all pages
            all_text = []
            for page in doc:
                page_text = page.get_text()
                all_text.append(page_text)
            
            combined_text = "\n\n".join(all_text)
        
        # Extract fields intelligently
        print("🔍 Extracting fields with AI-like intelligence...")
        all_fields = self.field_extractor.extract_fields_from_text(combined_text)
        
        # Group fields by section
        sections = self.group_fields_by_section(all_fields)
        
        # Generate markdown
        print("📝 Generating professional markdown...")
        enhanced_metadata = {
            **metadata,
            'source': str(self.pdf_path.name),
            'total_fields': len(all_fields)
        }
        markdown = self.markdown_generator.create_document(
            metadata.get('title', 'API Documentation'),
            sections,
            enhanced_metadata
        )
        
        # Generate JSON schema for LLM consumption
        print("🧠 Generating JSON schema for LLM understanding...")
        json_schema = self.markdown_generator.generate_json_schema(sections, enhanced_metadata)
        
        # Calculate quality score
        quality_score = self.calculate_quality_score(all_fields, combined_text)
        
        result = {
            'metadata': metadata,
            'fields': [field.to_dict() for field in all_fields],
            'sections': {name: [f.to_dict() for f in fields] for name, fields in sections.items()},
            'markdown': markdown,
            'json_schema': json_schema,
            'stats': {
                'total_fields': len(all_fields),
                'sections': len(sections),
                'quality_score': quality_score,
                'quality_level': self.get_quality_level(quality_score),
                'llm_optimized': True
            }
        }
        
        # Save results
        self.save_results(result)
        
        return result
    
    def extract_metadata(self, doc) -> Dict[str, Any]:
        """Extract metadata"""
        return {
            'title': doc.metadata.get('title', self.pdf_path.stem),
            'author': doc.metadata.get('author', ''),
            'pages': len(doc),
            'extraction_method': 'ULTIMATE'
        }
    
    def group_fields_by_section(self, fields: List[APIField]) -> Dict[str, List[APIField]]:
        """Group fields by logical sections"""
        # Generic field categorization without hardcoded assumptions
        sections = {
            'Data Fields': [],
            'Configuration': [],
            'System Information': [],
            'User Information': [],
            'Location Data': [],
            'Other Fields': []
        }
        
        # Categorize fields based on generic patterns
        for field in fields:
            name = field.name.lower()
            
            # System/technical fields
            if any(keyword in name for keyword in ['id', 'key', 'code', 'number', 'version']):
                sections['Data Fields'].append(field)
            # Configuration fields
            elif any(keyword in name for keyword in ['config', 'setting', 'option', 'mode', 'type']):
                sections['Configuration'].append(field)
            # System information
            elif any(keyword in name for keyword in ['device', 'os', 'system', 'platform', 'manufacturer']):
                sections['System Information'].append(field)
            # User-related fields
            elif any(keyword in name for keyword in ['user', 'account', 'name', 'email', 'profile']):
                sections['User Information'].append(field)
            # Location fields
            elif any(keyword in name for keyword in ['address', 'location', 'city', 'state', 'country', 'postal']):
                sections['Location Data'].append(field)
            else:
                sections['Other Fields'].append(field)
        
        # Remove empty sections
        return {name: fields for name, fields in sections.items() if fields}
    
    def calculate_quality_score(self, fields: List[APIField], text: str) -> float:
        """Calculate extraction quality score (0-100)"""
        score = 0
        
        # Field detection (40 points max)
        field_score = min(40, len(fields) * 3)
        score += field_score
        
        # Requirement detection (20 points max)
        fields_with_req = sum(1 for f in fields if f.requirement)
        req_score = min(20, fields_with_req * 2)
        score += req_score
        
        # Format detection (20 points max)
        fields_with_format = sum(1 for f in fields if f.format_spec)
        format_score = min(20, fields_with_format * 2)
        score += format_score
        
        # Bullet point conversion (10 points max)
        bullet_count = text.count('•')
        bullet_score = min(10, bullet_count)
        score += bullet_score
        
        # Value enumeration (10 points max)
        fields_with_values = sum(1 for f in fields if f.allowed_values)
        values_score = min(10, fields_with_values * 2)
        score += values_score
        
        return min(100, score)
    
    def get_quality_level(self, score: float) -> str:
        """Get quality level based on score"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 80:
            return "GREAT"
        elif score >= 70:
            return "GOOD"
        elif score >= 60:
            return "ACCEPTABLE"
        else:
            return "NEEDS_IMPROVEMENT"
    
    def save_results(self, result: Dict[str, Any]):
        """Save all results optimized for LLM consumption"""
        # Save enhanced markdown
        md_path = self.output_dir / "ultimate_extraction.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(result['markdown'])
        
        # Save JSON schema for LLM understanding
        schema_path = self.output_dir / "api_schema.json"
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(result['json_schema'], f, indent=2, ensure_ascii=False)
        
        # Save complete structured data
        json_path = self.output_dir / "extraction_data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': result['metadata'],
                'fields': result['fields'],
                'sections': result['sections'],
                'stats': result['stats']
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved LLM-optimized markdown: {md_path}")
        print(f"✅ Saved JSON schema: {schema_path}")
        print(f"✅ Saved structured data: {json_path}")


def test_ultimate_extractor():
    """Test the ultimate extractor"""
    pdf_path = "sample_document.pdf"
    output_dir = "output_ultimate"
    
    extractor = UltimatePDFExtractor(pdf_path, output_dir)
    result = extractor.extract()
    
    print("\n" + "=" * 60)
    print("🎯 ULTIMATE EXTRACTION RESULTS")
    print("=" * 60)
    
    stats = result['stats']
    print(f"📊 Quality Score: {stats['quality_score']:.1f}/100")
    print(f"🏆 Quality Level: {stats['quality_level']}")
    print(f"📋 Fields Found: {stats['total_fields']}")
    print(f"📑 Sections: {stats['sections']}")
    
    # Show sample field
    if result['fields']:
        print("\n🔍 Sample Field:")
        sample = result['fields'][0]
        print(f"   Name: {sample['name']}")
        print(f"   Required: {sample['requirement']}")
        print(f"   Description: {sample['description'][:100]}...")
        if sample['format']:
            print(f"   Format: {sample['format']}")
    
    # Show markdown sample
    print(f"\n📝 Markdown Preview:")
    print(result['markdown'][:800])
    print("...")
    
    return result


if __name__ == "__main__":
    test_ultimate_extractor()