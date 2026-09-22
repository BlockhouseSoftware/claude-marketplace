"""Prepare a catalog update only after the product's release tag exists.

Usage: python scripts/promote_release.py v0.3.1
Validates the immutable pin and mirrored metadata before writing the catalog.
Does not commit, push, merge or publish anything.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from check_catalog import MIRRORED, RELEASE_TAG, check_entry, fetch_manifest, repo_url


def promote(catalog_path: Path, tag: str) -> None:
    if not RELEASE_TAG.fullmatch(tag):
        raise ValueError('expected a release tag such as v0.3.1')
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    entry = next(p for p in catalog['plugins'] if p['name'] == 'trojaino')
    source = dict(entry['source'], ref=tag)
    with tempfile.TemporaryDirectory(prefix='catalog-pin-') as tmp:
        def git(*args):
            return subprocess.check_output(['git','-C',tmp,*args],stderr=subprocess.PIPE,timeout=60).decode().strip()
        git('init','-q')
        git('fetch','-q','--depth','1',repo_url(source),f'refs/tags/{tag}')
        source['sha'] = git('rev-parse','FETCH_HEAD^{commit}')
    manifest = fetch_manifest(source,60)
    entry.update({key:manifest[key] for key in MIRRORED})
    entry['source'] = source
    errors = []
    check_entry(entry,errors,True,60)
    if errors:
        raise ValueError('; '.join(errors))
    catalog_path.write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {tag} at {source["sha"]}; review the diff and run scripts/check_catalog.py.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tag')
    args = parser.parse_args()
    promote(Path('.claude-plugin/marketplace.json'), args.tag)
