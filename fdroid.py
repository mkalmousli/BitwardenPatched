#!/usr/bin/env python3
"""Publish out/*.apk into an F-Droid repository served from the gh-pages branch (GitHub Pages)."""
import glob, os, re, shutil, subprocess as sp

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = f"{HERE}/work/site"
REPO = os.environ["GITHUB_REPOSITORY"]
OWNER, NAME = REPO.split("/")
URL = f"https://{OWNER}.github.io/{NAME}/repo"
PW = os.environ["KS_PASS"]


def run(*cmd, cwd=SITE):
    sp.run(cmd, cwd=cwd, check=True)


shutil.rmtree(SITE, ignore_errors=True)
remote = f"https://x-access-token:{os.environ['GITHUB_TOKEN']}@github.com/{REPO}"
if sp.run(["git", "ls-remote", "--exit-code", "--heads", remote, "gh-pages"], capture_output=True).returncode == 0:
    run("git", "clone", "-q", "--branch", "gh-pages", remote, SITE, cwd=HERE)
else:
    os.makedirs(SITE)
    run("git", "init", "-q", "-b", "single")
    run("git", "remote", "add", "origin", remote)

os.makedirs(f"{SITE}/repo", exist_ok=True)
for old in glob.glob(f"{SITE}/repo/*.apk"):
    os.remove(old)
apks = glob.glob(f"{HERE}/out/android-*.apk")
for apk in apks:
    shutil.copy(apk, f"{SITE}/repo/")
# An APK (~140 MB) exceeds git's 100 MB file limit, so it is not stored on the Pages branch: the index lists it and
# clients fetch it from the release asset through this mirror URL (the release tag is part of the file name).
TAG = re.match(r"android-(.+)-NanoWarden\.apk", os.path.basename(apks[0]))[1]
open(f"{SITE}/config.yml", "w").write(f"""repo_url: {URL}
repo_name: NanoWarden
mirrors:
  - https://github.com/{REPO}/releases/download/{TAG}
repo_description: Unofficial patched builds of the Bitwarden Android app (fork). Not affiliated with Bitwarden Inc.
keystore: {os.environ['KEYSTORE']}
keystorepass: {PW}
keypass: {PW}
repo_keyalias: nanowarden
keydname: CN=NanoWarden
""")
os.chmod(f"{SITE}/config.yml", 0o600)
run("fdroid", "update", "--create-metadata", "--delete-unknown")
os.remove(f"{SITE}/config.yml")  # holds the key password; never publish it
shutil.copy("docs/index.html", f"{SITE}/index.html")
open(f"{SITE}/.gitignore", "w").write("config.yml\nmetadata/\n*.apk\n")
if sp.run(["git", "branch", "--show-current"], cwd=SITE, capture_output=True, text=True).stdout.strip() != "single": run("git", "checkout", "-q", "--orphan", "single")  # Pages branch is always one commit, no history
run("git", "add", "-A")
run("git", "-c", "user.name=nanowarden", "-c", "user.email=actions@users.noreply.github.com",
    "commit", "-qm", "NanoWarden site and F-Droid repo")
run("git", "push", "-q", "--force", "origin", "single:gh-pages")
