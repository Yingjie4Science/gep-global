"""Offline repository structure and published-evidence checks; no data downloads."""
import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


def check():
    errors = []
    for name in ('README.md', 'environment.yml', 'pyproject.toml',
                 'docs/REPRODUCING.md', 'docs/DATA_SOURCES_AND_PREPROCESSING.md',
                 'docs/DECISIONS_AND_TODOS.md', 'config/run_registry.json'):
        if not (ROOT / name).is_file():
            errors.append(f'Missing required file: {name}')
    sources = list((ROOT / 'src').glob('*.py')) + list((ROOT / 'scripts').rglob('*.py')) + list((ROOT / 'tests').glob('*.py'))
    for path in sources:
        try:
            ast.parse(path.read_text(), filename=str(path))
        except SyntaxError as exc:
            errors.append(str(exc))
    migration = json.loads((ROOT / 'config/layout_migration_2026-10-27.json').read_text())
    for item in migration['moves']:
        if not (ROOT / item['new_path']).is_file():
            errors.append(f"Missing migration destination: {item['new_path']}")
        if (ROOT / item['old_path']).exists():
            errors.append(f"Obsolete duplicate executable remains: {item['old_path']}")
    evidence = json.loads((ROOT / 'config/published_evidence_checksums.json').read_text())['files']
    for name, expected in evidence.items():
        path = ROOT / name
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f'Frozen evidence missing or changed: {name}')
    runs = json.loads((ROOT / 'config/run_registry.json').read_text())['runs']
    if len({row['id'] for row in runs}) != len(runs):
        errors.append('Duplicate run registry IDs')
    for row in runs:
        for key in ('report', 'evidence', 'receipts'):
            if row.get(key) and not (ROOT / row[key]).exists():
                errors.append(f"{row['id']}: missing {key}: {row[key]}")
        if row['entrypoint'].startswith('scripts/') and not (ROOT / row['entrypoint']).is_file():
            errors.append(f"{row['id']}: missing entry point")
    markdown = [ROOT / 'README.md'] + list((ROOT / 'docs').rglob('*.md'))
    for path in markdown:
        text = path.read_text()
        if sum(line.startswith('```') for line in text.splitlines()) % 2:
            errors.append(f'Unclosed code fence: {path.relative_to(ROOT)}')
        for target in re.findall(r'\]\(([^)]+)\)', text):
            target = target.strip('<>').split('#', 1)[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            if target.startswith('/'):
                errors.append(f'Nonportable Markdown file link: {path.relative_to(ROOT)} -> {target}')
            elif not (path.parent / unquote(target)).exists():
                errors.append(f'Broken local link: {path.relative_to(ROOT)} -> {target}')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'PASS: {len(sources)} Python files parse; {len(evidence)} frozen evidence files unchanged; '
          f'{len(runs)} registered runs and {len(markdown)} Markdown files have valid local paths.')
    print('Scope: organization and preserved evidence only; run unit tests and input-specific QA separately.')
    return 0


if __name__ == '__main__':
    raise SystemExit(check())
