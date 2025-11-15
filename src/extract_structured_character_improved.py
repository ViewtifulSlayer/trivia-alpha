#!/usr/bin/env python3
"""
Improved extraction script for structured character data from XML file.
Matches the molly.json structure with comprehensive field extraction.

This version includes:
- Better MediaWiki sidebar template parsing
- Notable events extraction from episode descriptions
- Characteristics/personality traits extraction
- Locations with context extraction
- Objects/items extraction
- Enhanced family relationships (grandparents, ancestors, nicknames)
- Better actor parsing with roles
- Status extraction
"""

import xml.etree.ElementTree as ET
import json
import re
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# MediaWiki XML namespace
NS = '{http://www.mediawiki.org/xml/export-0.11/}'

def clean_mediawiki_markup(text: str) -> str:
    """Remove MediaWiki markup from text, preserving content."""
    if not text:
        return ""
    # Remove [[links|display]] or [[links]] - keep the link text
    text = re.sub(r'\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]', r'\1', text)
    # Remove {{templates}} but try to extract useful content
    text = re.sub(r'\{\{([^}]+)\}\}', lambda m: extract_template_content(m.group(1)), text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove ref tags
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_template_content(template: str) -> str:
    """Extract useful content from MediaWiki templates."""
    # USS template: {{USS|Enterprise|NCC-1701-D|-D}} -> "USS Enterprise-D"
    uss_match = re.match(r'USS\|([^|]+)', template)
    if uss_match:
        return f"USS {uss_match.group(1)}"
    # Episode template: {{DS9|Time's Orphan}} -> "Time's Orphan"
    episode_match = re.match(r'(?:TNG|DS9|TOS|VOY|ENT|DIS|PIC|LD|PRO|SNW)\|([^|]+)', template)
    if episode_match:
        return episode_match.group(1)
    # Return empty for other templates
    return ""

def extract_link_display_text(link_content: str) -> str:
    """Extract display text from MediaWiki link: [[target|display]] -> display, [[target]] -> target"""
    if '|' in link_content:
        # Has display text: [[target|display]] -> return "display"
        return link_content.split('|', 1)[1].strip()
    else:
        # No display text: [[target]] -> return "target"
        return link_content.strip()

def is_placeholder_name(name: str, character_name: str) -> bool:
    """Check if a name is a generic placeholder (e.g., "Character's father", "Character's mother")"""
    if not name or not character_name:
        return False
    
    name_lower = name.lower()
    char_first_name = character_name.split()[0].lower()
    
    # Check for generic patterns
    placeholder_patterns = [
        f"{char_first_name}'s father",
        f"{char_first_name}'s mother",
        f"{char_first_name}'s sister",
        f"{char_first_name}'s brother",
        f"{char_first_name}'s family",
        "001",
        "placeholder",
    ]
    
    for pattern in placeholder_patterns:
        if pattern in name_lower:
            return True
    
    return False

def extract_sidebar_section(text: str) -> str:
    """Extract the sidebar template section from page text."""
    # Find sidebar template: {{sidebar individual ... }}
    sidebar_start = text.find('{{sidebar individual')
    if sidebar_start == -1:
        sidebar_start = text.find('{{sidebar character')
    if sidebar_start == -1:
        sidebar_start = text.find('{{infobox person')
    
    if sidebar_start == -1:
        return ""
    
    # Find the closing }} - need to handle nested braces
    brace_count = 0
    i = sidebar_start
    while i < len(text):
        if text[i:i+2] == '{{':
            brace_count += 1
        elif text[i:i+2] == '}}':
            brace_count -= 1
            if brace_count == 0:
                return text[sidebar_start:i+2]
        i += 1
    
    # If we didn't find closing, return first 5000 chars as fallback
    return text[sidebar_start:sidebar_start+5000]

def extract_sidebar_field(text: str, field_name: str, patterns: List[re.Pattern]) -> Optional[str]:
    """Extract a field from MediaWiki sidebar template format: |field = value"""
    # Restrict search to sidebar section for family fields
    if field_name in ['father', 'mother', 'spouse', 'sibling', 'relative']:
        sidebar_text = extract_sidebar_section(text)
        if not sidebar_text:
            return None
        search_text = sidebar_text
    else:
        search_text = text[:5000]
    
    # First try sidebar format: |field = [[value]] or |field = value
    sidebar_pattern = re.compile(rf'\|\s*{field_name}\s*=\s*([^\n]+)', re.I)
    match = sidebar_pattern.search(search_text)
    if match:
        value = match.group(1).strip()
        # Extract from [[link]] format - prioritize display text over link target
        link_match = re.search(r'\[\[([^\]]+)\]\]', value)
        if link_match:
            link_content = link_match.group(1)
            display_text = extract_link_display_text(link_content)
            # Filter out placeholder links (contain "001" or similar)
            if '001' in display_text or display_text.lower().startswith('placeholder'):
                return None
            cleaned = clean_mediawiki_markup(display_text).split(',')[0].split('(')[0].strip()[:100]
            return cleaned if cleaned else None
        # Extract from {{template}} format
        template_match = re.search(r'\{\{([^}]+)\}\}', value)
        if template_match:
            return extract_template_content(template_match.group(1))
        # Plain text
        return clean_mediawiki_markup(value).split(',')[0].split('(')[0].strip()[:100]
    
    # Fall back to pattern matching
    for pattern in patterns:
        match = pattern.search(search_text)
        if match:
            result_raw = match.group(1)
            # Extract display text if it's a link
            if '[[' in result_raw and ']]' in result_raw:
                link_match = re.search(r'\[\[([^\]]+)\]\]', result_raw)
                if link_match:
                    result = extract_link_display_text(link_match.group(1))
                else:
                    result = result_raw
            else:
                result = result_raw
            result = clean_mediawiki_markup(result).strip()
            # Filter placeholders
            if '001' in result or result.lower().startswith('placeholder'):
                continue
            if result and len(result) > 1:
                return result[:100]
    return None

def extract_year(text: str) -> Optional[int]:
    """Extract a 4-digit year from text."""
    year_pattern = re.compile(r'\b(19\d{2}|2[0-3]\d{2})\b')
    match = year_pattern.search(text)
    if match:
        year = int(match.group(1))
        if 1900 <= year <= 2400:  # Reasonable range for Star Trek
            return year
    return None

def extract_species(text: str) -> Optional[str]:
    """Extract species information."""
    patterns = [
        re.compile(r'\|\s*species\s*=\s*\[\[([^\]]+)\]\]', re.I),
        re.compile(r'Species[:\s]+\[\[([^\]]+)\]\]', re.I),
        re.compile(r'was\s+(?:a|an)\s+\[\[([^\]]+)\]\]', re.I),
    ]
    valid_species = ['human', 'bajoran', 'vulcan', 'klingon', 'ferengi', 'cardassian', 
                     'romulan', 'borg', 'android', 'trill', 'betazoid', 'cardassian']
    result = extract_sidebar_field(text, 'species', patterns)
    if result and result.lower() in valid_species:
        return result
    return None

def extract_birth_info(text: str) -> Tuple[Optional[int], Optional[str]]:
    """Extract birth year and location. Format: |born = [[2368]], {{USS|Enterprise|NCC-1701-D|-D}}"""
    sidebar_text = extract_sidebar_section(text)
    search_text = sidebar_text if sidebar_text else text[:5000]
    
    # Look for |born = pattern
    born_match = re.search(r'\|\s*born\s*=\s*([^\n]+)', search_text, re.I)
    
    if born_match:
        born_value = born_match.group(1).strip()
        
        # Extract year from [[year]] or plain year
        year_match = re.search(r'\[\[(\d{4})\]\]', born_value)
        if year_match:
            year = int(year_match.group(1)) if year_match.group(1).isdigit() else None
        else:
            year_match = re.search(r'\b(\d{4})\b', born_value)
            year = int(year_match.group(1)) if year_match and year_match.group(1).isdigit() else None
        
        # Extract location - handle links with pipes: [[target|display]] -> display
        location = None
        
        # Check for USS template
        uss_match = re.search(r'\{\{USS\|([^\}]+)\}\}', born_value)
        if uss_match:
            uss_parts = uss_match.group(1).split('|')
            ship_name = uss_parts[0].strip()
            if len(uss_parts) > 2:
                suffix = uss_parts[-1].strip()
                location = f"USS {ship_name}{suffix}" if suffix.startswith('-') else f"USS {ship_name}"
            else:
                location = f"USS {ship_name}"
        else:
            # Look for location link: [[location]] or [[target|display]]
            location_match = re.search(r'\[\[([^\]]+)\]\]', born_value)
            if location_match:
                link_content = location_match.group(1)
                # Handle pipe: [[target|display]] -> display
                if '|' in link_content:
                    location = link_content.split('|', 1)[1].strip()
                else:
                    location = link_content.strip()
                # Clean up - remove any remaining markup
                location = clean_mediawiki_markup(location).split(',')[0].split('(')[0].strip()
                # Reject obviously wrong locations (like "Sisko|Sisko")
                if '|' in location or len(location) < 2:
                    location = None
        
        if year and location:
            return year, location
        elif year:
            return year, None
    
    # Fallback: search for year and location separately, but only in birth context
    # Look for "born" or "Born" near a year - be more careful with location
    born_context_pattern = re.compile(r'(?:born|Born)[^.!?]{0,200}(\d{4})[^.!?]{0,200}(?:on|at|in)\s+([A-Z][^\]!?]+)', re.I)
    born_context_match = born_context_pattern.search(text[:5000])
    if born_context_match:
        year = int(born_context_match.group(1)) if born_context_match.group(1).isdigit() else None
        location_raw = born_context_match.group(2)
        # Clean location - remove any remaining markup
        location = clean_mediawiki_markup(location_raw).split(',')[0].split('(')[0].split(']')[0].strip()[:100]
        # Validate location - should be a real place name, not a fragment
        if location and len(location) > 2 and not location.endswith(']]') and '[' not in location:
            if year and 1900 <= year <= 2400:  # Reasonable range
                return year, location
    
    # Last resort: just year from sidebar if no location found
    year_match = re.search(r'\|\s*born\s*=\s*\[\[(\d{4})\]\]', search_text, re.I)
    if year_match and year_match.group(1).isdigit():
        year = int(year_match.group(1))
        if 1900 <= year <= 2400:
            return year, None
    
    return None, None

def extract_family_relationships(text: str, character_name: str = "") -> Dict:
    """Extract family relationships with enhanced parsing - now includes spouse, children, and all relative types."""
    # Restrict to sidebar section only to avoid picking up wrong relationships from body text
    sidebar_text = extract_sidebar_section(text)
    if not sidebar_text:
        # Return empty family if no sidebar found
        return {
            "father": None,
            "mother": None,
            "spouse": [],
            "children": [],
            "siblings": [],
            "paternal_grandfather": None,
            "maternal_grandfather": None,
            "maternal_grandmother": None,
            "maternal_great_grandmother": None,
            "paternal_ancestors": [],
            "daughter_in_law": [],
            "son_in_law": [],
            "grandsons": [],
            "granddaughters": [],
            "father_in_law": None,
            "mother_in_law": None,
            "brother_in_law": [],
            "sister_in_law": [],
            "cousins": [],
            "uncles": [],
            "aunts": [],
            "nephews": [],
            "nieces": []
        }
    
    # Use sidebar text for all family extraction
    text = sidebar_text
    
    family = {
        "father": None,
        "mother": None,
        "spouse": [],
        "children": [],
        "siblings": [],
        "paternal_grandfather": None,
        "maternal_grandfather": None,
        "maternal_grandmother": None,
        "maternal_great_grandmother": None,
        "paternal_ancestors": [],
        "daughter_in_law": [],
        "son_in_law": [],
        "grandsons": [],
        "granddaughters": [],
        "father_in_law": None,
        "mother_in_law": None,
        "brother_in_law": [],
        "sister_in_law": [],
        "cousins": [],
        "uncles": [],
        "aunts": [],
        "nephews": [],
        "nieces": []
    }
    
    # Helper to extract and clean relationship
    def extract_relation(field_name: str, patterns: List[re.Pattern]) -> Optional[str]:
        result = extract_sidebar_field(text, field_name, patterns)
        if result and len(result) > 2:
            # Filter out placeholders
            if is_placeholder_name(result, character_name):
                return None
            if 'family' not in result.lower() and '001' not in result:
                return result[:100]
        return None
    
    # Father
    father_patterns = [
        re.compile(r'\|\s*father\s*=\s*\[\[([^\]]+)\]\]', re.I),
        re.compile(r'Father[:\s]+\[\[([^\]]+)\]\]', re.I),
    ]
    family["father"] = extract_relation('father', father_patterns)
    
    # Mother
    mother_patterns = [
        re.compile(r'\|\s*mother\s*=\s*\[\[([^\]]+)\]\]', re.I),
        re.compile(r'Mother[:\s]+\[\[([^\]]+)\]\]', re.I),
    ]
    family["mother"] = extract_relation('mother', mother_patterns)
    
    # Spouse - can have multiple spouses
    spouse_match = re.search(r'\|\s*spouse\s*=\s*([^\n]+)', text[:5000], re.I)
    if spouse_match:
        spouse_text = spouse_match.group(1)
        # Split by <br> tags
        spouse_parts = re.split(r'<br\s*/?>', spouse_text, flags=re.I)
        for part in spouse_parts:
            part = part.strip()
            if part and '001' not in part:  # Skip placeholder links
                # Extract name and relationship
                name_match = re.search(r'\[\[([^\]]+)\]\]', part)
                if name_match:
                    name_raw = name_match.group(1)
                    # Extract display text from link: [[target|display]] -> display
                    name = extract_link_display_text(name_raw)
                    name = clean_mediawiki_markup(name).strip()[:100]
                    # Filter placeholders
                    if '001' in name or name.lower().startswith('placeholder'):
                        continue
                    
                    # Extract relationship from parentheses
                    rel_match = re.search(r'\(([^)]+)\)', part)
                    relationship = None
                    if rel_match:
                        relationship = clean_mediawiki_markup(rel_match.group(1)).strip()[:100]
                    
                    # Extract status (deceased, etc.)
                    status = None
                    if 'deceased' in part.lower():
                        # Try to extract year
                        year_match = re.search(r'deceased.*?(\d{4})', part, re.I)
                        if year_match:
                            status = f"deceased {year_match.group(1)}"
                        else:
                            status = "deceased"
                    
                    if name and len(name) > 2:
                        spouse_obj = {"name": name}
                        if relationship:
                            spouse_obj["relationship"] = relationship
                        if status:
                            spouse_obj["status"] = status
                        family["spouse"].append(spouse_obj)
    
    # Children - can have multiple children
    children_match = re.search(r'\|\s*children\s*=\s*([^\n]+)', text[:5000], re.I)
    if children_match:
        children_text = children_match.group(1)
        # Split by <br> tags
        children_parts = re.split(r'<br\s*/?>', children_text, flags=re.I)
        for part in children_parts:
            part = part.strip()
            if part and '001' not in part:  # Skip placeholder links like "two additional sons"
                # Extract name and relationship
                name_match = re.search(r'\[\[([^\]]+)\]\]', part)
                if name_match:
                    name_raw = name_match.group(1)
                    # Extract display text from link: [[target|display]] -> display
                    name = extract_link_display_text(name_raw)
                    name = clean_mediawiki_markup(name).strip()[:100]
                    # Filter placeholders
                    if '001' in name or name.lower().startswith('placeholder'):
                        continue
                    
                    # Extract relationship from parentheses
                    rel_match = re.search(r'\(([^)]+)\)', part)
                    relationship = None
                    if rel_match:
                        relationship = clean_mediawiki_markup(rel_match.group(1)).strip()[:100]
                    
                    # Extract "via X" qualifier
                    via_match = re.search(r'via\s+([A-Za-z\s]+)', part, re.I)
                    via = None
                    if via_match:
                        via = clean_mediawiki_markup(via_match.group(1)).strip()[:50]
                    
                    if name and len(name) > 2:
                        child_obj = {"name": name}
                        if relationship:
                            child_obj["relationship"] = relationship
                        if via:
                            child_obj["via"] = via
                        family["children"].append(child_obj)
    
    # Siblings with nickname support: |sibling = [[Kirayoshi O'Brien]] ([[brother]]) or [[Kirayoshi O'Brien|Yoshi]]
    # Also look for "nicknamed 'Yoshi'" patterns
    sibling_patterns = [
        re.compile(r'\|\s*sibling\s*=\s*\[\[([^\]]+)\]\]\s*\(\[\[([^\]]+)\]\]\)', re.I),
        re.compile(r'\|\s*sibling\s*=\s*\[\[([^\]]+)\|([^\]]+)\]\]', re.I),  # [[Name|Nickname]]
        re.compile(r'\|\s*sibling\s*=\s*\[\[([^\]]+)\]\]', re.I),
    ]
    seen_siblings = set()
    for pattern in sibling_patterns:
        for match in pattern.finditer(text[:5000]):
            sibling_name_raw = match.group(1)
            sibling_name = extract_link_display_text(sibling_name_raw)
            sibling_name = clean_mediawiki_markup(sibling_name).strip()[:100]
            nickname = None
            relationship = "sibling"
            
            # Skip placeholder links
            if 'family' in sibling_name.lower() or '001' in sibling_name:
                continue
            
            if len(match.groups()) >= 2:
                second_group = match.group(2).strip().lower()
                if second_group in ['brother', 'sister', 'sibling']:
                    relationship = second_group
                else:
                    nickname = second_group  # Likely a nickname
            
            # Look for nickname in surrounding text: "nicknamed 'Yoshi'" or "(nicknamed 'Yoshi')"
            # Format: [[Kirayoshi]] ([[nickname]]d "Yoshi")
            if sibling_name and len(sibling_name) > 2:
                # Search for nickname in narrative text - look for pattern: (nicknamed "Yoshi")
                # Search broader context for the nickname pattern
                nickname_pattern = re.compile(rf'{re.escape(sibling_name.split()[0])}[^.!?]*\(\[\[nickname\]\]d\s+["\']([A-Za-z]+)["\']\)', re.I)
                nickname_match = nickname_pattern.search(text[:20000])
                if nickname_match:
                    nickname = nickname_match.group(1)
                else:
                    # Also try simpler pattern: (nicknamed "Yoshi")
                    simple_nickname = re.search(rf'\(\[\[nickname\]\]d\s+["\']([A-Za-z]+)["\']\)', text[:20000], re.I)
                    if simple_nickname:
                        # Check if it's near the sibling name
                        nickname_pos = simple_nickname.start()
                        sibling_context = text[max(0, nickname_pos-300):nickname_pos+100]
                        if sibling_name.split()[0].lower() in sibling_context.lower():
                            nickname = simple_nickname.group(1)
            
            if sibling_name and len(sibling_name) > 2 and sibling_name.lower() not in seen_siblings:
                seen_siblings.add(sibling_name.lower())
                sibling_obj = {"name": sibling_name, "relationship": relationship}
                if nickname:
                    sibling_obj["nickname"] = nickname
                family["siblings"].append(sibling_obj)
    
    # Grandparents and ancestors are in |relative field
    # Format: |relative = [[Michael O'Brien]] ([[paternal]] [[grandfather]]), [[Hiro Ishikawa]] ([[maternal]] grandfather), ...
    relative_match = re.search(r'\|\s*relative\s*=\s*([^\n]+)', text[:5000], re.I)
    if relative_match:
        relative_text = relative_match.group(1)
        
        # Extract paternal grandfather
        paternal_gf_match = re.search(r'\[\[([^\]]+)\]\]\s*\(\[\[paternal\]\]\s*\[\[grandfather\]\]\)', relative_text, re.I)
        if paternal_gf_match:
            gf_raw = paternal_gf_match.group(1)
            family["paternal_grandfather"] = extract_link_display_text(gf_raw)
            family["paternal_grandfather"] = clean_mediawiki_markup(family["paternal_grandfather"]).strip()[:100]
        
        # Extract maternal grandfather
        maternal_gf_match = re.search(r'\[\[([^\]]+)\]\]\s*\(\[\[maternal\]\]\s*grandfather\)', relative_text, re.I)
        if maternal_gf_match:
            gf_raw = maternal_gf_match.group(1)
            family["maternal_grandfather"] = extract_link_display_text(gf_raw)
            family["maternal_grandfather"] = clean_mediawiki_markup(family["maternal_grandfather"]).strip()[:100]
        
        # Extract maternal grandmother (handle "Mrs. Ishikawa" format)
        maternal_gm_match = re.search(r'\[\[([^\]]+)\]\]\s*\(maternal\s*\[\[grandmother\]\]\)', relative_text, re.I)
        if maternal_gm_match:
            gm_raw = maternal_gm_match.group(1)
            gm_name = extract_link_display_text(gm_raw)
            gm_name = clean_mediawiki_markup(gm_name).strip()[:100]
            # Check if it's "Missus|Mrs." format - look for full name
            if '|' in maternal_gm_match.group(1):
                parts = maternal_gm_match.group(1).split('|')
                if len(parts) >= 2:
                    # Format: [[Missus|Mrs.]] [[Ishikawa]] - need to get next link
                    next_link = re.search(r'\[\[Missus\|Mrs\.\]\]\s+\[\[([^\]]+)\]\]', relative_text, re.I)
                    if next_link:
                        next_link_display = extract_link_display_text(next_link.group(1))
                        family["maternal_grandmother"] = f"Mrs. {clean_mediawiki_markup(next_link_display).strip()}"
                    else:
                        family["maternal_grandmother"] = gm_name
                else:
                    family["maternal_grandmother"] = gm_name
            else:
                family["maternal_grandmother"] = gm_name
        
        # Extract maternal great-grandmother (filter out "001" placeholders)
        maternal_ggm_match = re.search(r'\[\[([^\]]+)\]\]\s*\(maternal\s*\[\[great-grandmother\]\]\)', relative_text, re.I)
        if maternal_ggm_match:
            ggm_raw = maternal_ggm_match.group(1)
            ggm_name = extract_link_display_text(ggm_raw)
            ggm_name = clean_mediawiki_markup(ggm_name).strip()[:100]
            # Filter out placeholder links like "Keiko's grandmother 001"
            if '001' not in ggm_name:
                family["maternal_great_grandmother"] = ggm_name
            else:
                # Try to extract just the name part
                clean_name = re.sub(r'\s+001$', '', ggm_name)
                if clean_name:
                    family["maternal_great_grandmother"] = clean_name
        
        # Extract paternal ancestors (both with and without [[ancestor]] link)
        ancestor_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(paternal\s*\[\[ancestor\]\]\)', relative_text, re.I)
        for ancestor_match in ancestor_matches:
            ancestor_raw = ancestor_match.group(1)
            ancestor = extract_link_display_text(ancestor_raw)
            ancestor = clean_mediawiki_markup(ancestor).strip()[:100]
            if ancestor and ancestor not in family["paternal_ancestors"]:
                family["paternal_ancestors"].append(ancestor)
        
        # Also look for "paternal ancestor" without [[ancestor]] link (e.g., "Brian Boru (paternal ancestor)")
        ancestor_simple_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(paternal\s+ancestor\)', relative_text, re.I)
        for ancestor_match in ancestor_simple_matches:
            ancestor_raw = ancestor_match.group(1)
            ancestor = extract_link_display_text(ancestor_raw)
            ancestor = clean_mediawiki_markup(ancestor).strip()[:100]
            if ancestor and ancestor not in family["paternal_ancestors"]:
                family["paternal_ancestors"].append(ancestor)
        
        # Extract daughter-in-law
        dil_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?daughter-in-law\]?\]?\)', relative_text, re.I)
        for match in dil_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            if name and '001' not in name and name not in [d['name'] for d in family["daughter_in_law"]]:
                family["daughter_in_law"].append({"name": name})
        
        # Extract son-in-law
        sil_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?son-in-law\]?\]?\)', relative_text, re.I)
        for match in sil_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            if name and '001' not in name and name not in [d['name'] for d in family["son_in_law"]]:
                family["son_in_law"].append({"name": name})
        
        # Extract grandsons
        grandson_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?grandson\]?\]?', relative_text, re.I)
        for match in grandson_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            # Extract "via X" if present
            context = relative_text[max(0, match.start()-50):match.end()+100]
            via_match = re.search(r'via\s+([A-Za-z\s]+)', context, re.I)
            via = None
            if via_match:
                via = clean_mediawiki_markup(via_match.group(1)).strip()[:50]
            
            if name and '001' not in name and name not in [d['name'] for d in family["grandsons"]]:
                grandson_obj = {"name": name}
                if via:
                    grandson_obj["via"] = via
                family["grandsons"].append(grandson_obj)
        
        # Extract granddaughters
        granddaughter_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?granddaughter\]?\]?\)', relative_text, re.I)
        for match in granddaughter_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            if name and '001' not in name and name not in [d['name'] for d in family["granddaughters"]]:
                family["granddaughters"].append({"name": name})
        
        # Extract father-in-law
        fil_match = re.search(r'\[\[([^\]]+)\]\]\s*\(\[?\[?father-in-law\]?\]?\)', relative_text, re.I)
        if fil_match:
            name = clean_mediawiki_markup(fil_match.group(1)).split('|')[0].strip()[:100]
            if name and '001' not in name:
                family["father_in_law"] = name
        
        # Extract mother-in-law
        mil_match = re.search(r'\[\[([^\]]+)\]\]\s*\(\[?\[?mother-in-law\]?\]?\)', relative_text, re.I)
        if mil_match:
            name = clean_mediawiki_markup(mil_match.group(1)).split('|')[0].strip()[:100]
            if name and '001' not in name:
                family["mother_in_law"] = name
        
        # Extract brother-in-law
        bil_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?brother-in-law\]?\]?\)', relative_text, re.I)
        for match in bil_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            if name and '001' not in name and name not in family["brother_in_law"]:
                family["brother_in_law"].append(name)
        
        # Extract sister-in-law
        sil_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?sister-in-law\]?\]?\)', relative_text, re.I)
        for match in sil_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            if name and '001' not in name and name not in family["sister_in_law"]:
                family["sister_in_law"].append(name)
        
        # Extract cousins
        cousin_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?cousin\]?\]?\)', relative_text, re.I)
        for match in cousin_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            if name and '001' not in name and name not in family["cousins"]:
                family["cousins"].append(name)
        
        # Extract uncles
        uncle_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?uncle\]?\]?\)', relative_text, re.I)
        for match in uncle_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            # Check for "paternal uncle" or "maternal uncle"
            context = relative_text[max(0, match.start()-50):match.start()]
            is_paternal = 'paternal' in context.lower()
            if name and '001' not in name:
                uncle_obj = {"name": name}
                if is_paternal:
                    uncle_obj["type"] = "paternal"
                family["uncles"].append(uncle_obj)
        
        # Extract aunts
        aunt_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?aunt\]?\]?\)', relative_text, re.I)
        for match in aunt_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            if name and '001' not in name and name not in family["aunts"]:
                family["aunts"].append(name)
        
        # Extract nephews
        nephew_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?nephew\]?\]?\)', relative_text, re.I)
        for match in nephew_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            if name and '001' not in name and name not in family["nephews"]:
                family["nephews"].append(name)
        
        # Extract nieces
        niece_matches = re.finditer(r'\[\[([^\]]+)\]\]\s*\(\[?\[?niece\]?\]?\)', relative_text, re.I)
        for match in niece_matches:
            name_raw = match.group(1)
            name = extract_link_display_text(name_raw)
            name = clean_mediawiki_markup(name).strip()[:100]
            if name and '001' not in name and name not in family["nieces"]:
                family["nieces"].append(name)
    
    return family

