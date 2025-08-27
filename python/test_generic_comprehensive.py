#!/usr/bin/env python3
"""
Comprehensive test of generic PDF extractor to validate it works
for various PDF document types and patterns
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from processors.pdf_extractor_generic import extract_pdf, GenericPDFExtractor


def test_generic_bullet_patterns():
    """Test various bullet patterns that might appear in different PDFs"""
    
    test_cases = [
        {
            "name": "VTS-style split bullets",
            "text": """Field: tokenType
Format: It is one of the following values:
l
SECURE_ELEMENT
l
HCE
l
CARD_ON_FILE"""
        },
        {
            "name": "Standard dash bullets", 
            "text": """Available options include:
- Option A: First choice
- Option B: Second choice
- Option C: Third choice"""
        },
        {
            "name": "Asterisk bullets",
            "text": """Requirements:
* Must be valid
* Must be active
* Must be authenticated"""
        },
        {
            "name": "Mixed content",
            "text": """Configuration settings:
apiEndpoint: https://api.example.com/v1
timeout: 30
retries: 3
The following modes are supported:
l
DEVELOPMENT
l
PRODUCTION
l
TESTING"""
        }
    ]
    
    extractor = GenericPDFExtractor()
    
    print("=== TESTING BULLET PATTERN RECOGNITION ===\n")
    
    for test_case in test_cases:
        print(f"--- {test_case['name']} ---")
        print("INPUT:")
        print(test_case['text'])
        
        processed = extractor.process_text(test_case['text'])
        print("\nOUTPUT:")
        print(processed)
        
        # Count bullets
        bullet_count = processed.count('•')
        print(f"\nBullets detected: {bullet_count}")
        
        if bullet_count > 0:
            bullet_lines = [line.strip() for line in processed.split('\n') if line.strip().startswith('•')]
            for bullet in bullet_lines:
                print(f"  {bullet}")
        
        print("\n" + "="*60 + "\n")


def test_field_extraction_patterns():
    """Test field extraction with different document styles"""
    
    test_cases = [
        {
            "name": "API Documentation Style",
            "text": """
userId: (Required) The unique identifier for the user
Format: String; max length 50 characters
Example: "user_12345"

accountType: (Optional) Type of account
Format: It is one of the following values:
• PERSONAL
• BUSINESS
• ENTERPRISE

createdDate: (Conditional) Account creation timestamp
Format: ISO 8601 datetime
Example: "2024-01-15T10:30:00Z"
"""
        },
        {
            "name": "Configuration File Style", 
            "text": """
# Database Configuration
host: localhost
port: 5432
database: myapp_prod
username: dbuser
ssl_mode: require

# Cache Settings  
redis_host: redis.example.com
redis_port: 6379
ttl: 3600
"""
        },
        {
            "name": "Table-like Structure",
            "text": """
| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| id | integer | Yes | Primary key identifier |
| name | string | Yes | User display name |
| email | string | No | Contact email address |
| status | enum | Yes | Account status (active/inactive) |
"""
        }
    ]
    
    print("=== TESTING FIELD EXTRACTION PATTERNS ===\n")
    
    for test_case in test_cases:
        print(f"--- {test_case['name']} ---")
        
        extractor = GenericPDFExtractor()
        
        # Simulate full extraction process
        processed_text = extractor.process_text(test_case['text'])
        structure = extractor.detect_document_structure(processed_text)
        fields = extractor.extract_fields(processed_text, structure)
        
        print(f"Document Type: {structure['document_type']}")
        print(f"Fields Extracted: {len(fields)}")
        print(f"Has Tables: {structure['has_tables']}")
        print(f"Has Lists: {structure['has_lists']}")
        
        print("\nExtracted Fields:")
        for i, field in enumerate(fields[:5]):  # Show first 5
            print(f"  {i+1}. {field.name}")
            print(f"     Type: {field.field_type}")
            print(f"     Content: {field.content[:100]}..." if len(field.content) > 100 else f"     Content: {field.content}")
            if field.metadata:
                print(f"     Metadata: {field.metadata}")
        
        if len(fields) > 5:
            print(f"  ... and {len(fields) - 5} more")
        
        print("\n" + "="*60 + "\n")


def test_with_vts_pdf():
    """Test the generic extractor with actual VTS PDF"""
    
    vts_pdf_path = "/Users/wadearnold/Documents/GitHub/wadearnold/mcp-document-markdown/VTS_chapter4.pdf"
    
    if not Path(vts_pdf_path).exists():
        print("⚠️  VTS PDF not found, skipping real PDF test")
        return
    
    print("=== TESTING WITH ACTUAL VTS PDF ===\n")
    
    # Test with standard config
    print("--- Standard Configuration ---")
    results = extract_pdf(vts_pdf_path)
    
    print(f"Document Type: {results['metadata']['document_type']}")
    print(f"Total Fields: {results['metadata']['total_fields']}")
    print(f"Field Types: {list(results['summary']['field_types'].keys())}")
    
    # Count bullets in processed text
    bullet_count = results['processed_text'].count('•')
    print(f"Bullets in processed text: {bullet_count}")
    
    # Test with enhanced config for API docs
    print("\n--- Enhanced API Config ---")
    api_config = {
        'bullet_indicators': [
            'following values', 'following apis', 'includes', 'types',
            'one of the following', 'it is one of', 'format: it is',
            'examples', 'such as', 'options', 'values', 'apis'
        ]
    }
    
    results_enhanced = extract_pdf(vts_pdf_path, api_config)
    
    print(f"Enhanced - Total Fields: {results_enhanced['metadata']['total_fields']}")
    enhanced_bullets = results_enhanced['processed_text'].count('•')
    print(f"Enhanced - Bullets: {enhanced_bullets}")
    
    print(f"\nImprovement: {enhanced_bullets - bullet_count} additional bullets detected")
    
    # Show sample fields with bullets
    fields_with_bullets = [f for f in results_enhanced['fields'] if '•' in f['content']]
    print(f"Fields containing bullets: {len(fields_with_bullets)}")
    
    if fields_with_bullets:
        print("\nSample field with bullets:")
        field = fields_with_bullets[0]
        print(f"Name: {field['name']}")
        lines = field['content'].split('\n')
        bullet_lines = [line for line in lines if line.strip().startswith('•')]
        for line in bullet_lines[:3]:
            print(f"  {line.strip()}")
    
    print("\n" + "="*60 + "\n")


def main():
    """Run all tests"""
    print("🧪 COMPREHENSIVE GENERIC PDF EXTRACTOR TESTS\n")
    
    test_generic_bullet_patterns()
    test_field_extraction_patterns() 
    test_with_vts_pdf()
    
    print("✅ All tests completed!")


if __name__ == "__main__":
    main()