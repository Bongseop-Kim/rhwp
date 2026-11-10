#!/bin/sh
# ponytail: 웹 build-rhwp.mjs의 축약판. 이 저장소 작업 트리를 PoC 서버의 /vendor/rhwp로 빌드한다.
set -eu
SRC=$(cd "$(dirname "$0")/.." && pwd)
POC=$(cd "$(dirname "$0")" && pwd)
OUT=$POC/site/public/vendor/rhwp
CORE_VER=${CORE_VER:-0.9.0}

# 1. 엔진(wasm)은 npm 배포본을 쓴다 — Rust 빌드 생략
mkdir -p "$POC/runtime"
[ -f "$POC/runtime/node_modules/@rhwp/core/rhwp_bg.wasm" ] ||
  npm install --prefix "$POC/runtime" --ignore-scripts --no-audit --no-fund "@rhwp/core@$CORE_VER"
CORE=$POC/runtime/node_modules/@rhwp/core
mkdir -p "$SRC/pkg"
for f in rhwp.js rhwp_bg.wasm rhwp.d.ts rhwp_bg.wasm.d.ts; do cp "$CORE/$f" "$SRC/pkg/$f"; done

# 2. studio 빌드 (PWA 제외, 우리 서버 경로)
cd "$SRC/rhwp-studio"
[ -d node_modules ] || npm ci --ignore-scripts --no-audit --no-fund
cat > vite.poc.config.mjs <<'EOF'
import upstream from './vite.config.ts';
export default { ...upstream, base: '/vendor/rhwp/studio/', plugins: upstream.plugins.flat(Infinity).filter((p) => !p?.name?.includes('pwa')) };
EOF
grep -qx 'vite.poc.config.mjs' "$SRC/.git/info/exclude" || echo 'vite.poc.config.mjs' >> "$SRC/.git/info/exclude"
grep -qx 'pkg/' "$SRC/.git/info/exclude" || echo 'pkg/' >> "$SRC/.git/info/exclude"
RHWP_DISABLE_EXTERNAL_WEBFONTS=1 RHWP_WITHOUT_HWPCTRL=1 RHWP_WITHOUT_AI=1 \
  node node_modules/vite/bin/vite.js build --config vite.poc.config.mjs --outDir "$OUT/studio" --emptyOutDir

# 3. core·editor SDK 배치
mkdir -p "$OUT/core" "$OUT/editor"
cp "$CORE/rhwp.js" "$CORE/rhwp_bg.wasm" "$OUT/core/"
for f in index.js transport.js document-agent-contract.js; do cp "$SRC/npm/editor/$f" "$OUT/editor/$f"; done
sed -i '' "s#'https://edwardkim.github.io/rhwp/'#'/vendor/rhwp/studio/index.html?chrome=embed'#" "$OUT/editor/index.js"
echo "built $(cd "$SRC" && git rev-parse --short HEAD)$(cd "$SRC" && git diff --quiet || echo '+dirty')"
