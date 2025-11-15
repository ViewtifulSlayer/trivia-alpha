#!/usr/bin/env python3
"""Debug script to examine XML content for any character."""

import xml.etree.ElementTree as ET
import sys
import re

NS = '{http://www.mediawiki.org/xml/export-0.11/}'

def find_and_display_character(xml_path, character_name):
    """Find character page and display relevant sections."""
    print(f"Searching for '{character_name}' in XML file...")
    
    for event, elem in ET.iterparse(xml_path, events=('start', 'end')):
        if event == 'end' and elem.tag == f'{NS}page':
            title_elem = elem.find(f'{NS}title')
            ns_elem = elem.find(f'{NS}ns')
            revision_elem = elem.find(f'{NS}revision')
            
            if title_elem is not None and revision_elem is not None:
                title = title_elem.text or ''
                ns = ns_elem.text if ns_elem is not None else '0'
                
                if ns != '0':
                    elem.clear()
                    continue
                
                if character_name.lower() in title.lower() and '(mirror)' not in title.lower():
                    text_elem = revision_elem.find(f'{NS}text')
                    if text_elem is not None and text_elem.text:
                        text = text_elem.text
                        print(f"\n{'='*80}")
                        print(f"Found: {title}")
                        print(f"{'='*80}\n")
                        
                        # Display first 3000 chars
                        print("FIRST 3000 CHARACTERS:")
                        print("-" * 80)
                        print(text[:3000])
                        print("-" * 80)
                        
                        # Look for specific patterns
                        print("\n\nSEARCHING FOR SPECIFIC PATTERNS:")
                        print("-" * 80)
                        
                        # Status
                        print("\n1. STATUS:")
                        status_matches = re.findall(r'\|.*status.*=.*', text[:5000], re.I)
                        for match in status_matches[:3]:
                            print(f"   {match[:200]}")
                        
                        # Born
                        print("\n2. BORN:")
                        born_matches = re.findall(r'\|.*born.*=.*', text[:5000], re.I)
                        for match in born_matches[:3]:
                            print(f"   {match[:200]}")
                        
                        # Actor
                        print("\n3. ACTOR:")
                        actor_matches = re.findall(r'\|.*actor.*=.*', text[:5000], re.I)
                        for match in actor_matches[:3]:
                            print(f"   {match[:200]}")
                        
                        print("\n" + "="*80)
                        break
            
            elem.clear()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python debug_character_xml.py <xml_file> <character_name>")
        sys.exit(1)
    
    find_and_display_character(sys.argv[1], sys.argv[2])

