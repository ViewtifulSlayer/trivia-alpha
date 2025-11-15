#!/usr/bin/env python3
"""
Main trivia question generator - ties together filtering, question generation, and difficulty scoring.
"""

import json
import sys
from typing import Dict, List, Optional
from filter_pages import filter_pages_by_tags, get_matching_pages
from difficulty_scorer import calculate_difficulty, get_difficulty_level, filter_by_difficulty
from generate_questions import generate_questions_from_pages
from episode_question_generator import is_episode_page, generate_episode_questions

def load_data(data_path: str) -> Dict:
    """Load extracted data from JSON file."""
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_trivia_questions(
    data: Dict,
    series: Optional[List[str]] = None,
    characters: Optional[List[str]] = None,
    species: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    organizations: Optional[List[str]] = None,
    concepts: Optional[List[str]] = None,
    episodes: Optional[List[str]] = None,
    max_difficulty: float = 0.8,
    max_questions: int = 10,
    question_types: List[str] = ['what']
) -> List[Dict]:
    """
    Generate trivia questions based on selected tags.
    
    Args:
        data: Loaded data dictionary with pages and indices
        series: List of series to filter by
        characters: List of characters to filter by
        species: List of species to filter by
        locations: List of locations to filter by
        organizations: List of organizations to filter by
        concepts: List of concepts to filter by
        episodes: List of episodes to filter by
        max_difficulty: Maximum difficulty (0.0-1.0)
        max_questions: Maximum number of questions to generate
        question_types: List of question types ('what', 'who', 'where', 'which')
    
    Returns:
        List of question dictionaries with difficulty scores
    """
    pages = data.get('pages', [])
    indices = data.get('indices', {})
    
    # Step 1: Filter pages by tags
    matching_indices = filter_pages_by_tags(
        pages=pages,
        indices=indices,
        series=series,
        characters=characters,
        species=species,
        locations=locations,
        organizations=organizations,
        concepts=concepts,
        episodes=episodes,
        match_all=False  # Match ANY selected tag
    )
    
    if not matching_indices:
        return []
    
    matching_pages = [pages[i] for i in matching_indices]
    
    print(f"Found {len(matching_pages)} pages matching filters")
    
    # Step 1.5: STRICT title matching for character searches (Priority 1 fix)
    if characters and len(characters) > 0:
        # Find pages where title exactly matches character (or very close match)
        character_titles = [c.lower().strip() for c in characters]
        # Also create variations (e.g., "Jean-Luc Picard" -> also check "Picard")
        character_variations = set(character_titles)
        for char_title in character_titles:
            # Add last name if full name provided
            parts = char_title.split()
            if len(parts) > 1:
                character_variations.add(parts[-1])  # Last name
                if len(parts) > 2:
                    character_variations.add(' '.join(parts[-2:]))  # Last two words
        
        exact_match_pages = []
        close_match_pages = []
        other_pages = []
        
        for page in matching_pages:
            page_title = page.get('title', '').lower().strip()
            matched = False
            
            for char_title in character_variations:
                # Exact match (title is exactly the character name)
                if page_title == char_title:
                    exact_match_pages.append(page)
                    matched = True
                    break
                # Close match (character name is the main part of title)
                elif page_title.startswith(char_title + ' ') or page_title.startswith(char_title + '('):
                    close_match_pages.append(page)
                    matched = True
                    break
                # Reverse match (title is part of character name, e.g., "Picard" matches "Jean-Luc Picard")
                elif char_title in page_title and len(char_title) > 3:  # Avoid short matches
                    # Check if it's a meaningful match (not just a substring)
                    if page_title.startswith(char_title) or ' ' + char_title in page_title:
                        close_match_pages.append(page)
                        matched = True
                        break
            
            if not matched:
                other_pages.append(page)
        
        # Use strict matching: ONLY exact/close matches for character searches
        if exact_match_pages or close_match_pages:
            matching_pages = exact_match_pages + close_match_pages
            print(f"  Using strict title matching: {len(exact_match_pages)} exact, {len(close_match_pages)} close matches")
            print(f"  Excluded {len(other_pages)} pages that only mention character")
        else:
            # Fallback: if no title matches, use all (but warn)
            print(f"  WARNING: No pages with matching title found, using all {len(matching_pages)} pages")
    
    # Step 2: Filter by difficulty
    filtered_pages = filter_by_difficulty(
        matching_pages,
        max_difficulty=max_difficulty,
        min_difficulty=0.0
    )
    
    print(f"After difficulty filtering: {len(filtered_pages)} pages")
    
    # Step 3: Generate questions
    # Prioritize episode pages for question generation (user's workflow)
    episode_pages = [p for p in filtered_pages if is_episode_page(p)]
    other_pages = [p for p in filtered_pages if not is_episode_page(p)]
    
    questions = []
    
    # Generate questions from episode pages first (preferred source)
    for episode_page in episode_pages[:max_questions]:
        episode_questions = generate_episode_questions(episode_page, max_questions=3)
        questions.extend(episode_questions)
        if len(questions) >= max_questions:
            break
    
    # If we need more questions, generate from other pages
    if len(questions) < max_questions:
        focus_tags = {
            'characters': characters or [],
            'species': species or [],
            'locations': locations or []
        }
        
        remaining_questions = generate_questions_from_pages(
            other_pages,
            question_types=question_types,
            max_questions_per_page=3,
            max_total_questions=max_questions - len(questions),
            focus_tags=focus_tags
        )
        questions.extend(remaining_questions)
    
    # Step 4: Add difficulty scores to questions
    for question in questions:
        # Find source page
        source_title = question.get('source_page')
        source_page = next(
            (p for p in filtered_pages if p.get('title') == source_title),
            None
        )
        
        if source_page:
            difficulty = calculate_difficulty(source_page)
            question['difficulty'] = difficulty
            question['difficulty_level'] = get_difficulty_level(difficulty)
        else:
            question['difficulty'] = 0.5
            question['difficulty_level'] = 'Medium'
    
    # Sort by difficulty (easier first)
    questions.sort(key=lambda q: q.get('difficulty', 0.5))
    
    return questions

def main():
    """Example usage of trivia generator."""
    if len(sys.argv) < 2:
        print("Usage: python trivia_generator.py <data_file> [options]")
        print("\nExample:")
        print("  python trivia_generator.py ../data/extracted/extracted_data.json --series DS9 --character Odo")
        sys.exit(1)
    
    data_path = sys.argv[1]
    
    # Load data
    print(f"Loading data from {data_path}...")
    data = load_data(data_path)
    print(f"Loaded {len(data.get('pages', []))} pages")
    
    # Example: Generate questions for DS9, Odo
    print("\nGenerating questions for: DS9, Character: Odo")
    questions = generate_trivia_questions(
        data,
        series=['DS9'],
        characters=['Odo'],
        max_difficulty=0.7,
        max_questions=5
    )
    
    print(f"\nGenerated {len(questions)} questions:\n")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q['question']}")
        print(f"   Answer: {q['answer']}")
        print(f"   Difficulty: {q['difficulty_level']} ({q['difficulty']:.2f})")
        print(f"   Source: {q['source_page']}")
        print()

if __name__ == '__main__':
    main()

