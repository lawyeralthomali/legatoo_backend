#!/usr/bin/env python3
"""
Debug script to examine the actual text content and find patterns
"""

import sys
import os
import re

def examine_text():
    """Examine the extracted text to understand its structure"""
    try:
        # Read the extracted text
        with open("extracted_text_full.txt", "r", encoding="utf-8") as f:
            text = f.read()
        
        print("=== TEXT EXAMINATION ===")
        print(f"Total text length: {len(text)} characters")
        
        # Split into lines
        lines = text.split('\n')
        print(f"Total lines: {len(lines)}")
        
        # Show first 20 non-empty lines
        print("\n=== FIRST 20 NON-EMPTY LINES ===")
        count = 0
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and count < 20:
                print(f"Line {i}: {line}")
                count += 1
        
        # Look for any Arabic text patterns
        print("\n=== LOOKING FOR ARABIC PATTERNS ===")
        arabic_keywords = ['الباب', 'الفصل', 'المادة', 'مادة', 'أول', 'ثاني', 'ثالث', 'أولى', 'ثانية', 'ثالثة', 'نظام', 'العمل']
        
        for keyword in arabic_keywords:
            matches = []
            for i, line in enumerate(lines, 1):
                if keyword in line:
                    matches.append((i, line.strip()))
            
            if matches:
                print(f"\nKeyword '{keyword}' found in {len(matches)} lines:")
                for line_num, content in matches[:3]:  # Show first 3 matches
                    print(f"  Line {line_num}: {content[:100]}...")
        
        # Look for any numbers or patterns that might indicate structure
        print("\n=== LOOKING FOR STRUCTURAL PATTERNS ===")
        structural_patterns = [
            r'\d+',  # Any digits
            r'[أ-ي]+',  # Arabic letters
            r'المادة\s*\d+',  # Article with number
            r'الباب\s*\d+',  # Chapter with number
            r'الفصل\s*\d+'   # Section with number
        ]
        
        for pattern in structural_patterns:
            regex = re.compile(pattern, re.UNICODE)
            matches = []
            for i, line in enumerate(lines[:200], 1):  # Check first 200 lines
                line = line.strip()
                if regex.search(line):
                    matches.append((i, line))
            
            if matches:
                print(f"\nPattern '{pattern}' found in {len(matches)} lines:")
                for line_num, content in matches[:2]:  # Show first 2 matches
                    print(f"  Line {line_num}: {content[:80]}...")
        
        # Check for specific line that might contain the document structure
        print("\n=== CHECKING FOR DOCUMENT TITLE AND STRUCTURE ===")
        for i, line in enumerate(lines[:50], 1):
            line = line.strip()
            if line and len(line) > 10:  # Non-empty lines with some content
                print(f"Line {i}: {line}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_text()
