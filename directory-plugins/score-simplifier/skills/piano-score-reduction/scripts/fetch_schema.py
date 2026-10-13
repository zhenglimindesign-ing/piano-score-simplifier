#!/usr/bin/env python3
"""Fetch only the pinned official MusicXML 4.0 schemas into a requested directory."""
import argparse
import hashlib
from pathlib import Path
import shutil
import ssl
import subprocess
from urllib.error import URLError
from urllib.request import urlopen

HASHES = {
    'musicxml.xsd': 'bfe37ed25a9ec00e6f2591d53df260b84efe12aed209ba3ac0a76f9287665a99',
    'xml.xsd': '616a3077df5cfc954ac74a75abe9697b95eef7a85dbe09367d995a483e840eb5',
    'xlink.xsd': '6e601f8eeb41618b50e4c7f944dff754e57ea43b602755470dda24c9c2f6df92',
}
p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
a = p.parse_args()
a.directory.mkdir(parents=True, exist_ok=True)
for name, expected in HASHES.items():
    target = a.directory / name
    if target.exists():
        data = target.read_bytes()
    else:
        url = 'https://raw.githubusercontent.com/w3c/musicxml/v4.0/schema/' + name
        try:
            with urlopen(url, timeout=20) as response:
                data = response.read(1_000_001)
        except URLError as exc:
            # Some framework Python installs lack a CA bundle. System curl uses
            # its own verified trust store; never disable certificate checking.
            if not isinstance(exc.reason, ssl.SSLCertVerificationError) or not shutil.which('curl'):
                raise
            data = subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                                   '--proto', '=https', '--max-time', '20', '--max-filesize', '1000000', url],
                                  capture_output=True, check=True).stdout
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f'Schema hash mismatch: {name}; preserved any existing file')
    if not target.exists():
        target.write_bytes(data)
    print(name + ': verified')
