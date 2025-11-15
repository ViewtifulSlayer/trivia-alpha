#!/usr/bin/env python3
"""
Extended quality testing for question generation.
Tests multiple scenarios, question types, and analyzes patterns.
"""

import json
import sys
from collections import defaultdict
from trivia_generator import load_data, generate_trivia_questions

# Extended test scenarios
EXTENDED_SCENARIOS = [
    # Character tests (different series)
    {'name': 'DS9 + Odo', 'series': ['DS9'], 'characters': ['Odo'], 'description': 'DS9 character'},
    {'name': 'TNG + Picard', 'series': ['TNG'], 'characters': ['Picard'], 'description': 'TNG character'},
    {'name': 'VOY + Janeway', 'series': ['VOY'], 'characters': ['Janeway'], 'description': 'VOY character'},
    {'name': 'TOS + Kirk', 'series': ['TOS'], 'characters': ['Kirk'], 'description': 'TOS character'},
    {'name': 'DS9 + Quark', 'series': ['DS9'], 'characters': ['Quark'], 'description': 'DS9 character'},
    
    # Species tests
    {'name': 'DS9 + Klingon', 'series': ['DS9'], 'species': ['Klingon'], 'description': 'DS9 species'},
    {'name': 'TNG + Vulcan', 'series': ['TNG'], 'species': ['Vulcan'], 'description': 'TNG species'},
    {'name': 'TOS + Andorian', 'series': ['TOS'], 'species': ['Andorian'], 'description': 'TOS species'},
    
    # Location tests
    {'name': 'TNG + Enterprise', 'series': ['TNG'], 'locations': ['Enterprise'], 'description': 'TNG location'},
    {'name': 'DS9 + Deep Space 9', 'series': ['DS9'], 'locations': ['Deep Space 9'], 'description': 'DS9 location'},
    {'name': 'VOY + Voyager', 'series': ['VOY'], 'locations': ['Voyager'], 'description': 'VOY location'},
    
    # Organization tests
    {'name': 'DS9 + Starfleet', 'series': ['DS9'], 'organizations': ['Starfleet'], 'description': 'DS9 organization'},
    {'name': 'TNG + Federation', 'series': ['TNG'], 'organizations': ['Federation'], 'description': 'TNG organization'},
    
    # Concept tests
    {'name': 'TNG + Warp drive', 'series': ['TNG'], 'concepts': ['Warp drive'], 'description': 'TNG concept'},
    {'name': 'TOS + Prime Directive', 'series': ['TOS'], 'concepts': ['Prime Directive'], 'description': 'TOS concept'},
    
    # Combined filters
    {'name': 'DS9 + Odo + Klingon', 'series': ['DS9'], 'characters': ['Odo'], 'species': ['Klingon'], 'description': 'DS9 character + species'},
    {'name': 'TNG + Picard + Enterprise', 'series': ['TNG'], 'characters': ['Picard'], 'locations': ['Enterprise'], 'description': 'TNG character + location'},
    
    # Different question types
    {'name': 'DS9 + Odo (who)', 'series': ['DS9'], 'characters': ['Odo'], 'question_types': ['who'], 'description': 'Who questions'},
    {'name': 'TNG + Enterprise (where)', 'series': ['TNG'], 'locations': ['Enterprise'], 'question_types': ['where'], 'description': 'Where questions'},
    {'name': 'DS9 + Klingon (which)', 'series': ['DS9'], 'species': ['Klingon'], 'question_types': ['which'], 'description': 'Which questions'},
    
    # Multiple question types
    {'name': 'DS9 + Quark (mixed)', 'series': ['DS9'], 'characters': ['Quark'], 'question_types': ['what', 'who'], 'description': 'Mixed question types'},
]

