#!/usr/bin/env python3
"""Clean up minimal/useless characters from extraction directory.
    
Removes characters that aren't useful for question generation:
- No timeline events (even if they have quotes, descriptions, or appearances)
- Only single appearance with no other content
- Very minimal content that won't generate good questions
"""
import os
import json
import argparse
from pathlib import Path


def is_minimal_character(data: dict) -> bool:
    """Check if character is minimal/useless for question generation.
    
    Returns True if character should be removed.
    """
    # Count timeline sections (everything except 'character' and 'appearances')
    timeline_sections = [k for k in data.keys() if k not in ['character', 'appearances']]
    
    # Count total timeline items
    timeline_items = 0
    for section in timeline_sections:
        if isinstance(data[section], list):
            timeline_items += len(data[section])
    
    # No timeline events = not useful for question generation
    if timeline_items == 0:
        return True
    
    # Count appearances
    appearances = data.get('appearances', {})
    appearance_count = sum(len(eps) for eps in appearances.values() if isinstance(eps, list))
    
    # Single appearance with minimal timeline (1-2 events) = probably not useful
    if appearance_count == 1 and timeline_items <= 2:
        return True
    
    return False


def cleanup_directory(directory: str, dry_run: bool = False):
    """Clean up minimal characters from directory."""
    directory = Path(directory)
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        return
    
    removed_count = 0
    kept_count = 0
    total_size_removed = 0
    
    json_files = list(directory.glob("*.json"))
    # Exclude checkpoint file
    json_files = [f for f in json_files if f.name != "bulk_extraction_checkpoint.json"]
    
    print(f"Scanning {len(json_files)} character files...")
    print()
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            char_name = data.get('character', {}).get('name', json_file.stem)
            
            if is_minimal_character(data):
                file_size = json_file.stat().st_size
                if dry_run:
                    print(f"[WOULD REMOVE] {char_name} ({json_file.name})")
                else:
                    json_file.unlink()
                    print(f"[REMOVED] {char_name} ({json_file.name})")
                removed_count += 1
                total_size_removed += file_size
            else:
                kept_count += 1
                if kept_count % 100 == 0:
                    print(f"Kept {kept_count} characters so far...")
        
        except Exception as e:
            print(f"[ERROR] Failed to process {json_file.name}: {e}")
    
    print()
    print("=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)
    if dry_run:
        print(f"[DRY RUN] Would remove: {removed_count} characters")
        print(f"[DRY RUN] Would keep: {kept_count} characters")
        print(f"[DRY RUN] Space that would be freed: {total_size_removed:,} bytes ({total_size_removed / 1024:.1f} KB)")
    else:
        print(f"Removed: {removed_count} characters")
        print(f"Kept: {kept_count} characters")
        print(f"Space freed: {total_size_removed:,} bytes ({total_size_removed / 1024:.1f} KB)")
    print(f"Total processed: {removed_count + kept_count} characters")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clean up minimal/useless characters from extraction directory"
    )
    parser.add_argument(
        "directory",
        help="Directory containing character JSON files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually deleting files"
    )
    args = parser.parse_args()
    
    cleanup_directory(args.directory, dry_run=args.dry_run)

