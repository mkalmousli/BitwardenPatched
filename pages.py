"""Shared GitHub Pages publishing: the gh-pages branch is always exactly one commit, and Pages is switched on if it is not yet."""
import os, shutil, subprocess as sp, sys

REPO = os.environ["GITHUB_REPOSITORY"]
URL = f"https://x-access-token:{os.environ['GITHUB_TOKEN']}@github.com/{REPO}"


def git(site, *cmd, **kw):
    return sp.run(["git", "-C", site, *cmd], check=kw.pop("check", True), **kw)


def checkout(site):
    """Fresh clone of the current site (to keep files other jobs published), or an empty repo on first run."""
    shutil.rmtree(site, ignore_errors=True)
    if sp.run(["git", "clone", "-q", "--depth", "1", "--branch", "gh-pages", URL, site]).returncode:
        os.makedirs(site)
        git(site, "init", "-q", "-b", "gh-pages")
        git(site, "remote", "add", "origin", URL)


def push(site, message):
    """Replace gh-pages with one parentless commit of `site`; returns False if the push was rejected."""
    shutil.copytree(f"{os.path.dirname(os.path.abspath(__file__))}/docs", site, dirs_exist_ok=True)  # the whole site lives at /
    open(f"{site}/.nojekyll", "w").close()  # serve files as they are, no Jekyll processing
    git(site, "checkout", "-q", "--orphan", "single")
    git(site, "add", "-A", "-f")
    git(site, "-c", "user.name=bitwarden-patched", "-c", "user.email=actions@users.noreply.github.com", "commit", "-qm", message)
    ok = git(site, "push", "-q", "--force", "origin", "single:gh-pages", check=False).returncode == 0
    if ok:
        enable()
    return ok


def enable():
    """Point GitHub Pages at gh-pages (a no-op if already set up) and trigger a build."""
    sp.run(["gh", "api", "-X", "POST", f"repos/{REPO}/pages", "-f", "source[branch]=gh-pages", "-f", "source[path]=/"], capture_output=True)
    sp.run(["gh", "api", "-X", "POST", f"repos/{REPO}/pages/builds"], capture_output=True)


def publish(files, message="Bitwarden Patched site"):
    """Write {path: text or bytes} into the site and push, retrying if the other job pushed meanwhile."""
    for _ in range(5):
        checkout("work/pages")
        for path, text in files.items():
            os.makedirs(os.path.dirname(f"work/pages/{path}"), exist_ok=True)
            open(f"work/pages/{path}", "wb" if isinstance(text, bytes) else "w").write(text)
        if push("work/pages", message):
            return
    sys.exit("could not push gh-pages")
