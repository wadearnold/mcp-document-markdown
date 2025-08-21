import sys
import os
import argparse
import re
from pathlib import Path
import json
from datetime import datetime

# Import PDF processing libraries
import pypdf
import pdfplumber
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image
import io
import base64

# Structured table output uses JSON format for LLM optimization

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not available. Using approximation for token counting.", file=sys.stderr)

class PDFToMarkdownConverter:
    def __init__(self, pdf_path, output_dir, preserve_tables=True, extract_images=True, enable_chunking=True, structured_tables=True, build_search_index=True):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.preserve_tables = preserve_tables
        self.extract_images = extract_images
        self.enable_chunking = enable_chunking
        self.structured_tables = structured_tables
        self.build_search_index = build_search_index
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        if self.extract_images:
            self.images_dir.mkdir(exist_ok=True)
        
        # Store extracted tables for structured conversion
        self.extracted_tables = []
        
        # Initialize token counter
        self.token_encoder = None
        if TIKTOKEN_AVAILABLE:
            try:
                # Use cl100k_base encoding (used by GPT-4 and Claude)
                self.token_encoder = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                print(f"Warning: Could not initialize tiktoken: {e}", file=sys.stderr)
        
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
        
        # Save organized content (this does all the work)
        sections = self.save_and_organize_content(markdown_content)
        
        # Apply smart chunking to large sections if enabled
        if self.enable_chunking:
            self.apply_smart_chunking(sections)
        
        # Extract and create dedicated API endpoint files
        self.extract_api_endpoints_to_files(markdown_content)
        
        # Convert tables to structured formats if enabled
        if self.structured_tables:
            self.convert_tables_to_structured_formats()
        
        # Generate metadata file with statistics
        self.generate_metadata_file()
        
        # Build searchable index with terms, endpoints, and error codes if enabled
        if self.build_search_index:
            self.build_searchable_index(markdown_content, sections)
        
        # Return success message
        return f"Converted PDF to organized sections in {self.output_dir}"
    
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
                            
                            # Store for structured conversion
                            if self.structured_tables:
                                table_info = {
                                    'page': page_num,
                                    'table_index': len(tables_by_page[page_num]) - 1,
                                    'dataframe': df.copy(),
                                    'raw_data': table,
                                    'title': self.detect_table_title(table, page_num)
                                }
                                self.extracted_tables.append(table_info)
                        except Exception as e:
                            # Fallback to raw table
                            tables_by_page[page_num].append(table)
                            
                            # Store raw table for structured conversion
                            if self.structured_tables:
                                table_info = {
                                    'page': page_num,
                                    'table_index': len(tables_by_page[page_num]) - 1,
                                    'dataframe': None,
                                    'raw_data': table,
                                    'title': self.detect_table_title(table, page_num)
                                }
                                self.extracted_tables.append(table_info)
        
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
        
        # Title case and short (but not common sentence starters)
        if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]*)*$', line) and len(line) < 80:
            words = line.split()
            # More restrictive: must be 2-6 words and not start with common sentence words
            if (2 <= len(words) <= 6 and 
                not words[0].lower() in ['this', 'the', 'when', 'where', 'how', 'what', 'why', 'if', 'after', 'before', 'during', 'once', 'while', 'since', 'though', 'although', 'because', 'since']):
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
            # Use pandas markdown with better formatting
            if table.empty:
                return ""
            # Clean up the dataframe first
            table = table.fillna('')
            # Convert to string and clean up cells
            for col in table.columns:
                table[col] = table[col].astype(str).str.strip()
            return table.to_markdown(index=False, tablefmt='pipe')
        else:
            # Convert list table to markdown
            if not table or not table[0]:
                return ""
            
            # Clean up the table data
            cleaned_table = []
            for row in table:
                if row:  # Skip empty rows
                    cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                    if any(cell for cell in cleaned_row):  # Only keep rows with content
                        cleaned_table.append(cleaned_row)
            
            if not cleaned_table:
                return ""
            
            md_lines = []
            # Header
            header_row = cleaned_table[0]
            md_lines.append("| " + " | ".join(header_row) + " |")
            # Separator
            md_lines.append("| " + " | ".join("---" for _ in header_row) + " |")
            # Rows
            for row in cleaned_table[1:]:
                # Ensure row has same number of columns as header
                padded_row = row + [""] * (len(header_row) - len(row))
                padded_row = padded_row[:len(header_row)]  # Truncate if too long
                md_lines.append("| " + " | ".join(padded_row) + " |")
            
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
            
            # Add text content - ensure we're getting all of it
            text_content = page_data['text']
            if text_content.strip():  # Only add if there's actual content
                markdown_parts.append(text_content)
            
            # Add tables if any
            if page_num in tables_content:
                for i, table in enumerate(tables_content[page_num]):
                    table_md = self.table_to_markdown(table)
                    if table_md:  # Only add if table conversion succeeded
                        markdown_parts.append("\n")
                        markdown_parts.append(f"**Table {i+1} (Page {page_num}):**")
                        markdown_parts.append("\n")
                        markdown_parts.append(table_md)
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
        """Detect if line is part of a table (very conservative - let pdfplumber handle real tables)"""
        # Only detect very obvious table rows that pdfplumber might miss
        # Such as pipe-separated or tab-separated data
        if '|' in line and line.count('|') >= 2:
            return True
        
        # Tab-separated data with multiple tabs
        if '\t' in line and line.count('\t') >= 2:
            return True
            
        # Otherwise, let pdfplumber handle table extraction
        return False
    
    def format_table_row(self, line):
        """Format a line as a markdown table row"""
        if '|' in line:
            # Already pipe-separated, clean it up
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            return '| ' + ' | '.join(cells) + ' |'
        elif '\t' in line:
            # Tab-separated
            cells = [cell.strip() for cell in line.split('\t') if cell.strip()]
            return '| ' + ' | '.join(cells) + ' |'
        else:
            # Space-separated (fallback)
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
            
            # Calculate token count for section
            token_count = self.count_tokens(section['content'])
            word_count = len(section['content'].split())
            
            # Extract additional semantic metadata
            semantic_tags = self.extract_semantic_tags(section['content'])
            contains_code = self.detect_code_blocks(section['content'])
            contains_tables = '|' in section['content'] and section['content'].count('|') > 4
            api_endpoints = self.extract_api_endpoints(section['content'])
            processing_priority = self.determine_processing_priority(section.get('type', 'content'))
            
            # Add comprehensive metadata header optimized for LLM processing
            section_content = f"""---
title: {section['title']}
section_type: {section.get('type', 'content')}
processing_priority: {processing_priority}
tokens: {token_count}
words: {word_count}
optimal_model: {self.get_best_fit_model(token_count)}
semantic_tags: {semantic_tags}
contains_code: {contains_code}
contains_tables: {contains_tables}
api_endpoints_count: {len(api_endpoints)}
extracted_endpoints: {api_endpoints if api_endpoints else []}
llm_processing_notes: {self.get_processing_notes(section.get('type', 'content'), contains_code, contains_tables)}
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
        
        return sections
    
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
            # Detect any header level for section breaks (# ## ### etc.)
            header_match = re.match(r'^(#{1,3})\s+(.+)', line)
            
            if header_match:
                header_level = len(header_match.group(1))
                header_title = header_match.group(2).strip()
                
                # For level 1 headers, always start a new section
                # For level 2-3 headers, start new section if current section has content
                should_create_new_section = (
                    header_level == 1 or 
                    (header_level <= 3 and len(current_section['content'].strip()) > 50)
                )
                
                if should_create_new_section and current_section['content'].strip():
                    # Save current section
                    current_section['content'] = current_section['content'].strip()
                    sections.append(current_section)
                    
                    # Start new section
                    slug = self.create_slug(header_title)
                    # Pass current content for better type detection
                    section_type = self.determine_section_type(header_title, current_section['content'])
                    current_section = {
                        'title': header_title,
                        'content': line + '\n',
                        'type': section_type,
                        'slug': slug
                    }
                else:
                    # Add to current section if not creating new one
                    current_section['content'] += line + '\n'
            else:
                # Add all non-header content to current section
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            current_section['content'] = current_section['content'].strip()
            sections.append(current_section)
        
        # Filter out sections that are too small (less than 10 words)
        # but preserve all content by merging small sections with previous ones
        filtered_sections = []
        for section in sections:
            word_count = len(section['content'].split())
            if word_count < 10 and filtered_sections:
                # Merge with previous section
                filtered_sections[-1]['content'] += '\n\n' + section['content']
            else:
                filtered_sections.append(section)
        
        return filtered_sections if filtered_sections else sections
    
    def create_slug(self, title):
        """Create a URL-friendly slug from title"""
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug[:50].strip('-')
    
    def determine_section_type(self, title, content=None):
        """Determine the type of section based on title and content analysis"""
        title_lower = title.lower()
        
        # Enhanced detection with more specific patterns
        type_patterns = {
            'api_endpoint': {
                'title_words': ['endpoint', 'route', 'path', 'api', 'method'],
                'title_patterns': [r'^(GET|POST|PUT|DELETE|PATCH)', r'/api/', r'/{.*}'],
                'content_patterns': [r'(GET|POST|PUT|DELETE|PATCH)\s+/', r'curl\s+-X', r'endpoint:']
            },
            'authentication': {
                'title_words': ['auth', 'authentication', 'authorization', 'oauth', 'jwt', 'token', 'credential', 'login', 'sso'],
                'content_patterns': [r'Bearer\s+', r'API[_\s]?Key', r'client_id', r'client_secret']
            },
            'request_response': {
                'title_words': ['request', 'response', 'payload', 'body', 'header'],
                'content_patterns': [r'Content-Type:', r'{\s*"', r'application/json']
            },
            'error_handling': {
                'title_words': ['error', 'exception', 'status', 'fault', 'failure', 'troubleshoot'],
                'content_patterns': [r'\b[4-5]\d{2}\b', r'error_code', r'error_message']
            },
            'code_examples': {
                'title_words': ['example', 'sample', 'demo', 'tutorial', 'quickstart', 'getting started'],
                'content_patterns': [r'```', r'import\s+', r'function\s+', r'class\s+']
            },
            'data_models': {
                'title_words': ['model', 'schema', 'structure', 'entity', 'object', 'type'],
                'content_patterns': [r'"type":\s*"', r'required":\s*\[', r'properties":\s*{']
            },
            'configuration': {
                'title_words': ['config', 'configuration', 'setting', 'parameter', 'option', 'environment'],
                'content_patterns': [r'ENV\[', r'config\.', r'--[a-z-]+']
            },
            'testing': {
                'title_words': ['test', 'testing', 'validation', 'verify', 'assertion'],
                'content_patterns': [r'assert', r'expect\(', r'test\s+case', r'describe\(']
            },
            'security': {
                'title_words': ['security', 'encryption', 'ssl', 'tls', 'https', 'certificate'],
                'content_patterns': [r'X-.*-Token', r'HTTPS', r'TLS\s+\d']
            },
            'rate_limiting': {
                'title_words': ['rate', 'limit', 'throttle', 'quota', 'usage'],
                'content_patterns': [r'X-Rate-Limit', r'requests?\s+per\s+', r'quota']
            },
            'webhooks': {
                'title_words': ['webhook', 'callback', 'notification', 'event'],
                'content_patterns': [r'webhook_url', r'callback_url', r'event_type']
            },
            'pagination': {
                'title_words': ['pagination', 'paging', 'page', 'limit', 'offset'],
                'content_patterns': [r'page=\d+', r'limit=\d+', r'next_page', r'cursor']
            },
            'versioning': {
                'title_words': ['version', 'versioning', 'v1', 'v2', 'migration'],
                'content_patterns': [r'/v\d+/', r'api_version', r'version:\s*\d']
            },
            'introduction': {
                'title_words': ['intro', 'introduction', 'overview', 'summary', 'about', 'welcome'],
                'content_patterns': [r'This\s+(guide|document|API)', r'Welcome\s+to']
            },
            'reference': {
                'title_words': ['reference', 'specification', 'spec', 'appendix', 'glossary'],
                'content_patterns': [r'See\s+also:', r'Related:', r'Reference:']
            }
        }
        
        # Check each type pattern
        scores = {}
        for section_type, patterns in type_patterns.items():
            score = 0
            
            # Check title words
            for word in patterns.get('title_words', []):
                if word in title_lower:
                    score += 2  # Title matches are weighted higher
            
            # Check title patterns
            for pattern in patterns.get('title_patterns', []):
                if re.search(pattern, title, re.IGNORECASE):
                    score += 3  # Pattern matches are very specific
            
            # Check content patterns if content is provided
            if content:
                content_lower = content.lower()[:1000]  # Check first 1000 chars for efficiency
                for pattern in patterns.get('content_patterns', []):
                    if re.search(pattern, content_lower, re.IGNORECASE):
                        score += 1
            
            if score > 0:
                scores[section_type] = score
        
        # Return the type with highest score, or 'content' as fallback
        if scores:
            return max(scores, key=scores.get)
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
        
        # Write organized TOC with enhanced semantic categories
        type_order = [
            'introduction', 'authentication', 'api_endpoint', 'request_response', 
            'data_models', 'code_examples', 'error_handling', 'security',
            'rate_limiting', 'webhooks', 'pagination', 'versioning', 'testing',
            'configuration', 'reference', 'content'
        ]
        type_names = {
            'introduction': 'Introduction and Overview',
            'authentication': 'Authentication and Authorization',
            'api_endpoint': 'API Endpoints',
            'request_response': 'Requests and Responses',
            'data_models': 'Data Models and Schemas',
            'code_examples': 'Code Examples and Tutorials',
            'error_handling': 'Error Handling',
            'security': 'Security and Encryption',
            'rate_limiting': 'Rate Limiting and Throttling',
            'webhooks': 'Webhooks and Events',
            'pagination': 'Pagination',
            'versioning': 'Versioning and Migration',
            'testing': 'Testing and Validation',
            'configuration': 'Configuration and Settings',
            'reference': 'Reference Documentation',
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

    def extract_semantic_tags(self, content):
        """Extract semantic tags from content for better LLM understanding"""
        tags = set()
        content_lower = content.lower()
        
        # Technical domain tags
        if re.search(r'\b(json|xml|yaml|csv)\b', content_lower):
            tags.add('data-format')
        
        if re.search(r'\b(oauth|jwt|bearer|api[_\s]?key)\b', content_lower):
            tags.add('authentication')
        
        if re.search(r'\b[4-5]\d{2}\b', content):  # HTTP status codes
            tags.add('http-status')
        
        if re.search(r'\bcurl\s+-X\b', content_lower):
            tags.add('curl-example')
        
        if re.search(r'\b(request|response)\s+(body|payload|header)\b', content_lower):
            tags.add('http-message')
        
        if re.search(r'\b(rate[_\s]?limit|throttl|quota)\b', content_lower):
            tags.add('rate-limiting')
        
        if re.search(r'\b(webhook|callback|notification)\b', content_lower):
            tags.add('event-driven')
        
        if re.search(r'\b(encrypt|ssl|tls|certificate)\b', content_lower):
            tags.add('security')
        
        if re.search(r'\b(test|assert|expect|mock)\b', content_lower):
            tags.add('testing')
        
        if re.search(r'\b(version|v\d+|deprecat)\b', content_lower):
            tags.add('versioning')
        
        return list(tags)
    
    def detect_code_blocks(self, content):
        """Detect if content contains code blocks or examples"""
        code_indicators = [
            r'```',  # Markdown code blocks
            r'^\s*{[\s\S]*}$',  # JSON objects
            r'<[^>]+>',  # XML/HTML tags
            r'curl\s+-X',  # cURL commands
            r'(function|class|import|var|const|let)\s+',  # Programming keywords
            r'^\s*[a-zA-Z_]\w*\s*=',  # Variable assignments
            r'if\s*\(',  # Control structures
        ]
        
        for pattern in code_indicators:
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                return True
        
        return False
    
    def extract_api_endpoints(self, content):
        """Extract API endpoints from content"""
        endpoints = []
        
        # Pattern for HTTP methods with paths
        endpoint_patterns = [
            r'(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+([^\s\n]+)',
            r'curl\s+[^"]*(https?://[^\s"]+)',
            r'endpoint[:\s]+([^\s\n]+)',
            r'url[:\s]+([^\s\n]+/api[^\s\n]*)',
        ]
        
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) > 1:
                        endpoints.append(f"{match[0]} {match[1]}")
                    else:
                        endpoints.append(match[0])
                else:
                    endpoints.append(match)
        
        return list(set(endpoints))  # Remove duplicates
    
    def determine_processing_priority(self, section_type):
        """Determine processing priority for LLM workflows"""
        priority_map = {
            'introduction': 'high',  # Start here for context
            'authentication': 'critical',  # Essential for API usage
            'api_endpoint': 'critical',  # Core functionality
            'request_response': 'high',  # Important for implementation
            'data_models': 'high',  # Needed for data structure
            'error_handling': 'medium',  # Important for debugging
            'code_examples': 'high',  # Practical implementation
            'security': 'medium',  # Important for production
            'rate_limiting': 'low',  # Operational concern
            'webhooks': 'medium',  # Feature-specific
            'pagination': 'low',  # Implementation detail
            'versioning': 'low',  # Operational concern
            'testing': 'low',  # Development process
            'configuration': 'medium',  # Setup requirement
            'reference': 'low',  # Lookup information
            'content': 'low'  # General information
        }
        return priority_map.get(section_type, 'low')
    
    def get_processing_notes(self, section_type, has_code, has_tables):
        """Generate processing guidance for LLMs"""
        notes = []
        
        # Type-specific notes
        type_notes = {
            'api_endpoint': 'Focus on HTTP methods, URLs, parameters, and response formats',
            'authentication': 'Extract authentication mechanisms, required headers, and token formats',
            'request_response': 'Parse request/response structures, required fields, and data types',
            'error_handling': 'Identify error codes, error messages, and resolution steps',
            'code_examples': 'Code can be executed or adapted; extract language and dependencies',
            'data_models': 'Extract field definitions, data types, and validation rules',
            'configuration': 'Note configuration keys, environment variables, and setup steps'
        }
        
        if section_type in type_notes:
            notes.append(type_notes[section_type])
        
        # Content-specific notes
        if has_code:
            notes.append('Contains executable code examples')
        
        if has_tables:
            notes.append('Contains structured data in table format')
        
        return notes if notes else ['Standard text content for general processing']
    
    def get_best_fit_model(self, token_count):
        """Determine the best fitting LLM model for a given token count"""
        if token_count <= 3500:
            return "gpt-3.5"
        elif token_count <= 7000:
            return "gpt-4"
        elif token_count <= 30000:
            return "gpt-4-32k"
        elif token_count <= 95000:
            return "claude-instant"
        elif token_count <= 190000:
            return "claude-3"
        else:
            return "requires-splitting"
    
    def count_tokens(self, text):
        """Count tokens in text using tiktoken or approximation"""
        if self.token_encoder:
            try:
                return len(self.token_encoder.encode(text))
            except Exception:
                pass
        
        # Fallback approximation: ~4 characters per token
        return len(text) // 4
    
    def get_llm_context_info(self, token_count):
        """Get context window recommendations based on token count"""
        contexts = {
            "gpt-3.5": {"limit": 4096, "recommended": 3500},
            "gpt-4": {"limit": 8192, "recommended": 7000},
            "gpt-4-32k": {"limit": 32768, "recommended": 30000},
            "gpt-4-turbo": {"limit": 128000, "recommended": 120000},
            "claude-instant": {"limit": 100000, "recommended": 95000},
            "claude-2": {"limit": 100000, "recommended": 95000},
            "claude-3": {"limit": 200000, "recommended": 190000},
        }
        
        recommendations = []
        for model, limits in contexts.items():
            if token_count <= limits["recommended"]:
                status = "✅ Fits comfortably"
            elif token_count <= limits["limit"]:
                status = "⚠️ Near limit"
            else:
                status = "❌ Exceeds limit"
            
            recommendations.append({
                "model": model,
                "status": status,
                "usage": f"{token_count}/{limits['limit']} tokens ({(token_count/limits['limit']*100):.1f}%)"
            })
        
        return recommendations
    
    def generate_metadata_file(self):
        """Generate comprehensive metadata about the conversion"""
        metadata = {
            "generated": datetime.now().isoformat(),
            "source_pdf": os.path.basename(self.pdf_path),
            "output_directory": str(self.output_dir),
            "conversion_settings": {
                "preserve_tables": self.preserve_tables,
                "extract_images": self.extract_images
            },
            "sections": [],
            "statistics": {
                "total_sections": 0,
                "total_tokens": 0,
                "total_words": 0,
                "total_characters": 0,
                "tables_extracted": 0,
                "images_extracted": 0
            },
            "token_distribution": {
                "small": 0,  # < 1000 tokens
                "medium": 0,  # 1000-5000 tokens
                "large": 0,   # 5000-10000 tokens
                "xlarge": 0   # > 10000 tokens
            }
        }
        
        # Analyze sections
        sections_dir = self.output_dir / "sections"
        if sections_dir.exists():
            for section_file in sorted(sections_dir.glob("*.md")):
                with open(section_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata from front matter
                section_info = {
                    "filename": section_file.name,
                    "path": str(section_file.relative_to(self.output_dir))
                }
                
                # Parse front matter if exists
                if content.startswith("---"):
                    try:
                        end_idx = content.index("---", 3)
                        front_matter = content[3:end_idx].strip()
                        # Simple parsing of YAML-like front matter
                        for line in front_matter.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                section_info[key.strip()] = value.strip()
                        
                        # Get actual content after front matter
                        actual_content = content[end_idx+3:].strip()
                    except ValueError:
                        actual_content = content
                else:
                    actual_content = content
                
                # Calculate metrics
                token_count = self.count_tokens(actual_content)
                word_count = len(actual_content.split())
                char_count = len(actual_content)
                
                section_info.update({
                    "tokens": token_count,
                    "words": word_count,
                    "characters": char_count,
                    "llm_compatibility": self.get_llm_context_info(token_count)
                })
                
                # Categorize by size
                if token_count < 1000:
                    metadata["token_distribution"]["small"] += 1
                elif token_count < 5000:
                    metadata["token_distribution"]["medium"] += 1
                elif token_count < 10000:
                    metadata["token_distribution"]["large"] += 1
                else:
                    metadata["token_distribution"]["xlarge"] += 1
                
                metadata["sections"].append(section_info)
                metadata["statistics"]["total_tokens"] += token_count
                metadata["statistics"]["total_words"] += word_count
                metadata["statistics"]["total_characters"] += char_count
        
        metadata["statistics"]["total_sections"] = len(metadata["sections"])
        
        # Count tables and images
        if (self.output_dir / "complete" / "full-document.md").exists():
            with open(self.output_dir / "complete" / "full-document.md", 'r', encoding='utf-8') as f:
                full_content = f.read()
                metadata["statistics"]["tables_extracted"] = full_content.count("**Table ")
                metadata["statistics"]["images_extracted"] = full_content.count("![Image from page")
        
        # Add overall recommendations
        total_tokens = metadata["statistics"]["total_tokens"]
        metadata["recommendations"] = {
            "optimal_chunk_size": self.recommend_chunk_size(total_tokens),
            "processing_strategy": self.recommend_processing_strategy(metadata),
            "llm_compatibility_summary": self.get_llm_context_info(total_tokens)
        }
        
        # Save metadata
        metadata_file = self.output_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Also create a markdown summary
        self.create_metadata_summary(metadata)
    
    def recommend_chunk_size(self, total_tokens):
        """Recommend optimal chunk size based on total tokens"""
        if total_tokens < 4000:
            return "single_chunk"
        elif total_tokens < 30000:
            return "small_chunks_4k"
        elif total_tokens < 100000:
            return "medium_chunks_8k"
        else:
            return "large_chunks_32k"
    
    def recommend_processing_strategy(self, metadata):
        """Recommend how to process the document with LLMs"""
        strategies = []
        
        dist = metadata["token_distribution"]
        total_sections = metadata["statistics"]["total_sections"]
        
        if dist["xlarge"] > 0:
            strategies.append("⚠️ Large sections detected - consider splitting further")
        
        if total_sections > 20:
            strategies.append("📚 Many sections - process in batches or use hierarchical summarization")
        
        if metadata["statistics"]["tables_extracted"] > 5:
            strategies.append("📊 Multiple tables - consider specialized table processing")
        
        if dist["small"] > total_sections * 0.5:
            strategies.append("✅ Many small sections - can process multiple at once")
        
        return strategies if strategies else ["✅ Document is well-structured for LLM processing"]
    
    def extract_api_endpoints_to_files(self, content):
        """Extract API endpoints and create dedicated files for each"""
        endpoints_dir = self.output_dir / "api-endpoints"
        endpoints_dir.mkdir(exist_ok=True)
        
        # Extract all endpoints with their context
        endpoints = self.find_detailed_endpoints(content)
        
        if not endpoints:
            return
        
        endpoint_files = []
        
        for i, endpoint in enumerate(endpoints, 1):
            # Create filename from endpoint
            filename = self.create_endpoint_filename(endpoint['method'], endpoint['path'])
            filepath = endpoints_dir / f"{i:02d}-{filename}.md"
            
            # Create structured endpoint documentation
            endpoint_content = self.create_endpoint_documentation(endpoint)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(endpoint_content)
            
            endpoint_files.append({
                'filename': filepath.name,
                'method': endpoint['method'],
                'path': endpoint['path'],
                'summary': endpoint.get('summary', 'No summary available')
            })
        
        # Create API index file
        self.create_api_index(endpoint_files)
        
        return endpoint_files
    
    def find_detailed_endpoints(self, content):
        """Find API endpoints with detailed context analysis"""
        endpoints = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for HTTP method patterns
            method_match = re.match(r'^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+([^\s\n]+)', line.strip(), re.IGNORECASE)
            
            if method_match:
                method = method_match.group(1).upper()
                path = method_match.group(2)
                
                # Extract context around the endpoint (before and after)
                context_before = '\n'.join(lines[max(0, i-10):i])
                context_after = '\n'.join(lines[i+1:min(len(lines), i+20)])
                
                endpoint = {
                    'method': method,
                    'path': path,
                    'line_number': i,
                    'context_before': context_before,
                    'context_after': context_after,
                    'full_context': '\n'.join(lines[max(0, i-5):min(len(lines), i+15)])
                }
                
                # Extract additional information
                endpoint.update(self.analyze_endpoint_context(endpoint))
                endpoints.append(endpoint)
        
        # Remove duplicates based on method and path
        unique_endpoints = []
        seen = set()
        for ep in endpoints:
            key = f"{ep['method']} {ep['path']}"
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(ep)
        
        return unique_endpoints
    
    def analyze_endpoint_context(self, endpoint):
        """Analyze the context around an endpoint to extract detailed information"""
        full_context = endpoint['full_context']
        analysis = {
            'summary': '',
            'description': '',
            'parameters': [],
            'request_body': {},
            'responses': {},
            'headers': [],
            'authentication': '',
            'examples': []
        }
        
        # Extract summary (look for headers or descriptions near the endpoint)
        summary_patterns = [
            r'(?:#+\s*)([^\n]+?)(?:\n|$)',  # Markdown headers
            r'(?:^|\n)([A-Z][^.\n]+\.)',   # Sentences starting with capital letters
        ]
        
        for pattern in summary_patterns:
            matches = re.findall(pattern, endpoint['context_before'], re.MULTILINE)
            if matches:
                analysis['summary'] = matches[-1].strip()  # Take the last/closest match
                break
        
        # Extract parameters from URL path
        path_params = re.findall(r'\{([^}]+)\}', endpoint['path'])
        for param in path_params:
            analysis['parameters'].append({
                'name': param,
                'location': 'path',
                'type': 'string',  # Default assumption
                'required': True
            })
        
        # Look for query parameters in context
        query_patterns = [
            r'[?&]([a-zA-Z_][a-zA-Z0-9_]*)=',
            r'parameter[s]?:\s*([a-zA-Z_][a-zA-Z0-9_,\s]*)',
            r'query:\s*([a-zA-Z_][a-zA-Z0-9_,\s]*)'
        ]
        
        for pattern in query_patterns:
            matches = re.findall(pattern, full_context, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    params = [p.strip() for p in match.split(',')]
                    for param in params:
                        if param and param not in [p['name'] for p in analysis['parameters']]:
                            analysis['parameters'].append({
                                'name': param,
                                'location': 'query',
                                'type': 'string',
                                'required': False
                            })
        
        # Extract request body information (JSON patterns)
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple JSON objects
            r'```json\s*\n(.*?)\n```',           # Code blocks
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, full_context, re.DOTALL | re.IGNORECASE)
            if matches:
                try:
                    # Try to parse as JSON to validate
                    json.loads(matches[0])
                    analysis['request_body'] = {
                        'content_type': 'application/json',
                        'example': matches[0],
                        'schema': 'See example for structure'
                    }
                    break
                except:
                    # If not valid JSON, still include as example
                    analysis['request_body'] = {
                        'content_type': 'application/json',
                        'example': matches[0],
                        'schema': 'Example may need validation'
                    }
                    break
        
        # Extract response information (status codes)
        status_codes = re.findall(r'\b(2\d{2}|3\d{2}|4\d{2}|5\d{2})\b', full_context)
        for code in set(status_codes):  # Remove duplicates
            analysis['responses'][code] = {
                'description': self.get_status_code_description(code)
            }
        
        # Extract authentication information
        auth_patterns = [
            r'Bearer\s+token',
            r'API[_\s]?Key',
            r'Authorization:\s*([^\n]+)',
            r'auth[a-z]*:\s*([^\n]+)'
        ]
        
        for pattern in auth_patterns:
            matches = re.findall(pattern, full_context, re.IGNORECASE)
            if matches:
                analysis['authentication'] = matches[0] if isinstance(matches[0], str) else 'Required'
                break
        
        # Extract cURL examples
        curl_pattern = r'curl\s+[^`\n]*(?:`[^`]*`[^`\n]*)*'
        curl_matches = re.findall(curl_pattern, full_context, re.IGNORECASE | re.MULTILINE)
        for curl in curl_matches:
            analysis['examples'].append({
                'language': 'curl',
                'code': curl.strip()
            })
        
        return analysis
    
    def create_endpoint_filename(self, method, path):
        """Create a safe filename for an endpoint"""
        # Clean the path
        clean_path = re.sub(r'[^\w\-_/]', '', path)
        clean_path = clean_path.replace('/', '-').strip('-')
        
        # Combine method and path
        filename = f"{method.lower()}-{clean_path}"
        
        # Ensure it's not too long
        return filename[:50].strip('-')
    
    def create_endpoint_documentation(self, endpoint):
        """Create comprehensive documentation for a single endpoint"""
        method = endpoint['method']
        path = endpoint['path']
        
        # Calculate tokens for the endpoint documentation
        full_content = endpoint['full_context']
        token_count = self.count_tokens(full_content)
        
        doc = f"""---
