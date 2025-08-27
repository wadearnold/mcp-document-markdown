#!/usr/bin/env python3
"""
Debug bullet point extraction
"""
import fitz
from pathlib import Path

def debug_bullets():
    pdf_path = "VTS_chapter4.pdf"
    
    with fitz.open(pdf_path) as doc:
        # Get page 4 (Token Information) where tokenType should have values
        page = doc.load_page(3)  # 0-indexed, so page 4 is index 3
        text = page.get_text()
        
        print("=== RAW TEXT FROM PAGE 4 ===")
        lines = text.split('\n')
        
        # Find tokenType section
        tokentype_start = -1
        for i, line in enumerate(lines):
            if 'tokenType' in line:
                tokentype_start = i
                break
        
        if tokentype_start != -1:
            # Show lines around tokenType
            start = max(0, tokentype_start - 2)
            end = min(len(lines), tokentype_start + 15)
            
            print(f"\nLines {start}-{end} around tokenType:")
            for i in range(start, end):
                marker = ">>> " if i == tokentype_start else "    "
                print(f"{marker}{i:3d}: '{lines[i]}'")
        
        print(f"\nTotal lines with 'l ': {sum(1 for line in lines if line.strip().startswith('l '))}")
        print(f"Total lines with '• ': {sum(1 for line in lines if line.strip().startswith('• '))}")

if __name__ == "__main__":
    debug_bullets()