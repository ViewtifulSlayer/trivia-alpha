#!/usr/bin/env python3
"""
Learn from user corrections to improve question generation.
This script allows interactive correction of questions and builds a pattern library.
"""
import json
import re
from typing import Dict, List, Optional
from pathlib import Path

# Pattern library - stores learned patterns for better question generation
PATTERN_LIBRARY = {
    'fondness': {
        'pattern': r'fondness for (\w+)',
        'templates': [
            "Which episode of {series} showed {character}'s particular fondness for {item}?",
            "In which episode of {series} did {character} express a fondness for {item}?",
            "What was {character} shown to have a particular fondness for in \"{episode}\" of {series}?"
        ]
    },
    'preference': {
        'pattern': r'preference for (\w+)',
        'templates': [
            "Which episode of {series} revealed {character}'s preference for {item}?",
            "In \"{episode}\" of {series}, what preference did {character} express?"
        ]
    },
    # Add more patterns as we learn them
}

def extract_item_from_answer(answer: str, pattern_key: str) -> Optional[str]:
    """Extract the item (like 'Bularian canapés') from an answer."""
    if pattern_key in PATTERN_LIBRARY:
        pattern = PATTERN_LIBRARY[pattern_key]['pattern']
        match = re.search(pattern, answer, re.I)
        if match:
            return match.group(1)
    return None


def extract_contextual_item_from_event(character_file: str, episode: str, series: str) -> Optional[str]:
    """
    Extract the contextual item from the original event text in the character JSON.
    This is where the actual event description lives.
    """
    try:
        with open(character_file, 'r', encoding='utf-8') as f:
            char_data = json.load(f)
        
        # Look through timeline sections for the matching event
        timeline_sections = {
            'personal_life': char_data.get('personal_life', []),
            'career': char_data.get('career', []),
            'relationships': char_data.get('relationships', []),
            'other': char_data.get('other', []),
        }
        
        for section_name, events in timeline_sections.items():
            if not isinstance(events, list):
                continue
            
            for event in events:
                if not isinstance(event, dict):
                    continue
                
                event_episode = event.get('episode', '')
                event_series = event.get('series', '')
                event_text = event.get('event', '') or event.get('background', '') or event.get('relationship', '')
                
                # Match by episode and series
                if event_episode == episode and event_series == series and event_text:
                    # Look for patterns like "fondness for X"
                    patterns = [
                        r'fondness for ([^,\.]+)',
                        r'preference for ([^,\.]+)',
                        r'interest in ([^,\.]+)',
                        r'liking for ([^,\.]+)',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, event_text, re.I)
                        if match:
                            item = match.group(1).strip()
                            # Clean up common trailing words
                            item = re.sub(r'\s+(though|although|but|and|or).*$', '', item, flags=re.I)
                            return item
        
    except Exception as e:
        pass  # If we can't load the file, return None
    
    return None


