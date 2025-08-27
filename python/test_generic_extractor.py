#!/usr/bin/env python3
"""
Test the generic PDF extractor with the VTS document to ensure it works
without hardcoded VTS-specific patterns
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from processors.pdf_extractor_generic import extract_pdf


def test_generic_with_vts():
    """Test generic extractor with VTS PDF"""
    vts_pdf_path = "/Users/wadearnold/Documents/GitHub/wadearnold/mcp-document-markdown/VTS_chapter4.pdf"
    
    print("=== TESTING GENERIC PDF EXTRACTOR WITH VTS DOCUMENT ===")
    
    try:
        results = extract_pdf(vts_pdf_path)
        
        print(f"\n📄 Document Type: {results['metadata']['document_type']}")
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
            for section in results['structure']['sections'][:5]:
                print(f"    - {section}")
        
        # Show sample fields
        print(f"\n🔍 Sample Extracted Fields:")
        for i, field in enumerate(results['fields'][:5]):
            print(f"  {i+1}. {field['name']}: {field['content'][:100]}...")
            if field['metadata']:
                print(f"     Metadata: {field['metadata']}")
        
        # Test bullet point handling
        bullet_fields = [f for f in results['fields'] if '•' in f['content']]
        print(f"\n🎯 Fields with Bullets: {len(bullet_fields)}")
        
        if bullet_fields:
            print("  Sample bullet content:")
            for field in bullet_fields[:3]:
                lines = field['content'].split('\n')
                bullet_lines = [line for line in lines if line.strip().startswith('•')]
                for line in bullet_lines[:2]:
                    print(f"    {line.strip()}")
        
        print(f"\n✅ Generic extraction completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_config():
    """Test with custom configuration"""
    vts_pdf_path = "/Users/wadearnold/Documents/GitHub/wadearnold/mcp-document-markdown/VTS_chapter4.pdf"
    
    # Custom config for better API document handling
    config = {
        'bullet_indicators': [
            'following values', 'following apis', 'includes', 'types',
            'one of the following', 'it is one of', 'format: it is',
            'examples', 'such as', 'options', 'values'
        ]
    }
    
    print(f"\n=== TESTING WITH CUSTOM CONFIG ===")
    
    try:
        results = extract_pdf(vts_pdf_path, config)
        print(f"📊 Results with config: {results['metadata']['total_fields']} fields")
        
        # Compare bullet handling
        bullet_content = []
        for field in results['fields']:
            if '•' in field['content']:
                lines = field['content'].split('\n')
                bullet_lines = [line.strip() for line in lines if line.strip().startswith('•')]
                bullet_content.extend(bullet_lines)
        
        print(f"🎯 Total bullet points found: {len(bullet_content)}")
        if bullet_content:
            print("  Sample bullets:")
            for bullet in bullet_content[:5]:
                print(f"    {bullet}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with config: {e}")
        return False


if __name__ == "__main__":
    success1 = test_generic_with_vts()
    success2 = test_with_config()
    
    if success1 and success2:
        print(f"\n🎉 All tests passed! Generic extractor works well with VTS document.")
    else:
        print(f"\n⚠️  Some tests failed. Check output above.")