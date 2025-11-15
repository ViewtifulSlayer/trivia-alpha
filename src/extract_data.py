#!/usr/bin/env python3
"""
Extract structured data from Memory Alpha XML for trivia question generation.
Processes XML file and extracts pages with series, characters, and content.
"""

import xml.etree.ElementTree as ET
import json
import re
import sys
from collections import defaultdict
from datetime import datetime

# MediaWiki XML namespace
NS = '{http://www.mediawiki.org/xml/export-0.11/}'

# Series patterns
SERIES_PATTERNS = {
    'TOS': re.compile(r'\{\{TOS\|([^\}]+)\}\}'),
    'TNG': re.compile(r'\{\{TNG\|([^\}]+)\}\}'),
    'DS9': re.compile(r'\{\{DS9\|([^\}]+)\}\}'),
    'VOY': re.compile(r'\{\{VOY\|([^\}]+)\}\}'),
    'ENT': re.compile(r'\{\{ENT\|([^\}]+)\}\}'),
    'DIS': re.compile(r'\{\{DIS\|([^\}]+)\}\}'),
    'PIC': re.compile(r'\{\{PIC\|([^\}]+)\}\}'),
    'LD': re.compile(r'\{\{LD\|([^\}]+)\}\}'),
    'PRO': re.compile(r'\{\{PRO\|([^\}]+)\}\}'),
    'SNW': re.compile(r'\{\{SNW\|([^\}]+)\}\}'),
}

# Character link pattern: [[Character Name|Display Text]] or [[Character Name]]
CHARACTER_PATTERN = re.compile(r'\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]')

# Filter out non-character links (concepts, categories, etc.)
NON_CHARACTER_PATTERNS = [
    re.compile(r'^Category:'),
    re.compile(r'^File:'),
    re.compile(r'^Image:'),
    re.compile(r'^Template:'),
    re.compile(r'^Memory Alpha:'),
    re.compile(r'^User:'),
    re.compile(r'^Help:'),
    re.compile(r'^Portal:'),
    re.compile(r'^File talk:'),
    re.compile(r'^Talk:'),
    re.compile(r'^Special:'),
    re.compile(r'^MediaWiki:'),
    re.compile(r'^Module:'),
    re.compile(r'^GeoJson:'),
    re.compile(r'^Blog:'),
    re.compile(r'^Message Wall'),
    re.compile(r'^Board'),
    re.compile(r'^Topic'),
    re.compile(r'^Map'),
    # Common non-character terms
    re.compile(r'^(Starfleet|Federation|Earth|Human|planet|starship|officer|Captain|Commander|Lieutenant|Ensign|Doctor)$', re.I),
    re.compile(r'^\d+th century$', re.I),
    re.compile(r'^\d{4}$'),  # Years
    re.compile(r'^Alpha Quadrant$', re.I),
    re.compile(r'^Beta Quadrant$', re.I),
    re.compile(r'^Gamma Quadrant$', re.I),
    re.compile(r'^Delta Quadrant$', re.I),
    re.compile(r'^star system$', re.I),
    re.compile(r'^Pocket Books$', re.I),
]

def is_character_link(link_text):
    """Check if a link represents an actual character (not a concept/category)."""
    link_text = link_text.strip()
    
    # Filter out patterns that are clearly not characters
    for pattern in NON_CHARACTER_PATTERNS:
        if pattern.search(link_text):
            return False
    
    # Additional heuristics
    if len(link_text) > 50:  # Very long links are usually not characters
        return False
    
    if link_text.lower() in ['star trek', 'reference tables', 'regular cast']:
        return False
    
    return True

def extract_series_references(text):
    """Extract all series references from text."""
    series_refs = defaultdict(list)
    
    for series, pattern in SERIES_PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            series_refs[series].append(match.strip())
    
    return dict(series_refs)

def extract_characters(text, max_per_page=50):
    """Extract character links from text, filtering out non-characters."""
    char_matches = CHARACTER_PATTERN.findall(text)
    characters = []
    
    for char in char_matches[:max_per_page]:
        char = char.strip()
        if is_character_link(char):
            characters.append(char)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_chars = []
    for char in characters:
        if char.lower() not in seen:
            seen.add(char.lower())
            unique_chars.append(char)
    
    return unique_chars

