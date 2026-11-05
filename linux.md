# Maintaining Linux releases

Desktop Linux jobs build deb, rpm, AppImage and tar.gz for x64 and arm64.
The package name is `bitwarden-patched`, distinct from upstream Bitwarden.
See [user installation instructions](linux.html).

## Optional signed APT channel

The desktop publish job invokes `scripts/publish_apt.py` after creating its release.
Without signing configuration it reports that APT publication was skipped; ordinary
desktop releases still work. To enable it:

1. Create a dedicated noninteractive GPG signing key for this repository.
2. Store a base64-encoded export of its secret signing key in the GitHub Actions secret
   `APT_SIGNING_KEY`. Keep an offline backup; do not commit the key.
3. Set the Actions variable `APT_SIGNING_FINGERPRINT` to its full 40-character fingerprint.
4. Publish that fingerprint through an independently trusted channel for users to verify.
5. Dispatch the build workflow with `force=true` to rebuild existing versions, and check the `rolling-apt` prerelease contains `InRelease`,
   `Release`, `Release.gpg`, `Packages`, `Packages.gz`, `archive-keyring.gpg` and deb files.

The flat APT repository is hosted entirely in release assets. Packages are uploaded
before metadata; older payloads are retained for clients with cached indices.
GitHub does not offer atomic multi-asset replacement: clients can retry an update if
they fetch metadata during publication. Signing failures stop publication.
Do not bypass signature verification or use `trusted=yes`.

RPM files can be installed with DNF or Zypper. A signed RPM repository, AUR package,
Flatpak and Snap distribution are not provided by this project.
