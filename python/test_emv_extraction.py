#!/usr/bin/env python3
"""
Test the generic PDF extractor with EMV v4.4 Book 4 Appendix
Compare results with Claude's analysis capabilities
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from processors.pdf_extractor_generic import extract_pdf
import json


def test_emv_extraction():
    """Test generic extraction with EMV PDF"""
    
    emv_pdf_path = "/Users/wadearnold/Documents/GitHub/wadearnold/mcp-document-markdown/EMV_v4.4_Book_4_Appendix.pdf"
    
    if not Path(emv_pdf_path).exists():
        print("❌ EMV PDF not found at expected location")
        return False
    
    print("=== TESTING GENERIC EXTRACTOR WITH EMV v4.4 BOOK 4 APPENDIX ===\n")
    
    try:
        # Test with standard config
        print("--- Standard Configuration ---")
        results = extract_pdf(emv_pdf_path)
        
        print(f"📄 Document Type: {results['metadata']['document_type']}")
        print(f"🔢 Total Fields: {results['metadata']['total_fields']}")
        print(f"📝 Total Lines: {results['summary']['total_lines']}")
        print(f"📊 Has Tables: {results['metadata']['has_tables']}")
        print(f"📋 Has Lists: {results['metadata']['has_lists']}")
        
        print(f"\n🎯 Field Types Distribution:")
        for field_type, count in results['summary']['field_types'].items():
            print(f"  - {field_type}: {count}")
        
        print(f"\n📑 Sections Detected: {len(results['structure']['sections'])}")
        if results['structure']['sections']:
            print("  Sample sections:")
            for section in results['structure']['sections'][:10]:
                print(f"    - {section}")
        
        # Count bullets in processed text
        bullet_count = results['processed_text'].count('•')
        print(f"\n🎯 Bullets in processed text: {bullet_count}")
        
        # Show sample fields
        print(f"\n🔍 Sample Extracted Fields:")
        for i, field in enumerate(results['fields'][:10]):
            print(f"  {i+1}. Name: {field['name']}")
            print(f"     Type: {field['type']}")
            content_preview = field['content'][:100] + "..." if len(field['content']) > 100 else field['content']
            print(f"     Content: {content_preview}")
            if field['metadata']:
                print(f"     Metadata: {field['metadata']}")
            print()
        
        # Test with EMV-optimized config
        print("\n--- EMV-Optimized Configuration ---")
        emv_config = {
            'bullet_indicators': [
                'following', 'includes', 'types', 'values', 'options',
                'data elements', 'tags', 'formats', 'requirements',
                'specifications', 'shall', 'must', 'may'
            ]
        }
        
        results_emv = extract_pdf(emv_pdf_path, emv_config)
        
        print(f"📊 EMV-optimized - Total Fields: {results_emv['metadata']['total_fields']}")
        emv_bullets = results_emv['processed_text'].count('•')
        print(f"🎯 EMV-optimized - Bullets: {emv_bullets}")
        
        improvement = emv_bullets - bullet_count
        if improvement > 0:
            print(f"✅ Improvement: {improvement} additional bullets detected with EMV config")
        else:
            print(f"📊 No additional bullets with EMV config")
        
        # Look for EMV-specific patterns
        print(f"\n🔍 EMV-Specific Analysis:")
        emv_patterns = [
            'tag', 'length', 'value', 'TLV', 'data element',
            'mandatory', 'optional', 'conditional', 'format',
            'encoding', 'binary', 'numeric', 'alphanumeric'
        ]
        
        pattern_counts = {}
        for pattern in emv_patterns:
            count = results_emv['processed_text'].lower().count(pattern)
            if count > 0:
                pattern_counts[pattern] = count
        
        if pattern_counts:
            print("  EMV patterns found:")
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {pattern}: {count} occurrences")
        
        # Show fields with EMV-specific content
        emv_fields = []
        for field in results_emv['fields']:
            if any(pattern in field['content'].lower() for pattern in emv_patterns):
                emv_fields.append(field)
        
        print(f"\n📋 Fields with EMV-specific content: {len(emv_fields)}")
        for i, field in enumerate(emv_fields[:5]):
            print(f"  {i+1}. {field['name']}: {field['content'][:80]}...")
        
        # Save detailed results for comparison with Claude
        output_file = "emv_extraction_results.json"
        detailed_results = {
            'standard_config': {
                'total_fields': results['metadata']['total_fields'],
                'document_type': results['metadata']['document_type'],
                'bullet_count': bullet_count,
                'field_types': results['summary']['field_types'],
                'sections': results['structure']['sections'][:20],  # First 20 sections
                'sample_fields': [
                    {
                        'name': field['name'],
                        'type': field['type'],
                        'content': field['content'][:200]  # First 200 chars
                    } for field in results['fields'][:20]
                ]
            },
            'emv_optimized': {
                'total_fields': results_emv['metadata']['total_fields'],
                'bullet_count': emv_bullets,
                'emv_patterns': pattern_counts,
                'emv_specific_fields': len(emv_fields)
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        print("📊 Ready for comparison with Claude's analysis!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during EMV extraction: {e}")
        import traceback
        traceback.print_exc()
        return False


def analyze_extraction_quality():
    """Analyze the quality of extraction compared to expected EMV content"""
    
    print("\n=== EMV EXTRACTION QUALITY ANALYSIS ===\n")
    
    # Expected EMV content types
    expected_elements = [
        "Data elements with tags",
        "TLV structure descriptions", 
        "Format specifications (binary, numeric, alphanumeric)",
        "Length specifications",
        "Mandatory/Optional/Conditional indicators",
        "Encoding rules",
        "Usage examples",
        "Cross-references between elements"
    ]
    
    print("Expected EMV document elements:")
    for i, element in enumerate(expected_elements, 1):
        print(f"  {i}. {element}")
    
    print(f"\n💡 Key questions for Claude comparison:")
    print("1. Does Python extraction capture TLV structure properly?")
    print("2. Are data element tags and descriptions linked correctly?") 
    print("3. Does bullet detection work with EMV specification format?")
    print("4. Are format specifications (binary/numeric/alphanumeric) detected?")
    print("5. Does field categorization make sense for EMV content?")
    print("6. What EMV-specific patterns does Claude see that Python misses?")


if __name__ == "__main__":
    print("🧪 EMV v4.4 Book 4 Appendix - Generic PDF Extraction Test\n")
    
    success = test_emv_extraction()
    
    if success:
        analyze_extraction_quality()
        print(f"\n✅ EMV extraction test completed successfully!")
        print("📋 Next step: Compare these results with Claude's analysis of the same PDF")
    else:
        print(f"\n❌ EMV extraction test failed")
    
    print(f"\n" + "="*60)
    print("READY FOR CLAUDE COMPARISON")  
    print("="*60)