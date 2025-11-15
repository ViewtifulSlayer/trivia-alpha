#!/usr/bin/env python3
"""
Generate trivia questions from page content using template-based approach.
"""

import re
import random
from typing import Dict, List, Optional

# Question templates
QUESTION_TEMPLATES = {
    'what': [
        "What is the class of {subject}?",
        "What is the name of {subject}?",
        "What is {subject}?",
        "What was {subject}?",
    ],
    'who': [
        "Who was {subject}?",
        "Who is {subject}?",
        "Who was {subject}'s {relationship}?",
        "Who played {subject}?",
    ],
    'where': [
        "Where was {subject} born?",
        "Where is {subject} located?",
        "Where was {subject}?",
    ],
    'when': [
        "When is {subject}?",
        "When was {subject}?",
        "When did {subject} occur?",
    ],
    'which': [
        "Which episode featured {subject}?",
        "Which series featured {subject}?",
    ],
}

def clean_mediawiki_markup(text: str) -> str:
    """Remove MediaWiki markup from text."""
    # Remove [[links|display]] or [[links]]
    text = re.sub(r'\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]', r'\1', text)
    # Remove {{templates}}
    text = re.sub(r'\{\{[^\}]+\}\}', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_specific_facts(text: str, page: Dict) -> List[Dict]:
    """
    Extract specific, factual information: names, dates, locations, relationships, classes.
    These are better suited for trivia questions with concise answers.
    
    Args:
        text: Page content text
        page: Page dictionary with metadata
    
    Returns:
        List of specific fact dictionaries
    """
    facts = []
    page_title = page.get('title', '').strip()
    
    # Pattern 1: "X was born in Y" or "X was born on Y" (location/date)
    born_pattern = re.compile(r'([A-Z][^.!?]*?)\s+was\s+born\s+(?:in|on)\s+([^.!?]+)', re.I)
    for match in born_pattern.finditer(text):
        subject = match.group(1).strip()
        if subject.lower() == page_title.lower() or page_title.lower().startswith(subject.lower() + ' '):
            location_date = clean_mediawiki_markup(match.group(2).strip())
            # Extract just the key part (first 50 chars, stop at comma if present)
            answer = location_date.split(',')[0].strip()[:50]
            if len(answer) > 5 and len(answer) < 50:
                facts.append({
                    'type': 'born',
                    'subject': subject,
                    'predicate': answer,
                    'question_type': 'where' if any(word in answer.lower() for word in ['city', 'state', 'planet', 'location', 'place']) else 'when',
                    'text': match.group(0)
                })
    
    # Pattern 2: "X's father/mother/captain was Y" (relationships)
    relationship_pattern = re.compile(r'([A-Z][^.!?]*?)\'s\s+(father|mother|captain|creator|designer|inventor)\s+was\s+([A-Z][^.!?]+)', re.I)
    for match in relationship_pattern.finditer(text):
        subject = match.group(1).strip()
        rel_type = match.group(2).strip()
        person = match.group(3).strip()
        person = clean_mediawiki_markup(person).split(',')[0].split('(')[0].strip()[:50]
        
        if subject.lower() == page_title.lower() or page_title.lower().startswith(subject.lower() + ' '):
            if len(person) > 3 and len(person) < 50:
                facts.append({
                    'type': 'relationship',
                    'subject': subject,
                    'predicate': person,
                    'relationship': rel_type,
                    'question_type': 'who',
                    'text': match.group(0)
                })
    
    # Pattern 3: "X is a Y-class" or "X was a Y-class" (ship classes, types)
    class_pattern = re.compile(r'([A-Z][^.!?]*?)\s+(?:is|was)\s+(?:a|an)\s+([A-Z][^.!?]*?)\s*class', re.I)
    for match in class_pattern.finditer(text):
        subject = match.group(1).strip()
        ship_class = match.group(2).strip()
        ship_class = clean_mediawiki_markup(ship_class).split(',')[0].split('(')[0].strip()[:50]
        
        if subject.lower() == page_title.lower() or page_title.lower().startswith(subject.lower() + ' '):
            if len(ship_class) > 2 and len(ship_class) < 50:
                facts.append({
                    'type': 'class',
                    'subject': subject,
                    'predicate': ship_class,
                    'question_type': 'what',
                    'text': match.group(0)
                })
    
    # Pattern 4: "X is named Y" or "X was named Y" (names)
    named_pattern = re.compile(r'([A-Z][^.!?]*?)\s+(?:is|was)\s+named\s+([A-Z][^.!?]+)', re.I)
    for match in named_pattern.finditer(text):
        subject = match.group(1).strip()
        name = match.group(2).strip()
        name = clean_mediawiki_markup(name).split(',')[0].split('(')[0].split('.')[0].strip()[:50]
        
        if subject.lower() == page_title.lower() or page_title.lower().startswith(subject.lower() + ' '):
            if len(name) > 2 and len(name) < 50:
                facts.append({
                    'type': 'name',
                    'subject': subject,
                    'predicate': name,
                    'question_type': 'what',
                    'text': match.group(0)
                })
    
    # Pattern 5: Dates - "X occurred on Y" or "X is Y" (dates like "First Contact Day")
    date_pattern = re.compile(r'([A-Z][^.!?]*?)\s+(?:is|was|occurred\s+on|takes\s+place\s+on)\s+([A-Z][^.!?]*?\d{1,2}[^.!?]*)', re.I)
    for match in date_pattern.finditer(text):
        subject = match.group(1).strip()
        date = match.group(2).strip()
        date = clean_mediawiki_markup(date).split(',')[0].split('(')[0].strip()[:50]
        
        if subject.lower() == page_title.lower() or page_title.lower().startswith(subject.lower() + ' '):
            if any(char.isdigit() for char in date) and len(date) > 5 and len(date) < 50:
                facts.append({
                    'type': 'date',
                    'subject': subject,
                    'predicate': date,
                    'question_type': 'when',
                    'text': match.group(0)
                })
    
    return facts

def extract_facts_from_content(text: str, page: Dict, focus_tags: Optional[Dict] = None) -> List[Dict]:
    """
    Extract factual statements from page content.
    Prioritizes specific facts (names, dates, locations, relationships) over narrative text.
    
    Args:
        text: Page content text
        page: Page dictionary with metadata
        focus_tags: Optional dict with tags to focus on (characters, species, etc.)
    
    Returns:
        List of fact dictionaries with subject, predicate, object
    """
    facts = []
    page_title = page.get('title', '').lower().strip()
    
    # First, extract specific facts (preferred for trivia - these have concise answers)
    specific_facts = extract_specific_facts(text, page)
    facts.extend(specific_facts)
    
    # If we have enough specific facts, prioritize them and skip narrative extraction
    if len(specific_facts) >= 5:
        return specific_facts[:10]  # Return top 10 specific facts
    
    # Otherwise, fall back to narrative patterns (but make answers more concise)
    # If focus tags provided, prioritize facts mentioning those tags
    focus_terms = set()
    strict_character_match = False
    
    if focus_tags:
        if focus_tags.get('characters'):
            char_list = [c.lower().strip() for c in focus_tags['characters']]
            focus_terms.update(char_list)
            # Check if page title matches character (strict mode)
            if any(char_title == page_title or page_title.startswith(char_title + ' ') for char_title in char_list):
                strict_character_match = True
        if focus_tags.get('species'):
            focus_terms.update([s.lower() for s in focus_tags['species']])
        if focus_tags.get('locations'):
            focus_terms.update([l.lower() for l in focus_tags['locations']])
    
    # Pattern 1: "X was Y" or "X is Y" - STRICT filtering for character matches
    was_pattern = re.compile(r'([A-Z][^.!?]*?)\s+(?:was|is)\s+([^.!?]+)', re.I)
    for match in was_pattern.finditer(text):
        subject = match.group(1).strip()
        predicate = match.group(2).strip()
        
        # Clean predicate
        predicate = clean_mediawiki_markup(predicate)
        
        # Validate answer completeness (Priority 3 fix)
        if len(predicate) < 15:  # Too short, likely fragment
            continue
        if predicate.lower() in ['born on', 'named for', 'died in', 'created by', 'played by']:
            continue  # Common fragment patterns
        
        # Check if fact is relevant (Priority 2 fix - enhanced filtering)
        subject_lower = subject.lower().strip()
        is_relevant = False
        
        if strict_character_match:
            # STRICT MODE: Only facts where subject matches page title (character name)
            # This ensures facts are about the character, not just mentioning them
            if subject_lower == page_title or subject_lower.startswith(page_title + ' '):
                is_relevant = True
        elif focus_terms:
            # FOCUS MODE: Facts mentioning focus terms
            if any(term in subject_lower for term in focus_terms) or subject_lower == page_title:
                is_relevant = True
        else:
            # NO FOCUS: Include all facts about page title
            if subject_lower == page_title or subject_lower.startswith(page_title + ' '):
                is_relevant = True
        
        # Make predicate more concise - extract key phrase (first 60 chars, stop at comma)
        concise_predicate = predicate.split(',')[0].split('(')[0].strip()[:60]
        
        if is_relevant and len(subject) < 50 and len(concise_predicate) >= 10 and len(concise_predicate) <= 60:
            facts.append({
                'type': 'was',
                'subject': subject,
                'predicate': concise_predicate,  # Use concise version
                'text': clean_mediawiki_markup(match.group(0))
            })
    
    # Pattern 2: "X served as Y" - STRICT filtering
    served_pattern = re.compile(r'([A-Z][^.!?]*?)\s+served\s+as\s+([^.!?]+)', re.I)
    for match in served_pattern.finditer(text):
        subject = match.group(1).strip()
        role = match.group(2).strip()
        role = clean_mediawiki_markup(role)
        
        # Validate answer completeness
        if len(role) < 15:
            continue
        
        subject_lower = subject.lower().strip()
        is_relevant = False
        
        if strict_character_match:
            # STRICT: Only facts about the character
            if subject_lower == page_title or subject_lower.startswith(page_title + ' '):
                is_relevant = True
        elif focus_terms:
            if any(term in subject_lower for term in focus_terms) or subject_lower == page_title:
                is_relevant = True
        else:
            if subject_lower == page_title or subject_lower.startswith(page_title + ' '):
                is_relevant = True
        
        # Make role more concise
        concise_role = role.split(',')[0].split('(')[0].strip()[:60]
        
        if is_relevant and len(subject) < 50 and len(concise_role) >= 10 and len(concise_role) <= 60:
            facts.append({
                'type': 'role',
                'subject': subject,
                'predicate': concise_role,  # Use concise version
                'text': clean_mediawiki_markup(match.group(0))
            })
    
    # Pattern 3: "X is known for Y" - STRICT filtering
    known_pattern = re.compile(r'([A-Z][^.!?]*?)\s+is\s+known\s+for\s+([^.!?]+)', re.I)
    for match in known_pattern.finditer(text):
        subject = match.group(1).strip()
        trait = match.group(2).strip()
        trait = clean_mediawiki_markup(trait)
        
        # Validate answer completeness
        if len(trait) < 15:
            continue
        
        subject_lower = subject.lower().strip()
        is_relevant = False
        
        if strict_character_match:
            # STRICT: Only facts about the character
            if subject_lower == page_title or subject_lower.startswith(page_title + ' '):
                is_relevant = True
        elif focus_terms:
            if any(term in subject_lower for term in focus_terms) or subject_lower == page_title:
                is_relevant = True
        else:
            if subject_lower == page_title or subject_lower.startswith(page_title + ' '):
                is_relevant = True
        
        # Make trait more concise
        concise_trait = trait.split(',')[0].split('(')[0].strip()[:60]
        
        if is_relevant and len(subject) < 50 and len(concise_trait) >= 10 and len(concise_trait) <= 60:
            facts.append({
                'type': 'known_for',
                'subject': subject,
                'predicate': concise_trait,  # Use concise version
                'text': clean_mediawiki_markup(match.group(0))
            })
    
    # Sort facts: specific facts first (they have better answers), then by relevance
    facts.sort(key=lambda f: (
        f.get('type') in ['relationship', 'class', 'name', 'date', 'born'],  # Specific facts first
        any(term in f.get('subject', '').lower() for term in focus_terms) if focus_terms else False
    ), reverse=True)
    
    return facts[:15]  # Return top 15 facts

def validate_answer(answer: str) -> bool:
    """
    Validate that an answer is complete and not a fragment.
    
    Args:
        answer: Answer text to validate
    
    Returns:
        True if answer is valid, False if fragment
    """
    if not answer or len(answer) < 15:
        return False
    
    # Check for common fragment patterns
    answer_lower = answer.lower().strip()
    fragment_patterns = [
        'born on', 'named for', 'died in', 'created by',
        'played by', 'voiced by', 'portrayed by', 'born',
        'died', 'created', 'named'
    ]
    
    # If answer is just a fragment pattern with no context, reject
    if answer_lower in fragment_patterns:
        return False
    
    # If answer starts with fragment pattern and is very short, likely incomplete
    if any(answer_lower.startswith(pattern) for pattern in fragment_patterns) and len(answer) < 25:
        return False
    
    # Check if answer looks like a complete thought (has some substance)
    if len(answer.split()) < 3:  # Less than 3 words is likely incomplete
        return False
    
    return True

def is_character_page(page: Dict) -> bool:
    """Determine if a page is about a character."""
    page_title = page.get('title', '')
    page_title_lower = page_title.lower()
    has_characters = len(page.get('characters', [])) > 0
    
    # Check if title suggests character page
    character_indicators = ['character', 'actor', 'played', 'portrayed', 'voiced']
    if any(indicator in page_title_lower for indicator in character_indicators):
        return True
    
    # Check if page title is in the characters list (strong indicator)
    if has_characters:
        page_title_clean = page_title.split('(')[0].strip()  # Remove parentheticals
        if any(char.lower() == page_title_clean.lower() or page_title_clean.lower() in char.lower() for char in page.get('characters', [])):
            return True
    
    # If page has characters listed and title matches a character name pattern
    if has_characters:
        # Check if title is likely a person's name (has capital letters, not too long, no special chars)
        title_words = page_title.split()
        if len(title_words) <= 4 and len(title_words) >= 1:
            # Check if first word starts with capital (likely a name)
            if title_words[0] and title_words[0][0].isupper():
                # Exclude common non-character terms
                non_character_terms = ['enterprise', 'voyager', 'defiant', 'station', 'planet', 'ship', 'class']
                if not any(term in page_title_lower for term in non_character_terms):
                    return True
    
    return False

def select_appropriate_question_types(page: Dict, fact: Dict, requested_types: List[str]) -> List[str]:
    """
    Select question types that are appropriate for the page and fact.
    CRITICAL: Use 'who' for characters, not 'what'.
    
    Args:
        page: Page object
        fact: Fact object
        requested_types: User-requested question types
    
    Returns:
        List of appropriate question types
    """
    appropriate_types = []
    page_title = page.get('title', '').lower()
    is_character = is_character_page(page)
    
    # If fact has a preferred question type, use it
    if fact.get('question_type'):
        preferred_type = fact.get('question_type')
        if preferred_type in requested_types or not requested_types:
            return [preferred_type]
    
    # Check page characteristics
    has_locations = len(page.get('locations', [])) > 0
    has_species = len(page.get('species', [])) > 0
    has_episodes = len(page.get('episodes', [])) > 0
    
    # Filter requested types based on appropriateness
    for q_type in requested_types:
        if q_type == 'what':
            # "What" questions for things, concepts, classes - NOT characters
            if not is_character:
                appropriate_types.append(q_type)
        elif q_type == 'who':
            # "Who" questions for characters
            if is_character:
                appropriate_types.append(q_type)
        elif q_type == 'where':
            # "Where" questions for locations
            if has_locations or 'location' in page_title or 'born' in fact.get('type', ''):
                appropriate_types.append(q_type)
        elif q_type == 'when':
            # "When" questions for dates
            if 'date' in fact.get('type', '') or 'born' in fact.get('type', ''):
                appropriate_types.append(q_type)
        elif q_type == 'which':
            # "Which" questions for episodes/series
            if has_episodes or 'episode' in page_title:
                appropriate_types.append(q_type)
    
    # If no appropriate types found, use intelligent defaults
    if not appropriate_types:
        if is_character:
            appropriate_types = ['who']  # Characters get 'who'
        else:
            appropriate_types = ['what']  # Everything else gets 'what'
    
    return appropriate_types

def generate_question_from_fact(
    fact: Dict,
    page: Dict,
    question_type: str = 'what'
) -> Optional[Dict]:
    """
    Generate a question from a fact using templates.
    
    Args:
        fact: Fact dictionary with subject, predicate, etc.
        page: Page object with metadata
        question_type: Type of question ('what', 'who', 'where', 'which')
    
    Returns:
        Question dictionary or None if generation fails
    """
    if question_type not in QUESTION_TEMPLATES:
        return None
    
    # Get primary series
    series = page.get('series', ['Star Trek'])
    primary_series = series[0] if series else 'Star Trek'
    
    # Get subject (use page title - ensures question is about the page)
    subject = page.get('title', fact.get('subject', 'Unknown'))
    
    # Select template - use fact type to choose appropriate template
    templates = QUESTION_TEMPLATES.get(question_type, QUESTION_TEMPLATES['what'])
    fact_type = fact.get('type', '')
    relationship = fact.get('relationship', '')
    
    # Map fact types to specific templates
    template_index = 0
    if fact_type == 'relationship' and relationship:
        # Use relationship-specific template if available
        if question_type == 'who' and len(templates) > 2:
            # Try to find relationship template
            template_index = 2  # "Who was X's Y?"
        else:
            template_index = 0
    elif fact_type == 'class':
        template_index = 0  # "What is the class of X?"
    elif fact_type == 'name':
        template_index = 1  # "What is the name of X?"
    elif fact_type == 'date' or fact_type == 'born':
        if question_type == 'when':
            template_index = 0  # "When is X?"
        elif question_type == 'where':
            template_index = 0  # "Where was X born?"
        else:
            template_index = 0
    else:
        # Random selection for variety
        template_index = random.randint(0, len(templates) - 1)
    
    template = templates[template_index]
    
    # Generate question - handle relationship templates specially
    try:
        if relationship and '{relationship}' in template:
            question = template.format(subject=subject, relationship=relationship, series=primary_series)
        else:
            question = template.format(subject=subject, series=primary_series)
    except KeyError:
        # Fallback if template format fails
        try:
            question = template.format(subject=subject)
        except KeyError:
            return None
    
    # Extract answer from fact
    answer = fact.get('predicate', '').strip()
    if not answer:
        return None
    
    # For specific facts, answers are already concise - skip validation
    # For narrative facts, validate answer completeness
    if fact.get('type') not in ['relationship', 'class', 'name', 'date', 'born']:
        if not validate_answer(answer):
            return None
    else:
        # Ensure specific fact answers are reasonable length
        if len(answer) > 60:
            answer = answer[:60].rsplit(' ', 1)[0]  # Truncate at word boundary
    
    return {
        'question': question,
        'answer': answer,
        'source_page': page.get('title'),
        'series': series,
        'tags': {
            'character': page.get('characters', [])[:3],  # Top 3 characters
            'species': page.get('species', [])[:2],
            'location': page.get('locations', [])[:2],
            'organization': page.get('organizations', [])[:2],
            'concept': page.get('concepts', [])[:2],
            'episode': page.get('episodes', [])[:2],
        },
        'question_type': question_type,
        'content_snippet': page.get('content_snippet', '')[:200],
        'fact_text': fact.get('text', '')
    }

def generate_questions_from_page(
    page: Dict,
    question_types: List[str] = ['what'],
    max_questions: int = 5,
    focus_tags: Optional[Dict] = None
) -> List[Dict]:
    """
    Generate multiple questions from a single page.
    
    Args:
        page: Page object
        question_types: List of question types to generate
        max_questions: Maximum number of questions to generate
    
    Returns:
        List of question dictionaries
    """
    questions = []
    
    # Extract facts from content
    full_text = page.get('full_text', '')
    if not full_text:
        return questions
    
    facts = extract_facts_from_content(full_text, page, focus_tags=focus_tags)
    
    if not facts:
        return questions
    
    # Generate questions from facts - select appropriate question types per fact
    for fact in facts:
        if len(questions) >= max_questions:
            break
        
        # Select appropriate question types for this fact
        appropriate_types = select_appropriate_question_types(page, fact, question_types)
        
        for q_type in appropriate_types:
            if len(questions) >= max_questions:
                break
            question = generate_question_from_fact(fact, page, q_type)
            if question:
                # Avoid duplicate questions (same question text)
                if not any(q['question'] == question['question'] for q in questions):
                    questions.append(question)
    
    return questions

def generate_questions_from_pages(
    pages: List[Dict],
    question_types: List[str] = ['what'],
    max_questions_per_page: int = 3,
    max_total_questions: int = 10,
    focus_tags: Optional[Dict] = None
) -> List[Dict]:
    """
    Generate questions from multiple pages.
    
    Args:
        pages: List of page objects
        question_types: List of question types to generate
        max_questions_per_page: Maximum questions per page
        max_total_questions: Maximum total questions to generate
    
    Returns:
        List of question dictionaries
    """
    all_questions = []
    
    for page in pages:
        if len(all_questions) >= max_total_questions:
            break
        
        questions = generate_questions_from_page(
            page,
            question_types=question_types,
            max_questions=max_questions_per_page,
            focus_tags=focus_tags
        )
        
        all_questions.extend(questions)
    
    return all_questions[:max_total_questions]