title: {method} {path}
method: {method}
path: {path}
endpoint_type: api_endpoint
tokens: {token_count}
optimal_model: {self.get_best_fit_model(token_count)}
has_parameters: {len(endpoint.get('parameters', [])) > 0}
has_request_body: {bool(endpoint.get('request_body', {}))}
has_examples: {len(endpoint.get('examples', [])) > 0}
authentication_required: {bool(endpoint.get('authentication', ''))}
---

# {method} {path}

## Summary
{endpoint.get('summary', 'No summary available')}

## Description
{endpoint.get('description', 'No detailed description available')}

## Authentication
{endpoint.get('authentication', 'Authentication requirements not specified')}

## Parameters
"""
        
        # Add parameters section
        if endpoint.get('parameters'):
            doc += "\n| Name | Location | Type | Required | Description |\n"
            doc += "|------|----------|------|----------|-------------|\n"
            for param in endpoint['parameters']:
                doc += f"| {param['name']} | {param['location']} | {param['type']} | {param['required']} | - |\n"
        else:
            doc += "No parameters required.\n"
        
        # Add request body section
        if endpoint.get('request_body'):
            req_body = endpoint['request_body']
            doc += f"\n## Request Body\n"
            doc += f"**Content-Type:** {req_body.get('content_type', 'application/json')}\n\n"
            if req_body.get('example'):
                doc += f"**Example:**\n```json\n{req_body['example']}\n```\n"
        
        # Add responses section
        doc += "\n## Responses\n"
        if endpoint.get('responses'):
            for code, response in endpoint['responses'].items():
                doc += f"\n### {code}\n{response.get('description', 'No description')}\n"
        else:
            doc += "Response formats not documented in source.\n"
        
        # Add examples section
        if endpoint.get('examples'):
            doc += "\n## Examples\n"
            for example in endpoint['examples']:
                doc += f"\n### {example['language'].upper()}\n```{example['language']}\n{example['code']}\n```\n"
        
        # Add raw context for LLM reference
        doc += f"\n## Source Context\n```\n{endpoint['full_context'][:1000]}{'...' if len(endpoint['full_context']) > 1000 else ''}\n```\n"
        
        return doc
    
    def get_status_code_description(self, code):
        """Get human-readable description for HTTP status codes"""
        descriptions = {
            '200': 'OK - Success',
            '201': 'Created - Resource created successfully',
            '204': 'No Content - Success with no response body',
            '400': 'Bad Request - Invalid request format',
            '401': 'Unauthorized - Authentication required',
            '403': 'Forbidden - Access denied',
            '404': 'Not Found - Resource not found',
            '422': 'Unprocessable Entity - Validation failed',
            '500': 'Internal Server Error - Server error'
        }
        return descriptions.get(code, f'HTTP {code}')
    
    def apply_smart_chunking(self, sections):
        """Apply smart chunking to sections that exceed token limits"""
        chunked_dir = self.output_dir / "chunked"
        chunked_dir.mkdir(exist_ok=True)
        
        # Define token limits for different LLM context windows
        chunk_limits = {
            'small': 3500,    # GPT-3.5 safe limit
            'medium': 7000,   # GPT-4 safe limit  
            'large': 30000,   # GPT-4-32K safe limit
            'xlarge': 95000   # Claude safe limit
        }
        
        chunked_sections = []
        
        for section in sections:
            token_count = self.count_tokens(section['content'])
            
            # If section is small enough, no chunking needed
            if token_count <= chunk_limits['small']:
                continue
                
            # Determine which chunk sizes to create
            chunks_to_create = []
            if token_count > chunk_limits['small']:
                chunks_to_create.append(('small', chunk_limits['small']))
            if token_count > chunk_limits['medium']:
                chunks_to_create.append(('medium', chunk_limits['medium']))
            if token_count > chunk_limits['large']:
                chunks_to_create.append(('large', chunk_limits['large']))
            
            # Create chunks for each size
            for chunk_size, token_limit in chunks_to_create:
                chunks = self.chunk_section_intelligently(section, token_limit)
                
                if len(chunks) > 1:  # Only save if actually chunked
                    chunk_dir = chunked_dir / chunk_size
                    chunk_dir.mkdir(exist_ok=True)
                    
                    # Save chunked files
                    for i, chunk in enumerate(chunks, 1):
                        chunk_filename = f"{section['slug']}-chunk-{i:02d}.md"
                        chunk_filepath = chunk_dir / chunk_filename
                        
                        chunk_content = self.create_chunk_documentation(
                            section, chunk, i, len(chunks), chunk_size, token_limit
                        )
                        
                        with open(chunk_filepath, 'w', encoding='utf-8') as f:
                            f.write(chunk_content)
                        
                        chunked_sections.append({
                            'original_section': section['title'],
                            'chunk_size': chunk_size,
                            'chunk_number': i,
                            'total_chunks': len(chunks),
                            'filename': chunk_filename,
                            'tokens': self.count_tokens(chunk['content'])
                        })
        
        # Create chunking index
        if chunked_sections:
            self.create_chunking_index(chunked_sections)
        
        return chunked_sections
    
    def chunk_section_intelligently(self, section, token_limit):
        """Split a section into chunks at natural boundaries"""
        content = section['content']
        chunks = []
        
        # First, try to split by major headers (## or ###)
        header_splits = self.split_by_headers(content, token_limit)
        if header_splits:
            return header_splits
        
        # If no header splits work, try paragraph boundaries
        paragraph_splits = self.split_by_paragraphs(content, token_limit)
        if paragraph_splits:
            return paragraph_splits
        
        # Last resort: split by sentences
        sentence_splits = self.split_by_sentences(content, token_limit)
        return sentence_splits
    
    def split_by_headers(self, content, token_limit):
        """Split content by markdown headers"""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = self.count_tokens(line)
            
            # Check if this is a header that could be a good split point
            if re.match(r'^#{2,4}\s+', line) and current_tokens > 0:
                # Check if adding this line would exceed limit
                if current_tokens + line_tokens > token_limit * 0.9:  # 90% safety margin
                    # Save current chunk
                    if current_chunk:
                        chunks.append({
                            'content': '\n'.join(current_chunk),
                            'split_type': 'header',
                            'boundary': line.strip()
                        })
                        current_chunk = []
                        current_tokens = 0
            
            current_chunk.append(line)
            current_tokens += line_tokens
            
            # Emergency split if we're way over limit
            if current_tokens > token_limit:
                chunks.append({
                    'content': '\n'.join(current_chunk[:-1]),
                    'split_type': 'forced',
                    'boundary': 'Token limit exceeded'
                })
                current_chunk = [line]
                current_tokens = line_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': '\n'.join(current_chunk),
                'split_type': 'final',
                'boundary': 'End of section'
            })
        
        return chunks if len(chunks) > 1 else []
    
    def split_by_paragraphs(self, content, token_limit):
        """Split content by paragraph boundaries"""
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)
            
            # If single paragraph exceeds limit, we need sentence splitting
            if paragraph_tokens > token_limit:
                if current_chunk:
                    chunks.append({
                        'content': '\n\n'.join(current_chunk),
                        'split_type': 'paragraph',
                        'boundary': 'Paragraph boundary'
                    })
                    current_chunk = []
                    current_tokens = 0
                
                # Split this large paragraph by sentences
                sentence_chunks = self.split_large_paragraph_by_sentences(paragraph, token_limit)
                chunks.extend(sentence_chunks)
                continue
            
            # Check if adding this paragraph would exceed limit
            if current_tokens + paragraph_tokens > token_limit * 0.9:
                if current_chunk:
                    chunks.append({
                        'content': '\n\n'.join(current_chunk),
                        'split_type': 'paragraph',
                        'boundary': 'Paragraph boundary'
                    })
                    current_chunk = []
                    current_tokens = 0
            
            current_chunk.append(paragraph)
            current_tokens += paragraph_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': '\n\n'.join(current_chunk),
                'split_type': 'paragraph',
                'boundary': 'End of section'
            })
        
        return chunks if len(chunks) > 1 else []
    
    def split_by_sentences(self, content, token_limit):
        """Split content by sentence boundaries as last resort"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', content)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > token_limit * 0.9:
                if current_chunk:
                    chunks.append({
                        'content': ' '.join(current_chunk),
                        'split_type': 'sentence',
                        'boundary': 'Sentence boundary'
                    })
                    current_chunk = []
                    current_tokens = 0
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': ' '.join(current_chunk),
                'split_type': 'sentence',
                'boundary': 'End of section'
            })
        
        return chunks if len(chunks) > 1 else []
    
    def split_large_paragraph_by_sentences(self, paragraph, token_limit):
        """Split a large paragraph by sentences"""
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > token_limit * 0.9:
                if current_chunk:
                    chunks.append({
                        'content': ' '.join(current_chunk),
                        'split_type': 'sentence',
                        'boundary': 'Large paragraph split'
                    })
                    current_chunk = []
                    current_tokens = 0
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append({
                'content': ' '.join(current_chunk),
                'split_type': 'sentence',
                'boundary': 'Large paragraph split'
            })
        
        return chunks
    
    def create_chunk_documentation(self, original_section, chunk, chunk_num, total_chunks, chunk_size, token_limit):
        """Create documentation for a chunk"""
        chunk_tokens = self.count_tokens(chunk['content'])
        
        return f"""---
title: {original_section['title']} (Part {chunk_num})
original_section: {original_section['title']}
section_type: {original_section.get('type', 'content')}
chunk_info:
  chunk_number: {chunk_num}
  total_chunks: {total_chunks}
  chunk_size: {chunk_size}
  token_limit: {token_limit}
  actual_tokens: {chunk_tokens}
  split_type: {chunk['split_type']}
  split_boundary: {chunk['boundary']}
optimal_model: {self.get_best_fit_model(chunk_tokens)}
processing_priority: {self.determine_processing_priority(original_section.get('type', 'content'))}
is_chunk: true
---

# {original_section['title']} (Part {chunk_num} of {total_chunks})

**Chunk Information:**
- **Size**: {chunk_size} token limit ({chunk_tokens} actual tokens)
- **Split Method**: {chunk['split_type']}
- **Split Boundary**: {chunk['boundary']}
- **Optimal Model**: {self.get_best_fit_model(chunk_tokens)}

## Content

{chunk['content']}

---

**Navigation:**
- **Previous**: {'Part ' + str(chunk_num - 1) if chunk_num > 1 else 'Original section'}
- **Next**: {'Part ' + str(chunk_num + 1) if chunk_num < total_chunks else 'End of section'}
- **Original Section**: {original_section['title']}

**Processing Notes:**
- This is a chunked section optimized for {chunk_size} context windows
- Consider processing chunks in sequence for complete understanding
- Reference original section for full context if needed
"""
    
    def create_chunking_index(self, chunked_sections):
        """Create an index of all chunked sections"""
        index_content = f"""# Smart Chunking Index

Generated: {datetime.now().isoformat()}
Total Chunked Sections: {len(set(c['original_section'] for c in chunked_sections))}
Total Chunks Created: {len(chunked_sections)}

## Chunking Strategy

This document contains sections that were automatically split to fit within different LLM context windows:

- **Small chunks (3.5K tokens)**: Optimized for GPT-3.5
- **Medium chunks (7K tokens)**: Optimized for GPT-4
- **Large chunks (30K tokens)**: Optimized for GPT-4-32K
- **XLarge chunks (95K tokens)**: Optimized for Claude

## Chunked Sections Overview

"""
        
        # Group by original section
        sections_map = {}
        for chunk in chunked_sections:
            original = chunk['original_section']
            if original not in sections_map:
                sections_map[original] = {}
            
            chunk_size = chunk['chunk_size']
            if chunk_size not in sections_map[original]:
                sections_map[original][chunk_size] = []
            
            sections_map[original][chunk_size].append(chunk)
        
        for section_name, size_chunks in sections_map.items():
            index_content += f"\n### {section_name}\n\n"
            
            for chunk_size, chunks in size_chunks.items():
                index_content += f"**{chunk_size.title()} Chunks ({len(chunks)} parts):**\n"
                for chunk in chunks:
                    index_content += f"- [Part {chunk['chunk_number']}]({chunk_size}/{chunk['filename']}) - {chunk['tokens']} tokens\n"
                index_content += "\n"
        
        index_content += """
## Usage Guidelines

### For LLM Processing:
1. **Choose appropriate chunk size** based on your LLM's context window
2. **Process chunks sequentially** for complete understanding
3. **Reference original sections** when context is needed across chunks
4. **Use chunk metadata** for processing optimization

### Chunk Selection:
- **GPT-3.5**: Use small chunks (3.5K tokens)
- **GPT-4**: Use medium chunks (7K tokens) 
- **GPT-4-32K**: Use large chunks (30K tokens)
- **Claude**: Use xlarge chunks (95K tokens) or original sections

### Processing Strategies:
- **Sequential Processing**: Process chunks in order for complete coverage
- **Parallel Processing**: Process independent chunks simultaneously
- **Summarization**: Use chunks to create progressive summaries
- **Context Building**: Combine chunks for comprehensive analysis

## Technical Details

Chunking is performed using intelligent boundary detection:
1. **Header boundaries**: Split at markdown headers (##, ###)
2. **Paragraph boundaries**: Split at paragraph breaks
3. **Sentence boundaries**: Split at sentence endings (last resort)

Each chunk preserves:
- Original context and meaning
- Proper markdown formatting
- Metadata for processing guidance
- Navigation links between chunks
"""
        
        # Save index
        index_file = self.output_dir / "chunked" / "README.md"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
    
    def detect_table_title(self, table_data, page_num):
        """Detect or generate a title for a table"""
        if not table_data or not table_data[0]:
            return f"Table {page_num}"
        
        # Use first row as potential title if it looks like a header
        first_row = table_data[0]
        if len(first_row) == 1 and len(first_row[0]) > 0:
            # Single cell in first row might be a title
            title = str(first_row[0]).strip()
            if len(title) < 100 and not any(char in title for char in '|():'):
                return title
        
        # Generate title from column headers
        if len(first_row) > 1:
            headers = [str(cell).strip() for cell in first_row if cell]
            if headers:
                return f"Table: {' vs '.join(headers[:3])}"
        
        return f"Table {page_num}"
    
    def convert_tables_to_structured_formats(self):
        """Convert extracted tables to JSON and YAML formats"""
        if not self.extracted_tables:
            return
        
        # Create tables directory
        tables_dir = self.output_dir / "tables"
        tables_dir.mkdir(exist_ok=True)
        
        # Convert each table
        all_tables_data = []
        
        for i, table_info in enumerate(self.extracted_tables, 1):
            table_data = self.process_table_for_structure(table_info)
            all_tables_data.append(table_data)
            
            # Create individual table files
            table_filename = f"table_{i:02d}"
            
            # Save as JSON for programmatic access
            json_file = tables_dir / f"{table_filename}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(table_data, f, indent=2, ensure_ascii=False)
            
            # Create enhanced markdown version
            self.create_enhanced_table_markdown(table_info, table_data, tables_dir / f"{table_filename}.md")
        
        # Create tables index
        self.create_tables_index(all_tables_data, tables_dir)
        
        return len(all_tables_data)
    
    def process_table_for_structure(self, table_info):
        """Process table data into structured format"""
        metadata = {
            'title': table_info['title'],
            'page': table_info['page'],
            'table_index': table_info['table_index'],
            'extracted_at': datetime.now().isoformat(),
            'data_types': {},
            'summary_stats': {},
            'structure': {}
        }
        
        if table_info['dataframe'] is not None:
            df = table_info['dataframe']
            
            # Basic structure info
            metadata['structure'] = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns)
            }
            
            # Data type detection and conversion
            processed_data = []
            for _, row in df.iterrows():
                row_data = {}
                for col in df.columns:
                    value = row[col]
                    processed_value, data_type = self.detect_and_convert_cell_value(value)
                    row_data[col] = processed_value
                    
                    # Track data types
                    if col not in metadata['data_types']:
                        metadata['data_types'][col] = {}
                    if data_type not in metadata['data_types'][col]:
                        metadata['data_types'][col][data_type] = 0
                    metadata['data_types'][col][data_type] += 1
                
                processed_data.append(row_data)
            
            # Summary statistics for numeric columns
            for col in df.columns:
                numeric_values = []
                for row in processed_data:
                    if isinstance(row[col], (int, float)):
                        numeric_values.append(row[col])
                
                if numeric_values:
                    metadata['summary_stats'][col] = {
                        'count': len(numeric_values),
                        'min': min(numeric_values),
                        'max': max(numeric_values),
                        'avg': sum(numeric_values) / len(numeric_values)
                    }
        else:
            # Process raw table data
            raw_data = table_info['raw_data']
            if raw_data and len(raw_data) > 1:
                headers = raw_data[0] if raw_data[0] else [f"Column_{i}" for i in range(len(raw_data[1]))]
                
                metadata['structure'] = {
                    'rows': len(raw_data) - 1,
                    'columns': len(headers),
                    'column_names': headers
                }
                
                processed_data = []
                for row_data in raw_data[1:]:
                    if row_data:
                        row_dict = {}
                        for i, header in enumerate(headers):
                            value = row_data[i] if i < len(row_data) else ""
                            processed_value, data_type = self.detect_and_convert_cell_value(value)
                            row_dict[header] = processed_value
                        processed_data.append(row_dict)
            else:
                processed_data = []
        
        return {
            'metadata': metadata,
            'data': processed_data
        }
    
    def detect_and_convert_cell_value(self, value):
        """Detect the data type and convert cell value appropriately"""
        if pd.isna(value) or value == '' or value is None:
            return None, 'null'
        
        str_value = str(value).strip()
        
        # Try integer
        try:
            if '.' not in str_value and str_value.isdigit():
                return int(str_value), 'integer'
        except ValueError:
            pass
        
        # Try float
        try:
            if '.' in str_value:
                return float(str_value), 'float'
        except ValueError:
            pass
        
        # Check for boolean
        if str_value.lower() in ['true', 'false', 'yes', 'no']:
            return str_value.lower() in ['true', 'yes'], 'boolean'
        
        # Check for dates (basic patterns)
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, str_value):
                return str_value, 'date'
        
        # Check for URLs
        if str_value.startswith(('http://', 'https://', 'www.')):
            return str_value, 'url'
        
        # Check for emails
        if '@' in str_value and '.' in str_value:
            return str_value, 'email'
        
        # Default to string
        return str_value, 'string'
    
    def create_enhanced_table_markdown(self, table_info, structured_data, output_file):
        """Create enhanced markdown file for a table with metadata"""
        metadata = structured_data['metadata']
        data = structured_data['data']
        
        content = f"""---
title: {metadata['title']}
table_info:
  page: {metadata['page']}
  table_index: {metadata['table_index']}
  extracted_at: {metadata['extracted_at']}
structure:
  rows: {metadata['structure'].get('rows', 0)}
  columns: {metadata['structure'].get('columns', 0)}
  column_names: {metadata['structure'].get('column_names', [])}
data_types: {json.dumps(metadata['data_types'], indent=2) if metadata['data_types'] else '{}'}
summary_stats: {json.dumps(metadata['summary_stats'], indent=2) if metadata['summary_stats'] else '{}'}
---

# {metadata['title']}

**Table Information:**
- **Source Page**: {metadata['page']}
- **Rows**: {metadata['structure'].get('rows', 0)}
- **Columns**: {metadata['structure'].get('columns', 0)}
- **Extracted**: {metadata['extracted_at'][:19]}

## Structure Analysis

### Column Information
"""
        
        # Add column analysis
        if metadata['data_types']:
            for col, types in metadata['data_types'].items():
                primary_type = max(types.items(), key=lambda x: x[1])[0]
                content += f"- **{col}**: Primary type `{primary_type}`"
                if len(types) > 1:
                    content += f" (mixed: {', '.join(f'{t}({c})' for t, c in types.items())})"
                content += "\n"
        
        # Add summary statistics
        if metadata['summary_stats']:
            content += "\n### Summary Statistics\n"
            for col, stats in metadata['summary_stats'].items():
                content += f"- **{col}**: {stats['count']} values, range {stats['min']:.2f} - {stats['max']:.2f}, avg {stats['avg']:.2f}\n"
        
        # Add the actual table
        if data and table_info['dataframe'] is not None:
            content += "\n## Table Data\n\n"
            content += table_info['dataframe'].to_markdown(index=False, tablefmt='pipe')
        elif data:
            content += "\n## Table Data\n\n"
            if metadata['structure'].get('column_names'):
                headers = metadata['structure']['column_names']
                content += "| " + " | ".join(headers) + " |\n"
                content += "| " + " | ".join("---" for _ in headers) + " |\n"
                
                for row in data:
                    row_values = [str(row.get(col, "")) for col in headers]
                    content += "| " + " | ".join(row_values) + " |\n"
        
        content += f"""

## Processing Notes

- **Data Types**: Automatically detected and converted
- **Quality**: {len([r for r in data if any(v for v in r.values())])} non-empty rows out of {len(data) if data else 0}
- **Format**: Available in JSON format for LLM processing
- **LLM Ready**: Structured data optimized for programmatic analysis

## Available Formats

- **Markdown**: This file (enhanced with metadata and analysis)
- **JSON**: `table_{metadata['table_index']:02d}.json` (structured data for LLM processing)

## Usage Examples

### Load JSON in Python
```python
import json
with open('table_{metadata['table_index']:02d}.json') as f:
    table_data = json.load(f)
    
# Access data
rows = table_data['data']
metadata = table_data['metadata']
```

### Query Data
```python
# Filter rows by condition (example)
filtered = [row for row in table_data['data'] if row.get('column_name') == 'value']

# Get column values
column_values = [row.get('column_name') for row in table_data['data']]
```
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def create_tables_index(self, all_tables_data, tables_dir):
        """Create an index of all structured tables"""
        index_content = f"""# Tables Index

