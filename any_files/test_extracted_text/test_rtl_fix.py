#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import codecs

# Set UTF-8 encoding for stdout
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

sys.path.append(os.path.dirname(__file__))

from extract_arabic_pdf_easyocr import fix_arabic_text, ensure_rtl_text_direction

def test_rtl_fix():
    """Test RTL text fixing"""
    
    # Test Arabic text that should be RTL
    test_text = "بدء تحقيقات خاصة والإشراف عليها، حسب الاقتضاء"
    
    print("Original text:")
    print(repr(test_text))
    print("Display:", test_text)
    print()
    
    # Apply Arabic fixing
    fixed_text = fix_arabic_text(test_text)
    print("After fix_arabic_text:")
    print(repr(fixed_text))
    print("Display:", fixed_text)
    print()
    
    # Apply RTL direction
    rtl_text = ensure_rtl_text_direction(fixed_text)
    print("After ensure_rtl_text_direction:")
    print(repr(rtl_text))
    print("Display:", rtl_text)
    print()
    
    # Check for RTL marks
    rtl_200f = rtl_text.count('\u200F')
    rtl_202e = rtl_text.count('\u202E') 
    rtl_202c = rtl_text.count('\u202C')
    
    print(f"RTL Mark (\\u200F): {rtl_200f}")
    print(f"Override (\\u202E): {rtl_202e}")
    print(f"Pop (\\u202C): {rtl_202c}")
    
    return rtl_text

if __name__ == "__main__":
    test_rtl_fix()
