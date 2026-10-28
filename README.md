# NanoWarden

Rule-based patches for the official [Bitwarden](https://github.com/bitwarden) clients (GPL-3.0), built automatically.
No upstream source is stored here, only `nano.py`.

| Target | Upstream | Output |
|---|---|---|
| `android` | bitwarden/android | F-Droid flavor APK (debug-signed) |
| `browser` | bitwarden/clients (`apps/browser`) | Chrome and Firefox zips |

Each rule finds its edit by anchor text, so it survives file moves between releases. The workflow checks upstream every 6 hours,
builds any new release, and publishes it under Releases. If a rule stops matching, the build fails and opens an issue.

Rules make the client treat accounts as having advanced features (e.g. local TOTP). Server-enforced features still follow server policy.
Local use: `python3 nano.py build android|browser`. Unofficial; not affiliated with Bitwarden Inc.