Generated: {datetime.now().isoformat()}
Total Tables: {len(all_tables_data)}

## Table Summary

"""
        
        for i, table_data in enumerate(all_tables_data, 1):
            metadata = table_data['metadata']
            structure = metadata['structure']
            
            index_content += f"""### Table {i}: {metadata['title']}

- **Source**: Page {metadata['page']}
- **Size**: {structure.get('rows', 0)} rows × {structure.get('columns', 0)} columns
- **Columns**: {', '.join(structure.get('column_names', []))}
- **Files**: 
  - [Markdown](table_{i:02d}.md) - Enhanced documentation with analysis
  - [JSON](table_{i:02d}.json) - Structured data for LLM processing

"""
        
        index_content += """## Processing Information

### Data Type Detection
Tables are automatically analyzed for:
- **Numeric data**: Integers and floats with summary statistics
- **Dates**: Common date formats (YYYY-MM-DD, MM/DD/YYYY, etc.)
- **URLs and Emails**: Automatically identified
- **Boolean values**: True/false, yes/no patterns
- **Mixed types**: Columns with multiple data types are flagged

### Available Formats

1. **Markdown (.md)**: Enhanced documentation with metadata and analysis
2. **JSON (.json)**: Structured data optimized for LLM processing

### LLM Integration