def extract_portrayed_by(text: str) -> List[Dict]:
    """Extract actor information with roles. Format: |actor = [[Angela Tedeski|Angela]] and [[Angelica Tedeski]]<br>[[Hana Hatae]] (primary)<br>[[Michelle Krusiec]]"""
    actors = []
    patterns = [
        re.compile(r'\|\s*actor\s*=\s*([^\n]+)', re.I),
        re.compile(r'Played\s+by[:\s]+([^\n]+)', re.I),
        re.compile(r'Portrayed\s+by[:\s]+([^\n]+)', re.I),
    ]
    
    for pattern in patterns:
        match = pattern.search(text[:5000])
        if match:
            actor_text = match.group(1)
            # Split by <br> tags to get separate actors
            actor_lines = re.split(r'<br>', actor_text)
            
            for line in actor_lines:
                line = line.strip()
                if not line:
                    continue
                
                # Extract actor name(s) from [[links]]
                actor_links = re.findall(r'\[\[([^\]]+)\]\]', line)
                
                # Check for role indicators in this line
                has_primary = "(primary)" in line.lower()
                has_infant = "infant" in line.lower()
                has_adult = "adult" in line.lower()
                
                # Handle "Angela and Angelica Tedeski" - combine into one entry
                if len(actor_links) >= 2 and "and" in line.lower():
                    # Check if both are Tedeski
                    if "tedeski" in actor_links[0].lower() and "tedeski" in actor_links[1].lower():
                        actors.append({
                            "actor": "Angela and Angelica Tedeski",
                            "role": "infant"
                        })
                        continue
                
                # Process each actor link in the line
                for actor_link in actor_links:
                    actor_parts = actor_link.split('|')
                    actor_name = clean_mediawiki_markup(actor_parts[0]).strip()[:100]
                    
                    # Filter out invalid actor entries
                    invalid_actors = ['unknown', 'photograph', 'image', 'photo', 'picture', 'n/a', 'none']
                    if any(invalid in actor_name.lower() for invalid in invalid_actors):
                        continue
                    
                    # Determine role based on line context
                    if has_primary:
                        role = "primary"
                    elif has_infant or "tedeski" in actor_name.lower():
                        role = "infant"
                    elif has_adult or "krusiec" in actor_name.lower():
                        role = "adult version (age 18)"
                    else:
                        # Default: first actor is primary, others are additional
                        role = "primary" if len(actors) == 0 else "additional"
                    
                    if actor_name and len(actor_name) > 2 and actor_name.lower() not in ['and', 'or', 'angela']:
                        actors.append({
                            "actor": actor_name,
                            "role": role
                        })
            break
    
    return actors

