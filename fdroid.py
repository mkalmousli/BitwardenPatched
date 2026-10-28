#!/usr/bin/env python3
"""Publish out/*.apk into an F-Droid repository served from the gh-pages branch (GitHub Pages)."""
import glob, os, shutil, subprocess as sp

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
    run("git", "init", "-q", "-b", "gh-pages")
    run("git", "remote", "add", "origin", remote)

os.makedirs(f"{SITE}/repo", exist_ok=True)
for apk in glob.glob(f"{HERE}/out/android-*.apk"):
    shutil.copy(apk, f"{SITE}/repo/")
open(f"{SITE}/config.yml", "w").write(f"""repo_url: {URL}
repo_name: NanoWarden
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
open(f"{SITE}/.gitignore", "w").write("config.yml\nmetadata/\n")
run("git", "add", "-A")
run("git", "-c", "user.name=nanowarden", "-c", "user.email=actions@users.noreply.github.com",
    "commit", "-qm", "Update F-Droid repo")
run("git", "push", "-q", "origin", "HEAD:gh-pages")
