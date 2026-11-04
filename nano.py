#!/usr/bin/env python3
"""Bitwarden Patched: fetch a Bitwarden client, patch it, build it.

  nano.py latest <target>        newest upstream release tag
  nano.py build  <target> [tag]  clone, patch, build; artifacts land in ./out
"""
import glob, json, os, re, shutil, subprocess as sp, sys, urllib.request

from build_targets import android, browser, desktop
from build_utils import sub

HERE = os.path.dirname(os.path.abspath(__file__))


TARGETS = {
    "android": ("bitwarden/android", r"-bwpm$", android),
    "browser": ("bitwarden/clients", r"^browser-v", browser),
    "desktop": ("bitwarden/clients", r"^desktop-v", desktop),
}


def latest(target):
    repo, pattern, _ = TARGETS[target]
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases?per_page=60")
    if token := os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    for rel in json.load(urllib.request.urlopen(req)):
        if not rel["prerelease"] and re.search(pattern, rel["tag_name"]):
            return rel["tag_name"]
    sys.exit("no matching release")


def artifacts_glob(pattern):
    """Expand a trailing @(a|b|c) alternative into separate globs."""
    m = re.search(r"@\((.*?)\)", pattern)
    return [pattern[:m.start()] + alt + pattern[m.end():] for alt in m[1].split("|")] if m else [pattern]


def build(target, tag=None):
    repo, _, build_fn = TARGETS[target]
    tag = tag or latest(target)
    src = f"{HERE}/work/{target}"
    shutil.rmtree(src, ignore_errors=True)
    sp.run(["git", "clone", "-q", "--depth", "1", "--branch", tag, f"https://github.com/{repo}", src], check=True)
    artifacts = build_fn(src)
    os.makedirs(f"{HERE}/out", exist_ok=True)
    label = os.environ.get("NANO_PLATFORM", "")  # desktop: file names do not always carry the OS and arch
    for pattern in artifacts_glob(artifacts):
        for f in glob.glob(f"{src}/{pattern}", recursive=True):
            name = re.sub(r"[ _]+", "-", os.path.basename(f)).replace("Bitwarden-Patched", "bitwarden-patched")
            name = re.sub(r"^bitwarden-patched-", "", name)
            name = f"{label}-{name}" if label else name
            print("artifact:", shutil.copy(f, f"{HERE}/out/bitwarden-patched-{target}-{tag}-{name}"))
    if os.environ.get("NANO_SOURCE") == "0":
        return
    # Corresponding source: the upstream tree with our patches applied (tracked files only, so no tokens or build output).
    files = sp.run(["git", "ls-files", "-z"], cwd=src, capture_output=True, check=True).stdout
    sp.run(["tar", "czf", f"{HERE}/out/bitwarden-patched-{target}-{tag}-source.tar.gz", "--null", "-T", "-",
            "--transform", f"s,^,bitwarden-patched-{target}-{tag}/,"], cwd=src, input=files, check=True)


if __name__ == "__main__":
    cmd, target, *rest = sys.argv[1:]
    print(latest(target)) if cmd == "latest" else build(target, *rest)
