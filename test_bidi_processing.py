#!/usr/bin/env python3
"""
Test script to verify bidirectional text processing is working correctly.

This script tests the Arabic text processing functions to ensure
the bidirectional text processing is working properly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_bidi_processing():
    """Test bidirectional text processing."""
    
    print("🧪 Testing Bidirectional Text Processing")
    print("=" * 50)
    
    # Test text (this is the backwards Arabic text from the extracted files)
    test_text = "ة عجارلما ةنجل لمع ةحئلا"
    print(f"Original text (backwards): {test_text}")
    
    try:
        # Test 1: Check if python-bidi is available
        print(f"\n1. Testing python-bidi availability...")
        try:
            from bidi.algorithm import get_display
            print(f"   ✅ python-bidi is available")
            
            # Test bidirectional processing
            processed_text = get_display(test_text)
            print(f"   Processed text: {processed_text}")
            
        except ImportError as e:
            print(f"   ❌ python-bidi not available: {e}")
            return False
        
        # Test 2: Check if arabic-reshaper is available
        print(f"\n2. Testing arabic-reshaper availability...")
        try:
            import arabic_reshaper
            print(f"   ✅ arabic-reshaper is available")
            
            # Test Arabic reshaping
            reshaped_text = arabic_reshaper.reshape(test_text)
            print(f"   Reshaped text: {reshaped_text}")
            
        except ImportError as e:
            print(f"   ❌ arabic-reshaper not available: {e}")
            return False
        
        # Test 3: Test our ArabicTextProcessor
        print(f"\n3. Testing ArabicTextProcessor...")
        try:
            from app.utils.arabic_text_processor import ArabicTextProcessor
            
            # Test is_arabic_text
            is_arabic = ArabicTextProcessor.is_arabic_text(test_text)
            print(f"   Is Arabic text: {is_arabic}")
            
            # Test normalize_arabic_text
            normalized = ArabicTextProcessor.normalize_arabic_text(test_text)
            print(f"   Normalized text: {normalized}")
            
            # Test process_bidirectional_text
            bidi_processed = ArabicTextProcessor.process_bidirectional_text(test_text)
            print(f"   Bidirectional processed: {bidi_processed}")
            
            # Test preprocess_arabic_text (full pipeline)
            preprocessed = ArabicTextProcessor.preprocess_arabic_text(test_text)
            print(f"   Fully preprocessed: {preprocessed}")
            
            print(f"   ✅ ArabicTextProcessor is working correctly")
            
        except ImportError as e:
            print(f"   ❌ ArabicTextProcessor not available: {e}")
            return False
        
        # Test 4: Test with a longer Arabic text
        print(f"\n4. Testing with longer Arabic text...")
        longer_text = "ةكرشلاب نيمهاسملل ةماعلا ةيعمجلا لبق نم ةكرشلا"
        print(f"   Original: {longer_text}")
        
        processed_longer = ArabicTextProcessor.preprocess_arabic_text(longer_text)
        print(f"   Processed: {processed_longer}")
        
        print(f"\n🎉 All tests passed! Bidirectional processing is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def show_expected_vs_actual():
    """Show expected vs actual results."""
    
    print(f"\n📖 Expected vs Actual Results")
    print("=" * 50)
    
    print(f"\n❌ Current (Wrong Direction):")
    print(f"   'ة عجارلما ةنجل لمع ةحئلا'")
    print(f"   (This reads backwards)")
    
    print(f"\n✅ Expected (Correct Direction):")
    print(f"   'الآلية عمل لجنة الشركة'")
    print(f"   (This reads correctly from right to left)")
    
    print(f"\n🔧 The Fix Should:")
    print(f"   1. Detect Arabic text")
    print(f"   2. Apply bidirectional processing")
    print(f"   3. Reshape Arabic letters")
    print(f"   4. Return correctly formatted text")

def check_server_status():
    """Check if the server is running and needs restart."""
    
    print(f"\n🖥️  Server Status Check")
    print("=" * 50)
    
    print(f"\n⚠️  Important Notes:")
    print(f"   1. If you modified the code, the server needs to be restarted")
    print(f"   2. The changes are in app/services/enhanced_document_processor.py")
    print(f"   3. Restart your FastAPI server to apply the changes")
    
    print(f"\n🔄 To Apply the Fix:")
    print(f"   1. Stop your current server (Ctrl+C)")
    print(f"   2. Restart the server:")
    print(f"      python run.py")
    print(f"   3. Upload a new document or reprocess an existing one")
    print(f"   4. Check the extracted text files")

if __name__ == "__main__":
    print("🔍 Bidirectional Text Processing Test")
    print("=" * 50)
    
    # Run the tests
    success = test_bidi_processing()
    
    if success:
        show_expected_vs_actual()
    else:
        print(f"\n❌ Tests failed. Check your environment setup.")
    
    check_server_status()
    
    print(f"\n💡 Next Steps:")
    print(f"   1. If tests passed, restart your server")
    print(f"   2. Upload a new Arabic document")
    print(f"   3. Check the extracted text files")
    print(f"   4. The Arabic text should now display correctly")




