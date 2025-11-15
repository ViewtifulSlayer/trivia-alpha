#!/usr/bin/env python3
"""
Generate trivia questions from episode pages, following user's workflow:
1. Start with episode as anchor point
2. Extract questions from episode description
3. Build questions of varying difficulty
"""

import re
from typing import Dict, List, Optional
from generate_questions import clean_mediawiki_markup

def is_episode_page(page: Dict) -> bool:
    """Determine if a page is about an episode."""
    page_title = page.get('title', '').lower()
    has_episodes = len(page.get('episodes', [])) > 0
    
    # Check if title suggests episode page
    episode_indicators = ['episode', 'season', 'stardate']
    if any(indicator in page_title for indicator in episode_indicators):
        return True
    
    # If page has episodes listed and title matches episode name
    if has_episodes:
        page_title_clean = page_title.split('(')[0].strip()
        if any(ep.lower() == page_title_clean or page_title_clean in ep.lower() for ep in page.get('episodes', [])):
            return True
    
    return False

def extract_episode_season(text: str, page: Dict) -> Optional[str]:
    """Extract season number from episode page."""
    # Pattern: "Season X" or "DS9 Season X" or "episode X of season Y"
    season_patterns = [
        re.compile(r'season\s+(\d+)', re.I),
        re.compile(r'episode\s+\d+\s+of\s+season\s+(\d+)', re.I),
        re.compile(r'(\d+)(?:st|nd|rd|th)\s+season', re.I),
    ]
    
    for pattern in season_patterns:
        match = pattern.search(text)
        if match:
            return match.group(1)
    
    return None