def analyze_question_quality(questions):
    """Analyze quality metrics for a set of questions."""
    metrics = {
        'total': len(questions),
        'fragments': 0,
        'has_markup': 0,
        'incomplete': 0,
        'answer_lengths': [],
        'question_types': defaultdict(int),
        'templates_used': defaultdict(int),
        'difficulty_distribution': defaultdict(int),
    }
    
    fragment_patterns = ['born on', 'named for', 'died in', 'created by', 'played by']
    
    for q in questions:
        answer = q.get('answer', '').lower()
        
        # Check for fragments
        if any(pattern in answer for pattern in fragment_patterns) and len(answer) < 25:
            metrics['fragments'] += 1
        
        # Check for markup
        if '[' in q.get('answer', '') or '{{' in q.get('answer', ''):
            metrics['has_markup'] += 1
        
        # Check for incomplete answers
        if len(answer.split()) < 3:
            metrics['incomplete'] += 1
        
        # Answer length
        metrics['answer_lengths'].append(len(q.get('answer', '')))
        
        # Question type
        metrics['question_types'][q.get('question_type', 'unknown')] += 1
        
        # Template used (extract from question text)
        question_text = q.get('question', '')
        if "role" in question_text.lower():
            metrics['templates_used']['role'] += 1
        elif "known for" in question_text.lower():
            metrics['templates_used']['known_for'] += 1
        elif "happened" in question_text.lower():
            metrics['templates_used']['happened'] += 1
        elif "was" in question_text.lower() and "role" not in question_text.lower():
            metrics['templates_used']['was'] += 1
        
        # Difficulty - handle both dict and float formats
        difficulty_obj = q.get('difficulty', {})
        if isinstance(difficulty_obj, dict):
            difficulty = difficulty_obj.get('level', 'Unknown')
        else:
            # If it's a float, convert to level
            diff_score = float(difficulty_obj) if difficulty_obj else 0.0
            if diff_score < 0.3:
                difficulty = 'Easy'
            elif diff_score < 0.6:
                difficulty = 'Medium'
            else:
                difficulty = 'Hard'
        metrics['difficulty_distribution'][difficulty] += 1
    
    if metrics['answer_lengths']:
        metrics['avg_answer_length'] = sum(metrics['answer_lengths']) / len(metrics['answer_lengths'])
    else:
        metrics['avg_answer_length'] = 0
    
    return metrics

