import importlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules['pages'] = types.SimpleNamespace(REPO='mkalmousli/BitwardenPatched')
sitegen = importlib.import_module('sitegen')


class IDs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        self.ids.extend(value for key, value in attrs if key == 'id')


class SiteTests(unittest.TestCase):
    def test_ids_are_unique(self):
        parser = IDs()
        parser.feed((ROOT / 'docs/index.html').read_text())
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertIn('dl', parser.ids)
        self.assertIn('icon-dl', parser.ids)

    def test_release_downloads_and_binary_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            old = Path(directory) / 'firefox/bitwarden-patched.xpi'
            old.parent.mkdir()
            old.write_bytes(b'old binary')
            sitegen.fill(directory)
            self.assertFalse(old.exists())
            data = json.loads((Path(directory) / 'data/versions.json').read_text())
            for target, entries in sitegen.STATE.items():
                self.assertEqual(len(data[target]), min(len(entries), sitegen.KEEP))
                for entry in data[target]:
                    for asset in entry['assets']:
                        self.assertIsNone(asset['pages'])
                        self.assertIn('/releases/download/', asset['release_url'])

    def test_source_files_at_most_100_lines(self):
        extensions = {'.py', '.js', '.cjs', '.css', '.html', '.sh', '.yml', '.yaml'}
        import subprocess
        paths = subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard'], cwd=ROOT).decode().splitlines()
        for path in set(paths):
            file = ROOT / path
            if file.suffix in extensions and file.is_file():
                self.assertLessEqual(len(file.read_text().splitlines()), 100, path)


if __name__ == '__main__':
    unittest.main()
