import os
import re
import json
import argparse
import traceback
from datetime import datetime, timezone

# Local import - using direct converter (recommended approach)
from convert_character_direct import convert_from_json

# --- Helper functions --------------------------------------------------


def is_character_page(page: dict) -> bool:
    """Return True if page is about an individual/character. Requires sidebar character template."""
    title = page.get("title", "")
    text = page.get("full_text", "")
    text_lower = text.lower()
    
    # Skip obviously non-character pages
    if not title or len(title) > 100:
        return False
    
    # Exclude list/organization pages
    exclude_patterns = [
        " members", " list", " category:", " template:",
        " episode", " novel", " comic", " book", " song",
        " organization", " alliance", " empire", " federation",
        " species", " race", " planet", " starship", " class",
    ]
    title_lower = title.lower()
    if any(pattern in title_lower for pattern in exclude_patterns):
        return False
    
    # REQUIRE character sidebar template - this is the most reliable indicator
    # Memory Alpha uses "{{sidebar individual" for character pages
    character_templates = [
        "{{sidebar individual",
        "{{sidebar individual|",
        "{{sidebar character",
        "{{sidebar character|",
        "{{infobox person",
        "{{infobox person|",
    ]
    has_character_template = any(template in text_lower for template in character_templates)
    
    if not has_character_template:
        return False
    
    # Additional validation: check for character-specific fields in sidebar
    # Character pages typically have: |actor=, |species=, |affiliation=, etc.
    sidebar_indicators = [
        "|actor", "|played by", "|portrayed by",
        "|species", "|affiliation", "|rank",
    ]
    has_sidebar_fields = any(indicator in text_lower[:5000] for indicator in sidebar_indicators)
    
    return has_sidebar_fields


CHECKPOINT_FILENAME = "bulk_extraction_checkpoint.json"


def load_checkpoint(output_dir):
    checkpoint_path = os.path.join(output_dir, CHECKPOINT_FILENAME)
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "processed": [],
        "failed": {},
        "started": datetime.now(timezone.utc).isoformat() + "Z",
    }


def save_checkpoint(output_dir, checkpoint):
    checkpoint_path = os.path.join(output_dir, CHECKPOINT_FILENAME)
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)


def is_stub_character(data: dict) -> bool:
    """Check if character is a stub (minimal content - not useful for question generation).
    
    Rejects characters that only have:
    - Character attributes (name, species, etc.)
    - Appearances list
    But NO timeline events, quotes, descriptions, or family relationships.
    """
    # Count timeline sections (everything except 'character' and 'appearances')
    timeline_sections = [k for k in data.keys() if k not in ['character', 'appearances']]
    
    # Count total timeline items
    timeline_items = 0
    for section in timeline_sections:
        if isinstance(data[section], list):
            timeline_items += len(data[section])
    
    # Count appearances
    appearances = data.get('appearances', {})
    appearance_count = sum(len(eps) for eps in appearances.values() if isinstance(eps, list))
    
    # Get character info
    char_info = data.get('character', {})
    has_quote = char_info.get('quote') is not None
    has_description = char_info.get('description') is not None and char_info.get('description', '').strip()
    
    # Check for family relationships
    has_family = any([
        char_info.get('father'),
        char_info.get('mother'),
        char_info.get('siblings', []),
        char_info.get('spouses', []),
        char_info.get('children', [])
    ])
    
    # Auto-reject if:
    # 1. No timeline items AND no appearances (complete stub)
    # 2. Has appearances but ONLY character info + appearances (no timeline, no quote, no description, no family)
    # This catches files that are just "character" + "appearances" with nothing else useful
    if timeline_items == 0 and appearance_count == 0:
        return True  # Complete stub
    
    # Minimal content stub: ONLY has character attributes + appearances, nothing else
    if timeline_items == 0 and not has_quote and not has_description and not has_family:
        return True  # Just character info + appearances, reject
    
    return False


def validate_output(output_path):
    if not os.path.exists(output_path):
        return False, "File not created"
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Invalid JSON: {e}"

    # Basic validation rules
    if "character" not in data:
        return False, "Missing 'character' key"
    
    # Check if stub - skip validation for stubs (they'll be filtered out)
    if is_stub_character(data):
        return False, "Stub character (no timeline, no appearances)"
    
    # Ensure every timeline item has content_type
    for key, value in data.items():
        if isinstance(value, list):
            for item in value:
                if key == "trivia_facts":
                    continue  # trivia_facts are plain strings for now
                if isinstance(item, dict) and "content_type" not in item:
                    return False, f"Missing content_type in section {key}"
    return True, "OK"


def bulk_extract(json_path, output_dir, start_after=None, limit=None):
    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)

    # Load big extraction JSON to get index
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

# Load/initialize checkpoint
    checkpoint = load_checkpoint(output_dir)
    processed_set = set(checkpoint["processed"])

    # Load pages and iterate directly
    pages = data["pages"]
    
    # Track processed count
    processed_count = 0
    seen_titles = set()  # Avoid duplicates
    
    # Iterate through all pages, checking if they're character pages
    print(f"Scanning {len(pages):,} pages for character pages...")
    checked = 0
    
    for page_idx, page in enumerate(pages):
        if limit and processed_count >= limit:
            break
        
        checked += 1
        if checked % 5000 == 0:
            print(f"  Checked {checked:,}/{len(pages):,} pages ({checked*100//len(pages)}%), found {processed_count} new characters so far...")
            
        # Check if this is a character page
        if not is_character_page(page):
            continue
        
        char = page.get("title", "")
        if not char or char in seen_titles:
            continue
        
        # Skip obviously invalid titles
        if not re.match(r"^[A-Za-z]", char):
            continue
        
        if char in processed_set:
            continue
        
        seen_titles.add(char)
        safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", char.lower())
        output_path = os.path.join(output_dir, f"{safe_name}.json")
        
        try:
            success = convert_from_json(json_path, char, output_path)
            if not success:
                raise RuntimeError("Extraction returned False")
            valid, msg = validate_output(output_path)
            if not valid:
                # Check if it's a stub (filtered out) vs real validation failure
                if "Stub character" in msg:
                    # Remove the file and skip silently
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    print(f"[SKIP] {char} (minimal content - not useful for questions)")
                else:
                    raise RuntimeError(f"Validation failed: {msg}")
            else:
                checkpoint["processed"].append(char)
                processed_set.add(char)
                processed_count += 1
                print(f"[OK] {char}")
        except Exception as e:
            err = traceback.format_exc()
            checkpoint["failed"][char] = err
            print(f"[FAIL] {char}: {e}")
        finally:
            save_checkpoint(output_dir, checkpoint)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk extract characters from extracted_data.json")
    # CLI
    parser.add_argument("json_path", help="Path to extracted_data.json")
    parser.add_argument("output_dir", help="Directory to save character JSON files")
    parser.add_argument("--start-after", help="Character name to start after (resume)")
    parser.add_argument("--limit", type=int, help="Limit number of characters to process")
    args = parser.parse_args()

    bulk_extract(args.json_path, args.output_dir, start_after=args.start_after, limit=args.limit)
