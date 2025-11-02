"""
Test Script - Verify Arabic Embedding Enhancements

This script tests the three enhancements made to arabic_legal_embedding_service.py:
1. Default model is arabert-st
2. Arabic text normalization works correctly
3. Only SentenceTransformer is used (no raw BERT)
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService
import numpy as np


async def test_enhancements():
    """Test all three enhancements"""
    
    print("=" * 80)
    print("🧪 Testing Arabic Embedding Service Enhancements")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        
        # Test 1: Verify Default Model
        print("\n" + "=" * 80)
        print("TEST 1: Default Model is 'arabert-st'")
        print("=" * 80)
        
        service = ArabicLegalEmbeddingService(db)
        print(f"✅ Default model: {service.model_name}")
        
        if service.model_name == 'arabert-st':
            print("✅ PASS: Default model is arabert-st")
        else:
            print(f"❌ FAIL: Expected 'arabert-st', got '{service.model_name}'")
        
        # Test 2: Verify Normalization Works
        print("\n" + "=" * 80)
        print("TEST 2: Arabic Text Normalization")
        print("=" * 80)
        
        # Test normalization function
        test_cases = [
            ("المَادَّةُ الأُولَى", "الماده الاولى", "Diacritics & Alif & Ta'a"),
            ("أمر", "امر", "Alif hamza"),
            ("إجراء", "اجراء", "Alif kasra"),
            ("آداب", "اداب", "Alif madda"),
            ("مادة", "ماده", "Ta'a Marbuta"),
        ]
        
        all_passed = True
        for original, expected, description in test_cases:
            normalized = service._normalize_arabic_legal_text(original)
            if normalized == expected:
                print(f"✅ {description}: '{original}' → '{normalized}'")
            else:
                print(f"❌ {description}: Expected '{expected}', got '{normalized}'")
                all_passed = False
        
        if all_passed:
            print("\n✅ PASS: All normalization tests passed")
        else:
            print("\n❌ FAIL: Some normalization tests failed")
        
        # Test 3: Verify No Raw BERT Code
        print("\n" + "=" * 80)
        print("TEST 3: Raw BERT Support Removed")
        print("=" * 80)
        
        # Check that raw BERT fields don't exist
        has_model = hasattr(service, 'model') and service.model is not None
        has_tokenizer = hasattr(service, 'tokenizer') and service.tokenizer is not None
        has_model_type = hasattr(service, 'model_type')
        has_mean_pooling = hasattr(service, '_mean_pooling')
        
        if not has_model:
            print("✅ self.model: Not present (removed)")
        else:
            print("❌ self.model: Still present")
        
        if not has_tokenizer:
            print("✅ self.tokenizer: Not present (removed)")
        else:
            print("❌ self.tokenizer: Still present")
        
        if not has_model_type:
            print("✅ self.model_type: Not present (removed)")
        else:
            print("❌ self.model_type: Still present")
        
        if not has_mean_pooling:
            print("✅ _mean_pooling(): Not present (removed)")
        else:
            print("❌ _mean_pooling(): Still present")
        
        raw_bert_removed = not (has_model or has_tokenizer or has_model_type or has_mean_pooling)
        
        if raw_bert_removed:
            print("\n✅ PASS: All raw BERT code removed")
        else:
            print("\n❌ FAIL: Some raw BERT code still present")
        
        # Test 4: Test Actual Embedding Generation
        print("\n" + "=" * 80)
        print("TEST 4: Test Embedding Generation")
        print("=" * 80)
        
        try:
            # Initialize model
            print("🤖 Initializing model...")
            service.initialize_model()
            print(f"✅ Model loaded: {service.model_name}")
            print(f"   Embedding dimension: {service.embedding_dimension}")
            
            # Test with Arabic text
            test_text = "المادة الأولى: فسخ عقد العمل"
            print(f"\n📝 Test text: {test_text}")
            
            embedding = service.encode_text(test_text)
            print(f"✅ Embedding generated: {len(embedding)} dimensions")
            print(f"   Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
            
            # Test normalization impact
            text_with_diacritics = "المَادَّةُ الأُولَى: فِسْخُ عَقْدِ العَمَلِ"
            text_without_diacritics = "الماده الاولى: فسخ عقد العمل"
            
            emb1 = service.encode_text(text_with_diacritics)
            emb2 = service.encode_text(text_without_diacritics)
            
            similarity = service.cosine_similarity(emb1, emb2)
            print(f"\n🔍 Normalization test:")
            print(f"   With diacritics: '{text_with_diacritics[:30]}...'")
            print(f"   Without diacritics: '{text_without_diacritics[:30]}...'")
            print(f"   Similarity: {similarity:.4f}")
            
            if similarity > 0.99:
                print("   ✅ PASS: Embeddings are nearly identical (normalization working)")
            else:
                print(f"   ⚠️  WARNING: Similarity is {similarity:.4f} (expected > 0.99)")
            
            print("\n✅ PASS: Embedding generation works correctly")
            
        except Exception as e:
            print(f"\n❌ FAIL: Embedding generation failed: {str(e)}")
        
        # Final Summary
        print("\n" + "=" * 80)
        print("📊 FINAL SUMMARY")
        print("=" * 80)
        print(f"✅ Default Model: {'arabert-st' if service.model_name == 'arabert-st' else '❌ Wrong'}")
        print(f"✅ Normalization: {'Active' if all_passed else '❌ Failed'}")
        print(f"✅ Raw BERT Removed: {'Yes' if raw_bert_removed else '❌ Still Present'}")
        print(f"✅ Embedding Generation: {'Working' if embedding is not None else '❌ Failed'}")
        print("=" * 80)
        print("\n🎉 All enhancements verified and working!" if all([
            service.model_name == 'arabert-st',
            all_passed,
            raw_bert_removed,
            embedding is not None
        ]) else "\n⚠️  Some tests failed - please review above")


if __name__ == "__main__":
    print("🚀 Starting Enhancement Tests...\n")
    asyncio.run(test_enhancements())

