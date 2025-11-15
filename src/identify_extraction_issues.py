#!/usr/bin/env python3
"""Identify remaining extraction issues before re-extraction."""
import json
import re
from pathlib import Path
from collections import defaultdict

def find_formatting_issues():
    """Find MediaWiki formatting artifacts in extracted data."""
    extract_dir = Path("data/characters/bulk_extract_full_20251114")
    json_files = [f for f in extract_dir.glob("*.json") if f.name != "bulk_extraction_checkpoint.json"]
    
    issues = {
        'quote_text': [],
        'quote_source': [],
        'description': [],
        'timeline_events': [],
        'character_name': [],
        'other_fields': []
    }
    
    formatting_patterns = {
        'triple_quotes': re.compile(r"'''"),
        'double_quotes': re.compile(r"''"),
        'brackets': re.compile(r'\[\[([^\]]+)\]\]'),
        'templates': re.compile(r'\{\{[^}]+\}\}'),
        'html_tags': re.compile(r'<[^>]+>'),
    }
    
    print(f"Scanning {len(json_files)} character files for formatting issues...\n")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            char = data.get('character', {})
            char_name = char.get('name', 'Unknown')
            
            # Check quote
            quote = char.get('quote')
            if quote and isinstance(quote, dict):
                quote_text = quote.get('text', '')
                quote_source = quote.get('source', '')
                
                for pattern_name, pattern in formatting_patterns.items():
                    if pattern.search(quote_text):
                        issues['quote_text'].append({
                            'character': char_name,
                            'issue': pattern_name,
                            'text': quote_text[:150]
                        })
                    if pattern.search(quote_source):
                        issues['quote_source'].append({
                            'character': char_name,
                            'issue': pattern_name,
                            'text': quote_source[:150]
                        })
            
            # Check description
            description = char.get('description', '')
            if description:
                for pattern_name, pattern in formatting_patterns.items():
                    if pattern.search(description):
                        issues['description'].append({
                            'character': char_name,
                            'issue': pattern_name,
                            'text': description[:150]
                        })
                        break  # Only report once per description
            
            # Check timeline events
            timeline_sections = {k: v for k, v in data.items() if k not in ['character', 'appearances']}
            for section_name, events in timeline_sections.items():
                if isinstance(events, list):
                    for event in events:
                        for field in ['event', 'background', 'relationship']:
                            text = event.get(field, '')
                            if text:
                                for pattern_name, pattern in formatting_patterns.items():
                                    if pattern.search(text):
                                        issues['timeline_events'].append({
                                            'character': char_name,
                                            'section': section_name,
                                            'issue': pattern_name,
                                            'text': text[:150]
                                        })
                                        break
            
            # Check character name for issues
            name = char.get('name', '')
            if name:
                for pattern_name, pattern in formatting_patterns.items():
                    if pattern.search(name):
                        issues['character_name'].append({
                            'character': char_name,
                            'issue': pattern_name
                        })
            
            # Check other character fields
            for field in ['species', 'rank', 'occupation', 'father', 'mother']:
                value = char.get(field)
                if value and isinstance(value, str):
                    for pattern_name, pattern in formatting_patterns.items():
                        if pattern.search(value):
                            issues['other_fields'].append({
                                'character': char_name,
                                'field': field,
                                'issue': pattern_name,
                                'text': value[:100]
                            })
                            break
        
        except Exception as e:
            continue
    
    # Print summary
    print("=" * 60)
    print("EXTRACTION ISSUES SUMMARY")
    print("=" * 60)
    
    total_issues = sum(len(v) for v in issues.values())
    print(f"\nTotal formatting issues found: {total_issues}")
    
    print(f"\nBy Category:")
    for category, issue_list in issues.items():
        if issue_list:
            print(f"  {category}: {len(issue_list)} issues")
            
            # Show unique characters affected
            unique_chars = len(set(i['character'] for i in issue_list))
            print(f"    ({unique_chars} unique characters affected)")
            
            # Show sample issues
            if len(issue_list) <= 5:
                print(f"    Samples:")
                for issue in issue_list[:3]:
                    print(f"      - {issue['character']}: {issue['issue']}")
            else:
                print(f"    Top 3 samples:")
                for issue in issue_list[:3]:
                    print(f"      - {issue['character']}: {issue['issue']}")
                    if 'text' in issue:
                        print(f"        Text: {issue['text'][:80]}...")
    
    # Recommendations
    print(f"\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    if issues['quote_text'] or issues['quote_source']:
        print("OK: Quote formatting fix already applied - will be cleaned in re-extraction")
    
    if issues['description']:
        desc_count = len(issues['description'])
        print(f"WARNING: {desc_count} descriptions have formatting issues")
        print("   Recommendation: Description cleaning is already in clean_mediawiki_markup()")
        print("   May need to verify it's being applied correctly")
    
    if issues['timeline_events']:
        timeline_count = len(issues['timeline_events'])
        print(f"WARNING: {timeline_count} timeline events have formatting issues (MOST COMMON)")
        print("   Recommendation: Timeline events are cleaned, but may need additional passes")
        print("   Check if clean_mediawiki_markup() is removing all formatting correctly")
    
    if issues['character_name']:
        print(f"WARNING: {len(issues['character_name'])} character names have formatting issues")
        print("   Recommendation: Character names should be cleaned during extraction")
    
    if issues['other_fields']:
        other_count = len(issues['other_fields'])
        print(f"WARNING: {other_count} other character fields have formatting issues")
        print("   Recommendation: All character fields should use clean_mediawiki_markup()")
    
    if total_issues == 0:
        print("SUCCESS: No formatting issues found! Data is clean.")

if __name__ == "__main__":
    find_formatting_issues()

