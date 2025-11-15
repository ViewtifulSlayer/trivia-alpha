#!/usr/bin/env python3
"""Show questions for user review and correction."""
import json
import sys

questions_file = "data/questions_for_correction.json"

with open(questions_file, "r", encoding="utf-8") as f:
    questions = json.load(f)

print(f"Total questions: {len(questions)}\n")
print("=" * 70)
print("QUESTIONS FOR REVIEW")
print("=" * 70)

# Show all "In which episode did..." questions first (these often need work)
print("\n\n'In which episode did...' questions (often need improvement):")
print("-" * 70)
episode_did_questions = [q for q in questions if q["question"].startswith("In which episode did")]
for i, q in enumerate(episode_did_questions[:15], 1):
    print(f"\n{i}. {q['question']}")
    print(f"   Answer: {q.get('answer', 'N/A')}")
    print(f"   Character: {q.get('character', 'N/A')}")
    print(f"   Source: {q.get('source', 'N/A')}")

# Show a sample of other question types
print("\n\n\nOther question types (sample):")
print("-" * 70)
other_questions = [q for q in questions if not q["question"].startswith("In which episode did")]
for i, q in enumerate(other_questions[:15], 1):
    print(f"\n{i}. {q['question']}")
    print(f"   Answer: {q.get('answer', 'N/A')}")
    print(f"   Type: {q.get('type', 'N/A')}, Source: {q.get('source', 'N/A')}")

print("\n\n" + "=" * 70)
print(f"Found {len(episode_did_questions)} 'In which episode did...' questions")
print(f"Found {len(other_questions)} other questions")
print("\nTo correct a question, use:")
print('  python src/learn_from_corrections.py "<original>" "<corrected>" [question_data.json]')

