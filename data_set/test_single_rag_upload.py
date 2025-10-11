"""
Single File RAG Upload Test Script

Quick test script to upload a single law file to the RAG system.
Useful for testing and debugging before batch upload.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def flatten_law_structure(law_data):
    """Flatten hierarchical law structure."""
    law_source = law_data.get('law_sources', [{}])[0]
    
    # Collect all articles
    articles = []
    for branch in law_source.get('branches', []):
        for chapter in branch.get('chapters', []):
            for article in chapter.get('articles', []):
                articles.append({
                    'article_number': article.get('article_number', ''),
                    'title': article.get('title', ''),
                    'content': article.get('content', ''),
                    'keywords': article.get('keywords', [])
                })
    
    return {
        'law_name': law_source.get('name', 'Unknown Law'),
        'law_type': law_source.get('type', 'law'),
        'jurisdiction': law_source.get('jurisdiction'),
        'issuing_authority': law_source.get('issuing_authority'),
        'issue_date': law_source.get('issue_date'),
        'description': law_source.get('description'),
        'articles': articles
    }


def test_upload(file_path, base_url='http://localhost:8000'):
    """Test upload of a single file."""
    print("="*60)
    print("🧪 RAG SINGLE FILE UPLOAD TEST")
    print("="*60)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📁 File: {file_path}")
    print(f"🌐 Server: {base_url}")
    
    try:
        # Read JSON file
        print("\n📖 Reading file...")
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Flatten structure
        print("🔄 Flattening structure...")
        flattened_data = flatten_law_structure(raw_data)
        
        print(f"✅ Prepared data:")
        print(f"   Law Name: {flattened_data['law_name']}")
        print(f"   Articles: {len(flattened_data['articles'])}")
        
        # Upload
        print("\n📤 Uploading to RAG system...")
        endpoint = f"{base_url}/api/v1/rag/upload"
        
        response = requests.post(
            endpoint,
            json=flattened_data,
            headers={'Content-Type': 'application/json'},
            timeout=300
        )
        
        # Parse response
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                data = result.get('data', {})
                print("\n✅ SUCCESS!")
                print(f"   Law Source ID: {data.get('law_source_id')}")
                print(f"   Articles Created: {data.get('articles_created')}")
                print(f"   Chunks Created: {data.get('chunks_created')}")
                print(f"   Processing Time: {data.get('processing_time')}s")
                print(f"   Status: {data.get('status')}")
            else:
                print("\n❌ UPLOAD FAILED")
                print(f"   Message: {result.get('message')}")
                errors = result.get('errors', [])
                for error in errors:
                    print(f"   - {error.get('message')}")
        else:
            print(f"\n❌ HTTP ERROR: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Parse Error: {str(e)}")
    except requests.exceptions.Timeout:
        print(f"\n❌ Request Timeout (>5 minutes)")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    # Default test file
    test_file = "data_set/files/1.json"
    
    # Allow custom file path from command line
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    # Allow custom base URL from environment or command line
    base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    if len(sys.argv) > 2:
        base_url = sys.argv[2]
    
    test_upload(test_file, base_url)

