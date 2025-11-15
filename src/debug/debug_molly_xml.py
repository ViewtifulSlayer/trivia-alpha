#!/usr/bin/env python3
"""Debug: Check what the Molly O'Brien page looks like in XML."""

import xml.etree.ElementTree as ET

NS = '{http://www.mediawiki.org/xml/export-0.11/}'

xml_path = '../data/raw/enmemoryalpha_pages_current.xml'

print("Searching for 'Molly O'Brien' page...")

for event, elem in ET.iterparse(xml_path, events=('start', 'end')):
    if event == 'end' and elem.tag == f'{NS}page':
        title_elem = elem.find(f'{NS}title')
        ns_elem = elem.find(f'{NS}ns')
        revision_elem = elem.find(f'{NS}revision')
        
        if title_elem is not None and revision_elem is not None:
            title = title_elem.text or ''
            ns = ns_elem.text if ns_elem is not None else '0'
            
            if ns == '0' and 'molly' in title.lower() and 'obrien' in title.lower() and 'file' not in title.lower():
                text_elem = revision_elem.find(f'{NS}text')
                if text_elem is not None and text_elem.text:
                    text = text_elem.text
                    print(f"\nFound: {title}")
                    print(f"Text length: {len(text)}")
                    print(f"\nFirst 2000 characters:")
                    print(text[:2000])
                    print("\n" + "="*60)
                    print("Looking for key patterns...")
                    
                    # Check for species
                    if 'Species' in text or 'species' in text:
                        print("Found 'Species' in text")
                        # Find context
                        species_pos = text.lower().find('species')
                        if species_pos >= 0:
                            print(f"Context: {text[max(0, species_pos-50):species_pos+100]}")
                    
                    # Check for birth
                    if 'Born' in text or 'born' in text:
                        print("\nFound 'Born' in text")
                        born_pos = text.lower().find('born')
                        if born_pos >= 0:
                            print(f"Context: {text[max(0, born_pos-50):born_pos+150]}")
                    
                    # Check for father
                    if 'Father' in text or 'father' in text:
                        print("\nFound 'Father' in text")
                        father_pos = text.lower().find('father')
                        if father_pos >= 0:
                            print(f"Context: {text[max(0, father_pos-50):father_pos+150]}")
                    
                    # Check for mother
                    if 'Mother' in text or 'mother' in text:
                        print("\nFound 'Mother' in text")
                        mother_pos = text.lower().find('mother')
                        if mother_pos >= 0:
                            print(f"Context: {text[max(0, mother_pos-50):mother_pos+150]}")
                    
                    break
        
        elem.clear()

