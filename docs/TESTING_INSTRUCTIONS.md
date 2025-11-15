# Testing the Improved Extraction Script

## Quick Start

### Step 1: Run the Extraction Script

From the `projects/trivia_alpha/` directory, run:

```bash
python src/extract_structured_character_improved.py data/raw/enmemoryalpha_pages_current.xml "Molly O'Brien" data/characters/molly_improved.json
```

**Note:** If you're in the workspace root (`D:\Development\Resonance7`), use:

```bash
python projects/trivia_alpha/src/extract_structured_character_improved.py projects/trivia_alpha/data/raw/enmemoryalpha_pages_current.xml "Molly O'Brien" projects/trivia_alpha/data/characters/molly_improved.json
```

### Step 2: Check the Output

The script will print progress information:
- "Searching for 'Molly O'Brien' in XML file..."
- "Found page: Molly O'Brien" (when found)
- "Extracting structured data..."
- Summary of extracted fields

### Step 3: Compare with Target

Open both files and compare:

**Target file:** `data/characters/molly.json` (the ideal structure)
**Output file:** `data/characters/molly_improved.json` (what the script extracted)

## What to Look For

### ✅ Fields That Should Match

1. **Basic Info:**
   - `character.name` - Should be "Molly O'Brien"
   - `character.species` - Should be "Human"
   - `character.status` - Should be "Active (2375)" or similar
   - `character.born.year` - Should be `2368`
   - `character.born.location` - Should be "USS Enterprise-D"

2. **Family:**
   - `character.family.father` - Should be "Miles O'Brien"
   - `character.family.mother` - Should be "Keiko O'Brien"
   - `character.family.siblings` - Should include Kirayoshi with nickname "Yoshi"
   - `character.family.paternal_grandfather` - Should be "Michael O'Brien"
   - `character.family.maternal_grandfather` - Should be "Hiro Ishikawa"

3. **Actors:**
   - `character.portrayed_by` - Should have multiple actors:
     - Hana Hatae (primary)
     - Angela and Angelica Tedeski (infant)
     - Michelle Krusiec (adult version)

4. **Appearances:**
   - `character.appearances.TNG` - Should have episodes like "Disaster", "Power Play", "Rascals"
   - `character.appearances.DS9` - Should have episodes like "Time's Orphan", "Accession", etc.

5. **Notable Events:**
   - `character.notable_events` - Should have events like:
     - "Time's Orphan" - Fell through time portal
     - "Accession" - Acquired Lupi doll
     - "Body Parts" - Brother Kirayoshi born

6. **Characteristics:**
   - `character.characteristics` - Should have traits like "Loved to color"

7. **Locations:**
   - `character.locations` - Should have locations with periods:
     - USS Enterprise-D (2368-2369)
     - Deep Space 9 (2369-2375)
     - Earth (2375+)

8. **Objects:**
   - `character.objects` - Should include "Lupi" (Bajoran doll)

9. **Trivia Facts:**
   - `trivia_facts` - Should have multiple questions with answers

## Manual Comparison Method

### Option 1: Side-by-Side in Editor

1. Open `data/characters/molly.json` in one editor tab
2. Open `data/characters/molly_improved.json` in another tab
3. Compare field by field

### Option 2: Use a JSON Diff Tool

If you have a JSON diff tool or VS Code extension, use it to compare the two files.

### Option 3: Quick Visual Check

Look for these key indicators of success:

```json
{
  "character": {
    "species": "Human",  // ✅ Should not be null
    "born": {
      "year": 2368,      // ✅ Should not be null
      "location": "USS Enterprise-D"  // ✅ Should not be null
    },
    "family": {
      "siblings": [
        {
          "name": "Kirayoshi O'Brien",
          "nickname": "Yoshi"  // ✅ Should have nickname
        }
      ]
    },
    "notable_events": [...],  // ✅ Should not be empty array
    "characteristics": [...], // ✅ Should not be empty array
    "locations": [...],        // ✅ Should not be empty array
    "objects": [...]           // ✅ Should not be empty array
  }
}
```

## Troubleshooting

### Issue: Script can't find the character

**Check:**
- Is the XML file path correct?
- Does the character name match exactly? (Try with/without apostrophe: "Molly O'Brien" vs "Molly OBrien")

### Issue: Fields are null or empty

**Possible causes:**
- MediaWiki format might be different than expected
- Character page might not have the information in the expected format
- Regex patterns might need adjustment

**Solution:**
- Check the actual XML content for that character page
- Compare with what `molly.json` has manually entered
- Adjust regex patterns in the script if needed

### Issue: Script runs but produces errors

**Check:**
- Python version (should be 3.6+)
- Are all imports available? (uses standard library only)
- XML file is valid and accessible

## Expected Output Example

When successful, you should see output like:

```
Searching for 'Molly O'Brien' in XML file...
Found page: Molly O'Brien
Extracting structured data...
Saved to data/characters/molly_improved.json

Extracted Data:
  Name: Molly O'Brien
  Species: Human
  Status: Active (2375)
  Born: 2368 on USS Enterprise-D
  Father: Miles O'Brien
  Mother: Keiko O'Brien
  Siblings: 1
  Actors: 3
  Notable Events: 3
  Characteristics: 5
  Locations: 3
  Objects: 1
  Trivia Facts: 10
```

## Next Steps After Testing

1. **If extraction is successful:** Test with other characters (Lwaxana Troi, etc.)
2. **If fields are missing:** Review the MediaWiki format and adjust regex patterns
3. **If performance is slow:** The script uses streaming, so it should be efficient even for large XML files

## Quick Test Command

For a quick test, you can also check if the script runs without errors:

```bash
python src/extract_structured_character_improved.py --help
```

Or just run it and see what happens - it will tell you if it can't find the character or if there are any errors.

