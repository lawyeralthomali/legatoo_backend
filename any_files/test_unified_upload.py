"""
Test script for the new unified upload endpoint.
This demonstrates how to properly call POST /api/v1/laws/upload
"""

import requests

# Test the unified upload endpoint
def test_unified_upload_json():
    """Test uploading a JSON file"""
    
    url = "http://localhost:8000/api/v1/laws/upload"
    
    # Example JSON file path
    json_file_path = "data_set/cases/sample_case_upload.json"
    
    with open(json_file_path, 'rb') as f:
        files = {
            'file': ('sample_law.json', f, 'application/json')
        }
        
        response = requests.post(url, files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_unified_upload_pdf():
    """Test uploading a PDF file"""
    
    url = "http://localhost:8000/api/v1/laws/upload"
    
    # Example PDF file path
    pdf_file_path = "uploads/legal_documents/test.pdf"
    
    with open(pdf_file_path, 'rb') as f:
        files = {
            'file': ('test.pdf', f, 'application/pdf')
        }
        
        data = {
            'law_name': 'نظام العمل',
            'law_type': 'law',
            'jurisdiction': 'المملكة العربية السعودية',
            'issuing_authority': 'وزارة العمل',
            'description': 'نظام العمل السعودي'
        }
        
        response = requests.post(url, files=files, data=data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


# Correct way to call using curl:
# ======================================
# For JSON file:
"""
curl -X POST "http://localhost:8000/api/v1/laws/upload" \
  -F "file=@data_set/cases/sample_case_upload.json"
"""

# For PDF file with metadata:
"""
curl -X POST "http://localhost:8000/api/v1/laws/upload" \
  -F "file=@your_document.pdf" \
  -F "law_name=نظام العمل" \
  -F "law_type=law" \
  -F "jurisdiction=المملكة العربية السعودية" \
  -F "issuing_authority=وزارة العمل"
"""

# Using Python requests library:
"""
import requests

url = "http://localhost:8000/api/v1/laws/upload"

# Upload JSON file (auto-detects and processes)
with open('law_data.json', 'rb') as f:
    files = {'file': ('law_data.json', f, 'application/json')}
    response = requests.post(url, files=files)

# Upload PDF file (requires metadata)
with open('law_document.pdf', 'rb') as f:
    files = {'file': ('law_document.pdf', f, 'application/pdf')}
    data = {
        'law_name': 'Law Name',
        'law_type': 'law',
        'jurisdiction': 'Saudi Arabia'
    }
    response = requests.post(url, files=files, data=data)
"""

if __name__ == "__main__":
    # Uncomment to test
    # test_unified_upload_json()
    # test_unified_upload_pdf()
    pass