def test_scenario(data, scenario, max_questions=10):
    """Test a single scenario."""
    print(f"\n{'='*60}")
    print(f"Testing: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print(f"{'='*60}")
    
    try:
        questions = generate_trivia_questions(
            data,
            series=scenario.get('series'),
            characters=scenario.get('characters'),
            species=scenario.get('species'),
            locations=scenario.get('locations'),
            organizations=scenario.get('organizations'),
            concepts=scenario.get('concepts'),
            question_types=scenario.get('question_types', ['what']),
            max_questions=max_questions,
            max_difficulty=0.5
        )
        
        if not questions:
            print("  No questions generated")
            return {
                'scenario': scenario['name'],
                'questions': [],
                'metrics': None,
                'success': False
            }
        
        metrics = analyze_question_quality(questions)
        
        print(f"\nGenerated {len(questions)} questions")
        print(f"Quality Metrics:")
        print(f"  Fragments: {metrics['fragments']}/{metrics['total']} ({metrics['fragments']/metrics['total']*100:.1f}%)")
        print(f"  Has Markup: {metrics['has_markup']}/{metrics['total']} ({metrics['has_markup']/metrics['total']*100:.1f}%)")
        print(f"  Incomplete: {metrics['incomplete']}/{metrics['total']} ({metrics['incomplete']/metrics['total']*100:.1f}%)")
        print(f"  Avg Answer Length: {metrics['avg_answer_length']:.1f} chars")
        print(f"  Question Types: {dict(metrics['question_types'])}")
        print(f"  Templates Used: {dict(metrics['templates_used'])}")
        print(f"  Difficulty: {dict(metrics['difficulty_distribution'])}")
        
        print(f"\nSample Questions:")
        for i, q in enumerate(questions[:5], 1):
            answer = q.get('answer', '')
            if len(answer) > 100:
                answer = answer[:100] + '...'
            print(f"\n  {i}. {q.get('question', 'N/A')}")
            print(f"     Answer: {answer}")
            # Handle difficulty format
            diff_obj = q.get('difficulty', {})
            if isinstance(diff_obj, dict):
                diff_level = diff_obj.get('level', 'Unknown')
                diff_score = diff_obj.get('score', 0)
            else:
                diff_score = float(diff_obj) if diff_obj else 0.0
                if diff_score < 0.3:
                    diff_level = 'Easy'
                elif diff_score < 0.6:
                    diff_level = 'Medium'
                else:
                    diff_level = 'Hard'
            print(f"     Difficulty: {diff_level} ({diff_score:.2f})")
            print(f"     Source: {q.get('source_page', 'N/A')}")
        
        return {
            'scenario': scenario['name'],
            'questions': questions,
            'metrics': metrics,
            'success': True
        }
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'scenario': scenario['name'],
            'questions': [],
            'metrics': None,
            'success': False,
            'error': str(e)
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python extended_quality_test.py <extracted_data.json>")
        sys.exit(1)
    
    data_path = sys.argv[1]
    print("Loading data...")
    data = load_data(data_path)
    print(f"Loaded {len(data['pages'])} pages\n")
    
    results = []
    
    for scenario in EXTENDED_SCENARIOS:
        result = test_scenario(data, scenario, max_questions=10)
        results.append(result)
    
    # Summary analysis
    print(f"\n\n{'='*60}")
    print("EXTENDED TEST SUMMARY")
    print(f"{'='*60}\n")
    
    successful = [r for r in results if r['success']]
    total_questions = sum(len(r['questions']) for r in successful)
    
    print(f"Overall Statistics:")
    print(f"  Scenarios Tested: {len(EXTENDED_SCENARIOS)}")
    print(f"  Successful Scenarios: {len(successful)}")
    print(f"  Total Questions Generated: {total_questions}")
    
    if successful:
        # Aggregate metrics
        all_fragments = sum(r['metrics']['fragments'] for r in successful if r['metrics'])
        all_markup = sum(r['metrics']['has_markup'] for r in successful if r['metrics'])
        all_incomplete = sum(r['metrics']['incomplete'] for r in successful if r['metrics'])
        
        print(f"  Fragment Rate: {all_fragments}/{total_questions} ({all_fragments/total_questions*100:.1f}%)")
        print(f"  Markup Rate: {all_markup}/{total_questions} ({all_markup/total_questions*100:.1f}%)")
        print(f"  Incomplete Rate: {all_incomplete}/{total_questions} ({all_incomplete/total_questions*100:.1f}%)")
        
        # Template variety analysis
        all_templates = defaultdict(int)
        all_q_types = defaultdict(int)
        for r in successful:
            if r['metrics']:
                for template, count in r['metrics']['templates_used'].items():
                    all_templates[template] += count
                for q_type, count in r['metrics']['question_types'].items():
                    all_q_types[q_type] += count
        
        print(f"\nTemplate Distribution:")
        for template, count in sorted(all_templates.items(), key=lambda x: -x[1]):
            print(f"  {template}: {count} ({count/total_questions*100:.1f}%)")
        
        print(f"\nQuestion Type Distribution:")
        for q_type, count in sorted(all_q_types.items(), key=lambda x: -x[1]):
            print(f"  {q_type}: {count} ({count/total_questions*100:.1f}%)")
        
        # Scenario success rates
        print(f"\nScenario Success Rates:")
        character_scenarios = [r for r in successful if 'Character' in r['scenario'] or any(c in r['scenario'] for c in ['Odo', 'Picard', 'Janeway', 'Kirk', 'Quark'])]
        other_scenarios = [r for r in successful if r not in character_scenarios]
        
        print(f"  Character searches: {len(character_scenarios)}/{len([s for s in EXTENDED_SCENARIOS if s.get('characters')])} successful")
        print(f"  Other searches: {len(other_scenarios)}/{len([s for s in EXTENDED_SCENARIOS if not s.get('characters')])} successful")
    
    # Save detailed results
    output_path = data_path.replace('extracted_data.json', 'extended_test_results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_scenarios': len(EXTENDED_SCENARIOS),
                'successful_scenarios': len(successful),
                'total_questions': total_questions,
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {output_path}")

if __name__ == '__main__':
    main()

