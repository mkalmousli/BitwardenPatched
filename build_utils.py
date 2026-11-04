"""Shared source patching and command execution."""
import os, re, subprocess as sp, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def run(src, *cmd):
    sp.run(cmd, cwd=src, check=True, shell=sys.platform == "win32")  # npm and npx are .cmd shims on Windows


def sub(src, anchor, find, repl):
    """Rewrite code matching regex `find` in whichever file contains `anchor` (files may move between releases)."""
    grep = sp.run(["git", "grep", "-lF", "-e", anchor], cwd=src, capture_output=True, text=True)
    done = 0
    for path in (p for p in grep.stdout.split() if not re.search(r"spec|test|Test|mock", p)):
        text = open(f"{src}/{path}").read()
        new, n = re.subn(find, repl, text)
        if n:
            open(f"{src}/{path}", "w").write(new)
            print(f"patched {path} ({n}x)")
            done += n
    if not done:
        sys.exit(f"RULE BROKEN, upstream changed: {anchor}")


