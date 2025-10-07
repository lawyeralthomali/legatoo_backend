import json

try:
    with open('files/extracted_legal_structure.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("✅ JSON is valid")
    print(f"Law sources: {len(data.get('law_sources', []))}")
except json.JSONDecodeError as e:
    print(f"❌ JSON Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
