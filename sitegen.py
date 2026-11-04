#!/usr/bin/env python3
"""Rebuild and publish the whole site on gh-pages: docs/, data/versions.json (from state.json), the last few
Android versions as an F-Droid repo, and browser extension update manifests.
Runs after every build and on every commit; with nothing new in out/ it only refreshes the static parts."""
import datetime, glob, json, os, shutil
import pages, state
from fdroid_index import fdroid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = pages.REPO
KEEP = state.KEEP
STATE = state.load()


def versions(site):
    """data/versions.json: the last KEEP versions per target, with direct release download URLs."""
    out = {"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "repo": REPO}
    for target, entries in STATE.items():
        out[target] = []
        for i, e in enumerate(entries[:KEEP]):
            assets = []
            for a in e["assets"]:
                assets.append({**a, "release_url": f"https://github.com/{REPO}/releases/download/{e['tag']}/{a['name']}",
                               "pages": None})
            out[target].append({**e, "assets": assets, "release": f"https://github.com/{REPO}/releases/tag/{e['tag']}"})
    os.makedirs(f"{site}/data", exist_ok=True)
    with open(f"{site}/data/versions.json", "w") as stream:
        json.dump(out, stream, indent=1)


def fill(site):
    shutil.copytree(f"{HERE}/docs", site, dirs_exist_ok=True)  # the whole site lives at /
    if os.path.isdir(f"{HERE}/work/extra"):
        extra = f"{HERE}/work/extra"
        for path in glob.glob(f"{extra}/**/*", recursive=True):
            if os.path.isfile(path) and path.endswith((".json", ".xml")):
                dest = os.path.join(site, os.path.relpath(path, extra))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy(path, dest)
    # Old browser binaries are redundant: manifests point to release assets.
    for directory in ("chrome", "firefox"):
        for suffix in ("*.crx", "*.xpi"):
            for path in glob.glob(f"{site}/{directory}/{suffix}"):
                os.remove(path)
    fdroid(site, REPO)
    versions(site)


if __name__ == "__main__":
    os.chdir(HERE)
    pages.publish(fill)
