import os
import pwd
from pathlib import Path
import shutil
import subprocess as sp
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from apt_repository import build


class AptTests(unittest.TestCase):
    def test_signed_repository_and_real_apt_download(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / 'gpg'
            home.mkdir(mode=0o700)
            previous = os.environ.get('GNUPGHOME')
            os.environ['GNUPGHOME'] = str(home)
            self.addCleanup(self.restore_home, previous)
            def run(*args, **kwargs):
                result = sp.run(args, capture_output=True, **kwargs)
                if result.returncode:
                    raise AssertionError(f'{args}: {result.stderr.decode()} {result.stdout.decode()}')
                return result
            run('gpg', '--batch', '--passphrase', '', '--quick-generate-key',
                'APT Test <test@example.invalid>', 'rsa2048', 'sign', '0')
            listing = run('gpg', '--with-colons', '--list-keys').stdout.decode()
            fingerprint = next(line.split(':')[9] for line in listing.splitlines() if line.startswith('fpr:'))
            package = root / 'fixture'
            (package / 'DEBIAN').mkdir(parents=True)
            (package / 'DEBIAN').chmod(0o755)
            (package / 'DEBIAN/control').write_text(
                'Package: bitwarden-patched-test\nVersion: 1.0\nArchitecture: all\n'
                'Maintainer: Test <test@example.invalid>\nDescription: APT integration fixture\n')
            repository = root / 'repo'
            repository.mkdir()
            run('dpkg-deb', '--root-owner-group', '--build', str(package), str(repository / 'fixture.deb'))
            build(repository, repository, fingerprint)
            run('gpg', '--batch', '--verify', str(repository / 'InRelease'))
            source = root / 'sources.list'
            source.write_text(f'deb [signed-by={repository}/archive-keyring.gpg] file:{repository} ./\n')
            for name in ['lists/partial', 'cache/archives/partial', 'empty']:
                (root / name).mkdir(parents=True)
            options = ['-o', f'Dir::Etc::sourcelist={source}', '-o', 'Dir::Etc::sourceparts=-',
                       '-o', f'Dir::State::lists={root}/lists', '-o', f'Dir::Cache={root}/cache',
                       '-o', f'Dir::Etc::parts={root}/empty', '-o', f'APT::Sandbox::User={pwd.getpwuid(os.getuid()).pw_name}',
                       '-o', 'Acquire::Languages=none']
            update = run('apt-get', *options, 'update')
            self.assertNotIn(b'NO_PUBKEY', update.stderr)
            run('apt-get', *options, 'download', 'bitwarden-patched-test', cwd=root)
            fetched = next(root.glob('bitwarden-patched-test*.deb'))
            self.assertEqual(fetched.read_bytes(), (repository / 'fixture.deb').read_bytes())

    @staticmethod
    def restore_home(previous):
        if previous is None:
            os.environ.pop('GNUPGHOME', None)
        else:
            os.environ['GNUPGHOME'] = previous


if __name__ == '__main__':
    unittest.main()
