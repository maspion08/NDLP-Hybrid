"""Quick check struktur annotations_round1.json"""
import json

with open('evaluation/annotations_round1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Type top-level: {type(data).__name__}")

if isinstance(data, list):
    print(f"Total items: {len(data)}")
    print(f"\nFirst item type: {type(data[0]).__name__}")
    print(f"First item content:")
    print(json.dumps(data[0], indent=2, ensure_ascii=False)[:1000])
    
    if len(data) > 1:
        print(f"\nSecond item type: {type(data[1]).__name__}")
        print(f"Second item (first 500 chars): {str(data[1])[:500]}")

elif isinstance(data, dict):
    print(f"Top-level keys: {list(data.keys())[:10]}")
    first_key = list(data.keys())[0]
    print(f"\nFirst key: {first_key}")
    print(f"Value type: {type(data[first_key]).__name__}")
    print(f"Value content: {json.dumps(data[first_key], indent=2, ensure_ascii=False)[:1000]}")