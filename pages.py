"""GitHub Pages publishing: the gh-pages branch is always exactly one parentless commit, and Pages is switched on if needed."""
import os, shutil, subprocess as sp, sys

REPO = os.environ["GITHUB_REPOSITORY"]
URL = f"https://x-access-token:{os.environ['GITHUB_TOKEN']}@github.com/{REPO}"
SITE = "work/site"


def git(*cmd, check=True, **kw):
    return sp.run(["git", "-C", SITE, *cmd], check=check, **kw)


def checkout():
    """Fresh clone of the live site, or an empty repo on first run. Returns the commit it started from."""
    shutil.rmtree(SITE, ignore_errors=True)
    if sp.run(["git", "clone", "-q", "--depth", "1", "--branch", "gh-pages", URL, SITE]).returncode:
        os.makedirs(SITE)
        git("init", "-q", "-b", "gh-pages")
        git("remote", "add", "origin", URL)
        return ""
    return git("rev-parse", "HEAD", capture_output=True, text=True).stdout.strip()


def publish(fill, message="Bitwarden Patched site"):
    """fill(site_dir) edits a fresh checkout; the result replaces gh-pages. If another job published in between,
    the push is refused (force-with-lease) and everything is redone on top of what it published."""
    for _ in range(5):
        base = checkout()
        fill(SITE)
        open(f"{SITE}/.nojekyll", "w").close()  # serve files as they are, no Jekyll
        git("checkout", "-q", "--orphan", "single")
        git("add", "-A", "-f")
        git("-c", "user.name=bitwarden-patched", "-c", "user.email=actions@users.noreply.github.com", "commit", "-qm", message)
        if git("push", "-q", f"--force-with-lease=refs/heads/gh-pages:{base}", "origin", "single:gh-pages", check=False).returncode == 0:
            enable()
            return
    sys.exit("could not push gh-pages")


def enable():
    """Point GitHub Pages at gh-pages (a no-op if already set up) and trigger a build."""
    sp.run(["gh", "api", "-X", "POST", f"repos/{REPO}/pages", "-f", "source[branch]=gh-pages", "-f", "source[path]=/"], capture_output=True)
    sp.run(["gh", "api", "-X", "POST", f"repos/{REPO}/pages/builds"], capture_output=True)
