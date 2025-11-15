#!/usr/bin/env python3
"""
Interactive tool for correcting unnatural questions and learning patterns.
"""
import json
import sys
from pathlib import Path
from learn_from_corrections import apply_correction, save_correction, load_corrections

def correct_question_interactive(question_data: Dict):
    """Interactively correct a single question."""
    print("\n" + "="*60)
    print("QUESTION TO CORRECT:")
    print(f"  {question_data['question']}")
    print(f"\n  Answer: {question_data.get('answer', 'N/A')}")
    print(f"  Character: {question_data.get('character', 'N/A')}")
    print(f"  Series: {question_data.get('series', 'N/A')}")
    print(f"  Episode: {question_data.get('episode', 'N/A')}")
    print(f"  Type: {question_data.get('type', 'N/A')}")
    print(f"  Source: {question_data.get('source', 'N/A')}")
    
    print("\n" + "-"*60)
    print("Please provide a corrected version of this question.")
    print("(Or press Enter to skip, 'q' to quit)")
    
    corrected = input("\nCorrected question: ").strip()
    
    if not corrected:
        return None
    
    if corrected.lower() == 'q':
        return 'quit'
    
    # Learn from the correction
    correction = apply_correction(
        question_data['question'],
        corrected,
        question_data
    )
    
    save_correction(correction)
    
    print(f"\n✓ Correction saved!")
    print(f"  Learned template: {correction.get('generalized_template', 'N/A')}")
    
    return correction


def correct_from_report(report_file: str = "data/unnatural_questions_report.json"):
    """Correct questions from the unnatural questions report."""
    with open(report_file, 'r', encoding='utf-8') as f:
        unnatural_questions = json.load(f)
    
    print(f"\nFound {len(unnatural_questions)} unnatural questions to correct.")
    print("We'll go through them one by one.\n")
    
    corrections = []
    for i, q in enumerate(unnatural_questions, 1):
        print(f"\n[{i}/{len(unnatural_questions)}]")
        result = correct_question_interactive(q)
        
        if result == 'quit':
            print("\nStopped by user.")
            break
        
        if result:
            corrections.append(result)
    
    print(f"\n\nCompleted! Learned {len(corrections)} corrections.")
    return corrections


def correct_specific_question(question_text: str, questions_file: str = "data/questions_mvp_improved.json"):
    """Correct a specific question by text."""
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    # Find the question
    matching = [q for q in questions if q.get('question') == question_text]
    
    if not matching:
        print(f"Question not found: {question_text}")
        return None
    
    question_data = matching[0]
    return correct_question_interactive(question_data)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'report':
            # Correct from report
            report_file = sys.argv[2] if len(sys.argv) > 2 else "data/unnatural_questions_report.json"
            correct_from_report(report_file)
        else:
            # Correct specific question
            question_text = sys.argv[1]
            correct_specific_question(question_text)
    else:
        print("Usage:")
        print("  interactive_corrector.py report [report_file]  - Correct questions from report")
        print("  interactive_corrector.py '<question text>'     - Correct specific question")
        print("\nExample:")
        print('  interactive_corrector.py "In which episode did Alynna Nechayev have a particular fondness?"')

