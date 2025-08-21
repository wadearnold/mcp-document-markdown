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

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not available. Using approximation for token counting.", file=sys.stderr)

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
        self.save_and_organize_content(markdown_content)
        
        # Extract and create dedicated API endpoint files
        self.extract_api_endpoints_to_files(markdown_content)
        
        # Generate metadata file with statistics
        self.generate_metadata_file()
        
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
