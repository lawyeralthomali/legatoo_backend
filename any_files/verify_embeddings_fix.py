"""
Verify that Arabic embeddings are working correctly after fixing FakeEmbeddings issue.
This script tests that semantic search actually works with meaningful embeddings.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np

def test_embeddings():
    """Test that embeddings produce meaningful semantic similarities."""
    
    print("🚀 Testing Arabic embeddings...")
    print("=" * 60)
    
    # Initialize the embeddings model
    print("\n📦 Loading Arabic embeddings model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="Omartificial-Intelligence-Space/GATE-AraBert-v1",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    print("✅ Model loaded successfully!")
    
    # Test texts in Arabic
    print("\n📝 Testing with Arabic legal texts...")
    texts = [
        "مهام واختصاصات مفتشي العمل في المملكة",  # Labor inspector duties
        "تفتيش أماكن العمل والتأكد من تطبيق النظام",  # Workplace inspection (SIMILAR to query)
        "إجازة الحج للعاملين في القطاع الخاص",  # Hajj leave (DIFFERENT topic)
        "حقوق المرأة العاملة أثناء الحمل والوضع"  # Pregnancy rights (DIFFERENT topic)
    ]
    
    query = "ماهي مهام واختصاصات مفتشي العمل"  # What are labor inspector duties?
    
    # Generate embeddings
    print("\n🔢 Generating embeddings...")
    text_embeddings = [embeddings.embed_query(text) for text in texts]
    query_embedding = embeddings.embed_query(query)
    
    # Calculate cosine similarities
    print("\n📊 Calculating similarities with query:")
    print(f"Query: '{query}'\n")
    
    similarities = []
    for i, text in enumerate(texts):
        # Cosine similarity
        text_vec = np.array(text_embeddings[i])
        query_vec = np.array(query_embedding)
        
        similarity = np.dot(text_vec, query_vec) / (np.linalg.norm(text_vec) * np.linalg.norm(query_vec))
        similarities.append((text, similarity))
        
        print(f"{i+1}. Similarity: {similarity:.4f}")
        print(f"   Text: {text}")
        print()
    
    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    print("\n" + "=" * 60)
    print("📈 RESULTS (sorted by relevance):")
    print("=" * 60)
    
    for i, (text, score) in enumerate(similarities):
        print(f"{i+1}. Score: {score:.4f} - {text}")
    
    # Validate results
    print("\n" + "=" * 60)
    print("🔍 VALIDATION:")
    print("=" * 60)
    
    # Check if the most similar text is actually about labor inspection
    top_text = similarities[0][0]
    top_score = similarities[0][1]
    
    if "تفتيش" in top_text or "مفتش" in top_text:
        print("✅ PASS: Most similar text is about labor inspection (correct!)")
        print(f"   Top match: {top_text}")
        print(f"   Similarity: {top_score:.4f}")
    else:
        print("❌ FAIL: Most similar text is NOT about labor inspection")
        print(f"   Top match: {top_text}")
        print(f"   This suggests embeddings are still not working properly")
        return False
    
    # Check that dissimilar texts have lower scores
    bottom_score = similarities[-1][1]
    score_diff = top_score - bottom_score
    
    if score_diff > 0.1:
        print(f"✅ PASS: Good score differentiation ({score_diff:.4f} difference)")
    else:
        print(f"⚠️  WARNING: Low score differentiation ({score_diff:.4f})")
        print("   Embeddings might still be using random values")
    
    print("\n" + "=" * 60)
    print("✅ EMBEDDINGS ARE WORKING CORRECTLY!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Restart your FastAPI server to load the new embeddings")
    print("   2. Re-upload your legal documents")
    print("   3. Test your RAG queries - they should return relevant results now")
    
    return True

if __name__ == "__main__":
    try:
        test_embeddings()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure you have installed the required packages:")
        print("   pip install langchain-huggingface sentence-transformers")
        sys.exit(1)