The structured table data is optimized for:
- **Data Analysis**: Query and filter operations
- **Report Generation**: Summary statistics and insights
- **API Development**: Direct JSON integration
- **Data Visualization**: Structured format for charts and graphs
- **Machine Learning**: Clean, typed data for analysis

### Usage Patterns

```python
# Load all tables
import json
import glob

table_files = glob.glob('tables/*.json')
all_tables = []
for file in table_files:
    with open(file) as f:
        all_tables.append(json.load(f))

# Analyze table structures
for table in all_tables:
    print(f"Table: {table['metadata']['title']}")
    print(f"Columns: {table['metadata']['structure']['column_names']}")
    print(f"Data types: {table['metadata']['data_types']}")
```

## Quality Metrics

"""
        
        # Add quality metrics
        total_rows = sum(t['metadata']['structure'].get('rows', 0) for t in all_tables_data)
        total_cols = sum(t['metadata']['structure'].get('columns', 0) for t in all_tables_data)
        
        index_content += f"""- **Total Data Points**: {total_rows} rows across {len(all_tables_data)} tables
- **Average Table Size**: {total_rows / len(all_tables_data):.1f} rows per table
- **Column Distribution**: {total_cols} total columns
- **Data Type Coverage**: Numeric, text, dates, URLs, and boolean detection
- **Processing Success**: {len([t for t in all_tables_data if t['data']])} tables with extracted data
"""
        
        # Save index
        index_file = tables_dir / "README.md"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
    
    def build_searchable_index(self, content, sections):
        """Build comprehensive searchable index with terms, endpoints, and error codes"""
        index_dir = self.output_dir / "search-index"
        index_dir.mkdir(exist_ok=True)
        
        # Extract different types of searchable content
        terms_index = self.extract_technical_terms(content, sections)
        endpoints_index = self.extract_endpoints_for_search(content, sections)
        error_codes_index = self.extract_error_codes(content, sections)
        concepts_index = self.extract_key_concepts(content, sections)
        
        # Build comprehensive search database
        search_database = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_terms': len(terms_index),
                'total_endpoints': len(endpoints_index),
                'total_error_codes': len(error_codes_index),
                'total_concepts': len(concepts_index),
                'search_types': ['terms', 'endpoints', 'errors', 'concepts']
            },
            'terms': terms_index,
            'endpoints': endpoints_index,
            'error_codes': error_codes_index,
            'concepts': concepts_index
        }
        
        # Save main search database
        search_file = index_dir / "search-database.json"
        with open(search_file, 'w', encoding='utf-8') as f:
            json.dump(search_database, f, indent=2, ensure_ascii=False)
        
        # Create individual indexes for different search types
        self.create_individual_indexes(index_dir, search_database)
        
        # Create search interface documentation
        self.create_search_documentation(index_dir, search_database)
        
        return len(terms_index) + len(endpoints_index) + len(error_codes_index)
    
    def extract_technical_terms(self, content, sections):
        """Extract and index technical terms with frequency and context"""
        terms_index = {}
        
        # Technical term patterns
        patterns = {
            'api_terms': r'\b(?:API|REST|GraphQL|endpoint|authentication|authorization|token|OAuth|JWT|CORS|rate.?limit)\b',
            'http_methods': r'\b(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b',
            'status_codes': r'\b(?:200|201|400|401|403|404|500|502|503)\b',
            'data_formats': r'\b(?:JSON|XML|YAML|CSV|Base64|UTF-8|ASCII)\b',
            'protocols': r'\b(?:HTTP|HTTPS|TLS|SSL|TCP|UDP|WebSocket|gRPC)\b',
            'programming': r'\b(?:function|method|class|object|array|string|integer|boolean|null|undefined)\b',
            'database': r'\b(?:SQL|NoSQL|database|table|query|index|schema|migration)\b',
            'security': r'\b(?:encryption|hash|salt|certificate|private.?key|public.?key|signature)\b'
        }
        
        for section in sections:
            section_content = section.get('content', '')
            section_title = section.get('title', 'Unknown')
            section_slug = section.get('slug', 'unknown')
            
            for category, pattern in patterns.items():
                matches = re.finditer(pattern, section_content, re.IGNORECASE)
                
                for match in matches:
                    term = match.group().lower()
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(section_content), match.end() + 50)
                    context = section_content[context_start:context_end].strip()
                    
                    if term not in terms_index:
                        terms_index[term] = {
                            'term': term,
                            'category': category,
                            'frequency': 0,
                            'sections': [],
                            'contexts': []
                        }
                    
                    terms_index[term]['frequency'] += 1
                    
                    # Add section reference if not already present
                    section_ref = {
                        'title': section_title,
                        'slug': section_slug,
                        'occurrences': 1
                    }
                    
                    # Check if section already referenced
                    existing_section = None
                    for sect in terms_index[term]['sections']:
                        if sect['slug'] == section_slug:
                            existing_section = sect
                            break
                    
                    if existing_section:
                        existing_section['occurrences'] += 1
                    else:
                        terms_index[term]['sections'].append(section_ref)
                    
                    # Add context (limit to 3 most recent)
                    if len(terms_index[term]['contexts']) < 3:
                        terms_index[term]['contexts'].append({
                            'section': section_title,
                            'context': context,
                            'relevance': self.calculate_term_relevance(term, context)
                        })
        
        return terms_index
    
    def extract_endpoints_for_search(self, content, sections):
        """Extract API endpoints with detailed searchable information"""
        endpoints_index = {}
        
        # Enhanced endpoint patterns
        endpoint_patterns = [
            r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}.]+)',
            r'([/\w\-{}.]+)\s*-\s*(GET|POST|PUT|DELETE|PATCH)',
            r'endpoint[:\s]+([/\w\-{}.]+)',
            r'(https?://[^\s]+/[^\s]*)',
        ]
        
        for section in sections:
            section_content = section.get('content', '')
            section_title = section.get('title', 'Unknown')
            section_slug = section.get('slug', 'unknown')
            
            for pattern in endpoint_patterns:
                matches = re.finditer(pattern, section_content, re.IGNORECASE)
                
                for match in matches:
                    # Extract method and path
                    groups = match.groups()
                    if len(groups) >= 2:
                        method = groups[0] if groups[0] in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] else groups[1]
                        path = groups[1] if groups[0] in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] else groups[0]
                    else:
                        method = 'UNKNOWN'
                        path = groups[0]
                    
                    # Clean up path
                    path = path.strip('.,;')
                    if not path.startswith('/') and not path.startswith('http'):
                        continue
                    
                    endpoint_key = f"{method}:{path}"
                    
                    if endpoint_key not in endpoints_index:
                        endpoints_index[endpoint_key] = {
                            'method': method,
                            'path': path,
                            'full_endpoint': f"{method} {path}",
                            'sections': [],
                            'parameters': [],
                            'descriptions': [],
                            'examples': []
                        }
                    
                    # Add section reference
                    section_ref = {
                        'title': section_title,
                        'slug': section_slug,
                        'context': self.extract_endpoint_context(section_content, match.start(), match.end())
                    }
                    endpoints_index[endpoint_key]['sections'].append(section_ref)
                    
                    # Extract parameters from path
                    path_params = re.findall(r'\{([^}]+)\}', path)
                    for param in path_params:
                        if param not in endpoints_index[endpoint_key]['parameters']:
                            endpoints_index[endpoint_key]['parameters'].append({
                                'name': param,
                                'type': 'path',
                                'required': True
                            })
        
        return endpoints_index
    
    def extract_error_codes(self, content, sections):
        """Extract and categorize error codes with context"""
        error_codes_index = {}
        
        # Error code patterns
        error_patterns = {
            'http_status': r'\b(4\d{2}|5\d{2})\b',
            'error_messages': r'error[:\s]+"([^"]+)"',
            'exception_types': r'(\w+Error|\w+Exception)',
            'error_codes': r'error.?code[:\s]+(\w+)',
        }
        
        for section in sections:
            section_content = section.get('content', '')
            section_title = section.get('title', 'Unknown')
            section_slug = section.get('slug', 'unknown')
            
            for category, pattern in error_patterns.items():
                matches = re.finditer(pattern, section_content, re.IGNORECASE)
                
                for match in matches:
                    if category == 'error_messages':
                        error_code = match.group(1)
                    else:
                        error_code = match.group(1) if match.groups() else match.group()
                    
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(section_content), match.end() + 100)
                    context = section_content[context_start:context_end].strip()
                    
                    if error_code not in error_codes_index:
                        error_codes_index[error_code] = {
                            'code': error_code,
                            'category': category,
                            'frequency': 0,
                            'sections': [],
                            'descriptions': [],
                            'solutions': []
                        }
                    
                    error_codes_index[error_code]['frequency'] += 1
                    
                    # Add section reference
                    section_ref = {
                        'title': section_title,
                        'slug': section_slug,
                        'context': context
                    }
                    error_codes_index[error_code]['sections'].append(section_ref)
                    
                    # Extract description and solution if available
                    description = self.extract_error_description(section_content, match.start())
                    if description:
                        error_codes_index[error_code]['descriptions'].append(description)
        
        return error_codes_index
    
    def extract_key_concepts(self, content, sections):
        """Extract key technical concepts and their relationships"""
        concepts_index = {}
        
        # Concept extraction patterns
        concept_patterns = {
            'definitions': r'(\w+)\s+(?:is|means|refers to|defines?)\s+([^.!?]+[.!?])',
            'acronyms': r'\b([A-Z]{2,})\s*[-–]\s*([^.!?]+[.!?])',
            'technical_terms': r'\b(authentication|authorization|encryption|validation|serialization|deserialization)\b',
        }
        
        for section in sections:
            section_content = section.get('content', '')
            section_title = section.get('title', 'Unknown')
            section_slug = section.get('slug', 'unknown')
            
            # Extract concepts
            for category, pattern in concept_patterns.items():
                matches = re.finditer(pattern, section_content, re.IGNORECASE)
                
                for match in matches:
                    if category == 'definitions':
                        concept = match.group(1).lower()
                        definition = match.group(2).strip()
                    elif category == 'acronyms':
                        concept = match.group(1).lower()
                        definition = match.group(2).strip()
                    else:
                        concept = match.group().lower()
                        definition = self.extract_concept_context(section_content, match.start(), match.end())
                    
                    if concept not in concepts_index:
                        concepts_index[concept] = {
                            'concept': concept,
                            'category': category,
                            'definitions': [],
                            'sections': [],
                            'related_terms': []
                        }
                    
                    # Add definition if not already present
                    if definition and definition not in concepts_index[concept]['definitions']:
                        concepts_index[concept]['definitions'].append(definition)
                    
                    # Add section reference
                    section_ref = {
                        'title': section_title,
                        'slug': section_slug,
                        'relevance': self.calculate_concept_relevance(concept, section_content)
                    }
                    concepts_index[concept]['sections'].append(section_ref)
        
        # Find related terms
        for concept, data in concepts_index.items():
            data['related_terms'] = self.find_related_concepts(concept, concepts_index)
        
        return concepts_index
    
    def calculate_term_relevance(self, term, context):
        """Calculate relevance score for a term in context"""
        relevance_indicators = [
            'important', 'critical', 'required', 'necessary', 'essential',
            'note', 'warning', 'caution', 'example', 'see also'
        ]
        
        score = 1.0
        context_lower = context.lower()
        
        for indicator in relevance_indicators:
            if indicator in context_lower:
                score += 0.2
        
        # Boost score if term appears in section headers or emphasis
        if any(marker in context for marker in ['#', '**', '__']):
            score += 0.5
        
        return min(score, 3.0)  # Cap at 3.0
    
    def extract_endpoint_context(self, content, start, end):
        """Extract relevant context around an endpoint"""
        context_start = max(0, start - 200)
        context_end = min(len(content), end + 200)
        context = content[context_start:context_end].strip()
        
        # Look for description patterns
        desc_patterns = [
            r'(.*?)(GET|POST|PUT|DELETE|PATCH)',
            r'(GET|POST|PUT|DELETE|PATCH)(.*?)(\n|$)',
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, context, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group().strip()
        
        return context[:300] + '...' if len(context) > 300 else context
    
    def extract_error_description(self, content, error_position):
        """Extract description for an error code"""
        # Look for description in surrounding context
        context_start = max(0, error_position - 100)
        context_end = min(len(content), error_position + 300)
        context = content[context_start:context_end]
        
        # Look for common description patterns
        desc_patterns = [
            r'(.*?)(4\d{2}|5\d{2})(.*?)(\n|\.|$)',
            r'error[:\s]+"([^"]+)"',
            r'description[:\s]+([^.\n]+)',
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                description = match.group().strip()
                if len(description) > 10:  # Only meaningful descriptions
                    return description
        
        return None
    
    def extract_concept_context(self, content, start, end):
        """Extract context for a concept"""
        context_start = max(0, start - 50)
        context_end = min(len(content), end + 150)
        context = content[context_start:context_end].strip()
        
        # Clean up context
        sentences = re.split(r'[.!?]+', context)
        if len(sentences) > 1:
            return sentences[0] + '.'
        
        return context
    
    def calculate_concept_relevance(self, concept, content):
        """Calculate how relevant a concept is to a section"""
        concept_count = content.lower().count(concept.lower())
        content_length = len(content.split())
        
        if content_length == 0:
            return 0.0
        
        # Calculate frequency-based relevance
        frequency_score = (concept_count / content_length) * 1000
        
        # Boost if in title or headers
        if concept.lower() in content[:200].lower():
            frequency_score *= 2
        
        return round(frequency_score, 2)
    
    def find_related_concepts(self, target_concept, concepts_index):
        """Find concepts related to the target concept"""
        related = []
        target_sections = set(s['slug'] for s in concepts_index[target_concept]['sections'])
        
        for concept, data in concepts_index.items():
            if concept == target_concept:
                continue
            
            # Check for shared sections
            concept_sections = set(s['slug'] for s in data['sections'])
            overlap = len(target_sections.intersection(concept_sections))
            
            if overlap > 0:
                related.append({
                    'concept': concept,
                    'shared_sections': overlap,
                    'relationship_strength': round(overlap / len(target_sections), 2)
                })
        
        # Sort by relationship strength and return top 5
        related.sort(key=lambda x: x['relationship_strength'], reverse=True)
        return related[:5]
    
    def create_individual_indexes(self, index_dir, search_database):
        """Create individual index files for different search types"""
        
        # Terms index
        terms_file = index_dir / "terms-index.json"
        with open(terms_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'type': 'terms_index',
                    'total_terms': len(search_database['terms']),
                    'categories': list(set(t['category'] for t in search_database['terms'].values()))
                },
                'terms': search_database['terms']
            }, f, indent=2, ensure_ascii=False)
        
        # Endpoints index
        endpoints_file = index_dir / "endpoints-index.json"
        with open(endpoints_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'type': 'endpoints_index',
                    'total_endpoints': len(search_database['endpoints']),
                    'methods': list(set(e['method'] for e in search_database['endpoints'].values()))
                },
                'endpoints': search_database['endpoints']
            }, f, indent=2, ensure_ascii=False)
        
        # Error codes index
        errors_file = index_dir / "errors-index.json"
        with open(errors_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'type': 'errors_index',
                    'total_errors': len(search_database['error_codes']),
                    'categories': list(set(e['category'] for e in search_database['error_codes'].values()))
                },
                'error_codes': search_database['error_codes']
            }, f, indent=2, ensure_ascii=False)
        
        # Concepts index
        concepts_file = index_dir / "concepts-index.json"
        with open(concepts_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'type': 'concepts_index',
                    'total_concepts': len(search_database['concepts']),
                    'categories': list(set(c['category'] for c in search_database['concepts'].values()))
                },
                'concepts': search_database['concepts']
            }, f, indent=2, ensure_ascii=False)
    
    def create_search_documentation(self, index_dir, search_database):
        """Create comprehensive search documentation and examples"""
        doc_content = f"""# Search Index Documentation

