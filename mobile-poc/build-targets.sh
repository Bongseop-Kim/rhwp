#!/bin/bash
# S0-1: rhwp-native-ffi 를 host·iOS·Android 타깃으로 빌드하고 크기를 기록한다.
# 사용: mobile-poc/build-targets.sh   (결과: mobile-poc/out/sizes.txt, 로그: mobile-poc/out/*.log)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/mobile-poc/out"; mkdir -p "$OUT"
export CARGO_TARGET_DIR="$ROOT/target/mobile-poc"
NDK="${ANDROID_NDK_HOME:-$HOME/Library/Android/sdk/ndk/27.1.12297006}"
BIN="$NDK/toolchains/llvm/prebuilt/darwin-x86_64/bin"
export CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER="$BIN/aarch64-linux-android24-clang"
export CC_aarch64_linux_android="$BIN/aarch64-linux-android24-clang"
export CXX_aarch64_linux_android="$BIN/aarch64-linux-android24-clang++"
export AR_aarch64_linux_android="$BIN/llvm-ar"
export ANDROID_NDK="$NDK" ANDROID_NDK_HOME="$NDK"
build() { # target, variant(default|skia)
  local target="$1" variant="$2" feat=()
  [[ "$variant" == skia* ]] && feat=(--features native-skia)
  variant="$variant-slim"; local log="$OUT/$target-$variant.log"
  if cargo build --release --locked -p rhwp-native-ffi --target "$target" ${feat[@]+"${feat[@]}"} >"$log" 2>&1; then
    local dir="$CARGO_TARGET_DIR/$target/release" keep="$OUT/$target-$variant"; mkdir -p "$keep"
    for f in "$dir"/librhwp_native_ffi.{a,so,dylib}; do
      [[ -f "$f" ]] || continue
      cp "$f" "$keep/"; local s="$keep/$(basename "$f")"
      case "$f" in
        *.so) "$BIN/llvm-strip" "$s" ;;
        *.dylib) strip -x "$s" ;;
      esac
      echo "$target $variant $(basename "$f") $(stat -f%z "$s")" >> "$OUT/sizes.txt"
    done
    echo "OK $target $variant" >> "$OUT/sizes.txt"
  else
    echo "FAIL $target $variant (see $log)" >> "$OUT/sizes.txt"
  fi
}
[[ $# -gt 0 ]] || set -- aarch64-apple-darwin aarch64-apple-ios aarch64-apple-ios-sim aarch64-linux-android
for t in "$@"; do build "$t" skia; done
echo DONE >> "$OUT/sizes.txt"
