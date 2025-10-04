#!/usr/bin/env python3
"""Simple test for bidirectional text processing."""

try:
    from bidi.algorithm import get_display
    print("python-bidi is available")
    
    # Test with the backwards Arabic text
    test_text = "ة عجارلما ةنجل لمع ةحئلا"
    print(f"Original text: {test_text}")
    
    processed = get_display(test_text)
    print(f"Processed text: {processed}")
    
    # Test if it's different (should be)
    if test_text != processed:
        print("Bidirectional processing is working - text was changed")
    else:
        print("Bidirectional processing didn't change the text")
        
except ImportError as e:
    print(f"python-bidi not available: {e}")

try:
    import arabic_reshaper
    print("arabic-reshaper is available")
    
    test_text = "ة عجارلما ةنجل لمع ةحئلا"
    reshaped = arabic_reshaper.reshape(test_text)
    print(f"Reshaped text: {reshaped}")
    
except ImportError as e:
    print(f"arabic-reshaper not available: {e}")
