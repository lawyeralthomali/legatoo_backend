#!/usr/bin/env python3
"""
Test script to verify Arabic text direction fix
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_arabic_fix():
    """Test the Arabic text direction fix"""
    try:
        # Read the original extracted text
        with open("extracted_text_full.txt", "r", encoding="utf-8") as f:
            original_text = f.read()
        
        # Apply the fix (reverse each line)
        lines = original_text.split('\n')
        corrected_lines = []
        
        for line in lines:
            corrected_line = line[::-1]
            corrected_lines.append(corrected_line)
        
        corrected_text = '\n'.join(corrected_lines)
        
        # Save the corrected text
        with open("corrected_arabic_text.txt", "w", encoding="utf-8") as f:
            f.write(corrected_text)
        
        print("Arabic text direction fix applied!")
        print("Original text saved to: extracted_text_full.txt")
        print("Corrected text saved to: corrected_arabic_text.txt")
        
        # Show a sample of the correction
        print("\n=== SAMPLE CORRECTION ===")
        original_lines = original_text.split('\n')
        corrected_lines = corrected_text.split('\n')
        
        for i in range(min(10, len(original_lines))):
            orig = original_lines[i].strip()
            corr = corrected_lines[i].strip()
            if orig and corr:
                print(f"Original:  {orig}")
                print(f"Corrected: {corr}")
                print()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_arabic_fix()
