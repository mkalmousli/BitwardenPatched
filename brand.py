"""Client identity and branding entry points."""
import glob, json
import brand_about
from brand_images import fork_badge, stamp, vector_badge, NAME, PAGES
from brand_android import android

def browser(src, sub):
    brand_about.browser(src, sub)
    sub(src, '"Bitwarden Password Manager"', r'"message": "Bitwarden Password Manager"', f'"message": "{NAME}"')
    sub(src, '"extDesc"', r'("extDesc": \{\s*"message": )"[^"]*"',
        r'\1"Unofficial patch of Bitwarden. Source: https://github.com/mkalmousli/BitwardenPatched. Not affiliated with Bitwarden Inc."')
    sub(src, '"__firefox__browser_specific_settings"', r'"id": "\{446900e4-[^}]*\}"',  # own add-on id, so it never collides with the official one
        f'"id": "nanowarden@mkalmousli.github.io", "update_url": "{PAGES}/firefox/updates.json"')
    for f in glob.glob(f"{src}/apps/browser/src/images/icon*.png"):
        stamp(f)


def desktop(src, sub):
    """Own name and app id so it installs next to the official desktop app; no signing, notarising or store packaging."""
    brand_about.desktop(src, sub)
    path = f"{src}/apps/desktop/electron-builder.json"
    cfg = json.load(open(path))
    cfg["productName"], cfg["appId"] = NAME, "com.bitwarden.desktop.patched"
    cfg.setdefault("extraMetadata", {})["name"] = "bitwarden-patched"
    cfg["copyright"] = "GPL-3.0. Unofficial Bitwarden patch: github.com/mkalmousli/BitwardenPatched"
    cfg["extraMetadata"]["description"] = "Unofficial Bitwarden patch. Source: https://github.com/mkalmousli/BitwardenPatched"
    cfg["extraMetadata"]["homepage"] = "https://github.com/mkalmousli/BitwardenPatched"
    for hook in ("afterSign", "appxManifestCreated", "publish"):
        cfg.pop(hook, None)
    cfg.get("win", {}).pop("signtoolOptions", None)
    cfg.get("win", {}).pop("signExts", None)
    cfg["mac"].update({"identity": None, "hardenedRuntime": False, "gatekeeperAssess": False})
    for key in ("provisioningProfile", "entitlements", "entitlementsInherit"):
        cfg["mac"].pop(key, None)
    for kind in ("appImage", "deb", "rpm"):
        cfg.setdefault(kind, {})["artifactName"] = "bitwarden-patched-${version}-${arch}.${ext}"
    json.dump(cfg, open(path, "w"), indent=2)
    # The macOS part of the after-pack hook copies Swift extensions and signs with Bitwarden's Apple identity: skip it all.
    hook = f"{src}/apps/desktop/scripts/after-pack.js"
    text = open(hook).read()
    if "if (isMacOsBuild) {" not in text:
        raise SystemExit("RULE BROKEN, upstream changed: after-pack.js")
    open(hook, "w").write(text.replace("if (isMacOsBuild) {", "if (false && isMacOsBuild) {"))
