#!/usr/bin/env python3
"""NanoWarden: fetch a Bitwarden client, apply the TARGETS rules below, build it.

  nano.py latest <target>        newest upstream release tag
  nano.py build  <target> [tag]  clone, patch, build; artifacts land in ./out
"""
import glob, json, os, re, shutil, subprocess as sp, sys, urllib.request
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))

@dataclass
class Rule:
    """anchor locates the file (tolerates moves between releases); find is a regex, sub its replacement."""
    anchor: str
    find: str
    sub: str

@dataclass
class Target:
    repo: str
    tag: str  # regex a release tag must match
    rules: list[Rule]
    build: list[list[str]]
    artifacts: str  # glob relative to the source root

TARGETS = {
    "android": Target(
        repo="bitwarden/android",
        tag="-bwpm$",
        rules=[Rule(
            "isPremium = profile.hasPremiumPersonally",
            r"isPremium = profile\.hasPremiumPersonally == true \|\|\s*profile\.hasPremiumFromOrganization == true,",
            "isPremium = true,",
        )],
        build=[["./gradlew", "app:assembleFdroidDebug", "-q"]],
        artifacts="app/build/outputs/apk/**/*.apk",
    ),
    "browser": Target(
        repo="bitwarden/clients",
        tag="^browser-v",
        rules=[
            Rule("hasPremiumFromAnyOrganization === true ||",
                 r"profile\?\.hasPremiumFromAnyOrganization === true \|\|\s*profile\?\.hasPremiumPersonally === true", "true"),
            Rule("!!profile?.hasPremiumPersonally", r"!!profile\?\.hasPremiumPersonally", "true"),
        ],
        build=[["npm", "ci"]] + [["npm", "run", f"dist:{b}", "--prefix", "apps/browser"] for b in ("chrome", "firefox")],
        artifacts="apps/browser/dist/*.zip",
    ),
}


def latest(t):
    req = urllib.request.Request(f"https://api.github.com/repos/{t.repo}/releases?per_page=60")
    if token := os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    for rel in json.load(urllib.request.urlopen(req)):
        if not rel["prerelease"] and re.search(t.tag, rel["tag_name"]):
            return rel["tag_name"]
    sys.exit("no matching release")


def apply_rules(src, rules):
    """Locate each edit by its anchor text (files may move between releases), then rewrite it."""
    for rule in rules:
        grep = sp.run(["git", "grep", "-lF", rule.anchor], cwd=src, capture_output=True, text=True)
        done = 0
        for path in (h for h in grep.stdout.split() if not re.search(r"spec|test|Test|mock", h)):
            text = open(f"{src}/{path}").read()
            new, n = re.subn(rule.find, rule.sub, text)
            if n:
                open(f"{src}/{path}", "w").write(new)
                print(f"patched {path} ({n}x)")
                done += n
        if not done:
            sys.exit(f"RULE BROKEN, upstream changed: {rule.anchor}")


def build(target, tag):
    t = TARGETS[target]
    tag = tag or latest(t)
    src = f"{HERE}/work/{target}"
    shutil.rmtree(src, ignore_errors=True)
    sp.run(["git", "clone", "-q", "--depth", "1", "--branch", tag, f"https://github.com/{t.repo}", src], check=True)
    apply_rules(src, t.rules)
    if target == "android":  # SDK comes from GitHub Packages; any valid token can read it
        open(f"{src}/user.properties", "w").write(f"gitHubToken={os.environ['GITHUB_TOKEN']}\n")
    for cmd in t.build:
        sp.run(cmd, cwd=src, check=True)
    os.makedirs(f"{HERE}/out", exist_ok=True)
    for f in glob.glob(f"{src}/{t.artifacts}", recursive=True):
        print("artifact:", shutil.copy(f, f"{HERE}/out/{target}-{tag}-{os.path.basename(f)}"))


if __name__ == "__main__":
    cmd, target, *rest = sys.argv[1:]
    if cmd == "latest":
        print(latest(TARGETS[target]))
    else:
        build(target, rest[0] if rest else None)