Generated: {search_database['metadata']['generated_at']}

## Overview

This search index provides comprehensive searchable access to all content in the document, organized into four main categories:

- **Terms**: {search_database['metadata']['total_terms']} technical terms with frequency and context
- **Endpoints**: {search_database['metadata']['total_endpoints']} API endpoints with parameters and examples
- **Error Codes**: {search_database['metadata']['total_error_codes']} error codes with descriptions and solutions
- **Concepts**: {search_database['metadata']['total_concepts']} key concepts with definitions and relationships

## Index Files

### Main Database
- **`search-database.json`**: Complete search database with all categories
- **`terms-index.json`**: Technical terms with frequency analysis
- **`endpoints-index.json`**: API endpoints with detailed parameters
- **`errors-index.json`**: Error codes with context and solutions
- **`concepts-index.json`**: Key concepts with definitions and relationships

## Usage Examples

### Search Terms
```python
import json

# Load terms index
with open('search-index/terms-index.json') as f:
    terms_data = json.load(f)

# Find all authentication-related terms
auth_terms = {{
    term: data for term, data in terms_data['terms'].items() 
    if 'auth' in term or data['category'] == 'api_terms'
}}

# Get most frequent terms
frequent_terms = sorted(
    terms_data['terms'].items(), 
    key=lambda x: x[1]['frequency'], 
    reverse=True
)[:10]

# Find terms in specific sections
def find_terms_in_section(section_slug):
    results = []
    for term, data in terms_data['terms'].items():
        for section in data['sections']:
            if section['slug'] == section_slug:
                results.append((term, section['occurrences']))
    return sorted(results, key=lambda x: x[1], reverse=True)
```

