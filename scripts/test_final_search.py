"""Test final search with new model."""
import requests

url = "http://localhost:8000/api/v1/search/similar-laws"
params = {
    "query": "عقوبة تزوير الطوابع",
    "top_k": 5,
    "threshold": 0.5
}

print("🔍 Testing search with new Sentence Transformer model...")
print(f"Query: {params['query']}")
print("="*80)

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Success: {data['success']}")
    print(f"📊 Total results: {data['data']['total_results']}")
    
    if data['data']['results']:
        print("\n🎯 Top Results:")
        for i, result in enumerate(data['data']['results'], 1):
            print(f"\n{i}. Chunk {result['chunk_id']} - Similarity: {result['similarity']:.4f}")
            print(f"   Law: {result.get('law_metadata', {}).get('law_name', 'N/A')}")
            print(f"   Content: {result['content'][:100]}...")
    else:
        print("\n❌ No results found")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

