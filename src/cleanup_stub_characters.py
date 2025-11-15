#!/usr/bin/env python3
"""Clean up already-extracted stub characters from the extraction directory."""
import os
import json
import sys
sys.path.insert(0, 'src')
from bulk_extract_characters import is_stub_character

extraction_dir = "data/characters/bulk_extract_full_20251114-083000"

if not os.path.exists(extraction_dir):
    print(f"Directory not found: {extraction_dir}")
    sys.exit(1)

stub_count = 0
kept_count = 0
error_count = 0

print(f"Scanning {extraction_dir} for stub characters...")
print("=" * 70)

for filename in os.listdir(extraction_dir):
    if not filename.endswith('.json') or filename == 'bulk_extraction_checkpoint.json':
        continue
    
    filepath = os.path.join(extraction_dir, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if is_stub_character(data):
            os.remove(filepath)
            stub_count += 1
            print(f"[REMOVED] {filename}")
        else:
            kept_count += 1
    
    except Exception as e:
        error_count += 1
        print(f"[ERROR] {filename}: {e}")

print("=" * 70)
print(f"Summary:")
print(f"  Removed stubs: {stub_count}")
print(f"  Kept: {kept_count}")
print(f"  Errors: {error_count}")
print(f"  Total processed: {stub_count + kept_count + error_count}")

