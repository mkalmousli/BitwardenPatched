# Development

Code is split by responsibility, with a 100-line limit per source file (including
HTML, CSS, JavaScript, shell scripts and workflow YAML). Generated JSON, images,
license text and prose documentation are data, not source code.

- `nano.py`: source checkout and artifacts; `build_targets.py`: platform commands.
- `build_utils.py`: checked patch matching; `brand*.py`: identity, About and image patches.
- `pages.py`: remote publishing; `sitegen.py`: local site composition.
- `fdroid_index.py`: F-Droid signing and bounded APK retention.
- `scripts/apt_repository.py`: signed APT index; `scripts/publish_apt.py`: release publication.
- `docs/js/`: browser rendering and metadata loading; `docs/style.css`: presentation.

Use Python 3.12 and Node 24, as in CI. Install Pillow in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/pip install Pillow==13.0.0
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/local_site.py
.venv/bin/python -m http.server 8000 --directory work/local-site
```

`scripts/local_site.py` does not publish. Running `sitegen.py` directly publishes Pages.
The APT integration test uses GPG, dpkg-deb and apt-get with isolated temporary state;
it verifies signatures and downloads a fixture package without installing it.

For browser regressions, install Playwright and Chromium (or use the environment's
existing Playwright and `/usr/bin/chromium`), render the local site, then run
`node tests/site.cjs`. Set `CHROMIUM_PATH` if the browser is elsewhere.
The browser checks versions with the GitHub API blocked or pending, absent targets,
and missing version metadata. Full client builds require the platform tools in
`.github/workflows/build.yml` and are separate from these focused checks.