def extract_contextual_item(answer: str, question_data: Dict) -> Optional[str]:
    """
    Extract the contextual item (like "Bularian canapés") from the answer or source data.
    This looks for patterns like "fondness for X", "preference for X", etc.
    """
    # First try the answer text (in case it contains the full event description)
    patterns = [
        r'fondness for ([^,\.]+)',
        r'preference for ([^,\.]+)',
        r'interest in ([^,\.]+)',
        r'liking for ([^,\.]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, answer, re.I)
        if match:
            item = match.group(1).strip()
            # Clean up common trailing words
            item = re.sub(r'\s+(though|although|but|and|or).*$', '', item, flags=re.I)
            return item
    
    # If not in answer, try to find the character file and extract from event text
    # This would require knowing the character file path, which we might not have
    # For now, return None and we'll extract from the corrected question itself
    
    return None


def apply_correction(original_question: str, corrected_question: str, 
                    question_data: Dict) -> Dict:
    """
    Analyze a correction and extract patterns to learn from.
    Returns a pattern that can be added to the library.
    """
    # Extract what changed
    original_lower = original_question.lower()
    corrected_lower = corrected_question.lower()
    
    # Identify the pattern
    learned_pattern = {
        'original_template': original_question,
        'corrected_template': corrected_question,
        'question_type': question_data.get('type', ''),
        'source': question_data.get('source', ''),
        'character': question_data.get('character', ''),
        'series': question_data.get('series', ''),
        'episode': question_data.get('episode', ''),
        'answer': question_data.get('answer', ''),
    }
    
    # Try to generalize the template
    # Replace specific values with placeholders
    char_name = question_data.get('character', '')
    series = question_data.get('series', '')
    episode = question_data.get('episode', '')
    
    template = corrected_question
    
    # First, extract contextual items that might contain character names
    # This needs to happen before character name replacement
    contextual_item = None
    item_pattern_type = None
    
    # Look for patterns in the corrected question (preliminary check)
    patterns_to_check = [
        (r'said that ([^?]+) was what\?', 'quote_what_question'),
        (r'said that ([^?]+)\?', 'quote_what_question'),
    ]
    
    for pattern, pattern_type in patterns_to_check:
        item_match = re.search(pattern, corrected_question, re.I)
        if item_match:
            contextual_item = item_match.group(1).strip()
            item_pattern_type = pattern_type
            break
    
    # If we found a quote/what question, replace the statement content first
    if item_pattern_type == 'quote_what_question' and contextual_item:
        template = template.replace(contextual_item, '{statement_content}')
    
    # Replace character name (after statement content replacement)
    if char_name:
        template = template.replace(char_name, '{character}')
        # Also handle possessive forms
        if char_name.endswith('s'):
            template = template.replace(char_name + "'s", "{character}'s")
        else:
            template = template.replace(char_name + "'s", "{character}'s")
    
    # Replace series (handle both abbreviations and full names)
    if series:
        template = template.replace(series, '{series}')
        # Also handle common series name mappings
        series_name_map = {
            'ENT': 'Enterprise',
            'TNG': 'The Next Generation',
            'TOS': 'The Original Series',
            'DS9': 'Deep Space Nine',
            'VOY': 'Voyager',
            'DIS': 'Discovery',
            'SNW': 'Strange New Worlds',
            'LD': 'Lower Decks',
            'PRO': 'Prodigy',
        }
        if series in series_name_map:
            full_name = series_name_map[series]
            template = template.replace(full_name, '{series_name}')
            learned_pattern['series_name_mapping'] = {series: full_name}
    
    # Replace episode
    if episode:
        template = template.replace(episode, '{episode}')
        # Also handle quoted episodes
        template = template.replace(f'"{episode}"', '"{episode}"')
    
    # Extract and replace contextual items (like "Bularian canapés", "Sir-Neighs-a-Lot")
    # The contextual item is specific to THIS event, not a general template
    # Extract it from the corrected question itself
    # (Skip if we already extracted quote_what_question above)
    if item_pattern_type != 'quote_what_question':
        contextual_item = None
        item_pattern_type = None
    
    # Look for patterns in the corrected question
    patterns_to_extract = [
        (r'fondness for ([^?]+)', 'fondness_for'),
        (r'preference for ([^?]+)', 'preference_for'),
        (r'interest in ([^?]+)', 'interest_in'),
        (r'liking for ([^?]+)', 'liking_for'),
        (r'this character was nicknamed "([^"]+)"', 'nickname_reverse_question'),  # "this character was nicknamed \"Often Wrong\""
        (r'this character was nicknamed ([^,]+),', 'nickname_reverse_question'),  # "this character was nicknamed X,"
        (r'pony, ([^?]+)', 'pony_name'),  # "pony, Sir-Neighs-a-Lot"
        (r'pony named ([^?]+)', 'pony_name'),  # "pony named X"
        (r'named ([^?]+)', 'named_item'),  # Generic "named X" (must come after nickname patterns)
        (r'born (sometime during the \d{4}s)', 'temporal_detail'),  # "born sometime during the 2360s"
        (r'born (in \d{4})', 'temporal_detail'),  # "born in 2367"
        (r'(\d{4}s)', 'temporal_detail'),  # Generic "2360s" as contextual detail
        (r'what task is ([^?]+) attempting to accomplish\?', 'task_question'),  # "what task is X attempting to accomplish?"
        (r'what is ([^?]+) attempting to (find|accomplish|do|solve)', 'task_question'),  # "what is X attempting to find?"
        (r'which crew member ([^?]+)\?', 'who_question'),  # "which crew member was infected..."
        (r'which character ([^?]+)\?', 'who_question'),  # "which character..."
        (r'which officer ([^?]+)\?', 'who_question'),  # "which officer..."
        (r'who ([^?]+)\?', 'who_question'),  # "who was..."
        (r'who was ([^?]+) successor', 'successor_question'),  # "who was his successor"
        (r'was the successor of which ([^?]+)\?', 'successor_question'),  # "was the successor of which officer?"
        (r'said that ([^?]+) was what\?', 'quote_what_question'),  # "said that X was what?"
        (r'said that ([^?]+)\?', 'quote_what_question'),  # "said that X?"
        (r'had a valued family heirloom in the form of this type of ([^,]+), called', 'detail_what_question'),  # "had a valued family heirloom in the form of this type of coin, called"
        (r'in the form of this type of ([^,]+), called', 'detail_what_question'),  # "in the form of this type of X, called"
        (r'called his "([^"]+)"', 'named_detail'),  # "called his \"lucky loonie\""
        (r'called his ([^?]+)\?', 'named_detail'),  # "called his lucky loonie?"
        (r'it is revealed that ([^?]+) had', 'revealed_detail_question'),  # "it is revealed that X had"
        (r'was instrumental in leading an elite team that exonerated this ([^?]+)\?', 'exoneration_question'),  # "was instrumental in leading an elite team that exonerated this falsely accused Captain"
        (r'exonerated this ([^?]+)\?', 'exoneration_question'),  # "exonerated this falsely accused Captain"
        (r'was referred to be this similar-sounding nickname', 'nickname_question'),  # "was referred to be this similar-sounding nickname"
        (r'was referred to by this ([^?]+)\?', 'nickname_question'),  # "was referred to by this nickname?"
        (r'was known by this ([^?]+)\?', 'nickname_question'),  # "was known by this nickname?"
        (r'this character was nicknamed "([^"]+)"', 'nickname_reverse_question'),  # "this character was nicknamed \"Often Wrong\""
        (r'this character was nicknamed ([^,]+),', 'nickname_reverse_question'),  # "this character was nicknamed X,"
    ]
    
    for pattern, pattern_type in patterns_to_extract:
        item_match = re.search(pattern, corrected_question, re.I)
        if item_match:
            # Some patterns don't have capture groups (like "was referred to be this similar-sounding nickname")
            if item_match.groups():
                contextual_item = item_match.group(1).strip()
                # Clean up trailing punctuation
                contextual_item = contextual_item.rstrip('?.,;')
            else:
                # Pattern matched but no capture group - use empty string or pattern-specific handling
                contextual_item = ""
            item_pattern_type = pattern_type
            break
    
    if contextual_item:
        # Replace the specific item with a placeholder
        # Be careful with replacements - use word boundaries to avoid partial matches
        # For temporal details, we might need to replace the whole phrase
        if item_pattern_type == 'temporal_detail':
            # Replace the temporal detail phrase
            template = template.replace(contextual_item, '{temporal_detail}')
            learned_pattern['contextual_item'] = contextual_item
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Temporal detail is specific to this event - must be extracted from source event text when applying template'
        elif item_pattern_type == 'task_question':
            # For task questions, the contextual item is the character being asked about
            # The actual task/answer comes from the event text
            # Replace the subject character with placeholder
            template = template.replace(contextual_item, '{subject_character}')
            learned_pattern['subject_character'] = contextual_item
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Task question - subject character may differ from question character. Task/answer must be extracted from source event text.'
        elif item_pattern_type == 'who_question':
            # For "who" questions, the contextual item is the event description
            # The answer is a character name
            # Replace the event description with placeholder
            template = template.replace(contextual_item, '{event_description}')
            learned_pattern['event_description'] = contextual_item
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Who question - event description must be extracted from source event text. Answer is a character name.'
            learned_pattern['answer_type'] = 'character'
            
            # Also replace any episode name that appears in the template (may differ from question_data episode)
            # Look for quoted episode names like 'Observer Effect'
            episode_match = re.search(r"'([^']+)'", template)
            if episode_match:
                # Replace the episode name found in quotes with placeholder
                # This handles cases where the corrected question uses a different episode than question_data
                found_episode = episode_match.group(1)
                template = template.replace(found_episode, '{episode}')
                if found_episode != episode:
                    learned_pattern['episode_note'] = f'Corrected question uses episode "{found_episode}" instead of question_data episode "{episode}"'
        elif item_pattern_type == 'successor_question':
            # For successor questions, the contextual item is the relationship/role description
            # The answer is a character name (the predecessor or successor)
            # Extract the role/relationship description
            # Pattern: "who was his successor in the role of overseeing the Enterprise"
            # or "was the successor of which officer"
            learned_pattern['relationship_description'] = contextual_item if contextual_item else 'successor relationship'
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Successor question - relationship description must be extracted from source event text. Answer is a character name.'
            learned_pattern['answer_type'] = 'character'
            
            # Look for successor character names in the template (like "Admiral Gardner")
            # Pattern: "Admiral Gardner was the successor"
            successor_match = re.search(r'(\w+\s+\w+)\s+was the successor', template, re.I)
            if successor_match:
                successor_name = successor_match.group(1)
                template = template.replace(successor_name, '{successor_character}')
                learned_pattern['successor_character'] = successor_name
            
            # Also replace any episode name that appears in the template
            episode_match = re.search(r"'([^']+)'", template)
            if not episode_match:
                # Try without quotes
                episode_match = re.search(r'episode\s+(\w+)', template, re.I)
            if episode_match:
                found_episode = episode_match.group(1)
                template = template.replace(found_episode, '{episode}')
                if found_episode != episode:
                    learned_pattern['episode_note'] = f'Corrected question uses episode "{found_episode}" instead of question_data episode "{episode}"'
        elif item_pattern_type == 'detail_what_question':
            # For detail/what questions, the contextual item is the detail being asked about
            # The answer is a specific detail (like "coin" or "loonie")
            # Replace the detail description with placeholder
            template = template.replace(contextual_item, '{detail_type}')
            learned_pattern['detail_type'] = contextual_item
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Detail/What question - detail type must be extracted from source event text. Answer is a specific detail.'
            learned_pattern['answer_type'] = 'detail'
            
            # Also look for named details like "called his lucky loonie"
            named_detail_match = re.search(r'called his "?([^"?]+)"?\?', template, re.I)
            if named_detail_match:
                named_detail = named_detail_match.group(1).strip()
                template = template.replace(named_detail, '{named_detail}')
                learned_pattern['named_detail'] = named_detail
            
            # Also replace any episode name that appears in the template
            episode_match = re.search(r"'([^']+)'", template)
            if not episode_match:
                episode_match = re.search(r'episode\s+(\w+)', template, re.I)
            if episode_match:
                found_episode = episode_match.group(1)
                template = template.replace(found_episode, '{episode}')
                if found_episode != episode:
                    learned_pattern['episode_note'] = f'Corrected question uses episode "{found_episode}" instead of question_data episode "{episode}"'
        elif item_pattern_type == 'named_detail':
            # For named detail questions, extract the name
            template = template.replace(contextual_item, '{named_detail}')
            learned_pattern['named_detail'] = contextual_item
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Named detail question - detail name must be extracted from source event text.'
            learned_pattern['answer_type'] = 'detail'
        elif item_pattern_type == 'revealed_detail_question':
            # For "it is revealed that" questions, extract the full statement
            # This is a complex question structure
            learned_pattern['revealed_statement'] = contextual_item
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Revealed detail question - full statement must be extracted from source event text. Answer is a specific detail.'
            learned_pattern['answer_type'] = 'detail'
            
            # Replace episode name
            episode_match = re.search(r"'([^']+)'", template)
            if not episode_match:
                episode_match = re.search(r'episode\s+(\w+)', template, re.I)
            if episode_match:
                found_episode = episode_match.group(1)
                template = template.replace(found_episode, '{episode}')
                if found_episode != episode:
                    learned_pattern['episode_note'] = f'Corrected question uses episode "{found_episode}" instead of question_data episode "{episode}"'
        elif item_pattern_type == 'exoneration_question':
            # For exoneration questions, the contextual item is the description of who was exonerated
            # The answer is a character name (the person who was exonerated)
            # Replace the description with placeholder
            template = template.replace(contextual_item, '{exonerated_description}')
            learned_pattern['exonerated_description'] = contextual_item
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Exoneration question - description of exonerated person must be extracted from source event text. Answer is a character name.'
            learned_pattern['answer_type'] = 'character'
            
            # Extract the character who did the exonerating (if mentioned)
            exoneration_match = re.search(r'(\w+\s+\w+)\s+was instrumental in leading', template, re.I)
            if exoneration_match:
                exoneration_character = exoneration_match.group(1)
                template = template.replace(exoneration_character, '{exoneration_character}')
                learned_pattern['exoneration_character'] = exoneration_character
        elif item_pattern_type == 'nickname_question':
            # For nickname questions, the contextual item is the description of the nickname
            # The answer is the nickname itself
            # Pattern: "was referred to be this similar-sounding nickname" -> answer is the nickname
            learned_pattern['nickname_description'] = contextual_item if contextual_item else 'nickname'
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Nickname question - nickname must be extracted from source event text. Answer is the nickname itself.'
            learned_pattern['answer_type'] = 'nickname'
            
            # Look for the nickname pattern in the template
            # The question structure might be: "was referred to be this similar-sounding nickname" -> answer is the nickname
            # We don't need to replace anything in the template since the nickname is the answer, not in the question
        elif item_pattern_type == 'nickname_reverse_question':
            # For reversed nickname questions, the nickname is in the question, answer is the character
            # Pattern: "this character was nicknamed 'Often Wrong'" -> answer is the character name
            # Replace the nickname with placeholder (just the nickname, not the full phrase)
            nickname_only = contextual_item.strip('",').split(',')[0].strip()  # Extract just "Often Wrong" from "Often Wrong," a play..."
            template = template.replace(contextual_item, '{nickname}')
            # Also replace just the nickname if it appears separately
            if nickname_only and nickname_only != contextual_item:
                template = template.replace(nickname_only, '{nickname}')
            learned_pattern['nickname'] = nickname_only if nickname_only else contextual_item
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Reversed nickname question - nickname is in question, answer is character name. Easier difficulty than asking for nickname.'
            learned_pattern['answer_type'] = 'character'
            learned_pattern['difficulty'] = 'easy'
        elif item_pattern_type == 'quote_what_question':
            # For quote/what questions, the contextual item is what was said/asked about
            # The answer is a specific detail from the quote/statement
            # Replace the statement content with placeholder
            template = template.replace(contextual_item, '{statement_content}')
            learned_pattern['statement_content'] = contextual_item
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Quote/What question - statement content must be extracted from source event text. Answer is a specific detail from the statement.'
            learned_pattern['answer_type'] = 'detail'
            
            # Also replace any episode name that appears in the template
            episode_match = re.search(r"'([^']+)'", template)
            if episode_match:
                found_episode = episode_match.group(1)
                template = template.replace(found_episode, '{episode}')
                if found_episode != episode:
                    learned_pattern['episode_note'] = f'Corrected question uses episode "{found_episode}" instead of question_data episode "{episode}"'
        else:
            template = template.replace(contextual_item, '{item}')
            learned_pattern['contextual_item'] = contextual_item
            learned_pattern['item_pattern'] = item_pattern_type
            learned_pattern['note'] = 'Contextual item is specific to this event - must be extracted from source event text when applying template'
    
    learned_pattern['generalized_template'] = template
    
    return learned_pattern


def save_correction(correction: Dict, corrections_file: str = "data/question_corrections.json"):
    """Save a correction to the corrections file."""
    corrections_file_path = Path(corrections_file)
    
    if corrections_file_path.exists():
        with open(corrections_file_path, 'r', encoding='utf-8') as f:
            corrections = json.load(f)
    else:
        corrections = []
    
    corrections.append(correction)
    
    with open(corrections_file_path, 'w', encoding='utf-8') as f:
        json.dump(corrections, f, indent=2, ensure_ascii=False)
    
    print(f"Correction saved to {corrections_file}")


def load_corrections(corrections_file: str = "data/question_corrections.json") -> List[Dict]:
    """Load all corrections from file."""
    corrections_file_path = Path(corrections_file)
    
    if not corrections_file_path.exists():
        return []
    
    with open(corrections_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_corrected_question(question_data: Dict, corrections: List[Dict]) -> Optional[str]:
    """
    Try to generate a corrected question based on learned patterns.
    """
    question = question_data.get('question', '')
    answer = question_data.get('answer', '')
    character = question_data.get('character', '')
    series = question_data.get('series', '')
    episode = question_data.get('episode', '')
    question_type = question_data.get('type', '')
    source = question_data.get('source', '')
    
    # Check if we have a similar correction
    for correction in corrections:
        # Match by question type and source
        if (correction.get('question_type') == question_type and 
            correction.get('source') == source):
            
            # Check if answer pattern matches
            if 'fondness' in answer.lower():
                # Use fondness template
                item = extract_item_from_answer(answer, 'fondness')
                if item and episode and series:
                    template = "Which episode of {series} showed {character}'s particular fondness for {item}?"
                    return template.format(series=series, character=character, item=item)
    
    return None


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: learn_from_corrections.py <original_question> <corrected_question> [question_json]")
        print("\nExample:")
        print('  learn_from_corrections.py "In which episode did Alynna Nechayev have a particular fondness?" "Which episode of TNG showed Alynna Nechayev\'s particular fondness for Bularian canapés?"')
        sys.exit(1)
    
    original = sys.argv[1]
    corrected = sys.argv[2]
    
    # Load question data if provided
    question_data = {}
    if len(sys.argv) > 3:
        with open(sys.argv[3], 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Check if it's a list or single object
            if isinstance(data, list):
                # Find matching question
                for q in data:
                    if isinstance(q, dict) and q.get('question') == original:
                        question_data = q
                        break
            elif isinstance(data, dict):
                # Single question object
                question_data = data
    
    correction = apply_correction(original, corrected, question_data)
    save_correction(correction)
    
    print("\nLearned pattern:")
    print(f"  Original: {original}")
    print(f"  Corrected: {corrected}")
    if 'generalized_template' in correction:
        print(f"  Template: {correction['generalized_template']}")

