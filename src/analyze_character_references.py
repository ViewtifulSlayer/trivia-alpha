#!/usr/bin/env python3
"""Analyze character cross-references to find mentioned characters without pages."""
import json
from pathlib import Path
from collections import defaultdict

def analyze_references():
    """Find characters referenced in family relationships and other fields."""
    extract_dir = Path("data/characters/bulk_extract_full_20251114")
    
    if not extract_dir.exists():
        print("Extraction directory not found")
        return
    
    # Get all extracted character names
    json_files = [f for f in extract_dir.glob("*.json") if f.name != "bulk_extraction_checkpoint.json"]
    extracted_names = set()
    
    print(f"Loading {len(json_files)} extracted characters...")
    referenced_chars = defaultdict(int)
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            char = data.get('character', {})
            char_name = char.get('name', '')
            if char_name:
                extracted_names.add(char_name.lower())
            
            # Collect family references
            for field in ['father', 'mother', 'spouses', 'children', 'siblings']:
                value = char.get(field)
                if value:
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                referenced_chars[item.lower()] += 1
                            elif isinstance(item, dict):
                                name = item.get('name', '')
                                if name:
                                    referenced_chars[name.lower()] += 1
                    elif isinstance(value, str):
                        referenced_chars[value.lower()] += 1
            
            # Collect quote source references
            quote = char.get('quote', {})
            if isinstance(quote, dict):
                source = quote.get('source', '')
                if source:
                    # Try to extract character name from quote source
                    # Simple heuristic: first word before comma or "reciting"
                    parts = source.split(',')[0].split(' reciting')[0].split(' as ')[0]
                    # Remove MediaWiki formatting
                    parts = parts.replace("'''", "").replace("''", "").strip()
                    if parts and len(parts) > 2:
                        referenced_chars[parts.lower()] += 1
        
        except Exception as e:
            continue
    
    print(f"\nExtracted characters: {len(extracted_names)}")
    print(f"Unique referenced characters: {len(referenced_chars)}")
    
    # Find referenced characters not in extracted set
    missing = {name: count for name, count in referenced_chars.items() 
               if name not in extracted_names and len(name) > 2}
    
    print(f"\nReferenced but not extracted: {len(missing)}")
    print("\nTop 20 most-referenced missing characters:")
    sorted_missing = sorted(missing.items(), key=lambda x: x[1], reverse=True)[:20]
    for name, count in sorted_missing:
        print(f"  {name}: referenced {count} times")
    
    return len(missing)

if __name__ == "__main__":
    analyze_references()

