#!/usr/bin/env python3
"""Analyze question quality issues."""
import json
import re
from collections import Counter

def analyze_questions(questions_file):
    """Analyze questions for quality issues."""
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    print(f"Analyzing {len(questions)} questions...\n")
    print("=" * 60)
    
    issues = {
        'redundant_character_name': [],
        'broken_grammar': [],
        'truncated_mid_sentence': [],
        'awkward_verb_tense': [],
        'nonsensical_phrases': []
    }
    
    # Patterns to detect issues
    for q in questions:
        question = q.get('question', '')
        char_name = q.get('character', '')
        
        if not question or not char_name:
            continue
        
        # Issue 1: Redundant character name in question text
        # "In which episode did Alynna Nechayev nechayev had..."
        char_lower = char_name.lower()
        # Check if character name appears after "did [character]"
        pattern = rf"did {re.escape(char_name)} {re.escape(char_lower)}"
        if re.search(pattern, question, re.I):
            issues['redundant_character_name'].append({
                'question': question,
                'character': char_name
            })
        
        # Issue 2: Broken grammar - "did [character] [past_tense_verb]"
        # "did Alynna Nechayev had" or "did Alynna Nechayev was"
        broken_patterns = [
            rf"did {re.escape(char_name)} (had|was|were|did|went|came|said|told)",
            rf"did {re.escape(char_name)} (in \d{{4}}|in \d{{3}})",
        ]
        for pattern in broken_patterns:
            if re.search(pattern, question, re.I):
                issues['broken_grammar'].append({
                    'question': question,
                    'character': char_name
                })
                break
        
        # Issue 3: Truncated mid-sentence with "...?"
        if question.endswith('...?'):
            issues['truncated_mid_sentence'].append({
                'question': question,
                'character': char_name
            })
        
        # Issue 4: Awkward verb tense - "did [character] [verb]ed"
        # "did Alynna Nechayev transported" should be "did Alynna Nechayev transport"
        awkward_pattern = rf"did {re.escape(char_name)} (\w+ed|\w+ing) (?!her|him|them|it|the|a|an)"
        if re.search(awkward_pattern, question, re.I):
            issues['awkward_verb_tense'].append({
                'question': question,
                'character': char_name
            })
        
        # Issue 5: Nonsensical phrases - check for common bad patterns
        nonsensical_patterns = [
            r"thumb\|",  # MediaWiki artifacts
            r"thumb\s*\|",  # More artifacts
            r"\[\[.*?\]\]",  # Unprocessed links
            rf"{re.escape(char_name)}\s+{re.escape(char_name.lower())}",  # Name repetition
        ]
        for pattern in nonsensical_patterns:
            if re.search(pattern, question, re.I):
                issues['nonsensical_phrases'].append({
                    'question': question,
                    'character': char_name,
                    'pattern': pattern
                })
                break
    
    # Print results
    print("QUALITY ISSUES FOUND:\n")
    
    total_issues = sum(len(v) for v in issues.values())
    print(f"Total questions with issues: {total_issues}")
    print(f"Percentage: {total_issues/len(questions)*100:.1f}%\n")
    
    for issue_type, issue_list in issues.items():
        if issue_list:
            print(f"{issue_type.replace('_', ' ').title()}: {len(issue_list)}")
            print("  Sample issues:")
            for issue in issue_list[:5]:
                print(f"    - {issue['question'][:100]}...")
            print()
    
    # Analyze by question type
    print("\nIssues by Question Type:")
    type_issues = Counter()
    for issue_type, issue_list in issues.items():
        for issue in issue_list:
            # Try to find the question in the list to get its type
            for q in questions:
                if q.get('question') == issue['question']:
                    type_issues[q.get('type', 'unknown')] += 1
                    break
    
    for qtype, count in type_issues.most_common():
        print(f"  {qtype}: {count} issues")
    
    # Analyze by source
    print("\nIssues by Source:")
    source_issues = Counter()
    for issue_type, issue_list in issues.items():
        for issue in issue_list:
            for q in questions:
                if q.get('question') == issue['question']:
                    source_issues[q.get('source', 'unknown')] += 1
                    break
    
    for source, count in source_issues.most_common():
        print(f"  {source}: {count} issues")
    
    return issues

if __name__ == "__main__":
    import sys
    questions_file = sys.argv[1] if len(sys.argv) > 1 else "data/questions_mvp.json"
    analyze_questions(questions_file)