### Search Endpoints
```python
# Load endpoints index
with open('search-index/endpoints-index.json') as f:
    endpoints_data = json.load(f)

# Find all POST endpoints
post_endpoints = {{
    key: data for key, data in endpoints_data['endpoints'].items()
    if data['method'] == 'POST'
}}

# Search for specific path patterns
user_endpoints = {{
    key: data for key, data in endpoints_data['endpoints'].items()
    if 'user' in data['path'].lower()
}}

# Get endpoints with parameters
parameterized_endpoints = {{
    key: data for key, data in endpoints_data['endpoints'].items()
    if data['parameters']
}}
```

### Search Error Codes
```python
# Load error codes index
with open('search-index/errors-index.json') as f:
    errors_data = json.load(f)

# Find HTTP status codes
http_errors = {{
    code: data for code, data in errors_data['error_codes'].items()
    if data['category'] == 'http_status'
}}

# Search for specific error types
auth_errors = {{
    code: data for code, data in errors_data['error_codes'].items()
    if any('auth' in desc.lower() for desc in data.get('descriptions', []))
}}

# Get most common errors
common_errors = sorted(
    errors_data['error_codes'].items(),
    key=lambda x: x[1]['frequency'],
    reverse=True
)[:5]
```

### Search Concepts
```python
# Load concepts index
with open('search-index/concepts-index.json') as f:
    concepts_data = json.load(f)

# Find concept definitions
def get_concept_definition(concept_name):
    concept = concepts_data['concepts'].get(concept_name.lower())
    if concept:
        return {{
            'definitions': concept['definitions'],
            'sections': concept['sections'],
            'related': concept['related_terms']
        }}
    return None

# Find related concepts
def find_related_concepts(concept_name):
    concept = concepts_data['concepts'].get(concept_name.lower())
    if concept:
        return concept['related_terms']
    return []

# Search concepts by category
security_concepts = {{
    name: data for name, data in concepts_data['concepts'].items()
    if any('security' in definition.lower() for definition in data.get('definitions', []))
}}
```

