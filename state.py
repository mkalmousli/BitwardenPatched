#!/usr/bin/env python3
"""state.json: what has been built, newest first, last KEEP versions per target.
  state.py record <target> <tag> <patch-hash>   add the files in out/ as a new entry"""
import datetime, glob, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILE = f"{HERE}/state.json"
KEEP = 7


def load():
    return json.load(open(FILE)) if os.path.exists(FILE) else {"android": [], "browser": [], "desktop": []}


def record(target, tag, ph):
    state = load()
    state.setdefault(target, [])
    assets = [{"name": os.path.basename(f), "size": os.path.getsize(f), "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest()}
              for f in sorted(glob.glob(f"{HERE}/out/*")) if not f.endswith("SHA256SUMS")]
    entry = {"tag": tag, "built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "patches": ph, "assets": assets}
    state[target] = [entry] + [e for e in state[target] if e["tag"] != tag]
    state[target].sort(key=lambda e: e["built"], reverse=True)
    state[target] = state[target][:KEEP]
    json.dump(state, open(FILE, "w"), indent=2)
    open(FILE, "a").write("\n")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    record(*args) if cmd == "record" else sys.exit("usage: state.py record <target> <tag> <patch-hash>")
