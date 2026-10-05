#!/usr/bin/env python3
"""Read-only host inventory. Presence is deliberately not reported as E2E support."""
import importlib.metadata
import json
import platform
from pathlib import Path
import shutil
import sys

modules = {}
for name in ('lxml', 'mido'):
    try:
        modules[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        modules[name] = None
candidates = [shutil.which(n) for n in ('mscore', 'musescore', 'MuseScore4')]
candidates.append('/Applications/MuseScore 4.app/Contents/MacOS/mscore')
candidates.append(shutil.which('mscore3'))
mscore = next((p for p in candidates if p and Path(p).is_file()), None)
print(json.dumps(dict(python=platform.python_version(), platform=platform.system(), modules=modules,
                     python_supported=sys.version_info >= (3, 10), musescore=mscore,
                     pdf_renderer=shutil.which('pdftoppm'), executable_probe='NOT_RUN',
                     host_e2e='NOT_RUN', account_access='NOT_CHECKED'), indent=2))
