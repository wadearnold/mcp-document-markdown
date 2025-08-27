#!/usr/bin/env python3
"""
Test bullet fix specifically
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'python'))

from processors.pdf_extractor_ultimate import IntelligentTextProcessor

def test_bullet_fix():
    processor = IntelligentTextProcessor()
    
    # Test with the exact pattern we found
    test_text = """tokenType
(Conditional) This is a required field in the following APIs:
l
Approve Provisioning
l
Approve Provisioning Stand-In Notification
l
Token Create Notification
Format: It is one of the following values:
l
SECURE_ELEMENT
l
HCE
l
CARD_ON_FILE"""

    print("=== BEFORE PROCESSING ===")
    print(test_text)
    
    print("\n=== AFTER PROCESSING ===")
    processed = processor.fix_encoding_and_bullets(test_text)
    print(processed)
    
    print("\n=== ANALYSIS ===")
    lines = processed.split('\n')
    bullet_lines = [line for line in lines if line.strip().startswith('•')]
    l_lines = [line for line in lines if line.strip().startswith('l ')]
    
    print(f"Bullet lines (•): {len(bullet_lines)}")
    for line in bullet_lines:
        print(f"  '{line.strip()}'")
    
    print(f"Remaining l lines: {len(l_lines)}")
    for line in l_lines:
        print(f"  '{line.strip()}'")

if __name__ == "__main__":
    test_bullet_fix()