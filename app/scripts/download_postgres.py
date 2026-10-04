"""Fetch pinned Ubuntu packages with APT; verify before project-local extraction.

Requires the matching Ubuntu amd64 package index. Does not install packages,
run maintainer scripts, modify apt sources or alter a system service.
"""
from pathlib import Path
import hashlib
import json
import subprocess

BASE = Path(__file__).resolve().parents[1]
manifest = json.loads((Path(__file__).parent / 'pg-packages.json').read_text())
packages = BASE / '.runtime/pg-packages'
root = BASE / '.runtime/pg-root'
packages.mkdir(parents=True, exist_ok=True)
for item in manifest:
    name, version = item['package'], item['version']
    metadata = subprocess.check_output(['apt-cache','show',f'{name}={version}'], text=True)
    if 'SHA256: '+item['sha256'] not in metadata:
        raise SystemExit(f'Package index mismatch: {name}. Reassess version; do not bypass verification.')
    subprocess.run(['apt-get','download',f'{name}={version}'], cwd=packages, check=True)
    matches=list(packages.glob(f'{name}_{version}_*.deb'))
    if len(matches)!=1 or hashlib.sha256(matches[0].read_bytes()).hexdigest()!=item['sha256']:
        raise SystemExit(f'Package checksum mismatch: {name}')
    subprocess.run(['dpkg-deb','-x',str(matches[0]),str(root)],check=True)
print('Verified PostgreSQL packages extracted within app/.runtime/pg-root.')