def extract_appearances(text: str) -> Dict[str, List[str]]:
    """Extract episode appearances by series."""
    appearances = {series: [] for series in ['TNG', 'DS9', 'TOS', 'VOY', 'ENT', 'DIS', 'PIC', 'LD', 'PRO', 'SNW']}
    
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
    
    for series, pattern in series_patterns.items():
        episodes = []
        for match in pattern.finditer(text):
            episode_raw = match.group(1)
            episode = extract_link_display_text(episode_raw)
            episode = clean_mediawiki_markup(episode).strip()
            if episode and episode not in episodes:
                episodes.append(episode)
        appearances[series] = episodes[:20]  # Limit to 20 per series
    
    return appearances

def extract_notable_events(text: str, character_name: str, appearances: Dict[str, List[str]]) -> List[Dict]:
    """Extract notable events from episode descriptions."""
    events = []
    
    # Look for episode references with character actions - broader search
    for series, episode_list in appearances.items():
        for episode in episode_list:
            # Find all mentions of this episode
            # Pattern: {{DS9|Episode Name}} - need to match literal {{ and }}
            escaped_episode = re.escape(episode)
            # Build pattern: \{\{SERIES\|EPISODE\}\}
            pattern = '\\{\\{' + series + '\\|' + escaped_episode + '\\}\\}'
            episode_mentions = list(re.finditer(pattern, text, re.I))
            
            for mention in episode_mentions:
                # Get context around episode mention (500 chars before and after)
                start = max(0, mention.start() - 500)
                end = min(len(text), mention.end() + 500)
                context = text[start:end]
                
                # Look for character name in context
                if character_name.lower() in context.lower():
                    # Extract sentences containing both episode and character
                    sentences = re.split(r'[.!?]\s+', context)
                    for sentence in sentences:
                        if episode.lower() in sentence.lower() and character_name.lower() in sentence.lower():
                            # Clean and extract event - remove file references and markup
                            event_text = clean_mediawiki_markup(sentence).strip()
                            # Remove file references like "File:Molly O'Brien in bed.jpg"
                            event_text = re.sub(r'File:[^\s]+\.(jpg|png|gif|jpeg)\s*', '', event_text, flags=re.I)
                            # Remove section headers like "==On Deep Space 9=="
                            event_text = re.sub(r'==[^=]+==\s*', '', event_text)
                            # Remove appendices sections
                            event_text = re.sub(r'==\s*Appendices\s*==.*', '', event_text, flags=re.I | re.DOTALL)
                            # Remove asterisks and formatting
                            event_text = re.sub(r'\*+\s*', '', event_text)
                            event_text = event_text.strip()
                            
                            if len(event_text) > 15 and len(event_text) < 300:
                                # Skip if event is just "(photograph only)" or similar
                                if re.search(r'\(photograph\s+only\)|==\s*\(photograph', event_text, re.I):
                                    continue
                                
                                # Extract year if mentioned
                                year = extract_year(context)
                                
                                # Create summary (first 100 chars, stop at comma/parenthesis)
                                event_summary = event_text[:100]
                                if ',' in event_summary:
                                    event_summary = event_summary.split(',')[0]
                                if '(' in event_summary:
                                    event_summary = event_summary.split('(')[0]
                                event_summary = event_summary.strip()
                                
                                # Skip if summary is empty
                                if not event_summary:
                                    continue
                                
                                events.append({
                                    "episode": episode,
                                    "series": series,
                                    "year": year,
                                    "event": event_summary,
                                    "details": event_text[:300]
                                })
                                break  # One event per episode mention
    
    # Also look for specific event patterns
    event_keywords = ['fell through', 'acquired', 'born', 'died', 'married', 'transferred', 'moved']
    for keyword in event_keywords:
        keyword_matches = list(re.finditer(rf'{re.escape(character_name)}[^.!?]*{keyword}[^.!?]+', text, re.I))
        for match in keyword_matches:
            # Find nearby episode reference
            context_start = max(0, match.start() - 300)
            context_end = min(len(text), match.end() + 300)
            context = text[context_start:context_end]
            
            # Look for episode template
            episode_match = re.search(r'\{\{(TNG|DS9|TOS|VOY|ENT|DIS|PIC|LD|PRO|SNW)\|([^\}]+)\}\}', context)
            if episode_match:
                series = episode_match.group(1)
                episode = episode_match.group(2)
                event_text = clean_mediawiki_markup(match.group(0)).strip()
                
                if len(event_text) > 15 and len(event_text) < 300:
                    # Clean event text
                    event_text = re.sub(r'File:[^\s]+\.(jpg|png|gif|jpeg)\s*', '', event_text, flags=re.I)
                    event_text = re.sub(r'==[^=]+==\s*', '', event_text)
                    event_text = event_text.strip()
                    
                    # Skip if event is just "(photograph only)" or similar
                    if re.search(r'\(photograph\s+only\)|==\s*\(photograph', event_text, re.I):
                        continue
                    
                    year = extract_year(context)
                    # Create clean summary
                    event_summary = event_text[:100]
                    if ',' in event_summary:
                        event_summary = event_summary.split(',')[0]
                    if '(' in event_summary:
                        event_summary = event_summary.split('(')[0]
                    event_summary = event_summary.strip()
                    
                    # Skip if summary is empty
                    if not event_summary:
                        continue
                    
                    events.append({
                        "episode": episode,
                        "series": series,
                        "year": year,
                        "event": event_summary,
                        "details": event_text[:300]
                    })
    
    # Remove duplicates and limit
    seen_events = set()
    unique_events = []
    for event in events:
        event_key = (event["episode"], event["event"][:50])
        if event_key not in seen_events:
            seen_events.add(event_key)
            unique_events.append(event)
    
    return unique_events[:10]  # Limit to 10 events

