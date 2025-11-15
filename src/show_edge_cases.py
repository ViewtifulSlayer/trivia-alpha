#!/usr/bin/env python3
"""Show the 3 edge case unverified questions with their source data."""
import json
import os

# Load questions
with open('data/questions_from_616_characters.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

unverified = [q for q in questions if not q.get('verified', True)]

print("=" * 70)
print("EDGE CASES - 3 Unverified Questions")
print("=" * 70)

for i, q in enumerate(unverified, 1):
    print(f"\n{i}. {q.get('question')}")
    print(f"   Answer: {q.get('answer')}")
    print(f"   Character: {q.get('character')}")
    print(f"   Source: {q.get('source')}")
    print(f"   Type: {q.get('type')}")

# Load character data
print("\n" + "=" * 70)
print("SOURCE DATA FROM CHARACTER JSONS")
print("=" * 70)

char_dir = 'data/characters/bulk_extract_family_fixed_20251114-171343'
edge_characters = ['B\'Etor', 'Duras, son of Ja\'rod', 'Kang']

for char_name in edge_characters:
    # Find the file
    safe_name = char_name.lower().replace(' ', '_').replace(',', '').replace('\'', '').replace(' ', '_')
    possible_files = [
        f"{safe_name}.json",
        f"{char_name.lower().replace(' ', '_').replace(',', '_').replace('\'', '_')}.json",
        f"{char_name.lower().replace(' ', '_').replace(',', '').replace('\'', '')}.json"
    ]
    
    found = False
    for filename in os.listdir(char_dir):
        if filename.endswith('.json') and filename != 'bulk_extraction_checkpoint.json':
            with open(os.path.join(char_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('character', {}).get('name') == char_name:
                    found = True
                    char = data.get('character', {})
                    print(f"\n{char_name}:")
                    print(f"  Siblings: {char.get('siblings', [])}")
                    print(f"  Children: {char.get('children', [])}")
                    print(f"  Spouses: {char.get('spouses', [])}")
                    break
    
    if not found:
        print(f"\n{char_name}: NOT FOUND")

