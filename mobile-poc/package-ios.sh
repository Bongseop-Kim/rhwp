#!/bin/bash
# iOS 기기·시뮬레이터(arm64)만 담은 XCFramework 를 만든다 → dist/ios/RhwpNative.xcframework
# upstream scripts/package-swift-xcframework.sh 는 macOS 조각까지 빌드해 앱에는 과하다.
# 헤더는 넣지 않는다(앱 모듈이 rhwp_native_ffi.h 를 직접 갖는다).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/mobile-poc/build-targets.sh" aarch64-apple-ios aarch64-apple-ios-sim
REL="$ROOT/target/mobile-poc"
rm -rf "$ROOT/dist/ios"; mkdir -p "$ROOT/dist/ios"
xcodebuild -create-xcframework \
  -library "$REL/aarch64-apple-ios/release/librhwp_native_ffi.a" \
  -library "$REL/aarch64-apple-ios-sim/release/librhwp_native_ffi.a" \
  -output "$ROOT/dist/ios/RhwpNative.xcframework"
du -sh "$ROOT/dist/ios/RhwpNative.xcframework"/*
