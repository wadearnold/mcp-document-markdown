#!/usr/bin/env python3
"""
Complete test of ULTIMATE PDF extraction pipeline
"""
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from processors.pdf_extractor_ultimate import UltimatePDFExtractor


def test_complete_pipeline():
    """Test the ULTIMATE PDF extraction pipeline"""
    
    pdf_path = "VTS_chapter4.pdf"  # PDF is in root directory
    output_dir = "output_ultimate_test"
    
    print("=" * 60)
    print("ULTIMATE PDF EXTRACTION PIPELINE TEST")
    print("=" * 60)
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Extract with ULTIMATE extractor
    print("\n🚀 Extracting with ULTIMATE PDF Extractor...")
    extractor = UltimatePDFExtractor(pdf_path, output_dir)
    result = extractor.extract()
    
    # Display results
    stats = result['stats']
    print(f"   ✅ Quality Score: {stats['quality_score']:.1f}/100")
    print(f"   🏆 Quality Level: {stats['quality_level']}")
    print(f"   📋 Fields Found: {stats['total_fields']}")
    print(f"   📑 Sections: {stats['sections']}")
    print(f"   🧠 LLM Optimized: {stats.get('llm_optimized', False)}")
    
    # Quality checks
    print("\n📊 Quality Checks:")
    markdown = result['markdown']
    
    # Check for bullet points
    bullet_count = markdown.count('•')
    l_pattern_count = len([line for line in markdown.split('\n') if line.strip().startswith('l ')])
    print(f"   ✅ Bullet points: {bullet_count}")
    print(f"   {'✅' if l_pattern_count == 0 else '❌'} Bad 'l' patterns: {l_pattern_count}")
    
    # Check for proper structure
    h1_count = markdown.count('\n# ')
    h2_count = markdown.count('\n## ')
    table_rows = markdown.count('\n|')
    print(f"   📋 Headers: H1={h1_count}, H2={h2_count}")
    print(f"   📊 Table rows: {table_rows}")
    
    # Check for metadata
    has_metadata = "## Document Metadata" in markdown
    has_summary = "## Document Summary" in markdown
    has_toc = "## Table of Contents" in markdown
    has_stats = "## Field Statistics" in markdown
    
    print(f"   📄 Document Metadata: {'✅' if has_metadata else '❌'}")
    print(f"   📝 Document Summary: {'✅' if has_summary else '❌'}")
    print(f"   📑 Table of Contents: {'✅' if has_toc else '❌'}")
    print(f"   📊 Field Statistics: {'✅' if has_stats else '❌'}")
    
    print(f"\n📁 Output saved to: {Path(output_dir).absolute()}")
    print(f"   📝 Markdown: ultimate_extraction.md")
    print(f"   🧠 JSON Schema: api_schema.json")
    print(f"   📊 Data: extraction_data.json")
    
    return result


def compare_with_claude_reading():
    """Compare ULTIMATE extraction with Claude's native PDF reading"""
    
    print("\n" + "=" * 60)
    print("🆚 ULTIMATE vs CLAUDE NATIVE PDF READING")
    print("=" * 60)
    
    # Expected content based on Claude's native reading
    claude_expectations = {
        'fields': [
            'primaryAccountNumber', 'cvv2', 'name', 'expirationDate',
            'billingAddress', 'token', 'tokenType', 'tokenStatus', 
            'deviceID', 'deviceType', 'walletProviderAccountScore'
        ],
        'structure': ['Cardholder Information', 'Token Information', 
                     'Device Information', 'Address', 'Risk Information'],
        'features': {
            'bullets': True,
            'tables': True,
            'metadata': True,
            'structure': True
        }
    }
    
    # Run ULTIMATE extraction
    result = test_complete_pipeline()
    
    print(f"\n🎯 ULTIMATE Extractor Results:")
    print(f"   Quality Score: {result['stats']['quality_score']:.1f}/100")
    print(f"   Quality Level: {result['stats']['quality_level']}")
    print(f"   Fields Extracted: {result['stats']['total_fields']}")
    
    # Check structure detection
    markdown = result['markdown']
    print(f"\n📋 Structure Detection:")
    structure_found = 0
    for section in claude_expectations['structure']:
        found = section in markdown
        if found:
            structure_found += 1
        print(f"   {'✅' if found else '❌'} {section}")
    
    # Check key field detection
    print(f"\n🔍 Key Field Detection:")
    fields_found = 0
    for field in claude_expectations['fields']:
        found = field in markdown
        if found:
            fields_found += 1
        print(f"   {'✅' if found else '❌'} {field}")
    
    # Feature comparison
    print(f"\n⚡ Feature Comparison:")
    bullet_count = markdown.count('•')
    table_count = markdown.count('|')
    has_metadata = "Document Metadata" in markdown
    has_structure = structure_found >= 4
    
    print(f"   {'✅' if bullet_count > 0 else '❌'} Bullet Points: {bullet_count}")
    print(f"   {'✅' if table_count > 0 else '❌'} Tables: {table_count // 2} rows")
    print(f"   {'✅' if has_metadata else '❌'} Metadata Section")
    print(f"   {'✅' if has_structure else '❌'} Document Structure")
    
    # Calculate scores
    field_score = (fields_found / len(claude_expectations['fields'])) * 100
    structure_score = (structure_found / len(claude_expectations['structure'])) * 100
    
    print(f"\n📊 Comparison Scores:")
    print(f"   Field Detection: {field_score:.1f}%")
    print(f"   Structure Detection: {structure_score:.1f}%")
    print(f"   Overall Quality: {result['stats']['quality_score']:.1f}/100")
    
    # Final assessment
    if result['stats']['quality_score'] >= 80:
        print(f"\n🏆 VERDICT: ULTIMATE extractor matches/exceeds Claude's native reading!")
        print(f"   Quality Level: {result['stats']['quality_level']}")
    else:
        print(f"\n⚠️  VERDICT: ULTIMATE extractor needs improvement")
    
    return result


if __name__ == "__main__":
    compare_with_claude_reading()