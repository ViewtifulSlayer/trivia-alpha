#!/usr/bin/env python3
"""
Apply learned patterns to improve question generation.
This uses the corrections library to generate better questions.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from learn_from_corrections import load_corrections

def find_matching_pattern(question_data: Dict, corrections: List[Dict]) -> Optional[Dict]:
    """
    Find a matching learned pattern for a question.
    """
    question_type = question_data.get('type', '')
    source = question_data.get('source', '')
    
    # Look for patterns that match question type and source
    for correction in corrections:
        if (correction.get('question_type') == question_type and 
            correction.get('source') == source):
            
            # Check if the original template matches the current question structure
            original_template = correction.get('original_template', '')
            
            # Simple check: does the question have similar structure?
            # For now, we'll match by checking if it's the same question type/source
            # and has similar keywords
            
            # Check for specific patterns like "fondness"
            if 'fondness' in original_template.lower():
                # Check if current question also has "fondness" or similar incomplete action
                current_q = question_data.get('question', '').lower()
                if 'fondness' in current_q or ('have' in current_q and 'particular' in current_q):
                    return correction
    
    return None


def extract_item_from_event_text(event_text: str, pattern_type: str) -> Optional[str]:
    """
    Extract the contextual item from event text based on pattern type.
    """
    patterns = {
        'fondness_for': r'fondness for ([^,\.]+)',
        'preference_for': r'preference for ([^,\.]+)',
        'interest_in': r'interest in ([^,\.]+)',
        'liking_for': r'liking for ([^,\.]+)',
    }
    
    pattern = patterns.get(pattern_type)
    if not pattern:
        return None
    
    match = re.search(pattern, event_text, re.I)
    if match:
        item = match.group(1).strip()
        # Clean up common trailing words
        item = re.sub(r'\s+(though|although|but|and|or).*$', '', item, flags=re.I)
        return item
    
    return None


def apply_pattern_to_question(question_data: Dict, pattern: Dict, event_text: str) -> Optional[str]:
    """
    Apply a learned pattern to generate a corrected question.
    """
    template = pattern.get('generalized_template', '')
    if not template:
        return None
    
    # Extract contextual item from event text
    item_pattern = pattern.get('item_pattern')
    contextual_item = None
    
    if item_pattern:
        contextual_item = extract_item_from_event_text(event_text, item_pattern)
    
    # Fill in the template
    character = question_data.get('character', '')
    series = question_data.get('series', '')
    episode = question_data.get('episode', '')
    
    corrected = template
    
    # Replace placeholders
    corrected = corrected.replace('{character}', character)
    corrected = corrected.replace('{series}', series)
    corrected = corrected.replace('{episode}', episode)
    
    if contextual_item:
        corrected = corrected.replace('{item}', contextual_item)
    else:
        # If we can't extract the item, the template won't work
        return None
    
    return corrected


def improve_questions_with_patterns(questions_file: str, characters_dir: str, 
                                   output_file: str = None):
    """
    Apply learned patterns to improve questions in a file.
    """
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    corrections = load_corrections()
    
    if not corrections:
        print("No corrections found. Please provide some corrections first.")
        return
    
    print(f"Loaded {len(corrections)} learned patterns")
    print(f"Processing {len(questions)} questions...\n")
    
    improved_count = 0
    
    for q in questions:
        # Try to find a matching pattern
        pattern = find_matching_pattern(q, corrections)
        
        if pattern:
            # We'd need the event text to extract the contextual item
            # For now, we'll just mark it for manual review
            print(f"Found pattern match for: {q.get('question', '')[:60]}...")
            print(f"  Pattern: {pattern.get('generalized_template', '')}")
            print(f"  Note: Requires event text to extract contextual item")
            improved_count += 1
    
    print(f"\nFound {improved_count} questions that could be improved with learned patterns")
    print("Note: To fully apply patterns, we need access to the original event text from character JSON files.")


if __name__ == "__main__":
    import sys
    questions_file = sys.argv[1] if len(sys.argv) > 1 else "data/questions_mvp_improved.json"
    characters_dir = sys.argv[2] if len(sys.argv) > 2 else "data/characters/bulk_extract_full_20251114-083000"
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    improve_questions_with_patterns(questions_file, characters_dir, output_file)

