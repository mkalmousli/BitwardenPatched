#!/usr/bin/env python3
"""Write the GitHub release notes for the files in out/:  release.py <target> <tag> <patch-hash> > notes.md"""
import glob, hashlib, os, re, subprocess as sp, sys

target, tag, ph = sys.argv[1:4]
REPO = os.environ["GITHUB_REPOSITORY"]
SITE = f"https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}"
UPSTREAM = {"android": "bitwarden/android", "browser": "bitwarden/clients"}[target]
FP = open(f"{os.path.dirname(os.path.abspath(__file__))}/fingerprint.txt").read().strip()

WHAT = {  # file name suffix: (label, who it is for)
    "arm64-v8a.apk": ("Android, arm64-v8a", "**Most phones made since 2017.** Pick this if unsure."),
    "armeabi-v7a.apk": ("Android, armeabi-v7a", "Older 32-bit ARM phones and tablets."),
    "x86_64.apk": ("Android, x86_64", "Emulators, Chromebooks and Intel/AMD Android devices."),
    "x86.apk": ("Android, x86", "Old 32-bit x86 emulators."),
    "universal.apk": ("Android, universal", "Works everywhere, but about 3x larger than the matching ABI build."),
    "dist-chrome.zip": ("Chrome / Edge / Brave, zip", "Load unpacked via `chrome://extensions` (unzip first)."),
    "dist-firefox.zip": ("Firefox, zip", "Temporary add-on via `about:debugging`."),
    "source.tar.gz": ("Patched source", "Upstream tree with this project's patches applied (GPL-3.0 source offer)."),
}
ORDER = list(WHAT)


def kind(name):
    return next((k for k in ORDER if name.endswith(k)), None) or ("crx" if name.endswith(".crx") else "xpi" if name.endswith(".xpi") else name)


def size(n):
    return f"{n / 1048576:.1f} MB"


files = sorted(glob.glob("out/*"), key=lambda f: (ORDER.index(kind(f)) if kind(f) in ORDER else 99, f))
base = f"https://github.com/{REPO}/releases/download/{tag}"
rows = []
for f in files:
    n, k = os.path.basename(f), kind(f)
    label, note = WHAT.get(k, ({"crx": "Chrome family, self-updating CRX", "xpi": "Firefox, signed self-updating XPI"}.get(k, n), ""))
    note = note or {"crx": "Drag onto `chrome://extensions` (Linux) or deploy by policy; updates itself.",
                    "xpi": "Open in Firefox and click Add; updates itself."}.get(k, "")
    rows.append(f"| [**{label}**]({base}/{n}) | {note} | {size(os.path.getsize(f))} | `{hashlib.sha256(open(f, 'rb').read()).hexdigest()[:16]}…` |")

ver = tag.replace("browser-", "").replace("-bwpm", "")
badges = " ".join(f"![{a}](https://img.shields.io/github/downloads/{REPO}/{tag}/{b}?label={a}&color=0f766e&style=flat-square)"
                  for a, b in (("downloads", "total"),)) + \
    f" ![all releases](https://img.shields.io/github/downloads/{REPO}/total?label=all%20releases&color=175ddc&style=flat-square)" \
    f" ![upstream](https://img.shields.io/badge/upstream-{ver.replace('-', '--')}-175ddc?style=flat-square)" \
    f" ![license](https://img.shields.io/badge/license-GPL--3.0-lightgrey?style=flat-square)"

lines = [badges, "",
         f"Patched build of **{'Bitwarden for Android' if target == 'android' else 'the Bitwarden browser extension'} {ver}**, "
         f"built from the official [`{tag}`](https://github.com/{UPSTREAM}/releases/tag/{tag}) release. Same version number as upstream.", ""]
if target == "android":
    lines += ["## Install", "",
              f"- **Easiest, with automatic updates:** add `{SITE}/repo?fingerprint={FP}` to F-Droid, Droidify or Neo Store.",
              "- **Or download the APK for your phone's CPU** below. Not sure? Take `arm64-v8a`.",
              "- Installs next to the official app (`com.x8bit.bitwarden.patched`); it never replaces it.", ""]
else:
    lines += ["## Install", "",
              f"- **Firefox / Chrome with automatic updates:** use the `.xpi` / `.crx` below (update manifests are served from {SITE}).",
              "- Zips work everywhere as an unpacked extension but do not update themselves.", ""]
lines += ["## Downloads", "", "| File | For | Size | SHA-256 |", "|---|---|---|---|", *rows, "",
          "Full checksums are in the `SHA256SUMS` asset. GitHub also attaches the repository source (`Source code`, zip and tar.gz) to every release.", ""]
if target == "android":
    lines += [f"APK signing certificate SHA-256: `{FP}`", ""]
lines += ["## What is patched", "",
          "- The client-side premium check is always on (built-in TOTP codes and other local features).",
          "- Own name, application id and a fork badge on the original logo.",
          "- Android: one APK per CPU architecture." if target == "android" else "- Own Firefox add-on id and Chrome update channel.",
          f"- Nothing else changes. [Full patch list]({'https://github.com/' + REPO}#patches).", "",
          "Server-enforced features still follow your account's plan. Unofficial, not affiliated with Bitwarden Inc.", "",
          f"<sub>patches {ph}</sub>"]
print("\n".join(lines))
