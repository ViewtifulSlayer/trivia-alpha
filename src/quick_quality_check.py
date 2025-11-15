#!/usr/bin/env python3
"""Quick quality check of questions for MVP readiness."""
import json
import random

with open('data/questions_from_616_characters.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

print("=" * 70)
print("QUICK QUALITY CHECK FOR MVP")
print("=" * 70)
print(f"\nTotal questions: {len(questions):,}")
print(f"Verified: {sum(1 for q in questions if q.get('verified', False)):,} ({100*sum(1 for q in questions if q.get('verified', False))/len(questions):.1f}%)")

# Sample random questions
sample = random.sample(questions, min(20, len(questions)))

print("\n" + "=" * 70)
print("RANDOM SAMPLE (20 questions)")
print("=" * 70)

issues = []
for i, q in enumerate(sample, 1):
    question = q.get('question', '')
    answer = q.get('answer', '')
    char = q.get('character', '')
    qtype = q.get('type', '')
    
    # Check for common issues
    issue_flags = []
    if 'In which episode did' in question and question.endswith('?'):
        if not answer or len(answer) < 3:
            issue_flags.append("INCOMPLETE")
    if char and char.lower() in question.lower() and qtype == 'what':
        if 'happened to' in question.lower():
            pass  # This is okay
        else:
            issue_flags.append("REDUNDANT_NAME")
    if len(question.split()) < 5:
        issue_flags.append("TOO_SHORT")
    if not answer or len(answer) < 2:
        issue_flags.append("NO_ANSWER")
    
    status = "OK" if not issue_flags else "ISSUE"
    if issue_flags:
        issues.append((i, issue_flags))
    
    print(f"\n[{status}] {i}. {question}")
    print(f"   Answer: {answer}")
    print(f"   Character: {char} | Type: {qtype} | Source: {q.get('source', 'unknown')}")
    if issue_flags:
        print(f"   Issues: {', '.join(issue_flags)}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Questions with potential issues: {len(issues)}/{len(sample)} ({100*len(issues)/len(sample):.1f}%)")

if len(issues) <= 2:
    print("\n[PASS] QUALITY: EXCELLENT - Ready for MVP")
elif len(issues) <= 5:
    print("\n[WARN] QUALITY: GOOD - Minor issues, acceptable for MVP")
else:
    print("\n[FAIL] QUALITY: NEEDS WORK - Consider pattern integration first")

