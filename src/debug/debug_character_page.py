#!/usr/bin/env python3
"""
Debug tool to examine raw character page content from JSON.
Shows MediaWiki markup, highlights key sections, and helps identify extraction issues.
"""

import json
import sys
import re
from typing import Optional

def load_character_page(json_path: str, character_name: str) -> Optional[dict]:
    """Load character page from JSON file."""
    print(f"Loading JSON file: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = data.get('pages', [])
    character_name_lower = character_name.lower()
    
    # Find by exact title match
    for page in pages:
        if page.get('title', '').lower() == character_name_lower:
            return page
    
    # Try with (character) suffix
    for page in pages:
        title_lower = page.get('title', '').lower()
        if title_lower == character_name_lower + ' (character)':
            return page
    
    print(f"Character '{character_name}' not found")
    return None

def extract_sidebar_section(text: str) -> str:
    """Extract the sidebar template section."""
    # Look for {{Sidebar character}} or similar
    sidebar_match = re.search(r'\{\{Sidebar\s+character[^}]*\}\}(.*?)(?=\n==|\{\{|$)', text, re.DOTALL)
    if sidebar_match:
        return sidebar_match.group(1)
    return ""

def highlight_sections(text: str) -> dict:
    """Identify and extract key sections of the page."""
    sections = {
        'sidebar': '',
        'infobox': '',
        'first_paragraph': '',
        'notable_sections': []
    }
    
    # Extract sidebar
    sidebar_match = re.search(r'\{\{Sidebar\s+character[^}]*\}\}(.*?)(?=\n==|\{\{|$)', text, re.DOTALL)
    if sidebar_match:
        sections['sidebar'] = sidebar_match.group(1)
    
    # Extract infobox if different format
    infobox_match = re.search(r'\{\{Infobox[^}]*\}\}(.*?)(?=\n==|\{\{|$)', text, re.DOTALL)
    if infobox_match:
        sections['infobox'] = infobox_match.group(1)
    
    # Get first paragraph (usually after intro templates)
    first_para_match = re.search(r'(?:==\s*[^=]+\s*==\s*)?([^\n=]{100,500})', text)
    if first_para_match:
        sections['first_paragraph'] = first_para_match.group(1)[:500]
    
    # Find section headers
    section_headers = re.findall(r'^==\s*([^=]+)\s*==', text, re.MULTILINE)
    sections['notable_sections'] = section_headers[:10]  # First 10 sections
    
    return sections

def analyze_field_extraction(text: str, field_name: str) -> dict:
    """Analyze what patterns exist for a specific field."""
    analysis = {
        'found': False,
        'patterns': [],
        'raw_value': None
    }
    
    # Common field patterns
    patterns = {
        'species': [
            r'\|\s*species\s*=\s*\[\[([^\]]+)\]\]',
            r'\|\s*species\s*=\s*([^\n\|]+)',
            r'Species[:\s]+\[\[([^\]]+)\]\]',
        ],
        'born': [
            r'\|\s*born\s*=\s*\[\[(\d{4})\]\]',
            r'\|\s*born\s*=\s*([^\n\|]+)',
            r'Born[:\s]+(\d{4})',
        ],
        'status': [
            r'\|\s*status\s*=\s*([^\n\|]+)',
            r'\|\s*datestatus\s*=\s*([^\n\|]+)',
            r'Status[:\s]+([^\n\|]+)',
        ],
        'father': [
            r'\|\s*father\s*=\s*\[\[([^\]]+)\]\]',
            r'\|\s*father\s*=\s*([^\n\|]+)',
        ],
        'mother': [
            r'\|\s*mother\s*=\s*\[\[([^\]]+)\]\]',
            r'\|\s*mother\s*=\s*([^\n\|]+)',
        ],
        'spouse': [
            r'\|\s*spouse\s*=\s*\[\[([^\]]+)\]\]',
            r'\|\s*spouse\s*=\s*([^\n\|]+)',
        ],
        'children': [
            r'\|\s*children\s*=\s*\[\[([^\]]+)\]\]',
            r'\|\s*children\s*=\s*([^\n\|]+)',
        ],
        'actor': [
            r'\|\s*actor\s*=\s*\[\[([^\]]+)\]\]',
            r'\|\s*portrayed\s*=\s*\[\[([^\]]+)\]\]',
            r'\|\s*portrayed\s+by\s*=\s*\[\[([^\]]+)\]\]',
        ],
    }
    
    if field_name.lower() in patterns:
        for pattern in patterns[field_name.lower()]:
            matches = re.finditer(pattern, text[:5000], re.IGNORECASE)
            for match in matches:
                analysis['found'] = True
                analysis['patterns'].append({
                    'pattern': pattern,
                    'match': match.group(0),
                    'value': match.group(1) if match.lastindex else match.group(0)
                })
                if not analysis['raw_value']:
                    analysis['raw_value'] = match.group(1) if match.lastindex else match.group(0)
    
    return analysis

def print_page_analysis(page: dict, character_name: str):
    """Print detailed analysis of the character page."""
    title = page.get('title', '')
    full_text = page.get('full_text', '')
    text_length = len(full_text)
    
    print("=" * 80)
    print(f"CHARACTER PAGE ANALYSIS: {title}")
    print("=" * 80)
    print(f"\nPage Stats:")
    print(f"  Title: {title}")
    print(f"  Text Length: {text_length:,} characters")
    print(f"  Series: {', '.join(page.get('series', []))}")
    print(f"  Characters mentioned: {len(page.get('characters', []))}")
    
    # Extract sections
    sections = highlight_sections(full_text)
    
    print(f"\n{'=' * 80}")
    print("SIDEBAR SECTION (First 2000 chars):")
    print("=" * 80)
    if sections['sidebar']:
        sidebar_preview = sections['sidebar'][:2000]
        print(sidebar_preview)
        if len(sections['sidebar']) > 2000:
            print(f"\n... ({len(sections['sidebar']) - 2000} more characters)")
    else:
        print("No sidebar section found")
    
    print(f"\n{'=' * 80}")
    print("FIRST PARAGRAPH:")
    print("=" * 80)
    if sections['first_paragraph']:
        print(sections['first_paragraph'])
    else:
        print("No first paragraph found")
    
    print(f"\n{'=' * 80}")
    print("SECTION HEADERS:")
    print("=" * 80)
    for i, section in enumerate(sections['notable_sections'], 1):
        print(f"  {i}. {section}")
    
    print(f"\n{'=' * 80}")
    print("FIELD EXTRACTION ANALYSIS:")
    print("=" * 80)
    
    fields_to_check = ['species', 'born', 'status', 'father', 'mother', 'spouse', 'children', 'actor']
    for field in fields_to_check:
        analysis = analyze_field_extraction(full_text, field)
        status = "[FOUND]" if analysis['found'] else "[NOT FOUND]"
        print(f"\n{field.upper()}: {status}")
        if analysis['found']:
            print(f"  Raw value: {analysis['raw_value']}")
            print(f"  Patterns matched: {len(analysis['patterns'])}")
            for i, pattern_info in enumerate(analysis['patterns'][:3], 1):
                print(f"    {i}. Pattern: {pattern_info['pattern'][:60]}...")
                print(f"       Match: {pattern_info['match'][:80]}")
    
    print(f"\n{'=' * 80}")
    print("RAW TEXT PREVIEW (First 3000 characters):")
    print("=" * 80)
    print(full_text[:3000])
    if text_length > 3000:
        print(f"\n... ({text_length - 3000:,} more characters)")

def main():
    if len(sys.argv) < 3:
        print("Usage: python debug_character_page.py <json_file> <character_name>")
        print("\nExample:")
        print("  python debug_character_page.py ../data/extracted/extracted_data.json 'Molly O'Brien'")
        sys.exit(1)
    
    json_path = sys.argv[1]
    character_name = sys.argv[2]
    
    page = load_character_page(json_path, character_name)
    if not page:
        sys.exit(1)
    
    print_page_analysis(page, character_name)
    
    # Optionally load extracted JSON for comparison
    safe_name = character_name.lower().replace(' ', '_').replace("'", "")
    extracted_path = f"../data/characters/{safe_name}.json"
    try:
        with open(extracted_path, 'r', encoding='utf-8') as f:
            extracted = json.load(f)
        print(f"\n{'=' * 80}")
        print("EXTRACTED DATA SUMMARY:")
        print("=" * 80)
        char_data = extracted.get('character', {})
        print(f"  Species: {char_data.get('species')}")
        print(f"  Status: {char_data.get('status')}")
        print(f"  Born: {char_data.get('born', {}).get('year')} on {char_data.get('born', {}).get('location')}")
        print(f"  Father: {char_data.get('family', {}).get('father')}")
        print(f"  Mother: {char_data.get('family', {}).get('mother')}")
        print(f"  Actors: {len(char_data.get('portrayed_by', []))}")
        print(f"  Notable Events: {len(char_data.get('notable_events', []))}")
        print(f"  Characteristics: {len(char_data.get('characteristics', []))}")
        print(f"  Trivia Facts: {len(extracted.get('trivia_facts', []))}")
    except FileNotFoundError:
        print(f"\nNote: No extracted JSON found at {extracted_path} for comparison")

if __name__ == '__main__':
    main()

