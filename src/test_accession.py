#!/usr/bin/env python3
"""Test episode question generation with Accession and Time's Orphan episodes."""

import json
from episode_question_generator import is_episode_page, generate_episode_questions

# Load data
data = json.load(open('../data/extracted/extracted_data.json', 'r', encoding='utf-8'))
pages = data['pages']

# Find Time's Orphan episode
times_orphan = [p for p in pages if 'time' in p.get('title', '').lower() and 'orphan' in p.get('title', '').lower()]
print("Searching for 'Time's Orphan' episode:")
for p in times_orphan:
    print(f"  - {p['title']} (Series: {p.get('series', [])})")

if times_orphan:
    ep = times_orphan[0]
    print(f"\n{'='*60}")
    print(f"Testing: {ep['title']}")
    print(f"{'='*60}")
    print(f"Is episode page: {is_episode_page(ep)}")
    print(f"Series: {ep.get('series', [])}")
    
    # Show episode description (first 1000 chars)
    content = ep.get('full_text', '')
    print(f"\nEpisode content (first 1000 chars):")
    print(content[:1000])
    print("...")
    
    # Generate questions
    questions = generate_episode_questions(ep, 10)
    print(f"\n{'='*60}")
    print(f"Generated {len(questions)} questions:")
    print(f"{'='*60}")
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. {q['question']}")
        print(f"   Answer: {q['answer']}")
        print(f"   Type: {q.get('fact_type', 'unknown')}")
        print(f"   Source: {q.get('source_page', 'N/A')}")

# Also test Accession
print(f"\n\n{'='*60}")
print("Testing: Accession (episode)")
print(f"{'='*60}")
accession = [p for p in pages if 'accession' in p.get('title', '').lower() and 'episode' in p.get('title', '').lower()]
if accession:
    ep = accession[0]
    print(f"Episode: {ep['title']}")
    print(f"Series: {ep.get('series', [])}")
    print(f"Is episode page: {is_episode_page(ep)}")
    
    # Show content
    content = ep.get('full_text', '')
    print(f"\nEpisode content (first 1500 chars):")
    print(content[:1500])
    print("...")
    
    # Generate questions
    questions = generate_episode_questions(ep, 10)
    print(f"\nGenerated {len(questions)} questions:")
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. {q['question']}")
        print(f"   Answer: {q['answer']}")
        print(f"   Type: {q.get('fact_type', 'unknown')}")
