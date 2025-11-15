# Star Trek Trivia Generator

A web-based tool for generating Star Trek franchise trivia questions from Memory Alpha wiki data.

🌐 **Live Demo**: [https://viewtifulslayer.github.io/trivia-alpha/](https://viewtifulslayer.github.io/trivia-alpha/)

## Features

- **Tag-based Filtering**: Filter questions by series, character, difficulty, question type, and source
- **Question Navigation**: Browse questions with previous/next buttons or jump to random questions
- **Answer Reveal**: Click to reveal answers when ready
- **Export Options**: Export filtered questions as JSON or plain text
- **Modular Design**: Structure ready for future additions (rounds, etc.)

## Local Development

1. Serve the files using a local web server (required for JSON loading):

```bash
# Python 3
python -m http.server 8000

# Node.js (if you have http-server installed)
npx http-server

# Or use any local web server
```

2. Open `http://localhost:8000` in your browser

## GitHub Pages Deployment

1. Push the `web/` directory contents to your GitHub repository
2. Enable GitHub Pages in repository settings
3. Set source to `/` (root) or `/web` depending on your structure
4. The `.nojekyll` file ensures Jekyll doesn't process the files

## Data

Questions are loaded from `data/questions.json`. To update:
1. Run the question generator: `python src/generate_character_questions.py <character_dir> -o data/questions_mvp.json`
2. Copy to web: `cp data/questions_mvp.json web/data/questions.json`

## Future Enhancements

- **Rounds**: Pre-configured question sets by series
- **Question Sets**: Save and load custom filter combinations
- **Difficulty Weighting**: Adjust question selection based on difficulty distribution
- **Print Mode**: Optimized layout for printing question sheets

