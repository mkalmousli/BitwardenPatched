# NanoWarden

**Patched, automatically updated builds of the official Bitwarden apps: Android and the Chrome/Firefox browser extension.**

## What is this?

Bitwarden's clients are open source (GPL-3.0), but several features in the official apps are switched on only for
accounts the client considers "premium", most notably **built-in TOTP / authenticator codes** (the one-time codes
for two-factor login). NanoWarden takes the official source, changes the client-side check so these features are
available, builds it, and publishes the result on the [Releases](../../releases) page.

- It is a **patch layer, not a copy of the source**. This repo holds no Bitwarden code, only the patch logic (`nano.py`) and the automation.
- It **stays current by itself**. A GitHub Actions workflow checks for new official releases every 6 hours,
  patches and builds them, and publishes the new version.
- If an upstream change breaks a patch, the build fails loudly and opens an issue instead of shipping something wrong.

**Website:** https://mkalmousli.github.io/NanoWarden (one-click install links and latest downloads)

## F-Droid repository (Android)

Add this repository to F-Droid, Droidify, Neo Store or any F-Droid client, and updates arrive automatically:

```
https://mkalmousli.github.io/NanoWarden/repo?fingerprint=B1D78FEC2A8513EFD0EF78AE2C73887DFDC84F4CE6C786C61D524E1D4B43821B
```

(F-Droid → Settings → Repositories → **+**, or open the link on your phone.) The fingerprint pins the signing key.

## Website branch

GitHub Pages is served from the `gh-pages` branch, which holds no history: every publish replaces it with a single commit.

## Browser extension auto-updates

Releases include a self-updating `.xpi` (Firefox) and `.crx` (Chrome family), served with update manifests from the website. The Firefox build is signed through Mozilla's unlisted channel and needs the repo secrets `AMO_KEY` and `AMO_SECRET`; without them only the zip and CRX are produced. Chrome on Windows/macOS accepts off-store CRX files only via enterprise policy.

## Branding

To avoid confusion with the official app, builds are clearly marked as a fork: the app and extension are named
**NanoWarden** with their own teal logo and colour scheme, the Android application id is `com.x8bit.bitwarden.nano` (it installs *next to* the
official app instead of replacing it), and the browser extension carries the same name.

## Downloads

Go to [Releases](../../releases):

| Target | File | Install |
|---|---|---|
| `android` | `*.apk` | Sideload on Android 8+ (signed with the NanoWarden key; prefer the F-Droid repo above for automatic updates) |
| `browser` | `*chrome*.zip`, `*firefox*.zip` | Chrome/Edge/Brave: `chrome://extensions` → Developer mode → Load unpacked (unzip first). Firefox: `about:debugging` → Load Temporary Add-on |

Log in with your normal Bitwarden account (cloud or self-hosted).

## Patches

Every change is listed here; there are no others. Rules find their file by a snippet of text, not a path, and a rule that matches nothing fails the build.

| # | Target | Patch | Why | Where (rule) |
|---|---|---|---|---|
| 1 | Android | `isPremium` is always `true` | Opens the client-side premium gate (built-in TOTP codes and other local features) | `nano.py` `android()` |
| 2 | Browser | `hasPremiumPersonally$` / `hasPremiumFromAnySource$` always `true` | Same gate in the extension | `nano.py` `browser()` |
| 3 | Android | App name `NanoWarden`, application id `com.x8bit.bitwarden.nano` | Installs next to the official app, never replaces it | `brand.py` `android()` |
| 4 | Browser | Extension name `NanoWarden` and an "unofficial build" description | Cannot be mistaken for the official extension | `brand.py` `browser()` |
| 5 | Both | Teal colour scheme (blue scale hue-rotated) and an original "N" icon | Visually distinct fork, no Bitwarden logo | `brand.py` |
| 6 | Browser | Own Firefox add-on id and update URL, own Chrome update URL | Lets the fork self-update without colliding with the official add-on | `brand.py`, `ext.py` |

Not changed: encryption, networking, login and sync code. Anything the **server** enforces (attachment uploads, emergency access, Send files) still follows your account's plan.

## Versioning

Releases carry the **same version number and tag as upstream Bitwarden** (for example `v2026.10.0-bwpm` for Android and `browser-v2026.10.0` for the extension). If only the patches change, the release for that version is rebuilt in place.

## How it works

`nano.py` has one function per target (`android`, `browser`). Each one clones the official release tag, finds the
premium check by searching for a known snippet (so it survives files being moved between releases), rewrites it,
and runs the official build.

```
python3 nano.py latest browser   # newest upstream release tag
python3 nano.py build android    # clone + patch + build, artifacts in ./out
```

Adding another client means adding one function and one line in `TARGETS`.

## Legal

- **Licence.** Bitwarden's clients are GPL-3.0, which permits modifying and redistributing them. The builds published here are
  modified versions under the same licence. This repo's own code is GPL-3.0 too (see `LICENSE`). **Source offer:** the
  complete corresponding source of every release is the upstream tag named in the release (`github.com/bitwarden/android` or
  `github.com/bitwarden/clients`) plus the modifications made by `nano.py` in this repo at that release's commit.
- **Not affiliated.** Unofficial, community-maintained, not endorsed by Bitwarden Inc. "Bitwarden" is their trademark; it is used
  here only to say what this is derived from. Builds use their own name, logo and colours so they cannot be mistaken for the official app.
- **Your responsibility.** Bitwarden sells premium features and its cloud service has terms of use. Using patched clients against
  Bitwarden's hosted servers may not comply with those terms, and server-side limits still apply. Self-hosted servers
  (Bitwarden or Vaultwarden) are the intended setup. If you rely on Bitwarden's cloud, consider buying a plan.
- **No warranty.** Provided as is. You are responsible for your own vault and backups. Not legal advice.
