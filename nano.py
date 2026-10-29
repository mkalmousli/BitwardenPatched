#!/usr/bin/env python3
"""Bitwarden Patched: fetch a Bitwarden client, patch it, build it.

  nano.py latest <target>        newest upstream release tag
  nano.py build  <target> [tag]  clone, patch, build; artifacts land in ./out
"""
import brand, glob, json, os, re, shutil, subprocess as sp, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def run(src, *cmd):
    sp.run(cmd, cwd=src, check=True, shell=sys.platform == "win32")  # npm and npx are .cmd shims on Windows


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
    # Speed: no lint (it only checks, never changes the APK), parallel project execution, a larger heap, the build cache.
    init = f"{src}/../speed.init.gradle"
    open(init, "w").write('allprojects { tasks.configureEach { if (name.startsWith("lint")) enabled = false } }\n')
    run(src, "./gradlew", "app:assembleFdroidRelease", "-q", "--parallel", "--build-cache", "--init-script", init,
        "-Dorg.gradle.jvmargs=-Xmx6g -XX:+UseParallelGC", "-Dkotlin.compiler.execution.strategy=in-process",
        "-Pkotlin.incremental=false", "-Dorg.gradle.workers.max=4")
    ks, pw = keystore()
    apksigner = sorted(glob.glob(f"{os.environ['ANDROID_HOME']}/build-tools/*/apksigner"))[-1]
    for unsigned in glob.glob(f"{src}/app/build/outputs/apk/fdroid/release/*.apk"):
        abi = re.search(r"-(universal|x86_64|x86|armeabi-v7a|arm64-v8a)(?:-release)?(?:-unsigned)?\.apk$", unsigned)[1]
        run(src, apksigner, "sign", "--ks", ks, "--ks-pass", f"pass:{pw}", "--out", f"{src}/{abi}.apk", unsigned)
    return "*.apk"


def clients_premium(src):
    """The premium check lives in libs/common, shared by the browser extension and the desktop app."""
    sub(src, "hasPremiumFromAnyOrganization === true ||",
        r"profile\?\.hasPremiumFromAnyOrganization === true \|\|\s*profile\?\.hasPremiumPersonally === true", "true")
    sub(src, "!!profile?.hasPremiumPersonally", r"!!profile\?\.hasPremiumPersonally", "true")


def browser(src):
    brand.browser(src, sub)
    clients_premium(src)
    run(src, "npm", "ci")
    for flavor in ("chrome", "firefox"):
        run(src, "npm", "run", f"dist:{flavor}", "--prefix", "apps/browser")
    return "apps/browser/dist/*.zip"


def desktop(src):
    """Windows, Linux and macOS builds; each CI job builds its own platform/arch natively (NANO_PLATFORM, e.g. windows-arm64)."""
    plat = os.environ.get("NANO_PLATFORM") or {"win32": "windows-x64", "darwin": "macos-arm64"}.get(sys.platform, "linux-x64")
    osname, arch = plat.split("-")
    brand.desktop(src, sub)
    clients_premium(src)
    app = f"{src}/apps/desktop"
    run(src, "npm", "ci")
    run(app, "npm", "run", "build-native")
    run(app, "npm", "run", "build:oss")
    targets = {"linux": ["--linux", "deb", "AppImage", "tar.gz"], "windows": ["--win", "nsis", "portable"], "macos": ["--mac", "dmg", "zip"]}[osname]
    run(app, "npx", "electron-builder", *targets, f"--{arch}", "-p", "never")
    return "apps/desktop/dist/*.@(exe|AppImage|deb|dmg|zip|tar.gz)"


TARGETS = {  # name: (upstream repo, regex a release tag must match, build function)
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
