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
