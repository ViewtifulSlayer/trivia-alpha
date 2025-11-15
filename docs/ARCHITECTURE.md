# Architecture Documentation

## Overview

Star Trek Trivia Question Generator is a web-based tool that extracts structured character data from Memory Alpha wiki XML exports and generates trivia questions. The system uses a bottom-up data modeling approach, starting with well-structured character templates and building extraction logic to match them.

**Data Source**: Memory Alpha Wiki XML Export (`data/raw/enmemoryalpha_pages_current.xml`)
- **Size**: ~447 MB
- **Pages**: ~219,384 total pages
- **Valid Pages**: ~63,068 pages (after filtering)
- **Format**: MediaWiki XML export (version 0.11)

**Target Platform**: GitHub Pages (static web hosting)
- **Limits**: 1 GB total, 100 MB per file
- **Current Data**: ~82 MB compressed JSON

## System Architecture

### High-Level Flow

```
XML Export → Bulk Extraction → Categorization → Structured Extraction → Category Files → Question Generator → Web App
```

1. **Bulk Extraction** (`src/extract_data.py`)
   - Streams through XML using `xml.etree.ElementTree.iterparse`
   - Extracts all pages with tags: characters, species, locations, organizations, concepts, episodes
   - Outputs `data/extracted/extracted_data.json` (~292 MB) with indices for fast lookup
   - Used for categorization and question generation

2. **Categorization** (future: `src/categorize_data.py`)
   - Filters bulk extraction by data type
   - Identifies character pages, species pages, location pages, etc.
   - Enables batch processing of categories

3. **Structured Extraction** (Two approaches available)
   - **Legacy Approach** (`src/extract_structured_character_improved.py`):
     - Extracts deep structured data for specific entities
     - Can work from XML directly or from bulk extraction JSON
     - Outputs category-specific JSON files (e.g., `data/characters/*.json`)
     - Uses pattern matching to extract specific fields
   - **Direct Conversion Approach** (`src/convert_character_direct.py`) - **Recommended**:
     - Direct MediaWiki-to-JSON conversion matching `rom_example.json` structure
     - Extracts sidebar/infobox fields directly
     - Preserves timeline sections as arrays of event objects with `content_type` fields
     - Extracts all episodes from Appendices section
     - Outputs clean, structured JSON ready for question generation
     - Focuses on data extraction only (no trivia question generation)

4. **Question Generation** (`src/generate_questions.py`, `src/episode_question_generator.py`)
   - Uses structured character data
   - Generates questions with appropriate types (what, who, when, where, which)
   - Scores difficulty (Easy, Medium, Hard)

5. **Web Frontend** (planned: `web/`)
   - Static HTML/JavaScript
   - Loads JSON data
   - Generates questions on-demand
   - GitHub Pages deployment

## Source Code Structure

### Directory Organization

```
src/
├── extract_data.py                    # Bulk extraction (Stage 1)
├── extract_structured_character_improved.py  # Legacy structured character extraction (Stage 2)
├── convert_character_direct.py        # Direct MediaWiki-to-JSON converter (Stage 2 - Recommended)
├── generate_questions.py             # Question generation from pages
├── episode_question_generator.py      # Episode-based question generation
├── trivia_generator.py                # Main generator (orchestrates filtering + generation)
├── filter_pages.py                    # Page filtering by tags (used by trivia_generator)
├── difficulty_scorer.py              # Difficulty calculation (used by trivia_generator)
├── scan_family_fields.py              # Tool: Scan character pages for family patterns
├── test_accession.py                  # Test: Episode question generation
├── test_question_quality.py           # Test: Question quality validation
├── extended_quality_test.py           # Test: Extended quality testing
└── debug/                              # Debug tools (development only)
    ├── debug_character_xml.py
    ├── debug_description.py
    ├── debug_lwaxana.py
    ├── debug_molly_page.py
    ├── debug_molly_xml_content.py
    └── debug_molly_xml.py
```

### Core Scripts

**Extraction Pipeline:**
- **`extract_data.py`** - Bulk extraction script. Processes entire XML file, extracts all pages with categorization tags (characters, species, locations, organizations, concepts, episodes). Outputs `data/extracted/extracted_data.json` with indices for fast lookup. Used for categorization and question generation.

