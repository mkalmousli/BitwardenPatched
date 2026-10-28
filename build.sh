#!/usr/bin/env bash
# Fetches upstream Bitwarden Android, applies ./patches, and builds the F-Droid debug APK with a locally built SDK.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); APP_COMMIT=976ce745c99c4d93c44234da6f3990294c02e3c0
mkdir -p build && cd build && ROOT=$(pwd); SDK_COMMIT=d9119f7af71bce0543b571bf000e18a67ad362ee
export ANDROID_HOME=${ANDROID_HOME:-$HOME/android-sdk}; NDK_V=27.0.12077973

# JDK 21
if ! javac -version 2>&1 | grep -q ' 21'; then
  sudo apt-get update -qq && sudo apt-get install -y -qq openjdk-21-jdk perl make >/dev/null
fi
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which javac))))
[ "$("$JAVA_HOME/bin/javac" -version 2>&1 | grep -c ' 21')" = 1 ] || export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Android SDK + NDK
if [ ! -d "$ANDROID_HOME/cmdline-tools/latest" ]; then
  mkdir -p "$ANDROID_HOME/cmdline-tools" && cd /tmp
  curl -sLo ct.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
  unzip -q ct.zip && mv cmdline-tools "$ANDROID_HOME/cmdline-tools/latest"; cd "$ROOT"
fi
SM=$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager
yes | $SM --licenses >/dev/null 2>&1 || true
$SM "ndk;$NDK_V" "platform-tools" >/dev/null

# Rust + SDK (pinned commit matching the app)
command -v rustup >/dev/null || curl -sSf https://sh.rustup.rs | sh -s -- -y
. "$HOME/.cargo/env"
[ -d sdk ] || { git clone -q https://github.com/bitwarden/sdk-internal sdk; git -C sdk checkout -q $SDK_COMMIT; }
cd sdk
rustup target add aarch64-linux-android --toolchain "$(grep channel rust-toolchain.toml | head -1 | cut -d'"' -f2)"
N=$ANDROID_HOME/ndk/$NDK_V/toolchains/llvm/prebuilt/linux-x86_64/bin
export ANDROID_NDK_HOME=$ANDROID_HOME/ndk/$NDK_V PATH=$N:$PATH
export CC_aarch64_linux_android=$N/aarch64-linux-android26-clang AR_aarch64_linux_android=$N/llvm-ar
export CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER=$N/aarch64-linux-android26-clang
cargo build -p bitwarden-uniffi --release --target=aarch64-linux-android
K=crates/bitwarden-uniffi/kotlin
mkdir -p $K/sdk/src/main/jniLibs/arm64-v8a
cp target/aarch64-linux-android/release/libbitwarden_uniffi.so $K/sdk/src/main/jniLibs/arm64-v8a/
(cd $K && bash build-schemas.sh && ./gradlew sdk:publishToMavenLocal -Pversion=LOCAL -q)
cd "$ROOT"

# App
[ -d android ] || { git clone -q https://github.com/bitwarden/android; git -C android checkout -q $APP_COMMIT; for p in "$HERE"/patches/*.patch; do git -C android apply "$p"; done; }
cd android
echo "localSdk=true" > user.properties
./gradlew app:assembleFdroidDebug -q
find app/build/outputs -name '*.apk' -exec ls -lh {} \;
