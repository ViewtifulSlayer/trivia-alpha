# Question Correction Workflow

## Overview
This document describes how to work collaboratively to improve question quality by detecting and correcting unnatural-sounding questions.

## Tools

### 1. Detect Unnatural Questions
```bash
python src/detect_unnatural_questions.py data/questions_mvp_improved.json data/unnatural_questions_report.json
```

This will:
- Analyze all questions for unnatural patterns
- Generate a report of problematic questions
- Suggest improvements where possible

### 2. Learn from Corrections
```bash
python src/learn_from_corrections.py "<original question>" "<corrected question>" [question_data.json]
```

Example:
```bash
python src/learn_from_corrections.py \
  "In which episode did Alynna Nechayev have a particular fondness?" \
  "Which episode of TNG showed Alynna Nechayev's particular fondness for Bularian canapés?" \
  data/test_correction.json
```

This will:
- Save the correction to `data/question_corrections.json`
- Extract patterns and templates
- Build a library of learned patterns

### 3. Interactive Corrector
```bash
python src/interactive_corrector.py report data/unnatural_questions_report.json
```

This will:
- Go through each unnatural question one by one
- Prompt you for corrections
- Save each correction automatically

## Workflow

1. **Generate questions** (if needed):
   ```bash
   python src/generate_character_questions.py data/characters/bulk_extract_full_20251114-083000 -o data/questions_new.json
   ```

2. **Detect unnatural questions**:
   ```bash
   python src/detect_unnatural_questions.py data/questions_new.json data/unnatural_report.json
   ```

3. **Review the report** - Check `data/unnatural_questions_report.json` to see what was detected

4. **Correct questions** - Either:
   - Use interactive corrector: `python src/interactive_corrector.py report data/unnatural_report.json`
   - Or correct specific questions: `python src/interactive_corrector.py "<question text>"`

5. **Apply learned patterns** - The corrections are saved and can be used to improve future question generation

## Pattern Learning

When you provide a correction, the system learns:
- The original question template
- The corrected question template
- A generalized template (with placeholders)
- Context (question type, source, character, series, episode)
- **Contextual items** - specific details that must be extracted from the source event text

### Important: Contextual Items

The template uses placeholders like `{item}` for contextual details that are **specific to each event**. For example:
- "Bularian canapés" is specific to Alynna Nechayev's fondness in that particular episode
- This should NOT be hardcoded in the template
- When applying the template, the system must extract the item from the original event text

Example learned pattern:
```json
{
  "original_template": "In which episode did Alynna Nechayev have a particular fondness?",
  "corrected_template": "Which episode of TNG showed Alynna Nechayev's particular fondness for Bularian canapés?",
  "generalized_template": "Which episode of {series} showed {character}'s particular fondness for {item}?",
  "contextual_item": "Bularian canapés",
  "item_pattern": "fondness_for",
  "note": "Contextual item is specific to this event - must be extracted from source event text when applying template",
  "question_type": "when",
  "source": "timeline_event"
}
```

When applying this template to a new question:
1. Match the pattern (question type, source, structure)
2. Extract the contextual item from the source event text (e.g., "fondness for X")
3. Fill in the template with character, series, and the extracted item

## Next Steps

Once we have enough corrections, we can:
1. Update the question generator to use learned templates
2. Create pattern matching to automatically apply corrections
3. Build a quality scoring system based on learned patterns

