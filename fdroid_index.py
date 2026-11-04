"""F-Droid indexing. APKs stay local because signed indices need real files."""
import glob, os, shutil, subprocess as sp
import state
HERE = os.path.dirname(os.path.abspath(__file__))
KEEP = 2
LIMIT = 95 * 1024 * 1024
BUDGET = 600 * 1024 * 1024
APPID = "com.x8bit.bitwarden.patched"
PRIORITY = ["arm64-v8a", "armeabi-v7a", "x86_64", "x86"]


def fdroid(site, repo_name):
    """Add new per-ABI APKs, rotate out old versions, and regenerate the signed index (with the listing metadata from fdroid/) every run."""
    if "KEYSTORE" not in os.environ:
        return  # a docs-only run: leave the F-Droid repo exactly as published
    OWNER, NAME = repo_name.split("/")
    STATE = state.load()
    repo = f"{site}/repo"
    os.makedirs(repo, exist_ok=True)
    for apk in glob.glob(f"{HERE}/out/bitwarden-patched-android-*.apk"):
        if apk.endswith("-universal.apk"):
            continue  # about 3x the size of the others; release only
        if os.path.getsize(apk) > LIMIT:
            print(f"skipping {os.path.basename(apk)}: over the git file limit")
            continue
        shutil.copy(apk, repo)
    present = {}
    for f in glob.glob(f"{repo}/*.apk"):
        present[os.path.basename(f)] = f
    # Newest version first, and within a version the most common CPUs first; a file is kept while the budget lasts.
    # Older versions stay downloadable from the GitHub releases, so only the Pages copy is dropped.
    keep, total = set(), 0
    for e in STATE["android"][:KEEP]:
        for abi in PRIORITY:
            name = f"bitwarden-patched-android-{e['tag']}-{abi}.apk"
            if name not in present and abi == "x86_64":
                name = name.replace("x86_64.apk", "x86-64.apk")
            if name in present and (not keep or total + os.path.getsize(present[name]) <= BUDGET):
                keep.add(name)
                total += os.path.getsize(present[name])
    for name, f in present.items():
        if name not in keep:
            print("rotating out", name)
            os.remove(f)
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
    os.makedirs(f"{site}/repo/icons", exist_ok=True)
    shutil.copy(f"{HERE}/fdroid/repo-icon.png", f"{site}/repo/icons/icon.png")
    try:
        sp.run(["fdroid", "update", "--create-metadata", "--delete-unknown"], cwd=site, check=True)
    finally:
        os.remove(f"{site}/config.yml")  # holds the key password; never publish it
    shutil.rmtree(f"{site}/metadata", ignore_errors=True)


