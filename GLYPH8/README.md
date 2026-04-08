# GLYPH8

## Project layout

- `downloads_extractor.py` — Extract text from selected files in your `Downloads` folder.
- `glyph_system.py` — Event-driven analytics, probability engine, audit trail, context reference store, report generation, and response generation core.
- `automation.py` — Automate extraction, context-reference ingestion, and event processing on a schedule or repeatedly.
- `docs/DOWNLOADS_EXTRACTION_SUMMARY.md` — Notes and summary of the extracted documents and structural insights.
- `docs/AUTOMATION.md` — Documentation for automation and scheduling.
- `docs/downloads_corpus/` — Extracted article text files from Downloads sources.
- `docs/automation_results/` — Automation output and generated report artifacts.
- `docs/SAAS_ARCHITECTURE.md` — Architecture notes for SaaS-style event analytics and constraint-based behavior.

## How to run

1. Open a terminal in the `GLYPH8` folder.
2. Install required Python libraries if needed:
   ```bash
   python3 -m pip install --user PyPDF2 python-docx
   ```
3. Run the extractor:
   ```bash
   python3 downloads_extractor.py ~/Downloads --output downloads_corpus
   ```

The command will create `downloads_corpus/` with one `.txt` file per extracted document.

## Notes

- The extractor currently targets a small set of important files by name.
- You can update the file list in `downloads_extractor.py` to add or remove sources.
- The design keeps the repository flat: one top-level folder with one subfolder for docs.
