"""Self-update support for the browser extension: a signed-off CRX for Chrome-family and a signed XPI for Firefox,
plus the update manifests served from GitHub Pages. Runs after `nano.py build browser`, before the release is created."""
import glob, hashlib, json, os, re, shutil, subprocess as sp, sys, zipfile

REPO, REL = os.environ["GITHUB_REPOSITORY"], os.environ["REL"]
SITE = f"https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}"
ASSET = f"https://github.com/{REPO}/releases/download/{REL}"


def sh(*cmd, **kw):
    kw.setdefault("text", True)
    return sp.run(cmd, check=True, **kw)


def chrome_id(pem):
    der = sh("openssl", "rsa", "-in", pem, "-pubout", "-outform", "DER", capture_output=True, text=False).stdout
    return "".join(chr(97 + int(c, 16)) for c in hashlib.sha256(der).hexdigest()[:32])


def chrome(version, pem):
    src = glob.glob("out/*chrome*.zip")[0]
    shutil.rmtree("work/crx", ignore_errors=True)
    zipfile.ZipFile(src).extractall("work/crx")
    m = json.load(open("work/crx/manifest.json"))
    m["update_url"] = f"{SITE}/chrome/updates.xml"
    json.dump(m, open("work/crx/manifest.json", "w"))
    crx = f"out/NanoWarden-{version}.crx"
    sh("npx", "-y", "crx3", "-p", pem, "-o", crx, "work/crx")
    xml = (f'<?xml version="1.0" encoding="UTF-8"?><gupdate xmlns="http://www.google.com/update2/response" protocol="2.0">'
           f'<app appid="{chrome_id(pem)}"><updatecheck codebase="{ASSET}/{os.path.basename(crx)}" version="{m["version"]}"/></app></gupdate>')
    return {"chrome/updates.xml": xml}


def firefox(version):
    src = glob.glob("out/*firefox*.zip")[0]
    if not os.environ.get("AMO_KEY"):
        print("AMO_KEY not set: skipping Firefox signing")
        return {}
    shutil.rmtree("work/ff", ignore_errors=True)
    zipfile.ZipFile(src).extractall("work/ff")
    try:  # AMO refuses a version it has already signed, e.g. a rebuild of the same upstream release
        sh("npx", "-y", "web-ext", "sign", "--channel=unlisted", "-s", "work/ff", "-a", "work/ffsigned",
           f"--api-key={os.environ['AMO_KEY']}", f"--api-secret={os.environ['AMO_SECRET']}")
    except sp.CalledProcessError:
        print("Firefox signing failed, skipping")
        return {}
    xpi = glob.glob("work/ffsigned/*.xpi")[0]
    out = f"out/NanoWarden-{version}.xpi"
    shutil.copy(xpi, out)
    ver = json.load(open("work/ff/manifest.json"))["version"]
    upd = {"addons": {"nanowarden@mkalmousli.github.io": {"updates": [{
        "version": ver, "update_link": f"{ASSET}/{os.path.basename(out)}",
        "update_hash": "sha256:" + hashlib.sha256(open(out, "rb").read()).hexdigest()}]}}}
    return {"firefox/updates.json": json.dumps(upd)}


def publish(files):
    """Push the update manifests to gh-pages, retrying if the Android job pushed meanwhile."""
    url = f"https://x-access-token:{os.environ['GITHUB_TOKEN']}@github.com/{REPO}"
    for _ in range(5):
        shutil.rmtree("work/pages", ignore_errors=True)
        if sp.run(["git", "clone", "-q", "--depth", "1", "--branch", "gh-pages", url, "work/pages"]).returncode:
            sh("git", "init", "-q", "-b", "single", "work/pages")  # first run: the Android job hasn't created it yet
            sh("git", "-C", "work/pages", "remote", "add", "origin", url)
        for path, text in files.items():
            os.makedirs(os.path.dirname(f"work/pages/{path}"), exist_ok=True)
            open(f"work/pages/{path}", "w").write(text)
        if sh("git", "-C", "work/pages", "branch", "--show-current", capture_output=True).stdout.strip() != "single":
            sh("git", "-C", "work/pages", "checkout", "-q", "--orphan", "single")  # Pages branch is always one commit
        sh("git", "-C", "work/pages", "add", "-A")
        sh("git", "-C", "work/pages", "-c", "user.name=nanowarden", "-c", "user.email=nanowarden@users.noreply.github.com",
           "commit", "-qm", "NanoWarden site and extension manifests")
        if sp.run(["git", "-C", "work/pages", "push", "-q", "--force", "origin", "single:gh-pages"]).returncode == 0:
            return
    sys.exit("could not push gh-pages")


if __name__ == "__main__":
    version = re.sub(r"^browser-v", "", sys.argv[1])
    os.makedirs("work", exist_ok=True)
    open("work/crx.pem", "w").write(open(os.environ["CRX_KEY"]).read())
    publish({**chrome(version, "work/crx.pem"), **firefox(version)})
