#!/usr/bin/env python3
"""
Debug script to analyze the extracted text and save results to file
"""

import sys
import os
import re

def analyze_text():
    """Analyze the extracted text and save results to file"""
    try:
        # Read the extracted text
        with open("extracted_text_full.txt", "r", encoding="utf-8") as f:
            text = f.read()
        
        # Split into lines
        lines = text.split('\n')
        
        # Analyze and save to file
        with open("text_analysis_results.txt", "w", encoding="utf-8") as f:
            f.write("=== TEXT ANALYSIS RESULTS ===\n")
            f.write(f"Total text length: {len(text)} characters\n")
            f.write(f"Total lines: {len(lines)}\n\n")
            
            # Show first 30 non-empty lines
            f.write("=== FIRST 30 NON-EMPTY LINES ===\n")
            count = 0
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and count < 30:
                    f.write(f"Line {i}: {line}\n")
                    count += 1
            
            f.write("\n=== LOOKING FOR ARABIC KEYWORDS ===\n")
            arabic_keywords = ['الباب', 'الفصل', 'المادة', 'مادة', 'أول', 'ثاني', 'ثالث', 'أولى', 'ثانية', 'ثالثة', 'نظام', 'العمل']
            
            for keyword in arabic_keywords:
                matches = []
                for i, line in enumerate(lines, 1):
                    if keyword in line:
                        matches.append((i, line.strip()))
                
                if matches:
                    f.write(f"\nKeyword '{keyword}' found in {len(matches)} lines:\n")
                    for line_num, content in matches[:5]:  # Show first 5 matches
                        f.write(f"  Line {line_num}: {content[:150]}...\n")
            
            f.write("\n=== LOOKING FOR STRUCTURAL PATTERNS ===\n")
            structural_patterns = [
                r'المادة\s*\d+',  # Article with number
                r'الباب\s*\d+',  # Chapter with number
                r'الفصل\s*\d+',   # Section with number
                r'مادة\s*\d+',   # Article (alternative)
                r'الباب\s+الأول', # First chapter
                r'الفصل\s+الأول', # First section
                r'المادة\s+الأولى' # First article
            ]
            
            for pattern in structural_patterns:
                regex = re.compile(pattern, re.UNICODE)
                matches = []
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if regex.search(line):
                        matches.append((i, line))
                
                if matches:
                    f.write(f"\nPattern '{pattern}' found in {len(matches)} lines:\n")
                    for line_num, content in matches[:3]:  # Show first 3 matches
                        f.write(f"  Line {line_num}: {content[:100]}...\n")
            
            f.write("\n=== CHECKING FOR DOCUMENT TITLE AND STRUCTURE ===\n")
            for i, line in enumerate(lines[:100], 1):
                line = line.strip()
                if line and len(line) > 15:  # Non-empty lines with substantial content
                    f.write(f"Line {i}: {line}\n")
        
        print("Analysis complete! Results saved to 'text_analysis_results.txt'")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_text()
