#!/usr/bin/env python3
"""Bitwarden Patched: fetch a Bitwarden client, patch it, build it.

  nano.py latest <target>        newest upstream release tag
  nano.py build  <target> [tag]  clone, patch, build; artifacts land in ./out
"""
import brand, glob, json, os, re, shutil, subprocess as sp, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def run(src, *cmd):
    sp.run(cmd, cwd=src, check=True)


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


def keystore():
    """Stable signing key from the environment (CI); otherwise a throwaway local one."""
    path, pw = os.environ.get("KEYSTORE"), os.environ.get("KS_PASS", "nanowarden")
    path = path or f"{HERE}/work/local.jks"
    if not os.path.exists(path):
        run(HERE, "keytool", "-genkeypair", "-keystore", path, "-alias", "nanowarden", "-storepass", pw,
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-dname", "CN=NanoWarden")
    return path, pw


def android(src):
    brand.android(src, sub)
    sub(src, "isPremium = profile.hasPremiumPersonally",
        r"isPremium = profile\.hasPremiumPersonally == true \|\|\s*profile\.hasPremiumFromOrganization == true,",
        "isPremium = true,")
    # The SDK comes from GitHub Packages; any valid token can read it.
    open(f"{src}/user.properties", "w").write(f"gitHubToken={os.environ['GITHUB_TOKEN']}\n")
    run(src, "./gradlew", "app:assembleFdroidRelease", "-q")
    ks, pw = keystore()
    apksigner = sorted(glob.glob(f"{os.environ['ANDROID_HOME']}/build-tools/*/apksigner"))[-1]
    for unsigned in glob.glob(f"{src}/app/build/outputs/apk/fdroid/release/*.apk"):
        abi = re.search(r"-(universal|x86_64|x86|armeabi-v7a|arm64-v8a)(?:-release)?(?:-unsigned)?\.apk$", unsigned)[1]
        run(src, apksigner, "sign", "--ks", ks, "--ks-pass", f"pass:{pw}", "--out", f"{src}/{abi}.apk", unsigned)
    return "*.apk"


def browser(src):
    brand.browser(src, sub)
    sub(src, "hasPremiumFromAnyOrganization === true ||",
        r"profile\?\.hasPremiumFromAnyOrganization === true \|\|\s*profile\?\.hasPremiumPersonally === true", "true")
    sub(src, "!!profile?.hasPremiumPersonally", r"!!profile\?\.hasPremiumPersonally", "true")
    run(src, "npm", "ci")
    for flavor in ("chrome", "firefox"):
        run(src, "npm", "run", f"dist:{flavor}", "--prefix", "apps/browser")
    return "apps/browser/dist/*.zip"


TARGETS = {  # name: (upstream repo, regex a release tag must match, build function)
    "android": ("bitwarden/android", r"-bwpm$", android),
    "browser": ("bitwarden/clients", r"^browser-v", browser),
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


def build(target, tag=None):
    repo, _, build_fn = TARGETS[target]
    tag = tag or latest(target)
    src = f"{HERE}/work/{target}"
    shutil.rmtree(src, ignore_errors=True)
    sp.run(["git", "clone", "-q", "--depth", "1", "--branch", tag, f"https://github.com/{repo}", src], check=True)
    artifacts = build_fn(src)
    os.makedirs(f"{HERE}/out", exist_ok=True)
    for f in glob.glob(f"{src}/{artifacts}", recursive=True):
        print("artifact:", shutil.copy(f, f"{HERE}/out/bitwarden-patched-{target}-{tag}-{os.path.basename(f)}"))
    # Corresponding source: the upstream tree with our patches applied (tracked files only, so no tokens or build output).
    files = sp.run(["git", "ls-files", "-z"], cwd=src, capture_output=True, check=True).stdout
    sp.run(["tar", "czf", f"{HERE}/out/bitwarden-patched-{target}-{tag}-source.tar.gz", "--null", "-T", "-",
            "--transform", f"s,^,bitwarden-patched-{target}-{tag}/,"], cwd=src, input=files, check=True)


if __name__ == "__main__":
    cmd, target, *rest = sys.argv[1:]
    print(latest(target)) if cmd == "latest" else build(target, *rest)
