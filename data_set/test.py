"""
RAG System Accuracy Test - Test all 1.json articles

This script tests the RAG system by:
1. Loading all 30 articles from 1.json
2. For each article's keywords, searching the RAG system
3. Checking if the correct article is retrieved in top-k results
4. Calculating accuracy per article and overall system accuracy
"""

import json
import requests
from typing import List, Dict
import numpy as np
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
RAG_SEARCH_ENDPOINT = f"{API_BASE_URL}/api/v1/rag/search"
TOP_K = 5  # Number of results to retrieve
THRESHOLD = 0.5  # Minimum similarity threshold


def search_rag(query: str, top_k: int = TOP_K) -> List[Dict]:
    """
    Search RAG system with a query.
    
    Args:
        query: Search query (keyword)
        top_k: Number of results to retrieve
        
    Returns:
        List of result dictionaries with article info
    """
    try:
        response = requests.post(
            RAG_SEARCH_ENDPOINT,
            json={
                'query': query,
                'top_k': top_k,
                'threshold': THRESHOLD
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return result.get('data', {}).get('results', [])
        
        return []
        
    except Exception as e:
        print(f"❌ Search failed for '{query}': {str(e)}")
        return []


def normalize_article_number(article_num: str) -> str:
    """Normalize article number for comparison."""
    return str(article_num).strip().lower()


# Load the JSON file (fix path for Windows)
print("="*70)
print("🧪 RAG ACCURACY TEST - Testing all articles from 1.json")
print("="*70)
print(f"API: {API_BASE_URL}")
print(f"Top-K: {TOP_K}")
print(f"Threshold: {THRESHOLD}")
print("="*70)

try:
    with open("files/1.json", "r", encoding="utf-8") as f:  # Fixed path
        law_data = json.load(f)
    print("✅ Loaded 1.json successfully\n")
except FileNotFoundError:
    print("❌ File not found: files/1.json")
    print("   Make sure you're in the data_set directory")
    exit(1)

# Collect all articles with keywords
articles = []
for source in law_data["law_sources"]:
    for branch in source["branches"]:
        for chapter in branch["chapters"]:
            for article in chapter["articles"]:
                articles.append({
                    "article_number": article["article_number"],
                    "title": article["title"],
                    "keywords": article["keywords"],
                    "content": article["content"][:100] + "..."  # Preview
                })

print(f"📊 Found {len(articles)} articles to test\n")

# Test each article
results = []
total_keywords = 0
total_successes = 0

for idx, art in enumerate(articles, 1):
    article_number = art["article_number"]
    keywords = art["keywords"]
    title = art["title"]
    
    print(f"\n{'='*70}")
    print(f"Testing Article {idx}/{len(articles)}: {article_number} - {title}")
    print(f"{'='*70}")
    print(f"Keywords: {', '.join(keywords)}")
    
    article_result = {
        "article_number": article_number,
        "title": title,
        "keywords": {},
        "success_count": 0,
        "total_keywords": len(keywords)
    }
    
    for kw in keywords:
        print(f"\n  🔍 Searching for: '{kw}'")
        
        # Search RAG system
        retrieved = search_rag(kw)
        
        if not retrieved:
            print(f"     ⚠️  No results returned")
            article_result["keywords"][kw] = {
                "success": False,
                "found_in_position": None,
                "top_score": 0
            }
            continue
        
        # Check if our article is in the results
        success = False
        position = None
        top_score = retrieved[0].get('similarity_score', 0)
        
        for pos, result in enumerate(retrieved, 1):
            retrieved_article = result.get('article_number', '')
            retrieved_score = result.get('similarity_score', 0)
            
            if normalize_article_number(retrieved_article) == normalize_article_number(article_number):
                success = True
                position = pos
                print(f"     ✅ Found at position {position} (score: {retrieved_score:.4f})")
                article_result["success_count"] += 1
                total_successes += 1
                break
        
        if not success:
            print(f"     ❌ Not found in top {TOP_K}")
            print(f"        Top result: Article {retrieved[0].get('article_number')} (score: {top_score:.4f})")
        
        article_result["keywords"][kw] = {
            "success": success,
            "found_in_position": position,
            "top_score": top_score
        }
        
        total_keywords += 1
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.3)
    
    # Calculate article accuracy
    if keywords:
        article_result["accuracy"] = article_result["success_count"] / len(keywords)
    else:
        article_result["accuracy"] = None
    
    results.append(article_result)
    
    # Print article summary
    if article_result["accuracy"] is not None:
        accuracy_pct = article_result["accuracy"] * 100
        status = "✅" if accuracy_pct >= 70 else "⚠️" if accuracy_pct >= 50 else "❌"
        print(f"\n{status} Article Accuracy: {accuracy_pct:.1f}% ({article_result['success_count']}/{len(keywords)} keywords)")

# Calculate overall system accuracy
print("\n" + "="*70)
print("📊 OVERALL RESULTS")
print("="*70)

accuracies = [r["accuracy"] for r in results if r["accuracy"] is not None]
overall_accuracy = np.mean(accuracies) if accuracies else 0

print(f"\n✅ Articles Tested: {len(results)}")
print(f"✅ Total Keywords Tested: {total_keywords}")
print(f"✅ Successful Retrievals: {total_successes}")
print(f"✅ Failed Retrievals: {total_keywords - total_successes}")
print(f"\n🎯 OVERALL SYSTEM ACCURACY: {overall_accuracy:.2%}")

if overall_accuracy >= 0.8:
    print("🎉 EXCELLENT! System is performing very well!")
elif overall_accuracy >= 0.6:
    print("✅ GOOD! System is performing well")
elif overall_accuracy >= 0.4:
    print("⚠️  MODERATE! System needs improvement")
else:
    print("❌ LOW! System needs significant improvement")

# Detailed results per article
print("\n" + "="*70)
print("📄 DETAILED RESULTS PER ARTICLE")
print("="*70)

for r in results:
    acc = r.get('accuracy')
    if acc is not None:
        status = "✅" if acc >= 0.7 else "⚠️" if acc >= 0.5 else "❌"
        print(f"\n{status} Article {r['article_number']}: {r['title']}")
        print(f"   Accuracy: {acc:.1%} ({r['success_count']}/{r['total_keywords']} keywords)")
        
        # Show keyword details
        for kw, details in r["keywords"].items():
            if details["success"]:
                print(f"   ✅ '{kw}' → Found at position {details['found_in_position']}")
            else:
                print(f"   ❌ '{kw}' → Not found (top score: {details['top_score']:.4f})")

# Save results to JSON
output_file = "rag_accuracy_test_results.json"
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_config": {
                "api_url": API_BASE_URL,
                "top_k": TOP_K,
                "threshold": THRESHOLD,
                "total_articles": len(results),
                "total_keywords": total_keywords
            },
            "overall_accuracy": overall_accuracy,
            "total_successes": total_successes,
            "total_failures": total_keywords - total_successes,
            "article_results": results
        }, f, ensure_ascii=False, indent=2)
    print(f"\n📝 Detailed results saved to: {output_file}")
except Exception as e:
    print(f"\n⚠️  Failed to save results: {str(e)}")

print("\n" + "="*70)
print("✅ Test completed!")
print("="*70)
