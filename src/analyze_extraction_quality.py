#!/usr/bin/env python3
"""Quick analysis of bulk extraction quality."""

import json
import os
import sys
from pathlib import Path

def analyze_character_file(filepath):
    """Analyze a character JSON file and return quality metrics."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    char = data.get('character', {})
    
    # Count timeline sections (everything except 'character' and 'appearances')
    timeline_sections = [k for k in data.keys() if k not in ['character', 'appearances']]
    timeline_count = len(timeline_sections)
    
    # Count total timeline items
    timeline_items = 0
    for section in timeline_sections:
        if isinstance(data[section], list):
            timeline_items += len(data[section])
    
    # Count appearances
    appearances = data.get('appearances', {})
    appearance_count = sum(len(eps) for eps in appearances.values() if isinstance(eps, list))
    
    # Check for key fields
    has_description = bool(char.get('description'))
    has_quote = bool(char.get('quote'))
    has_family = any([char.get('father'), char.get('mother'), char.get('siblings'), 
                      char.get('spouses'), char.get('children')])
    
    # File size
    file_size = os.path.getsize(filepath)
    
    # Categorize
    if timeline_count == 0 and appearance_count == 0:
        category = "STUB"
    elif timeline_items < 3 and appearance_count < 5:
        category = "MINIMAL"
    elif timeline_items >= 10 or appearance_count >= 10:
        category = "RICH"
    else:
        category = "GOOD"
    
    return {
        'name': char.get('name', 'Unknown'),
        'category': category,
        'timeline_sections': timeline_count,
        'timeline_items': timeline_items,
        'appearances': appearance_count,
        'has_description': has_description,
        'has_quote': has_quote,
        'has_family': has_family,
        'file_size': file_size,
        'timeline_section_names': timeline_sections
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_extraction_quality.py <directory>")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    results = []
    
    for json_file in directory.glob("*.json"):
        if json_file.name == "bulk_extraction_checkpoint.json":
            continue
        
        try:
            result = analyze_character_file(json_file)
            results.append(result)
        except Exception as e:
            print(f"Error analyzing {json_file.name}: {e}", file=sys.stderr)
    
    # Sort by category, then by timeline items
    results.sort(key=lambda x: (x['category'], -x['timeline_items']))
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"Analysis of {len(results)} character files")
    print(f"{'='*80}\n")
    
    # Group by category
    by_category = {}
    for r in results:
        cat = r['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(r)
    
    for category in ['RICH', 'GOOD', 'MINIMAL', 'STUB']:
        if category not in by_category:
            continue
        
        chars = by_category[category]
        print(f"\n{category} ({len(chars)} characters):")
        print("-" * 80)
        for char in chars:
            print(f"  {char['name']:30} | Sections: {char['timeline_sections']:2} | "
                  f"Items: {char['timeline_items']:3} | Appearances: {char['appearances']:3} | "
                  f"Desc: {'Y' if char['has_description'] else 'N'} | "
                  f"Quote: {'Y' if char['has_quote'] else 'N'} | "
                  f"Family: {'Y' if char['has_family'] else 'N'}")
    
    print(f"\n{'='*80}")
    print("Summary:")
    print(f"  RICH:   {len(by_category.get('RICH', []))}")
    print(f"  GOOD:   {len(by_category.get('GOOD', []))}")
    print(f"  MINIMAL: {len(by_category.get('MINIMAL', []))}")
    print(f"  STUB:   {len(by_category.get('STUB', []))}")