## Advanced Search Patterns

### Cross-Reference Search
```python
def find_cross_references(search_term):
    \"\"\"Find all references to a term across all indexes\"\"\"
    results = {{
        'terms': [],
        'endpoints': [],
        'errors': [],
        'concepts': []
    }}
    
    # Search in terms
    for term, data in terms_data['terms'].items():
        if search_term.lower() in term.lower():
            results['terms'].append((term, data))
    
    # Search in endpoints
    for key, data in endpoints_data['endpoints'].items():
        if search_term.lower() in data['path'].lower():
            results['endpoints'].append((key, data))
    
    # Search in error descriptions
    for code, data in errors_data['error_codes'].items():
        for desc in data.get('descriptions', []):
            if search_term.lower() in desc.lower():
                results['errors'].append((code, data))
                break
    
    # Search in concepts
    for concept, data in concepts_data['concepts'].items():
        if search_term.lower() in concept.lower():
            results['concepts'].append((concept, data))
    
    return results
```

### Relevance Scoring
```python
def search_with_relevance(query):
    \"\"\"Search with relevance scoring across all categories\"\"\"
    results = []
    query_lower = query.lower()
    
    # Score terms
    for term, data in terms_data['terms'].items():
        if query_lower in term:
            score = data['frequency'] * 2  # Frequency boost
            if query_lower == term:
                score *= 3  # Exact match boost
            results.append({{
                'type': 'term',
                'item': term,
                'score': score,
                'data': data
            }})
    
    # Score endpoints
    for key, data in endpoints_data['endpoints'].items():
        if query_lower in data['path'].lower():
            score = len(data['sections']) * 10  # Section count boost
            results.append({{
                'type': 'endpoint',
                'item': key,
                'score': score,
                'data': data
            }})
    
    # Sort by relevance
    return sorted(results, key=lambda x: x['score'], reverse=True)
```

