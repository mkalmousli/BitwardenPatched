"""Platform build commands; source checkout and artifact collection live in nano.py."""
import glob, os, re, sys
import brand
from build_utils import run, sub, HERE

def keystore():
    """Stable signing key from the environment (CI); otherwise a throwaway local one."""
    path, pw = os.environ.get("KEYSTORE"), os.environ.get("KS_PASS", "nanowarden")
    path = path or f"{HERE}/work/local.jks"
    if not os.path.exists(path):
        run(HERE, "keytool", "-genkeypair", "-keystore", path, "-alias", "nanowarden", "-storepass", pw,
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-dname", "CN=NanoWarden")
    return path, pw


def android(src):
    brand.android(src, sub)
    sub(src, "isPremium = profile.hasPremiumPersonally",
        r"isPremium = profile\.hasPremiumPersonally == true \|\|\s*profile\.hasPremiumFromOrganization == true,",
        "isPremium = true,")
    # The SDK comes from GitHub Packages; any valid token can read it.
    open(f"{src}/user.properties", "w").write(f"gitHubToken={os.environ['GITHUB_TOKEN']}\n")
    # Speed: no lint (it only checks, never changes the APK), parallel project execution, a larger heap, the build cache.
    init = f"{src}/../speed.init.gradle"
    open(init, "w").write('allprojects { tasks.configureEach { if (name.startsWith("lint")) enabled = false } }\n')
    run(src, "./gradlew", "app:assembleFdroidRelease", "-q", "--parallel", "--build-cache", "--init-script", init,
        "-Dorg.gradle.jvmargs=-Xmx6g -XX:+UseParallelGC", "-Dkotlin.compiler.execution.strategy=in-process",
        "-Pkotlin.incremental=false", "-Dorg.gradle.workers.max=4")
    ks, pw = keystore()
    apksigner = sorted(glob.glob(f"{os.environ['ANDROID_HOME']}/build-tools/*/apksigner"))[-1]
    for unsigned in glob.glob(f"{src}/app/build/outputs/apk/fdroid/release/*.apk"):
        abi = re.search(r"-(universal|x86_64|x86|armeabi-v7a|arm64-v8a)(?:-release)?(?:-unsigned)?\.apk$", unsigned)[1]
        run(src, apksigner, "sign", "--ks", ks, "--ks-pass", f"pass:{pw}", "--out", f"{src}/{abi}.apk", unsigned)
    return "*.apk"


def clients_premium(src):
    """The premium check lives in libs/common, shared by the browser extension and the desktop app."""
    sub(src, "hasPremiumFromAnyOrganization === true ||",
        r"profile\?\.hasPremiumFromAnyOrganization === true \|\|\s*profile\?\.hasPremiumPersonally === true", "true")
    sub(src, "!!profile?.hasPremiumPersonally", r"!!profile\?\.hasPremiumPersonally", "true")


def browser(src):
    brand.browser(src, sub)
    clients_premium(src)
    run(src, "npm", "ci")
    for flavor in ("chrome", "firefox"):
        run(src, "npm", "run", f"dist:{flavor}", "--prefix", "apps/browser")
    return "apps/browser/dist/*.zip"


def desktop(src):
    """Windows, Linux and macOS builds; each CI job builds its own platform/arch natively (NANO_PLATFORM, e.g. windows-arm64)."""
    plat = os.environ.get("NANO_PLATFORM") or {"win32": "windows-x64", "darwin": "macos-arm64"}.get(sys.platform, "linux-x64")
    osname, arch = plat.split("-")
    brand.desktop(src, sub)
    clients_premium(src)
    app = f"{src}/apps/desktop"
    run(src, "npm", "ci")
    run(app, "npm", "run", "build-native")
    run(app, "npm", "run", "build:oss")
    targets = {"linux": ["--linux", "deb", "rpm", "AppImage", "tar.gz"], "windows": ["--win", "nsis", "portable"], "macos": ["--mac", "dmg", "zip"]}[osname]
    run(app, "npx", "electron-builder", *targets, f"--{arch}", "-p", "never")
    return "apps/desktop/dist/*.@(exe|AppImage|deb|rpm|dmg|zip|tar.gz)"