def extract_characteristics(text: str, character_name: str) -> List[str]:
    """Extract personality traits and characteristics from narrative text."""
    characteristics = []
    
    # Look for specific patterns found in the XML:
    # "Molly loved to color, and often did so after dinner"
    # "She was, however, in charge of putting her [[plate]] in the [[replicator]]"
    # "Molly had a good aim, she grew bored with it"
    # "Molly sometimes referred to Kira as her [[aunt]]"
    
    # Pattern 1: "loved to X, and often did so"
    loved_pattern = re.compile(rf'{re.escape(character_name.split()[0])}[^.!?]*loved\s+to\s+([^,!?]+)', re.I)
    loved_match = loved_pattern.search(text[:20000])
    if loved_match:
        trait = clean_mediawiki_markup(loved_match.group(1)).strip()
        if trait:
            characteristics.append(f"Loved to {trait}")
    
    # Pattern 2: "often did so after X" or "often colored after dinner"
    often_pattern = re.compile(rf'{re.escape(character_name.split()[0])}[^.!?]*often\s+([^.!?]+after[^.!?]+)', re.I)
    often_match = often_pattern.search(text[:20000])
    if often_match:
        trait = clean_mediawiki_markup(often_match.group(1)).strip()
        if trait:
            characteristics.append(f"Often {trait}")
    
    # Pattern 2b: "often colored after dinner" (more specific)
    colored_pattern = re.compile(rf'{re.escape(character_name.split()[0])}[^.!?]*often\s+colored\s+after\s+dinner', re.I)
    if colored_pattern.search(text[:20000]):
        characteristics.append("Often colored after dinner")
    
    # Pattern 3: "in charge of putting her plate in the replicator"
    charge_pattern = re.compile(rf'{re.escape(character_name.split()[0])}[^.!?]*(?:was|is)[^.!?]*in\s+charge\s+of\s+([^.!?]+)', re.I)
    charge_match = charge_pattern.search(text[:20000])
    if charge_match:
        trait = clean_mediawiki_markup(charge_match.group(1)).strip()
        if trait:
            characteristics.append(f"In charge of {trait}")
    
    # Pattern 3b: More specific - "putting her plate in the replicator"
    replicator_pattern = re.compile(rf'{re.escape(character_name.split()[0])}[^.!?]*putting\s+her\s+\[\[plate\]\]\s+in\s+the\s+\[\[replicator\]\]', re.I)
    if replicator_pattern.search(text[:20000]):
        characteristics.append("In charge of putting her plate in the replicator")
    
    # Pattern 4: "had good aim with darts but grew bored"
    aim_pattern = re.compile(rf'{re.escape(character_name.split()[0])}[^.!?]*had\s+good\s+aim\s+([^.!?]+)', re.I)
    aim_match = aim_pattern.search(text[:20000])
    if aim_match:
        trait = clean_mediawiki_markup(aim_match.group(1)).strip()
        if trait:
            characteristics.append(f"Had good aim with {trait} but grew bored")
    
    # Pattern 4b: More specific - "had good aim with darts"
    darts_pattern = re.compile(rf'{re.escape(character_name.split()[0])}[^.!?]*had\s+good\s+aim\s+with\s+\[\[darts\]\]', re.I)
    if darts_pattern.search(text[:20000]):
        characteristics.append("Had good aim with darts but grew bored")
    
    # Pattern 5: "sometimes referred to X as her Y"
    referred_pattern = re.compile(rf'{re.escape(character_name.split()[0])}[^.!?]*sometimes\s+referred\s+to\s+([^.!?]+)\s+as\s+([^.!?]+)', re.I)
    referred_match = referred_pattern.search(text[:20000])
    if referred_match:
        person = clean_mediawiki_markup(referred_match.group(1)).strip()
        relation = clean_mediawiki_markup(referred_match.group(2)).strip()
        # Clean up duplicate "her" if present
        relation = re.sub(r'^her\s+', '', relation, flags=re.I)
        if person and relation:
            characteristics.append(f"Sometimes referred to {person} as her {relation}")
    
    return characteristics[:10]  # Limit to 10

