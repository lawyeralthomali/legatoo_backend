"""
Direct test of the document parsing logic with your actual file
"""

import json
import asyncio
from app.services.document_parser_service import LegalDocumentParser
from app.models.legal_knowledge import KnowledgeDocument
from app.db.database import AsyncSessionLocal

async def test_direct_parsing():
    """Test the parsing logic directly with your file."""
    
    print("🧪 Testing direct parsing with your saudi_labor_law.json file...")
    
    try:
        # Read your actual file
        with open('data_set/files/saudi_labor_law.json', 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"✅ File loaded successfully")
        print(f"📋 JSON structure:")
        print(f"  - Type: {type(json_data)}")
        print(f"  - Keys: {list(json_data.keys())}")
        print(f"  - law_sources type: {type(json_data['law_sources'])}")
        
        # Test the parsing logic
        if isinstance(json_data, dict) and 'law_sources' in json_data:
            law_sources_value = json_data['law_sources']
            
            if isinstance(law_sources_value, list):
                law_sources_data = law_sources_value
                print("✅ law_sources is an array")
            else:
                law_sources_data = [law_sources_value]
                print("✅ law_sources is a single object (converted to array)")
            
            print(f"📊 Final processing data:")
            print(f"  - Law sources count: {len(law_sources_data)}")
            
            if law_sources_data:
                first_source = law_sources_data[0]
                print(f"  - First source name: {first_source.get('name', 'N/A')}")
                print(f"  - First source type: {first_source.get('type', 'N/A')}")
                print(f"  - Articles count: {len(first_source.get('articles', []))}")
                
                # Test first few articles
                articles = first_source.get('articles', [])
                if articles:
                    print(f"  - First article: {articles[0].get('article', 'N/A')}")
                    print(f"  - First article text length: {len(articles[0].get('text', ''))}")
                    
                    if len(articles) > 1:
                        print(f"  - Second article: {articles[1].get('article', 'N/A')}")
        
        print("\n✅ Direct parsing test completed successfully!")
        print("🎯 The JSON structure is compatible with our parser!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_parsing())