- **`extract_structured_character_improved.py`** - Legacy structured character extraction script. Extracts deep structured data for individual characters from XML using pattern matching. Outputs category-specific JSON files (e.g., `data/characters/molly.json`). Can work from XML directly or from bulk extraction JSON. **Note**: This is the older approach; see `convert_character_direct.py` for the recommended direct conversion method.

- **`convert_character_direct.py`** - **Recommended** direct MediaWiki-to-JSON converter. Converts character pages directly from `extracted_data.json` to the `rom_example.json` format. Extracts sidebar/infobox fields directly, preserves timeline sections as arrays of event objects with `content_type` fields, extracts all episodes from Appendices section. Outputs clean, structured JSON ready for question generation. Focuses on data extraction only (no trivia question generation). Usage: `python src/convert_character_direct.py data/extracted/extracted_data.json "Character Name" data/characters/output.json`

**Question Generation:**
- **`generate_questions.py`** - Core question generation module. Contains question templates, fact extraction, and answer generation logic. Generates questions from page content using template-based approach.

- **`episode_question_generator.py`** - Episode-based question generation module. Implements user's "anchor point" workflow: generates questions from episode pages following episode descriptions. Functions: `is_episode_page()`, `extract_episode_facts()`, `generate_episode_questions()`.

- **`trivia_generator.py`** - Main trivia generator script. Orchestrates the full pipeline: loads data, filters pages by tags (using `filter_pages.py`), generates questions (using `generate_questions.py` and `episode_question_generator.py`), scores difficulty (using `difficulty_scorer.py`). Command-line interface for generating questions.

**Supporting Modules:**
- **`filter_pages.py`** - Page filtering utilities. `filter_pages_by_tags()` filters pages by selected tags (series, characters, species, locations, etc.) with AND/OR logic. Used by `trivia_generator.py`.

- **`difficulty_scorer.py`** - Difficulty calculation utilities. `calculate_difficulty()` scores question difficulty (0.0-1.0), `get_difficulty_level()` converts to Easy/Medium/Hard. Used by `trivia_generator.py`.

**Development Tools:**
- **`scan_family_fields.py`** - Analysis tool. Scans character pages to identify family relationship patterns. Used to enhance family extraction capabilities.

- **`debug/`** - Debug scripts for development. Tools for examining XML content, JSON structure, and extraction results. Not used in production pipeline.

