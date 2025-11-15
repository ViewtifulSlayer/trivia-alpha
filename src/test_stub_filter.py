#!/usr/bin/env python3
"""Test the stub filter on example files."""
import sys
import json
sys.path.insert(0, 'src')
from bulk_extract_characters import is_stub_character

test_files = [
    'septimus.json',      # Bad - should be STUB
    'strek.json',        # Bad - should be STUB
    'dan_king.json',     # Bad - should be STUB
    'kyle_riker.json',   # Good - should KEEP (has quote + description)
    'haynem.json',       # Excellent - should KEEP (has timeline events)
    'biddle.json',       # Bad - should be STUB
    'biddle_coleridge.json',  # Bad - should be STUB
]

for f in test_files:
    try:
        with open(f'data/characters/bulk_extract_full_20251114-083000/{f}', encoding='utf-8') as file:
            data = json.load(file)
        is_stub = is_stub_character(data)
        status = "STUB (reject)" if is_stub else "KEEP"
        print(f"{f:30} -> {status}")
    except Exception as e:
        print(f"{f:30} -> ERROR: {e}")

