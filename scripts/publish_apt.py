"""Publish the rolling APT channel after desktop release creation (CI only)."""
import base64
import os
from pathlib import Path
import subprocess as sp
import tempfile
from apt_repository import build


def main():
    key = os.environ.get('APT_SIGNING_KEY')
    fingerprint = os.environ.get('APT_SIGNING_FINGERPRINT', '').replace(' ', '')
    if not key:
        print('APT channel not published: configure APT_SIGNING_KEY and APT_SIGNING_FINGERPRINT')
        return
    if len(fingerprint) != 40 or any(c not in '0123456789abcdefABCDEF' for c in fingerprint):
        raise ValueError('A full signing key fingerprint is required')
    repo = os.environ['GITHUB_REPOSITORY']
    tag = 'rolling-apt'
    with tempfile.TemporaryDirectory() as temporary:
        os.environ['GNUPGHOME'] = temporary
        sp.run(['gpg', '--batch', '--import'], input=base64.b64decode(key, validate=True), check=True)
        output = Path(temporary) / 'index'
        packages = build('out', output, fingerprint)
        os.environ['GH_REPO'] = repo
        gh = ['gh']
        found = sp.run([*gh, 'release', 'view', tag], capture_output=True)
        if found.returncode:
            sp.run([*gh, 'release', 'create', tag, '--prerelease', '--title', 'Rolling APT repository',
                    '--notes', 'Signed APT metadata and Debian packages. See docs/linux.md.'], check=True)
        # Upload payloads first, signatures last; retain older package assets for clients with cached indices.
        sp.run([*gh, 'release', 'upload', tag, *map(str, packages), '--clobber'], check=True)
        for name in ['Packages', 'Packages.gz', 'archive-keyring.gpg', 'Release', 'Release.gpg', 'InRelease']:
            sp.run([*gh, 'release', 'upload', tag, str(output / name), '--clobber'], check=True)


if __name__ == '__main__':
    main()
