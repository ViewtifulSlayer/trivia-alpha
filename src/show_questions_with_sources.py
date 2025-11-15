#!/usr/bin/env python3
"""Show questions with their source character files and source data."""
import json
import os
import sys

questions_file = "data/questions_for_correction.json"
characters_dir = "data/characters/bulk_extract_full_20251114-083000"

with open(questions_file, "r", encoding="utf-8") as f:
    questions = json.load(f)

print(f"Total questions: {len(questions)}\n")
print("=" * 80)

# Group by character
by_character = {}
for q in questions:
    char = q.get("character", "Unknown")
    if char not in by_character:
        by_character[char] = []
    by_character[char].append(q)

# Show problematic "In which episode did..." questions first
print("\n\n'In which episode did...' QUESTIONS (Need Review):")
print("=" * 80)

episode_did_questions = [q for q in questions if q["question"].startswith("In which episode did")]

for i, q in enumerate(episode_did_questions, 1):
    char = q.get("character", "Unknown")
    source_type = q.get("source", "unknown")
    
    # Find character file
    safe_name = char.lower().replace(" ", "_").replace("'", "").replace("(", "").replace(")", "")
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in safe_name)
    char_file = os.path.join(characters_dir, f"{safe_name}.json")
    
    print(f"\n{'='*80}")
    print(f"QUESTION {i}:")
    print(f"  Question: {q['question']}")
    print(f"  Answer: {q.get('answer', 'N/A')}")
    print(f"  Character: {char}")
    print(f"  Source Type: {source_type}")
    print(f"  Character File: {char_file}")
    
    # Try to load and show source data
    if os.path.exists(char_file):
        try:
            with open(char_file, "r", encoding="utf-8") as f:
                char_data = json.load(f)
            
            if source_type == "timeline_event":
                # Find the relevant timeline event - check all possible sections
                timeline_events = []
                for section in ["history", "legacy", "background", "timeline", "early_life", 
                               "starfleet_career", "relationships", "alternate_timeline", "alternate_histories"]:
                    if section in char_data:
                        timeline_events.extend(char_data[section])
                
                print(f"  Timeline Events ({len(timeline_events)} total):")
                # Find events matching the episode from the question
                answer_episode = q.get("episode") or q.get("answer", "")
                matching_events = [e for e in timeline_events if answer_episode.lower() in str(e.get("episode", "")).lower()]
                
                if matching_events:
                    for j, event in enumerate(matching_events[:3], 1):
                        episode = event.get("episode", "N/A")
                        series = event.get("series", "N/A")
                        content = event.get("event", event.get("content", ""))[:250]
                        print(f"    {j}. [{series}] {episode}:")
                        print(f"       {content}...")
                else:
                    # Show first few events
                    for j, event in enumerate(timeline_events[:3], 1):
                        episode = event.get("episode", "N/A")
                        series = event.get("series", "N/A")
                        content = event.get("event", event.get("content", ""))[:250]
                        print(f"    {j}. [{series}] {episode}:")
                        print(f"       {content}...")
            
            elif source_type == "quote":
                # Quotes are in character.quote (single) or character.quotes (array)
                char_info = char_data.get("character", {})
                quote = char_info.get("quote")
                quotes = char_info.get("quotes", [])
                
                if quote:
                    text = quote.get("text", "")[:200]
                    source = quote.get("source", "N/A")
                    episode = quote.get("episode", "N/A")
                    print(f"  Quote:")
                    print(f"    \"{text}...\"")
                    print(f"    Source: {source}, Episode: {episode}")
                elif quotes:
                    print(f"  Quotes ({len(quotes)} total):")
                    for j, quote in enumerate(quotes[:3], 1):
                        text = quote.get("text", "")[:150]
                        source = quote.get("source", "N/A")
                        episode = quote.get("episode", "N/A")
                        print(f"    {j}. \"{text}...\" (Source: {source}, Episode: {episode})")
                else:
                    print(f"  No quotes found in character data")
            
            elif source_type == "appearances":
                appearances = char_data.get("appearances", {})
                print(f"  Appearances: {appearances}")
            
        except Exception as e:
            print(f"  Error loading character file: {e}")
    else:
        print(f"  Character file not found!")
    
    print()

print(f"\n\nTotal 'In which episode did...' questions: {len(episode_did_questions)}")
print(f"\nTo view a specific character file, check: {characters_dir}/")

