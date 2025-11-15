#!/usr/bin/env python3
"""Analyze unverified questions to understand why they failed verification."""
import json
import sys

questions_file = sys.argv[1] if len(sys.argv) > 1 else 'data/questions_from_616_characters.json'

with open(questions_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

unverified = [q for q in data if not q.get('verified', True)]
verified = [q for q in data if q.get('verified', True)]

print(f"Total questions: {len(data)}")
print(f"Verified: {len(verified)} ({len(verified)/len(data)*100:.1f}%)")
print(f"Unverified: {len(unverified)} ({len(unverified)/len(data)*100:.1f}%)")
print()

# Analyze verification notes
notes = {}
for q in unverified:
    note = q.get('verification_notes', 'Unknown')
    # Handle if note is a list
    if isinstance(note, list):
        note = ', '.join(str(n) for n in note) if note else 'Unknown'
    note_str = str(note)
    notes[note_str] = notes.get(note_str, 0) + 1

print("=" * 70)
print("VERIFICATION NOTES (Top 15)")
print("=" * 70)
for note, count in sorted(notes.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"{count:4} - {note}")

print()
print("=" * 70)
print("SAMPLE UNVERIFIED QUESTIONS (First 30)")
print("=" * 70)
for i, q in enumerate(unverified[:30], 1):
    q_type = q.get('type', 'unknown')
    question = q.get('question', '')[:100]
    answer = q.get('answer', '')[:60]
    note = q.get('verification_notes', 'No note')
    print(f"\n{i}. [{q_type}] {question}")
    print(f"   Answer: {answer}")
    print(f"   Note: {note}")

