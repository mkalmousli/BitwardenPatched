"""Render the website locally without importing the credentialed publisher."""
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules['pages'] = types.SimpleNamespace(REPO='mkalmousli/BitwardenPatched')
import sitegen

if __name__ == '__main__':
    if 'KEYSTORE' in os.environ:
        raise SystemExit('Local rendering requires an environment without KEYSTORE')
    output = ROOT / 'work/local-site'
    output.mkdir(parents=True, exist_ok=True)
    sitegen.fill(str(output))
    print(f'Local website: {output}')
