# mobile-poc

`mobile/touch-editing` 브랜치의 모바일 패치를 실기기에서 확인하던 시제품 도구다. upstream PR 대상이 아니다.

## 구성

| 파일 | 내용 |
|---|---|
| `build.sh` | 이 저장소의 studio를 빌드해 `site/public/vendor/rhwp/`에 둔다. 엔진은 npm `@rhwp/core`(기본 0.9.0)를 쓴다 |
| `server.py` | `127.0.0.1:8765` 정적 서버. 페이지가 `POST /log` 로 보낸 로그를 파일에 쌓는다 |
| `site/public/app.html` | 앱 형태 화면. 헤더 + 문서 + 키보드 위 툴바(서식 상태 이벤트 연동) |
| `site/public/poc.html` | 엔진 로딩·한글 입력 확인용. `?mini=1`(chrome 숨김), `?long=1`(긴 본문), `?zoom=view:zoom-200` |
| `site/public/icons.txt` | Remix Icon SVG 경로(Apache-2.0) |
| `tools/pinch.mjs` | Chrome 원격 디버깅으로 두 손가락 핀치 전송 |
| `tools/eval.mjs` | Chrome 원격 디버깅으로 페이지에서 식 평가 |

## 실행 (Android 실기기)

```sh
sh mobile-poc/build.sh
python3 -I mobile-poc/server.py mobile-poc/site/public mobile-poc/poc.log &
adb reverse tcp:8765 tcp:8765
adb shell "am start -a android.intent.action.VIEW -d 'http://localhost:8765/app.html' com.android.chrome"

# 핀치·식 평가가 필요하면
adb forward tcp:9222 localabstract:chrome_devtools_remote
WS=$(curl -s http://127.0.0.1:9222/json | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['webSocketDebuggerUrl'])")
node mobile-poc/tools/pinch.mjs "$WS" 110 200 80 170
```

## 호스트 페이지가 지켜야 할 것

- `<meta name="viewport" content="..., user-scalable=no, interactive-widget=resizes-content">`
- `onFormatStateChanged` 구독, 문서를 연 뒤 `view:zoom-fit-content` 실행
- 툴바 버튼은 `pointerdown` 에서 `preventDefault()` (키보드 유지)
- 글머리표는 `format:toggle-bullet` 에 `{ bulletChar: '•' }`
