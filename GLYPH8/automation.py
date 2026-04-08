from __future__ import annotations
from datetime import datetime
from pathlib import Path
import argparse
import json
import logging
import time
from typing import Dict, List

from downloads_extractor import build_downloads_corpus, save_corpus, build_context_references, save_references
from glyph_system import GlyphEngine, GlyphEvent, CulturalLevel


DEFAULT_FILES = [
    'Epistemology - Wikipedia.pdf',
    'Cognitive anthropology - Wikipedia.pdf',
    'Behaviorism - Wikipedia.pdf',
    'Statistics - Wikipedia.pdf',
    'Sign (semiotics) - Wikipedia.pdf',
    'Value (semiotics) - Wikipedia.pdf',
    'Abstract Wikipedia - Meta-Wiki.pdf',
    'JONAH_STUDY_Dataset_BCDE_Civilizational.docx',
]


def setup_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger('glyph_automation')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger


def create_event_from_file(filename: str, text: str) -> GlyphEvent:
    event_id = filename.replace(' ', '_').replace('.', '_').replace('/', '_')
    category = 'knowledge' if 'Wikipedia' in filename or 'Abstract' in filename else 'dataset'
    probability = 0.75 if 'JONAH' in filename else 0.6
    description = text.strip().split('\n', 1)[0][:180]
    return GlyphEvent(
        event_id=event_id,
        source=filename,
        timestamp=datetime.utcnow().isoformat() + 'Z',
        user_probability=probability,
        category=category,
        description=description,
        data={'source_file': filename, 'text_snippet': description},
        level=CulturalLevel.SECONDARY,
    )


def create_events_from_corpus(corpus: Dict[str, str]) -> List[GlyphEvent]:
    return [create_event_from_file(filename, text) for filename, text in corpus.items() if text]


def run_automation_cycle(download_dir: Path, output_dir: Path, result_dir: Path, logger: logging.Logger) -> None:
    logger.info('Starting automation cycle')
    corpus = build_downloads_corpus(download_dir, DEFAULT_FILES)
    save_corpus(corpus, output_dir)
    engine = GlyphEngine()
    references = build_context_references(corpus)
    for reference in references:
        engine.add_context_reference(reference)
    save_references(references, result_dir)
    events = create_events_from_corpus(corpus)

    responses = []
    for event in events:
        response = engine.process_event(event)
        logger.info('Processed event %s level=%s category=%s confidence=%.2f', event.event_id, event.level.value, event.category, response.confidence)
        responses.append({
            'event_id': response.title,
            'body': response.body,
            'confidence': response.confidence,
            'metadata': response.metadata,
        })

    result_path = result_dir / f'automation_results_{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.json'
    result_dir.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps({'responses': responses}, indent=2), encoding='utf-8')
    logger.info('Saved automation results to %s', result_path)


def main() -> None:
    parser = argparse.ArgumentParser(description='Run GLYPH automation for Downloads extraction and event processing.')
    parser.add_argument('download_dir', type=Path, help='Path to the Downloads directory')
    parser.add_argument('--output', type=Path, default=Path('docs/downloads_corpus'), help='Path to save extracted text corpus')
    parser.add_argument('--results', type=Path, default=Path('docs/automation_results'), help='Path to save automation results')
    parser.add_argument('--log', type=Path, default=Path('docs/automation.log'), help='Path to write automation log')
    parser.add_argument('--interval', type=int, default=0, help='Seconds between repeated automation cycles; 0 runs once')
    args = parser.parse_args()

    logger = setup_logger(args.log)
    logger.info('Automation starting with download_dir=%s output=%s results=%s interval=%s', args.download_dir, args.output, args.results, args.interval)

    while True:
        try:
            run_automation_cycle(args.download_dir, args.output, args.results, logger)
        except Exception as exc:
            logger.exception('Automation cycle failed: %s', exc)
        if args.interval <= 0:
            break
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
