#!/usr/bin/env python3
"""
Direct MediaWiki-to-JSON converter for character pages.
Converts character pages from Memory Alpha directly to JSON structure
matching rom_example.json format with content_type fields.

This approach:
- Extracts sidebar/infobox fields directly
- Preserves timeline sections as arrays of event objects
- Adds explicit content_type fields for script processing
- Handles family relationships in structured format
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

def extract_sidebar_section(text: str) -> str:
    """Extract the sidebar template section from page text."""
    sidebar_start = text.find('{{sidebar individual')
    if sidebar_start == -1:
        sidebar_start = text.find('{{sidebar character')
    if sidebar_start == -1:
        sidebar_start = text.find('{{infobox person')
    
    if sidebar_start == -1:
        return ""
    
    # Find the closing }} - handle nested braces
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
    
    return text[sidebar_start:sidebar_start+5000]

def extract_link_display_text(link_content: str) -> str:
    """Extract display text from MediaWiki link: [[target|display]] -> display, [[target]] -> target"""
    if '|' in link_content:
        return link_content.split('|', 1)[1].strip()
    return link_content.strip()

def clean_mediawiki_markup(text: str, preserve_episode_refs: bool = False) -> str:
    """Remove MediaWiki markup, preserving content.
    
    Args:
        preserve_episode_refs: If True, convert {{SERIES|Episode}} to (SERIES: "Episode") format
                                instead of removing them. Default False.
    """
    if not text:
        return ""
    
    # Ensure we're working with a string (handle encoding issues)
    if not isinstance(text, str):
        text = str(text)
    
    # Remove section headers: ===Section Name=== or ==Section Name==
    # Also handle section markers like "Legacy(?)" that appear in text
    # Convert to plain text: ===USS Enterprise-D=== becomes "USS Enterprise-D\n\n"
    # Check if text starts with a section header
    header_match = re.match(r'^={2,}\s*([^=]+)\s*={2,}', text)
    if header_match:
        # Text starts with header - replace with header text + line break
        header_text = header_match.group(1).strip()
        text = text[header_match.end():].lstrip()
        text = header_text + '\n\n' + text
    else:
        # Replace headers in middle of text with just the header text
        text = re.sub(r'={2,}\s*([^=]+)\s*={2,}', r'\1', text)
    
    # Remove section markers that appear at the start of text (like "Legacy(?)")
    # These are often leftover from section parsing
    # BUT be careful - only remove if it's clearly a section marker, not a normal word
    # Only remove if followed by specific patterns that indicate it's a section marker
    # Don't remove single capitalized words that might be character names or normal text
    # This regex was too aggressive and removed words like "Pel", "Rules", "Bar" from episode names
    # We'll skip this removal for now - section markers should be handled at paragraph level
    # text = re.sub(r'^([A-Z][a-z]+(?:\([^)]+\))?)\s+', '', text)
    
    # Remove MediaWiki text formatting: '''bold''', ''italic'', etc.
    # Handle multiple consecutive quotes (e.g., '''' or '''')
    text = re.sub(r"''+", '', text)  # Remove all sequences of single quotes
    
    # Convert episode templates to (SERIES: "Episode") format if requested
    # This preserves episode references in the text while extracting them separately
    if preserve_episode_refs:
        def convert_episode_template(match):
            series = match.group(1)
            episode = match.group(2).strip()
            # Clean episode name (remove any pipes)
            if '|' in episode:
                episode = episode.split('|')[-1]
            return f'({series}: "{episode}")'
        # Handle ({{SERIES|Episode}}) format first - convert to single parentheses
        text = re.sub(r'\(\{\{(TNG|DS9|TOS|VOY|ENT|DIS|PIC|LD|PRO|SNW)\|([^}]+)\}\}\)', convert_episode_template, text, flags=re.IGNORECASE)
        # Then convert {{SERIES|Episode}} to (SERIES: "Episode")
        text = re.sub(r'\{\{(TNG|DS9|TOS|VOY|ENT|DIS|PIC|LD|PRO|SNW)\|([^}]+)\}\}', convert_episode_template, text, flags=re.IGNORECASE)
        # Fix any double parentheses that might have been created
        text = re.sub(r'\(\(([^)]+)\)\)', r'(\1)', text)
    else:
        # Remove episode templates: {{ENT|Episode Name}} or ({{ENT|Episode Name}})
        # These should be removed as they're extracted separately
        text = re.sub(r'\(\{\{(TNG|DS9|TOS|VOY|ENT|DIS|PIC|LD|PRO|SNW)\|[^}]+\}\}\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\{\{(TNG|DS9|TOS|VOY|ENT|DIS|PIC|LD|PRO|SNW)\|[^}]+\}\}', '', text, flags=re.IGNORECASE)
        
        # Also remove already-converted episode references in format (SERIES: "Episode")
        # These might have been converted in a previous pass or exist in source
        text = re.sub(r'\(\s*(TNG|DS9|TOS|VOY|ENT|DIS|PIC|LD|PRO|SNW)\s*:\s*"[^"]+"\s*\)', '', text, flags=re.IGNORECASE)
    
    # Remove image references: thumb|left|, thumb|right|, etc.
    text = re.sub(r'thumb\|[^|]+\|', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*thumb\s*\|', '', text, flags=re.IGNORECASE)
    
    # Remove [[links|display]] - keep display text, handle nested brackets
    # Handle both [[target|display]] and [[target]] formats
    def replace_link(match):
        link_content = match.group(1)
        # Handle [[target|display]] - return display text
        if '|' in link_content:
            parts = link_content.split('|', 1)
            # If display text exists and is not empty, use it; otherwise use target
            display = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
            if display:
                return display
            # Fall back to target if display is empty
            return parts[0].strip() if parts[0].strip() else link_content.strip()
        # Handle [[target]] - return target (which is the link text)
        result = link_content.strip()
        # Ensure we never return empty string - that would remove content
        return result if result else link_content
    # Match [[...]] - handle nested brackets by being careful
    # First pass: handle complete [[...]] links
    # Use a more robust pattern that handles edge cases
    text = re.sub(r'\[\[([^\]]+)\]\]', replace_link, text)
    
    # Remove other templates - handle nested templates properly using brace counting
    def remove_nested_templates(text):
        """Remove MediaWiki templates, handling nested braces."""
        result = []
        i = 0
        while i < len(text):
            if i < len(text) - 1 and text[i:i+2] == '{{':
                # Found start of template - find matching closing braces
                brace_count = 0
                start = i
                i += 2  # Skip {{
                while i < len(text):
                    if i < len(text) - 1 and text[i:i+2] == '{{':
                        brace_count += 1
                        i += 2
                    elif i < len(text) - 1 and text[i:i+2] == '}}':
                        if brace_count == 0:
                            # Found matching closing
                            i += 2  # Skip }}
                            break  # Skip this template
                        else:
                            brace_count -= 1
                            i += 2
                    else:
                        i += 1
                # Template removed, continue
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)
    
    # Remove templates like {{plainlist|...}}, {{aquote|...}}, etc.
    text = remove_nested_templates(text)
    
    # Clean up leftover incomplete markers: [[, ]], {{, }}
    # Remove orphaned opening brackets/braces (but be careful not to remove valid punctuation)
    text = re.sub(r'\[\[+', '', text)  # Remove [[ or [[[
    text = re.sub(r'\{\{+', '', text)  # Remove {{ or {{{{
    # Remove orphaned closing brackets/braces at word boundaries or end of text
    text = re.sub(r'\]\]+', '', text)  # Remove ]] or ]]]
    text = re.sub(r'\}\}+', '', text)  # Remove }} or }}}}
    
    # Remove malformed episode references like (dis: "Ferengi") or (series: "episode")
    # These are likely parsing errors - remove them
    text = re.sub(r'\([a-z]{2,4}:\s*"[^"]+"\)', '', text, flags=re.IGNORECASE)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove ref tags
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    
    # Remove trailing artifacts: (), .}}, etc.
    text = re.sub(r'\s*\(\)\s*$', '', text)  # Trailing ()
    text = re.sub(r'\.\}\}\s*$', '', text)  # Trailing .}}
    text = re.sub(r'\}\}\s*$', '', text)  # Trailing }}
    
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*\.\s*\.\s*\.', '...', text)  # Fix ellipsis
    
    # Remove any remaining escaped quotes that shouldn't be there
    # (JSON.dump() will properly escape quotes when writing, so we want clean text here)
    # Only unescape if it's a literal backslash-quote sequence in the source
    text = text.replace('\\"', '"')  # Unescape literal \" sequences
    
    # Clean up any double spaces that might have been created
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

def extract_sidebar_field(sidebar_text: str, field_name: str) -> Optional[str]:
    """Extract a field from sidebar: |field = value"""
    pattern = re.compile(rf'\|\s*{field_name}\s*=\s*([^\n]+)', re.I)
    match = pattern.search(sidebar_text)
    if not match:
        return None
    
    value = match.group(1).strip()
    # Extract from [[link]] format
    link_match = re.search(r'\[\[([^\]]+)\]\]', value)
    if link_match:
        link_content = link_match.group(1)
        display_text = extract_link_display_text(link_content)
        return clean_mediawiki_markup(display_text)
    
    # Plain text
    return clean_mediawiki_markup(value)

def extract_sidebar_list(sidebar_text: str, field_name: str) -> List[str]:
    """Extract a list field from sidebar: |field = [[item1]]<br>[[item2]] or multi-line format"""
    # Try to match field that might span multiple lines (until next | or end)
    # Pattern: |field = value (value can span multiple lines until next |field or closing }} of sidebar)
    # Need to be careful - don't stop at }} inside templates, only at the actual sidebar closing
    # Use a simpler approach: find the field, then extract until we hit a new field or the sidebar closes
    # Find the field start
    field_pattern = re.compile(rf'\|\s*{re.escape(field_name)}\s*=\s*', re.I)
    match = field_pattern.search(sidebar_text)
    if not match:
        return []
    
    # Start after the = sign
    start_pos = match.end()
    
    # Find the end - look for next |field = or closing }}
    # But we need to handle nested templates, so count braces
    i = start_pos
    brace_count = 0
    while i < len(sidebar_text):
        # Check for template start
        if i < len(sidebar_text) - 1 and sidebar_text[i:i+2] == '{{':
            brace_count += 1
            i += 2
            continue
        # Check for template end
        if i < len(sidebar_text) - 1 and sidebar_text[i:i+2] == '}}':
            if brace_count > 0:
                brace_count -= 1
                i += 2
                continue
            else:
                # This is the sidebar closing - stop here
                break
        # Check for next field (only if we're not inside a template)
        if brace_count == 0 and i < len(sidebar_text) - 1 and sidebar_text[i] == '|':
            # Check if this is a new field (has = after |)
            next_eq = sidebar_text.find('=', i, min(i+50, len(sidebar_text)))
            if next_eq > i and next_eq < i+50:
                # This is a new field - stop here
                break
        i += 1
    
    value = sidebar_text[start_pos:i].strip()
    if not value:
        return []
    
    items = []
    # Split by <br> tags, newlines, or multiple spaces
    # MediaWiki can use <br>, <br/>, <br />, or just line breaks
    parts = re.split(r'<br\s*/?>|\n+', value, flags=re.I)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # For the "relative" field, we want to preserve the full text with relationship labels
        # For other fields, extract links normally
        # Check if this looks like a relative field (has relationship labels in parentheses)
        has_relationship_label = re.search(r'\([^)]*(?:grandson|granddaughter|nephew|niece|daughter-in-law|son-in-law|cousin|uncle|aunt)[^)]*\)', part, re.I)
        
        if has_relationship_label:
            # This is a relative field - extract the name link but keep the relationship label
            # Format: [[Name]] ([[relationship]]) or [[Name]] (relationship)
            # Also handle templates like {{dis|Gaila|Ferengi}} - extract the name from template
            # First, try to extract name from templates like {{dis|Name|Description}}
            template_match = re.search(r'\{\{dis\|([^|]+)\|', part)
            if template_match:
                # Extract name from template
                template_name = template_match.group(1).strip()
                # Get the relationship label if present
                rel_match = re.search(r'\([^)]*(?:cousin|uncle|aunt|nephew|niece)[^)]*\)', part, re.I)
                if rel_match:
                    full_item = f"{template_name} {rel_match.group(0)}"
                else:
                    full_item = template_name
                items.append(full_item.strip())
            else:
                # No template, extract from link
                part_clean = re.sub(r'\{\{[^}]+\}\}', '', part)
                # Extract the name from the first link (skip template links)
                name_match = re.search(r'\[\[([^\]]+)\]\]', part_clean)
                if name_match:
                    name = extract_link_display_text(name_match.group(1))
                    # Keep the full text with relationship for later parsing
                    # Replace [[Name]] with just Name, but keep the relationship label
                    full_item = re.sub(r'\[\[([^\]]+)\]\]', lambda m: extract_link_display_text(m.group(1)), part_clean, count=1)
                    # Clean up any remaining link brackets in relationship labels
                    full_item = re.sub(r'\[\[([^\]]+)\]\]', r'\1', full_item)
                    # Handle special cases like "An [[Prinadora's father 001|ex-father-in-law]]"
                    # Remove leading articles like "An", "A", "The"
                    full_item = re.sub(r'^(An|A|The)\s+', '', full_item, flags=re.I).strip()
                    items.append(full_item.strip())
        else:
            # Regular field - extract links normally
            # For spouse/partner fields, we want to keep all spouses even if one is "ex-wife"
            # Extract each link separately
            links = re.findall(r'\[\[([^\]]+)\]\]', part)
            if links:
                for link_content in links:
                    display_text = extract_link_display_text(link_content)
                    cleaned = clean_mediawiki_markup(display_text)
                    # For spouse fields, don't filter "ex-wife" - we want to keep all spouses
                    # But still filter other relationship words
                    if cleaned:
                        # Check if it's a relationship word that should be filtered
                        # But allow "ex-wife" and "ex-husband" in spouse lists (they're status, not separate items)
                        if cleaned.lower() in ['ex-wife', 'ex-husband', 'wife', 'husband']:
                            # These are relationship labels, not names - skip them
                            continue
                        if not is_filtered_item(cleaned):
                            items.append(cleaned)
            else:
                # No links, but might be plain text name
                cleaned = clean_mediawiki_markup(part)
                # Remove parenthetical relationship labels like "(son)", "(wife)", etc.
                cleaned = re.sub(r'\([^)]*(?:son|daughter|wife|husband|brother|sister|father|mother)[^)]*\)', '', cleaned, flags=re.I)
                cleaned = cleaned.strip()
                # Only add if it's not filtered
                if cleaned and not is_filtered_item(cleaned):
                    items.append(cleaned)
    
    return items

def is_filtered_item(text: str) -> bool:
    """Check if an item should be filtered out (relationship labels, status words, dates, etc.)"""
    if not text or not text.strip():
        return True
    
    text_lower = text.lower().strip()
    
    # Relationship words
    relationship_words = [
        'son', 'daughter', 'wife', 'husband', 'brother', 'sister', 'father', 'mother',
        'son-in-law', 'daughter-in-law', 'grandson', 'granddaughter', 'nephew', 'niece',
        'cousin', 'uncle', 'aunt', 'grandfather', 'grandmother', 'half-sister', 'half-brother',
        'ex-wife', 'ex-husband', 'former', 'in-law', 'brother-in-law', 'sister-in-law',
        'ex-father-in-law', 'ex-mother-in-law', 'father-in-law', 'mother-in-law',
        'paternal', 'maternal', 'clone', 'godson', 'goddaughter', 'godfather', 'godmother'
    ]
    if text_lower in relationship_words:
        return True
    
    # Status/descriptive words
    status_words = ['deceased', 'dead', 'alive', 'missing', 'retired', 'active', 'former']
    if text_lower in status_words:
        return True
    
    # Dates (just numbers like "2367")
    if re.match(r'^\d{4}$', text_lower):
        return True
    
    # Descriptive phrases (containing words like "second", "unborn", "pioneer", etc.)
    descriptive_patterns = [
        r'second\s+\w+', r'unborn\s+\w+', r'pioneer\s+\w+', r'great-?great',
        r'\w+\'s\s+\w+',  # possessive phrases like "Kirk's ancestor", "Yates' father", "Chakotay's sister"
        r'alternate\s+timeline', r'descendant', r'ancestor',
        r'^an\s+unnamed', r'^a\s+unnamed', r'^the\s+unnamed',  # "an unnamed Gaia Klingon"
        r'unnamed\s+\w+',  # "unnamed something"
        r'three\s+hyper-?evolved',  # "Three hyper-evolved offspring"
        r'hybrids?\s+\w+\s+son',  # "Hybrids Troi son"
        r'^clone$',  # standalone "clone"
        r'great-?grandfather', r'great-?grandmother',  # "great-grandfather"
        r'^two\s+\w+',  # "Two brothers", "Two siblings"
        r'^one\s+\w+',  # "One half-sibling"
        r'^one$',  # standalone "One"
        r'^nanoprobe$',  # standalone "nanoprobe"
        r'legal\s+ward',  # "legal ward"
        r'^a\s+partner$',  # "A partner"
        r'^his\s+wife$',  # "his wife"
        r'^her\s+husband$',  # "her husband"
        r'^grandparent$',  # standalone "grandparent"
        r'^binary\s+clone$',  # "binary clone"
        r'^mrs\.?$',  # "Mrs." or "Mrs" (standalone)
        r'^mr\.?\s+\w+$',  # "Mr. Sato" (but we want to keep "Mr. Tigan" - this is tricky, so we'll be more specific)
        r'\w+\'s\s+mother$',  # "Trip's mother", "Hoshi's mother"
        r'\w+\'s\s+father$',  # "Trip's father"
    ]
    for pattern in descriptive_patterns:
        if re.search(pattern, text_lower):
            return True
    
    # Very short items that are likely fragments
    if len(text_lower) <= 2:
        return True
    
    return False

def extract_character_info(text: str, title: str) -> Dict:
    """Extract character info from sidebar."""
    sidebar_text = extract_sidebar_section(text)
    if not sidebar_text:
        return {"name": title}
    
    char_info = {
        "name": title,
        "species": extract_sidebar_field(sidebar_text, "species"),
        "affiliation": extract_sidebar_list(sidebar_text, "affiliation"),
        "rank": extract_sidebar_field(sidebar_text, "rank"),
        "occupation": extract_sidebar_field(sidebar_text, "occupation"),
        "status": extract_sidebar_field(sidebar_text, "status"),
    }
    
    # Born field
    born_field = extract_sidebar_field(sidebar_text, "born")
    if born_field:
        char_info["born"] = {"year": born_field}
    else:
        char_info["born"] = {}
    
    # Family relationships
    char_info["father"] = extract_sidebar_field(sidebar_text, "father")
    char_info["mother"] = extract_sidebar_field(sidebar_text, "mother")
    
    # Siblings - can be a list
    siblings_list = extract_sidebar_list(sidebar_text, "sibling")
    if siblings_list:
        char_info["siblings"] = siblings_list
    else:
        # Try singular form as fallback
        sibling_field = extract_sidebar_field(sidebar_text, "sibling")
        char_info["siblings"] = [sibling_field] if sibling_field else []
    
    # Spouses/Partners - MediaWiki uses "partner" field, but also check "spouse"/"spouses"
    # The "partner" field can contain multiple people with relationship labels
    spouses_list = (extract_sidebar_list(sidebar_text, "partner") or 
                   extract_sidebar_list(sidebar_text, "spouse") or 
                   extract_sidebar_list(sidebar_text, "spouses"))
    if spouses_list:
        char_info["spouses"] = spouses_list
    else:
        # Try singular form as fallback
        spouse_field = (extract_sidebar_field(sidebar_text, "partner") or 
                       extract_sidebar_field(sidebar_text, "spouse") or 
                       extract_sidebar_field(sidebar_text, "spouses"))
        char_info["spouses"] = [spouse_field] if spouse_field else []
    
    # Children - should be a list
    children_list = extract_sidebar_list(sidebar_text, "children")
    if children_list:
        char_info["children"] = children_list
    else:
        # Try as single field as fallback
        children_field = extract_sidebar_field(sidebar_text, "children")
        char_info["children"] = [children_field] if children_field else []
    
    # Extended family relationships - initialize all lists first
    char_info["grandsons"] = []
    char_info["granddaughters"] = []
    char_info["sons_in_law"] = []
    char_info["daughters_in_law"] = []
    char_info["other_relatives"] = []
    
    # Grandchildren - try multiple field name variations (singular and plural)
    grandsons = (extract_sidebar_list(sidebar_text, "grandson") or 
                 extract_sidebar_list(sidebar_text, "grandsons") or
                 extract_sidebar_list(sidebar_text, "grandson(s)"))
    if grandsons:
        char_info["grandsons"] = grandsons
    
    granddaughters = (extract_sidebar_list(sidebar_text, "granddaughter") or 
                     extract_sidebar_list(sidebar_text, "granddaughters") or
                     extract_sidebar_list(sidebar_text, "granddaughter(s)"))
    if granddaughters:
        char_info["granddaughters"] = granddaughters
    
    # In-laws - try multiple field name variations (with hyphens, underscores, and spaces)
    sons_in_law = (extract_sidebar_list(sidebar_text, "son-in-law") or 
                   extract_sidebar_list(sidebar_text, "son_in_law") or
                   extract_sidebar_list(sidebar_text, "sons-in-law") or
                   extract_sidebar_list(sidebar_text, "sons_in_law") or
                   extract_sidebar_list(sidebar_text, "son in law") or
                   extract_sidebar_list(sidebar_text, "sons in law"))
    if sons_in_law:
        char_info["sons_in_law"] = sons_in_law
    
    daughters_in_law = (extract_sidebar_list(sidebar_text, "daughter-in-law") or 
                        extract_sidebar_list(sidebar_text, "daughter_in_law") or
                        extract_sidebar_list(sidebar_text, "daughters-in-law") or
                        extract_sidebar_list(sidebar_text, "daughters_in_law") or
                        extract_sidebar_list(sidebar_text, "daughter in law") or
                        extract_sidebar_list(sidebar_text, "daughters in law"))
    if daughters_in_law:
        char_info["daughters_in_law"] = daughters_in_law
    
    # Other relatives - MediaWiki uses "relative" field (not "other relatives")
    # This field contains mixed relationship types that need to be parsed
    # Format: |relative = [[Nog]] ([[grandson]])<br>[[Stol]] ([[nephew]])<br>[[Leeta]] ([[daughter-in-law]])
    relative_field = extract_sidebar_list(sidebar_text, "relative") or extract_sidebar_list(sidebar_text, "relatives")
    if relative_field:
        # Parse the relative field to extract different relationship types
        # The extract_sidebar_list already extracts links, so we get items like "Nog (grandson)"
        for item in relative_field:
            if not item or not item.strip():
                continue
                
            item_lower = item.lower()
            # Skip if it's just a relationship word (like "nephew" extracted separately)
            if item_lower.strip() in ['son', 'daughter', 'wife', 'husband', 'brother', 'sister', 'father', 'mother', 
                                      'grandson', 'granddaughter', 'nephew', 'niece', 'cousin', 'uncle', 'aunt',
                                      'son-in-law', 'daughter-in-law', 'father-in-law', 'mother-in-law']:
                continue
            
            # Check if it contains relationship labels and categorize
            # Handle both (grandson) and ([[grandson]]) formats
            if 'grandson' in item_lower:
                # Extract name (remove relationship label in parentheses)
                name = re.sub(r'\s*\([^)]*(?:grandson)[^)]*\)', '', item, flags=re.I).strip()
                name = re.sub(r'\s*\(\[\[grandson\]\]\)', '', name, flags=re.I).strip()
                if name and name.lower() not in ['grandson', 'grandsons'] and name not in char_info["grandsons"]:
                    char_info["grandsons"].append(name)
            elif 'granddaughter' in item_lower:
                name = re.sub(r'\s*\([^)]*(?:granddaughter)[^)]*\)', '', item, flags=re.I).strip()
                name = re.sub(r'\s*\(\[\[granddaughter\]\]\)', '', name, flags=re.I).strip()
                if name and name.lower() not in ['granddaughter', 'granddaughters'] and name not in char_info["granddaughters"]:
                    char_info["granddaughters"].append(name)
            elif 'daughter-in-law' in item_lower or 'daughter in law' in item_lower:
                name = re.sub(r'\s*\([^)]*(?:daughter-in-law|daughter in law)[^)]*\)', '', item, flags=re.I).strip()
                name = re.sub(r'\s*\(\[\[daughter-in-law\]\]\)', '', name, flags=re.I).strip()
                # Also handle "former daughter-in-law"
                name = re.sub(r'\s*former\s+', '', name, flags=re.I).strip()
                if name and name.lower() not in ['daughter-in-law', 'daughters-in-law', 'daughter in law'] and name not in char_info["daughters_in_law"]:
                    char_info["daughters_in_law"].append(name)
            elif 'son-in-law' in item_lower or 'son in law' in item_lower:
                name = re.sub(r'\s*\([^)]*(?:son-in-law|son in law)[^)]*\)', '', item, flags=re.I).strip()
                name = re.sub(r'\s*\(\[\[son-in-law\]\]\)', '', name, flags=re.I).strip()
                if name and name.lower() not in ['son-in-law', 'sons-in-law', 'son in law'] and name not in char_info["sons_in_law"]:
                    char_info["sons_in_law"].append(name)
            else:
                # Other relative (nephew, cousin, etc.) - remove relationship label
                name = re.sub(r'\s*\([^)]+\)', '', item).strip()
                # Remove any remaining link brackets
                name = re.sub(r'\[\[([^\]]+)\]\]', r'\1', name)
                # Filter out relationship words and descriptive phrases
                if name and not is_filtered_item(name) and name not in char_info["other_relatives"]:
                    char_info["other_relatives"].append(name)
    
    # Also try "other relatives" field name as fallback
    other_relatives = (extract_sidebar_list(sidebar_text, "other relatives") or
                      extract_sidebar_list(sidebar_text, "other_relatives") or
                      extract_sidebar_list(sidebar_text, "other relative") or
                      extract_sidebar_list(sidebar_text, "other_relative"))
    if other_relatives:
        for item in other_relatives:
            if item and item not in char_info["other_relatives"]:
                char_info["other_relatives"].append(item)
    
    # Played by
    char_info["played_by"] = extract_sidebar_field(sidebar_text, "actor")
    
    # Description (first paragraph after sidebar closes)
    sidebar_end = text.find(sidebar_text) + len(sidebar_text) if sidebar_text else 0
    if sidebar_end > 0:
        # Find first paragraph after sidebar (skip templates, quotes, etc.)
        after_sidebar = text[sidebar_end:sidebar_end+3000]
        # Look for first substantial text block starting with character name or "was a/an/the"
        # Pattern: }} followed by optional templates/quotes, then text starting with capital letter
        desc_match = re.search(
            r'\}\}\s*(?:\{\{[^}]+\}\}\s*)*\n\s*([A-Z][^\n=]{100,800})', 
            after_sidebar, 
            re.MULTILINE
        )
        if desc_match:
            desc_text = desc_match.group(1)
            # Remove any remaining templates/quotes at start
            desc_text = re.sub(r'^\s*\{\{[^}]+\}\}\s*', '', desc_text)
            desc_text = clean_mediawiki_markup(desc_text)
            # Truncate at sentence boundary if too long
            if len(desc_text) > 500:
                # Find last sentence ending before 500 chars
                sentence_end = desc_text[:500].rfind('.')
                if sentence_end > 200:
                    desc_text = desc_text[:sentence_end+1]
                else:
                    desc_text = desc_text[:500]
            char_info["description"] = desc_text if desc_text else None
        else:
            char_info["description"] = None
    else:
        char_info["description"] = None
    
    # Quote (if present) - handle {{aquote|text|source|year|episode}}
    # Template format: {{aquote|text with [[links]]|source|year|episode}}
    # Need to handle nested pipes in quote text, so find template boundaries first
    quote_start = text.find('{{aquote|')
    if quote_start != -1:
        # Find the closing }} by counting braces
        i = quote_start + 9  # Skip past "{{aquote|"
        brace_count = 2  # We have {{
        bracket_count = 0  # Track [[ for nested structures
        parts = []
        current_part = ""
        
        while i < len(text):
            char = text[i]
            
            # Track brackets for nested [[links]]
            if text[i:i+2] == '[[':
                bracket_count += 1
                current_part += text[i:i+2]
                i += 2
                continue
            elif text[i:i+2] == ']]' and bracket_count > 0:
                bracket_count -= 1
                current_part += text[i:i+2]
                i += 2
                continue
            
            # If we're inside brackets, just add to current part
            if bracket_count > 0:
                current_part += char
                i += 1
                continue
            
            # Check for closing }}
            if text[i:i+2] == '}}' and len(parts) >= 3:
                parts.append(current_part)
                break
            
            # Check for pipe separator (only if we're not inside brackets)
            if char == '|' and len(parts) < 3:
                parts.append(current_part)
                current_part = ""
                i += 1
                continue
            
            current_part += char
            i += 1
        
        if len(parts) >= 4:
            quote_text_raw = parts[0]
            quote_source_raw = parts[1]
            quote_episode_raw = parts[3]
            
            # Clean quote text - handle nested [[links]] but keep display text
            quote_text = quote_text_raw
            # Replace [[target|display]] with display, [[target]] with target
            quote_text = re.sub(r'\[\[([^\]]+)\]\]', lambda m: m.group(1).split('|')[-1], quote_text)
            # Remove any remaining templates
            quote_text = re.sub(r'\{\{[^}]+\}\}', '', quote_text)
            # Clean HTML entities
            quote_text = quote_text.replace('&hellip;', '...')
            quote_text = quote_text.replace('&mdash;', '—')
            quote_text = quote_text.replace('&ndash;', '–')
            quote_text = clean_mediawiki_markup(quote_text)
            
            # Clean source
            quote_source = clean_mediawiki_markup(quote_source_raw)
            
            # Clean episode - extract just the episode name
            quote_episode = quote_episode_raw.split('|')[-1] if '|' in quote_episode_raw else quote_episode_raw
            quote_episode = clean_mediawiki_markup(quote_episode)
            
            if quote_text and len(quote_text) > 10 and not quote_text.startswith('['):  # Valid quote
                char_info["quote"] = {
                    "text": quote_text,
                    "source": quote_source,
                    "episode": quote_episode
                }
            else:
                char_info["quote"] = None
        else:
            char_info["quote"] = None
    else:
        char_info["quote"] = None
    
    return char_info

def detect_content_type(paragraph: str) -> str:
    """Detect content type of a paragraph."""
    paragraph_lower = paragraph.lower()
    
    # Priority 1: Check for episode references - if it has an episode, it's an event
    if re.search(r'\{\{(TNG|DS9|TOS|VOY|ENT|DIS|PIC|LD|PRO|SNW)\|', paragraph):
        return "event"
    
    # Priority 2: Check for relationship keywords (but not if it's clearly an event)
    relationship_keywords = ["relationship", "married", "divorced", "brother", "sister", "father", "mother", "son", "daughter", "loved", "close"]
    if any(kw in paragraph_lower for kw in relationship_keywords) and not re.search(r'\d{4}', paragraph):
        # If it mentions relationships but no year/episode, likely relationship content
        return "relationship"
    
    # Priority 3: Check for background/summary keywords
    background_keywords = ["was a", "was an", "was the", "became", "worked as", "served as", "known as"]
    if any(kw in paragraph_lower for kw in background_keywords):
        return "background"
    
    # Default: if it has a year or seems narrative, it's an event
    if re.search(r'\d{4}', paragraph) or len(paragraph) > 100:
        return "event"
    
    # Fallback
    return "background"

def extract_episode_from_text(text: str) -> Optional[Tuple[str, str]]:
    """Extract series and episode from text: {{DS9|Episode Name}}"""
    episode_match = re.search(r'\{\{(TNG|DS9|TOS|VOY|ENT|DIS|PIC|LD|PRO|SNW)\|([^}]+)\}\}', text)
    if episode_match:
        return (episode_match.group(1), episode_match.group(2).strip())
    return None

def extract_timeline_sections(text: str, character_name: str) -> Dict:
    """Extract timeline sections from page text."""
    sections = {}
    
    # Find all section headers: == Section Name ==
    section_pattern = re.compile(r'^==\s*([^=]+)\s*==', re.MULTILINE)
    matches = list(section_pattern.finditer(text))
    
    for i, match in enumerate(matches):
        section_name = match.group(1).strip().lower().replace(' ', '_')
        start_pos = match.end()
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(text)
        section_text = text[start_pos:end_pos]
        
        # Skip certain sections that aren't useful for question generation
        # Note: Trivia sections don't exist on wiki pages - trivia was generated by old extraction script
        # Skip memorable_quotes - we already have the main quote in character.quote
        skip_sections = [
            'appendices', 
            'background_information', 
            'external_links',
            'external_link',  # Also handle singular form
            'references',
            'apocrypha',
            'connections',
            'memorable_quotes',
            'see_also',
            'external_links_and_references'
        ]
        if section_name in skip_sections:
            continue
        
        # Additional check: skip if section name contains "external", "link", "reference", "category"
        # This catches variations we might have missed
        skip_keywords = ['external', 'link', 'reference', 'category', 'interwiki']
        if any(keyword in section_name for keyword in skip_keywords):
            continue
        
        # Parse paragraphs in section
        paragraphs = re.split(r'\n\n+', section_text)
        events = []
        
        for para in paragraphs:
            para = para.strip()
            if not para or len(para) < 20:
                continue
            
            # Extract episode info BEFORE cleaning (so we can remove it from text)
            episode_info = extract_episode_from_text(para)
            
            # Skip paragraphs that are just interwiki links, categories, or other metadata
            # Interwiki links: de:Title, fr:Title, etc. (may contain parentheses)
            # Categories: Category:Name
            para_stripped = para.strip()
            # Check if paragraph is mostly interwiki/category content
            interwiki_pattern = r'[a-z]{2,3}:[^\s]+'
            category_pattern = r'Category:[^\s]+'
            interwiki_matches = len(re.findall(interwiki_pattern, para_stripped, re.I))
            category_matches = len(re.findall(category_pattern, para_stripped, re.I))
            # If most of the content is interwiki/category links, skip it
            words = para_stripped.split()
            if len(words) > 0 and (interwiki_matches + category_matches) >= len(words) * 0.8:
                continue  # Skip interwiki/category lines
            
            # Clean paragraph - remove episode references since we have structured series/episode fields
            # Episode info is extracted separately for the episode field, so we don't need it in text
            cleaned = clean_mediawiki_markup(para, preserve_episode_refs=False)
            if not cleaned:
                continue
            
            # Remove trailing artifacts that might remain
            cleaned = re.sub(r'\s*\(\)\s*', ' ', cleaned)  # Any () (not just trailing)
            cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
            cleaned = re.sub(r'\s*\.\s*$', '', cleaned)  # Trailing period if it's just "."
            cleaned = cleaned.strip()
            
            # Skip if it's still just interwiki/category content after cleaning
            if re.match(r'^[a-z]{2,3}:[^\s]+', cleaned, re.I) or cleaned.startswith('Category:'):
                continue
            
            if not cleaned or len(cleaned) < 10:
                continue
            
            # Detect content type
            content_type = detect_content_type(para)  # Use original para for detection
            
            event_obj = {
                "content_type": content_type
            }
            
            if content_type == "event":
                event_obj["event"] = cleaned
                if episode_info:
                    event_obj["series"] = episode_info[0]
                    # Clean episode name - but don't use full clean_mediawiki_markup
                    # as it removes section markers that might match episode names
                    episode_name = episode_info[1]
                    if '|' in episode_name:
                        episode_name = episode_name.split('|')[-1]
                    # Only do minimal cleaning for episode names - remove templates and links
                    episode_name = episode_name.strip()
                    # Remove any remaining template markers
                    episode_name = re.sub(r'\{\{[^}]+\}\}', '', episode_name)
                    # Remove link markers but keep text
                    episode_name = re.sub(r'\[\[([^\]]+)\]\]', lambda m: m.group(1).split('|')[-1], episode_name)
                    event_obj["episode"] = episode_name.strip()
            elif content_type == "background":
                event_obj["background"] = cleaned
            elif content_type == "relationship":
                event_obj["relationship"] = cleaned
            
            events.append(event_obj)
        
        if events:
            sections[section_name] = events
    
    return sections

def extract_appearances(text: str) -> Dict:
    """Extract appearances from Appendices section - uses same logic as extract_appearances_section.py"""
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
    
    # Find series context (e.g., * {{DS9}})
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
    
    # Pattern for {{e|Episode}} format (used in Appendices)
    e_pattern = re.compile(r'\{\{e\|([^}]+)\}\}')
    
    # Also search for direct {{SERIES|Episode}} patterns
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
    
    # Remove empty series
    return {k: v for k, v in appearances.items() if v}

def convert_character_page(text: str, title: str) -> Dict:
    """Convert a character page from MediaWiki to JSON structure."""
    result = {
        "character": extract_character_info(text, title)
    }
    
    # Extract timeline sections
    timeline_sections = extract_timeline_sections(text, title)
    result.update(timeline_sections)
    
    # Extract appearances
    result["appearances"] = extract_appearances(text)
    
    return result

def convert_from_json(json_path: str, character_name: str, output_path: str) -> bool:
    """Convert character page from extracted_data.json to new format."""
    print(f"Loading JSON file: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = data.get('pages', [])
    indices = data.get('indices', {})
    
    # Find character page
    character_name_lower = character_name.lower()
    for page in pages:
        if page.get('title', '').lower() == character_name_lower:
            print(f"Found page: {page.get('title')}")
            full_text = page.get('full_text', '')
            
            # Convert to new format
            result = convert_character_page(full_text, page.get('title', character_name))
            
            # Save
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"Saved to {output_path}")
            return True
    
    print(f"Character '{character_name}' not found")
    return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python convert_character_direct.py <json_path> <character_name> <output_path>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    character_name = sys.argv[2]
    output_path = sys.argv[3]
    
    convert_from_json(json_path, character_name, output_path)