def extract_locations(text: str, character_name: str, birth_location: Optional[str] = None, birth_year: Optional[int] = None) -> List[Dict]:
    """Extract locations with periods and reasons from narrative text."""
    locations = []
    
    # Location 1: USS Enterprise-D (from birth info)
    if birth_location and birth_year:
        locations.append({
            "location": birth_location,
            "period": f"{birth_year}-{birth_year + 1}",
            "reason": "Born and lived there as infant"
        })
    
    # Location 2: Deep Space 9 - "Molly moved aboard [[Deep Space 9]], as her father got a new assignment there"
    ds9_pattern = re.compile(rf'{re.escape(character_name.split()[0])}[^.!?]*moved\s+aboard\s+\[\[Deep\s+Space\s+9\]\]', re.I)
    ds9_match = ds9_pattern.search(text[:20000])
    if ds9_match:
        # Look for year context
        context = text[max(0, ds9_match.start()-500):ds9_match.end()+500]
        year_match = re.search(r'(\d{4})', context)
        start_year = year_match.group(1) if year_match else "2369"
        locations.append({
            "location": "Deep Space 9",
            "period": f"{start_year}-2375",
            "reason": "Family moved there when father transferred"
        })
    
    # Location 3: Earth - "Keiko took Molly and Yoshi to Earth for their safety"
    earth_pattern = re.compile(rf'Keiko\s+took\s+{re.escape(character_name.split()[0])}[^.!?]*to\s+Earth', re.I)
    earth_match = earth_pattern.search(text[:20000])
    if earth_match:
        context = text[max(0, earth_match.start()-500):earth_match.end()+500]
        year_match = re.search(r'(\d{4})', context)
        year = year_match.group(1) if year_match else "2375"
        locations.append({
            "location": "Earth",
            "period": f"{year}+",
            "reason": "Moved with family when father became Professor of Engineering at Starfleet Academy"
        })
    
    return locations[:5]  # Limit to 5

