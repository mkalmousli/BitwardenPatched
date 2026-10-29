#!/usr/bin/env python3
"""Rebuild and publish the whole site on gh-pages: docs/, data/versions.json (from state.json), the last few
Android versions as an F-Droid repo, and the browser extension files and update manifests.
Runs after every build and on every commit; with nothing new in out/ it only refreshes the static parts."""
import datetime, glob, hashlib, json, os, re, shutil, subprocess as sp, sys
import pages, state

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = pages.REPO
OWNER, NAME = REPO.split("/")
KEEP = state.KEEP
LIMIT = 95 * 1024 * 1024    # git refuses files over 100 MB
BUDGET = 850 * 1024 * 1024  # a Pages site may not exceed 1 GB
ABIS = r"universal|x86_64|x86|armeabi-v7a|arm64-v8a"
APPID = "com.x8bit.bitwarden.patched"
STATE = state.load()


def apk_tag(path):
    return re.match(rf"bitwarden-patched-android-(.+)-(?:{ABIS})\.apk$", os.path.basename(path))[1]


def fdroid(site):
    """Add new per-ABI APKs, rotate out old versions, and regenerate the index when anything changed."""
    if "KEYSTORE" not in os.environ:
        return  # a docs-only run: leave the F-Droid repo exactly as published
    repo = f"{site}/repo"
    os.makedirs(repo, exist_ok=True)
    changed = False
    for apk in glob.glob(f"{HERE}/out/bitwarden-patched-android-*.apk"):
        if apk.endswith("-universal.apk"):
            continue  # about 3x the size of the others; release only
        if os.path.getsize(apk) > LIMIT:
            print(f"skipping {os.path.basename(apk)}: over the git file limit")
            continue
        shutil.copy(apk, repo)
        changed = True
    present = {}
    for f in glob.glob(f"{repo}/*.apk"):
        present.setdefault(apk_tag(f), []).append(f)
    keep, total = [], 0
    for e in STATE["android"][:KEEP]:  # newest first; stop once the budget is used up, but always keep the newest
        size = sum(os.path.getsize(f) for f in present.get(e["tag"], []))
        if keep and total + size > BUDGET:
            break
        keep.append(e["tag"])
        total += size
    for tag, files in present.items():
        if tag not in keep:
            print("rotating out", tag)
            for f in files:
                os.remove(f)
            changed = True
    meta = hashlib.sha256(b"".join(open(f, "rb").read() for f in sorted(glob.glob(f"{HERE}/fdroid/**/*.*", recursive=True)) if os.path.isfile(f))).hexdigest()
    stamp = f"{site}/.fdroid-meta"
    meta_changed = not os.path.exists(stamp) or open(stamp).read() != meta
    if not changed and not meta_changed:
        return
    open(stamp, "w").write(meta)
    with open(f"{site}/config.yml", "w") as f:
        f.write(f"""repo_url: https://{OWNER}.github.io/{NAME}/repo
repo_name: Bitwarden Patched
repo_icon: icon.png
repo_description: Patched builds of the open-source Bitwarden Android app (unofficial fork, not affiliated with Bitwarden Inc.).
keystore: {os.environ['KEYSTORE']}
keystorepass: {os.environ['KS_PASS']}
keypass: {os.environ['KS_PASS']}
repo_keyalias: nanowarden
archive_older: 0
keydname: CN=NanoWarden
""")
    os.chmod(f"{site}/config.yml", 0o600)
    # Listing metadata (name, description, icon, screenshots) lives in fdroid/ and is applied on every reindex.
    os.makedirs(f"{site}/metadata", exist_ok=True)
    shutil.copy(f"{HERE}/fdroid/{APPID}.yml", f"{site}/metadata/")
    shutil.copytree(f"{HERE}/fdroid/locale", f"{site}/metadata/{APPID}", dirs_exist_ok=True)
    os.makedirs(f"{site}/icons", exist_ok=True)
    shutil.copy(f"{HERE}/fdroid/repo-icon.png", f"{site}/icons/icon.png")
    sp.run(["fdroid", "update", "--create-metadata", "--delete-unknown"], cwd=site, check=True)
    os.remove(f"{site}/config.yml")  # holds the key password; never publish it
    shutil.rmtree(f"{site}/metadata", ignore_errors=True)


def versions(site):
    """data/versions.json: the last KEEP versions per target, with a Pages URL for every file stored on the site."""
    out = {"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "repo": REPO}
    for target, entries in STATE.items():
        out[target] = []
        for i, e in enumerate(entries[:KEEP]):
            assets = []
            for a in e["assets"]:
                local = {".apk": "repo/" + a["name"]}.get(os.path.splitext(a["name"])[1])
                if i == 0 and a["name"].endswith(".crx"):
                    local = "chrome/bitwarden-patched.crx"
                if i == 0 and a["name"].endswith(".xpi"):
                    local = "firefox/bitwarden-patched.xpi"
                assets.append({**a, "release_url": f"https://github.com/{REPO}/releases/download/{e['tag']}/{a['name']}",
                               "pages": local if local and os.path.exists(f"{site}/{local}") else None})
            out[target].append({**e, "assets": assets, "release": f"https://github.com/{REPO}/releases/tag/{e['tag']}"})
    os.makedirs(f"{site}/data", exist_ok=True)
    json.dump(out, open(f"{site}/data/versions.json", "w"), indent=1)


def fill(site):
    shutil.copytree(f"{HERE}/docs", site, dirs_exist_ok=True)  # the whole site lives at /
    if os.path.isdir(f"{HERE}/work/extra"):
        shutil.copytree(f"{HERE}/work/extra", site, dirs_exist_ok=True)
    fdroid(site)
    versions(site)


if __name__ == "__main__":
    os.chdir(HERE)
    pages.publish(fill)
