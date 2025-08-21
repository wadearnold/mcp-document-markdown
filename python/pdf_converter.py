import sys
import os
import argparse
import re
from pathlib import Path

# Import PDF processing libraries
import pypdf
import pdfplumber
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image
import io
import base64

class PDFToMarkdownConverter:
    def __init__(self, pdf_path, output_dir, preserve_tables=True, extract_images=True):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.preserve_tables = preserve_tables
        self.extract_images = extract_images
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        if self.extract_images:
            self.images_dir.mkdir(exist_ok=True)
        
    def convert(self):
        """Main conversion method combining multiple approaches for best results"""
        markdown_content = []
        
        # Try multiple extraction methods and combine results
        try:
            # Method 1: PyMuPDF for text and images
            fitz_content = self.extract_with_pymupdf()
            
            # Method 2: pdfplumber for tables
            if self.preserve_tables:
                tables_content = self.extract_tables_with_pdfplumber()
            else:
                tables_content = {}
            
            # Method 3: pypdf for structure
            structure = self.extract_structure_with_pypdf()
            
            # Combine and organize content
            markdown_content = self.combine_content(fitz_content, tables_content, structure)
            
        except Exception as e:
            print(f"Error during conversion: {e}", file=sys.stderr)
            # Fallback to basic extraction
            markdown_content = self.basic_extraction()
        
        # Save organized content
        self.save_and_organize_content(markdown_content)
        
        # Save temp file for compatibility
        output_file = self.output_dir / "temp_converted.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(output_file)
    
    def extract_with_pymupdf(self):
        """Extract text and images using PyMuPDF"""
        doc = fitz.open(self.pdf_path)
        content = []
        
        for page_num, page in enumerate(doc, 1):
            # Extract text
            text = page.get_text()
            
            # Process text to identify headers and structure
            processed_text = self.process_text_structure(text)
            content.append({
                'page': page_num,
                'text': processed_text,
                'images': []
            })
            
            # Extract images if requested
            if self.extract_images:
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        # Extract image
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        # Save image
                        img_filename = f"page_{page_num}_img_{img_index}.png"
                        img_path = self.images_dir / img_filename
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            pix.save(str(img_path))
                        else:  # CMYK
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                            pix.save(str(img_path))
                        
                        content[-1]['images'].append(f"images/{img_filename}")
                        pix = None
                        
                    except Exception as e:
                        print(f"Error extracting image: {e}", file=sys.stderr)
        
        doc.close()
        return content
    
    def extract_tables_with_pdfplumber(self):
        """Extract tables using pdfplumber"""
        tables_by_page = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()
                if tables:
                    tables_by_page[page_num] = []
                    for table in tables:
                        # Convert to pandas DataFrame for better formatting
                        try:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            # Clean up the dataframe
                            df = df.fillna('')
                            tables_by_page[page_num].append(df)
                        except Exception as e:
                            # Fallback to raw table
                            tables_by_page[page_num].append(table)
        
        return tables_by_page
    
    def extract_structure_with_pypdf(self):
        """Extract document structure using pypdf"""
        structure = {
            'outline': [],
            'metadata': {}
        }
        
        try:
            with open(self.pdf_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                
                # Get metadata
                if reader.metadata:
                    structure['metadata'] = {
                        'title': reader.metadata.get('/Title', ''),
                        'author': reader.metadata.get('/Author', ''),
                        'subject': reader.metadata.get('/Subject', ''),
                    }
                
                # Get outline (bookmarks)
                if reader.outline:
                    structure['outline'] = self.process_outline(reader.outline)
        
        except Exception as e:
            print(f"Error extracting structure: {e}", file=sys.stderr)
        
        return structure
    
    def process_outline(self, outline, level=0):
        """Process PDF outline/bookmarks"""
        processed = []
        for item in outline:
            if isinstance(item, list):
                processed.extend(self.process_outline(item, level + 1))
            else:
                processed.append({
                    'title': item.title,
                    'level': level
                })
        return processed
    
    def process_text_structure(self, text):
        """Identify headers, code blocks, lists, and structure in text"""
        lines = text.split('\n')
        processed_lines = []
        in_code_block = False
        in_table = False
        code_block_type = None
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            original_line = line
            line = line.strip()
            
            # Skip empty lines (preserve them)
            if not line:
                processed_lines.append('')
                i += 1
                continue
            
            # Detect code blocks (JSON, XML, HTTP, etc.)
            if not in_code_block and self.is_code_block_start(line, lines[i:i+5]):
                code_block_type = self.detect_code_type(line, lines[i:i+5])
                processed_lines.append(f"```{code_block_type}")
                in_code_block = True
                processed_lines.append(line)
            elif in_code_block and self.is_code_block_end(line, lines[i:i+3]):
                processed_lines.append(line)
                processed_lines.append("```")
                in_code_block = False
                code_block_type = None
            elif in_code_block:
                # Preserve original indentation in code blocks
                processed_lines.append(original_line)
            
            # Detect tables
            elif not in_code_block and self.is_table_row(line):
                if not in_table:
                    in_table = True
                processed_lines.append(self.format_table_row(line))
            elif in_table and not self.is_table_row(line):
                in_table = False
                processed_lines.append('')  # Add space after table
                # Process this line normally
                processed_lines.append(self.format_text_line(line))
            
            # Detect headers
            elif not in_code_block and not in_table and self.is_header(line):
                level = self.determine_header_level(line)
                processed_lines.append(f"{'#' * level} {line}")
            
            # Detect lists
            elif not in_code_block and not in_table and self.is_list_item(line):
                processed_lines.append(self.format_list_item(line))
            
            # Regular text
            elif not in_code_block and not in_table:
                processed_lines.append(self.format_text_line(line))
            else:
                processed_lines.append(line)
            
            i += 1
        
        # Close any open code block
        if in_code_block:
            processed_lines.append("```")
        
        return '\n'.join(processed_lines)
    
    def is_header(self, line):
        """Detect if a line is likely a header"""
        # Skip very long lines
        if len(line) > 150:
            return False
            
        # Numbered sections (1., 1.1, 1.1.1, etc.)
        if re.match(r'^(\d+\.)+\s+[A-Z]', line):
            return True
        
        # Chapter patterns
        if re.match(r'^(Chapter|Section|Part)\s+\d+', line, re.IGNORECASE):
            return True
        
        # All caps and reasonable length
        if line.isupper() and 5 < len(line) < 100 and not re.search(r'[{}()\[\]]', line):
            return True
        
        # Title case and short
        if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]*)*$', line) and len(line) < 80:
            words = line.split()
            if len(words) >= 2 and len(words) <= 8:
                return True
        
        # API endpoints and technical headers
        if re.match(r'^(GET|POST|PUT|DELETE|PATCH)\s+', line):
            return True
            
        # Version headers
        if re.match(r'^(Version|v\d+)', line, re.IGNORECASE):
            return True
            
        return False
    
    def determine_header_level(self, line):
        """Determine the appropriate header level"""
        # API endpoints are level 3
        if re.match(r'^(GET|POST|PUT|DELETE|PATCH)\s+', line):
            return 3
        
        # Chapter patterns
        if re.match(r'^(Chapter|Part)\s+', line, re.IGNORECASE):
            return 1
            
        # Count dots in numbered sections
        dots = line.count('.')
        if dots > 0:
            return min(dots + 1, 6)
        
        # All caps headers
        if line.isupper():
            # Short all-caps are major sections (level 1)
            if len(line) < 30:
                return 1
            else:
                return 2
        
        # Title case headers are subsections
        if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]*)*$', line):
            return 3
        
        return 2
    
    def table_to_markdown(self, table):
        """Convert a table (DataFrame or list) to markdown format"""
        if isinstance(table, pd.DataFrame):
            return table.to_markdown(index=False)
        else:
            # Convert list table to markdown
            if not table or not table[0]:
                return ""
            
            md_lines = []
            # Header
            md_lines.append("| " + " | ".join(str(cell) for cell in table[0]) + " |")
            # Separator
            md_lines.append("|" + "|".join(" --- " for _ in table[0]) + "|")
            # Rows
            for row in table[1:]:
                md_lines.append("| " + " | ".join(str(cell) if cell else "" for cell in row) + " |")
            
            return "\n".join(md_lines)
    
    def combine_content(self, fitz_content, tables_content, structure):
        """Combine content from different sources into final markdown"""
        markdown_parts = []
        
        # Add metadata if available
        if structure['metadata'].get('title'):
            markdown_parts.append(f"# {structure['metadata']['title']}\n")
            if structure['metadata'].get('author'):
                markdown_parts.append(f"**Author:** {structure['metadata']['author']}\n")
        
        # Process each page
        for page_data in fitz_content:
            page_num = page_data['page']
            
            # Add page marker (comment)
            markdown_parts.append(f"\n<!-- Page {page_num} -->\n")
            
            # Add text content
            markdown_parts.append(page_data['text'])
            
            # Add tables if any
            if page_num in tables_content:
                for table in tables_content[page_num]:
                    markdown_parts.append("\n")
                    markdown_parts.append(self.table_to_markdown(table))
                    markdown_parts.append("\n")
            
            # Add image references
            for img_path in page_data['images']:
                markdown_parts.append(f"\n![Image from page {page_num}]({img_path})\n")
        
        return "\n".join(markdown_parts)
    
    def basic_extraction(self):
        """Fallback basic extraction method"""
        try:
            with open(self.pdf_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                text = []
                for page in reader.pages:
                    text.append(page.extract_text())
                return "\n\n".join(text)
        except Exception as e:
            return f"Error: Could not extract text from PDF: {e}"
    
    def is_code_block_start(self, line, next_lines):
        """Detect start of code blocks"""
        # JSON patterns
        if line.strip() in ['{', '['] or re.match(r'^\s*[{\[]', line):
            return True
        
        # XML patterns
        if re.match(r'^\s*<[^>]+>', line):
            return True
        
        # HTTP request patterns
        if re.match(r'^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+/', line):
            return True
        
        # Code patterns with specific indicators
        code_indicators = ['function', 'class', 'def ', 'var ', 'const ', 'let ', 'import ', 'from ']
        if any(indicator in line.lower() for indicator in code_indicators):
            return True
        
        # Look ahead for JSON/XML content
        if len(next_lines) > 1:
            next_content = ' '.join(next_lines[1:3])
            if re.search(r'[{}"\[\]:,]', next_content) and len(next_content.strip()) > 10:
                return True
        
        return False
    
    def is_code_block_end(self, line, next_lines):
        """Detect end of code blocks"""
        # End braces
        if line.strip() in ['}', ']', '/>']:
            return True
        
        # Look ahead - if next lines are clearly not code
        if len(next_lines) > 1:
            next_line = next_lines[1].strip()
            if next_line and not re.search(r'[{}"\[\]:,<>/]', next_line) and len(next_line) > 20:
                return True
        
        return False
    
    def detect_code_type(self, line, next_lines):
        """Detect the type of code block"""
        content = ' '.join([line] + [l.strip() for l in next_lines[:3]]).lower()
        
        if '{' in content and ('"' in content or ':' in content):
            return 'json'
        elif '<' in content and '>' in content:
            return 'xml'
        elif re.match(r'^(get|post|put|delete)', line.lower()):
            return 'http'
        elif any(lang in content for lang in ['function', 'class', 'def']):
            return 'javascript'
        elif 'select' in content or 'insert' in content:
            return 'sql'
        else:
            return ''
    
    def is_table_row(self, line):
        """Detect if line is part of a table"""
        # Multiple columns separated by spaces
        if len(line.split()) >= 3 and not line.startswith(('•', '-', '*')):
            # Check for tabular data patterns
            words = line.split()
            if len(words) >= 3:
                # Numbers or short consistent values
                return True
        return False
    
    def format_table_row(self, line):
        """Format a line as a markdown table row"""
        cells = line.split()
        return '| ' + ' | '.join(cells) + ' |'
    
    def is_list_item(self, line):
        """Detect if line is a list item"""
        # Bullet points
        if re.match(r'^\s*[•▪▫▸▹▴▵○●◦‣⁃]\s+', line):
            return True
        
        # Dashes and asterisks
        if re.match(r'^\s*[-*]\s+', line):
            return True
        
        # Numbered lists
        if re.match(r'^\s*\d+\.\s+', line):
            return True
        
        # Letter lists
        if re.match(r'^\s*[a-z]\.\s+', line):
            return True
        
        return False
    
    def format_list_item(self, line):
        """Format a list item"""
        # Replace bullet characters with standard markdown
        line = re.sub(r'^\s*[•▪▫▸▹▴▵○●◦‣⁃]\s+', '- ', line)
        
        # Ensure proper spacing for numbered lists
        line = re.sub(r'^\s*(\d+\.)\s+', r'\1 ', line)
        line = re.sub(r'^\s*([a-z]\.)\s+', r'\1 ', line)
        
        return line
    
    def format_text_line(self, line):
        """Format regular text lines"""
        # Clean up extra spaces
        line = re.sub(r'\s+', ' ', line)
        
        # Detect and format inline code
        line = self.format_inline_code(line)
        
        # Format bold text (all caps words)
        line = re.sub(r'\b([A-Z]{3,})\b', r'**\1**', line)
        
        return line
    
    def format_inline_code(self, line):
        """Format inline code elements"""
        # API endpoints in text
        line = re.sub(r'\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(/[^\s]*)', r'`\1 \2`', line)
        
        # File extensions and technical terms
        line = re.sub(r'\b(\w+\.(json|xml|pdf|csv|txt|md))\b', r'`\1`', line)
        
        # Status codes
        line = re.sub(r'\b(200|201|400|401|403|404|500)\b', r'`\1`', line)
        
        return line
    
    def save_and_organize_content(self, content):
        """Save content and organize into intelligent sections"""
        # First save the complete document
        complete_dir = self.output_dir / "complete"
        complete_dir.mkdir(exist_ok=True)
        complete_file = complete_dir / "full-document.md"
        
        with open(complete_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Split into intelligent sections
        sections = self.split_into_intelligent_sections(content)
        
        # Create sections directory
        sections_dir = self.output_dir / "sections"
        sections_dir.mkdir(exist_ok=True)
        
        # Save each section
        section_files = []
        for i, section in enumerate(sections, 1):
            filename = f"{i:02d}-{section['slug']}.md"
            filepath = sections_dir / filename
            
            # Add metadata header
            section_content = f"""---
section: {section['title']}
type: {section.get('type', 'content')}
tokens: {len(section['content'].split())}
---

{section['content']}"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(section_content)
            
            section_files.append({
                'filename': filename,
                'title': section['title'],
                'type': section.get('type', 'content')
            })
        
        # Generate table of contents
        self.generate_table_of_contents(section_files)
        
        # Also create a summary index file
        self.create_summary_index(sections)
        
        return content
    
    def create_summary_index(self, sections):
        """Create a summary index for quick reference"""
        summary_content = "# Document Summary\n\n"
        summary_content += "## Quick Reference\n\n"
        
        for section in sections:
            summary_content += f"### {section['title']}\n"
            summary_content += f"**Type:** {section['type']}\n"
            summary_content += f"**Content:** {len(section['content'].split())} words\n\n"
            
            # Extract first few lines as preview
            lines = section['content'].split('\n')
            preview_lines = [line for line in lines[:10] if line.strip() and not line.startswith('#')][:3]
            if preview_lines:
                summary_content += "**Preview:**\n"
                for line in preview_lines:
                    summary_content += f"> {line}\n"
            summary_content += "\n"
        
        # Save summary
        summary_file = self.output_dir / "summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
    
    def split_into_intelligent_sections(self, content):
        """Split content into intelligent sections based on headers and content type"""
        sections = []
        lines = content.split('\n')
        current_section = {'title': 'Introduction', 'content': '', 'type': 'intro', 'slug': 'introduction'}
        
        for line in lines:
            # Detect major section breaks (# Headers)
            if line.startswith('# ') and len(current_section['content'].strip()) > 100:
                # Save current section
                current_section['content'] = current_section['content'].strip()
                sections.append(current_section)
                
                # Start new section
                title = line[2:].strip()
                slug = self.create_slug(title)
                section_type = self.determine_section_type(title)
                current_section = {
                    'title': title,
                    'content': line + '\n',
                    'type': section_type,
                    'slug': slug
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            current_section['content'] = current_section['content'].strip()
            sections.append(current_section)
        
        return sections
    
    def create_slug(self, title):
        """Create a URL-friendly slug from title"""
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug[:50].strip('-')
    
    def determine_section_type(self, title):
        """Determine the type of section based on title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['api', 'endpoint', 'request', 'response']):
            return 'api'
        elif any(word in title_lower for word in ['auth', 'security', 'token', 'credential']):
            return 'security'
        elif any(word in title_lower for word in ['error', 'status', 'code']):
            return 'errors'
        elif any(word in title_lower for word in ['example', 'sample', 'demo']):
            return 'examples'
        elif any(word in title_lower for word in ['intro', 'overview', 'summary']):
            return 'intro'
        elif any(word in title_lower for word in ['reference', 'spec', 'schema']):
            return 'reference'
        else:
            return 'content'
    
    def generate_table_of_contents(self, section_files):
        """Generate a comprehensive table of contents"""
        toc_content = f"""# Technical Specification - Table of Contents

Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## Document Structure

This document has been automatically organized into sections for optimal AI assistant usage.

## Sections

"""
        
        # Group by type
        sections_by_type = {}
        for section in section_files:
            section_type = section['type']
            if section_type not in sections_by_type:
                sections_by_type[section_type] = []
            sections_by_type[section_type].append(section)
        
        # Write organized TOC
        type_order = ['intro', 'security', 'api', 'reference', 'examples', 'errors', 'content']
        type_names = {
            'intro': 'Introduction & Overview',
            'security': 'Security & Authentication', 
            'api': 'API Endpoints',
            'reference': 'Reference Documentation',
            'examples': 'Examples & Samples',
            'errors': 'Error Handling',
            'content': 'General Content'
        }
        
        for section_type in type_order:
            if section_type in sections_by_type:
                toc_content += f"\n### {type_names.get(section_type, section_type.title())}\n\n"
                for section in sections_by_type[section_type]:
                    toc_content += f"- [{section['title']}](sections/{section['filename']})\n"
        
        # Add any remaining types
        for section_type, sections in sections_by_type.items():
            if section_type not in type_order:
                toc_content += f"\n### {section_type.title()}\n\n"
                for section in sections:
                    toc_content += f"- [{section['title']}](sections/{section['filename']})\n"
        
        toc_content += f"""

## Usage Tips

- **For API integration**: Start with Security & Authentication, then API Endpoints
- **For understanding**: Begin with Introduction & Overview
- **For troubleshooting**: Check Error Handling section
- **For implementation**: Review Examples & Samples

## Complete Document

- [Full Document](complete/full-document.md) - Complete specification in one file

"""
        
        # Save TOC
        toc_file = self.output_dir / "index.md"
        with open(toc_file, 'w', encoding='utf-8') as f:
            f.write(toc_content)

def main():
    parser = argparse.ArgumentParser(description='Convert PDF to Markdown')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('output_dir', help='Output directory')
    parser.add_argument('--preserve-tables', action='store_true', 
                      help='Preserve table formatting')
    parser.add_argument('--extract-images', action='store_true',
                      help='Extract and reference images')
    
    args = parser.parse_args()
    
    converter = PDFToMarkdownConverter(
        args.pdf_path,
        args.output_dir,
        args.preserve_tables,
        args.extract_images
    )
    
    output_file = converter.convert()
    print(f"Conversion complete: {output_file}")

if __name__ == "__main__":
    main()