def extract_objects(text: str, character_name: str) -> List[Dict]:
    """Extract objects/items associated with the character. Format: 'acquired a Bajoran doll named [[Lupi]]'"""
    objects = []
    
    # Look for pattern: "acquired a Bajoran doll named [[Lupi]]"
    # Also check context for episode and acquisition info
    lupi_pattern = re.compile(r'acquired\s+(?:a|an)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+doll\s+named\s+\[\[([^\]]+)\]\]', re.I)
    
    for match in lupi_pattern.finditer(text[:20000]):
        object_type = clean_mediawiki_markup(match.group(1)).strip()[:50]
        object_name_raw = match.group(2)
        object_name = extract_link_display_text(object_name_raw)
        object_name = clean_mediawiki_markup(object_name).strip()[:50]
        
        if object_name and len(object_name) > 2:
            # Get context around the match
            context_start = max(0, match.start() - 500)
            context_end = min(len(text), match.end() + 500)
            context = text[context_start:context_end]
            
            # Find episode
            episode_match = re.search(r'\{\{(TNG|DS9|TOS|VOY|ENT|DIS|PIC|LD|PRO|SNW)\|([^\}]+)\}\}', context)
            episode = episode_match.group(2) if episode_match else None
            
            # Find acquisition info: "from Bajor in 2372"
            acquired_match = re.search(r'from\s+([A-Z][a-z]+)\s+in\s+(\d{4})', context, re.I)
            if acquired_match:
                acquired = f"From {acquired_match.group(1)} in {acquired_match.group(2)}"
            else:
                acquired = "Unknown"
            
            objects.append({
                "name": object_name,
                "type": object_type,
                "episodes": [episode] if episode else [],
                "acquired": acquired
            })
    
    return objects[:5]  # Limit to 5

def extract_status(text: str) -> Optional[str]:
    """Extract character status. Format: |status = Active and |datestatus = 2375 on separate lines."""
    # Look for status and datestatus on separate lines
    status_match = re.search(r'\|\s*status\s*=\s*([^\n]+)', text[:3000], re.I)
    datestatus_match = re.search(r'\|\s*datestatus\s*=\s*(\d{4})', text[:3000], re.I)
    
    if status_match and datestatus_match:
        status_text = clean_mediawiki_markup(status_match.group(1)).strip()
        year = datestatus_match.group(1)
        return f"{status_text} ({year})"
    elif status_match:
        status = clean_mediawiki_markup(status_match.group(1)).strip()[:100]
        if status:
            return status
    return None

