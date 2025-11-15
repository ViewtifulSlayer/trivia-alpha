# Star Trek Trivia Question Generator

A web-based tool for generating Star Trek franchise trivia questions from Memory Alpha wiki data. Uses a bottom-up data modeling approach to extract structured character information and generate high-quality trivia questions.

## Quick Start

### Web Interface (Recommended)
The easiest way to use the trivia generator is via the [live web interface](https://viewtifulslayer.github.io/trivia-alpha/web/).

### Local Development
```bash
# Serve the web interface locally
cd web
python -m http.server 8000
# Open http://localhost:8000
```

### Data Extraction & Question Generation
```bash
# Extract a single character
python src/convert_character_direct.py data/extracted/extracted_data.json "Character Name" output.json

# Bulk extract characters
python src/bulk_extract_characters.py data/extracted/extracted_data.json output_directory/

# Generate questions from character data
python src/generate_character_questions.py data/characters/ -o data/questions.json
```

## Project Structure

```
trivia_alpha/
├── src/              # Python data processing scripts
│   ├── extract_structured_character_improved.py  # Main extraction script
│   ├── generate_questions.py                     # Question generator
│   └── ...
├── data/             # Processed data files (organized by type)
│   ├── raw/                                     # Source XML file
│   ├── extracted/                               # Bulk extraction (292MB)
│   ├── characters/                              # Character extractions
│   ├── series/                                  # Series data (future)
│   ├── species/                                 # Species data (future)
│   ├── locations/                               # Location data (future)
│   ├── organizations/                           # Organization data (future)
│   ├── episodes/                                # Episode data (future)
│   └── scans/                                   # Test/scan outputs
├── docs/             # Documentation
│   ├── ARCHITECTURE.md           # Complete architecture documentation
│   └── TESTING_INSTRUCTIONS.md   # Testing guide for extraction script
├── web/              # HTML/JavaScript frontend (planned, GitHub Pages)
└── README.md         # This file
```

## Documentation

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Complete system architecture, data structures, and design decisions
- **[docs/TESTING_INSTRUCTIONS.md](docs/TESTING_INSTRUCTIONS.md)** - Guide for testing the extraction script
- **Session Logs** - `sessions/current/` - Development history and decisions

## Data Source

- **Memory Alpha Wiki Export**: `data/raw/enmemoryalpha_pages_current.xml`
- **Format**: MediaWiki XML export (version 0.11)
- **Size**: ~447 MB
- **Pages**: ~219,384 total pages
- **Valid Pages**: ~63,068 pages (after filtering)

## Current Status

✅ **Milestone 1**: Project structure, XML examination  
✅ **Milestone 2**: Data extraction pipeline (bulk extraction)  
✅ **Milestone 3**: Structured character extraction (bottom-up approach)  
✅ **Question Generation**: Production-ready system (15,927 questions, 100% verified)  
✅ **Milestone 4**: Web app deployed to GitHub Pages with dark mode interface

## Key Features

- **Structured Character Extraction**: Extracts comprehensive character data (family, appearances, events, characteristics, objects)
- **Question Generation**: Generates trivia questions with appropriate types (what, who, when, where, which) and difficulty levels
- **Bottom-Up Modeling**: Template-driven extraction ensures quality and consistency
- **Comprehensive Family Data**: Extracts all relationship types (spouse, children, in-laws, cousins, etc.)

## Data Extraction Results

### Bulk Extraction
- **Pages Extracted**: 63,068 valid pages (from 219,384 total)
- **Series Coverage**: 10 series (TNG: 13k, VOY: 11k, DS9: 11k pages)
- **Characters Indexed**: 113,556 unique character references
- **Output File**: `data/extracted/extracted_data.json` (~272 MB, ~82 MB compressed)

### Structured Character Extraction
- **Template**: `data/characters/molly.json` - Ideal target structure
- **Extraction Script**: `src/extract_structured_character_improved.py`
- **Tested Characters**: Molly O'Brien, Joseph Sisko, Lwaxana Troi, Miles O'Brien
- **Fields Extracted**: Status, birth info, comprehensive family relationships, actors, appearances, notable events, characteristics, locations, objects
- **Output Location**: `data/characters/*.json`

### Data Pipeline
1. **Bulk Extraction**: XML → `data/extracted/extracted_data.json` (categorizes all pages)
2. **Categorization**: Filter bulk extraction by type (characters, species, locations, etc.)
3. **Structured Extraction**: Extract deep data for specific entities → category subdirectories

## Live Demo

🌐 **Try it now**: [Star Trek Trivia Generator](https://viewtifulslayer.github.io/trivia-alpha/web/)

The web interface features:
- **15,927 verified trivia questions** from 616 characters
- **Dark mode** interface (default)
- **Advanced filtering** by series, character, difficulty, question type, and source
- **Question navigation** with previous/next/random
- **Export options** (JSON and text formats)

## License

**Tool**: MIT License  
**Data source**: Memory Alpha (Creative Commons Attribution-NonCommercial 4.0)

