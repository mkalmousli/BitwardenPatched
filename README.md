# NanoWarden

**Patched, automatically updated builds of the official Bitwarden apps: Android and the Chrome/Firefox browser extension.**

## What is this?

Bitwarden's clients are open source (GPL-3.0), but several features in the official apps are switched on only for
accounts the client considers "premium", most notably **built-in TOTP / authenticator codes** (the one-time codes
for two-factor login). NanoWarden takes the official source, changes the client-side check so these features are
available, builds it, and publishes the result on the [Releases](../../releases) page.

- It is **not a fork**. This repo holds no Bitwarden source, only the patch logic (`nano.py`) and the automation.
- It **stays current by itself**. A GitHub Actions workflow checks for new official releases every 6 hours,
  patches and builds them, and publishes the new version.
- If an upstream change breaks a patch, the build fails loudly and opens an issue instead of shipping something wrong.

## F-Droid repository (Android)

Add this repository to F-Droid, Droidify, Neo Store or any F-Droid client, and updates arrive automatically:

```
https://mkalmousli.github.io/NanoWarden/repo?fingerprint=B1D78FEC2A8513EFD0EF78AE2C73887DFDC84F4CE6C786C61D524E1D4B43821B
```

(F-Droid → Settings → Repositories → **+**, or open the link on your phone.) The fingerprint pins the signing key.

## Branding

To avoid confusion with the official app, builds are clearly marked as a fork: the app is named
**NanoWarden (Bitwarden fork)**, the Android application id is `com.x8bit.bitwarden.nano` (it installs *next to* the
official app instead of replacing it), and the browser extension carries the same name.

## Downloads

Go to [Releases](../../releases):

| Target | File | Install |
|---|---|---|
| `android` | `*.apk` | Sideload on Android 8+ (signed with the NanoWarden key; prefer the F-Droid repo above for automatic updates) |
| `browser` | `*chrome*.zip`, `*firefox*.zip` | Chrome/Edge/Brave: `chrome://extensions` → Developer mode → Load unpacked (unzip first). Firefox: `about:debugging` → Load Temporary Add-on |

Log in with your normal Bitwarden account (cloud or self-hosted).

## What it changes, and what it doesn't

Only the client-side premium check. TOTP generation and other local features work. Anything the **server** enforces
(file attachment uploads, emergency access, Send file hosting, and so on) is still governed by your account's plan,
because the server rejects those requests regardless of what the client does.

## How it works

`nano.py` has one function per target (`android`, `browser`). Each one clones the official release tag, finds the
premium check by searching for a known snippet (so it survives files being moved between releases), rewrites it,
and runs the official build.

```
python3 nano.py latest browser   # newest upstream release tag
python3 nano.py build android    # clone + patch + build, artifacts in ./out
```

Adding another client means adding one function and one line in `TARGETS`.

## Disclaimer

Unofficial, community-maintained, and not affiliated with or endorsed by Bitwarden Inc. Bitwarden is a trademark of
its owner. Consider supporting Bitwarden with a paid plan if you rely on it.
