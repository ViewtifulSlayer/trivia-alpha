#!/usr/bin/env python3
"""Debug description extraction."""

import json
import re
from generate_questions import clean_mediawiki_markup

data = json.load(open('../data/extracted/extracted_data.json', 'r', encoding='utf-8'))
pages = data['pages']

# Find Time's Orphan
times_orphan = [p for p in pages if 'time' in p.get('title', '').lower() and 'orphan' in p.get('title', '').lower() and 'episode' in p.get('title', '').lower()]

if times_orphan:
    ep = times_orphan[0]
    text = ep.get('full_text', '')
    
    print("Raw description area (first 500 chars after }}):")
    desc_start = text.find('}}')
    if desc_start > 0:
        desc_area = text[desc_start:desc_start+500]
        print(desc_area)
        print("\n" + "="*60)
        
        # Try to extract description
        desc_match = re.search(r'\}\}\s*([^=]+?)(?:==|$)', text, re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()
            print("Extracted description:")
            print(description)
            print("\n" + "="*60)
            
            # Clean it
            cleaned = clean_mediawiki_markup(description)
            print("Cleaned description:")
            print(cleaned)
            print("\n" + "="*60)
            
            # Try to find "Molly O'Brien"
            if "Molly" in cleaned or "molly" in cleaned.lower():
                print("Found 'Molly' in description!")
                # Find context
                molly_pos = cleaned.lower().find("molly")
                if molly_pos >= 0:
                    context = cleaned[max(0, molly_pos-50):molly_pos+100]
                    print(f"Context around 'Molly': {context}")
            
            # Try plain name pattern
            plain_name_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b')
            names = plain_name_pattern.findall(cleaned)
            print(f"\nFound names: {names}")

