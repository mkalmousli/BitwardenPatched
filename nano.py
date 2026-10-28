#!/usr/bin/env python3
"""NanoWarden: fetch a Bitwarden client, apply rules.json edits, build it.

  nano.py latest <target>          print the newest upstream release tag
  nano.py build  <target> [tag]    clone, patch, build; artifacts land in ./out
"""
import glob, json, os, re, shutil, subprocess as sp, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(f"{HERE}/rules.json"))


def latest(cfg):
    req = urllib.request.Request(f"https://api.github.com/repos/{cfg['repo']}/releases?per_page=60")
    if token := os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    for rel in json.load(urllib.request.urlopen(req)):
        if not rel["prerelease"] and re.search(cfg["tag"], rel["tag_name"]):
            return rel["tag_name"]
    sys.exit("no matching release")


def apply_rules(src, rules):
    """Locate each edit by its anchor text (files may move between releases), then rewrite it."""
    for rule in rules:
        hits = sp.run(["git", "grep", "-lF", rule["anchor"]], cwd=src, capture_output=True, text=True).stdout.split()
        hits = [h for h in hits if not re.search(r"spec|test|Test|mock", h)]
        done = 0
        for path in hits:
            text = open(f"{src}/{path}").read()
            new, n = re.subn(rule["find"], rule["with"], text)
            if n:
                open(f"{src}/{path}", "w").write(new)
                print(f"patched {path} ({n}x)")
                done += n
        if not done:
            sys.exit(f"RULE BROKEN, upstream changed: {rule['anchor']}")


def build(target, tag):
    cfg = CFG[target]
    tag = tag or latest(cfg)
    src = f"{HERE}/work/{target}"
    shutil.rmtree(src, ignore_errors=True)
    sp.run(["git", "clone", "-q", "--depth", "1", "--branch", tag, f"https://github.com/{cfg['repo']}", src], check=True)
    apply_rules(src, cfg["rules"])
    if target == "android":  # SDK comes from GitHub Packages; any valid token can read it
        open(f"{src}/user.properties", "w").write(f"gitHubToken={os.environ['GITHUB_TOKEN']}\n")
    for cmd in cfg["build"]:
        sp.run(cmd, cwd=src, check=True)
    os.makedirs(f"{HERE}/out", exist_ok=True)
    for f in glob.glob(f"{src}/{cfg['artifacts']}", recursive=True):
        dest = f"{HERE}/out/{target}-{tag}-{os.path.basename(f)}"
        shutil.copy(f, dest)
        print("artifact:", dest)


if __name__ == "__main__":
    cmd, target, *rest = sys.argv[1:]
    if cmd == "latest":
        print(latest(CFG[target]))
    else:
        build(target, rest[0] if rest else None)
