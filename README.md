# NanoWarden

Patch set for the [official Bitwarden Android app](https://github.com/bitwarden/android) (GPL-3.0).
This repository contains only patches and a build script; no upstream source is included.

| Patch | Purpose |
|---|---|
| `0001-enable-client-side-features.patch` | Makes the client treat accounts as having advanced features available (e.g. local TOTP generation). Features enforced by the server remain subject to server policy. |
| `0002-local-sdk-build.patch` | Resolves the Bitwarden SDK from a local build instead of GitHub Packages, so no access token is required. |

## Build
`./build.sh` clones upstream at a pinned commit, builds the SDK from source, applies the patches, and produces a debug-signed arm64 APK under `build/android/app/build/outputs/`.

Unofficial and not affiliated with Bitwarden Inc.
