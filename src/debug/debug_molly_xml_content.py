#!/usr/bin/env python3
"""
Debug script to examine the actual XML content for Molly O'Brien
to understand the MediaWiki format and fix extraction patterns.
"""

import xml.etree.ElementTree as ET
import re
import sys

NS = '{http://www.mediawiki.org/xml/export-0.11/}'

def find_and_display_molly_page(xml_path):
    """Find Molly O'Brien page and display relevant sections."""
    print("Searching for 'Molly O'Brien' in XML file...")
    
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
                
                if 'molly' in title.lower() and "o'brien" in title.lower() and '(mirror)' not in title.lower():
                    text_elem = revision_elem.find(f'{NS}text')
                    if text_elem is not None and text_elem.text:
                        text = text_elem.text
                        print(f"\n{'='*80}")
                        print(f"Found: {title}")
                        print(f"{'='*80}\n")
                        
                        # Display first 2000 chars
                        print("FIRST 2000 CHARACTERS:")
                        print("-" * 80)
                        print(text[:2000])
                        print("-" * 80)
                        
                        # Look for specific patterns
                        print("\n\nSEARCHING FOR SPECIFIC PATTERNS:")
                        print("-" * 80)
                        
                        # Status
                        print("\n1. STATUS:")
                        status_matches = re.findall(r'\|.*status.*=.*', text[:5000], re.I)
                        for match in status_matches[:5]:
                            print(f"   {match[:200]}")
                        
                        # Born
                        print("\n2. BORN:")
                        born_matches = re.findall(r'\|.*born.*=.*', text[:5000], re.I)
                        for match in born_matches[:5]:
                            print(f"   {match[:200]}")
                        
                        # Sibling
                        print("\n3. SIBLING:")
                        sibling_matches = re.findall(r'\|.*sibling.*=.*', text[:5000], re.I)
                        for match in sibling_matches[:5]:
                            print(f"   {match[:200]}")
                        
                        # Actor
                        print("\n4. ACTOR:")
                        actor_matches = re.findall(r'\|.*actor.*=.*', text[:5000], re.I)
                        for match in actor_matches[:5]:
                            print(f"   {match[:200]}")
                        
                        # Look for "Yoshi" nickname
                        print("\n5. NICKNAME 'YOSHI':")
                        yoshi_matches = re.findall(r'.{0,100}Yoshi.{0,100}', text[:10000], re.I)
                        for match in yoshi_matches[:3]:
                            print(f"   {match}")
                        
                        # Look for "Lupi" doll
                        print("\n6. LUPI DOLL:")
                        lupi_matches = re.findall(r'.{0,100}Lupi.{0,100}', text[:10000], re.I)
                        for match in lupi_matches[:3]:
                            print(f"   {match}")
                        
                        # Look for characteristics
                        print("\n7. CHARACTERISTICS (loved, colored, etc.):")
                        char_matches = re.findall(r'.{0,100}(?:loved|colored|replicator|darts|aunt).{0,100}', text[:10000], re.I)
                        for match in char_matches[:5]:
                            print(f"   {match}")
                        
                        # Look for locations
                        print("\n8. LOCATIONS (Enterprise-D, Deep Space 9, Earth):")
                        loc_matches = re.findall(r'.{0,100}(?:Enterprise-D|Deep Space 9|Earth).{0,100}', text[:10000], re.I)
                        for match in loc_matches[:5]:
                            print(f"   {match}")
                        
                        # Look for grandparents
                        print("\n9. GRANDPARENTS:")
                        grand_matches = re.findall(r'\|.*(?:grandfather|grandmother).*=.*', text[:5000], re.I)
                        for match in grand_matches[:5]:
                            print(f"   {match[:200]}")
                        
                        print("\n" + "="*80)
                        break
            
            elem.clear()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python debug_molly_xml_content.py <xml_file>")
        sys.exit(1)
    
    find_and_display_molly_page(sys.argv[1])

