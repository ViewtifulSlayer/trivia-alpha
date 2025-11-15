#!/usr/bin/env python3
"""Analyze quality of generated questions."""
import json
from pathlib import Path
from collections import Counter

def analyze_questions(questions_file):
    """Analyze question quality and identify issues."""
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    print(f"Analyzing {len(questions)} questions...\n")
    print("=" * 60)
    
    # Basic stats
    verified = [q for q in questions if q.get('verified', False)]
    unverified = [q for q in questions if not q.get('verified', False)]
    
    print(f"Verified: {len(verified)} ({len(verified)/len(questions)*100:.1f}%)")
    print(f"Unverified: {len(unverified)} ({len(unverified)/len(questions)*100:.1f}%)")
    
    # By source type
    print(f"\nBy Source Type:")
    source_counts = Counter(q.get('source', 'unknown') for q in questions)
    for source, count in source_counts.most_common():
        verified_count = sum(1 for q in questions if q.get('source') == source and q.get('verified'))
        print(f"  {source}: {count} total ({verified_count} verified)")
    
    # By question type
    print(f"\nBy Question Type:")
    type_counts = Counter(q.get('type', 'unknown') for q in questions)
    for qtype, count in type_counts.most_common():
        print(f"  {qtype}: {count}")
    
    # By difficulty
    print(f"\nBy Difficulty:")
    diff_counts = Counter(q.get('difficulty', 'unknown') for q in questions)
    for diff, count in diff_counts.most_common():
        print(f"  {diff}: {count}")
    
    # Analyze unverified questions
    if unverified:
        print(f"\nUnverified Questions Analysis:")
        unverified_sources = Counter(q.get('source', 'unknown') for q in unverified)
        print("  By source:")
        for source, count in unverified_sources.most_common():
            print(f"    {source}: {count}")
        
        print(f"\n  Sample unverified questions:")
        for q in unverified[:10]:
            print(f"    Q: {q.get('question', '')[:80]}...")
            print(f"    A: {q.get('answer', '')}")
            print(f"    Source: {q.get('source')}, Type: {q.get('type')}")
            if q.get('verification_notes'):
                print(f"    Notes: {q.get('verification_notes')}")
            print()
    
    # Check for quality issues
    print(f"\nQuality Issues:")
    issues = {
        'empty_answers': [],
        'very_long_answers': [],
        'very_short_questions': [],
        'duplicate_questions': [],
    }
    
    question_texts = {}
    for q in questions:
        answer = q.get('answer', '')
        question = q.get('question', '')
        
        if not answer or answer.strip() == '':
            issues['empty_answers'].append(q)
        elif len(answer) > 200:
            issues['very_long_answers'].append(q)
        
        if len(question) < 10:
            issues['very_short_questions'].append(q)
        
        # Check for duplicates
        q_key = question.lower().strip()
        if q_key in question_texts:
            issues['duplicate_questions'].append((q, question_texts[q_key]))
        else:
            question_texts[q_key] = q
    
    print(f"  Empty answers: {len(issues['empty_answers'])}")
    print(f"  Very long answers (>200 chars): {len(issues['very_long_answers'])}")
    print(f"  Very short questions (<10 chars): {len(issues['very_short_questions'])}")
    print(f"  Duplicate questions: {len(issues['duplicate_questions'])}")
    
    # Sample quality questions
    print(f"\nSample High-Quality Questions (verified, various types):")
    high_quality = [q for q in verified if q.get('answer') and len(q.get('answer', '')) < 100]
    for q in high_quality[:10]:
        print(f"  Q: {q.get('question', '')}")
        print(f"  A: {q.get('answer', '')}")
        print(f"  ({q.get('type')}, {q.get('difficulty')}, {q.get('source')})")
        print()

if __name__ == "__main__":
    import sys
    questions_file = sys.argv[1] if len(sys.argv) > 1 else "data/questions_test_sample.json"
    analyze_questions(questions_file)

