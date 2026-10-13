#!/usr/bin/env python3
"""Read-only host inventory. Presence is deliberately not reported as E2E support."""
import importlib.metadata
import json
import platform
from pathlib import Path
import shutil
import sys
import argparse

from score_intake import SCORE_KINDS, DELIVERIES, inspect_pdf, budget_checkpoint, check_pdf_edit_records

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input', type=Path, help='Optional source PDF to inspect without modifying it')
parser.add_argument('--score-kind', choices=SCORE_KINDS, default='unknown', help='Agent declaration after viewing source roles')
parser.add_argument('--delivery', choices=DELIVERIES, default='editable_score')
parser.add_argument('--budget-state', type=Path, help='Observed stage use and optional limits as JSON')
parser.add_argument('--pdf-edit-records', type=Path, help='Normalized local PDF edit records; not raw OMR output')
args = parser.parse_args()

modules = {}
for name in ('lxml', 'mido', 'pypdf'):
    try:
        modules[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        modules[name] = None
candidates = [shutil.which(n) for n in ('mscore', 'musescore', 'MuseScore4')]
candidates.append('/Applications/MuseScore 4.app/Contents/MacOS/mscore')
candidates.append(shutil.which('mscore3'))
mscore = next((p for p in candidates if p and Path(p).is_file()), None)
report = dict(python=platform.python_version(), platform=platform.system(), modules=modules,
                     python_supported=sys.version_info >= (3, 10), musescore=mscore,
                     pdf_renderer=shutil.which('pdftoppm'), executable_probe='NOT_RUN',
                     host_e2e='NOT_RUN', account_access='NOT_CHECKED')
exit_code = 0
try:
    if args.input:
        if args.input.suffix.lower() != '.pdf':
            raise ValueError('--input currently inspects PDF; use score_tool.py inspect for MusicXML/MXL')
        report['input'] = inspect_pdf(args.input, args.score_kind, args.delivery)
    if args.pdf_edit_records:
        if not args.input:
            raise ValueError('--pdf-edit-records requires its original --input PDF')
        report['pdf_edit_records'] = check_pdf_edit_records(json.loads(args.pdf_edit_records.read_text()), report['input']['source_sha256'])
        if report['pdf_edit_records']['status'] == 'FAIL':
            exit_code = 2
    if args.budget_state:
        report['budget'] = budget_checkpoint(json.loads(args.budget_state.read_text()))
        if report['budget']['action'] == 'REPLAN_METHOD' and not exit_code:
            exit_code = 3
except Exception as exc:
    report['error'] = f'{type(exc).__name__}: {exc}'
    exit_code = 1
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(exit_code)
