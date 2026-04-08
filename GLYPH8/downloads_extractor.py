from pathlib import Path
from typing import List, Dict
import re

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from glyph_system import ContextReference
except ImportError:
    ContextReference = None


def extract_text_from_pdf(path: Path, max_pages: int = 5) -> str:
    if PdfReader is None:
        raise ImportError('PyPDF2 is required to extract text from PDF files.')
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages[:max_pages]:
        pages.append(page.extract_text() or '')
    return '\n'.join(pages)


def extract_text_from_docx(path: Path) -> str:
    if Document is None:
        raise ImportError('python-docx is required to extract text from DOCX files.')
    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return '\n'.join(paragraphs)


def build_downloads_corpus(download_dir: Path, files: List[str]) -> Dict[str, str]:
    corpus = {}
    for filename in files:
        path = download_dir / filename
        if not path.exists():
            corpus[filename] = ''
            continue
        if filename.lower().endswith('.pdf'):
            corpus[filename] = extract_text_from_pdf(path)
        elif filename.lower().endswith('.docx'):
            corpus[filename] = extract_text_from_docx(path)
        else:
            corpus[filename] = path.read_text(encoding='utf-8', errors='ignore')
    return corpus


def save_corpus(corpus: Dict[str, str], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, text in corpus.items():
        safe_name = filename.replace(' ', '_').replace('/', '_')
        (output_dir / f'{safe_name}.txt').write_text(text, encoding='utf-8')


def file_to_tags(filename: str) -> List[str]:
    base = re.sub(r'[^a-zA-Z0-9 ]+', ' ', filename)
    return [token.lower() for token in base.split() if len(token) > 2]


def build_context_references(corpus: Dict[str, str]) -> List[ContextReference]:
    if ContextReference is None:
        raise ImportError('glyph_system.ContextReference is required for building context references.')
    references: List[ContextReference] = []
    for filename, text in corpus.items():
        if not text:
            continue
        ref_id = filename.replace(' ', '_').replace('.', '_').replace('/', '_')
        title = filename.replace('_', ' ').replace('-', ' ')
        snippet = ' '.join(text.strip().splitlines()[:4])
        tags = file_to_tags(filename)
        if 'wikipedia' in title.lower():
            tags.append('wikipedia')
        if 'abstract' in title.lower():
            tags.append('abstract')
        references.append(ContextReference(ref_id=ref_id, title=title, text=snippet, tags=list(dict.fromkeys(tags)), source=filename))
    return references


def save_references(references: List[ContextReference], output_dir: Path) -> None:
    import json
    output_dir.mkdir(parents=True, exist_ok=True)
    data = [
        {
            'ref_id': reference.ref_id,
            'title': reference.title,
            'text': reference.text,
            'tags': reference.tags,
            'source': reference.source,
        }
        for reference in references
    ]
    (output_dir / 'context_references.json').write_text(json.dumps(data, indent=2), encoding='utf-8')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extract text from selected Downloads files.')
    parser.add_argument('download_dir', type=Path, help='Path to the Downloads directory')
    parser.add_argument('--output', type=Path, default=Path('downloads_corpus'), help='Output directory for extracted text')
    args = parser.parse_args()

    files = [
        'Epistemology - Wikipedia.pdf',
        'Cognitive anthropology - Wikipedia.pdf',
        'Behaviorism - Wikipedia.pdf',
        'Statistics - Wikipedia.pdf',
        'Sign (semiotics) - Wikipedia.pdf',
        'Value (semiotics) - Wikipedia.pdf',
        'Abstract Wikipedia - Meta-Wiki.pdf',
        'JONAH_STUDY_Dataset_BCDE_Civilizational.docx',
    ]
    corpus = build_downloads_corpus(args.download_dir, files)
    save_corpus(corpus, args.output)
    print(f'Extracted {len(corpus)} files to {args.output}')