def extract_species(text):
    """Extract species references from text."""
    # Common species patterns
    species_keywords = [
        'Klingon', 'Vulcan', 'Human', 'Borg', 'Romulan', 'Cardassian',
        'Bajoran', 'Ferengi', 'Betazoid', 'Trill', 'Andorian', 'Tellarite',
        'Denobulan', 'Orion', 'Gorn', 'Tholian', 'Breen', 'Jem\'Hadar',
        'Vorta', 'Founder', 'Changeling', 'Q', 'Talaxian', 'Kazon',
        'Vidiian', 'Hirogen', 'Species 8472', 'Xindi'
    ]
    
    found_species = []
    text_lower = text.lower()
    
    for species in species_keywords:
        # Look for species mentions (as standalone words or in links)
        pattern = re.compile(r'\b' + re.escape(species.lower()) + r'\b', re.I)
        if pattern.search(text):
            found_species.append(species)
    
    return list(set(found_species))  # Remove duplicates

def extract_locations(text):
    """Extract location references from text."""
    # Common location patterns
    location_patterns = [
        r'\b(Deep Space 9|DS9)\b',
        r'\b(Alpha|Beta|Gamma|Delta) Quadrant\b',
        r'\b(Starbase \d+)\b',
        r'\b(Enterprise|Enterprise-D|Enterprise-E|Voyager|Defiant)\b',
        r'\b(Earth|Vulcan|Qo\'noS|Cardassia|Bajor|Romulus|Ferenginar)\b',
    ]
    
    found_locations = []
    for pattern in location_patterns:
        matches = re.findall(pattern, text, re.I)
        for match in matches:
            if isinstance(match, tuple):
                found_locations.extend([m for m in match if m])
            else:
                found_locations.append(match)
    
    return list(set(found_locations))  # Remove duplicates

def extract_organizations(text):
    """Extract organization references from text."""
    org_keywords = [
        'Starfleet', 'Federation', 'Klingon Empire', 'Romulan Star Empire',
        'Cardassian Union', 'Dominion', 'Borg Collective', 'Maquis',
        'Section 31', 'Tal Shiar', 'Obsidian Order'
    ]
    
    found_orgs = []
    text_lower = text.lower()
    
    for org in org_keywords:
        pattern = re.compile(r'\b' + re.escape(org.lower()) + r'\b', re.I)
        if pattern.search(text):
            found_orgs.append(org)
    
    return list(set(found_orgs))  # Remove duplicates

def extract_concepts(text):
    """Extract concept references (time periods, technologies, etc.)."""
    concepts = []
    
    # Time periods
    time_pattern = re.compile(r'\b(\d+th century)\b', re.I)
    time_matches = time_pattern.findall(text)
    concepts.extend(time_matches)
    
    # Technologies (common ones)
    tech_keywords = ['warp drive', 'transporter', 'phaser', 'replicator', 
                     'holodeck', 'deflector', 'shields', 'cloaking device']
    text_lower = text.lower()
    for tech in tech_keywords:
        if tech in text_lower:
            concepts.append(tech.title())
    
    return list(set(concepts))  # Remove duplicates

def clean_text(text):
    """Basic text cleaning - remove excessive MediaWiki markup."""
    # Remove HTML entities
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Configuration: Minimum page length (configurable for different series)
MIN_PAGE_LENGTH = 200

def extract_page_data(page_elem):
    """Extract structured data from a page element."""
    title_elem = page_elem.find(f'.//{NS}title')
    ns_elem = page_elem.find(f'.//{NS}ns')
    text_elem = page_elem.find(f'.//{NS}text')
    
    if title_elem is None or ns_elem is None or text_elem is None:
        return None
    
    title = title_elem.text or ''
    ns = ns_elem.text or '0'
    text_content = text_elem.text or ''
    
    # Only process main namespace pages (ns=0)
    if ns != '0' or not text_content:
        return None
    
    # Skip very short pages (likely stubs) - configurable threshold
    if len(text_content) < MIN_PAGE_LENGTH:
        return None
    
    # Extract series references
    series_refs = extract_series_references(text_content)
    
    # Extract characters
    characters = extract_characters(text_content)
    
    # Extract additional subject fields
    species = extract_species(text_content)
    locations = extract_locations(text_content)
    organizations = extract_organizations(text_content)
    concepts = extract_concepts(text_content)
    
    # Extract episodes from series_refs
    episodes = []
    for series, ep_list in series_refs.items():
        episodes.extend(ep_list)
    episodes = list(set(episodes))  # Remove duplicates
    
    # Get series list (for filtering)
    series_list = list(series_refs.keys())
    
    # Clean text for content snippets (first 500 chars)
    cleaned_text = clean_text(text_content[:500])
    
    return {
        'title': title,
        'text_length': len(text_content),
        'series': series_list,
        'series_refs': series_refs,  # Detailed references with episode names
        'characters': characters,
        'species': species,
        'locations': locations,
        'organizations': organizations,
        'concepts': concepts,
        'episodes': episodes,
        'content_snippet': cleaned_text,
        'full_text': text_content  # Keep full text for question generation
    }