def extract_episode_facts(text: str, page: Dict) -> List[Dict]:
    """
    Extract facts from episode pages that can be used for trivia questions.
    Follows user's workflow: episode as anchor, extract from description.
    
    Args:
        text: Episode page content
        page: Page dictionary
    
    Returns:
        List of episode-based facts
    """
    facts = []
    page_title = page.get('title', '').strip()
    episode_title = page_title
    
    # Extract season number
    season = extract_episode_season(text, page)
    
    # Pattern 1: Character relationships mentioned in episode
    # "X's daughter Y" or "X and Y's daughter Z" or "X O'Brien" and "Y O'Brien" (same last name)
    relationship_patterns = [
        re.compile(r'([A-Z][^.!?]*?)\'s\s+(daughter|son|father|mother|sister|brother|twin|creator)\s+([A-Z][^.!?]+)', re.I),
        re.compile(r'([A-Z][^.!?]*?)\s+and\s+([A-Z][^.!?]*?)\'s\s+(daughter|son)\s+([A-Z][^.!?]+)', re.I),
        # Pattern for "Miles O'Brien" and "Molly O'Brien" (same last name indicates relationship)
        re.compile(r'\[\[([A-Z][^\]]*?)\s+O\'?Brien\]\].*?\[\[([A-Z][^\]]*?)\s+O\'?Brien\]\]', re.I),
    ]
    
    # Also look for character names with same last name in description
    # Extract "Miles O'Brien", "Keiko O'Brien", "Molly O'Brien" pattern
    obrien_pattern = re.compile(r'\[\[([A-Z][a-z]+)\s+O\'?Brien\]\]', re.I)
    obrien_chars = obrien_pattern.findall(text)
    if len(obrien_chars) >= 2:
        # If we find multiple O'Briens, likely a family relationship
        for char in obrien_chars:
            if char.lower() not in ['miles', 'keiko']:  # Likely a child
                facts.append({
                    'type': 'episode_relationship',
                    'episode': episode_title,
                    'parent': 'Miles and Keiko O\'Brien',
                    'relationship': 'daughter' if 'molly' in char.lower() else 'child',
                    'child': f"{char} O'Brien",
                    'question_type': 'what',
                    'question_template': "What was Miles and Keiko O'Brien's daughter's name?",
                    'answer': f"{char} O'Brien",
                    'text': f"{char} O'Brien"
                })
    
    for pattern in relationship_patterns:
        for match in pattern.finditer(text):
            if len(match.groups()) == 3:
                parent = match.group(1).strip()
                rel_type = match.group(2).strip()
                child = match.group(3).strip()
                child = clean_mediawiki_markup(child).split(',')[0].split('(')[0].strip()[:50]
                
                if len(child) > 2 and len(child) < 50:
                    facts.append({
                        'type': 'episode_relationship',
                        'episode': episode_title,
                        'parent': parent,
                        'relationship': rel_type,
                        'child': child,
                        'question_type': 'what',
                        'question_template': f"What was {{parent}}'s {rel_type}'s name?",
                        'answer': child,
                        'text': match.group(0)
                    })
            elif len(match.groups()) == 4:
                parent1 = match.group(1).strip()
                parent2 = match.group(2).strip()
                rel_type = match.group(3).strip()
                child = match.group(4).strip()
                child = clean_mediawiki_markup(child).split(',')[0].split('(')[0].strip()[:50]
                
                if len(child) > 2 and len(child) < 50:
                    facts.append({
                        'type': 'episode_relationship',
                        'episode': episode_title,
                        'parent': f"{parent1} and {parent2}",
                        'relationship': rel_type,
                        'child': child,
                        'question_type': 'what',
                        'question_template': f"What was {{parent}}'s {rel_type}'s name?",
                        'answer': child,
                        'text': match.group(0)
                    })
    
    # Pattern 2: Objects/items mentioned in episode
    # "X's Y" where Y is an object (doll, ship, etc.)
    object_pattern = re.compile(r'([A-Z][^.!?]*?)\'s\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:appeared|featured|seen)', re.I)
    for match in object_pattern.finditer(text):
        owner = match.group(1).strip()
        object_name = match.group(2).strip()
        object_name = clean_mediawiki_markup(object_name).split(',')[0].split('(')[0].strip()[:50]
        
        if len(object_name) > 2 and len(object_name) < 50:
            facts.append({
                'type': 'episode_object',
                'episode': episode_title,
                'owner': owner,
                'object': object_name,
                'question_type': 'what',
                'question_template': f"{{owner}}'s {object_name} appeared in the episode {{episode}}. What was its name?",
                'answer': object_name,  # This might need refinement
                'text': match.group(0)
            })
    
    # Pattern 3: Episode description facts
    # Extract key events/characters from first paragraph (episode description)
    # The description is usually in the first paragraph after the sidebar
    # Look for the summary paragraph (usually starts after "}}")
    description_start = text.find('}}')
    if description_start > 0:
        description_text = text[description_start:description_start+500]  # First 500 chars after sidebar
    else:
        description_text = text[:500]  # Fallback to first 500 chars
    
    # Extract episode description (usually one sentence)
    description_sentences = description_text.split('.')[:2]  # First 1-2 sentences
    for sentence in description_sentences:
        # Pattern: "X sends Y through Z" or "X returns as Y"
        event_pattern = re.compile(r'([A-Z][^.!?]*?)\s+(sends|returns|becomes|discovers|meets|encounters)\s+([A-Z][^.!?]+)', re.I)
        for match in event_pattern.finditer(sentence):
            character = match.group(1).strip()
            action = match.group(2).strip()
            target = match.group(3).strip()
            target = clean_mediawiki_markup(target).split(',')[0].split('(')[0].strip()[:50]
            
            if len(target) > 2 and len(target) < 50:
                facts.append({
                    'type': 'episode_event',
                    'episode': episode_title,
                    'character': character,
                    'action': action,
                    'target': target,
                    'question_type': 'what',
                    'question_template': f"What was the title of the episode in which {character} {action} {{target}}?",
                    'answer': episode_title,
                    'text': match.group(0)
                })
    
    # Extract episode description for question generation
    # Look for the summary line (usually after "}}")
    desc_match = re.search(r'\}\}\s*([^=]+?)(?:==|$)', text, re.DOTALL)
    if desc_match:
        description = clean_mediawiki_markup(desc_match.group(1).strip())
        # Extract key phrases from description
        # "An accident on the planet Golana sends Molly O'Brien through a time portal..."
        # Can generate: "What was the title of the episode in which Molly O'Brien [action]?"
        
        # Find character names and actions in description
        # Pattern: "An accident... sends Molly O'Brien through a time portal"
        # Better approach: Find character names first, then find actions near them
        
        character_names = []
        
        # Extract character names (wiki link format: [[Character Name|Display]] or [[Character Name]])
        char_link_pattern = re.compile(r'\[\[([A-Z][^\|\]]+)(?:\|[^\]]+)?\]\]', re.I)
        for match in char_link_pattern.finditer(description):
            char_name = match.group(1).strip()
            # Filter out non-character links (locations, concepts, etc.)
            if len(char_name.split()) <= 3 and not any(word.lower() in ['planet', 'world', 'ship', 'station', 'century'] for word in char_name.split()):
                character_names.append((char_name, match.start()))
        
        # Also extract plain text character names (like "Molly O'Brien" in description)
        # Pattern: "First Last" or "First Middle Last" (capitalized names, handle apostrophes)
        # Better pattern that handles "Molly O'Brien" correctly
        plain_name_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]*\'[A-Z]?[a-z]+|\s+[A-Z][a-z]+){1,2})\b')
        for match in plain_name_pattern.finditer(description):
            char_name = match.group(1).strip()
            # Filter out common non-character words
            words = char_name.split()
            if len(words) >= 2 and not any(word.lower() in ['planet', 'world', 'ship', 'station', 'century', 'accident', 'portal', 'years', 'past', 'present', 'three', 'hundred', 'uninhabited', 'golana'] for word in words):
                # Check if it looks like a person's name (has common name patterns)
                name_lower = char_name.lower().replace("'", "")
                if any(name in name_lower for name in ['molly', 'miles', 'keiko', 'sisko', 'kira', 'bashir', 'odo', 'quark', 'dax', 'worff', 'picard', 'riker', 'data', 'troi', 'crusher', 'laforge', 'janeway', 'chakotay', 'paris', 'torres', 'tuvok', 'kim', 'doctor', 'neelix', 'seven', 'obrien', 'brien']):
                    character_names.append((char_name, match.start()))
        
        # For each character, find nearby actions
        for char_name, char_pos in character_names[:3]:  # Limit to first 3 characters
            # Look for action verbs near the character (within 100 chars)
            context_start = max(0, char_pos - 50)
            context_end = min(len(description), char_pos + 100)
            context = description[context_start:context_end]
            
            # Find action verbs near character
            # Handle both: "sends Molly O'Brien through" and "Molly O'Brien returns"
            action_verbs = ['sends', 'returns', 'becomes', 'discovers', 'meets', 'encounters', 'travels', 'goes']
            
            # Pattern 1: Verb before character: "sends Molly O'Brien through..."
            for verb in action_verbs:
                # Escape the character name but handle apostrophes
                char_escaped = re.escape(char_name).replace(r"\'", r"['']?")
                # Match: verb + character + "through/into/to" + target phrase
                pattern_before = re.compile(rf'({verb})\s+{char_escaped}\s+(?:through|into|to)\s+([^.!?]+?)(?:\s+three|\s+hundred|\.|$)', re.I)
                match = pattern_before.search(context)
                if match:
                    action = match.group(1)
                    target = match.group(2).strip() if len(match.groups()) >= 2 else ''
                    # Clean and extract key phrase
                    target = clean_mediawiki_markup(target)
                    # Get meaningful phrase (stop at numbers or long phrases)
                    target_parts = target.split()
                    # Take first 6-10 words, stop at numbers
                    target_clean = []
                    for word in target_parts[:10]:
                        if word.isdigit() and len(target_clean) > 3:
                            break
                        target_clean.append(word)
                    target = ' '.join(target_clean[:8])  # Max 8 words
                    
                    if len(target) > 5:  # Only if we have a meaningful target
                        facts.append({
                            'type': 'episode_description',
                            'episode': episode_title,
                            'character': char_name,
                            'action': action,
                            'target': target,
                            'question_type': 'what',
                            'question_template': f"What was the title of the episode in which {char_name} {action} {target}?",
                            'answer': episode_title,
                            'text': match.group(0)
                        })
                        break
            
            # Pattern 2: Character before verb: "Molly O'Brien returns..."
            if not any(f.get('character') == char_name and f.get('type') == 'episode_description' for f in facts):
                for verb in action_verbs:
                    pattern_after = re.compile(rf'{re.escape(char_name)}[^.!?]*?\s+({verb})[^.!?]*?(?:through|into|to|as|with|eighteen|old)', re.I)
                    match = pattern_after.search(context)
                    if match:
                        action = match.group(1)
                        # Extract what they return/become/etc.
                        target = match.group(0).split(verb)[1].strip()[:40] if len(match.group(0).split(verb)) > 1 else ''
                        target = clean_mediawiki_markup(target).split(',')[0].split('(')[0].strip()[:40]
                        
                        facts.append({
                            'type': 'episode_description',
                            'episode': episode_title,
                            'character': char_name,
                            'action': action,
                            'target': target,
                            'question_type': 'what',
                            'question_template': f"What was the title of the episode in which {char_name} {action} {target}?",
                            'answer': episode_title,
                            'text': match.group(0)
                        })
                        break
    
    # Add season fact if found
    if season:
        # Determine series from page
        series_list = page.get('series', [])
        primary_series = series_list[0] if series_list else 'Star Trek'
        
        facts.append({
            'type': 'episode_season',
            'episode': episode_title,
            'season': season,
            'question_type': 'which',
            'question_template': f"Which season of {primary_series} did the episode \"{episode_title}\" occur?",
            'answer': f"Season {season}",
            'text': f"Season {season}"
        })
    
    return facts