## LLM Integration

### Query Processing
The search index is optimized for LLM queries with:
- **Structured JSON format** for easy parsing
- **Contextual information** for each item
- **Relevance scoring** for result ranking
- **Cross-references** for relationship discovery

### Use Cases
- **Documentation Search**: Find specific terms, endpoints, or concepts
- **Error Resolution**: Look up error codes with context and solutions
- **API Discovery**: Explore available endpoints and their parameters
- **Concept Learning**: Understand technical terms and their relationships
- **Content Analysis**: Analyze document structure and key topics

## Quality Metrics

### Coverage Analysis
"""

        # Add quality metrics
        total_items = (search_database['metadata']['total_terms'] + 
                      search_database['metadata']['total_endpoints'] + 
                      search_database['metadata']['total_error_codes'] + 
                      search_database['metadata']['total_concepts'])
        
        doc_content += f"""
- **Total Searchable Items**: {total_items}
- **Terms Coverage**: {search_database['metadata']['total_terms']} technical terms identified
- **API Coverage**: {search_database['metadata']['total_endpoints']} endpoints indexed
- **Error Coverage**: {search_database['metadata']['total_error_codes']} error codes cataloged
- **Concept Coverage**: {search_database['metadata']['total_concepts']} key concepts defined

### Index Statistics
- **Average term frequency**: {self.calculate_average_frequency(search_database['terms'])}
- **Endpoint methods**: {', '.join(set(e['method'] for e in search_database['endpoints'].values()))}
- **Error categories**: {', '.join(set(e['category'] for e in search_database['error_codes'].values()))}
- **Concept categories**: {', '.join(set(c['category'] for c in search_database['concepts'].values()))}

### Search Performance
- **Index size**: Optimized JSON format for fast queries
- **Memory usage**: Efficient structure for in-memory search
- **Query types**: Exact match, partial match, relevance-based
- **Response format**: Structured results with context and scoring
"""
        
        # Save documentation
        doc_file = index_dir / "README.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
    
    def calculate_average_frequency(self, terms_data):
        """Calculate average frequency across all terms"""
        if not terms_data:
            return 0
        frequencies = [data['frequency'] for data in terms_data.values()]
        return round(sum(frequencies) / len(frequencies), 1)
    
    def create_api_index(self, endpoint_files):
        """Create an index file listing all API endpoints"""
        index_content = f"""# API Endpoints Index

Generated: {datetime.now().isoformat()}
Total Endpoints: {len(endpoint_files)}

## Quick Reference

| Method | Path | Summary | File |
|--------|------|---------|------|
"""
        
        for endpoint in endpoint_files:
            summary = endpoint['summary'][:50] + '...' if len(endpoint['summary']) > 50 else endpoint['summary']
            index_content += f"| {endpoint['method']} | {endpoint['path']} | {summary} | [{endpoint['filename']}](api-endpoints/{endpoint['filename']}) |\n"
        
        index_content += f"""

## Usage for LLMs

Each endpoint file contains:
- Complete parameter documentation
- Request/response examples  
- Authentication requirements
- Source context for reference
- Token counts and processing guidance

### Processing Strategy
1. **Start with authentication endpoints** for API access setup
2. **Process core CRUD endpoints** for main functionality
3. **Handle specialized endpoints** based on use case
4. **Reference error codes** for debugging

### Batch Processing
- Group endpoints by authentication type
- Process related endpoints together (e.g., user management)
- Use token counts to optimize context windows

## Endpoint Categories
"""
        
        # Group by HTTP method
        methods = {}
        for endpoint in endpoint_files:
            method = endpoint['method']
            if method not in methods:
                methods[method] = []
            methods[method].append(endpoint)
        
        for method, endpoints in methods.items():
            index_content += f"\n### {method} Endpoints ({len(endpoints)})\n"
            for endpoint in endpoints:
                index_content += f"- [{endpoint['path']}](api-endpoints/{endpoint['filename']}) - {endpoint['summary']}\n"
        
        # Save index
        index_file = self.output_dir / "api-endpoints" / "README.md"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
    
    def create_metadata_summary(self, metadata):
        """Create a human-readable metadata summary"""
        summary = f"""# Document Metadata and LLM Compatibility Report

Generated: {metadata['generated']}
Source: {metadata['source_pdf']}

## Document Statistics

- **Total Sections**: {metadata['statistics']['total_sections']}
- **Total Tokens**: {metadata['statistics']['total_tokens']:,}
- **Total Words**: {metadata['statistics']['total_words']:,}
- **Tables Extracted**: {metadata['statistics']['tables_extracted']}
- **Images Extracted**: {metadata['statistics']['images_extracted']}

## Token Distribution

- Small sections (< 1K tokens): {metadata['token_distribution']['small']}
- Medium sections (1K-5K tokens): {metadata['token_distribution']['medium']}
- Large sections (5K-10K tokens): {metadata['token_distribution']['large']}
- Extra large sections (> 10K tokens): {metadata['token_distribution']['xlarge']}

## LLM Compatibility

### Overall Document
"""
        
        for compat in metadata['recommendations']['llm_compatibility_summary']:
            summary += f"- **{compat['model']}**: {compat['status']} ({compat['usage']})\n"
        
        summary += f"""

## Processing Recommendations

**Optimal Chunking Strategy**: {metadata['recommendations']['optimal_chunk_size']}

**Processing Strategies**:
"""
        
        for strategy in metadata['recommendations']['processing_strategy']:
            summary += f"- {strategy}\n"
        
        summary += """

## Section Details

| Section | Tokens | Words | LLM Fit |
| ------- | ------ | ----- | ------- |
"""
        
        for section in metadata['sections'][:10]:  # Show first 10 sections
            # Find best fitting model
            best_fit = "❌ Too large"
            for compat in section['llm_compatibility']:
                if "✅" in compat['status']:
                    best_fit = f"✅ {compat['model']}"
                    break
            
            summary += f"| {section.get('title', section['filename'][:30])} | {section['tokens']:,} | {section['words']:,} | {best_fit} |\n"
        
        if len(metadata['sections']) > 10:
            summary += f"\n*... and {len(metadata['sections']) - 10} more sections*\n"
        
        summary += """

## Usage Guide

1. **For GPT-3.5** (4K context): Process small sections individually
2. **For GPT-4** (8K-32K context): Can handle medium sections or combine small ones
3. **For Claude** (100K-200K context): Can process multiple large sections or entire document
4. **For embedding**: Each section is ready for vector database ingestion

---
*Use metadata.json for programmatic access to all metrics*
"""
        
        summary_file = self.output_dir / "llm-compatibility-report.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)

def main():
    parser = argparse.ArgumentParser(description='Convert PDF to Markdown')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('output_dir', help='Output directory')
    parser.add_argument('--preserve-tables', action='store_true', 
                      help='Preserve table formatting')
    parser.add_argument('--extract-images', action='store_true',
                      help='Extract and reference images')
    parser.add_argument('--enable-chunking', action='store_true', default=True,
                      help='Enable smart chunking by token limits (default: True)')
    parser.add_argument('--structured-tables', action='store_true', default=True,
                      help='Convert tables to structured JSON formats (default: True)')
    parser.add_argument('--build-search-index', action='store_true', default=True,
                      help='Build comprehensive search index with terms, endpoints, and error codes (default: True)')
    
    args = parser.parse_args()
    
    converter = PDFToMarkdownConverter(
        args.pdf_path,
        args.output_dir,
        args.preserve_tables,
        args.extract_images,
        args.enable_chunking,
        args.structured_tables,
        args.build_search_index
    )
    
    output_file = converter.convert()
    print(f"Conversion complete: {output_file}")

if __name__ == "__main__":
    main()
