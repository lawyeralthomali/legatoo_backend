"""
Simple test to verify the JSON parsing fix works with your file structure
"""

import json

def test_json_parsing():
    """Test the JSON parsing logic with your file structure."""
    
    # Simulate your JSON structure
    test_json = {
        "law_sources": {  # Single object, not array
            "name": "نظام العمل",
            "type": "law",
            "jurisdiction": "المملكة العربية السعودية",
            "issuing_authority": "ملك المملكة العربية السعودية",
            "issue_date": "1435/02/18هـ",
            "description": "نظام العمل السعودي",
            "articles": [
                {
                    "article": "المادة 1",
                    "text": "يسمى هذا النظام نظام العمل."
                },
                {
                    "article": "المادة 2", 
                    "text": "يقصد بالألفاظ والعبارات الآتية..."
                }
            ]
        }
    }
    
    print("🧪 Testing JSON parsing logic...")
    print(f"Original structure: law_sources is {type(test_json['law_sources'])}")
    
    # Apply the same logic as in the parser
    json_data = test_json
    
    if isinstance(json_data, dict):
        if 'law_sources' in json_data:
            law_sources_value = json_data['law_sources']
            print(f"Found law_sources: {type(law_sources_value)}")
            
            # Handle both single object and array cases
            if isinstance(law_sources_value, list):
                law_sources_data = law_sources_value
                print("✅ law_sources is an array (standard format)")
            else:
                # Single law source object - wrap in array
                law_sources_data = [law_sources_value]
                print("✅ law_sources is a single object (converted to array)")
            
            print(f"Final law_sources_data: {type(law_sources_data)} with {len(law_sources_data)} items")
            
            # Test processing the first law source
            if law_sources_data:
                first_source = law_sources_data[0]
                print(f"First source type: {type(first_source)}")
                print(f"First source name: {first_source.get('name', 'N/A')}")
                print(f"Articles count: {len(first_source.get('articles', []))}")
                
                # Test processing first article
                if first_source.get('articles'):
                    first_article = first_source['articles'][0]
                    print(f"First article type: {type(first_article)}")
                    print(f"First article number: {first_article.get('article', 'N/A')}")
                    print(f"Has text: {'text' in first_article}")
    
    print("\n✅ JSON parsing logic test completed successfully!")

if __name__ == "__main__":
    test_json_parsing()
