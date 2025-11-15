#!/usr/bin/env python3
"""
Filter pages based on selected tags (series, character, species, location, etc.).
Supports AND/OR logic for multiple tag selections.
"""

from typing import List, Dict, Set, Optional

def filter_pages_by_tags(
    pages: List[Dict],
    indices: Dict,
    series: Optional[List[str]] = None,
    characters: Optional[List[str]] = None,
    species: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    organizations: Optional[List[str]] = None,
    concepts: Optional[List[str]] = None,
    episodes: Optional[List[str]] = None,
    match_all: bool = False  # If True, page must match ALL selected tags; if False, ANY tag
) -> List[int]:
    """
    Filter pages by selected tags.
    
    Args:
        pages: List of page objects
        indices: Dictionary of indices (by_series, by_character, etc.)
        series: List of series to filter by
        characters: List of characters to filter by
        species: List of species to filter by
        locations: List of locations to filter by
        organizations: List of organizations to filter by
        concepts: List of concepts to filter by
        episodes: List of episodes to filter by
        match_all: If True, page must match all selected tags; if False, matches any tag
    
    Returns:
        List of page indices matching the criteria
    """
    if not any([series, characters, species, locations, organizations, concepts, episodes]):
        # No filters selected, return all pages
        return list(range(len(pages)))
    
    # Collect candidate page indices for each tag type
    candidate_sets = []
    
    if series:
        series_indices = set()
        for s in series:
            if s in indices.get('by_series', {}):
                series_indices.update(indices['by_series'][s])
        if series_indices:
            candidate_sets.append(series_indices)
    
    if characters:
        char_indices = set()
        for char in characters:
            char_lower = char.lower()
            if char_lower in indices.get('by_character', {}):
                char_indices.update(indices['by_character'][char_lower])
        if char_indices:
            candidate_sets.append(char_indices)
    
    if species:
        species_indices = set()
        for sp in species:
            sp_lower = sp.lower()
            if sp_lower in indices.get('by_species', {}):
                species_indices.update(indices['by_species'][sp_lower])
        if species_indices:
            candidate_sets.append(species_indices)
    
    if locations:
        location_indices = set()
        for loc in locations:
            loc_lower = loc.lower()
            if loc_lower in indices.get('by_location', {}):
                location_indices.update(indices['by_location'][loc_lower])
        if location_indices:
            candidate_sets.append(location_indices)
    
    if organizations:
        org_indices = set()
        for org in organizations:
            org_lower = org.lower()
            if org_lower in indices.get('by_organization', {}):
                org_indices.update(indices['by_organization'][org_lower])
        if org_indices:
            candidate_sets.append(org_indices)
    
    if concepts:
        concept_indices = set()
        for concept in concepts:
            concept_lower = concept.lower()
            if concept_lower in indices.get('by_concept', {}):
                concept_indices.update(indices['by_concept'][concept_lower])
        if concept_indices:
            candidate_sets.append(concept_indices)
    
    if episodes:
        episode_indices = set()
        for ep in episodes:
            ep_lower = ep.lower()
            if ep_lower in indices.get('by_episode', {}):
                episode_indices.update(indices['by_episode'][ep_lower])
        if episode_indices:
            candidate_sets.append(episode_indices)
    
    if not candidate_sets:
        return []  # No matches found
    
    # Apply AND/OR logic
    if match_all:
        # Page must match ALL selected tag types (intersection)
        result = candidate_sets[0]
        for candidate_set in candidate_sets[1:]:
            result = result.intersection(candidate_set)
    else:
        # Page matches ANY selected tag type (union)
        result = set()
        for candidate_set in candidate_sets:
            result = result.union(candidate_set)
    
    return sorted(list(result))

def get_matching_pages(
    pages: List[Dict],
    indices: Dict,
    filters: Dict,
    match_all: bool = False
) -> List[Dict]:
    """
    Get full page objects matching the filters.
    
    Args:
        pages: List of page objects
        indices: Dictionary of indices
        filters: Dictionary with filter keys (series, characters, etc.)
        match_all: If True, match all filters; if False, match any filter
    
    Returns:
        List of matching page objects
    """
    matching_indices = filter_pages_by_tags(
        pages=pages,
        indices=indices,
        series=filters.get('series'),
        characters=filters.get('characters'),
        species=filters.get('species'),
        locations=filters.get('locations'),
        organizations=filters.get('organizations'),
        concepts=filters.get('concepts'),
        episodes=filters.get('episodes'),
        match_all=match_all
    )
    
    return [pages[i] for i in matching_indices]

