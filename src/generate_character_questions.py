#!/usr/bin/env python3
"""
Generate trivia questions from structured character JSON files.

Works with the new character JSON format (rom_example.json structure) that includes:
- Timeline events with content_type, series, episode
- Appearances by series
- Quotes with episode sources
- Family relationships
- Character attributes
"""

import json
import re
import random
from typing import Dict, List, Optional, Tuple
from pathlib import Path


def clean_text(text: str) -> str:
    """Clean text for use in questions/answers."""
    if not text:
        return ""
    # Remove MediaWiki templates like {{DS9|Episode}}
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    # Remove MediaWiki image references (thumb|, etc.)
    text = re.sub(r'thumb\|[^|]+\|', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*thumb\s*\|', '', text, flags=re.IGNORECASE)
    # Remove HTML entities
    text = text.replace('&ndash;', '-').replace('&mdash;', '-').replace('&hellip;', '...')
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing punctuation
    text = text.strip('.,;:')
    return text.strip()


def remove_redundant_character_name(text: str, char_name: str) -> str:
    """Remove redundant character name from the start of event text."""
    if not text or not char_name:
        return text
    
    char_lower = char_name.lower()
    text_lower = text.lower()
    
    # Pattern: "Nechayev had..." when character is "Alynna Nechayev"
    # Remove if text starts with character's last name or full name
    patterns = [
        rf'^{re.escape(char_lower)}\s+',  # Full name at start
        rf'^{re.escape(char_name.split()[-1].lower())}\s+',  # Last name at start
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()


def extract_action_phrase(event_text: str, char_name: str) -> Optional[str]:
    """
    Extract a grammatically correct action phrase from event text for use in "did" questions.
    Returns None if event doesn't work well as a "did" question.
    """
    if not event_text or not char_name:
        return None
    
    # Clean the text
    text = clean_text(event_text)
    
    # Remove redundant character name
    text = remove_redundant_character_name(text, char_name)
    
    # Skip if it still starts with character name (redundant)
    if text.lower().startswith(char_name.lower()):
        return None
    
    # Skip if it contains MediaWiki artifacts
    if re.search(r'thumb\||\[\[.*?\]\]|\{\{.*?\}\}', text, re.I):
        return None
    
    # Skip if it's a full complex sentence (starts with "In 2369," or "During this year,")
    if re.match(r'^(In \d{4}|During|Later|After|Before|When|While)', text, re.I):
        # These are better as "What happened" questions, not "did" questions
        return None
    
    # Skip if it's too long (likely a full paragraph)
    if len(text) > 200:
        return None
    
    # Extract key action - look for main verb
    # Common patterns:
    # "had a fondness" -> "have a fondness"
    # "was promoted" -> "get promoted" or skip (passive)
    # "paid a visit" -> "pay a visit"
    # "ordered Picard" -> "order Picard"
    
    # Convert common past tense patterns to infinitive for "did" questions
    conversions = [
        (r'\bhad\s+', 'have '),
        (r'\bwas\s+', 'be '),  # But passive voice is awkward, might skip
        (r'\bwere\s+', 'be '),
        (r'\bpaid\s+', 'pay '),
        (r'\bordered\s+', 'order '),
        (r'\bvisited\s+', 'visit '),
        (r'\bassigned\s+', 'assign '),
        (r'\bauthorized\s+', 'authorize '),
        (r'\brequested\s+', 'request '),
        (r'\bcommanded\s+', 'command '),
        (r'\bplayed\s+', 'play '),
        (r'\boversaw\s+', 'oversee '),
        (r'\bunderstood\s+', 'understand '),
        (r'\bsympathized\s+', 'sympathize '),
        (r'\bcommitted\s+', 'commit '),
        (r'\bpreserving\s+', 'preserve '),
    ]
    
    # Try to find a good action phrase (first 3-5 words that form a verb phrase)
    words = text.split()
    
    # Skip if starts with passive voice or complex constructions
    if words[0].lower() in ['the', 'a', 'an', 'this', 'that', 'these', 'those']:
        return None
    
    # Find the main verb (usually in first few words)
    action_words = []
    found_verb = False
    
    for i, word in enumerate(words[:8]):  # Look at first 8 words
        word_lower = word.lower().strip('.,;:')
        if not word_lower:
            continue
        
        # Check if it's a verb (simple heuristic)
        if word_lower in ['had', 'was', 'were', 'did', 'paid', 'ordered', 'visited', 
                          'assigned', 'authorized', 'requested', 'commanded', 'played',
                          'oversaw', 'understood', 'sympathized', 'committed', 'became',
                          'received', 'gave', 'took', 'made', 'got', 'went', 'came']:
            found_verb = True
        
        action_words.append(word)
        
        # Stop after verb + object (roughly 3-5 words)
        if found_verb and i >= 2 and len(action_words) >= 4:
            break
    
    if not action_words:
        return None
    
    action_phrase = ' '.join(action_words)
    
    # Apply verb conversions
    for pattern, replacement in conversions:
        action_phrase = re.sub(pattern, replacement, action_phrase, flags=re.I)
    
    # Clean up
    action_phrase = action_phrase.strip('.,;:').strip()
    
    # Skip if too short or too long
    if len(action_phrase) < 5 or len(action_phrase) > 80:
        return None
    
    # Skip if it's clearly not an action (starts with articles, prepositions)
    if action_phrase.lower().startswith(('the ', 'a ', 'an ', 'in ', 'on ', 'at ', 'to ', 'for ')):
        return None
    
    return action_phrase


def extract_event_summary(event_text: str, max_length: int = 300) -> str:
    """Extract a concise summary from an event description for "What happened" questions."""
    # Remove section headers like "===USS Enterprise-D==="
    text = re.sub(r'===.*?===', '', event_text)
    # Remove MediaWiki templates and artifacts
    text = clean_text(text)
    
    # Remove redundant character names at start
    # (We'll pass char_name separately when needed)
    
    # Try to get complete sentences up to max_length
    sentences = text.split('.')
    result = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # Add period back (except for last sentence if we're truncating)
        sentence_with_period = sentence + '.'
        if current_length + len(sentence_with_period) <= max_length:
            result.append(sentence)
            current_length += len(sentence_with_period)
        else:
            # If this is the first sentence and it's too long, truncate it
            if not result:
                if len(sentence) > max_length:
                    truncated = sentence[:max_length]
                    last_space = truncated.rfind(' ')
                    if last_space > max_length * 0.7:
                        return truncated[:last_space].strip() + "..."
                    return truncated.strip() + "..."
            break
    
    if result:
        return '. '.join(result) + '.'
    
    # Fallback: truncate at word boundary if no sentences found
    if len(text) > max_length:
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:
            return truncated[:last_space].strip() + "..."
        return truncated.strip() + "..."
    
    return text.strip()


def generate_timeline_questions(character: Dict, timeline_sections: Dict) -> List[Dict]:
    """Generate questions from timeline events."""
    questions = []
    char_name = character.get('name', '')
    
    for section_name, events in timeline_sections.items():
        if not isinstance(events, list):
            continue
            
        for event in events:
            if not isinstance(event, dict):
                continue
                
            content_type = event.get('content_type', '')
            event_text = event.get('event') or event.get('background') or event.get('relationship', '')
            series = event.get('series', '')
            episode = event.get('episode', '')
            
            if not event_text:
                continue
            
            # Clean event text
            event_text = clean_text(event_text)
            if len(event_text) < 20:  # Skip very short events
                continue
            
            # Skip events with MediaWiki artifacts that weren't cleaned
            if re.search(r'thumb\||\[\[.*?\]\]|\{\{[^}]*thumb', event_text, re.I):
                continue
            
            # Question type 1: "In which episode did [character] [action]?"
            # Only generate if we can extract a good action phrase
            if episode and series:
                action_phrase = extract_action_phrase(event_text, char_name)
                if action_phrase:
                    # Ensure action phrase starts with lowercase for "did" questions
                    action_phrase = action_phrase[0].lower() + action_phrase[1:] if action_phrase else action_phrase
                    questions.append({
                        'question': f"In which episode did {char_name} {action_phrase}?",
                        'answer': episode,
                        'series': series,
                        'character': char_name,
                        'type': 'when',
                        'source': 'timeline_event',
                        'difficulty': 'medium'
                    })
            
            # Question type 2: "What happened to [character] in [episode]?"
            # This works better for complex/full sentences
            if episode and series and content_type == 'event':
                # Clean and remove redundant character name for answer
                event_summary = extract_event_summary(event_text, 300)
                # Remove character name from start if redundant
                event_summary = remove_redundant_character_name(event_summary, char_name)
                
                # Also remove character name if it appears later in the sentence as subject
                # Only replace when it's clearly the subject (followed by verb), not in phrases
                char_last_name = char_name.split()[-1].lower()
                char_full_name_lower = char_name.lower()
                
                # Detect gender from context (look for pronouns in the original text)
                original_text_lower = event_text.lower()
                has_female_pronouns = any(pronoun in original_text_lower[:150] for pronoun in [' she ', ' her ', ' hers '])
                has_male_pronouns = any(pronoun in original_text_lower[:150] for pronoun in [' he ', ' his ', ' him '])
                
                # Default to 'she' if female pronouns found, otherwise 'he'
                pronoun = 'she' if has_female_pronouns or (not has_male_pronouns and ('she' in original_text_lower[:150] or 'her' in original_text_lower[:150])) else 'he'
                
                # Only replace when character name is subject (followed by verb like "was", "had", "ordered", etc.)
                # Pattern: "Nechayev was" or "Einstein had" -> "she was" or "he had"
                subject_verbs = ['was', 'were', 'had', 'ordered', 'paid', 'visited', 'assigned', 'authorized', 
                                'requested', 'commanded', 'played', 'oversaw', 'became', 'received', 'gave', 
                                'took', 'made', 'got', 'went', 'came', 'did', 'created', 'used']
                
                for verb in subject_verbs:
                    # Replace "Lastname verb" with "pronoun verb"
                    pattern = rf'\b{re.escape(char_last_name)}\s+{re.escape(verb)}\b'
                    if re.search(pattern, event_summary, re.I):
                        event_summary = re.sub(pattern, f'{pronoun} {verb}', event_summary, flags=re.I, count=1)
                        break
                
                # Also handle full name as subject
                for verb in subject_verbs:
                    pattern = rf'\b{re.escape(char_full_name_lower)}\s+{re.escape(verb)}\b'
                    if re.search(pattern, event_summary, re.I):
                        event_summary = re.sub(pattern, f'{pronoun} {verb}', event_summary, flags=re.I, count=1)
                        break
                
                # Capitalize first letter if needed
                if event_summary and event_summary[0].islower():
                    event_summary = event_summary[0].upper() + event_summary[1:]
                
                # Skip if summary is too short or contains artifacts
                if len(event_summary) >= 20 and not re.search(r'thumb\||\[\[', event_summary, re.I):
                    questions.append({
                        'question': f"What happened to {char_name} in \"{episode}\"?",
                        'answer': event_summary,
                        'series': series,
                        'character': char_name,
                        'type': 'what',
                        'source': 'timeline_event',
                        'difficulty': 'hard'
                    })
            
            # Question type 3: "Which series featured [character] [action]?"
            # Only if we have a good action phrase
            if series and not episode:
                action_phrase = extract_action_phrase(event_text, char_name)
                if action_phrase:
                    action_phrase = action_phrase[0].lower() + action_phrase[1:] if action_phrase else action_phrase
                    questions.append({
                        'question': f"Which series featured {char_name} {action_phrase}?",
                        'answer': series,
                        'character': char_name,
                        'type': 'which',
                        'source': 'timeline_event',
                        'difficulty': 'medium'
                    })
    
    return questions


def generate_appearance_questions(character: Dict, appearances: Dict) -> List[Dict]:
    """Generate questions from character appearances."""
    questions = []
    char_name = character.get('name', '')
    
    if not appearances:
        return questions
    
    # Question type 1: "In which series did [character] appear?"
    series_list = list(appearances.keys())
    if len(series_list) > 0:
        questions.append({
            'question': f"In which series did {char_name} appear?",
            'answer': ', '.join(series_list),
            'character': char_name,
            'type': 'which',
            'source': 'appearances',
            'difficulty': 'easy'
        })
    
    # Question type 2: "How many episodes of [series] did [character] appear in?"
    for series, episodes in appearances.items():
        if isinstance(episodes, list) and len(episodes) > 0:
            questions.append({
                'question': f"How many episodes of {series} did {char_name} appear in?",
                'answer': str(len(episodes)),
                'series': series,
                'character': char_name,
                'type': 'how_many',
                'source': 'appearances',
                'difficulty': 'medium'
            })
            
            # Question type 3: "Which episode of [series] featured [character]?"
            if len(episodes) == 1:
                questions.append({
                    'question': f"Which episode of {series} featured {char_name}?",
                    'answer': episodes[0],
                    'series': series,
                    'character': char_name,
                    'type': 'which',
                    'source': 'appearances',
                    'difficulty': 'easy'
                })
    
    return questions


def clean_quote_source(source: str) -> str:
    """Clean quote source to extract character name."""
    if not source:
        return ""
    # Remove MediaWiki templates and formatting
    source = re.sub(r'\'\'\'|''', '', source)  # Remove bold markers
    source = re.sub(r'{{[^}]+}}', '', source)  # Remove templates
    source = re.sub(r'\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]', r'\1', source)  # Extract link text
    # Extract character name (usually first part before comma or "as" or "reciting")
    source = source.split(',')[0].split(' as ')[0].split(' reciting')[0].strip()
    return source


def generate_quote_questions(character: Dict) -> List[Dict]:
    """Generate questions from character quotes."""
    questions = []
    char_name = character.get('name', '')
    quote = character.get('quote')
    
    if not quote or not isinstance(quote, dict):
        return questions
    
    quote_text = quote.get('text', '')
    quote_source = quote.get('source', '')
    episode = quote.get('episode', '')
    
    if not quote_text:
        return questions
    
    # Clean quote text
    quote_text = clean_text(quote_text)
    if len(quote_text) < 10:
        return questions
    
    # Extract actual speaker from source
    speaker = clean_quote_source(quote_source) if quote_source else None
    
    # Skip if quote source is unclear or if character name appears in quote text
    # (indicating quote is ABOUT the character, not BY them)
    if not speaker or char_name.lower() in quote_text.lower():
        # Only generate episode question if we have episode info
        if episode:
            questions.append({
                'question': f"In which episode was the quote \"{quote_text[:100]}...\" said?",
                'answer': episode,
                'character': char_name,
                'type': 'when',
                'source': 'quote',
                'difficulty': 'hard',
                'quote_text': quote_text
            })
        return questions
    
    # Truncate long quotes for questions
    display_quote = quote_text[:150] + "..." if len(quote_text) > 150 else quote_text
    
    # Question type 1: "Who said '[quote]'?" (use actual speaker from source)
    questions.append({
        'question': f"Who said \"{display_quote}\"?",
        'answer': speaker,
        'episode': episode,
        'character': char_name,
        'type': 'who',
        'source': 'quote',
        'difficulty': 'medium',
        'quote_text': quote_text,
        'verified': True
    })
    
    # Question type 2: "In which episode did [speaker] say '[quote]'?"
    if episode and speaker:
        questions.append({
            'question': f"In which episode did {speaker} say \"{display_quote}\"?",
            'answer': episode,
            'character': char_name,
            'type': 'when',
            'source': 'quote',
            'difficulty': 'hard',
            'quote_text': quote_text,
            'verified': True
        })
    
    return questions


def generate_family_questions(character: Dict) -> List[Dict]:
    """Generate questions from family relationships."""
    questions = []
    char_name = character.get('name', '')
    
    # Father
    father = character.get('father')
    if father:
        questions.append({
            'question': f"Who was {char_name}'s father?",
            'answer': father,
            'character': char_name,
            'type': 'who',
            'source': 'family',
            'difficulty': 'medium'
        })
    
    # Mother
    mother = character.get('mother')
    if mother:
        questions.append({
            'question': f"Who was {char_name}'s mother?",
            'answer': mother,
            'character': char_name,
            'type': 'who',
            'source': 'family',
            'difficulty': 'medium'
        })
    
    # Siblings
    siblings = character.get('siblings', [])
    if siblings and isinstance(siblings, list) and len(siblings) > 0:
        sibling_names = [s if isinstance(s, str) else s.get('name', str(s)) for s in siblings]
        questions.append({
            'question': f"Who were {char_name}'s siblings?",
            'answer': ', '.join(sibling_names),
            'character': char_name,
            'type': 'who',
            'source': 'family',
            'difficulty': 'medium'
        })
    
    # Spouses
    spouses = character.get('spouses', [])
    if spouses and isinstance(spouses, list) and len(spouses) > 0:
        spouse_names = [s if isinstance(s, str) else s.get('name', str(s)) for s in spouses]
        questions.append({
            'question': f"Who was {char_name} married to?",
            'answer': ', '.join(spouse_names),
            'character': char_name,
            'type': 'who',
            'source': 'family',
            'difficulty': 'medium'
        })
    
    # Children
    children = character.get('children', [])
    if children and isinstance(children, list) and len(children) > 0:
        child_names = [c if isinstance(c, str) else c.get('name', str(c)) for c in children]
        questions.append({
            'question': f"Who were {char_name}'s children?",
            'answer': ', '.join(child_names),
            'character': char_name,
            'type': 'who',
            'source': 'family',
            'difficulty': 'medium'
        })
    
    return questions


def generate_attribute_questions(character: Dict) -> List[Dict]:
    """Generate questions from character attributes."""
    questions = []
    char_name = character.get('name', '')
    
    # Species
    species = character.get('species')
    if species:
        questions.append({
            'question': f"What species was {char_name}?",
            'answer': species,
            'character': char_name,
            'type': 'what',
            'source': 'attribute',
            'difficulty': 'easy'
        })
    
    # Rank
    rank = character.get('rank')
    if rank:
        questions.append({
            'question': f"What was {char_name}'s rank?",
            'answer': rank,
            'character': char_name,
            'type': 'what',
            'source': 'attribute',
            'difficulty': 'easy'
        })
    
    # Occupation
    occupation = character.get('occupation')
    if occupation:
        questions.append({
            'question': f"What was {char_name}'s occupation?",
            'answer': occupation,
            'character': char_name,
            'type': 'what',
            'source': 'attribute',
            'difficulty': 'easy'
        })
    
    # Born year
    born = character.get('born', {})
    if isinstance(born, dict):
        year = born.get('year')
        if year:
            questions.append({
                'question': f"When was {char_name} born?",
                'answer': str(year),
                'character': char_name,
                'type': 'when',
                'source': 'attribute',
                'difficulty': 'medium'
            })
    
    # Actor
    played_by = character.get('played_by')
    if played_by:
        questions.append({
            'question': f"Who played {char_name}?",
            'answer': played_by,
            'character': char_name,
            'type': 'who',
            'source': 'attribute',
            'difficulty': 'easy'
        })
    
    return questions


def verify_question(question: Dict, character_data: Dict) -> Dict:
    """
    Verify a question's answer against the source character JSON.
    Adds verification metadata to the question.
    """
    question = question.copy()  # Don't modify original
    question['verified'] = False
    question['verification_notes'] = []
    
    source = question.get('source', '')
    answer = question.get('answer', '')
    char_name = question.get('character', '')
    character = character_data.get('character', {})
    
    # Verify based on source type
    if source == 'quote':
        quote = character.get('quote', {})
        if isinstance(quote, dict):
            # If it's a "who said" question, verify the speaker
            if question.get('type') == 'who':
                quote_source = quote.get('source', '')
                cleaned_source = clean_quote_source(quote_source)
                if cleaned_source and answer.lower() in cleaned_source.lower():
                    question['verified'] = True
                elif not cleaned_source:
                    question['verification_notes'].append('Quote source unclear in JSON')
            # If it's a "when/episode" question, verify the episode
            elif question.get('type') == 'when':
                quote_episode = quote.get('episode', '')
                if quote_episode and answer.lower() in quote_episode.lower():
                    question['verified'] = True
    
    elif source == 'family':
        # Verify family relationships
        relationship_type = None
        if "father" in question['question'].lower():
            relationship_type = 'father'
        elif "mother" in question['question'].lower():
            relationship_type = 'mother'
        elif "siblings" in question['question'].lower():
            relationship_type = 'siblings'
        elif "married" in question['question'].lower() or "spouse" in question['question'].lower():
            relationship_type = 'spouses'
        elif "children" in question['question'].lower():
            relationship_type = 'children'
        
        if relationship_type:
            json_value = character.get(relationship_type)
            if json_value:
                if isinstance(json_value, list):
                    json_answers = [str(v) if isinstance(v, str) else str(v.get('name', v)) for v in json_value]
                    # First, try exact match with comma-separated answer
                    json_answer_str = ', '.join(json_answers)
                    if answer.lower() == json_answer_str.lower():
                        question['verified'] = True
                    # Handle comma-separated answers (e.g., "Sidney La Forge, Bret La Forge")
                    # But be careful - some names contain commas (e.g., "Duras, son of Ja'rod")
                    answer_list = [a.strip() for a in answer.split(',')]
                    json_list_lower = [ja.lower() for ja in json_answers]
                    answer_list_lower = [a.lower() for a in answer_list]
                    
                    # Check if all names in answer are in JSON list (fuzzy match)
                    # This handles cases where answer might be split differently
                    if len(answer_list) == len(json_answers):
                        # Try to match each answer item to a JSON item
                        matched = [False] * len(json_answers)
                        for a in answer_list_lower:
                            for i, ja in enumerate(json_list_lower):
                                if not matched[i] and (a in ja or ja in a or a == ja):
                                    matched[i] = True
                                    break
                        if all(matched):
                            question['verified'] = True
                    # Also check if answer matches any single item (for single-answer questions)
                    elif answer in json_answers or any(answer.lower() == str(a).lower() for a in json_answers):
                        question['verified'] = True
                elif isinstance(json_value, str):
                    if answer.lower() in json_value.lower() or json_value.lower() in answer.lower():
                        question['verified'] = True
    
    elif source == 'attribute':
        # Verify attributes
        attr_type = None
        if "species" in question['question'].lower():
            attr_type = 'species'
        elif "rank" in question['question'].lower():
            attr_type = 'rank'
        elif "occupation" in question['question'].lower():
            attr_type = 'occupation'
        elif "born" in question['question'].lower():
            attr_type = 'born'
        elif "played" in question['question'].lower():
            attr_type = 'played_by'
        
        if attr_type:
            if attr_type == 'born':
                born = character.get('born', {})
                if isinstance(born, dict):
                    year = born.get('year')
                    if year and str(year) == answer:
                        question['verified'] = True
            else:
                json_value = character.get(attr_type)
                if json_value and answer.lower() in str(json_value).lower():
                    question['verified'] = True
    
    elif source == 'appearances':
        # Verify appearances
        appearances = character_data.get('appearances', {})
        series = question.get('series')
        if series and series in appearances:
            episodes = appearances[series]
            if isinstance(episodes, list):
                if question.get('type') == 'how_many':
                    if str(len(episodes)) == answer:
                        question['verified'] = True
                elif question.get('type') == 'which':
                    if answer in episodes:
                        question['verified'] = True
        # Handle "which series" questions (no specific series, asking for all series)
        elif question.get('type') == 'which' and 'series' in question.get('question', '').lower() and not series:
            # Answer is comma-separated list of series like "TNG, DS9, VOY"
            answer_series = [s.strip() for s in answer.split(',')]
            json_series = list(appearances.keys())
            # Check if all series in answer are in JSON
            if all(s in json_series for s in answer_series) and len(answer_series) == len(json_series):
                question['verified'] = True
    
    elif source == 'timeline_event':
        # Verify timeline events are present
        question['verified'] = True  # Timeline events are already from the JSON
    
    return question


def generate_questions_from_character(character_data: Dict, verify: bool = True) -> List[Dict]:
    """Generate all questions from a character JSON structure."""
    questions = []
    
    character = character_data.get('character', {})
    if not character:
        return questions
    
    char_name = character.get('name', '')
    if not char_name:
        return questions
    
    # Get timeline sections (everything except 'character' and 'appearances')
    timeline_sections = {
        k: v for k, v in character_data.items() 
        if k not in ['character', 'appearances']
    }
    
    # Get appearances
    appearances = character_data.get('appearances', {})
    
    # Generate questions from each source
    questions.extend(generate_timeline_questions(character, timeline_sections))
    questions.extend(generate_appearance_questions(character, appearances))
    questions.extend(generate_quote_questions(character))
    questions.extend(generate_family_questions(character))
    questions.extend(generate_attribute_questions(character))
    
    # Verify questions if requested
    if verify:
        questions = [verify_question(q, character_data) for q in questions]
    
    return questions


def load_character_file(filepath: Path) -> Optional[Dict]:
    """Load a character JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def generate_questions_from_directory(directory: Path, limit: Optional[int] = None, verify: bool = True) -> List[Dict]:
    """Generate questions from all character JSON files in a directory."""
    all_questions = []
    
    json_files = list(directory.glob("*.json"))
    json_files = [f for f in json_files if f.name != "bulk_extraction_checkpoint.json"]
    
    if limit:
        json_files = json_files[:limit]
    
    print(f"Processing {len(json_files)} character files...")
    
    verified_count = 0
    unverified_count = 0
    
    for i, json_file in enumerate(json_files, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(json_files)} files...")
        
        character_data = load_character_file(json_file)
        if not character_data:
            continue
        
        questions = generate_questions_from_character(character_data, verify=verify)
        for q in questions:
            if q.get('verified'):
                verified_count += 1
            else:
                unverified_count += 1
        all_questions.extend(questions)
    
    print(f"Generated {len(all_questions)} questions from {len(json_files)} characters")
    if verify:
        print(f"  Verified: {verified_count}, Unverified: {unverified_count}")
    return all_questions


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Generate trivia questions from character JSON files")
    parser.add_argument("input", help="Character JSON file or directory containing character JSONs")
    parser.add_argument("-o", "--output", help="Output JSON file for questions")
    parser.add_argument("--limit", type=int, help="Limit number of character files to process")
    parser.add_argument("--series", help="Filter questions by series (TNG, DS9, VOY, etc.)")
    parser.add_argument("--character", help="Filter questions by character name")
    parser.add_argument("--difficulty", choices=['easy', 'medium', 'hard'], help="Filter by difficulty")
    parser.add_argument("--no-verify", action="store_true", help="Skip verification of answers against JSON")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    verify = not args.no_verify
    
    # Load character(s) and generate questions
    if input_path.is_file():
        character_data = load_character_file(input_path)
        if not character_data:
            sys.exit(1)
        questions = generate_questions_from_character(character_data, verify=verify)
    elif input_path.is_dir():
        questions = generate_questions_from_directory(input_path, limit=args.limit, verify=verify)
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        sys.exit(1)
    
    # Apply filters
    if args.series:
        questions = [q for q in questions if q.get('series') == args.series]
    
    if args.character:
        questions = [q for q in questions if q.get('character', '').lower() == args.character.lower()]
    
    if args.difficulty:
        questions = [q for q in questions if q.get('difficulty') == args.difficulty]
    
    # Optionally filter to only verified questions
    if verify:
        verified_questions = [q for q in questions if q.get('verified', False)]
        if len(verified_questions) < len(questions):
            print(f"Note: {len(questions) - len(verified_questions)} questions could not be verified")
    
    # Output results
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(questions)} questions to {output_path}")
    else:
        # Print sample questions
        print(f"\nGenerated {len(questions)} questions")
        print("\nSample questions:")
        for q in random.sample(questions, min(10, len(questions))):
            print(f"  Q: {q['question']}")
            print(f"  A: {q['answer']}")
            print(f"  (Type: {q['type']}, Difficulty: {q['difficulty']}, Source: {q['source']})")
            print()