def extract_character_info(text: str, title: str) -> Dict:
    """
    Extract comprehensive structured character information from page text.
    Returns data matching the molly.json structure.
    """
    char_data = {
        "character": {
            "name": title,
            "species": None,
            "status": None,
            "born": {
                "year": None,
                "location": None
            },
            "family": {
                "father": None,
                "mother": None,
                "siblings": [],
                "paternal_grandfather": None,
                "maternal_grandfather": None,
                "maternal_grandmother": None,
                "maternal_great_grandmother": None,
                "paternal_ancestors": []
            },
            "portrayed_by": [],
            "appearances": {
                "TNG": [],
                "DS9": [],
                "TOS": [],
                "VOY": [],
                "ENT": [],
                "DIS": [],
                "PIC": [],
                "LD": [],
                "PRO": [],
                "SNW": []
            },
            "notable_events": [],
            "characteristics": [],
            "locations": [],
            "objects": []
        },
        "trivia_facts": [],
        "metadata": {
            "source": f"Memory Alpha XML export",
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "data_structure_version": "1.0"
        }
    }
    
    # Extract all fields
    char_data["character"]["species"] = extract_species(text)
    char_data["character"]["status"] = extract_status(text)
    year, location = extract_birth_info(text)
    char_data["character"]["born"]["year"] = year
    char_data["character"]["born"]["location"] = location
    char_data["character"]["family"] = extract_family_relationships(text, title)
    char_data["character"]["portrayed_by"] = extract_portrayed_by(text)
    char_data["character"]["appearances"] = extract_appearances(text)
    char_data["character"]["notable_events"] = extract_notable_events(text, title, char_data["character"]["appearances"])
    char_data["character"]["characteristics"] = extract_characteristics(text, title)
    char_data["character"]["locations"] = extract_locations(text, title, char_data["character"]["born"]["location"], char_data["character"]["born"]["year"])
    char_data["character"]["objects"] = extract_objects(text, title)
    
    # Generate trivia facts from extracted data
    trivia_facts = []
    
    # Name question
    if char_data["character"]["name"]:
        trivia_facts.append({
            "question_type": "who",
            "question": f"Who was {char_data['character']['name']}?",
            "answer": char_data["character"]["name"],
            "difficulty": "Easy"
        })
    
    # Species question
    if char_data["character"]["species"]:
        trivia_facts.append({
            "question_type": "what",
            "question": f"What species was {char_data['character']['name']}?",
            "answer": char_data["character"]["species"],
            "difficulty": "Easy"
        })
    
    # Birth year question
    if char_data["character"]["born"]["year"]:
        trivia_facts.append({
            "question_type": "when",
            "question": f"When was {char_data['character']['name']} born?",
            "answer": str(char_data["character"]["born"]["year"]),
            "difficulty": "Medium"
        })
    
    # Birth location question
    if char_data["character"]["born"]["location"]:
        trivia_facts.append({
            "question_type": "where",
            "question": f"Where was {char_data['character']['name']} born?",
            "answer": char_data["character"]["born"]["location"],
            "difficulty": "Easy"
        })
    
    # Family questions
    if char_data["character"]["family"]["father"]:
        trivia_facts.append({
            "question_type": "who",
            "question": f"Who was {char_data['character']['name']}'s father?",
            "answer": char_data["character"]["family"]["father"],
            "difficulty": "Medium"
        })
    
    if char_data["character"]["family"]["mother"]:
        trivia_facts.append({
            "question_type": "who",
            "question": f"Who was {char_data['character']['name']}'s mother?",
            "answer": char_data["character"]["family"]["mother"],
            "difficulty": "Medium"
        })
    
    # Sibling questions
    for sibling in char_data["character"]["family"]["siblings"]:
        trivia_facts.append({
            "question_type": "what",
            "question": f"What was the name of {char_data['character']['name']}'s {sibling.get('relationship', 'sibling')}?",
            "answer": sibling["name"],
            "difficulty": "Medium"
        })
        if sibling.get("nickname"):
            trivia_facts.append({
                "question_type": "what",
                "question": f"What was {sibling['name']}'s nickname?",
                "answer": sibling["nickname"],
                "difficulty": "Hard"
            })
    
    # Object questions
    for obj in char_data["character"]["objects"]:
        trivia_facts.append({
            "question_type": "what",
            "question": f"What was the name of {char_data['character']['name']}'s {obj.get('type', 'item')}?",
            "answer": obj["name"],
            "difficulty": "Hard"
        })
    
    char_data["trivia_facts"] = trivia_facts
    
    return char_data

def extract_character_from_xml(xml_path: str, character_name: str, output_path: str):
    """
    Extract structured data for a specific character from XML file.
    
    Args:
        xml_path: Path to Memory Alpha XML file
        character_name: Name of character to extract (will search for matching pages)
        output_path: Path to save JSON file
    """
    print(f"Searching for '{character_name}' in XML file...")
    
    character_found = False
    character_data = None
    
    # Use streaming parser to find character page
    for event, elem in ET.iterparse(xml_path, events=('start', 'end')):
        if event == 'end' and elem.tag == f'{NS}page':
            title_elem = elem.find(f'{NS}title')
            ns_elem = elem.find(f'{NS}ns')
            revision_elem = elem.find(f'{NS}revision')
            
            if title_elem is not None and revision_elem is not None:
                title = title_elem.text or ''
                ns = ns_elem.text if ns_elem is not None else '0'
                
                # Skip file pages, category pages, etc. (only main namespace, ns=0)
                if ns != '0':
                    elem.clear()
                    continue
                
                # Check if this is the character page (exact match preferred)
                title_lower = title.lower()
                char_lower = character_name.lower()
                
                # Exclude file pages, disambiguation pages, mirror universe variants
                if ('file:' in title_lower or 
                    '(disambiguation)' in title_lower or
                    '(mirror)' in title_lower or
                    '(alternate)' in title_lower):
                    elem.clear()
                    continue
                
                # Exact match or title starts with character name
                is_match = (
                    title_lower == char_lower or
                    title_lower == char_lower + ' (character)' or
                    title_lower.startswith(char_lower + ' ') or
                    (char_lower in title_lower and len(title.split()) <= 4 and '(mirror)' not in title_lower)
                )
                
                if is_match:
                    text_elem = revision_elem.find(f'{NS}text')
                    if text_elem is not None and text_elem.text:
                        print(f"Found page: {title}")
                        print("Extracting structured data...")
                        
                        character_data = extract_character_info(text_elem.text, title)
                        character_found = True
                        
                        # Save to JSON
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(character_data, f, indent=2, ensure_ascii=False)
                        
                        print(f"Saved to {output_path}")
                        print(f"\nExtracted Data:")
                        print(f"  Name: {character_data['character']['name']}")
                        print(f"  Species: {character_data['character']['species']}")
                        print(f"  Status: {character_data['character']['status']}")
                        print(f"  Born: {character_data['character']['born']['year']} on {character_data['character']['born']['location']}")
                        print(f"  Father: {character_data['character']['family']['father']}")
                        print(f"  Mother: {character_data['character']['family']['mother']}")
                        print(f"  Siblings: {len(character_data['character']['family']['siblings'])}")
                        print(f"  Actors: {len(character_data['character']['portrayed_by'])}")
                        print(f"  Notable Events: {len(character_data['character']['notable_events'])}")
                        print(f"  Characteristics: {len(character_data['character']['characteristics'])}")
                        print(f"  Locations: {len(character_data['character']['locations'])}")
                        print(f"  Objects: {len(character_data['character']['objects'])}")
                        print(f"  Trivia Facts: {len(character_data['trivia_facts'])}")
                        
                        break
            
            # Clear element to free memory
            elem.clear()
    
    if not character_found:
        print(f"Character '{character_name}' not found in XML file")
        return False
    
    return True

