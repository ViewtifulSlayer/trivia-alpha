#!/usr/bin/env python3
"""Comprehensive analysis of extracted character files."""
import json
from pathlib import Path
from collections import defaultdict, Counter
import re

def analyze_extracted_characters():
    """Analyze all extracted character files for quality and patterns."""
    extract_dir = Path("data/characters/bulk_extract_full_20251114")
    
    if not extract_dir.exists():
        print("Extraction directory not found")
        return
    
    json_files = [f for f in extract_dir.glob("*.json") if f.name != "bulk_extraction_checkpoint.json"]
    print(f"Analyzing {len(json_files)} character files...\n")
    
    stats = {
        'total': len(json_files),
        'with_quotes': 0,
        'with_family': 0,
        'with_appearances': 0,
        'with_timeline': 0,
        'quote_issues': [],
        'formatting_issues': [],
        'missing_fields': defaultdict(int),
        'timeline_sections': Counter(),
        'appearance_counts': Counter(),
        'series_distribution': Counter(),
        'richness_distribution': {'RICH': 0, 'GOOD': 0, 'MINIMAL': 0, 'STUB': 0}
    }
    
    # Check for MediaWiki formatting artifacts
    formatting_patterns = {
        "triple_quotes": re.compile(r"'''"),
        "double_quotes": re.compile(r"''"),
        "brackets": re.compile(r'\[\[([^\]]+)\]\]'),
        "templates": re.compile(r'\{\{[^}]+\}\}'),
    }
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            char = data.get('character', {})
            char_name = char.get('name', 'Unknown')
            
            # Check quote quality
            quote = char.get('quote')
            if quote and isinstance(quote, dict):
                stats['with_quotes'] += 1
                quote_text = quote.get('text', '')
                quote_source = quote.get('source', '')
                
                # Check for formatting issues
                for pattern_name, pattern in formatting_patterns.items():
                    if pattern.search(quote_text) or pattern.search(quote_source):
                        stats['quote_issues'].append({
                            'character': char_name,
                            'issue': f'{pattern_name} in quote',
                            'text': quote_text[:100],
                            'source': quote_source[:100]
                        })
            
            # Check family relationships
            has_family = any(char.get(f) for f in ['father', 'mother', 'spouses', 'children', 'siblings'])
            if has_family:
                stats['with_family'] += 1
            
            # Check appearances
            appearances = data.get('appearances', {})
            if appearances:
                total_appearances = sum(len(eps) for eps in appearances.values() if isinstance(eps, list))
                if total_appearances > 0:
                    stats['with_appearances'] += 1
                    stats['appearance_counts'][total_appearances] += 1
                    for series, eps in appearances.items():
                        if eps:
                            stats['series_distribution'][series] += len(eps)
            
            # Check timeline sections
            timeline_sections = {k: v for k, v in data.items() if k not in ['character', 'appearances']}
            if timeline_sections:
                stats['with_timeline'] += 1
                for section_name, events in timeline_sections.items():
                    if isinstance(events, list) and events:
                        stats['timeline_sections'][section_name] += len(events)
            
            # Categorize richness
            timeline_count = sum(len(v) if isinstance(v, list) else 0 for v in timeline_sections.values())
            appearance_count = sum(len(eps) for eps in appearances.values() if isinstance(eps, list))
            has_quote = bool(quote)
            has_family_data = has_family
            
            if timeline_count >= 10 and appearance_count >= 5:
                stats['richness_distribution']['RICH'] += 1
            elif timeline_count >= 5 or appearance_count >= 3:
                stats['richness_distribution']['GOOD'] += 1
            elif timeline_count > 0 or appearance_count > 0:
                stats['richness_distribution']['MINIMAL'] += 1
            else:
                stats['richness_distribution']['STUB'] += 1
            
            # Check for missing common fields
            if not char.get('species'):
                stats['missing_fields']['species'] += 1
            if not char.get('rank') and not char.get('occupation'):
                stats['missing_fields']['rank_or_occupation'] += 1
            if not char.get('played_by'):
                stats['missing_fields']['played_by'] += 1
            
            # Check for formatting issues in character name or description
            description = char.get('description', '')
            if description:
                for pattern_name, pattern in formatting_patterns.items():
                    if pattern.search(description):
                        stats['formatting_issues'].append({
                            'character': char_name,
                            'issue': f'{pattern_name} in description',
                            'text': description[:100]
                        })
        
        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")
            continue
    
    # Print results
    print("=" * 60)
    print("EXTRACTION QUALITY ANALYSIS")
    print("=" * 60)
    
    print(f"\nTotal Characters: {stats['total']}")
    print(f"\nData Completeness:")
    print(f"  With quotes: {stats['with_quotes']} ({stats['with_quotes']/stats['total']*100:.1f}%)")
    print(f"  With family data: {stats['with_family']} ({stats['with_family']/stats['total']*100:.1f}%)")
    print(f"  With appearances: {stats['with_appearances']} ({stats['with_appearances']/stats['total']*100:.1f}%)")
    print(f"  With timeline events: {stats['with_timeline']} ({stats['with_timeline']/stats['total']*100:.1f}%)")
    
    print(f"\nRichness Distribution:")
    for level, count in stats['richness_distribution'].items():
        print(f"  {level}: {count} ({count/stats['total']*100:.1f}%)")
    
    print(f"\nMissing Fields:")
    for field, count in sorted(stats['missing_fields'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {field}: {count} ({count/stats['total']*100:.1f}%)")
    
    print(f"\nTop Timeline Sections (by event count):")
    for section, count in stats['timeline_sections'].most_common(10):
        print(f"  {section}: {count} events")
    
    print(f"\nSeries Distribution (total appearances):")
    for series, count in sorted(stats['series_distribution'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {series}: {count} appearances")
    
    print(f"\nAppearance Count Distribution:")
    for count_range, char_count in sorted(stats['appearance_counts'].items())[:20]:
        print(f"  {count_range} appearances: {char_count} characters")
    
    if stats['quote_issues']:
        print(f"\nQuote Formatting Issues: {len(stats['quote_issues'])}")
        print("Sample issues:")
        for issue in stats['quote_issues'][:10]:
            print(f"  {issue['character']}: {issue['issue']}")
            print(f"    Text: {issue['text']}")
            print(f"    Source: {issue['source']}")
    
    if stats['formatting_issues']:
        print(f"\nOther Formatting Issues: {len(stats['formatting_issues'])}")
        print("Sample issues:")
        for issue in stats['formatting_issues'][:10]:
            print(f"  {issue['character']}: {issue['issue']}")
    
    # Summary recommendations
    print(f"\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    quote_issue_pct = (len(stats['quote_issues']) / stats['with_quotes'] * 100) if stats['with_quotes'] > 0 else 0
    if quote_issue_pct > 10:
        print(f"WARNING: {quote_issue_pct:.1f}% of quotes have formatting issues - MediaWiki cleanup needed")
    
    stub_pct = (stats['richness_distribution']['STUB'] / stats['total'] * 100)
    if stub_pct > 5:
        print(f"WARNING: {stub_pct:.1f}% are stubs - consider filtering these out")
    
    missing_species_pct = (stats['missing_fields']['species'] / stats['total'] * 100)
    if missing_species_pct > 20:
        print(f"INFO: {missing_species_pct:.1f}% missing species - may be normal for some characters")
    
    rich_good_count = stats['richness_distribution']['RICH'] + stats['richness_distribution']['GOOD']
    rich_good_pct = (rich_good_count / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"\nSUCCESS: {rich_good_count} characters ({rich_good_pct:.1f}%) are RICH or GOOD quality")

if __name__ == "__main__":
    analyze_extracted_characters()

