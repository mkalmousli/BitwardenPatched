import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import fdroid_index

ROOT = Path(__file__).resolve().parents[1]


class FdroidTests(unittest.TestCase):
    def prepare(self, root):
        shutil.copytree(ROOT / 'fdroid', root / 'fdroid')
        (root / 'out').mkdir()
        site = root / 'site'
        (site / 'repo').mkdir(parents=True)
        for tag in ['v3', 'v2', 'v1']:
            (site / 'repo' / f'bitwarden-patched-android-{tag}-x86-64.apk').write_bytes(b'apk')
        (root / 'out/bitwarden-patched-android-v3-universal.apk').write_bytes(b'universal')
        (root / 'state.json').write_text(json.dumps({'android': [{'tag': t} for t in ['v3', 'v2', 'v1']]}))
        return site

    def test_rotation_preserves_x86_alias_and_upstream_screenshots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = self.prepare(root)
            with patch.object(fdroid_index, 'HERE', temporary), \
                 patch.object(fdroid_index.state, 'FILE', str(root / 'state.json')), \
                 patch.dict(os.environ, {'KEYSTORE': 'test.jks', 'KS_PASS': 'test-only'}), \
                 patch.object(fdroid_index.sp, 'run') as update:
                fdroid_index.fdroid(str(site), 'mkalmousli/BitwardenPatched')
                update.assert_called_once()
            self.assertEqual(len(list((site / 'repo').glob('*.apk'))), 2)
            self.assertFalse((site / 'repo/bitwarden-patched-android-v1-x86-64.apk').exists())
            self.assertFalse((site / 'config.yml').exists())
            for index in range(2, 5):
                self.assertTrue((ROOT / f'fdroid/locale/en-US/phoneScreenshots/{index}.png').exists())

    def test_signing_failure_removes_password_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = self.prepare(root)
            with patch.object(fdroid_index, 'HERE', temporary), \
                 patch.object(fdroid_index.state, 'FILE', str(root / 'state.json')), \
                 patch.dict(os.environ, {'KEYSTORE': 'test.jks', 'KS_PASS': 'test-only'}), \
                 patch.object(fdroid_index.sp, 'run', side_effect=subprocess.CalledProcessError(1, 'fdroid')):
                with self.assertRaises(subprocess.CalledProcessError):
                    fdroid_index.fdroid(str(site), 'mkalmousli/BitwardenPatched')
            self.assertFalse((site / 'config.yml').exists())


if __name__ == '__main__':
    unittest.main()
