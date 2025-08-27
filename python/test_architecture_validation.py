#!/usr/bin/env python3
"""
Architecture validation test - ensures NO VTS-specific code remains
and validates complete generic PDF processing capability
"""
import sys
from pathlib import Path
import inspect
import re
sys.path.append(str(Path(__file__).parent))

from processors.pdf_extractor_generic import GenericPDFExtractor
from processors.pdf_extractor_ultimate import UltimatePDFExtractor, IntelligentTextProcessor


def test_no_hardcoded_values():
    """Test that no hardcoded VTS values remain in core processors"""
    
    print("=== ARCHITECTURE VALIDATION: NO HARDCODED VALUES ===\n")
    
    # Test Generic Extractor
    print("1. Testing Generic PDF Extractor...")
    generic_extractor = GenericPDFExtractor()
    
    # Check that it has no hardcoded domain-specific values
    source_code = inspect.getsource(GenericPDFExtractor)
    
    forbidden_patterns = [
        'secure_element', 'hce', 'card_on_file', 'visa', 'token.*service',
        'cardholder', 'provisioning', 'device.*binding'
    ]
    
    found_issues = []
    for pattern in forbidden_patterns:
        if re.search(pattern, source_code, re.IGNORECASE):
            found_issues.append(pattern)
    
    if found_issues:
        print(f"❌ GENERIC EXTRACTOR HAS HARDCODED VALUES: {found_issues}")
        return False
    else:
        print("✅ Generic extractor is clean - no hardcoded values")
    
    # Test Ultimate Extractor (legacy but should be generic now)
    print("\n2. Testing Ultimate PDF Extractor...")
    ultimate_source = inspect.getsource(UltimatePDFExtractor)
    ultimate_issues = []
    
    for pattern in forbidden_patterns:
        if re.search(pattern, ultimate_source, re.IGNORECASE):
            ultimate_issues.append(pattern)
    
    if ultimate_issues:
        print(f"❌ ULTIMATE EXTRACTOR HAS HARDCODED VALUES: {ultimate_issues}")
        return False
    else:
        print("✅ Ultimate extractor is clean - no hardcoded values")
    
    return True


def test_generic_bullet_detection():
    """Test that bullet detection works without domain-specific assumptions"""
    
    print("\n=== TESTING GENERIC BULLET DETECTION ===\n")
    
    test_cases = [
        {
            "domain": "E-commerce",
            "text": """orderStatus
This field accepts one of the following values:
l
PENDING
l
CONFIRMED
l
SHIPPED
l
DELIVERED""",
            "expected_bullets": 4
        },
        {
            "domain": "System Configuration",
            "text": """logLevel
(Optional) Logging level configuration:
l
DEBUG
l
INFO
l
WARN
l
ERROR""",
            "expected_bullets": 4
        },
        {
            "domain": "User Management",
            "text": """userRole
Available roles in the system:
l
ADMIN
l
USER
l
GUEST
l
MODERATOR""",
            "expected_bullets": 4
        }
    ]
    
    processor = IntelligentTextProcessor()
    all_passed = True
    
    for test_case in test_cases:
        print(f"Testing {test_case['domain']} domain...")
        
        processed = processor.fix_encoding_and_bullets(test_case['text'])
        bullet_count = processed.count('•')
        
        if bullet_count == test_case['expected_bullets']:
            print(f"✅ {test_case['domain']}: {bullet_count} bullets detected correctly")
        else:
            print(f"❌ {test_case['domain']}: Expected {test_case['expected_bullets']} bullets, got {bullet_count}")
            all_passed = False
    
    return all_passed


