"""Deep check struktur annotations_round1.json"""
import json

with open('evaluation/annotations_round1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*70)
print("METADATA")
print("="*70)
print(f"Round: {data.get('round')}")
print(f"Started: {data.get('started_at')}")
print(f"Completed at: {data.get('completed_at')}")
print(f"Completed: {data.get('completed')}")
print(f"Progress: {data.get('progress')}")

print("\n" + "="*70)
print("ANNOTATIONS STRUCTURE")
print("="*70)

annotations = data.get('annotations', {})
print(f"Type: {type(annotations).__name__}")

if isinstance(annotations, dict):
    print(f"Total entries: {len(annotations)}")
    
    # First key
    first_key = list(annotations.keys())[0]
    first_val = annotations[first_key]
    
    print(f"\nFirst key: '{first_key}'")
    print(f"First value type: {type(first_val).__name__}")
    print(f"First value content (full):")
    print(json.dumps(first_val, indent=2, ensure_ascii=False)[:2000])
    
    # Cek 3 entries first
    print("\n" + "="*70)
    print("FIRST 3 KEYS:")
    for i, key in enumerate(list(annotations.keys())[:3]):
        val = annotations[key]
        print(f"\n[{i+1}] Key: {key}")
        if isinstance(val, dict):
            print(f"    Fields: {list(val.keys())}")
        else:
            print(f"    Value: {str(val)[:200]}")

elif isinstance(annotations, list):
    print(f"Total entries: {len(annotations)}")
    print(f"\nFirst entry (full):")
    print(json.dumps(annotations[0], indent=2, ensure_ascii=False)[:2000])