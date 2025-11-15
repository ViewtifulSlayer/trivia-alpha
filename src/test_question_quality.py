#!/usr/bin/env python3
"""
Test question generation across multiple scenarios to identify patterns and issues.
"""

import json
import sys
from typing import Dict, List
from trivia_generator import load_data, generate_trivia_questions

# Test scenarios - diverse combinations to identify patterns
TEST_SCENARIOS = [
    {
        'name': 'DS9 + Character (Odo)',
        'series': ['DS9'],
        'characters': ['Odo'],
        'description': 'Single series, single character'
    },
    {
        'name': 'TNG + Character (Picard)',
        'series': ['TNG'],
        'characters': ['Jean-Luc Picard'],
        'description': 'Single series, single character (main character)'
    },
    {
        'name': 'VOY + Character (Janeway)',
        'series': ['VOY'],
        'characters': ['Kathryn Janeway'],
        'description': 'Single series, single character (captain)'
    },
    {
        'name': 'DS9 + Species (Klingon)',
        'series': ['DS9'],
        'species': ['Klingon'],
        'description': 'Single series, single species'
    },
    {
        'name': 'TNG + Location (Enterprise)',
        'series': ['TNG'],
        'locations': ['Enterprise'],
        'description': 'Single series, single location'
    },
    {
        'name': 'DS9 + Character + Location',
        'series': ['DS9'],
        'characters': ['Odo'],
        'locations': ['Deep Space 9'],
        'description': 'Multiple tag types'
    },
    {
        'name': 'TNG + Character + Species',
        'series': ['TNG'],
        'characters': ['Data'],
        'species': ['Android'],
        'description': 'Character with species tag'
    },
    {
        'name': 'Multi-Series (TNG + DS9)',
        'series': ['TNG', 'DS9'],
        'description': 'Multiple series'
    },
    {
        'name': 'TOS + Character (Kirk)',
        'series': ['TOS'],
        'characters': ['James T. Kirk'],
        'description': 'Original series, iconic character'
    },
    {
        'name': 'DS9 + Organization (Starfleet)',
        'series': ['DS9'],
        'organizations': ['Starfleet'],
        'description': 'Series with organization'
    }
]

def analyze_question_quality(question: Dict) -> Dict:
    """Analyze quality metrics for a single question."""
    answer = question.get('answer', '')
    question_text = question.get('question', '')
    source = question.get('source_page', '')
    
    # Quality metrics
    metrics = {
        'answer_length': len(answer),
        'answer_is_fragment': False,
        'answer_has_markup': False,
        'question_relevant': True,
        'answer_complete': True,
        'issues': []
    }
    
    # Check for fragments (very short or incomplete)
    if len(answer) < 10:
        metrics['answer_is_fragment'] = True
        metrics['answer_complete'] = False
        metrics['issues'].append('Answer too short')
    
    # Check for common fragment patterns
    fragment_patterns = [
        'born on', 'named for', 'died in', 'created by',
        'played by', 'voiced by', 'portrayed by'
    ]
    answer_lower = answer.lower()
    if any(pattern in answer_lower for pattern in fragment_patterns):
        if len(answer) < 30:  # Short answers with these patterns are likely fragments
            metrics['answer_is_fragment'] = True
            metrics['answer_complete'] = False
            metrics['issues'].append('Answer appears to be fragment')
    
    # Check for MediaWiki markup remnants
    if '[[' in answer or '{{' in answer or '<' in answer:
        metrics['answer_has_markup'] = True
        metrics['issues'].append('Answer contains markup')
    
    # Check question relevance (does it mention selected tags?)
    # This is basic - could be enhanced
    
    return metrics