**Test Scripts:**
- **`test_accession.py`** - Tests episode question generation with specific episodes (Accession, Time's Orphan).
- **`test_question_quality.py`** - Tests question generation quality across multiple scenarios.
- **`extended_quality_test.py`** - Extended quality testing with 21 diverse scenarios.

### How Components Work Together

1. **Bulk Extraction** (`extract_data.py`) → Creates `data/extracted/extracted_data.json` with all pages categorized
2. **Structured Extraction** (Two approaches):
   - **Legacy**: `extract_structured_character_improved.py` → Creates `data/characters/*.json` with deep character data using pattern matching
   - **Recommended**: `convert_character_direct.py` → Creates `data/characters/*.json` with direct MediaWiki-to-JSON conversion matching `rom_example.json` structure
3. **Question Generation** (`trivia_generator.py`) → Uses bulk extraction for filtering, structured data for questions
   - Loads `data/extracted/extracted_data.json`
   - Filters pages using `filter_pages.py`
   - Generates questions using `generate_questions.py` and `episode_question_generator.py`
   - Scores difficulty using `difficulty_scorer.py`
   - Returns formatted questions

## Data Architecture

### Character Data Structure

The system uses a bottom-up approach: a well-structured template (`data/characters/molly.json`) defines the target structure, and extraction logic matches it.

#### Core Character Schema

```json
{
  "character": {
    "name": "string",
    "species": "string",
    "status": "string",
    "born": {
      "year": number,
      "location": "string"
    },
    "family": {
      "father": "string",
      "mother": "string",
      "spouse": ["string"],
      "children": ["string"],
      "siblings": [{"name": "string", "relationship": "string", "nickname": "string"}],
      "paternal_grandfather": "string",
      "maternal_grandfather": "string",
      "maternal_grandmother": "string",
      "maternal_great_grandmother": "string",
      "paternal_ancestors": ["string"],
      "daughter_in_law": ["string"],
      "son_in_law": ["string"],
      "grandsons": ["string"],
      "granddaughters": ["string"],
      "father_in_law": "string",
      "mother_in_law": "string",
      "brother_in_law": ["string"],
      "sister_in_law": ["string"],
      "cousins": ["string"],
      "uncles": ["string"],
      "aunts": ["string"],
      "nephews": ["string"],
      "nieces": ["string"]
    },
    "portrayed_by": [
      {
        "actor": "string",
        "role": "string"
      }
    ],
    "appearances": {
      "TNG": ["episode names"],
      "DS9": ["episode names"],
      "VOY": ["episode names"],
      "TOS": ["episode names"],
      "ENT": ["episode names"],
      "DIS": ["episode names"],
      "PIC": ["episode names"],
      "LD": ["episode names"],
      "SNW": ["episode names"],
      "PRO": ["episode names"]
    },
    "notable_events": [
      {
        "event": "string",
        "episode": "string",
        "series": "string",
        "summary": "string"
      }
    ],
    "characteristics": ["string"],
    "locations": [
      {
        "location": "string",
        "period": "string",
        "reason": "string"
      }
    ],
    "objects": [
      {
        "object": "string",
        "context": "string"
      }
    ]
  },
  "trivia_facts": [
    {
      "question_type": "what|who|when|where|which",
      "question": "string",
      "answer": "string",
      "difficulty": "Easy|Medium|Hard"
    }
  ]
}
```

### Page Data Structure (Legacy/Alternative)

For bulk extraction, pages are stored with:

```json
{
  "title": "Page Title",
  "series": ["TNG", "DS9"],
  "characters": ["Character Name"],
  "species": ["Klingon", "Vulcan"],
  "locations": ["Deep Space 9", "Alpha Quadrant"],
  "concepts": ["23rd century", "crew"],
  "organizations": ["Starfleet", "Federation"],
  "episodes": ["Episode Name"],
  "content_snippet": "First 500 chars...",
  "full_text": "Complete content...",
  "text_length": 12345
}
```

### Data Directory Structure

Data is organized by type in subdirectories:

```
data/
├── raw/                          # Source data files
│   └── enmemoryalpha_pages_current.xml  # XML source (447MB)
├── extracted/                    # Bulk extraction outputs
│   └── extracted_data.json      # Full bulk extraction (292MB)
├── characters/                   # Individual character extractions
│   ├── molly.json               # Template/ideal structure
│   ├── molly_extracted.json     # Extraction result
│   ├── joseph_sisko.json
│   └── ...
├── series/                       # Series-specific data (future)
│   └── (series-specific extractions)
├── species/                      # Species data (future)
│   └── (species-specific extractions)
├── locations/                     # Location data (future)
│   └── (location-specific extractions)
├── organizations/                # Organization data (future)
│   └── (organization-specific extractions)
├── episodes/                     # Episode data (future)
│   └── (episode-specific extractions)
└── scans/                        # Test/scan outputs
    └── family_fields_scan.json
```

**Pipeline Benefits:**
- **Bulk extraction** identifies page types (characters, species, locations, etc.)
- **Categorization** filters pages by type without re-parsing XML
- **Structured extraction** creates deep, category-specific data structures
- **Separation** allows different extraction methods per category

**Design Principle**: Bulk extraction enables efficient categorization; structured extraction creates deep data per category.

## Extraction Pipeline

### Two-Stage Extraction Approach

**Stage 1: Bulk Extraction** (`src/extract_data.py`)
- Processes entire XML file once
- Extracts all pages with categorization tags
- Creates `data/extracted/extracted_data.json` with indices
- Each page includes: `characters`, `species`, `locations`, `organizations`, `concepts`, `episodes` arrays
- **Purpose**: Fast categorization and filtering without re-parsing XML

**Stage 2: Structured Extraction** (Two approaches available)
- **Legacy Approach** (`src/extract_structured_character_improved.py`):
  - Can work from XML directly or from bulk extraction JSON
  - Extracts deep structured data for specific entities using pattern matching
  - Creates category-specific files (e.g., `data/characters/molly.json`)
  - **Purpose**: Rich, detailed data structures for trivia generation
- **Recommended Approach** (`src/convert_character_direct.py`):
  - Works from bulk extraction JSON (`data/extracted/extracted_data.json`)
  - Direct MediaWiki-to-JSON conversion matching `rom_example.json` structure
  - Extracts sidebar/infobox fields directly, preserves timeline sections with `content_type` fields
  - Extracts all episodes from Appendices section
  - **Purpose**: Clean, structured JSON ready for question generation (no trivia questions generated)

**Future: Categorization Script** (`src/categorize_data.py`)
- Reads `data/extracted/extracted_data.json`
- Filters pages by type (character pages, species pages, etc.)
- Enables batch extraction of all characters, all species, etc.
- **Purpose**: Efficient batch processing using bulk extraction results

### MediaWiki XML Parsing

**Streaming Parser**: Uses `xml.etree.ElementTree.iterparse` for memory-efficient processing of large XML files.

**Namespace Handling**: MediaWiki XML uses namespace `{http://www.mediawiki.org/xml/export-0.11/}`

**Key Patterns Extracted**:

1. **Sidebar Templates** (`{{Sidebar character}}`):
   - `|species = ...`
   - `|born = ...`
   - `|father = ...`, `|mother = ...`
   - `|spouse = ...`, `|children = ...`
   - `|sibling = ...`
   - `|relative = ...` (extended family)
   - `|actor = ...` or `|portrayed = ...`
   - `|status = ...` and `|datestatus = ...`

2. **Episode References**: `{{TNG|Episode Name}}`, `{{DS9|Episode Name}}`, etc.

3. **Narrative Text Patterns**:
   - Family nicknames: `([[nickname]]d "Yoshi")`
   - Characteristics: "Loved to color", "Often colored after dinner"
   - Locations: "Deep Space 9" with period and reason
   - Objects: "acquired a Bajoran doll named [[Lupi]]"

### Extraction Functions

**Core Extraction Scripts**:
- `src/extract_data.py` - Bulk extraction with categorization tags
- `src/extract_structured_character_improved.py` - Deep structured extraction

Key functions:
- `extract_status()` - Character status and date
- `extract_birth_info()` - Birth year and location (handles USS templates)
- `extract_family_relationships()` - Comprehensive family extraction
- `extract_portrayed_by()` - Actors with roles (handles `<br>` separators)
- `extract_notable_events()` - Events from episode descriptions
- `extract_characteristics()` - Personality traits and behaviors
- `extract_locations()` - Locations with context
- `extract_objects()` - Items associated with character
- `clean_mediawiki_markup()` - Removes MediaWiki syntax, preserves content

### Filtering & Quality

- **Minimum Page Length**: 200 characters (configurable)
- **Character Filtering**: Excludes "(mirror)", "(alternate)" variants from main search
- **Placeholder Filtering**: Removes "001" placeholders from family names
- **File Reference Cleaning**: Removes `File:*.jpg` references from events
- **Invalid Actor Filtering**: Removes invalid actor entries

## Question Generation

### Question Types

- **what** - Facts, objects, concepts
- **who** - Characters, people
- **when** - Dates, time periods
- **where** - Locations
- **which** - Choices, selections

### Difficulty Scoring

**Easy**: Basic facts (name, species, status)
**Medium**: Relationships, appearances, notable events
**Hard**: Specific details, obscure facts, complex relationships

### Generation Strategy

1. **Character-Based**: Generate questions from structured character data
2. **Episode-Based**: Generate questions from episode descriptions
3. **Hybrid**: Combine character facts with episode context

**Quality Metrics**:
- Fragment rate: 0% (down from 7%)
- Question relevance: 100% for character searches
- Template variety: Multiple question formats
- Appropriate question types: Matches content type

## Key Architectural Decisions

### 1. Bottom-Up Data Modeling

**Decision**: Start with well-structured template (`molly.json`), build extraction to match.

**Rationale**:
- Clear target structure
- Quality over quantity
- Easier testing with known-good data
- Template becomes extraction guide

**Alternative Considered**: Top-down extraction of all pages, then structure. Rejected due to complexity and quality concerns.

### 2. Separate Subject Fields

**Decision**: Use separate fields for `characters`, `species`, `locations`, `concepts`, `organizations`, `episodes`.

**Rationale**:
- Clear separation of tag types
- Easy filtering: "Show me questions about Klingons in DS9"
- Supports complex queries
- Better for UI (separate dropdowns/fields)

**Alternative Considered**: Unified "subjects" object or flat tags array. Rejected for clarity and query simplicity.

### 3. Content Storage: Snippet + Full Text

**Decision**: Store both `content_snippet` (500 chars) and `full_text` (complete).

**Rationale**:
- Full text essential for question generation
- Snippet useful for UI previews
- 82 MB compressed is acceptable for GitHub Pages
- Can optimize later if needed

**Future Optimization**: Can separate full_text into compressed file or use more aggressive compression.

### 4. Page Filtering: 200 Character Minimum

**Decision**: Filter pages with < 200 characters (configurable).

**Rationale**:
- Filters out stubs, redirects, very short pages
- 28.7% pass rate is expected (many pages are user pages, talk pages, redirects)
- Quality over quantity
- Configurable for future series adaptations

### 5. Single File MVP, Design for Hybrid Migration

**Decision**: Start with single compressed file, design loading abstraction for easy migration to hybrid.

**Rationale**:
- Simple for MVP
- Fast to implement
- Design allows transparent migration
- Application code doesn't need to change

**Future**: Can migrate to hybrid (metadata + series files) if load times become problematic.

### 6. Comprehensive Family Extraction

**Decision**: Extract all family relationship types (spouse, children, in-laws, cousins, etc.) from `|spouse=`, `|children=`, and `|relative=` fields.

**Rationale**:
- Rich trivia potential
- Complete character relationships
- Handles complex family structures
- Supports relationship-based questions

**Implementation**: Complex regex patterns to parse names, relationships, and "via" qualifiers.

## Technical Stack

### Backend Processing
- **Language**: Python 3
- **XML Parsing**: `xml.etree.ElementTree` (streaming)
- **Data Format**: JSON
- **Compression**: gzip

### Frontend (Planned)
- **Hosting**: GitHub Pages (static)
- **Language**: HTML, JavaScript (vanilla or lightweight framework)
- **Data Loading**: Fetch API, JSON parsing
- **Question Generation**: Client-side JavaScript

### Development Tools
- **Version Control**: Git
- **IDE**: Cursor (with Resonance 7 workspace structure)
- **Documentation**: Markdown

## Performance Considerations

### Extraction Performance
- **Streaming Parser**: Memory-efficient for 447 MB XML
- **Processing Time**: ~minutes for full extraction (depends on hardware)
- **Output Size**: ~82 MB compressed JSON

### Web App Performance
- **Initial Load**: ~82 MB download (acceptable for proof-of-concept)
- **Future Optimization**: Hybrid approach reduces initial load to ~1 MB (metadata)
- **Lazy Loading**: Series files loaded on-demand
- **Caching**: Browser caching of loaded data

### Scalability
- **Current**: Handles 63k pages comfortably
- **Future**: Hybrid approach supports larger datasets
- **Multi-Series**: Design supports other franchises (Star Wars, Doctor Who, etc.)

## Future Considerations

### Phase 2: Hybrid File Organization
- Split by series for lazy loading
- Metadata file for fast character search
- Common characters file for immediate access

### Phase 3: Multi-Series Support
- Series configuration system
- Per-series extraction settings
- Shared core extraction logic
- Series-specific optimizations

### Phase 4: Advanced Features
- Character relationship database (cross-reference family data)
- Question quality metrics and feedback
- User customization (difficulty, series, topics)
- Export/sharing functionality

## Maintenance & Updates

### Data Updates
- Re-run extraction when Memory Alpha XML is updated
- Version control for JSON outputs
- Incremental updates possible (extract only changed pages)

### Code Maintenance
- Extraction patterns may need updates for MediaWiki format changes
- Question generation logic may need refinement based on user feedback
- Web app optimization based on usage patterns

## References

- **Memory Alpha Wiki**: http://memory-alpha.fandom.com/wiki/Portal:Main
- **MediaWiki XML Export Format**: https://www.mediawiki.org/wiki/Help:Export
- **GitHub Pages Limits**: https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages#limits

---

**Last Updated**: 2025-11-11  
**Status**: Active Development  
**Version**: 1.0 (MVP Phase)

