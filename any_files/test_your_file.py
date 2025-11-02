"""
Test script for your actual saudi_labor_law.json file
"""

import requests
import json

def test_your_file():
    """Test with your actual saudi_labor_law.json file."""
    
    base_url = "http://192.168.100.13:8000"
    file_path = "data_set/files/saudi_labor_law.json"
    
    print("🔍 Testing debug endpoint with your actual file...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            
            response = requests.post(
                f"{base_url}/api/v1/documents/debug-upload",
                files=files
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Debug analysis successful!")
            print("\n📋 File Structure Analysis:")
            if result.get('data'):
                print(f"- Data type: {result['data']['json_analysis']['data_type']}")
                print(f"- Top level keys: {result['data']['json_analysis']['top_level_keys']}")
                print(f"- Has law_sources: {result['data']['structure_validation']['has_law_sources']}")
                print(f"- Law sources type: {result['data']['structure_validation']['law_sources_type']}")
                print(f"- Law sources count: {result['data']['structure_validation']['law_sources_count']}")
            else:
                print("No data in response")
                print(f"Full response: {result}")
            
            if 'first_law_source' in result['data']:
                print(f"\n📄 First Law Source:")
                print(f"- Type: {result['data']['first_law_source']['type']}")
                print(f"- Is dict: {result['data']['first_law_source']['is_dict']}")
                print(f"- Has name: {result['data']['first_law_source']['has_name']}")
                print(f"- Has articles: {result['data']['first_law_source']['has_articles']}")
                print(f"- Articles count: {result['data']['first_law_source']['articles_count']}")
                
                if 'first_article' in result['data']:
                    print(f"\n📝 First Article:")
                    print(f"- Type: {result['data']['first_article']['type']}")
                    print(f"- Is dict: {result['data']['first_article']['is_dict']}")
                    print(f"- Has text: {result['data']['first_article']['has_text']}")
                    print(f"- Has article: {result['data']['first_article']['has_article']}")
            
            print(f"\n📄 Content Preview (first 200 chars):")
            print(result['data']['content_preview'][:200] + "...")
            
        else:
            print(f"❌ Debug failed: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_upload_your_file():
    """Test the actual upload with your file."""
    
    base_url = "http://192.168.100.13:8000"
    file_path = "data_set/files/saudi_labor_law.json"
    
    print("\n📤 Testing actual upload with your file...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'title': 'نظام العمل السعودي',
                'category': 'law',
                'uploaded_by': 1
            }
            
            response = requests.post(
                f"{base_url}/api/v1/documents/upload",
                files=files,
                data=data
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"Document ID: {result['data']['document_id']}")
            print(f"Chunks created: {result['data']['chunks_created']}")
            print(f"Law sources processed: {result['data']['law_sources_processed']}")
            print(f"Articles processed: {result['data']['articles_processed']}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_your_file()
    test_upload_your_file()
