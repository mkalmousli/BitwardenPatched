"""Build a signed flat APT repository; payloads live in GitHub Releases."""
import datetime
from email.utils import format_datetime
import gzip
import hashlib
from pathlib import Path
import subprocess as sp


def run(*args, **kwargs):
    return sp.run(args, check=True, **kwargs)


def build(source, output, fingerprint):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    packages = sorted(Path(source).glob('*.deb'))
    if not packages:
        raise ValueError('No Debian packages to index')
    records = []
    for package in packages:
        control = run('dpkg-deb', '-f', str(package), capture_output=True, text=True).stdout
        with package.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        records.append(control.rstrip() + '\n' +
                       f'Filename: {package.name}\nSize: {package.stat().st_size}\nSHA256: {digest}\n')
    index = ('\n'.join(records) + '\n').encode()
    (output / 'Packages').write_bytes(index)
    (output / 'Packages.gz').write_bytes(gzip.compress(index, mtime=0))
    now = format_datetime(datetime.datetime.now(datetime.timezone.utc))
    architectures = sorted({run('dpkg-deb', '-f', str(p), 'Architecture',
                                capture_output=True, text=True).stdout.strip() for p in packages})
    release = ["Origin: Bitwarden Patched", "Label: Bitwarden Patched", f"Date: {now}",
               "Architectures: " + " ".join(architectures), "SHA256:"]
    for name in ('Packages', 'Packages.gz'):
        content = (output / name).read_bytes()
        release.append(f" {hashlib.sha256(content).hexdigest()} {len(content)} {name}")
    (output / 'Release').write_text('\n'.join(release) + '\n')
    for name, mode in [('InRelease', '--clearsign'), ('Release.gpg', '--detach-sign')]:
        run('gpg', '--batch', '--yes', '--local-user', fingerprint, '--digest-algo', 'SHA256',
            '--output', str(output / name), mode, str(output / 'Release'))
    key = run('gpg', '--batch', '--export', fingerprint, capture_output=True).stdout
    if not key:
        raise ValueError('Signing public key was not exported')
    (output / 'archive-keyring.gpg').write_bytes(key)
    return packages
