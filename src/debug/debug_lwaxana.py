#!/usr/bin/env python3
"""Debug: Check Lwaxana Troi page structure."""

import json

json_path = '../data/extracted/extracted_data.json'

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

pages = data.get('pages', [])

# Find Lwaxana Troi
for page in pages:
    if 'lwaxana' in page.get('title', '').lower() and 'troi' in page.get('title', '').lower():
        print(f"Found: {page['title']}")
        print(f"Series: {page.get('series', [])}")
        print(f"\nFull text (first 4000 chars):")
        text = page.get('full_text', '')
        print(text[:4000])
        print("\n" + "="*60)
        
        # Look for sidebar
        if 'sidebar' in text.lower():
            sidebar_start = text.lower().find('sidebar')
            print(f"\nSidebar found at position {sidebar_start}:")
            print(text[max(0, sidebar_start-50):sidebar_start+1000])
        
        break

