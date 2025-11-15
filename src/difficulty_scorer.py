#!/usr/bin/env python3
"""
Calculate difficulty scores for trivia questions based on page content metrics.
"""

from typing import Dict, List

def calculate_difficulty(page: Dict) -> float:
    """
    Calculate difficulty score for a page (0.0 = easy, 1.0 = hard).
    
    Factors:
    - Page length (longer = easier)
    - Character mentions (more = easier)
    - Episode references (more = easier)
    - Content density (more links = easier)
    
    Returns:
        Difficulty score between 0.0 and 1.0
    """
    # Factor 1: Page length (longer pages = more well-known content)
    text_length = page.get('text_length', 0)
    length_score = min(text_length / 10000.0, 1.0)  # Normalize to 0-1, cap at 10k chars
    
    # Factor 2: Character mentions (more mentions = more central)
    character_count = len(page.get('characters', []))
    character_score = min(character_count / 50.0, 1.0)  # Normalize to 0-1, cap at 50
    
    # Factor 3: Episode references (more references = more established)
    episode_count = len(page.get('episodes', []))
    episode_score = min(episode_count / 10.0, 1.0)  # Normalize to 0-1, cap at 10
    
    # Factor 4: Series coverage (more series = more well-known)
    series_count = len(page.get('series', []))
    series_score = min(series_count / 3.0, 1.0)  # Normalize to 0-1, cap at 3 series
    
    # Factor 5: Content richness (more subject fields = more developed)
    subject_fields = sum([
        len(page.get('species', [])),
        len(page.get('locations', [])),
        len(page.get('organizations', [])),
        len(page.get('concepts', []))
    ])
    richness_score = min(subject_fields / 10.0, 1.0)  # Normalize to 0-1, cap at 10
    
    # Calculate base difficulty (inverse of accessibility)
    # Higher scores = easier content, so difficulty = 1 - accessibility
    accessibility = (
        length_score * 0.3 +
        character_score * 0.2 +
        episode_score * 0.2 +
        series_score * 0.15 +
        richness_score * 0.15
    )
    
    difficulty = 1.0 - accessibility
    
    # Clamp to 0.0-1.0 range
    return max(0.0, min(1.0, difficulty))

def get_difficulty_level(difficulty: float) -> str:
    """
    Convert numeric difficulty to level name.
    
    Args:
        difficulty: Difficulty score (0.0-1.0)
    
    Returns:
        Difficulty level: "Easy", "Medium", or "Hard"
    """
    if difficulty < 0.3:
        return "Easy"
    elif difficulty < 0.7:
        return "Medium"
    else:
        return "Hard"

def filter_by_difficulty(
    pages: List[Dict],
    max_difficulty: float = 0.8,
    min_difficulty: float = 0.0
) -> List[Dict]:
    """
    Filter pages by difficulty threshold.
    
    Args:
        pages: List of page objects
        max_difficulty: Maximum difficulty to include (default 0.8 = filter very hard)
        min_difficulty: Minimum difficulty to include (default 0.0 = no minimum)
    
    Returns:
        Filtered list of pages within difficulty range
    """
    filtered = []
    for page in pages:
        difficulty = calculate_difficulty(page)
        if min_difficulty <= difficulty <= max_difficulty:
            page['_difficulty'] = difficulty
            page['_difficulty_level'] = get_difficulty_level(difficulty)
            filtered.append(page)
    
    return filtered

