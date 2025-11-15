#!/usr/bin/env python3
"""Check extraction progress and estimate total character count."""
import json
from pathlib import Path

def check_stats():
    # Check checkpoint
    checkpoint_path = Path("data/characters/bulk_extract_full_20251114/bulk_extraction_checkpoint.json")
    if checkpoint_path.exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            cp = json.load(f)
        processed = len(cp.get('processed', []))
        failed = len(cp.get('failed', {}))
        skipped = len(cp.get('skipped', []))
        print(f"Current Extraction Progress:")
        print(f"  Processed: {processed}")
        print(f"  Failed: {failed}")
        print(f"  Skipped (stubs): {skipped}")
        print(f"  Total attempted: {processed + failed + skipped}")
    
    # Count actual files
    extract_dir = Path("data/characters/bulk_extract_full_20251114")
    if extract_dir.exists():
        json_files = [f for f in extract_dir.glob("*.json") if f.name != "bulk_extraction_checkpoint.json"]
        print(f"\nActual character files extracted: {len(json_files)}")
    
    # Estimate total from extracted_data.json
    data_path = Path("data/extracted/extracted_data.json")
    if data_path.exists():
        print(f"\nAnalyzing extracted_data.json...")
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pages = data.get('pages', [])
        print(f"  Total pages in dataset: {len(pages)}")
        
        # Count character pages using same logic as bulk_extract_characters
        character_count = 0
        for page in pages:
            title = page.get("title", "")
            text = page.get("full_text", "")
            text_lower = text.lower()
            
            # Skip obviously non-character pages
            if not title or len(title) > 100:
                continue
            
            # Exclude list/organization pages
            exclude_patterns = [
                " members", " list", " category:", " template:",
                " episode", " novel", " comic", " book", " song",
                " organization", " alliance", " empire", " federation",
                " species", " race", " planet", " starship", " class",
            ]
            title_lower = title.lower()
            if any(pattern in title_lower for pattern in exclude_patterns):
                continue
            
            # Check for character sidebar template
            character_templates = [
                "{{sidebar individual",
                "{{sidebar character",
                "{{infobox person",
            ]
            has_character_template = any(template in text_lower for template in character_templates)
            
            if not has_character_template:
                continue
            
            # Check for character-specific fields
            sidebar_indicators = [
                "|actor", "|played by", "|portrayed by",
                "|species", "|affiliation", "|rank",
            ]
            has_sidebar_fields = any(indicator in text_lower[:5000] for indicator in sidebar_indicators)
            
            if has_sidebar_fields:
                character_count += 1
        
        print(f"\nEstimated total character pages: {character_count}")
        
        if checkpoint_path.exists():
            remaining = character_count - (processed + failed + skipped)
            print(f"  Remaining to process: {remaining}")
            if processed + failed + skipped > 0:
                progress = ((processed + failed + skipped) / character_count) * 100
                print(f"  Progress: {progress:.1f}%")

if __name__ == "__main__":
    check_stats()

