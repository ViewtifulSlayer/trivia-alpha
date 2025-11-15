#!/usr/bin/env python3
"""Check what types of questions are unverified."""
import json

with open('data/questions_from_616_characters.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

unverified = [q for q in data if not q.get('verified', True)]

# Categorize by type and source
categories = {}
for q in unverified:
    q_type = q.get('type', 'unknown')
    source = q.get('source', 'unknown')
    key = f"{q_type}/{source}"
    categories[key] = categories.get(key, 0) + 1

print("Unverified questions by type/source:")
for key, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    print(f"  {key}: {count}")

# Check "which series" questions
series_q = [q for q in unverified if q.get('type') == 'which' and 'series' in q.get('question', '').lower()]
print(f"\n'Which series' questions: {len(series_q)}")
if series_q:
    print(f"\nSample:")
    print(f"  Q: {series_q[0].get('question')}")
    print(f"  A: {series_q[0].get('answer')}")
    print(f"  Source: {series_q[0].get('source')}")

# Check family questions
family_q = [q for q in unverified if q.get('source') == 'family']
print(f"\nFamily questions: {len(family_q)}")
if family_q:
    print(f"\nSample:")
    print(f"  Q: {family_q[0].get('question')}")
    print(f"  A: {family_q[0].get('answer')}")
    print(f"  Type: {family_q[0].get('type')}")

