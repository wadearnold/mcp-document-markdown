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
    def __init__(self, pdf_path, output_dir, preserve_tables=True, extract_images=True, enable_chunking=True, structured_tables=True, generate_concept_map=True, resolve_cross_references=True, generate_summaries=True):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.preserve_tables = preserve_tables
        self.extract_images = extract_images
        self.enable_chunking = enable_chunking
        self.structured_tables = structured_tables
        self.generate_concept_map = generate_concept_map
        self.resolve_cross_references = resolve_cross_references
        self.generate_summaries = generate_summaries
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
        
        # Generate concept map and glossary of technical terms
        if self.generate_concept_map:
            self.generate_concept_map_and_glossary(sections)
        
        # Resolve cross-references and convert to markdown links
        if self.resolve_cross_references:
            self.resolve_and_link_cross_references(sections)
        
        # Generate multi-level summaries for progressive disclosure
        if self.generate_summaries:
            self.generate_multi_level_summaries(sections, markdown_content)
        
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
    
    def generate_concept_map_and_glossary(self, sections):
        """Generate concept map and comprehensive glossary of technical terms"""
        # Create concepts directory
        concepts_dir = self.output_dir / "concepts"
        concepts_dir.mkdir(exist_ok=True)
        
        # Extract comprehensive term information
        terms_data = self.extract_comprehensive_terms(sections)
        concepts_data = self.extract_concept_definitions(sections)
        relationships = self.build_concept_relationships(terms_data, concepts_data, sections)
        
        # Generate concept map
        concept_map = self.create_concept_map(terms_data, concepts_data, relationships)
        
        # Generate comprehensive glossary
        glossary = self.create_comprehensive_glossary(terms_data, concepts_data)
        
        # Create visualization data for concept relationships
        visualization_data = self.create_concept_visualization_data(concept_map, relationships)
        
        # Save all concept files
        self.save_concept_files(concepts_dir, concept_map, glossary, visualization_data, terms_data)
        
        return len(terms_data) + len(concepts_data)
    
    def extract_comprehensive_terms(self, sections):
        """Extract comprehensive technical terms with enhanced context"""
        terms_data = {}
        
        # Enhanced technical term patterns with more categories
        term_patterns = {
            'api_concepts': r'\b(?:API|REST|GraphQL|endpoint|authentication|authorization|token|OAuth|JWT|CORS|rate.?limit|webhook|callback)\b',
            'http_concepts': r'\b(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|HTTP|HTTPS|request|response|header|body|status.?code)\b',
            'data_concepts': r'\b(?:JSON|XML|YAML|CSV|Base64|UTF-8|ASCII|schema|validation|serialization|deserialization|encoding)\b',
            'security_concepts': r'\b(?:encryption|hash|salt|certificate|private.?key|public.?key|signature|TLS|SSL|HMAC|RSA|AES)\b',
            'database_concepts': r'\b(?:SQL|NoSQL|database|table|query|index|schema|migration|transaction|ACID|relation)\b',
            'programming_concepts': r'\b(?:function|method|class|object|array|string|integer|boolean|null|undefined|variable|constant)\b',
            'network_concepts': r'\b(?:TCP|UDP|IP|DNS|URL|URI|WebSocket|gRPC|protocol|port|socket|proxy|firewall)\b',
            'architecture_concepts': r'\b(?:microservices|monolith|container|docker|kubernetes|serverless|cloud|scaling|load.?balancer)\b',
            'business_concepts': r'\b(?:user|customer|account|profile|permission|role|license|subscription|payment|billing)\b',
            'process_concepts': r'\b(?:workflow|pipeline|deployment|testing|debugging|monitoring|logging|analytics|metrics)\b'
        }
        
        for section in sections:
            section_content = section.get('content', '')
            section_title = section.get('title', 'Unknown')
            section_slug = section.get('slug', 'unknown')
            section_type = section.get('section_type', 'general')
            
            for category, pattern in term_patterns.items():
                matches = re.finditer(pattern, section_content, re.IGNORECASE)
                
                for match in matches:
                    term = match.group().lower().strip()
                    
                    # Extract enhanced context
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(section_content), match.end() + 100)
                    context = section_content[context_start:context_end].strip()
                    
                    # Extract definition if present
                    definition = self.extract_term_definition(section_content, match.start(), term)
                    
                    if term not in terms_data:
                        terms_data[term] = {
                            'term': term,
                            'category': category,
                            'frequency': 0,
                            'sections': [],
                            'contexts': [],
                            'definitions': [],
                            'section_types': set(),
                            'importance_score': 0,
                            'related_terms': set(),
                            'usage_patterns': []
                        }
                    
                    terms_data[term]['frequency'] += 1
                    terms_data[term]['section_types'].add(section_type)
                    
                    # Add section reference
                    section_ref = {
                        'title': section_title,
                        'slug': section_slug,
                        'section_type': section_type,
                        'occurrences': 1,
                        'context_snippet': context[:200] + '...' if len(context) > 200 else context
                    }
                    
                    # Check if section already referenced
                    existing_section = None
                    for sect in terms_data[term]['sections']:
                        if sect['slug'] == section_slug:
                            existing_section = sect
                            break
                    
                    if existing_section:
                        existing_section['occurrences'] += 1
                    else:
                        terms_data[term]['sections'].append(section_ref)
                    
                    # Add definition if found
                    if definition and definition not in terms_data[term]['definitions']:
                        terms_data[term]['definitions'].append(definition)
                    
                    # Add context (limit to 5 best contexts)
                    if len(terms_data[term]['contexts']) < 5:
                        relevance = self.calculate_enhanced_relevance(term, context, section_type)
                        terms_data[term]['contexts'].append({
                            'section': section_title,
                            'context': context,
                            'relevance': relevance,
                            'section_type': section_type
                        })
                    
                    # Extract related terms from context
                    related_terms = self.extract_related_terms_from_context(context, term, term_patterns)
                    terms_data[term]['related_terms'].update(related_terms)
        
        # Calculate importance scores and convert sets to lists
        for term, data in terms_data.items():
            data['importance_score'] = self.calculate_term_importance(data)
            data['section_types'] = list(data['section_types'])
            data['related_terms'] = list(data['related_terms'])
            
            # Sort contexts by relevance
            data['contexts'].sort(key=lambda x: x['relevance'], reverse=True)
        
        return terms_data
    
    def extract_concept_definitions(self, sections):
        """Extract explicit concept definitions and explanations"""
        concepts_data = {}
        
        # Patterns for finding definitions
        definition_patterns = [
            r'(\w+)\s+(?:is|means|refers to|defines?|represents?)\s+([^.!?]{10,200}[.!?])',
            r'(\w+):\s+([^.!?]{10,200}[.!?])',
            r'(\w+)\s*[-–]\s*([^.!?]{10,200}[.!?])',
            r'(?:define|definition of|meaning of)\s+(\w+)[:\s]+([^.!?]{10,200}[.!?])',
            r'\b([A-Z]{2,})\s*\(([^)]{10,100})\)',  # Acronyms with explanations
        ]
        
        for section in sections:
            section_content = section.get('content', '')
            section_title = section.get('title', 'Unknown')
            section_slug = section.get('slug', 'unknown')
            section_type = section.get('section_type', 'general')
            
            for pattern in definition_patterns:
                matches = re.finditer(pattern, section_content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    concept = match.group(1).lower().strip()
                    definition = match.group(2).strip()
                    
                    # Filter out very short or very generic terms
                    if len(concept) < 2 or concept in ['the', 'and', 'for', 'with', 'this', 'that']:
                        continue
                    
                    # Clean up definition
                    definition = re.sub(r'\s+', ' ', definition).strip()
                    
                    if concept not in concepts_data:
                        concepts_data[concept] = {
                            'concept': concept,
                            'definitions': [],
                            'sections': [],
                            'category': self.categorize_concept(concept, definition),
                            'complexity_score': 0,
                            'usage_frequency': 0,
                            'related_concepts': set(),
                            'examples': []
                        }
                    
                    # Add definition if not already present
                    if definition not in concepts_data[concept]['definitions']:
                        concepts_data[concept]['definitions'].append(definition)
                    
                    # Add section reference
                    section_ref = {
                        'title': section_title,
                        'slug': section_slug,
                        'section_type': section_type,
                        'definition_context': definition
                    }
                    concepts_data[concept]['sections'].append(section_ref)
                    
                    # Calculate complexity
                    concepts_data[concept]['complexity_score'] = self.calculate_concept_complexity(definition)
                    
                    # Extract examples if present
                    examples = self.extract_concept_examples(section_content, match.start(), concept)
                    concepts_data[concept]['examples'].extend(examples)
        
        # Convert sets to lists and calculate final scores
        for concept, data in concepts_data.items():
            data['related_concepts'] = list(data['related_concepts'])
            data['usage_frequency'] = len(data['sections'])
        
        return concepts_data
    
    def build_concept_relationships(self, terms_data, concepts_data, sections):
        """Build relationships between concepts and terms"""
        relationships = {
            'term_to_term': {},
            'concept_to_concept': {},
            'term_to_concept': {},
            'hierarchical': {},
            'semantic_clusters': {}
        }
        
        # Build term-to-term relationships based on co-occurrence
        for term1, data1 in terms_data.items():
            relationships['term_to_term'][term1] = []
            
            for term2, data2 in terms_data.items():
                if term1 == term2:
                    continue
                
                # Calculate relationship strength based on shared sections
                shared_sections = set(s['slug'] for s in data1['sections']) & set(s['slug'] for s in data2['sections'])
                
                if shared_sections:
                    relationship_strength = len(shared_sections) / max(len(data1['sections']), len(data2['sections']))
                    
                    if relationship_strength > 0.1:  # Threshold for meaningful relationship
                        relationships['term_to_term'][term1].append({
                            'related_term': term2,
                            'strength': round(relationship_strength, 3),
                            'shared_sections': len(shared_sections),
                            'relationship_type': self.determine_relationship_type(term1, term2, data1, data2)
                        })
            
            # Sort by strength
            relationships['term_to_term'][term1].sort(key=lambda x: x['strength'], reverse=True)
            relationships['term_to_term'][term1] = relationships['term_to_term'][term1][:10]  # Top 10
        
        # Build concept-to-concept relationships
        for concept1, data1 in concepts_data.items():
            relationships['concept_to_concept'][concept1] = []
            
            for concept2, data2 in concepts_data.items():
                if concept1 == concept2:
                    continue
                
                # Check for definitional relationships
                definition_similarity = self.calculate_definition_similarity(data1['definitions'], data2['definitions'])
                
                if definition_similarity > 0.2:
                    relationships['concept_to_concept'][concept1].append({
                        'related_concept': concept2,
                        'similarity': round(definition_similarity, 3),
                        'relationship_type': 'definitional'
                    })
        
        # Build term-to-concept relationships
        for term, term_data in terms_data.items():
            relationships['term_to_concept'][term] = []
            
            for concept, concept_data in concepts_data.items():
                # Check if term appears in concept definitions
                for definition in concept_data['definitions']:
                    if term in definition.lower():
                        relationships['term_to_concept'][term].append({
                            'concept': concept,
                            'relationship_type': 'definition_mention',
                            'context': definition
                        })
        
        # Create semantic clusters
        relationships['semantic_clusters'] = self.create_semantic_clusters(terms_data, concepts_data)
        
        return relationships
    
    def create_concept_map(self, terms_data, concepts_data, relationships):
        """Create a comprehensive concept map structure"""
        concept_map = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_terms': len(terms_data),
                'total_concepts': len(concepts_data),
                'total_relationships': sum(len(rels) for rels in relationships['term_to_term'].values())
            },
            'nodes': {},
            'edges': [],
            'clusters': relationships['semantic_clusters'],
            'hierarchy': self.build_concept_hierarchy(terms_data, concepts_data)
        }
        
        # Create nodes for terms
        for term, data in terms_data.items():
            concept_map['nodes'][term] = {
                'id': term,
                'type': 'term',
                'category': data['category'],
                'importance': data['importance_score'],
                'frequency': data['frequency'],
                'sections': len(data['sections']),
                'definitions': data['definitions'][:2],  # Top 2 definitions
                'section_types': data['section_types']
            }
        
        # Create nodes for concepts
        for concept, data in concepts_data.items():
            concept_map['nodes'][concept] = {
                'id': concept,
                'type': 'concept',
                'category': data['category'],
                'complexity': data['complexity_score'],
                'frequency': data['usage_frequency'],
                'definitions': data['definitions'][:1],  # Primary definition
                'examples': data['examples'][:3]  # Top 3 examples
            }
        
        # Create edges for relationships
        edge_id = 0
        for source_term, relationships_list in relationships['term_to_term'].items():
            for rel in relationships_list:
                concept_map['edges'].append({
                    'id': edge_id,
                    'source': source_term,
                    'target': rel['related_term'],
                    'weight': rel['strength'],
                    'type': rel['relationship_type'],
                    'shared_sections': rel['shared_sections']
                })
                edge_id += 1
        
        return concept_map
    
    def create_comprehensive_glossary(self, terms_data, concepts_data):
        """Create a comprehensive glossary with categorized terms"""
        glossary = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_entries': len(terms_data) + len(concepts_data),
                'categories': list(set(data['category'] for data in terms_data.values()))
            },
            'terms': {},
            'concepts': {},
            'categories': {}
        }
        
        # Organize terms by category
        for category in glossary['metadata']['categories']:
            glossary['categories'][category] = {
                'terms': [],
                'description': self.get_category_description(category),
                'importance': self.calculate_category_importance(category, terms_data)
            }
        
        # Add terms to glossary
        for term, data in terms_data.items():
            glossary_entry = {
                'term': term,
                'category': data['category'],
                'frequency': data['frequency'],
                'importance': data['importance_score'],
                'definitions': data['definitions'],
                'primary_definition': data['definitions'][0] if data['definitions'] else self.generate_contextual_definition(term, data),
                'usage_contexts': [ctx['context'][:150] + '...' for ctx in data['contexts'][:3]],
                'appears_in_sections': [s['title'] for s in data['sections'][:5]],
                'section_types': data['section_types'],
                'related_terms': data['related_terms'][:10],
                'examples': self.extract_usage_examples(term, data['contexts'])
            }
            
            glossary['terms'][term] = glossary_entry
            glossary['categories'][data['category']]['terms'].append(term)
        
        # Add concepts to glossary
        for concept, data in concepts_data.items():
            glossary['concepts'][concept] = {
                'concept': concept,
                'category': data['category'],
                'complexity': data['complexity_score'],
                'definitions': data['definitions'],
                'primary_definition': data['definitions'][0] if data['definitions'] else '',
                'examples': data['examples'],
                'appears_in_sections': [s['title'] for s in data['sections']],
                'related_concepts': data['related_concepts']
            }
        
        # Sort categories by importance
        glossary['categories'] = dict(sorted(
            glossary['categories'].items(), 
            key=lambda x: x[1]['importance'], 
            reverse=True
        ))
        
        return glossary
    
    def create_concept_visualization_data(self, concept_map, relationships):
        """Create data structure optimized for visualization tools"""
        visualization = {
            'graph_data': {
                'nodes': [],
                'links': []
            },
            'hierarchy_data': concept_map['hierarchy'],
            'cluster_data': concept_map['clusters'],
            'statistics': {
                'node_count': len(concept_map['nodes']),
                'edge_count': len(concept_map['edges']),
                'cluster_count': len(concept_map['clusters']),
                'max_connections': 0,
                'avg_connections': 0
            }
        }
        
        # Convert nodes for visualization
        for node_id, node_data in concept_map['nodes'].items():
            vis_node = {
                'id': node_id,
                'label': node_id,
                'type': node_data['type'],
                'category': node_data['category'],
                'size': min(node_data.get('frequency', 1) * 10, 100),  # Scale size
                'color': self.get_category_color(node_data['category']),
                'importance': node_data.get('importance', 0),
                'tooltip': self.create_node_tooltip(node_data)
            }
            visualization['graph_data']['nodes'].append(vis_node)
        
        # Convert edges for visualization
        for edge in concept_map['edges']:
            vis_edge = {
                'source': edge['source'],
                'target': edge['target'],
                'weight': edge['weight'],
                'type': edge['type'],
                'thickness': min(edge['weight'] * 10, 5)  # Scale thickness
            }
            visualization['graph_data']['links'].append(vis_edge)
        
        # Calculate statistics
        connection_counts = {}
        for edge in concept_map['edges']:
            connection_counts[edge['source']] = connection_counts.get(edge['source'], 0) + 1
            connection_counts[edge['target']] = connection_counts.get(edge['target'], 0) + 1
        
        if connection_counts:
            visualization['statistics']['max_connections'] = max(connection_counts.values())
            visualization['statistics']['avg_connections'] = round(sum(connection_counts.values()) / len(connection_counts), 2)
        
        return visualization
    
    def save_concept_files(self, concepts_dir, concept_map, glossary, visualization_data, terms_data):
        """Save all concept-related files"""
        
        # Save concept map JSON
        concept_map_file = concepts_dir / "concept-map.json"
        with open(concept_map_file, 'w', encoding='utf-8') as f:
            json.dump(concept_map, f, indent=2, ensure_ascii=False)
        
        # Save glossary JSON
        glossary_file = concepts_dir / "glossary.json"
        with open(glossary_file, 'w', encoding='utf-8') as f:
            json.dump(glossary, f, indent=2, ensure_ascii=False)
        
        # Save visualization data
        viz_file = concepts_dir / "visualization-data.json"
        with open(viz_file, 'w', encoding='utf-8') as f:
            json.dump(visualization_data, f, indent=2, ensure_ascii=False)
        
        # Create human-readable glossary markdown
        self.create_glossary_markdown(concepts_dir, glossary)
        
        # Create concept map documentation
        self.create_concept_map_documentation(concepts_dir, concept_map, visualization_data)
        
        # Create category-specific glossaries
        self.create_category_glossaries(concepts_dir, glossary)
    
    # Helper methods for concept map generation
    def extract_term_definition(self, content, position, term):
        """Extract definition for a term from surrounding context"""
        # Look for definition patterns around the term
        context_start = max(0, position - 200)
        context_end = min(len(content), position + 300)
        context = content[context_start:context_end]
        
        # Definition patterns
        patterns = [
            rf'{re.escape(term)}\s+(?:is|means|refers to)\s+([^.!?]+[.!?])',
            rf'{re.escape(term)}:\s+([^.!?]+[.!?])',
            rf'{re.escape(term)}\s*[-–]\s*([^.!?]+[.!?])'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def calculate_enhanced_relevance(self, term, context, section_type):
        """Calculate enhanced relevance score"""
        base_score = 1.0
        
        # Section type bonus
        section_bonuses = {
            'authentication': 1.5,
            'api_endpoint': 1.3,
            'security': 1.4,
            'error_handling': 1.2
        }
        base_score *= section_bonuses.get(section_type, 1.0)
        
        # Context indicators
        indicators = ['important', 'critical', 'key', 'main', 'primary', 'essential']
        for indicator in indicators:
            if indicator in context.lower():
                base_score += 0.3
        
        # Definition indicators
        if any(pattern in context.lower() for pattern in [f'{term} is', f'{term} means', f'{term}:']):
            base_score += 0.5
        
        return min(base_score, 3.0)
    
    def extract_related_terms_from_context(self, context, main_term, term_patterns):
        """Extract related terms from context"""
        related_terms = set()
        
        for category, pattern in term_patterns.items():
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                term = match.group().lower().strip()
                if term != main_term and len(term) > 2:
                    related_terms.add(term)
        
        return related_terms
    
    def calculate_term_importance(self, term_data):
        """Calculate importance score for a term"""
        frequency_score = min(term_data['frequency'] / 10.0, 2.0)
        section_diversity = len(term_data['section_types']) * 0.5
        definition_bonus = 1.0 if term_data['definitions'] else 0.0
        
        return round(frequency_score + section_diversity + definition_bonus, 2)
    
    def categorize_concept(self, concept, definition):
        """Categorize a concept based on its definition"""
        definition_lower = definition.lower()
        
        if any(word in definition_lower for word in ['api', 'endpoint', 'request', 'response']):
            return 'api_concepts'
        elif any(word in definition_lower for word in ['security', 'encrypt', 'auth', 'credential']):
            return 'security_concepts'
        elif any(word in definition_lower for word in ['data', 'format', 'structure', 'schema']):
            return 'data_concepts'
        elif any(word in definition_lower for word in ['network', 'protocol', 'connection']):
            return 'network_concepts'
        else:
            return 'general_concepts'
    
    def calculate_concept_complexity(self, definition):
        """Calculate complexity score based on definition"""
        word_count = len(definition.split())
        technical_terms = len(re.findall(r'\b(?:API|HTTP|JSON|authentication|encryption|protocol)\b', definition, re.IGNORECASE))
        
        return round((word_count / 20.0) + (technical_terms * 0.5), 2)
    
    def extract_concept_examples(self, content, position, concept):
        """Extract examples for a concept"""
        # Look for example patterns
        context_start = max(0, position - 100)
        context_end = min(len(content), position + 500)
        context = content[context_start:context_end]
        
        example_patterns = [
            r'(?:for example|e\.g\.|such as)[:\s]+([^.!?]+[.!?])',
            r'example[:\s]+([^.!?]+[.!?])',
            r'like[:\s]+([^.!?]+[.!?])'
        ]
        
        examples = []
        for pattern in example_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                example = match.group(1).strip()
                if len(example) > 10:
                    examples.append(example)
        
        return examples[:3]  # Return top 3 examples
    
    def determine_relationship_type(self, term1, term2, data1, data2):
        """Determine the type of relationship between two terms"""
        if data1['category'] == data2['category']:
            return 'categorical'
        elif term2 in data1['related_terms'] or term1 in data2['related_terms']:
            return 'semantic'
        else:
            return 'contextual'
    
    def calculate_definition_similarity(self, definitions1, definitions2):
        """Calculate similarity between sets of definitions"""
        if not definitions1 or not definitions2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(' '.join(definitions1).lower().split())
        words2 = set(' '.join(definitions2).lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def create_semantic_clusters(self, terms_data, concepts_data):
        """Create semantic clusters of related terms"""
        clusters = {}
        
        # Group by category first
        for term, data in terms_data.items():
            category = data['category']
            if category not in clusters:
                clusters[category] = {
                    'cluster_id': category,
                    'terms': [],
                    'concepts': [],
                    'description': self.get_category_description(category),
                    'size': 0
                }
            
            clusters[category]['terms'].append({
                'term': term,
                'importance': data['importance_score'],
                'frequency': data['frequency']
            })
        
        # Add concepts to clusters
        for concept, data in concepts_data.items():
            category = data['category']
            if category in clusters:
                clusters[category]['concepts'].append({
                    'concept': concept,
                    'complexity': data['complexity_score']
                })
        
        # Calculate cluster sizes and sort
        for cluster_id, cluster in clusters.items():
            cluster['size'] = len(cluster['terms']) + len(cluster['concepts'])
            cluster['terms'].sort(key=lambda x: x['importance'], reverse=True)
            cluster['concepts'].sort(key=lambda x: x['complexity'], reverse=True)
        
        return clusters
    
    def build_concept_hierarchy(self, terms_data, concepts_data):
        """Build hierarchical structure of concepts"""
        hierarchy = {
            'root': {
                'name': 'Technical Documentation',
                'children': []
            }
        }
        
        # Create category-based hierarchy
        categories = set(data['category'] for data in terms_data.values())
        
        for category in categories:
            category_node = {
                'name': self.get_category_display_name(category),
                'type': 'category',
                'children': []
            }
            
            # Add important terms to category
            category_terms = [(term, data) for term, data in terms_data.items() if data['category'] == category]
            category_terms.sort(key=lambda x: x[1]['importance_score'], reverse=True)
            
            for term, data in category_terms[:10]:  # Top 10 terms per category
                term_node = {
                    'name': term,
                    'type': 'term',
                    'importance': data['importance_score'],
                    'frequency': data['frequency']
                }
                category_node['children'].append(term_node)
            
            hierarchy['root']['children'].append(category_node)
        
        return hierarchy
    
    def get_category_description(self, category):
        """Get description for a category"""
        descriptions = {
            'api_concepts': 'Application Programming Interface related terms and concepts',
            'http_concepts': 'HTTP protocol and web communication terms',
            'data_concepts': 'Data formats, structures, and processing terms',
            'security_concepts': 'Security, authentication, and encryption terms',
            'database_concepts': 'Database and data storage related terms',
            'programming_concepts': 'General programming and development terms',
            'network_concepts': 'Networking and communication protocol terms',
            'architecture_concepts': 'System architecture and design pattern terms',
            'business_concepts': 'Business logic and domain-specific terms',
            'process_concepts': 'Development processes and workflow terms'
        }
        return descriptions.get(category, 'General technical terms')
    
    def calculate_category_importance(self, category, terms_data):
        """Calculate importance score for a category"""
        category_terms = [data for data in terms_data.values() if data['category'] == category]
        if not category_terms:
            return 0.0
        
        total_frequency = sum(data['frequency'] for data in category_terms)
        avg_importance = sum(data['importance_score'] for data in category_terms) / len(category_terms)
        
        return round((total_frequency * 0.1) + avg_importance, 2)
    
    def generate_contextual_definition(self, term, term_data):
        """Generate a contextual definition based on usage"""
        if not term_data['contexts']:
            return f"Technical term appearing {term_data['frequency']} times in documentation"
        
        best_context = term_data['contexts'][0]['context']
        # Extract a sentence containing the term
        sentences = re.split(r'[.!?]+', best_context)
        for sentence in sentences:
            if term in sentence.lower():
                return sentence.strip() + '.'
        
        return f"Technical term in {term_data['category'].replace('_', ' ')} domain"
    
    def extract_usage_examples(self, term, contexts):
        """Extract usage examples from contexts"""
        examples = []
        for context_data in contexts[:3]:
            context = context_data['context']
            # Find sentences containing the term
            sentences = re.split(r'[.!?]+', context)
            for sentence in sentences:
                if term in sentence.lower() and len(sentence.strip()) > 20:
                    examples.append(sentence.strip() + '.')
                    break
        return examples
    
    def get_category_color(self, category):
        """Get color code for category visualization"""
        colors = {
            'api_concepts': '#FF6B6B',
            'http_concepts': '#4ECDC4',
            'data_concepts': '#45B7D1',
            'security_concepts': '#F9CA24',
            'database_concepts': '#6C5CE7',
            'programming_concepts': '#A0E7E5',
            'network_concepts': '#FFA726',
            'architecture_concepts': '#26A69A',
            'business_concepts': '#EF5350',
            'process_concepts': '#66BB6A'
        }
        return colors.get(category, '#95A5A6')
    
    def get_category_display_name(self, category):
        """Get display name for category"""
        display_names = {
            'api_concepts': 'API Concepts',
            'http_concepts': 'HTTP & Web',
            'data_concepts': 'Data & Formats',
            'security_concepts': 'Security',
            'database_concepts': 'Database',
            'programming_concepts': 'Programming',
            'network_concepts': 'Networking',
            'architecture_concepts': 'Architecture',
            'business_concepts': 'Business Logic',
            'process_concepts': 'Processes'
        }
        return display_names.get(category, category.replace('_', ' ').title())
    
    def create_node_tooltip(self, node_data):
        """Create tooltip text for visualization nodes"""
        if node_data['type'] == 'term':
            return f"Term: {node_data.get('id', '')}\nFrequency: {node_data.get('frequency', 0)}\nImportance: {node_data.get('importance', 0)}\nCategory: {node_data.get('category', '')}"
        else:
            return f"Concept: {node_data.get('id', '')}\nComplexity: {node_data.get('complexity', 0)}\nCategory: {node_data.get('category', '')}"
    
    def create_glossary_markdown(self, concepts_dir, glossary):
        """Create human-readable glossary in markdown format"""
        glossary_content = f"""# Technical Glossary

Generated: {datetime.now().isoformat()}
Total Terms: {len(glossary['terms'])}
Total Concepts: {len(glossary['concepts'])}

## Overview

This glossary contains technical terms and concepts extracted from the document, organized by category and importance. Terms are ranked by frequency and relevance to help LLMs understand the technical vocabulary used throughout the document.

## Quick Statistics

- **Most Common Category**: {glossary['statistics']['most_common_category']}
- **Average Term Frequency**: {glossary['statistics']['avg_term_frequency']:.1f}
- **High-Importance Terms**: {glossary['statistics']['high_importance_count']}
- **Concepts with Definitions**: {len([c for c in glossary['concepts'].values() if c['definitions']])}

## All Terms by Category

"""
        
        # Group terms by category
        terms_by_category = {}
        for term_data in glossary['terms'].values():
            category = term_data['category']
            if category not in terms_by_category:
                terms_by_category[category] = []
            terms_by_category[category].append(term_data)
        
        # Sort categories by number of terms
        sorted_categories = sorted(terms_by_category.items(), key=lambda x: len(x[1]), reverse=True)
        
        for category, terms in sorted_categories:
            category_name = category.replace('_', ' ').title()
            glossary_content += f"### {category_name} ({len(terms)} terms)\n\n"
            
            # Sort terms by importance score
            sorted_terms = sorted(terms, key=lambda x: x['importance_score'], reverse=True)
            
            for term_data in sorted_terms:
                term = term_data['term']
                freq = term_data['frequency']
                importance = term_data['importance_score']
                
                glossary_content += f"**{term.upper()}** (freq: {freq}, importance: {importance:.1f})\n"
                
                # Add definitions if available
                if term_data['definitions']:
                    for definition in term_data['definitions'][:2]:  # Limit to 2 best definitions
                        glossary_content += f"  - {definition}\n"
                
                # Add best context
                if term_data['contexts']:
                    best_context = term_data['contexts'][0]
                    context_snippet = best_context['context'][:150] + '...' if len(best_context['context']) > 150 else best_context['context']
                    glossary_content += f"  - *Context*: {context_snippet}\n"
                
                # Add related terms
                if term_data['related_terms']:
                    related = ', '.join(term_data['related_terms'][:5])
                    glossary_content += f"  - *Related*: {related}\n"
                
                glossary_content += "\n"
        
        # Add concepts section
        if glossary['concepts']:
            glossary_content += "## Detailed Concepts\n\n"
            
            # Sort concepts by complexity and usage
            sorted_concepts = sorted(glossary['concepts'].values(), 
                                   key=lambda x: (x['complexity_score'], len(x['definitions'])), 
                                   reverse=True)
            
            for concept_data in sorted_concepts:
                concept = concept_data['concept']
                category = concept_data['category']
                complexity = concept_data['complexity_score']
                
                glossary_content += f"### {concept.upper()}\n"
                glossary_content += f"*Category*: {category.replace('_', ' ').title()} | *Complexity*: {complexity:.1f}\n\n"
                
                # Add all definitions
                for i, definition in enumerate(concept_data['definitions'], 1):
                    glossary_content += f"{i}. {definition}\n"
                
                # Add examples
                if concept_data['examples']:
                    glossary_content += "\n**Examples:**\n"
                    for example in concept_data['examples'][:3]:
                        glossary_content += f"- {example}\n"
                
                # Add section references
                if concept_data['sections']:
                    section_titles = [s['title'] for s in concept_data['sections'][:3]]
                    glossary_content += f"\n*Found in sections*: {', '.join(section_titles)}\n"
                
                glossary_content += "\n"
        
        # Save glossary
        glossary_path = concepts_dir / "glossary.md"
        with open(glossary_path, 'w', encoding='utf-8') as f:
            f.write(glossary_content)
        
        return str(glossary_path)
    
    def create_concept_map_documentation(self, concepts_dir, concept_map, visualization_data):
        """Create documentation for the concept map"""
        # Create concept map overview
        map_content = f"""# Concept Map Documentation

Generated: {datetime.now().isoformat()}
Total Nodes: {len(visualization_data['nodes'])}
Total Relationships: {len(visualization_data['edges'])}

## Overview

This concept map visualizes the relationships between technical terms and concepts found in the document. It helps LLMs understand how different technical concepts are interconnected and provides a semantic network for better comprehension.

## Network Statistics

- **Total Terms**: {len([n for n in visualization_data['nodes'] if n['type'] == 'term'])}
- **Total Concepts**: {len([n for n in visualization_data['nodes'] if n['type'] == 'concept'])}
- **Total Relationships**: {len(visualization_data['edges'])}
- **Most Connected Node**: {max(visualization_data['nodes'], key=lambda x: x.get('connection_count', 0))['id']}
- **Average Connections per Node**: {sum(n.get('connection_count', 0) for n in visualization_data['nodes']) / len(visualization_data['nodes']):.1f}

## Core Concept Clusters

"""
        
        # Group nodes by category and importance
        clusters = {}
        for node in visualization_data['nodes']:
            category = node.get('category', 'general')
            if category not in clusters:
                clusters[category] = {'terms': [], 'concepts': []}
            
            if node['type'] == 'term':
                clusters[category]['terms'].append(node)
            else:
                clusters[category]['concepts'].append(node)
        
        # Sort clusters by total node count
        sorted_clusters = sorted(clusters.items(), 
                               key=lambda x: len(x[1]['terms']) + len(x[1]['concepts']), 
                               reverse=True)
        
        for category, cluster_data in sorted_clusters:
            category_name = category.replace('_', ' ').title()
            total_nodes = len(cluster_data['terms']) + len(cluster_data['concepts'])
            map_content += f"### {category_name} ({total_nodes} nodes)\n\n"
            
            # Most important terms in cluster
            if cluster_data['terms']:
                sorted_terms = sorted(cluster_data['terms'], key=lambda x: x.get('importance', 0), reverse=True)
                top_terms = [t['id'] for t in sorted_terms[:5]]
                map_content += f"**Key Terms**: {', '.join(top_terms)}\n\n"
            
            # Most important concepts in cluster
            if cluster_data['concepts']:
                sorted_concepts = sorted(cluster_data['concepts'], key=lambda x: x.get('complexity', 0), reverse=True)
                top_concepts = [c['id'] for c in sorted_concepts[:3]]
                map_content += f"**Key Concepts**: {', '.join(top_concepts)}\n\n"
        
        # Add relationship analysis
        map_content += "## Relationship Analysis\n\n"
        
        # Group relationships by type
        relationship_types = {}
        for edge in visualization_data['edges']:
            rel_type = edge.get('relationship_type', 'related')
            if rel_type not in relationship_types:
                relationship_types[rel_type] = []
            relationship_types[rel_type].append(edge)
        
        for rel_type, edges in relationship_types.items():
            map_content += f"**{rel_type.replace('_', ' ').title()}** ({len(edges)} connections)\n"
            
            # Show strongest relationships
            sorted_edges = sorted(edges, key=lambda x: x.get('strength', 0), reverse=True)
            for edge in sorted_edges[:5]:
                source = edge['source']
                target = edge['target']
                strength = edge.get('strength', 0)
                map_content += f"  - {source} → {target} (strength: {strength:.2f})\n"
            map_content += "\n"
        
        # Add network topology insights
        map_content += "## Network Topology\n\n"
        
        # Find hub nodes (high connection count)
        hub_nodes = sorted(visualization_data['nodes'], key=lambda x: x.get('connection_count', 0), reverse=True)[:10]
        map_content += "**Hub Nodes** (most connected):\n"
        for i, node in enumerate(hub_nodes, 1):
            connections = node.get('connection_count', 0)
            node_type = node['type'].title()
            map_content += f"{i}. {node['id']} ({node_type}, {connections} connections)\n"
        map_content += "\n"
        
        # Find bridge concepts (connecting different categories)
        bridge_concepts = []
        for node in visualization_data['nodes']:
            connected_categories = set()
            node_id = node['id']
            
            for edge in visualization_data['edges']:
                if edge['source'] == node_id:
                    target_node = next((n for n in visualization_data['nodes'] if n['id'] == edge['target']), None)
                    if target_node:
                        connected_categories.add(target_node.get('category', 'general'))
                elif edge['target'] == node_id:
                    source_node = next((n for n in visualization_data['nodes'] if n['id'] == edge['source']), None)
                    if source_node:
                        connected_categories.add(source_node.get('category', 'general'))
            
            if len(connected_categories) > 2:
                bridge_concepts.append((node, len(connected_categories)))
        
        if bridge_concepts:
            bridge_concepts.sort(key=lambda x: x[1], reverse=True)
            map_content += "**Bridge Concepts** (connecting multiple categories):\n"
            for node, category_count in bridge_concepts[:5]:
                map_content += f"- {node['id']} (connects {category_count} categories)\n"
        
        # Save concept map documentation
        map_path = concepts_dir / "concept_map.md"
        with open(map_path, 'w', encoding='utf-8') as f:
            f.write(map_content)
        
        return str(map_path)
    
    def create_category_glossaries(self, concepts_dir, glossary):
        """Create separate glossaries for each category"""
        category_files = []
        
        # Create categories directory
        categories_dir = concepts_dir / "categories"
        categories_dir.mkdir(exist_ok=True)
        
        # Group terms by category
        terms_by_category = {}
        for term_data in glossary['terms'].values():
            category = term_data['category']
            if category not in terms_by_category:
                terms_by_category[category] = []
            terms_by_category[category].append(term_data)
        
        # Group concepts by category
        concepts_by_category = {}
        for concept_data in glossary['concepts'].values():
            category = concept_data['category']
            if category not in concepts_by_category:
                concepts_by_category[category] = []
            concepts_by_category[category].append(concept_data)
        
        # Get all categories
        all_categories = set(terms_by_category.keys()) | set(concepts_by_category.keys())
        
        for category in all_categories:
            category_name = category.replace('_', ' ').title()
            category_terms = terms_by_category.get(category, [])
            category_concepts = concepts_by_category.get(category, [])
            
            category_content = f"""# {category_name} Glossary

Generated: {datetime.now().isoformat()}
Terms: {len(category_terms)}
Concepts: {len(category_concepts)}

## Category Overview

This glossary focuses specifically on {category_name.lower()} terms and concepts found in the document. This specialized vocabulary is essential for understanding the {category_name.lower()}-related content and context.

"""
            
            # Add terms section
            if category_terms:
                category_content += f"## Terms ({len(category_terms)})\n\n"
                
                # Sort terms by importance
                sorted_terms = sorted(category_terms, key=lambda x: x['importance_score'], reverse=True)
                
                for term_data in sorted_terms:
                    term = term_data['term']
                    freq = term_data['frequency']
                    importance = term_data['importance_score']
                    
                    category_content += f"### {term.upper()}\n"
                    category_content += f"*Frequency*: {freq} | *Importance*: {importance:.1f}\n\n"
                    
                    # Add definitions
                    if term_data['definitions']:
                        category_content += "**Definitions:**\n"
                        for definition in term_data['definitions']:
                            category_content += f"- {definition}\n"
                        category_content += "\n"
                    
                    # Add contexts
                    if term_data['contexts']:
                        category_content += "**Usage Contexts:**\n"
                        for context in term_data['contexts'][:3]:
                            snippet = context['context'][:200] + '...' if len(context['context']) > 200 else context['context']
                            category_content += f"- *{context['section']}*: {snippet}\n"
                        category_content += "\n"
                    
                    # Add related terms
                    if term_data['related_terms']:
                        related_in_category = [rt for rt in term_data['related_terms'] 
                                             if any(t['term'] == rt for t in category_terms)]
                        if related_in_category:
                            category_content += f"**Related in this category**: {', '.join(related_in_category)}\n\n"
                    
                    # Add section references
                    if term_data['sections']:
                        section_refs = [f"[{s['title']}](#{s['slug']})" for s in term_data['sections'][:3]]
                        category_content += f"**Found in**: {', '.join(section_refs)}\n\n"
                    
                    category_content += "---\n\n"
            
            # Add concepts section
            if category_concepts:
                category_content += f"## Detailed Concepts ({len(category_concepts)})\n\n"
                
                # Sort concepts by complexity
                sorted_concepts = sorted(category_concepts, key=lambda x: x['complexity_score'], reverse=True)
                
                for concept_data in sorted_concepts:
                    concept = concept_data['concept']
                    complexity = concept_data['complexity_score']
                    
                    category_content += f"### {concept.upper()}\n"
                    category_content += f"*Complexity Score*: {complexity:.1f}\n\n"
                    
                    # Add all definitions
                    if concept_data['definitions']:
                        category_content += "**Definitions:**\n"
                        for i, definition in enumerate(concept_data['definitions'], 1):
                            category_content += f"{i}. {definition}\n"
                        category_content += "\n"
                    
                    # Add examples
                    if concept_data['examples']:
                        category_content += "**Examples:**\n"
                        for example in concept_data['examples']:
                            category_content += f"- {example}\n"
                        category_content += "\n"
                    
                    # Add section references
                    if concept_data['sections']:
                        category_content += "**Detailed in sections:**\n"
                        for section in concept_data['sections']:
                            category_content += f"- *{section['title']}*: {section['definition_context'][:150]}...\n"
                        category_content += "\n"
                    
                    category_content += "---\n\n"
            
            # Add category summary
            category_content += f"## Category Summary\n\n"
            category_content += f"This {category_name.lower()} glossary contains {len(category_terms)} terms and {len(category_concepts)} detailed concepts. "
            
            if category_terms:
                avg_importance = sum(t['importance_score'] for t in category_terms) / len(category_terms)
                high_importance_count = len([t for t in category_terms if t['importance_score'] > avg_importance])
                category_content += f"The average term importance is {avg_importance:.1f}, with {high_importance_count} high-importance terms. "
            
            if category_concepts:
                avg_complexity = sum(c['complexity_score'] for c in category_concepts) / len(category_concepts)
                category_content += f"The average concept complexity is {avg_complexity:.1f}. "
            
            category_content += f"This specialized vocabulary is crucial for understanding {category_name.lower()}-specific content in the document.\n"
            
            # Save category glossary
            safe_category_name = category.replace('_', '-').lower()
            category_path = categories_dir / f"{safe_category_name}-glossary.md"
            with open(category_path, 'w', encoding='utf-8') as f:
                f.write(category_content)
            
            category_files.append(str(category_path))
        
        # Create category index
        index_content = f"""# Category Glossaries Index

Generated: {datetime.now().isoformat()}
Total Categories: {len(all_categories)}

## Available Category Glossaries

"""
        
        for category in sorted(all_categories):
            category_name = category.replace('_', ' ').title()
            safe_category_name = category.replace('_', '-').lower()
            term_count = len(terms_by_category.get(category, []))
            concept_count = len(concepts_by_category.get(category, []))
            
            index_content += f"- **[{category_name}]({safe_category_name}-glossary.md)** - {term_count} terms, {concept_count} concepts\n"
        
        index_content += f"\n## Usage\n\nEach category glossary provides specialized vocabulary for that domain. Use these glossaries to understand domain-specific terminology and concepts when working with the converted document content.\n"
        
        index_path = categories_dir / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        category_files.append(str(index_path))
        return category_files
    
    def resolve_and_link_cross_references(self, sections):
        """Detect and resolve cross-references, converting them to markdown links"""
        # Create cross-references directory
        xrefs_dir = self.output_dir / "cross-references"
        xrefs_dir.mkdir(exist_ok=True)
        
        # Build comprehensive reference mapping
        reference_map = self.build_reference_mapping(sections)
        
        # Detect and categorize cross-references
        cross_references = self.detect_cross_references(sections, reference_map)
        
        # Resolve references to markdown links
        resolved_references = self.resolve_references_to_links(cross_references, reference_map)
        
        # Update section files with resolved links
        updated_sections = self.update_sections_with_links(sections, resolved_references)
        
        # Generate cross-reference documentation
        self.generate_cross_reference_documentation(xrefs_dir, resolved_references, reference_map)
        
        return len(resolved_references)
    
    def build_reference_mapping(self, sections):
        """Build comprehensive mapping of referenceable content"""
        reference_map = {
            'sections': {},
            'headers': {},
            'figures': {},
            'tables': {},
            'pages': {},
            'equations': {},
            'code_blocks': {},
            'appendices': {},
            'footnotes': {},
            'external_docs': {},
            'api_endpoints': {}
        }
        
        # Map sections by title, slug, and aliases
        for i, section in enumerate(sections):
            section_title = section.get('title', f'Section {i+1}')
            section_slug = section.get('slug', f'section-{i+1}')
            section_file = f"{section_slug}.md"
            content = section.get('content', '')
            
            # Primary section mapping
            reference_map['sections'][section_title.lower()] = {
                'title': section_title,
                'slug': section_slug,
                'file': section_file,
                'section_number': i + 1,
                'type': section.get('section_type', 'general'),
                'aliases': self.extract_section_aliases(section_title, content)
            }
            
            # Extract page numbers from content
            page_refs = re.findall(r'Page (\d+)', content, re.IGNORECASE)
            for page_num in page_refs:
                reference_map['pages'][page_num] = {
                    'page': page_num,
                    'section': section_title,
                    'file': section_file,
                    'slug': section_slug
                }
            
            # Extract headers within sections
            headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
            for level, header_text in headers:
                header_slug = self.slugify(header_text)
                reference_map['headers'][header_text.lower()] = {
                    'text': header_text,
                    'level': len(level),
                    'slug': header_slug,
                    'section': section_title,
                    'file': section_file,
                    'anchor': f"#{header_slug}"
                }
            
            # Extract figure references
            figures = re.findall(r'(?:Figure|Fig\.?)\s*(\d+(?:\.\d+)?)[:\s]*([^.\n]*)', content, re.IGNORECASE)
            for fig_num, fig_caption in figures:
                reference_map['figures'][fig_num] = {
                    'number': fig_num,
                    'caption': fig_caption.strip(),
                    'section': section_title,
                    'file': section_file,
                    'slug': f"figure-{fig_num.replace('.', '-')}"
                }
            
            # Extract table references
            tables = re.findall(r'(?:Table)\s*(\d+(?:\.\d+)?)[:\s]*([^.\n]*)', content, re.IGNORECASE)
            for table_num, table_caption in tables:
                reference_map['tables'][table_num] = {
                    'number': table_num,
                    'caption': table_caption.strip(),
                    'section': section_title,
                    'file': section_file,
                    'slug': f"table-{table_num.replace('.', '-')}"
                }
            
            # Extract equation references
            equations = re.findall(r'(?:Equation|Eq\.?)\s*(\d+(?:\.\d+)?)', content, re.IGNORECASE)
            for eq_num in equations:
                reference_map['equations'][eq_num] = {
                    'number': eq_num,
                    'section': section_title,
                    'file': section_file,
                    'slug': f"equation-{eq_num.replace('.', '-')}"
                }
            
            # Extract code block references
            code_blocks = re.findall(r'(?:Listing|Code)\s*(\d+(?:\.\d+)?)[:\s]*([^.\n]*)', content, re.IGNORECASE)
            for code_num, code_caption in code_blocks:
                reference_map['code_blocks'][code_num] = {
                    'number': code_num,
                    'caption': code_caption.strip(),
                    'section': section_title,
                    'file': section_file,
                    'slug': f"code-{code_num.replace('.', '-')}"
                }
            
            # Extract appendix references
            if 'appendix' in section_title.lower() or section.get('section_type') == 'appendix':
                appendix_match = re.search(r'appendix\s*([a-z]|\d+)', section_title, re.IGNORECASE)
                if appendix_match:
                    appendix_id = appendix_match.group(1).upper()
                    reference_map['appendices'][appendix_id] = {
                        'id': appendix_id,
                        'title': section_title,
                        'file': section_file,
                        'slug': section_slug
                    }
            
            # Extract API endpoint references if it's an API section
            if section.get('section_type') == 'api_endpoint':
                api_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)'
                api_matches = re.findall(api_pattern, content, re.IGNORECASE)
                for method, path in api_matches:
                    endpoint_key = f"{method.upper()} {path}"
                    reference_map['api_endpoints'][endpoint_key.lower()] = {
                        'method': method.upper(),
                        'path': path,
                        'section': section_title,
                        'file': section_file,
                        'slug': section_slug
                    }
        
        return reference_map
    
    def detect_cross_references(self, sections, reference_map):
        """Detect various types of cross-references in content"""
        cross_references = {
            'section_refs': [],
            'page_refs': [],
            'figure_refs': [],
            'table_refs': [],
            'equation_refs': [],
            'code_refs': [],
            'appendix_refs': [],
            'header_refs': [],
            'api_refs': [],
            'see_also_refs': [],
            'above_below_refs': []
        }
        
        # Define detection patterns
        patterns = {
            'section_refs': [
                r'(?:see|refer to|described in|detailed in|as shown in)\s+(?:section|chapter)\s+([^.,\n]+)',
                r'(?:section|chapter)\s+(\d+(?:\.\d+)?)',
                r'(?:in|from)\s+(?:the\s+)?([^,.\n]+ section)',
            ],
            'page_refs': [
                r'(?:page|p\.)\s*(\d+)',
                r'(?:on page|see page)\s+(\d+)',
                r'(?:\(p\.\s*(\d+)\))',
            ],
            'figure_refs': [
                r'(?:figure|fig\.?)\s*(\d+(?:\.\d+)?)',
                r'(?:see|shown in|as in)\s+(?:figure|fig\.?)\s*(\d+(?:\.\d+)?)',
                r'(?:\((?:figure|fig\.?)\s*(\d+(?:\.\d+)?)\))',
            ],
            'table_refs': [
                r'(?:table)\s*(\d+(?:\.\d+)?)',
                r'(?:see|shown in|as in)\s+(?:table)\s*(\d+(?:\.\d+)?)',
                r'(?:\(table\s*(\d+(?:\.\d+)?)\))',
            ],
            'equation_refs': [
                r'(?:equation|eq\.?)\s*(\d+(?:\.\d+)?)',
                r'(?:\((?:equation|eq\.?)\s*(\d+(?:\.\d+)?)\))',
            ],
            'code_refs': [
                r'(?:listing|code)\s*(\d+(?:\.\d+)?)',
                r'(?:see|shown in)\s+(?:listing|code)\s*(\d+(?:\.\d+)?)',
            ],
            'appendix_refs': [
                r'(?:appendix)\s+([a-z]|\d+)',
                r'(?:see|refer to)\s+(?:appendix)\s+([a-z]|\d+)',
            ],
            'api_refs': [
                r'(?:endpoint|API)\s+(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)',
                r'(?:the\s+)?(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)(?:\s+endpoint)?',
            ],
            'see_also_refs': [
                r'(?:see also|also see|refer to|reference)\s+([^.,\n]+)',
                r'(?:for more information|more details)\s+(?:see|refer to)\s+([^.,\n]+)',
            ],
            'above_below_refs': [
                r'(?:above|below|earlier|later|previous|next)\s+(?:section|chapter|discussion)',
                r'(?:as mentioned|discussed)\s+(?:above|below|earlier|later|previously)',
            ]
        }
        
        # Process each section
        for section in sections:
            content = section.get('content', '')
            section_title = section.get('title', 'Unknown')
            section_file = f"{section.get('slug', 'unknown')}.md"
            
            # Detect each type of reference
            for ref_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        # Extract context around the reference
                        context_start = max(0, match.start() - 50)
                        context_end = min(len(content), match.end() + 50)
                        context = content[context_start:context_end].strip()
                        
                        reference_info = {
                            'type': ref_type,
                            'match_text': match.group(),
                            'context': context,
                            'position': match.start(),
                            'source_section': section_title,
                            'source_file': section_file,
                            'groups': match.groups() if match.groups() else []
                        }
                        
                        # Add specific reference details based on type
                        if ref_type == 'api_refs' and len(match.groups()) >= 2:
                            reference_info['method'] = match.group(1).upper()
                            reference_info['path'] = match.group(2)
                        elif len(match.groups()) >= 1:
                            reference_info['target'] = match.group(1).strip()
                        
                        cross_references[ref_type].append(reference_info)
        
        return cross_references
    
    def resolve_references_to_links(self, cross_references, reference_map):
        """Resolve detected references to markdown links"""
        resolved_references = []
        
        for ref_type, refs in cross_references.items():
            for ref in refs:
                resolution = self.resolve_single_reference(ref, reference_map, ref_type)
                if resolution:
                    resolved_references.append({
                        'original': ref,
                        'resolution': resolution,
                        'type': ref_type,
                        'link_text': resolution['link_text'],
                        'link_url': resolution['link_url'],
                        'description': resolution.get('description', ''),
                        'confidence': resolution.get('confidence', 0.5)
                    })
        
        return resolved_references
    
    def resolve_single_reference(self, ref, reference_map, ref_type):
        """Resolve a single reference to a markdown link"""
        if ref_type == 'page_refs':
            page_num = ref.get('target') or (ref['groups'][0] if ref['groups'] else None)
            if page_num and page_num in reference_map['pages']:
                page_info = reference_map['pages'][page_num]
                return {
                    'link_text': f"Page {page_num}",
                    'link_url': f"{page_info['file']}",
                    'description': f"Links to {page_info['section']}",
                    'confidence': 0.9
                }
        
        elif ref_type == 'figure_refs':
            fig_num = ref.get('target') or (ref['groups'][0] if ref['groups'] else None)
            if fig_num and fig_num in reference_map['figures']:
                fig_info = reference_map['figures'][fig_num]
                return {
                    'link_text': f"Figure {fig_num}",
                    'link_url': f"{fig_info['file']}#{fig_info['slug']}",
                    'description': f"Links to {fig_info['caption']}",
                    'confidence': 0.9
                }
        
        elif ref_type == 'table_refs':
            table_num = ref.get('target') or (ref['groups'][0] if ref['groups'] else None)
            if table_num and table_num in reference_map['tables']:
                table_info = reference_map['tables'][table_num]
                return {
                    'link_text': f"Table {table_num}",
                    'link_url': f"{table_info['file']}#{table_info['slug']}",
                    'description': f"Links to {table_info['caption']}",
                    'confidence': 0.9
                }
        
        elif ref_type == 'equation_refs':
            eq_num = ref.get('target') or (ref['groups'][0] if ref['groups'] else None)
            if eq_num and eq_num in reference_map['equations']:
                eq_info = reference_map['equations'][eq_num]
                return {
                    'link_text': f"Equation {eq_num}",
                    'link_url': f"{eq_info['file']}#{eq_info['slug']}",
                    'description': f"Links to equation in {eq_info['section']}",
                    'confidence': 0.9
                }
        
        elif ref_type == 'code_refs':
            code_num = ref.get('target') or (ref['groups'][0] if ref['groups'] else None)
            if code_num and code_num in reference_map['code_blocks']:
                code_info = reference_map['code_blocks'][code_num]
                return {
                    'link_text': f"Code {code_num}",
                    'link_url': f"{code_info['file']}#{code_info['slug']}",
                    'description': f"Links to {code_info['caption']}",
                    'confidence': 0.9
                }
        
        elif ref_type == 'appendix_refs':
            appendix_id = ref.get('target') or (ref['groups'][0] if ref['groups'] else None)
            if appendix_id and appendix_id.upper() in reference_map['appendices']:
                appendix_info = reference_map['appendices'][appendix_id.upper()]
                return {
                    'link_text': f"Appendix {appendix_id.upper()}",
                    'link_url': f"{appendix_info['file']}",
                    'description': f"Links to {appendix_info['title']}",
                    'confidence': 0.9
                }
        
        elif ref_type == 'api_refs':
            if 'method' in ref and 'path' in ref:
                endpoint_key = f"{ref['method']} {ref['path']}".lower()
                if endpoint_key in reference_map['api_endpoints']:
                    api_info = reference_map['api_endpoints'][endpoint_key]
                    return {
                        'link_text': f"{api_info['method']} {api_info['path']}",
                        'link_url': f"{api_info['file']}",
                        'description': f"Links to API endpoint documentation",
                        'confidence': 0.95
                    }
        
        elif ref_type == 'section_refs':
            target = ref.get('target', '').lower()
            # Try exact match first
            if target in reference_map['sections']:
                section_info = reference_map['sections'][target]
                return {
                    'link_text': section_info['title'],
                    'link_url': f"{section_info['file']}",
                    'description': f"Links to {section_info['title']}",
                    'confidence': 0.95
                }
            
            # Try fuzzy matching for section titles
            for section_key, section_info in reference_map['sections'].items():
                if target in section_key or any(alias.lower() in target for alias in section_info['aliases']):
                    return {
                        'link_text': section_info['title'],
                        'link_url': f"{section_info['file']}",
                        'description': f"Links to {section_info['title']}",
                        'confidence': 0.7
                    }
        
        elif ref_type == 'header_refs':
            target = ref.get('target', '').lower()
            if target in reference_map['headers']:
                header_info = reference_map['headers'][target]
                return {
                    'link_text': header_info['text'],
                    'link_url': f"{header_info['file']}{header_info['anchor']}",
                    'description': f"Links to section header",
                    'confidence': 0.8
                }
        
        return None
    
    def update_sections_with_links(self, sections, resolved_references):
        """Update section files with resolved markdown links"""
        updates_by_file = {}
        
        # Group updates by file
        for resolved_ref in resolved_references:
            source_file = resolved_ref['original']['source_file']
            if source_file not in updates_by_file:
                updates_by_file[source_file] = []
            updates_by_file[source_file].append(resolved_ref)
        
        # Apply updates to each file
        updated_sections = []
        for section in sections:
            section_file = f"{section.get('slug', 'unknown')}.md"
            file_path = self.output_dir / "sections" / section_file
            
            if section_file in updates_by_file and file_path.exists():
                # Read current content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Apply link replacements
                updated_content = content
                updates = updates_by_file[section_file]
                
                # Sort by position (reverse order to maintain positions)
                updates.sort(key=lambda x: x['original']['position'], reverse=True)
                
                for update in updates:
                    original_text = update['original']['match_text']
                    link_text = update['link_text']
                    link_url = update['link_url']
                    confidence = update['confidence']
                    
                    # Only replace high-confidence matches
                    if confidence >= 0.7:
                        markdown_link = f"[{link_text}]({link_url})"
                        updated_content = updated_content.replace(original_text, markdown_link, 1)
                
                # Write updated content back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                # Update section data
                section['content'] = updated_content
                updated_sections.append(section_file)
        
        return updated_sections
    
    def generate_cross_reference_documentation(self, xrefs_dir, resolved_references, reference_map):
        """Generate comprehensive cross-reference documentation"""
        # Create cross-reference index
        xref_content = f"""# Cross-Reference Index

Generated: {datetime.now().isoformat()}
Total References Resolved: {len(resolved_references)}

## Overview

This document catalogs all cross-references found in the PDF and their resolution to markdown links. Cross-references help create a navigable, interconnected document structure that's optimal for LLM understanding.

## Reference Statistics

"""
        
        # Calculate statistics
        ref_types = {}
        confidence_levels = {'high': 0, 'medium': 0, 'low': 0}
        
        for ref in resolved_references:
            ref_type = ref['type']
            confidence = ref['confidence']
            
            ref_types[ref_type] = ref_types.get(ref_type, 0) + 1
            
            if confidence >= 0.8:
                confidence_levels['high'] += 1
            elif confidence >= 0.6:
                confidence_levels['medium'] += 1
            else:
                confidence_levels['low'] += 1
        
        # Add statistics to content
        for ref_type, count in sorted(ref_types.items()):
            type_name = ref_type.replace('_', ' ').title()
            xref_content += f"- **{type_name}**: {count} references\n"
        
        xref_content += f"\n**Confidence Distribution:**\n"
        xref_content += f"- High Confidence (≥80%): {confidence_levels['high']} references\n"
        xref_content += f"- Medium Confidence (≥60%): {confidence_levels['medium']} references\n"
        xref_content += f"- Low Confidence (<60%): {confidence_levels['low']} references\n\n"
        
        # Add detailed reference listings
        for ref_type, count in sorted(ref_types.items()):
            if count == 0:
                continue
                
            type_name = ref_type.replace('_', ' ').title()
            xref_content += f"## {type_name} ({count})\n\n"
            
            type_refs = [ref for ref in resolved_references if ref['type'] == ref_type]
            type_refs.sort(key=lambda x: x['confidence'], reverse=True)
            
            for ref in type_refs:
                original_text = ref['original']['match_text']
                link_text = ref['link_text']
                link_url = ref['link_url']
                description = ref['description']
                confidence = ref['confidence']
                source_section = ref['original']['source_section']
                
                xref_content += f"**{original_text}** → [{link_text}]({link_url})\n"
                xref_content += f"  - *Source*: {source_section}\n"
                xref_content += f"  - *Description*: {description}\n"
                xref_content += f"  - *Confidence*: {confidence:.1%}\n\n"
        
        # Save cross-reference index
        index_path = xrefs_dir / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(xref_content)
        
        # Save machine-readable reference data
        xref_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_references': len(resolved_references),
                'reference_types': ref_types,
                'confidence_distribution': confidence_levels
            },
            'resolved_references': resolved_references,
            'reference_map': reference_map
        }
        
        data_path = xrefs_dir / "cross-references.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(xref_data, f, indent=2, ensure_ascii=False, default=str)
        
        return str(index_path)
    
    # Helper methods for cross-reference resolution
    def extract_section_aliases(self, title, content):
        """Extract alternative names/aliases for a section"""
        aliases = []
        
        # Extract common alias patterns
        alias_patterns = [
            r'(?:also known as|aka|referred to as)\s+([^.,\n]+)',
            r'(?:\(([^)]+)\))',  # Parenthetical aliases
        ]
        
        for pattern in alias_patterns:
            matches = re.findall(pattern, content[:500], re.IGNORECASE)  # Check first 500 chars
            aliases.extend([match.strip() for match in matches if len(match.strip()) > 2])
        
        return aliases[:5]  # Limit to 5 aliases
    
    def slugify(self, text):
        """Convert text to a URL-friendly slug"""
        # Remove special characters and convert to lowercase
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        # Replace spaces with hyphens
        slug = re.sub(r'[\s_-]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug
    
    def generate_multi_level_summaries(self, sections, full_content):
        """Generate multi-level summaries for progressive disclosure and context optimization"""
        # Create summaries directory
        summaries_dir = self.output_dir / "summaries"
        summaries_dir.mkdir(exist_ok=True)
        
        # Analyze document structure and content
        document_analysis = self.analyze_document_structure(sections, full_content)
        
        # Generate executive summary (250 words)
        executive_summary = self.generate_executive_summary(sections, document_analysis)
        
        # Generate detailed summary (1000 words)
        detailed_summary = self.generate_detailed_summary(sections, document_analysis)
        
        # Generate complete summary (full context with structure)
        complete_summary = self.generate_complete_summary(sections, document_analysis, full_content)
        
        # Create progressive disclosure index
        disclosure_index = self.create_progressive_disclosure_index(executive_summary, detailed_summary, complete_summary)
        
        # Save all summary files
        self.save_summary_files(summaries_dir, executive_summary, detailed_summary, complete_summary, disclosure_index)
        
        return len(sections)
    
    def analyze_document_structure(self, sections, full_content):
        """Analyze document structure for intelligent summarization"""
        analysis = {
            'total_sections': len(sections),
            'total_tokens': self.count_tokens(full_content),
            'document_type': self.detect_document_type(sections),
            'key_topics': self.extract_key_topics(sections),
            'section_priorities': self.calculate_section_priorities(sections),
            'complexity_level': self.assess_document_complexity(sections),
            'primary_audience': self.detect_primary_audience(sections),
            'content_distribution': self.analyze_content_distribution(sections),
            'technical_depth': self.assess_technical_depth(sections)
        }
        
        return analysis
    
    def detect_document_type(self, sections):
        """Detect the type of document for tailored summarization"""
        api_indicators = sum(1 for s in sections if s.get('section_type') == 'api_endpoint')
        auth_indicators = sum(1 for s in sections if 'auth' in s.get('title', '').lower())
        code_indicators = sum(1 for s in sections if 'code' in s.get('content', '').lower().count('```'))
        
        if api_indicators > len(sections) * 0.3:
            return 'api_documentation'
        elif code_indicators > len(sections) * 0.4:
            return 'technical_manual'
        elif any('research' in s.get('title', '').lower() for s in sections):
            return 'research_paper'
        elif any('legal' in s.get('title', '').lower() for s in sections):
            return 'legal_document'
        elif any('tutorial' in s.get('title', '').lower() for s in sections):
            return 'tutorial'
        else:
            return 'general_documentation'
    
    def extract_key_topics(self, sections):
        """Extract key topics using frequency analysis and semantic detection"""
        # Combine all content for analysis
        all_content = ' '.join(s.get('content', '') for s in sections)
        
        # Extract key phrases and topics
        key_phrases = {}
        
        # Technical terms (2-3 words)
        technical_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b',  # Title case phrases
            r'\b(?:API|HTTP|JSON|XML|OAuth|JWT|REST|GraphQL|HTTPS?|TCP|UDP|SQL|NoSQL)\b',  # Technical acronyms
            r'\b\w+(?:ing|tion|ment|ness|ity)\b',  # Process/concept words
        ]
        
        for pattern in technical_patterns:
            matches = re.findall(pattern, all_content)
            for match in matches:
                key_phrases[match.lower()] = key_phrases.get(match.lower(), 0) + 1
        
        # Get top topics by frequency
        sorted_topics = sorted(key_phrases.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:15] if count >= 3]
    
    def calculate_section_priorities(self, sections):
        """Calculate priority scores for sections based on content importance"""
        priorities = {}
        
        for section in sections:
            title = section.get('title', '')
            content = section.get('content', '')
            section_type = section.get('section_type', 'general')
            
            # Base priority score
            priority = 5.0
            
            # Boost for important section types
            type_boosts = {
                'introduction': 8.0,
                'overview': 7.5,
                'getting_started': 8.5,
                'api_endpoint': 7.0,
                'authentication': 8.0,
                'security': 7.5,
                'examples': 6.5,
                'troubleshooting': 6.0,
                'reference': 5.5,
                'appendix': 3.0
            }
            priority = type_boosts.get(section_type, priority)
            
            # Boost for important keywords in title
            important_keywords = ['overview', 'introduction', 'getting started', 'quickstart', 
                                'authentication', 'security', 'api', 'examples', 'tutorial']
            for keyword in important_keywords:
                if keyword in title.lower():
                    priority += 2.0
                    break
            
            # Boost for content length (longer sections often more important)
            content_length = len(content)
            if content_length > 2000:
                priority += 1.5
            elif content_length > 1000:
                priority += 1.0
            elif content_length < 200:
                priority -= 1.0
            
            # Boost for sections with code examples
            code_blocks = content.count('```')
            priority += min(code_blocks * 0.5, 2.0)
            
            # Boost for sections with lists (often important info)
            list_items = content.count('\n- ') + content.count('\n* ')
            priority += min(list_items * 0.1, 1.5)
            
            priorities[section.get('slug', 'unknown')] = round(priority, 2)
        
        return priorities
    
    def assess_document_complexity(self, sections):
        """Assess overall document complexity for appropriate summarization"""
        complexity_indicators = {
            'technical_terms': 0,
            'code_blocks': 0,
            'api_endpoints': 0,
            'average_section_length': 0,
            'nested_concepts': 0
        }
        
        total_content_length = 0
        
        for section in sections:
            content = section.get('content', '')
            total_content_length += len(content)
            
            # Count technical terms
            tech_terms = len(re.findall(r'\b(?:API|HTTP|JSON|XML|OAuth|JWT|REST|GraphQL|HTTPS?|TCP|UDP|SQL|NoSQL|Docker|Kubernetes)\b', content, re.IGNORECASE))
            complexity_indicators['technical_terms'] += tech_terms
            
            # Count code blocks
            complexity_indicators['code_blocks'] += content.count('```')
            
            # Count API endpoints
            if section.get('section_type') == 'api_endpoint':
                complexity_indicators['api_endpoints'] += 1
            
            # Count nested concepts (headers within sections)
            complexity_indicators['nested_concepts'] += len(re.findall(r'^#{2,6}\s+', content, re.MULTILINE))
        
        complexity_indicators['average_section_length'] = total_content_length / len(sections) if sections else 0
        
        # Calculate complexity score
        complexity_score = 0
        complexity_score += min(complexity_indicators['technical_terms'] / 10, 3.0)
        complexity_score += min(complexity_indicators['code_blocks'] / 5, 2.0)
        complexity_score += min(complexity_indicators['api_endpoints'] / 3, 2.0)
        complexity_score += min(complexity_indicators['average_section_length'] / 1000, 2.0)
        complexity_score += min(complexity_indicators['nested_concepts'] / 20, 1.0)
        
        if complexity_score < 3.0:
            return 'low'
        elif complexity_score < 6.0:
            return 'medium'
        else:
            return 'high'
    
    def detect_primary_audience(self, sections):
        """Detect primary audience for appropriate summarization tone"""
        developer_indicators = 0
        business_indicators = 0
        general_indicators = 0
        
        for section in sections:
            content = section.get('content', '').lower()
            title = section.get('title', '').lower()
            
            # Developer indicators
            if any(word in content for word in ['code', 'api', 'endpoint', 'function', 'class', 'method', 'variable']):
                developer_indicators += 1
            if any(word in title for word in ['api', 'development', 'sdk', 'integration', 'technical']):
                developer_indicators += 2
            
            # Business indicators
            if any(word in content for word in ['business', 'user', 'customer', 'workflow', 'process', 'benefit']):
                business_indicators += 1
            if any(word in title for word in ['overview', 'introduction', 'business', 'user guide']):
                business_indicators += 2
            
            # General indicators
            if any(word in content for word in ['tutorial', 'guide', 'help', 'support', 'getting started']):
                general_indicators += 1
        
        if developer_indicators > business_indicators and developer_indicators > general_indicators:
            return 'developers'
        elif business_indicators > general_indicators:
            return 'business_users'
        else:
            return 'general_users'
    
    def analyze_content_distribution(self, sections):
        """Analyze how content is distributed across sections"""
        distribution = {
            'section_types': {},
            'length_distribution': {},
            'content_balance': {}
        }
        
        # Section type distribution
        for section in sections:
            section_type = section.get('section_type', 'general')
            distribution['section_types'][section_type] = distribution['section_types'].get(section_type, 0) + 1
        
        # Length distribution
        lengths = [len(section.get('content', '')) for section in sections]
        if lengths:
            distribution['length_distribution'] = {
                'min': min(lengths),
                'max': max(lengths),
                'avg': sum(lengths) / len(lengths),
                'median': sorted(lengths)[len(lengths) // 2]
            }
        
        return distribution
    
    def assess_technical_depth(self, sections):
        """Assess the technical depth of the document"""
        depth_indicators = 0
        total_content = 0
        
        for section in sections:
            content = section.get('content', '')
            total_content += len(content)
            
            # Count technical depth indicators
            depth_indicators += content.count('```')  # Code blocks
            depth_indicators += len(re.findall(r'\b[A-Z_]{3,}\b', content))  # Constants/enums
            depth_indicators += len(re.findall(r'\b\w+\(\)', content))  # Function calls
            depth_indicators += content.count('http')  # API references
            depth_indicators += len(re.findall(r'\{.*?\}', content))  # JSON/object notation
        
        # Calculate depth ratio
        depth_ratio = depth_indicators / (total_content / 1000) if total_content > 0 else 0
        
        if depth_ratio < 2.0:
            return 'surface'
        elif depth_ratio < 5.0:
            return 'moderate'
        else:
            return 'deep'
    
    def generate_executive_summary(self, sections, analysis):
        """Generate executive summary (250 words) for quick overview"""
        target_words = 250
        
        # Prioritize sections for executive summary
        high_priority_sections = []
        for section in sections:
            section_slug = section.get('slug', 'unknown')
            priority = analysis['section_priorities'].get(section_slug, 5.0)
            if priority >= 7.0:  # High priority threshold
                high_priority_sections.append(section)
        
        # If no high priority sections, take first few sections
        if not high_priority_sections:
            high_priority_sections = sections[:3]
        
        summary_content = f"""# Executive Summary
        
Document Type: {analysis['document_type'].replace('_', ' ').title()}
Complexity: {analysis['complexity_level'].title()}
Target Audience: {analysis['primary_audience'].replace('_', ' ').title()}
Total Sections: {analysis['total_sections']}
Estimated Reading Time: {analysis['total_tokens'] // 200} minutes

## Overview

"""
        
        # Generate concise overview based on document type
        if analysis['document_type'] == 'api_documentation':
            summary_content += f"This API documentation provides comprehensive guidance for integrating with the service. "
        elif analysis['document_type'] == 'technical_manual':
            summary_content += f"This technical manual covers implementation details and best practices. "
        elif analysis['document_type'] == 'tutorial':
            summary_content += f"This tutorial guides users through step-by-step implementation. "
        else:
            summary_content += f"This document provides essential information and guidance. "
        
        # Add key topics
        if analysis['key_topics']:
            key_topics_text = ', '.join(analysis['key_topics'][:5])
            summary_content += f"Key areas covered include: {key_topics_text}. "
        
        # Add critical highlights from high priority sections
        words_used = len(summary_content.split())
        remaining_words = target_words - words_used
        
        summary_content += "\n## Key Points\n\n"
        
        for section in high_priority_sections[:3]:  # Limit to top 3 sections
            if remaining_words <= 20:
                break
                
            section_title = section.get('title', 'Section')
            section_content = section.get('content', '')
            
            # Extract key sentence from section
            sentences = re.split(r'[.!?]+', section_content)
            key_sentence = None
            
            # Find sentence with important keywords
            for sentence in sentences:
                if len(sentence.split()) > 5 and any(topic in sentence.lower() for topic in analysis['key_topics'][:5]):
                    key_sentence = sentence.strip()
                    break
            
            if not key_sentence and sentences:
                # Fallback to first substantial sentence
                key_sentence = next((s.strip() for s in sentences if len(s.split()) > 10), sentences[0].strip())
            
            if key_sentence:
                # Limit sentence length
                words_in_sentence = len(key_sentence.split())
                if words_in_sentence <= remaining_words - 10:
                    summary_content += f"- **{section_title}**: {key_sentence}\n"
                    remaining_words -= words_in_sentence + 5
                else:
                    # Truncate sentence
                    truncated = ' '.join(key_sentence.split()[:remaining_words - 10]) + '...'
                    summary_content += f"- **{section_title}**: {truncated}\n"
                    break
        
        # Add navigation guidance
        summary_content += f"\n## Next Steps\n\n"
        if analysis['document_type'] == 'api_documentation':
            summary_content += "Review authentication requirements, explore endpoint documentation, and check integration examples."
        elif analysis['document_type'] == 'tutorial':
            summary_content += "Follow the step-by-step instructions, try the examples, and refer to troubleshooting if needed."
        else:
            summary_content += "Explore detailed sections based on your specific needs and use cases."
        
        return {
            'title': 'Executive Summary',
            'word_count': len(summary_content.split()),
            'target_audience': analysis['primary_audience'],
            'reading_time': '1-2 minutes',
            'content': summary_content,
            'key_sections_covered': [s.get('title') for s in high_priority_sections],
            'optimization': 'Quick overview for decision making and initial understanding'
        }
    
    def generate_detailed_summary(self, sections, analysis):
        """Generate detailed summary (1000 words) for comprehensive understanding"""
        target_words = 1000
        
        # Select sections based on priority and coverage
        selected_sections = []
        priority_threshold = 6.0
        
        # Get sections above priority threshold
        for section in sections:
            section_slug = section.get('slug', 'unknown')
            priority = analysis['section_priorities'].get(section_slug, 5.0)
            if priority >= priority_threshold:
                selected_sections.append((section, priority))
        
        # If not enough content, lower threshold
        if len(selected_sections) < 5:
            priority_threshold = 5.5
            selected_sections = [(s, analysis['section_priorities'].get(s.get('slug', 'unknown'), 5.0)) 
                               for s in sections if analysis['section_priorities'].get(s.get('slug', 'unknown'), 5.0) >= priority_threshold]
        
        # Sort by priority
        selected_sections.sort(key=lambda x: x[1], reverse=True)
        
        summary_content = f"""# Detailed Summary

## Document Overview

**Type**: {analysis['document_type'].replace('_', ' ').title()}  
**Complexity Level**: {analysis['complexity_level'].title()}  
**Primary Audience**: {analysis['primary_audience'].replace('_', ' ').title()}  
**Technical Depth**: {analysis['technical_depth'].title()}  
**Total Content**: {analysis['total_sections']} sections, ~{analysis['total_tokens']} tokens

"""
        
        # Add document-specific context
        if analysis['document_type'] == 'api_documentation':
            summary_content += """This API documentation provides comprehensive integration guidance with detailed endpoint specifications, authentication methods, and practical examples. """
        elif analysis['document_type'] == 'technical_manual':
            summary_content += """This technical manual offers in-depth implementation guidance with code examples, best practices, and troubleshooting information. """
        
        # Add key topics section
        if analysis['key_topics']:
            summary_content += f"\n**Key Topics Covered**: {', '.join(analysis['key_topics'][:8])}\n\n"
        
        # Process selected sections
        words_used = len(summary_content.split())
        remaining_words = target_words - words_used
        words_per_section = remaining_words // min(len(selected_sections), 8)
        
        summary_content += "## Content Breakdown\n\n"
        
        sections_covered = 0
        for section, priority in selected_sections[:8]:  # Limit to top 8 sections
            if remaining_words <= 50:
                break
                
            section_title = section.get('title', 'Section')
            section_content = section.get('content', '')
            section_type = section.get('section_type', 'general')
            
            summary_content += f"### {section_title}\n"
            summary_content += f"*Priority: {priority:.1f} | Type: {section_type.replace('_', ' ').title()}*\n\n"
            
            # Generate section summary
            section_summary = self.summarize_section_content(section_content, min(words_per_section, remaining_words - 20))
            summary_content += section_summary + "\n\n"
            
            words_used_in_section = len(section_summary.split())
            remaining_words -= words_used_in_section + 15  # Account for headers
            sections_covered += 1
        
        # Add implementation guidance
        summary_content += "## Implementation Guidance\n\n"
        
        if analysis['primary_audience'] == 'developers':
            summary_content += "**For Developers**: Focus on API endpoints, code examples, and integration patterns. Pay attention to authentication requirements and error handling.\n\n"
        elif analysis['primary_audience'] == 'business_users':
            summary_content += "**For Business Users**: Review workflow descriptions, feature benefits, and user-facing functionality. Consider implementation timeline and resource requirements.\n\n"
        else:
            summary_content += "**Getting Started**: Begin with overview sections, follow step-by-step guides, and reference detailed sections as needed.\n\n"
        
        # Add complexity-based recommendations
        if analysis['complexity_level'] == 'high':
            summary_content += "**Complexity Note**: This is a technically complex document. Consider reviewing prerequisite knowledge and taking time to understand core concepts before implementation.\n\n"
        
        return {
            'title': 'Detailed Summary',
            'word_count': len(summary_content.split()),
            'target_audience': analysis['primary_audience'],
            'reading_time': '4-6 minutes',
            'content': summary_content,
            'sections_covered': sections_covered,
            'priority_threshold': priority_threshold,
            'optimization': 'Comprehensive understanding with key implementation details'
        }
    
    def summarize_section_content(self, content, max_words):
        """Create a focused summary of section content"""
        if not content or max_words <= 0:
            return ""
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return content[:max_words*5]  # Fallback to character limit
        
        # Score sentences for importance
        scored_sentences = []
        for sentence in sentences:
            score = 0
            
            # Boost for first and last sentences
            if sentence == sentences[0]:
                score += 2
            if sentence == sentences[-1]:
                score += 1
            
            # Boost for sentences with important keywords
            important_words = ['important', 'key', 'essential', 'required', 'must', 'should', 'example', 'note']
            for word in important_words:
                if word in sentence.lower():
                    score += 1
            
            # Boost for sentences with technical terms
            tech_terms = ['API', 'endpoint', 'authentication', 'parameter', 'response', 'request', 'method', 'function']
            for term in tech_terms:
                if term.lower() in sentence.lower():
                    score += 0.5
            
            # Penalize very long sentences
            if len(sentence.split()) > 30:
                score -= 1
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and build summary
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        summary_parts = []
        words_used = 0
        
        for sentence, score in scored_sentences:
            sentence_words = len(sentence.split())
            if words_used + sentence_words <= max_words:
                summary_parts.append(sentence)
                words_used += sentence_words
            elif words_used == 0:  # At least include one sentence
                # Truncate the sentence
                words_to_include = max_words - 5
                truncated = ' '.join(sentence.split()[:words_to_include]) + '...'
                summary_parts.append(truncated)
                break
        
        return '. '.join(summary_parts) + '.' if summary_parts else ""
    
    def generate_complete_summary(self, sections, analysis, full_content):
        """Generate complete summary with full context and structure"""
        summary_content = f"""# Complete Document Summary

## Comprehensive Analysis

**Document Classification**: {analysis['document_type'].replace('_', ' ').title()}  
**Complexity Assessment**: {analysis['complexity_level'].title()} complexity  
**Primary Audience**: {analysis['primary_audience'].replace('_', ' ').title()}  
**Technical Depth**: {analysis['technical_depth'].title()} technical detail  
**Structure**: {analysis['total_sections']} sections  
**Content Volume**: {analysis['total_tokens']} tokens (~{analysis['total_tokens'] // 200} minutes reading)

## Content Architecture

"""
        
        # Add detailed content distribution
        content_dist = analysis.get('content_distribution', {})
        if content_dist.get('section_types'):
            summary_content += "**Section Type Distribution**:\n"
            for section_type, count in sorted(content_dist['section_types'].items(), key=lambda x: x[1], reverse=True):
                summary_content += f"- {section_type.replace('_', ' ').title()}: {count} sections\n"
            summary_content += "\n"
        
        # Add key topics with context
        if analysis['key_topics']:
            summary_content += "**Primary Topics and Themes**:\n"
            for i, topic in enumerate(analysis['key_topics'][:10], 1):
                summary_content += f"{i}. {topic.title()}\n"
            summary_content += "\n"
        
        # Complete section breakdown
        summary_content += "## Section-by-Section Breakdown\n\n"
        
        for i, section in enumerate(sections, 1):
            section_title = section.get('title', f'Section {i}')
            section_content = section.get('content', '')
            section_type = section.get('section_type', 'general')
            section_slug = section.get('slug', 'unknown')
            priority = analysis['section_priorities'].get(section_slug, 5.0)
            
            # Section header
            summary_content += f"### {i}. {section_title}\n"
            summary_content += f"**Type**: {section_type.replace('_', ' ').title()} | **Priority**: {priority:.1f} | **Length**: {len(section_content)} chars\n\n"
            
            # Section summary
            if len(section_content) > 100:
                section_summary = self.summarize_section_content(section_content, 100)
                summary_content += f"{section_summary}\n\n"
            else:
                summary_content += f"{section_content[:200]}{'...' if len(section_content) > 200 else ''}\n\n"
            
            # Add metadata for this section
            if section_type == 'api_endpoint':
                api_methods = re.findall(r'\b(GET|POST|PUT|DELETE|PATCH)\b', section_content)
                if api_methods:
                    summary_content += f"*API Methods*: {', '.join(set(api_methods))}\n"
            
            if section_content.count('```') > 0:
                summary_content += f"*Contains*: {section_content.count('```')} code examples\n"
            
            summary_content += "\n---\n\n"
        
        # Add navigation and usage recommendations
        summary_content += "## Navigation Recommendations\n\n"
        
        # High priority sections first
        high_priority = [(s.get('title'), s.get('slug')) for s in sections 
                        if analysis['section_priorities'].get(s.get('slug', 'unknown'), 0) >= 7.0]
        
        if high_priority:
            summary_content += "**Start Here** (High Priority Sections):\n"
            for title, slug in high_priority[:5]:
                summary_content += f"- [{title}]({slug}.md)\n"
            summary_content += "\n"
        
        # Document-specific recommendations
        if analysis['document_type'] == 'api_documentation':
            summary_content += "**API Documentation Path**:\n"
            summary_content += "1. Review authentication and authorization\n"
            summary_content += "2. Explore core endpoints\n"
            summary_content += "3. Study request/response examples\n"
            summary_content += "4. Check error handling and troubleshooting\n\n"
        
        # Add context for different audiences
        summary_content += "## Audience-Specific Guidance\n\n"
        
        if analysis['primary_audience'] == 'developers':
            summary_content += "**For Developers**:\n- Focus on API endpoints and technical implementation details\n- Pay attention to code examples and integration patterns\n- Review authentication and error handling thoroughly\n\n"
        
        if analysis['complexity_level'] == 'high':
            summary_content += "**Complexity Notice**:\nThis document contains advanced technical concepts. Consider:\n- Reviewing prerequisite knowledge\n- Taking time to understand foundational concepts\n- Using the detailed summary for initial overview\n\n"
        
        # Add document statistics
        summary_content += "## Document Statistics\n\n"
        summary_content += f"- **Total Sections**: {len(sections)}\n"
        summary_content += f"- **Average Section Length**: {sum(len(s.get('content', '')) for s in sections) // len(sections) if sections else 0} characters\n"
        summary_content += f"- **Code Examples**: {sum(s.get('content', '').count('```') for s in sections)} blocks\n"
        summary_content += f"- **Estimated Implementation Time**: {'2-4 hours' if analysis['complexity_level'] == 'high' else '1-2 hours'}\n"
        
        return {
            'title': 'Complete Summary',
            'word_count': len(summary_content.split()),
            'target_audience': 'all_users',
            'reading_time': '10-15 minutes',
            'content': summary_content,
            'sections_covered': len(sections),
            'includes_navigation': True,
            'includes_statistics': True,
            'optimization': 'Full context understanding with detailed navigation and implementation guidance'
        }
    
    def create_progressive_disclosure_index(self, executive_summary, detailed_summary, complete_summary):
        """Create index for progressive disclosure navigation"""
        index_content = f"""# Progressive Disclosure Index

## Summary Levels

This document provides three levels of summarization designed for optimal LLM context usage and progressive understanding:

### 🚀 Executive Summary 
**Target**: Quick decision making and initial understanding  
**Length**: ~{executive_summary['word_count']} words  
**Reading Time**: {executive_summary['reading_time']}  
**Best For**: Initial assessment, project scoping, high-level overview  
**Context Window**: Fits in smallest LLM contexts (~1K tokens)

**Key Coverage**: {', '.join(executive_summary.get('key_sections_covered', [])[:3])}

[➤ Read Executive Summary](executive-summary.md)

### 📋 Detailed Summary
**Target**: Comprehensive understanding with key implementation details  
**Length**: ~{detailed_summary['word_count']} words  
**Reading Time**: {detailed_summary['reading_time']}  
**Best For**: Implementation planning, technical review, feature assessment  
**Context Window**: Fits in medium LLM contexts (~3K tokens)

**Sections Covered**: {detailed_summary.get('sections_covered', 0)} high-priority sections  
**Priority Threshold**: {detailed_summary.get('priority_threshold', 6.0):.1f}+

[➤ Read Detailed Summary](detailed-summary.md)

### 📖 Complete Summary
**Target**: Full context understanding with detailed navigation  
**Length**: ~{complete_summary['word_count']} words  
**Reading Time**: {complete_summary['reading_time']}  
**Best For**: Complete implementation, thorough analysis, reference documentation  
**Context Window**: Fits in large LLM contexts (~6K+ tokens)

**Sections Covered**: All {complete_summary.get('sections_covered', 0)} sections with full structure  
**Includes**: Navigation recommendations, audience guidance, implementation statistics

[➤ Read Complete Summary](complete-summary.md)

## Usage Recommendations

### For LLM Context Optimization:

1. **Limited Context (≤2K tokens)**: Use Executive Summary only
2. **Medium Context (2K-5K tokens)**: Use Detailed Summary  
3. **Large Context (≥5K tokens)**: Use Complete Summary
4. **Progressive Analysis**: Start with Executive → Detailed → Complete as needed

### For Different Use Cases:

- **Project Planning**: Executive Summary → specific sections
- **Technical Implementation**: Detailed Summary → relevant detailed sections  
- **Comprehensive Analysis**: Complete Summary → full document
- **Quick Reference**: Executive Summary for decisions, Detailed for specifics

### For Different Audiences:

- **Executives/Managers**: Executive Summary
- **Technical Leads**: Detailed Summary  
- **Developers/Implementers**: Complete Summary + original sections
- **Reviewers**: Progressive disclosure based on review depth needed

## Content Optimization Features

✅ **Token counting** for accurate context management  
✅ **Priority-based selection** of most important content  
✅ **Audience-specific recommendations** for appropriate detail level  
✅ **Progressive navigation** enabling drill-down exploration  
✅ **Context window guidance** for optimal LLM usage  
✅ **Implementation time estimates** for planning purposes

---

*Generated for optimal LLM processing and human understanding*
"""
        
        return {
            'title': 'Progressive Disclosure Index',
            'content': index_content,
            'summary_levels': 3,
            'optimization_features': 6,
            'context_guidance': True
        }
    
    def save_summary_files(self, summaries_dir, executive_summary, detailed_summary, complete_summary, disclosure_index):
        """Save all summary files with appropriate formatting"""
        
        # Save executive summary
        exec_path = summaries_dir / "executive-summary.md"
        with open(exec_path, 'w', encoding='utf-8') as f:
            f.write(executive_summary['content'])
        
        # Save detailed summary
        detailed_path = summaries_dir / "detailed-summary.md"
        with open(detailed_path, 'w', encoding='utf-8') as f:
            f.write(detailed_summary['content'])
        
        # Save complete summary
        complete_path = summaries_dir / "complete-summary.md"
        with open(complete_path, 'w', encoding='utf-8') as f:
            f.write(complete_summary['content'])
        
        # Save progressive disclosure index
        index_path = summaries_dir / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(disclosure_index['content'])
        
        # Save machine-readable summary metadata
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'summary_levels': {
                'executive': {
                    'file': 'executive-summary.md',
                    'word_count': executive_summary['word_count'],
                    'target_audience': executive_summary['target_audience'],
                    'reading_time': executive_summary['reading_time'],
                    'optimization': executive_summary['optimization']
                },
                'detailed': {
                    'file': 'detailed-summary.md',
                    'word_count': detailed_summary['word_count'],
                    'sections_covered': detailed_summary['sections_covered'],
                    'reading_time': detailed_summary['reading_time'],
                    'optimization': detailed_summary['optimization']
                },
                'complete': {
                    'file': 'complete-summary.md',
                    'word_count': complete_summary['word_count'],
                    'sections_covered': complete_summary['sections_covered'],
                    'reading_time': complete_summary['reading_time'],
                    'optimization': complete_summary['optimization']
                }
            },
            'progressive_disclosure': {
                'enabled': True,
                'levels': 3,
                'context_optimization': True
            }
        }
        
        metadata_path = summaries_dir / "summaries-metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return [str(exec_path), str(detailed_path), str(complete_path), str(index_path)]
    
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
    parser.add_argument('--generate-concept-map', action='store_true', default=True,
                      help='Generate concept map and glossary with technical terms and relationships (default: True)')
    parser.add_argument('--resolve-cross-references', action='store_true', default=True,
                      help='Detect and resolve cross-references to create navigable markdown links (default: True)')
    parser.add_argument('--generate-summaries', action='store_true', default=True,
                      help='Generate multi-level summaries for progressive disclosure and context optimization (default: True)')
    
    args = parser.parse_args()
    
    converter = PDFToMarkdownConverter(
        args.pdf_path,
        args.output_dir,
        args.preserve_tables,
        args.extract_images,
        args.enable_chunking,
        args.structured_tables,
        args.generate_concept_map,
        args.resolve_cross_references,
        args.generate_summaries
    )
    
    output_file = converter.convert()
    print(f"Conversion complete: {output_file}")

if __name__ == "__main__":
    main()
