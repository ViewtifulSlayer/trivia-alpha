#!/usr/bin/env python3
"""
Detect unnatural-sounding questions and suggest improvements.
This tool helps identify questions that don't sound natural to native English speakers.
"""
import json
import re
from typing import Dict, List, Tuple

def detect_unnatural_patterns(question: str, answer: str, question_type: str, source: str) -> List[Dict]:
    """
    Detect patterns that make questions sound unnatural.
    Returns list of issues found.
    """
    issues = []
    q_lower = question.lower()
    
    # Pattern 1: Incomplete action phrases
    # "did X have a particular fondness?" -> missing "for what?"
    if re.search(r'did \w+ \w+ (have|show|display|demonstrate) (a|an) \w+ \w+\?$', q_lower):
        issues.append({
            'type': 'incomplete_action',
            'severity': 'high',
            'pattern': 'Action phrase is incomplete (missing object/completion)',
            'example': question
        })
    
    # Pattern 2: Awkward "did X [verb]" constructions
    # "did X following" -> should be "did X follow" or rephrased
    awkward_verbs = ['following', 'assisted', 'participated', 'according', 'told']
    for verb in awkward_verbs:
        if f'did {verb}' in q_lower or re.search(rf'did \w+ \w+ {verb}', q_lower):
            issues.append({
                'type': 'awkward_verb_form',
                'severity': 'high',
                'pattern': f'Uses awkward verb form: {verb}',
                'example': question
            })
    
    # Pattern 3: Questions that end abruptly
    # "did X have a particular fondness?" -> should specify "for what?"
    if question.endswith('?') and len(question.split()) < 8:
        # Very short questions might be incomplete
        if 'did' in q_lower and ('have' in q_lower or 'show' in q_lower or 'display' in q_lower):
            issues.append({
                'type': 'too_short',
                'severity': 'medium',
                'pattern': 'Question seems incomplete or too short',
                'example': question
            })
    
    # Pattern 4: Questions that don't match answer structure
    # If answer is a thing (like "Bularian canapés"), question should ask "what"
    # If answer is an episode, question should ask "which episode"
    if question_type == 'when' and source == 'timeline_event':
        # "In which episode did X [action]?" should have episode as answer
        # But if action is incomplete, it's awkward
        if 'did' in q_lower and not any(word in q_lower for word in ['for', 'with', 'to', 'about', 'in']):
            # Action phrase might be incomplete
            issues.append({
                'type': 'mismatched_structure',
                'severity': 'medium',
                'pattern': 'Question structure might not match answer type',
                'example': question
            })
    
    # Pattern 5: Redundant or awkward phrasing
    # Check for repeated words (simple check)
    words = question.split()
    for i in range(len(words) - 1):
        if words[i].lower() == words[i+1].lower():
            issues.append({
                'type': 'redundant_word',
                'severity': 'low',
                'pattern': 'Contains repeated words',
                'example': question
            })
            break
    
    return issues


def suggest_improvements(question: str, answer: str, character: str, series: str, 
                        episode: str, question_type: str, source: str) -> List[str]:
    """
    Suggest better phrasings for a question.
    """
    suggestions = []
    q_lower = question.lower()
    
    # Template-based suggestions based on question type and source
    if question_type == 'when' and source == 'timeline_event':
        # Current: "In which episode did [character] [action]?"
        # Better options:
        
        # If action involves a specific thing (like "fondness for X")
        if 'fondness' in q_lower or 'preference' in q_lower or 'interest' in q_lower:
            # Extract what they have fondness for from answer or context
            if episode and series:
                suggestions.append(f"Which episode of {series} showed {character}'s particular fondness for [item]?")
                suggestions.append(f"In which episode of {series} did {character} express a fondness for [item]?")
        
        # If action is a specific event
        if episode and series:
            suggestions.append(f"Which episode of {series} featured {character} [doing specific action]?")
            suggestions.append(f"In which {series} episode did {character} [do specific action]?")
    
    if question_type == 'what' and source == 'timeline_event':
        # Current: "What happened to [character] in [episode]?"
        # This is usually good, but can be improved
        if episode and series:
            suggestions.append(f"In \"{episode}\" of {series}, what was {character} shown to [do/have/experience]?")
            suggestions.append(f"What did {character} do in \"{episode}\" of {series}?")
    
    return suggestions


def analyze_question_file(questions_file: str, output_file: str = None):
    """
    Analyze all questions in a file and identify unnatural ones.
    """
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    unnatural_questions = []
    
    for q in questions:
        question = q.get('question', '')
        answer = q.get('answer', '')
        question_type = q.get('type', '')
        source = q.get('source', '')
        character = q.get('character', '')
        series = q.get('series', '')
        episode = q.get('episode', '')
        
        issues = detect_unnatural_patterns(question, answer, question_type, source)
        
        if issues:
            suggestions = suggest_improvements(question, answer, character, series, episode, question_type, source)
            
            unnatural_questions.append({
                'question': question,
                'answer': answer,
                'character': character,
                'series': series,
                'episode': episode,
                'type': question_type,
                'source': source,
                'issues': issues,
                'suggestions': suggestions
            })
    
    # Print summary
    print(f"Analyzed {len(questions)} questions")
    print(f"Found {len(unnatural_questions)} potentially unnatural questions ({len(unnatural_questions)/len(questions)*100:.1f}%)\n")
    
    # Group by issue type
    issue_counts = {}
    for q in unnatural_questions:
        for issue in q['issues']:
            issue_type = issue['type']
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
    
    print("Issue breakdown:")
    for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue_type}: {count}")
    
    # Show examples
    print("\n\nSample unnatural questions:")
    for i, q in enumerate(unnatural_questions[:20], 1):
        print(f"\n{i}. {q['question']}")
        print(f"   Answer: {q['answer']}")
        print(f"   Issues: {', '.join([i['type'] for i in q['issues']])}")
        if q['suggestions']:
            print(f"   Suggestions:")
            for sug in q['suggestions'][:2]:
                print(f"     - {sug}")
    
    # Save detailed report
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unnatural_questions, f, indent=2, ensure_ascii=False)
        print(f"\n\nDetailed report saved to {output_file}")
    
    return unnatural_questions


if __name__ == "__main__":
    import sys
    questions_file = sys.argv[1] if len(sys.argv) > 1 else "data/questions_mvp_improved.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "data/unnatural_questions_report.json"
    analyze_question_file(questions_file, output_file)