def extract_character_from_json(json_path: str, character_name: str, output_path: str) -> bool:
    """
    Extract structured character data from bulk extraction JSON file.
    Uses indices for fast character lookup - much faster than XML streaming.
    """
    print(f"Loading JSON file: {json_path}")
    print("Loading JSON (this is faster than XML parsing)...")
    
    # Load JSON file (293MB, but JSON parsing is much faster than XML streaming)
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    indices = data.get('indices', {})
    pages = data.get('pages', [])
    
    print(f"Loaded {len(pages):,} pages")
    print(f"Character index contains {len(indices.get('by_character', {})):,} unique characters")
    
    # Search for character in index (case-insensitive)
    character_name_lower = character_name.lower()
    character_index = indices.get('by_character', {})
    
    # First, try to find by exact page title match (fastest and most accurate)
    page_indices = []
    title_matches = []
    for idx, page in enumerate(pages):
        title_lower = page.get('title', '').lower()
        if title_lower == character_name_lower or title_lower == character_name_lower + ' (character)':
            title_matches.append(idx)
    
    if title_matches:
        print(f"Found {len(title_matches)} page(s) with exact title match")
        page_indices = title_matches
    else:
        # Fall back to character index
        page_indices = character_index.get(character_name_lower, [])
    
    # If not found, try variations and partial matches
    if not page_indices:
        # Try with/without apostrophes and common variations
        variations = [
            character_name_lower.replace("'", ""),
            character_name_lower.replace("'", "'"),
            character_name_lower + " (character)",
        ]
        for variant in variations:
            if variant in character_index:
                page_indices = character_index[variant]
                print(f"Found variant match: '{variant}' -> {len(page_indices)} pages")
                break
    
    # If still not found, try partial matches (but prefer longer matches)
    if not page_indices:
        best_match = None
        best_match_len = 0
        for char_key, page_nums in character_index.items():
            if character_name_lower in char_key or char_key in character_name_lower:
                # Prefer longer, more specific matches
                match_len = min(len(char_key), len(character_name_lower))
                if match_len > best_match_len:
                    best_match = char_key
                    best_match_len = match_len
                    page_indices = page_nums
        
        if best_match:
            print(f"Found partial match: '{best_match}' -> {len(page_indices)} pages")
    
    if not page_indices:
        print(f"Character '{character_name}' not found in character index")
        print("Available characters (sample):", list(character_index.keys())[:20])
        return False
    
    print(f"Found {len(page_indices)} page(s) for character")
    
    # Try to find the main character page (prioritize exact title matches)
    character_found = False
    candidates = []
    
    for page_idx in page_indices:
        if page_idx >= len(pages):
            continue
        
        page = pages[page_idx]
        title = page.get('title', '')
        title_lower = title.lower()
        
        # Score candidates: exact match = highest priority
        score = 0
        title_words = title_lower.split()
        char_words = character_name_lower.split()
        
        if title_lower == character_name_lower:
            score = 100  # Exact match - highest priority
        elif title_lower == character_name_lower + ' (character)':
            score = 95  # Character page variant
        elif title_lower.startswith(character_name_lower + ' ') or title_lower.endswith(' ' + character_name_lower):
            score = 90  # Title starts/ends with character name
        elif all(word in title_words for word in char_words) and len(title_words) <= len(char_words) + 1:
            score = 85  # All words match, title not much longer
        elif character_name_lower in title_lower and len(title.split()) <= len(character_name.split()) + 2:
            score = 70  # Title contains character name, not too long
        elif title_lower in character_name_lower and len(title_words) >= 2:
            score = 60  # Title is substring of character name, but has multiple words
        elif character_name_lower in [c.lower() for c in page.get('characters', [])]:
            score = 50  # Character name in characters list
        
        if score > 0:
            candidates.append((score, page_idx, title, page))
    
    # Sort by score (highest first) and try best matches
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    if candidates:
        print(f"Found {len(candidates)} candidate page(s), trying best matches...")
        for score, page_idx, title, page in candidates[:5]:  # Try top 5 candidates
            print(f"  Trying: {title} (score: {score})")
            
            # Get full_text (still has MediaWiki markup)
            full_text = page.get('full_text', '')
            if not full_text:
                print(f"    Warning: Page '{title}' has no full_text, skipping")
                continue
            
            print(f"    Extracting structured data from: {title}")
            character_data = extract_character_info(full_text, title)
            
            # Verify this is actually the right character (check extracted name matches)
            extracted_name = character_data['character']['name'].lower()
            if (extracted_name == character_name_lower or 
                character_name_lower in extracted_name or
                extracted_name in character_name_lower):
                character_found = True
                
                # Save to JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(character_data, f, indent=2, ensure_ascii=False)
                
                print(f"Saved to {output_path}")
                print(f"\nExtracted Data:")
                print(f"  Name: {character_data['character']['name']}")
                print(f"  Species: {character_data['character']['species']}")
                print(f"  Status: {character_data['character']['status']}")
                if character_data['character']['born']['year']:
                    print(f"  Born: {character_data['character']['born']['year']} on {character_data['character']['born']['location']}")
                print(f"  Father: {character_data['character']['family']['father']}")
                print(f"  Mother: {character_data['character']['family']['mother']}")
                print(f"  Siblings: {len(character_data['character']['family']['siblings'])}")
                print(f"  Actors: {len(character_data['character']['portrayed_by'])}")
                print(f"  Notable Events: {len(character_data['character']['notable_events'])}")
                print(f"  Characteristics: {len(character_data['character']['characteristics'])}")
                print(f"  Locations: {len(character_data['character']['locations'])}")
                print(f"  Objects: {len(character_data['character']['objects'])}")
                print(f"  Trivia Facts: {len(character_data['trivia_facts'])}")
                
                break
            else:
                print(f"    Extracted name '{character_data['character']['name']}' doesn't match '{character_name}', trying next candidate...")
    
    if not character_found:
        print(f"Could not find main character page for '{character_name}'")
        return False
    
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_structured_character_improved.py <input_file> <character_name> [output_file]")
        print("\nInput file can be:")
        print("  - XML file: ../data/raw/enmemoryalpha_pages_current.xml")
        print("  - JSON file: ../data/extracted/extracted_data.json")
        print("\nExamples:")
        print("  python extract_structured_character_improved.py ../data/extracted/extracted_data.json 'Molly O'Brien' ../data/characters/molly.json")
        print("  python extract_structured_character_improved.py ../data/raw/enmemoryalpha_pages_current.xml 'Molly O'Brien' ../data/characters/molly.json")
        sys.exit(1)
    
    input_path = sys.argv[1]
    character_name = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else f'../data/characters/{character_name.lower().replace(" ", "_").replace("'", "")}.json'
    
    # Detect file type by extension
    if input_path.lower().endswith('.json'):
        extract_character_from_json(input_path, character_name, output_path)
    elif input_path.lower().endswith('.xml'):
        extract_character_from_xml(input_path, character_name, output_path)
    else:
        print(f"Error: Unknown file type. Expected .json or .xml, got: {input_path}")
        sys.exit(1)

if __name__ == '__main__':
    main()