def test_scenario(data: Dict, scenario: Dict, max_questions: int = 10) -> Dict:
    """Test a single scenario and return results."""
    print(f"\n{'=' * 60}")
    print(f"Testing: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print(f"{'=' * 60}")
    
    try:
        questions = generate_trivia_questions(
            data,
            series=scenario.get('series'),
            characters=scenario.get('characters'),
            species=scenario.get('species'),
            locations=scenario.get('locations'),
            organizations=scenario.get('organizations'),
            concepts=scenario.get('concepts'),
            episodes=scenario.get('episodes'),
            max_difficulty=0.8,
            max_questions=max_questions
        )
        
        # Analyze each question
        analyzed_questions = []
        for q in questions:
            metrics = analyze_question_quality(q)
            q['_quality_metrics'] = metrics
            analyzed_questions.append(q)
        
        # Calculate summary statistics
        total = len(analyzed_questions)
        fragments = sum(1 for q in analyzed_questions if q['_quality_metrics']['answer_is_fragment'])
        has_markup = sum(1 for q in analyzed_questions if q['_quality_metrics']['answer_has_markup'])
        incomplete = sum(1 for q in analyzed_questions if not q['_quality_metrics']['answer_complete'])
        avg_answer_length = sum(q['_quality_metrics']['answer_length'] for q in analyzed_questions) / total if total > 0 else 0
        
        # Print results
        print(f"\nGenerated {total} questions")
        print(f"Quality Metrics:")
        print(f"  Fragments: {fragments}/{total} ({fragments/total*100:.1f}%)")
        print(f"  Has Markup: {has_markup}/{total} ({has_markup/total*100:.1f}%)")
        print(f"  Incomplete: {incomplete}/{total} ({incomplete/total*100:.1f}%)")
        print(f"  Avg Answer Length: {avg_answer_length:.1f} chars")
        
        # Show sample questions
        print(f"\nSample Questions:")
        for i, q in enumerate(analyzed_questions[:5], 1):
            print(f"\n  {i}. {q['question']}")
            print(f"     Answer: {q['answer'][:100]}...")
            print(f"     Difficulty: {q.get('difficulty_level', 'Unknown')} ({q.get('difficulty', 0):.2f})")
            print(f"     Source: {q.get('source_page', 'Unknown')}")
            if q['_quality_metrics']['issues']:
                print(f"     Issues: {', '.join(q['_quality_metrics']['issues'])}")
        
        return {
            'scenario': scenario['name'],
            'description': scenario['description'],
            'total_questions': total,
            'fragments': fragments,
            'has_markup': has_markup,
            'incomplete': incomplete,
            'avg_answer_length': avg_answer_length,
            'questions': analyzed_questions
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'scenario': scenario['name'],
            'error': str(e),
            'total_questions': 0
        }

def main():
    """Run all test scenarios and generate analysis report."""
    if len(sys.argv) < 2:
        print("Usage: python test_question_quality.py <data_file>")
        sys.exit(1)
    
    data_path = sys.argv[1]
    
    print("=" * 60)
    print("QUESTION GENERATION QUALITY TEST SUITE")
    print("=" * 60)
    print(f"\nLoading data from {data_path}...")
    data = load_data(data_path)
    print(f"Loaded {len(data.get('pages', []))} pages")
    
    # Run all test scenarios
    results = []
    for scenario in TEST_SCENARIOS:
        result = test_scenario(data, scenario, max_questions=10)
        results.append(result)
    
    # Generate summary report
    print(f"\n\n{'=' * 60}")
    print("SUMMARY REPORT")
    print("=" * 60)
    
    total_scenarios = len([r for r in results if r.get('total_questions', 0) > 0])
    total_questions = sum(r.get('total_questions', 0) for r in results)
    total_fragments = sum(r.get('fragments', 0) for r in results)
    total_markup = sum(r.get('has_markup', 0) for r in results)
    total_incomplete = sum(r.get('incomplete', 0) for r in results)
    
    print(f"\nOverall Statistics:")
    print(f"  Scenarios Tested: {len(TEST_SCENARIOS)}")
    print(f"  Successful Scenarios: {total_scenarios}")
    print(f"  Total Questions Generated: {total_questions}")
    print(f"  Fragment Rate: {total_fragments}/{total_questions} ({total_fragments/total_questions*100:.1f}%)" if total_questions > 0 else "  Fragment Rate: N/A")
    print(f"  Markup Rate: {total_markup}/{total_questions} ({total_markup/total_questions*100:.1f}%)" if total_questions > 0 else "  Markup Rate: N/A")
    print(f"  Incomplete Rate: {total_incomplete}/{total_questions} ({total_incomplete/total_questions*100:.1f}%)" if total_questions > 0 else "  Incomplete Rate: N/A")
    
    # Identify patterns
    print(f"\n{'=' * 60}")
    print("PATTERN ANALYSIS")
    print("=" * 60)
    
    # Best scenarios (lowest fragment rate)
    valid_results = [r for r in results if r.get('total_questions', 0) > 0]
    if valid_results:
        best_scenarios = sorted(valid_results, key=lambda x: x.get('fragments', 999) / x.get('total_questions', 1))[:3]
        print(f"\nBest Scenarios (lowest fragment rate):")
        for r in best_scenarios:
            frag_rate = r.get('fragments', 0) / r.get('total_questions', 1) * 100
            print(f"  {r['scenario']}: {frag_rate:.1f}% fragments")
        
        worst_scenarios = sorted(valid_results, key=lambda x: x.get('fragments', 0) / x.get('total_questions', 1), reverse=True)[:3]
        print(f"\nWorst Scenarios (highest fragment rate):")
        for r in worst_scenarios:
            frag_rate = r.get('fragments', 0) / r.get('total_questions', 1) * 100
            print(f"  {r['scenario']}: {frag_rate:.1f}% fragments")
    
    # Save detailed results
    output_file = '../data/question_quality_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_scenarios': len(TEST_SCENARIOS),
                'successful_scenarios': total_scenarios,
                'total_questions': total_questions,
                'fragment_rate': total_fragments / total_questions if total_questions > 0 else 0,
                'markup_rate': total_markup / total_questions if total_questions > 0 else 0,
                'incomplete_rate': total_incomplete / total_questions if total_questions > 0 else 0
            },
            'scenarios': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 60}")
    print(f"Detailed results saved to: {output_file}")
    print("=" * 60)

if __name__ == '__main__':
    main()

