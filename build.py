#!/usr/bin/env python3
"""Fetch upstream Bitwarden Android, apply ./patches, build the SDK locally, then the F-Droid debug APK."""
import glob, os, shutil, subprocess as sp, sys, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "build")
APP_COMMIT = "976ce745c99c4d93c44234da6f3990294c02e3c0"
SDK_COMMIT = "d9119f7af71bce0543b571bf000e18a67ad362ee"
NDK = "27.0.12077973"
HOME = os.path.expanduser("~")
ANDROID = os.environ.get("ANDROID_HOME", os.path.join(HOME, "android-sdk"))
ENV = dict(os.environ, ANDROID_HOME=ANDROID, ANDROID_NDK_HOME=f"{ANDROID}/ndk/{NDK}")


def run(*cmd, cwd=None, env=None, stdin=None):
    print("+", " ".join(cmd), flush=True)
    sp.run(cmd, cwd=cwd, env=env or ENV, check=True, input=stdin, text=bool(stdin))


def clone(url, dest, commit):
    if not os.path.isdir(dest):
        run("git", "clone", "-q", url, dest)
        run("git", "checkout", "-q", commit, cwd=dest)


def setup_jdk():
    jdk = "/usr/lib/jvm/java-21-openjdk-amd64"
    if not os.path.exists(f"{jdk}/bin/javac"):
        run("sudo", "apt-get", "update", "-qq")
        run("sudo", "apt-get", "install", "-y", "-qq", "openjdk-21-jdk", "perl", "make", "unzip")
    ENV.update(JAVA_HOME=jdk, PATH=f"{jdk}/bin:{HOME}/.cargo/bin:" + ENV["PATH"])


def setup_android():
    sdkm = f"{ANDROID}/cmdline-tools/latest/bin/sdkmanager"
    if not os.path.exists(sdkm):
        zip_path = "/tmp/cmdline-tools.zip"
        urllib.request.urlretrieve(
            "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip", zip_path)
        zipfile.ZipFile(zip_path).extractall(ANDROID)
        os.makedirs(f"{ANDROID}/cmdline-tools", exist_ok=True)
        shutil.move(f"{ANDROID}/cmdline-tools", f"{ANDROID}/ct")
        os.makedirs(f"{ANDROID}/cmdline-tools")
        shutil.move(f"{ANDROID}/ct", f"{ANDROID}/cmdline-tools/latest")
        os.chmod(sdkm, 0o755)
        for f in glob.glob(f"{ANDROID}/cmdline-tools/latest/bin/*"):
            os.chmod(f, 0o755)
    sp.run([sdkm, "--licenses"], env=ENV, input="y\n" * 50, text=True, capture_output=True)
    run(sdkm, f"ndk;{NDK}", "platform-tools")


def build_sdk():
    sdk = os.path.join(WORK, "sdk")
    clone("https://github.com/bitwarden/sdk-internal", sdk, SDK_COMMIT)
    if not shutil.which("rustup", path=ENV["PATH"]):
        urllib.request.urlretrieve("https://sh.rustup.rs", "/tmp/rustup.sh")
        run("sh", "/tmp/rustup.sh", "-y")
    channel = next(l for l in open(f"{sdk}/rust-toolchain.toml") if "channel" in l).split('"')[1]
    run("rustup", "target", "add", "aarch64-linux-android", "--toolchain", channel)
    bin_dir = f"{ANDROID}/ndk/{NDK}/toolchains/llvm/prebuilt/linux-x86_64/bin"
    clang = f"{bin_dir}/aarch64-linux-android26-clang"
    env = dict(ENV, PATH=f"{bin_dir}:" + ENV["PATH"], CC_aarch64_linux_android=clang,
               AR_aarch64_linux_android=f"{bin_dir}/llvm-ar", CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER=clang)
    run("cargo", "build", "-p", "bitwarden-uniffi", "--release", "--target=aarch64-linux-android", cwd=sdk, env=env)
    kt = f"{sdk}/crates/bitwarden-uniffi/kotlin"
    libs = f"{kt}/sdk/src/main/jniLibs/arm64-v8a"
    os.makedirs(libs, exist_ok=True)
    shutil.copy(f"{sdk}/target/aarch64-linux-android/release/libbitwarden_uniffi.so", libs)
    run("bash", "build-schemas.sh", cwd=kt)
    run("./gradlew", "sdk:publishToMavenLocal", "-Pversion=LOCAL", "-q", cwd=kt)


def build_app():
    app = os.path.join(WORK, "android")
    fresh = not os.path.isdir(app)
    clone("https://github.com/bitwarden/android", app, APP_COMMIT)
    if fresh:
        for patch in sorted(glob.glob(f"{HERE}/patches/*.patch")):
            run("git", "apply", patch, cwd=app)
    open(f"{app}/user.properties", "w").write("localSdk=true\n")
    run("./gradlew", "app:assembleFdroidDebug", "-q", cwd=app)
    for apk in glob.glob(f"{app}/app/build/outputs/**/*.apk", recursive=True):
        print("APK:", apk)


if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    setup_jdk()
    setup_android()
    build_sdk()
    build_app()
