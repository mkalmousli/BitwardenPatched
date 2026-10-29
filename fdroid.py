#!/usr/bin/env python3
"""Publish the per-ABI APKs from out/ as an F-Droid repository on the gh-pages branch (GitHub Pages)."""
import glob, os, shutil, subprocess as sp, sys
import pages

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = f"{HERE}/work/site"
REPO = os.environ["GITHUB_REPOSITORY"]
OWNER, NAME = REPO.split("/")
URL = f"https://{OWNER}.github.io/{NAME}/repo"
PW = os.environ["KS_PASS"]
LIMIT = 95 * 1024 * 1024  # git refuses files over 100 MB

pages.checkout(SITE)
os.makedirs(f"{SITE}/repo", exist_ok=True)
for old in glob.glob(f"{SITE}/repo/*.apk"):
    os.remove(old)
apks = [a for a in glob.glob(f"{HERE}/out/bitwarden-patched-android-*.apk") if not a.endswith("-universal.apk")]
if not apks:
    sys.exit("no per-ABI APKs in out/")
for apk in apks:
    if os.path.getsize(apk) > LIMIT:
        print(f"skipping {os.path.basename(apk)}: over the git file limit, so it is not in the F-Droid repo")
    else:
        shutil.copy(apk, f"{SITE}/repo/")
open(f"{SITE}/config.yml", "w").write(f"""repo_url: {URL}
repo_name: Bitwarden Patched
repo_description: Patched builds of the open-source Bitwarden Android app (unofficial fork, not affiliated with Bitwarden Inc.).
keystore: {os.environ['KEYSTORE']}
keystorepass: {PW}
keypass: {PW}
repo_keyalias: nanowarden
keydname: CN=NanoWarden
""")
os.chmod(f"{SITE}/config.yml", 0o600)
sp.run(["fdroid", "update", "--create-metadata", "--delete-unknown"], cwd=SITE, check=True)
os.remove(f"{SITE}/config.yml")  # holds the key password; never publish it
shutil.rmtree(f"{SITE}/metadata", ignore_errors=True)
if not pages.push(SITE, "Bitwarden Patched site and F-Droid repo"):
    sys.exit("could not push gh-pages")