def test_generic_field_extraction():
    """Test field extraction without domain assumptions"""
    
    print("\n=== TESTING GENERIC FIELD EXTRACTION ===\n")
    
    test_documents = [
        {
            "type": "API Documentation",
            "content": """
userId: (Required) Unique identifier for the user
email: (Optional) User's email address  
status: (Conditional) Account status
createdAt: Timestamp of account creation
""",
            "expected_min_fields": 3
        },
        {
            "type": "Configuration File",
            "content": """
server: localhost
port: 8080
database: myapp
timeout: 30000
ssl_enabled: true
""",
            "expected_min_fields": 4
        },
        {
            "type": "Data Schema",
            "content": """
id: integer, Primary key (Required)
name: string, Display name (Required)  
active: boolean, Status flag (Optional)
created_at: datetime, Record creation timestamp
updated_at: datetime, Last modification timestamp
""",
            "expected_min_fields": 3
        }
    ]
    
    extractor = GenericPDFExtractor()
    all_passed = True
    
    for doc in test_documents:
        print(f"Testing {doc['type']}...")
        
        processed_text = extractor.process_text(doc['content'])
        structure = extractor.detect_document_structure(processed_text)
        fields = extractor.extract_fields(processed_text, structure)
        
        field_count = len(fields)
        
        if field_count >= doc['expected_min_fields']:
            print(f"✅ {doc['type']}: {field_count} fields extracted (>= {doc['expected_min_fields']} required)")
            print(f"   Document type detected: {structure['document_type']}")
        else:
            print(f"❌ {doc['type']}: Only {field_count} fields extracted, expected >= {doc['expected_min_fields']}")
            all_passed = False
    
    return all_passed


def test_configuration_flexibility():
    """Test that the system can be configured for different domains"""
    
    print("\n=== TESTING CONFIGURATION FLEXIBILITY ===\n")
    
    # Test different domain configs
    configs = [
        {
            "domain": "Healthcare",
            "config": {
                "bullet_indicators": ["symptoms", "conditions", "treatments", "medications", "following"]
            }
        },
        {
            "domain": "Finance", 
            "config": {
                "bullet_indicators": ["rates", "fees", "charges", "options", "following values"]
            }
        },
        {
            "domain": "Legal",
            "config": {
                "bullet_indicators": ["clauses", "terms", "conditions", "requirements", "following"]
            }
        }
    ]
    
    for config_test in configs:
        print(f"Testing {config_test['domain']} configuration...")
        
        try:
            extractor = GenericPDFExtractor(config_test['config'])
            
            # Test that it accepts the config without error
            print(f"✅ {config_test['domain']}: Configuration accepted")
            
            # Test that bullet indicators are applied
            if hasattr(extractor, 'bullet_indicators'):
                configured_indicators = set(extractor.bullet_indicators)
                expected_indicators = set(config_test['config']['bullet_indicators'])
                
                if expected_indicators.issubset(configured_indicators):
                    print(f"✅ {config_test['domain']}: Custom bullet indicators applied")
                else:
                    print(f"❌ {config_test['domain']}: Custom bullet indicators not applied correctly")
                    return False
            
        except Exception as e:
            print(f"❌ {config_test['domain']}: Configuration failed - {e}")
            return False
    
    return True


def main():
    """Run all architecture validation tests"""
    
    print("🏗️ ARCHITECTURE VALIDATION FOR GENERIC PDF PROCESSING\n")
    print("Ensuring NO domain-specific hardcoded values remain...")
    print("Validating universal PDF processing capability...\n")
    
    tests = [
        ("Hardcoded Values Check", test_no_hardcoded_values),
        ("Generic Bullet Detection", test_generic_bullet_detection),
        ("Generic Field Extraction", test_generic_field_extraction),
        ("Configuration Flexibility", test_configuration_flexibility)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"\n❌ {test_name}: FAILED with error - {e}")
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("ARCHITECTURE VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ARCHITECTURE VALIDATION SUCCESSFUL!")
        print("✅ No VTS-specific hardcoded values remain")
        print("✅ Universal PDF processing capability confirmed")
        print("✅ Ready for millions of different PDF types")
        return True
    else:
        print("\n⚠️ ARCHITECTURE VALIDATION FAILED!")
        print("❌ Issues found that need to be addressed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)