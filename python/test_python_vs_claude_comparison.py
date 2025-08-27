#!/usr/bin/env python3
"""
Python vs Claude API Comparison Test
Compare our improved Python extraction with Claude's direct PDF analysis
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from processors.pdf_extractor_generic import extract_pdf
import json
import time
from datetime import datetime


def run_python_extraction():
    """Run our improved Python extraction on EMV PDF"""
    
    emv_pdf_path = "/Users/wadearnold/Documents/GitHub/wadearnold/mcp-document-markdown/EMV_v4.4_Book_4_Appendix.pdf"
    
    if not Path(emv_pdf_path).exists():
        print("❌ EMV PDF not found at expected location")
        return None
    
    print("=== PYTHON EXTRACTION (IMPROVED VERSION) ===\n")
    
    start_time = time.time()
    
    try:
        # Run extraction with our improved generic extractor
        results = extract_pdf(emv_pdf_path)
        
        extraction_time = time.time() - start_time
        
        # Analyze results in detail
        python_analysis = {
            'timestamp': datetime.now().isoformat(),
            'extraction_time_seconds': round(extraction_time, 2),
            'basic_metrics': {
                'document_type': results['metadata']['document_type'],
                'total_fields': results['metadata']['total_fields'],
                'total_lines': results['summary']['total_lines'],
                'has_tables': results['metadata']['has_tables'],
                'has_lists': results['metadata']['has_lists'],
                'sections_detected': len(results['structure']['sections'])
            },
            'field_analysis': {
                'field_types': results['summary']['field_types'],
                'fields_with_metadata': len([f for f in results['fields'] if f['metadata']]),
                'fields_with_cross_refs': len([f for f in results['fields'] if f['metadata'].get('cross_references')]),
                'fields_with_section_context': len([f for f in results['fields'] if f['metadata'].get('section')])
            },
            'content_patterns': {
                'emv_data_elements': results['processed_text'].lower().count('data element'),
                'table_references': results['processed_text'].lower().count('table'),
                'format_specifications': results['processed_text'].lower().count('format'),
                'terminal_references': results['processed_text'].lower().count('terminal'),
                'tag_references': results['processed_text'].lower().count('tag'),
                'bullets_detected': results['processed_text'].count('•')
            },
            'sample_extractions': {
                'first_5_fields': [
                    {
                        'name': field['name'],
                        'type': field['type'], 
                        'content_preview': field['content'][:100] + ('...' if len(field['content']) > 100 else ''),
                        'has_metadata': bool(field['metadata'])
                    } for field in results['fields'][:5]
                ],
                'fields_with_rich_metadata': [
                    {
                        'name': field['name'],
                        'metadata_keys': list(field['metadata'].keys())
                    } for field in results['fields'] if len(field['metadata']) > 1
                ][:5]
            }
        }
        
        # Print summary
        print(f"⏱️ Extraction Time: {extraction_time:.2f} seconds")
        print(f"📄 Document Type: {results['metadata']['document_type']}")
        print(f"🔢 Total Fields: {results['metadata']['total_fields']}")
        print(f"📊 Has Tables: {results['metadata']['has_tables']}")
        print(f"📑 Sections: {len(results['structure']['sections'])}")
        
        print(f"\n🔍 Enhanced Analysis:")
        print(f"  - Fields with metadata: {python_analysis['field_analysis']['fields_with_metadata']}")
        print(f"  - Fields with cross-refs: {python_analysis['field_analysis']['fields_with_cross_refs']}")
        print(f"  - Fields with section context: {python_analysis['field_analysis']['fields_with_section_context']}")
        
        print(f"\n📋 EMV-Specific Patterns:")
        for pattern, count in python_analysis['content_patterns'].items():
            print(f"  - {pattern.replace('_', ' ').title()}: {count}")
        
        print(f"\n📝 Sample Field Extractions:")
        for i, field in enumerate(python_analysis['sample_extractions']['first_5_fields'], 1):
            print(f"  {i}. {field['name']}: {field['content_preview']}")
            print(f"     Type: {field['type']}, Has Metadata: {field['has_metadata']}")
        
        # Save detailed results
        with open("python_extraction_detailed.json", "w") as f:
            json.dump(python_analysis, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: python_extraction_detailed.json")
        
        return python_analysis
        
    except Exception as e:
        print(f"❌ Python extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_claude_comparison_template():
    """Create a structured template for Claude API comparison"""
    
    print("\n=== CLAUDE API COMPARISON TEMPLATE ===\n")
    
    claude_template = {
        'instructions': """
To compare with Python extraction, please analyze the EMV_v4.4_Book_4_Appendix.pdf and provide:

1. BASIC METRICS:
   - Document classification (structured_fields, tabular, narrative, etc.)
   - Estimated total extractable fields/data points
   - Number of tables identified
   - Number of distinct sections
   - Presence of bullet lists or numbered lists

2. STRUCTURAL ANALYSIS:
   - Section hierarchy (numbered sections like 11.1, 11.2)
   - Table structures and their contents
   - Cross-references between sections
   - Data element relationships

3. EMV-SPECIFIC CONTENT:
   - Data element definitions and their tags
   - Terminal capability specifications
   - Message format descriptions
   - Technical format notations (like "n 6", "an 8")
   - Cardholder/Attendant interface requirements

4. CONTENT QUALITY:
   - How well can you identify field names vs descriptions?
   - Can you map data elements to their specifications?
   - Are cross-references and dependencies clear?
   - How much context is preserved in extraction?

5. EXTRACTION CHALLENGES:
   - What aspects of the document are hardest to process?
   - Which structural elements might be missed by automated extraction?
   - What domain knowledge helps in understanding content?
   
Please provide specific examples and quantitative measures where possible.
""",
        'comparison_metrics': [
            'Field extraction accuracy',
            'Table structure recognition',
            'Section hierarchy detection', 
            'Cross-reference identification',
            'Technical format parsing',
            'Context preservation',
            'Processing speed',
            'Content completeness'
        ]
    }
    
    # Save template
    with open("claude_comparison_template.json", "w") as f:
        json.dump(claude_template, f, indent=2)
    
    print("📋 Claude comparison template created:")
    print("   1. Use the EMV PDF with Claude API")
    print("   2. Follow the instructions in claude_comparison_template.json")
    print("   3. Collect Claude's analysis results")
    print("   4. Run comparison analysis")
    
    print(f"\n💡 Instructions for Claude API:")
    print(claude_template['instructions'])
    
    return claude_template


def main():
    """Run the Python vs Claude comparison test"""
    
    print("🔬 PYTHON vs CLAUDE API COMPARISON TEST")
    print("=" * 50)
    
    # Run Python extraction
    python_results = run_python_extraction()
    
    if not python_results:
        print("❌ Python extraction failed, cannot proceed with comparison")
        return False
    
    # Create Claude comparison template
    claude_template = create_claude_comparison_template()
    
    print(f"\n🔄 NEXT STEPS:")
    print("1. ✅ Python extraction completed")
    print("2. 📋 Claude comparison template ready")  
    print("3. 🤖 Run Claude API analysis using the template")
    print("4. 📊 Compare results using the metrics framework")
    
    print(f"\n📁 Files Generated:")
    print("   - python_extraction_detailed.json (Python results)")
    print("   - claude_comparison_template.json (Claude instructions)")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)