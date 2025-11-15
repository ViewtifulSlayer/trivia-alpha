#!/usr/bin/env python3
"""
Scan character pages for family-related fields to identify patterns.
This will help expand the extraction to handle all family relationships.
"""

import xml.etree.ElementTree as ET
import sys
import re
import json
from collections import defaultdict

NS = '{http://www.mediawiki.org/xml/export-0.11/}'

def clean_mediawiki_markup(text: str) -> str:
    """Remove MediaWiki markup from text."""
    # Remove links: [[Link]] or [[Link|Display]]
    text = re.sub(r'\[\[([^\]]+)\]\]', lambda m: m.group(1).split('|')[-1], text)
    # Remove templates: {{template}}
    text = re.sub(r'\{\{[^\}]+\}\}', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def extract_family_fields(text: str) -> dict:
    """Extract all family-related fields from sidebar."""
    fields = {
        'father': None,
        'mother': None,
        'spouse': [],
        'children': [],
        'siblings': [],
        'relative': [],
        'other_family': []
    }
    
    # Look for family fields in sidebar (first 5000 chars)
    sidebar_text = text[:5000]
    
    # Father
    father_match = re.search(r'\|\s*father\s*=\s*([^\n]+)', sidebar_text, re.I)
    if father_match:
        father_text = father_match.group(1)
        # Extract links
        father_links = re.findall(r'\[\[([^\]]+)\]\]', father_text)
        if father_links:
            fields['father'] = clean_mediawiki_markup(father_links[0])
    
    # Mother
    mother_match = re.search(r'\|\s*mother\s*=\s*([^\n]+)', sidebar_text, re.I)
    if mother_match:
        mother_text = mother_match.group(1)
        mother_links = re.findall(r'\[\[([^\]]+)\]\]', mother_text)
        if mother_links:
            fields['mother'] = clean_mediawiki_markup(mother_links[0])
    
    # Spouse
    spouse_match = re.search(r'\|\s*spouse\s*=\s*([^\n]+)', sidebar_text, re.I)
    if spouse_match:
        spouse_text = spouse_match.group(1)
        # Split by <br> tags
        spouse_parts = re.split(r'<br\s*/?>', spouse_text, flags=re.I)
        for part in spouse_parts:
            part = part.strip()
            if part:
                # Extract name and relationship
                name_match = re.search(r'\[\[([^\]]+)\]\]', part)
                rel_match = re.search(r'\(([^)]+)\)', part)
                if name_match:
                    name = clean_mediawiki_markup(name_match.group(1))
                    relationship = clean_mediawiki_markup(rel_match.group(1)) if rel_match else None
                    fields['spouse'].append({
                        'name': name,
                        'relationship': relationship,
                        'raw': part[:200]
                    })
    
    # Children
    children_match = re.search(r'\|\s*children\s*=\s*([^\n]+)', sidebar_text, re.I)
    if children_match:
        children_text = children_match.group(1)
        # Split by <br> tags
        children_parts = re.split(r'<br\s*/?>', children_text, flags=re.I)
        for part in children_parts:
            part = part.strip()
            if part:
                # Extract name and relationship
                name_match = re.search(r'\[\[([^\]]+)\]\]', part)
                rel_match = re.search(r'\(([^)]+)\)', part)
                if name_match:
                    name = clean_mediawiki_markup(name_match.group(1))
                    relationship = clean_mediawiki_markup(rel_match.group(1)) if rel_match else None
                    fields['children'].append({
                        'name': name,
                        'relationship': relationship,
                        'raw': part[:200]
                    })
    
    # Siblings
    sibling_match = re.search(r'\|\s*sibling\s*=\s*([^\n]+)', sidebar_text, re.I)
    if sibling_match:
        sibling_text = sibling_match.group(1)
        sibling_parts = re.split(r'<br\s*/?>', sibling_text, flags=re.I)
        for part in sibling_parts:
            part = part.strip()
            if part:
                name_match = re.search(r'\[\[([^\]]+)\]\]', part)
                rel_match = re.search(r'\(([^)]+)\)', part)
                if name_match:
                    name = clean_mediawiki_markup(name_match.group(1))
                    relationship = clean_mediawiki_markup(rel_match.group(1)) if rel_match else None
                    fields['siblings'].append({
                        'name': name,
                        'relationship': relationship,
                        'raw': part[:200]
                    })
    
    # Relative (catch-all for other relationships)
    relative_match = re.search(r'\|\s*relative\s*=\s*([^\n]+)', sidebar_text, re.I)
    if relative_match:
        relative_text = relative_match.group(1)
        relative_parts = re.split(r'<br\s*/?>', relative_text, flags=re.I)
        for part in relative_parts:
            part = part.strip()
            if part:
                # Extract name and relationship
                name_match = re.search(r'\[\[([^\]]+)\]\]', part)
                rel_match = re.search(r'\(([^)]+)\)', part)
                if name_match:
                    name = clean_mediawiki_markup(name_match.group(1))
                    relationship = clean_mediawiki_markup(rel_match.group(1)) if rel_match else None
                    fields['relative'].append({
                        'name': name,
                        'relationship': relationship,
                        'raw': part[:200]
                    })
    
    # Look for other family-related fields
    family_field_patterns = [
        r'\|\s*grandfather\s*=\s*([^\n]+)',
        r'\|\s*grandmother\s*=\s*([^\n]+)',
        r'\|\s*son\s*=\s*([^\n]+)',
        r'\|\s*daughter\s*=\s*([^\n]+)',
        r'\|\s*brother\s*=\s*([^\n]+)',
        r'\|\s*sister\s*=\s*([^\n]+)',
        r'\|\s*uncle\s*=\s*([^\n]+)',
        r'\|\s*aunt\s*=\s*([^\n]+)',
        r'\|\s*cousin\s*=\s*([^\n]+)',
        r'\|\s*nephew\s*=\s*([^\n]+)',
        r'\|\s*niece\s*=\s*([^\n]+)',
        r'\|\s*grandson\s*=\s*([^\n]+)',
        r'\|\s*granddaughter\s*=\s*([^\n]+)',
        r'\|\s*son-in-law\s*=\s*([^\n]+)',
        r'\|\s*daughter-in-law\s*=\s*([^\n]+)',
    ]
    
    for pattern in family_field_patterns:
        field_name = re.search(r'\|\s*(\w+)\s*=', pattern).group(1) if re.search(r'\|\s*(\w+)\s*=', pattern) else 'unknown'
        matches = re.finditer(pattern, sidebar_text, re.I)
        for match in matches:
            field_text = match.group(1)
            name_match = re.search(r'\[\[([^\]]+)\]\]', field_text)
            if name_match:
                name = clean_mediawiki_markup(name_match.group(1))
                fields['other_family'].append({
                    'field': field_name,
                    'name': name,
                    'raw': field_text[:200]
                })
    
    return fields

def scan_characters(xml_path: str, character_names: list = None, max_pages: int = None) -> dict:
    """Scan character pages for family fields."""
    results = {}
    page_count = 0
    
    print(f"Scanning character pages for family fields...")
    if character_names:
        print(f"Looking for: {', '.join(character_names)}")
    if max_pages:
        print(f"Maximum pages to scan: {max_pages}")
    print()
    
    for event, elem in ET.iterparse(xml_path, events=('start', 'end')):
        if event == 'end' and elem.tag == f'{NS}page':
            title_elem = elem.find(f'{NS}title')
            ns_elem = elem.find(f'{NS}ns')
            revision_elem = elem.find(f'{NS}revision')
            
            if title_elem is not None and revision_elem is not None:
                title = title_elem.text or ''
                ns = ns_elem.text if ns_elem is not None else '0'
                
                # Only process main namespace (0) articles
                if ns != '0':
                    elem.clear()
                    continue
                
                # Skip mirror/alternate universe variants
                if '(mirror)' in title.lower() or '(alternate)' in title.lower():
                    elem.clear()
                    continue
                
                # If character_names specified, only process those
                if character_names:
                    if not any(name.lower() in title.lower() for name in character_names):
                        elem.clear()
                        continue
                
                text_elem = revision_elem.find(f'{NS}text')
                if text_elem is not None and text_elem.text:
                    text = text_elem.text
                    
                    # Check if this looks like a character page (has sidebar)
                    if 'sidebar individual' in text or 'sidebar character' in text:
                        family_fields = extract_family_fields(text)
                        
                        # Only include if we found at least one family field
                        if any([
                            family_fields['father'],
                            family_fields['mother'],
                            family_fields['spouse'],
                            family_fields['children'],
                            family_fields['siblings'],
                            family_fields['relative'],
                            family_fields['other_family']
                        ]):
                            results[title] = family_fields
                            print(f"[OK] {title}")
                            if family_fields['spouse']:
                                print(f"  Spouse: {len(family_fields['spouse'])}")
                            if family_fields['children']:
                                print(f"  Children: {len(family_fields['children'])}")
                            if family_fields['relative']:
                                print(f"  Relatives: {len(family_fields['relative'])}")
                            if family_fields['other_family']:
                                print(f"  Other family: {len(family_fields['other_family'])}")
                            
                            page_count += 1
                            if max_pages and page_count >= max_pages:
                                break
            
            elem.clear()
    
    return results

def analyze_patterns(results: dict) -> dict:
    """Analyze extracted family fields to identify patterns."""
    analysis = {
        'field_usage': defaultdict(int),
        'relationship_types': defaultdict(int),
        'field_formats': defaultdict(list),
        'examples': {}
    }
    
    for character, fields in results.items():
        for field_name, field_value in fields.items():
            if field_value:
                if isinstance(field_value, list):
                    if field_value:
                        analysis['field_usage'][field_name] += len(field_value)
                        for item in field_value:
                            if isinstance(item, dict) and 'relationship' in item:
                                if item['relationship']:
                                    analysis['relationship_types'][item['relationship']] += 1
                            if isinstance(item, dict) and 'raw' in item:
                                analysis['field_formats'][field_name].append(item['raw'])
                else:
                    analysis['field_usage'][field_name] += 1
        
        # Store examples
        if character not in analysis['examples']:
            analysis['examples'][character] = fields
    
    return analysis

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scan_family_fields.py <xml_file> [character1] [character2] ... [--max N]")
        print("Example: python scan_family_fields.py enmemoryalpha_pages_current.xml 'Joseph Sisko' 'Benjamin Sisko'")
        sys.exit(1)
    
    xml_path = sys.argv[1]
    character_names = []
    max_pages = None
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--max':
            try:
                max_pages = int(sys.argv[i + 1])
                i += 2
            except (ValueError, IndexError):
                max_pages = 50
                i += 1
        elif not arg.startswith('--'):
            character_names.append(arg)
            i += 1
        else:
            i += 1
    
    # If no specific characters, scan a sample
    if not character_names:
        print("No specific characters provided. Scanning sample of character pages...")
        max_pages = max_pages or 100
    
    results = scan_characters(xml_path, character_names if character_names else None, max_pages)
    
    print(f"\n{'='*80}")
    print(f"Scanned {len(results)} character pages with family fields")
    print(f"{'='*80}\n")
    
    # Analyze patterns
    analysis = analyze_patterns(results)
    
    print("FIELD USAGE:")
    print("-" * 80)
    for field, count in sorted(analysis['field_usage'].items(), key=lambda x: -x[1]):
        print(f"  {field}: {count}")
    
    print("\nRELATIONSHIP TYPES FOUND:")
    print("-" * 80)
    for rel_type, count in sorted(analysis['relationship_types'].items(), key=lambda x: -x[1]):
        print(f"  {rel_type}: {count}")
    
    # Save results
    output_file = 'data/family_fields_scan.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'results': results,
            'analysis': {
                'field_usage': dict(analysis['field_usage']),
                'relationship_types': dict(analysis['relationship_types']),
                'total_characters': len(results)
            },
            'examples': analysis['examples']
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    print(f"Examples saved for: {', '.join(list(analysis['examples'].keys())[:10])}")

