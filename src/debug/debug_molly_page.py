#!/usr/bin/env python3
"""Debug: Check what the Molly O'Brien page looks like in extracted JSON."""

import json
import re

json_path = '../data/extracted/extracted_data.json'

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

pages = data.get('pages', [])

# Find Molly O'Brien
for page in pages:
    if page.get('title', '').lower() == 'molly o\'brien':
        print(f"Found: {page['title']}")
        print(f"Series: {page.get('series', [])}")
        print(f"\nFull text (first 3000 chars):")
        print(page.get('full_text', '')[:3000])
        print("\n" + "="*60)
        
        # Look for specific patterns
        text = page.get('full_text', '')
        
        # Find "Species:" or similar
        if 'Species' in text or 'species' in text:
            species_pos = text.lower().find('species')
            print(f"\n'Species' found at position {species_pos}:")
            print(text[max(0, species_pos-30):species_pos+100])
        
        # Find "Born:" or similar
        if 'Born' in text or 'born' in text:
            born_pos = text.lower().find('born')
            print(f"\n'Born' found at position {born_pos}:")
            print(text[max(0, born_pos-30):born_pos+150])
        
        # Find "Father:"
        if 'Father' in text:
            father_pos = text.find('Father')
            print(f"\n'Father' found at position {father_pos}:")
            print(text[max(0, father_pos-30):father_pos+150])
        
        # Find "Mother:"
        if 'Mother' in text:
            mother_pos = text.find('Mother')
            print(f"\n'Mother' found at position {mother_pos}:")
            print(text[max(0, mother_pos-30):mother_pos+150])
        
        # Find "Sibling"
        if 'Sibling' in text or 'Brother' in text:
            sibling_pos = text.lower().find('sibling')
            if sibling_pos < 0:
                sibling_pos = text.lower().find('brother')
            print(f"\n'Sibling/Brother' found at position {sibling_pos}:")
            print(text[max(0, sibling_pos-30):sibling_pos+150])
        
        break

