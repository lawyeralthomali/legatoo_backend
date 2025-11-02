"""
Test script for Document Upload API

This script provides examples and tests for the legal document upload API.
"""

import json
import requests
import os
from typing import Dict, Any


def create_sample_json_document() -> Dict[str, Any]:
    """Create a sample JSON legal document for testing."""
    return {
        "law_sources": [
            {
                "name": "نظام العمل السعودي - نموذج اختبار",
                "type": "law",
                "jurisdiction": "المملكة العربية السعودية",
                "issuing_authority": "وزارة الموارد البشرية والتنمية الاجتماعية",
                "issue_date": "2023-01-01",
                "last_update": "2023-12-01",
                "description": "نموذج اختبار لنظام العمل السعودي",
                "source_url": "https://example.com/test-law",
                "articles": [
                    {
                        "article": "1",
                        "title": "تعريفات أساسية",
                        "text": "في تطبيق أحكام هذا النظام يقصد بالكلمات والعبارات التالية المعاني المبينة أمام كل منها:\n\nالعامل: كل شخص طبيعي يعمل لدى صاحب عمل لقاء أجر.\nصاحب العمل: كل شخص طبيعي أو اعتباري يستخدم عاملاً أو أكثر.\nالأجر: كل ما يعطى للعامل مقابل عمله نقداً أو عيناً.",
                        "keywords": ["تعريفات", "عامل", "صاحب عمل", "أجر"],
                        "order_index": 1
                    },
                    {
                        "article": "2",
                        "title": "نطاق التطبيق",
                        "text": "يطبق هذا النظام على جميع العمال وأصحاب العمل في المملكة العربية السعودية، عدا:\n\n1- عمال الحكومة والقطاع العام.\n2- عمال الخدمة المنزلية.\n3- عمال الزراعة والرعي.",
                        "keywords": ["نطاق التطبيق", "عمال", "أصحاب عمل"],
                        "order_index": 2
                    }
                ]
            }
        ]
    }


def test_upload_endpoint(base_url: str = "http://localhost:8000") -> None:
    """Test the document upload endpoint."""
    
    print("🧪 Testing Document Upload API")
    print("=" * 50)
    
    # Create sample document
    sample_doc = create_sample_json_document()
    
    # Save to temporary file
    temp_file = "test_law_document.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(sample_doc, f, ensure_ascii=False, indent=2)
    
    try:
        # Test 1: Upload document
        print("📤 Test 1: Uploading document...")
        
        with open(temp_file, 'rb') as f:
            files = {'file': f}
            data = {
                'title': 'نظام العمل السعودي - اختبار',
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
            print(f"✅ Upload successful!")
            print(f"Document ID: {result['data']['document_id']}")
            print(f"Chunks created: {result['data']['chunks_created']}")
            print(f"Law sources: {result['data']['law_sources_processed']}")
            print(f"Articles: {result['data']['articles_processed']}")
            
            # Test 2: Get upload status
            print("\n📊 Test 2: Getting upload status...")
            doc_id = result['data']['document_id']
            
            status_response = requests.get(
                f"{base_url}/api/v1/documents/upload/status/{doc_id}"
            )
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                print(f"✅ Status retrieved!")
                print(f"Status: {status_result['data']['status']}")
                print(f"Chunks count: {status_result['data']['chunks_count']}")
                print(f"File size: {status_result['data']['file_size_bytes']} bytes")
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
                print(status_response.text)
        
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the server is running on", base_url)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"\n🧹 Cleaned up temporary file: {temp_file}")


def test_supported_formats(base_url: str = "http://localhost:8000") -> None:
    """Test the supported formats endpoint."""
    
    print("\n📋 Testing Supported Formats Endpoint")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/v1/documents/supported-formats")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Supported formats retrieved!")
            print(f"Supported formats: {result['data']['supported_formats']}")
            
            for format_info in result['data']['format_details'].items():
                format_type, details = format_info
                print(f"\n{format_type}:")
                print(f"  Status: {details['status']}")
                print(f"  Description: {details['description']}")
                if 'features' in details:
                    print(f"  Features: {', '.join(details['features'])}")
        else:
            print(f"❌ Failed to get supported formats: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the server is running on", base_url)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_error_cases(base_url: str = "http://localhost:8000") -> None:
    """Test error cases for the upload endpoint."""
    
    print("\n❌ Testing Error Cases")
    print("=" * 50)
    
    # Test 1: Invalid file type
    print("Test 1: Invalid file type...")
    try:
        files = {'file': ('test.txt', 'This is not a JSON file', 'text/plain')}
        data = {
            'title': 'Test Document',
            'category': 'law'
        }
        
        response = requests.post(
            f"{base_url}/api/v1/documents/upload",
            files=files,
            data=data
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 422:  # Validation error
            result = response.json()
            print(f"✅ Error handled correctly: {result['message']}")
        else:
            print(f"❌ Unexpected response: {response.text}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    # Test 2: Invalid category
    print("\nTest 2: Invalid category...")
    try:
        sample_doc = create_sample_json_document()
        temp_file = "test_invalid_category.json"
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(sample_doc, f, ensure_ascii=False, indent=2)
        
        with open(temp_file, 'rb') as f:
            files = {'file': f}
            data = {
                'title': 'Test Document',
                'category': 'invalid_category'  # Invalid category
            }
            
            response = requests.post(
                f"{base_url}/api/v1/documents/upload",
                files=files,
                data=data
            )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 422:
            result = response.json()
            print(f"✅ Error handled correctly: {result['message']}")
        else:
            print(f"❌ Unexpected response: {response.text}")
        
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")


def main():
    """Run all tests."""
    print("🚀 Document Upload API Test Suite")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Run tests
    test_upload_endpoint(base_url)
    test_supported_formats(base_url)
    test_error_cases(base_url)
    
    print("\n✅ Test suite completed!")
    print("\nTo run the server:")
    print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
