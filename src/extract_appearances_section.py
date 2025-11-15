#!/usr/bin/env python3
"""
Extract all episodes from the Appendices section of a character page.
This handles collapsible "show all" sections by searching the entire text.
"""

import json
import re
import sys

def extract_all_episodes(text: str) -> dict:
    """
    Extract ALL episode appearances from the entire page text.
    Searches for {{SERIES|Episode}} templates throughout, not just in specific sections.
    """
    appearances = {
        'TNG': [],
        'DS9': [],
        'TOS': [],
        'VOY': [],
        'ENT': [],
        'DIS': [],
        'PIC': [],
        'LD': [],
        'PRO': [],
        'SNW': []
    }
    
    # First, find series context (e.g., * {{DS9}})
    series_contexts = {}
    for series in ['TNG', 'DS9', 'TOS', 'VOY', 'ENT', 'DIS', 'PIC', 'LD', 'PRO', 'SNW']:
        # Find series header: * {{DS9}} or * {{LD}}
        series_match = re.search(
            rf'\*\s*\{{{{?{series}\}}?}}\s*\n(.*?)(?=\*\s*\{{{{?[A-Z]|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if series_match:
            series_contexts[series] = series_match.group(1)
    
    # Also search for direct {{SERIES|Episode}} patterns throughout
    series_patterns = {
        'TNG': re.compile(r'\{\{TNG\|([^\}]+)\}\}'),
        'DS9': re.compile(r'\{\{DS9\|([^\}]+)\}\}'),
        'TOS': re.compile(r'\{\{TOS\|([^\}]+)\}\}'),
        'VOY': re.compile(r'\{\{VOY\|([^\}]+)\}\}'),
        'ENT': re.compile(r'\{\{ENT\|([^\}]+)\}\}'),
        'DIS': re.compile(r'\{\{DIS\|([^\}]+)\}\}'),
        'PIC': re.compile(r'\{\{PIC\|([^\}]+)\}\}'),
        'LD': re.compile(r'\{\{LD\|([^\}]+)\}\}'),
        'PRO': re.compile(r'\{\{PRO\|([^\}]+)\}\}'),
        'SNW': re.compile(r'\{\{SNW\|([^\}]+)\}\}'),
    }
    
    # Pattern for {{e|Episode}} format (used in Appendices)
    e_pattern = re.compile(r'\{\{e\|([^\}]+)\}\}')
    
    for series, pattern in series_patterns.items():
        episodes = set()  # Use set to avoid duplicates
        
        # Method 1: Extract from series-specific context (Appendices section)
        if series in series_contexts:
            context_text = series_contexts[series]
            # Find all {{e|Episode}} in this series context
            for match in e_pattern.finditer(context_text):
                episode_raw = match.group(1)
                # Extract display text if pipe exists: Episode|display -> display
                if '|' in episode_raw:
                    episode = episode_raw.split('|', 1)[1].strip()
                else:
                    episode = episode_raw.strip()
                # Clean up any remaining markup
                episode = re.sub(r'\[\[([^\]]+)\]\]', r'\1', episode)  # Remove [[links]]
                episode = re.sub(r'<[^>]+>', '', episode)  # Remove HTML tags
                episode = re.sub(r'\s*\([^)]+\)\s*$', '', episode)  # Remove trailing (Season X) or (archive footage)
                episode = episode.strip()
                if episode and len(episode) > 1:
                    episodes.add(episode)
        
        # Method 2: Also search for direct {{SERIES|Episode}} patterns throughout text
        for match in pattern.finditer(text):
            episode_raw = match.group(1)
            # Extract display text if pipe exists: Episode|display -> display
            if '|' in episode_raw:
                episode = episode_raw.split('|', 1)[1].strip()
            else:
                episode = episode_raw.strip()
            # Clean up any remaining markup
            episode = re.sub(r'\[\[([^\]]+)\]\]', r'\1', episode)  # Remove [[links]]
            episode = re.sub(r'<[^>]+>', '', episode)  # Remove HTML tags
            episode = episode.strip()
            if episode and len(episode) > 1 and '|' not in episode:  # Avoid malformed entries
                episodes.add(episode)
        
        appearances[series] = sorted(list(episodes))  # Sort alphabetically
    
    return appearances

def extract_appearances_section(text: str) -> str:
    """Extract the Appendices section specifically."""
    # Look for == Appendices == or == Appearances == section
    appendices_match = re.search(
        r'==\s*(?:Appendices|Appearances)\s*==\s*(.*?)(?=\n==|$)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if appendices_match:
        return appendices_match.group(1)
    return ""

def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_appearances_section.py <json_path> <character_name>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    character_name = sys.argv[2]
    
    print(f"Loading JSON file: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = data.get('pages', [])
    character_name_lower = character_name.lower()
    
    # Find character page
    page = None
    for p in pages:
        title_lower = p.get('title', '').lower()
        if title_lower == character_name_lower or title_lower == character_name_lower + ' (character)':
            page = p
            break
    
    if not page:
        print(f"Character '{character_name}' not found")
        sys.exit(1)
    
    full_text = page.get('full_text', '')
    print(f"\nFound: {page.get('title')}")
    print(f"Text length: {len(full_text):,} characters\n")
    
    # Extract Appendices section
    appendices_text = extract_appearances_section(full_text)
    if appendices_text:
        print("=" * 80)
        print("APPENDICES SECTION:")
        print("=" * 80)
        print(appendices_text[:2000])  # First 2000 chars
        if len(appendices_text) > 2000:
            print(f"\n... ({len(appendices_text) - 2000} more characters)")
        print()
    else:
        print("No Appendices section found\n")
    
    # Extract ALL episodes from entire text
    print("=" * 80)
    print("ALL EPISODE APPEARANCES (from entire page):")
    print("=" * 80)
    appearances = extract_all_episodes(full_text)
    
    total = 0
    for series, episodes in appearances.items():
        if episodes:
            print(f"\n{series}: {len(episodes)} episodes")
            for episode in episodes:
                print(f"  - {episode}")
            total += len(episodes)
    
    print(f"\nTotal: {total} episode appearances")
    
    # Show JSON format
    print("\n" + "=" * 80)
    print("JSON FORMAT:")
    print("=" * 80)
    print(json.dumps({"appearances": appearances}, indent=2))

if __name__ == '__main__':
    main()

