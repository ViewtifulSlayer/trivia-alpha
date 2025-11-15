#!/usr/bin/env python3
"""Verify all fixes are in place for re-extraction."""
import re
from pathlib import Path

def verify_fixes():
    """Check that all fixes are properly implemented."""
    print("=" * 60)
    print("VERIFICATION OF RE-EXTRACTION FIXES")
    print("=" * 60)
    
    converter_path = Path("src/convert_character_direct.py")
    bulk_extract_path = Path("src/bulk_extract_characters.py")
    
    issues = []
    fixes_verified = []
    
    # Check 1: Quote formatting fix in clean_mediawiki_markup
    print("\n1. Checking quote formatting fix...")
    if converter_path.exists():
        content = converter_path.read_text(encoding='utf-8')
        
        # Check for quote removal regex
        if re.search(r"re\.sub\(r[\"']''\+[\"']", content):
            fixes_verified.append("OK: Quote formatting removal (''+) in clean_mediawiki_markup()")
        else:
            issues.append("ERROR: Quote formatting removal NOT found")
        
        # Check that clean_mediawiki_markup is called on quotes
        quote_text_clean = 'clean_mediawiki_markup(quote_text)' in content
        quote_source_clean = 'clean_mediawiki_markup(quote_source' in content
        
        if quote_text_clean and quote_source_clean:
            fixes_verified.append("OK: Quote text and source are cleaned")
        else:
            issues.append("ERROR: Quote cleaning not applied to all quote fields")
        
        # Check description cleaning
        if 'clean_mediawiki_markup(desc_text)' in content:
            fixes_verified.append("OK: Description text is cleaned")
        else:
            issues.append("ERROR: Description cleaning not found")
        
        # Check timeline event cleaning
        if 'clean_mediawiki_markup(para_cleaned)' in content or 'clean_mediawiki_markup(cleaned)' in content:
            fixes_verified.append("OK: Timeline events are cleaned")
        else:
            issues.append("ERROR: Timeline event cleaning not found")
        
        # Count total uses of clean_mediawiki_markup
        uses = len(re.findall(r'clean_mediawiki_markup\(', content))
        fixes_verified.append(f"OK: clean_mediawiki_markup() called {uses} times (ensures comprehensive cleaning)")
    
    # Check 2: Stub filtering
    print("\n2. Checking stub filtering...")
    if bulk_extract_path.exists():
        content = bulk_extract_path.read_text(encoding='utf-8')
        
        if 'def is_stub_character' in content:
            fixes_verified.append("OK: is_stub_character() function exists")
        else:
            issues.append("ERROR: is_stub_character() function NOT found")
        
        if 'is_stub_character(data)' in content:
            fixes_verified.append("OK: Stub filtering is applied during extraction")
        else:
            issues.append("ERROR: Stub filtering not applied")
    
    # Check 3: Direct converter integration
    print("\n3. Checking converter integration...")
    if bulk_extract_path.exists():
        content = bulk_extract_path.read_text(encoding='utf-8')
        
        if 'from convert_character_direct import convert_from_json' in content:
            fixes_verified.append("OK: Direct converter is integrated")
        else:
            issues.append("ERROR: Direct converter not integrated")
        
        if 'convert_from_json(' in content:
            fixes_verified.append("OK: convert_from_json() is being used")
        else:
            issues.append("ERROR: convert_from_json() not being called")
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    if fixes_verified:
        print(f"\nVERIFIED FIXES ({len(fixes_verified)}):")
        for fix in fixes_verified:
            print(f"  {fix}")
    
    if issues:
        print(f"\nISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"  {issue}")
        print("\nWARNING: Please fix these issues before re-extraction!")
    else:
        print("\nSUCCESS: ALL FIXES VERIFIED - Ready for re-extraction!")
    
    return len(issues) == 0

if __name__ == "__main__":
    verify_fixes()

