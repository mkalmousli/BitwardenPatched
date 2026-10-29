#!/usr/bin/env python3
"""Decide what CI has to build: newest upstream tag per target, minus targets whose release already carries the current
patch hash. Writes the job matrix (one entry per ABI / platform) and the tags to $GITHUB_OUTPUT."""
import hashlib, json, os, subprocess as sp
import nano

HERE = os.path.dirname(os.path.abspath(__file__))
PH = hashlib.sha1(b"".join(open(f"{HERE}/{f}", "rb").read() for f in ("nano.py", "brand.py", "ext.py", "release.py", "fingerprint.txt"))).hexdigest()[:7]
UBU = "ubuntu-latest"
MATRIX = {  # target: [(job id, runner, extra matrix keys)]
    "android": [(abi, UBU, {"abi": abi}) for abi in ("arm64-v8a", "armeabi-v7a", "x86_64", "x86", "universal")],
    "browser": [("browser", UBU, {})],
    "desktop": [("linux-x64", UBU, {}), ("linux-arm64", "ubuntu-24.04-arm", {}), ("windows-x64", "windows-latest", {}),
                ("windows-arm64", "windows-11-arm", {}), ("macos-arm64", "macos-latest", {}), ("macos-x64", "macos-15-intel", {})],
}
include, tags = [], {}
for target, jobs in MATRIX.items():
    tag = nano.latest(target)
    body = sp.run(["gh", "release", "view", tag, "--json", "body", "--jq", ".body"], capture_output=True, text=True).stdout
    if f"patches {PH}" in body:
        print(f"{target} {tag}: already built")
        continue
    tags[target] = {"tag": tag, "ph": PH}
    for i, (id_, runner, extra) in enumerate(jobs):
        include.append({"target": target, "id": id_, "os": runner, "platform": id_ if target == "desktop" else "",
                        "source": "1" if i == 0 else "0", **extra})
out = os.environ.get("GITHUB_OUTPUT")
lines = {"matrix": json.dumps({"include": include}), "tags": json.dumps(tags), "any": "1" if include else "0"}
print(json.dumps(lines, indent=1))
if out:
    open(out, "a").write("".join(f"{k}={v}\n" for k, v in lines.items()))
