#!/bin/bash
# Package the RHWP native C ABI plus its JNI bridge as one Android shared library.
# Usage: ANDROID_NDK_HOME=<ndk> CARGO_TARGET_DIR=<shared-target> scripts/package-android.sh [abi...]
# Output: dist/android/jniLibs/<abi>/librhwp_android.so, dist/android/RhwpNative.kt
# The Rust static library is linked with the bridge so that only the JNI entry
# points are exported and the linker drops C ABI surface the bridge never calls.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NDK="${ANDROID_NDK_HOME:?set ANDROID_NDK_HOME to an Android NDK (r27 or newer)}"
API="${ANDROID_API:-24}"
HOST_TAG="$(ls "$NDK/toolchains/llvm/prebuilt" | head -n 1)"
BIN="$NDK/toolchains/llvm/prebuilt/$HOST_TAG/bin"
TARGET_DIR="${CARGO_TARGET_DIR:-$ROOT/target/pr-review}"
DIST="$ROOT/dist/android"
JNI_DIR="$ROOT/bindings/android"
HEADERS="$ROOT/bindings/swift/Sources/CRhwpNative"

[[ $# -gt 0 ]] || set -- arm64-v8a
rm -rf "$DIST"

for abi in "$@"; do
  case "$abi" in
    arm64-v8a) target=aarch64-linux-android; clang=aarch64-linux-android ;;
    armeabi-v7a) target=armv7-linux-androideabi; clang=armv7a-linux-androideabi ;;
    x86_64) target=x86_64-linux-android; clang=x86_64-linux-android ;;
    x86) target=i686-linux-android; clang=i686-linux-android ;;
    *) echo "error: unknown ABI $abi"; exit 1 ;;
  esac
  env_target="$(echo "$target" | tr 'a-z-' 'A-Z_')"
  cc_target="$(echo "$target" | tr '-' '_')"
  export "CARGO_TARGET_${env_target}_LINKER=$BIN/$clang$API-clang"
  export "CC_$cc_target=$BIN/$clang$API-clang" "CXX_$cc_target=$BIN/$clang$API-clang++"
  export "AR_$cc_target=$BIN/llvm-ar" ANDROID_NDK="$NDK"

  echo "[build] $abi ($target)"
  rustup target add "$target"
  cargo build --release --locked --manifest-path "$ROOT/bindings/Native/Cargo.toml" \
    --target "$target" --target-dir "$TARGET_DIR" --features native-skia

  out="$DIST/jniLibs/$abi"
  mkdir -p "$out"
  echo "[link] $abi"
  # 16 KB pages: required for Android 15+ devices. exclude-libs hides the C ABI
  # so gc-sections can drop what the bridge does not reach.
  "$BIN/$clang$API-clang" -c -O2 -fPIC -I"$HEADERS" "$JNI_DIR/rhwp_jni.c" -o "$out/rhwp_jni.o"
  "$BIN/$clang$API-clang++" -shared \
    "$out/rhwp_jni.o" "$TARGET_DIR/$target/release/librhwp_native_ffi.a" \
    -Wl,--gc-sections -Wl,--exclude-libs,ALL -Wl,-z,max-page-size=16384 \
    -static-libstdc++ -llog -ldl -lm \
    -o "$out/librhwp_android.so"
  rm "$out/rhwp_jni.o"
  "$BIN/llvm-strip" "$out/librhwp_android.so"
  echo "$abi $(wc -c < "$out/librhwp_android.so") bytes"
done

cp "$JNI_DIR/RhwpNative.kt" "$DIST/"
echo "=== done: $DIST ==="