def extract_all_data(xml_path, output_json, max_pages=None, progress_interval=10000):
    """Extract all page data from XML file."""
    print(f"Extracting data from: {xml_path}")
    print("=" * 60)
    
    pages_data = []
    page_count = 0
    processed_count = 0
    
    # Use iterparse for memory-efficient streaming
    context = ET.iterparse(xml_path, events=('start', 'end'))
    context = iter(context)
    event, root = next(context)
    
    print("Processing XML (this may take several minutes)...")
    
    for event, elem in context:
        if event == 'end' and elem.tag.replace(NS, '') == 'page':
            page_count += 1
            
            page_data = extract_page_data(elem)
            if page_data:
                pages_data.append(page_data)
                processed_count += 1
            
            # Clear element to free memory
            elem.clear()
            root.clear()
            
            if page_count % progress_interval == 0:
                print(f"  Processed {page_count:,} pages, extracted {processed_count:,} valid pages...")
            
            # Limit for testing
            if max_pages and page_count >= max_pages:
                break
    
    print(f"\n{'=' * 60}")
    print(f"Total pages processed: {page_count:,}")
    print(f"Valid pages extracted: {processed_count:,}")
    
    # Build indices for quick lookup (modular design - easy to add more indices)
    series_index = defaultdict(list)
    character_index = defaultdict(list)
    species_index = defaultdict(list)
    location_index = defaultdict(list)
    organization_index = defaultdict(list)
    concept_index = defaultdict(list)
    episode_index = defaultdict(list)
    
    for idx, page in enumerate(pages_data):
        # Index by series
        for series in page['series']:
            series_index[series].append(idx)
        
        # Index by character
        for char in page['characters']:
            character_index[char.lower()].append(idx)
        
        # Index by species
        for species in page.get('species', []):
            species_index[species.lower()].append(idx)
        
        # Index by location
        for location in page.get('locations', []):
            location_index[location.lower()].append(idx)
        
        # Index by organization
        for org in page.get('organizations', []):
            organization_index[org.lower()].append(idx)
        
        # Index by concept
        for concept in page.get('concepts', []):
            concept_index[concept.lower()].append(idx)
        
        # Index by episode
        for episode in page.get('episodes', []):
            episode_index[episode.lower()].append(idx)
    
    result = {
        'metadata': {
            'extraction_date': datetime.now().isoformat(),
            'source_file': xml_path,
            'total_pages_processed': page_count,
            'valid_pages_extracted': processed_count,
            'series_count': len(series_index),
            'character_count': len(character_index),
            'species_count': len(species_index),
            'location_count': len(location_index),
            'organization_count': len(organization_index),
            'concept_count': len(concept_index),
            'episode_count': len(episode_index),
            'min_page_length': MIN_PAGE_LENGTH  # Store config for reference
        },
        'pages': pages_data,
        'indices': {
            'by_series': {k: v for k, v in series_index.items()},
            'by_character': {k: v for k, v in character_index.items()},
            'by_species': {k: v for k, v in species_index.items()},
            'by_location': {k: v for k, v in location_index.items()},
            'by_organization': {k: v for k, v in organization_index.items()},
            'by_concept': {k: v for k, v in concept_index.items()},
            'by_episode': {k: v for k, v in episode_index.items()}
        }
    }
    
    # Save to JSON
    print(f"\nSaving to {output_json}...")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    file_size_mb = len(json.dumps(result, ensure_ascii=False).encode('utf-8')) / (1024 * 1024)
    print(f"Saved {file_size_mb:.2f} MB to {output_json}")
    
    # Print summary statistics
    print(f"\n{'=' * 60}")
    print("Extraction Summary:")
    print(f"  Series found: {len(series_index)}")
    for series in sorted(series_index.keys()):
        print(f"    {series}: {len(series_index[series])} pages")
    
    print(f"\n  Top 10 Characters:")
    top_chars = sorted(character_index.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for char, indices in top_chars:
        print(f"    {char}: {len(indices)} pages")
    
    print(f"\n  Subject Fields:")
    print(f"    Species: {len(species_index)} unique")
    print(f"    Locations: {len(location_index)} unique")
    print(f"    Organizations: {len(organization_index)} unique")
    print(f"    Concepts: {len(concept_index)} unique")
    print(f"    Episodes: {len(episode_index)} unique")
    
    return result

if __name__ == '__main__':
    xml_path = '../data/raw/enmemoryalpha_pages_current.xml'
    output_json = '../data/extracted/extracted_data.json'
    
    # For testing, limit pages (remove max_pages=None for full extraction)
    max_pages = None  # Set to a number (e.g., 1000) for testing
    
    try:
        extract_all_data(xml_path, output_json, max_pages=max_pages)
        print("\n" + "=" * 60)
        print("Extraction complete!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

