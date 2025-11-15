#!/usr/bin/env python3
"""Check extraction progress and see if there are more characters to process."""
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from bulk_extract_characters import is_character_page

json_path = "data/extracted/extracted_data.json"
checkpoint_path = "data/characters/bulk_extract_full_20251114-083000/bulk_extraction_checkpoint.json"

print("Loading data...")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

with open(checkpoint_path, "r", encoding="utf-8") as f:
    checkpoint = json.load(f)

pages = data["pages"]
processed_set = set(checkpoint["processed"])

print(f"Total pages: {len(pages):,}")
print(f"Processed characters: {len(processed_set):,}")

print("\nScanning for character pages...")
character_pages = []
for i, page in enumerate(pages):
    if is_character_page(page):
        char = page.get("title", "")
        if char and char not in processed_set:
            character_pages.append(char)
    if (i + 1) % 10000 == 0:
        print(f"  Scanned {i+1:,} pages, found {len(character_pages)} unprocessed characters so far...")

print(f"\nTotal unprocessed characters found: {len(character_pages)}")
if character_pages:
    print(f"First 10 remaining: {character_pages[:10]}")
else:
    print("All characters have been processed!")