def generate_episode_questions(page: Dict, max_questions: int = 5) -> List[Dict]:
    """
    Generate questions from an episode page following user's workflow.
    
    Args:
        page: Episode page dictionary
        max_questions: Maximum questions to generate
    
    Returns:
        List of question dictionaries
    """
    questions = []
    
    if not is_episode_page(page):
        return questions
    
    full_text = page.get('full_text', '')
    if not full_text:
        return questions
    
    # Extract episode facts
    episode_facts = extract_episode_facts(full_text, page)
    
    if not episode_facts:
        return questions
    
    episode_title = page.get('title', '')
    series = page.get('series', ['Star Trek'])
    primary_series = series[0] if series else 'Star Trek'
    
    # Generate questions from facts, avoiding duplicates
    seen_questions = set()
    
    for fact in episode_facts:
        if len(questions) >= max_questions:
            break
            
        question_text = None
        answer = fact.get('answer', '')
        
        if fact.get('type') == 'episode_relationship':
            # "What was X's daughter's name?"
            parent = fact.get('parent', '')
            rel_type = fact.get('relationship', '')
            question_text = f"What was {parent}'s {rel_type}'s name?"
            answer = fact.get('child', '')
        
        elif fact.get('type') == 'episode_season':
            # "Which season of DS9 did the episode 'Time's Orphan' occur?"
            question_text = f"Which season of {primary_series} did the episode \"{episode_title}\" occur?"
            answer = fact.get('answer', '')
        
        elif fact.get('type') == 'episode_event' or fact.get('type') == 'episode_description':
            # "What was the title of the DS9 episode in which Molly O'Brien [action]?"
            character = fact.get('character', '')
            action = fact.get('action', '')
            target = fact.get('target', '')
            
            # Clean up character name (remove wiki markup)
            character = clean_mediawiki_markup(character)
            if '[' in character:
                # Extract from [[Character Name|Display]] format
                char_match = re.search(r'\[\[([^\|\]]+)', character)
                if char_match:
                    character = char_match.group(1)
            
            # Build question - use description if available
            # For "sends through" type questions, format better
            if action == 'sends' and target:
                # "What was the title of the episode in which [character] [action] [target]?"
                question_text = f"What was the title of the {primary_series} episode in which {character} {action} {target}?"
            elif action == 'returns' and target:
                # "What was the title of the episode in which [character] [action] [target]?"
                question_text = f"What was the title of the {primary_series} episode in which {character} {action} {target}?"
            elif target and len(target) > 5:
                question_text = f"What was the title of the {primary_series} episode in which {character} {action} {target}?"
            else:
                # Fallback: simpler question
                question_text = f"What was the title of the {primary_series} episode in which {character} {action}?"
            answer = episode_title
        
        elif fact.get('type') == 'episode_object':
            # "[Character]'s [object] appeared in episodes. What was its name?"
            owner = fact.get('owner', '')
            obj = fact.get('object', '')
            question_text = f"{owner}'s {obj} appeared in the episode \"{episode_title}\". What was its name?"
            answer = fact.get('object', '')
        
        # Only add if question is unique
        if question_text and answer:
            question_key = (question_text.lower(), answer.lower())
            if question_key not in seen_questions:
                seen_questions.add(question_key)
                questions.append({
                    'question': question_text,
                    'answer': answer,
                    'source_page': episode_title,
                    'series': series,
                    'question_type': fact.get('question_type', 'what'),
                    'fact_type': fact.get('type'),
                    'difficulty': 0.3,  # Default difficulty
                    'difficulty_level': 'Medium'
                })
    
    return questions

