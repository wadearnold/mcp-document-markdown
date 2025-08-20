// python_scripts.go - Python scripts embedded in Go

package main

// pythonConvertScript is the main PDF to Markdown conversion script
const pythonConvertScript = `
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
        
        # Save to file
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
        """Identify headers and structure in text"""
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                processed_lines.append('')
                continue
            
            # Detect potential headers
            if self.is_header(line):
                # Determine header level
                level = self.determine_header_level(line)
                processed_lines.append(f"{'#' * level} {line}")
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def is_header(self, line):
        """Detect if a line is likely a header"""
        # All caps and short
        if line.isupper() and len(line) < 100:
            return True
        
        # Numbered sections
        if re.match(r'^(\d+\.)+\s+\w+', line):
            return True
        
        # Chapter patterns
        if re.match(r'^(Chapter|Section|Part)\s+\d+', line, re.IGNORECASE):
            return True
        
        return False
    
    def determine_header_level(self, line):
        """Determine the header level (1-6)"""
        if re.match(r'^(Chapter|Part)\s+', line, re.IGNORECASE):
            return 1
        elif re.match(r'^(Section|\d+\.)\s+', line, re.IGNORECASE):
            return 2
        elif re.match(r'^\d+\.\d+\.?\s+', line):
            return 3
        elif line.isupper():
            return 2
        else:
            return 3
    
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
`

// pythonAnalyzeScript analyzes PDF structure
const pythonAnalyzeScript = `
import sys
import pypdf
import pdfplumber
import json

def analyze_pdf(pdf_path):
    """Analyze PDF structure and return information"""
    analysis = {
        'pages': 0,
        'has_toc': False,
        'has_tables': False,
        'has_images': False,
        'chapters': [],
        'metadata': {},
        'table_count': 0,
        'image_count': 0
    }
    
    # Analyze with pypdf
    try:
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            analysis['pages'] = len(reader.pages)
            
            # Check for TOC
            if reader.outline:
                analysis['has_toc'] = True
                analysis['chapters'] = extract_chapter_info(reader.outline)
            
            # Get metadata
            if reader.metadata:
                analysis['metadata'] = {
                    'title': reader.metadata.get('/Title', ''),
                    'author': reader.metadata.get('/Author', ''),
                    'subject': reader.metadata.get('/Subject', ''),
                    'creator': reader.metadata.get('/Creator', ''),
                }
            
            # Check for images
            for page in reader.pages:
                if '/XObject' in page['/Resources']:
                    xObject = page['/Resources']['/XObject'].get_object()
                    for obj in xObject:
                        if xObject[obj]['/Subtype'] == '/Image':
                            analysis['image_count'] += 1
                            analysis['has_images'] = True
    
    except Exception as e:
        print(f"Error with pypdf analysis: {e}", file=sys.stderr)
    
    # Analyze tables with pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    analysis['has_tables'] = True
                    analysis['table_count'] += len(tables)
    
    except Exception as e:
        print(f"Error with pdfplumber analysis: {e}", file=sys.stderr)
    
    return analysis

def extract_chapter_info(outline, chapters=None, level=0):
    """Extract chapter information from outline"""
    if chapters is None:
        chapters = []
    
    for item in outline:
        if isinstance(item, list):
            extract_chapter_info(item, chapters, level + 1)
        else:
            chapters.append({
                'title': item.title,
                'level': level
            })
    
    return chapters

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <pdf_path>", file=sys.stderr)
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    analysis = analyze_pdf(pdf_path)
    
    # Format output
    print(f"PDF Analysis for: {pdf_path}")
    print(f"Pages: {analysis['pages']}")
    print(f"Has Table of Contents: {analysis['has_toc']}")
    print(f"Has Tables: {analysis['has_tables']} ({analysis['table_count']} tables)")
    print(f"Has Images: {analysis['has_images']} ({analysis['image_count']} images)")
    
    if analysis['metadata']:
        print("\nMetadata:")
        for key, value in analysis['metadata'].items():
            if value:
                print(f"  {key}: {value}")
    
    if analysis['chapters']:
        print(f"\nChapters/Sections ({len(analysis['chapters'])} items):")
        for chapter in analysis['chapters'][:10]:  # Show first 10
            indent = "  " * chapter['level']
            print(f"{indent}- {chapter['title']}")
        if len(analysis['chapters']) > 10:
            print(f"  ... and {len(analysis['chapters']) - 10} more")
    
    # Output JSON for parsing
    print("\n---JSON---")
    print(json.dumps(analysis))

if __name__ == "__main__":
    main()
`