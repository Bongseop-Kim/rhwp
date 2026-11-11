#!/usr/bin/env python3
"""S0-2~4 탐침: C ABI로 HTML 붙여넣기 → 렌더 → 탭 판정 → 문단 수정 → HWPX 저장.

사용: python3 mobile-poc/probe.py <librhwp_native_ffi.dylib> <outdir> [input.hwpx|input.html]
"""
import base64, json, struct, sys, zipfile, zlib, io, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bindings/Native/examples"))
from native_host import NativeHost, NativeCallError  # noqa: E402


def png(width, height, rgba, stride=None):
    stride = stride or width * 4
    raw = b"".join(b"\0" + rgba[y * stride:y * stride + width * 4] for y in range(height))
    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


PHOTO = base64.b64encode(png(60, 40, bytes([220, 60, 60, 255]) * 2400)).decode()
SAMPLE_HTML = f"""<p>첫 문단입니다. 글자만 있어요.</p>
<p>서식이 <b>굵은 글자</b>와 <span style="color:#ff0000">빨간 글자</span>가 섞인 문단입니다.</p>
<table border="1"><tr><th>구분</th><th>내용</th></tr><tr><td>원인</td><td>미끄러운 바닥</td></tr></table>
<p>표 아래 문단입니다.</p>
<p><img src="data:image/png;base64,{PHOTO}" width="60" height="40"></p>
<p>사진 아래 마지막 문단입니다.</p>"""


def step(name, fn):
    try:
        value = fn()
        print(f"[ok] {name}: {json.dumps(value, ensure_ascii=False)[:600]}")
        return value
    except NativeCallError as error:
        print(f"[ERR] {name}: {error.code}: {error.response.get('error')}")
    except Exception as error:  # noqa: BLE001
        print(f"[EXC] {name}: {type(error).__name__}: {error}")
    return None


def save(host, handle, path):
    prepared = host.request(handle, op="prepareSave", format="hwpx")
    data = host.copy_buffer(prepared)
    Path(path).write_bytes(data)
    host.request(handle, op="acknowledgeSave", token=prepared["token"])
    return {"bytes": len(data), "report": prepared.get("report")}


def render(host, handle, page, path, scale=2.0):
    frame = host.request(handle, op="render", page=page, scale=scale)
    pixels = host.copy_buffer(frame)
    Path(path).write_bytes(png(frame["width"], frame["height"], pixels, frame["stride"]))
    return {k: frame[k] for k in ("width", "height", "stride")}


def pos(paragraph, offset=0, section=0):
    return {"section": section, "paragraph": paragraph, "scalarOffset": offset, "cellPath": []}


def sel(a, b):
    return {"anchor": a, "focus": b}


def section_runs(path):
    """본문 section0.xml 에서 문단별 (charPrIDRef, 글자) 목록 — 서식 보존 확인용."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("Contents/section0.xml").decode("utf-8")
        names = z.namelist()
    out = []
    for p in re.findall(r"<hp:p\b.*?</hp:p>", xml, flags=re.S)[:40]:
        runs = [(m.group(1), re.sub(r"<[^>]+>", "", m.group(2)))
                for m in re.finditer(r'<hp:run\b[^>]*charPrIDRef="(\d+)"[^>]*>(.*?)</hp:run>', p, flags=re.S)]
        out.append([r for r in runs if r[1]])
    return out, [n for n in names if n.startswith("BinData/")]


def main():
    lib, outdir = sys.argv[1], Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
    source = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    host = NativeHost(lib)
    print("caps", json.dumps(host.call("capabilities"), ensure_ascii=False)[:400])

    a_path = outdir / "A.hwpx"
    if source and source.suffix == ".hwpx":
        a_path = source
    else:
        html = source.read_text("utf-8") if source else SAMPLE_HTML
        import ctypes
        fn = host.library.rhwp_session_open_html
        fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t]; fn.restype = ctypes.c_void_p
        data = html.encode("utf-8")
        h = host._result(fn(ctypes.create_string_buffer(data), len(data)))["handle"]
        step("save A (openHtml)", lambda: save(host, h, a_path))
        host.call("close", h)

    h = host.open_bytes(a_path.read_bytes())
    info = step("info", lambda: host.request(h, op="info"))
    step("fontState", lambda: host.request(h, op="fontState"))
    for page in range(info["pageCount"]):
        step(f"render p{page}", lambda: render(host, h, page, outdir / f"A-p{page}.png"))
    acc = step("accessibility", lambda: host.request(h, op="accessibility", request={
        "geometry": False, "maxNodes": 500, "maxTextBytes": 200000, "maxDepth": 4,
        "maxGeometryQueries": 0, "maxSelectionRects": 1}))
    if acc:
        (outdir / "accessibility.json").write_text(json.dumps(acc, ensure_ascii=False, indent=1))

    size = host.request(h, op="pageSize", page=0)["size"]
    hits, errors = {}, {}
    y = 20.0
    while y < size["height"]:
        for x in (size["width"] * 0.25, size["width"] * 0.5, size["width"] * 0.75):
            try:
                p = host.request(h, op="hitTest", page=0, x=x, y=y)["hit"]["position"]
                key = (p["paragraph"], tuple(json.dumps(c) for c in p["cellPath"]))
                hits.setdefault(key, (x, y, p["scalarOffset"]))
            except NativeCallError as e:
                errors.setdefault(f"{e.code}: {e.response.get('error')}", (x, y))
        y += 12.0
    print("hitTest 위치:", [(k[0], "cell" if k[1] else "body", v) for k, v in sorted(hits.items())])
    print("hitTest 오류:", errors)

    runs, bins = section_runs(a_path)
    print("BinData:", bins)
    for i, r in enumerate(runs):
        print(f"  문단#{i}: {r}")

    # 본문 문단마다 끝에 글자 하나 넣어 보기 → 어떤 문단이 수정 가능한지
    rev = host.request(h, op="info")["revision"]
    paragraph = 0
    editable = {}
    while paragraph < 60:
        try:
            out = host.request(h, op="beginEdit", expectedRevision=rev, selection=sel(pos(paragraph), pos(paragraph)))["outcome"]
            rev = out["revision"]
            out = host.request(h, op="replaceSelection", text="※", expectedRevision=rev)["outcome"]
            rev = out["revision"]; editable[paragraph] = "ok"
        except NativeCallError as e:
            msg = e.response.get("error", "")
            if e.code == "invalidArgument":
                editable[paragraph] = f"invalid: {msg}"
                if "outside the document" in msg:
                    del editable[paragraph]
                    break
            else:
                editable[paragraph] = f"{e.code}: {msg}"
            rev = host.request(h, op="info")["revision"]
        paragraph += 1
    print("문단별 수정:", json.dumps(editable, ensure_ascii=False, indent=1))

    step("splitParagraph@0:3", lambda: (
        host.request(h, op="setSelection", selection=sel(pos(0, 3), pos(0, 3)), expectedRevision=host.request(h, op="info")["revision"]),
        host.request(h, op="executeCommand", command={"command": "splitParagraph"}, expectedRevision=host.request(h, op="info")["revision"]))[1])
    step("copySelection", lambda: (
        host.request(h, op="setSelection", selection=sel(pos(0, 0), pos(0, 3)), expectedRevision=host.request(h, op="info")["revision"]),
        host.request(h, op="copySelection", expectedRevision=host.request(h, op="info")["revision"]))[1])

    def rev():
        return host.request(h, op="info")["revision"]
    def delete_objects(paragraph):
        return host.request(h, op="executeCommand", expectedRevision=rev(),
                            command={"command": "deleteParagraphObjects", "section": 0, "paragraph": paragraph})["outcome"]
    # 뒤에서부터 지워야 앞 문단 번호가 안 밀린다. +1 은 위 splitParagraph 로 밀린 만큼.
    for paragraph in sorted((k + 1 for k, v in editable.items() if v != "ok"), reverse=True):
        step(f"표·사진 지우기(문단 {paragraph})", lambda: delete_objects(paragraph))
    step("undo", lambda: host.request(h, op="undo", expectedRevision=rev())["outcome"])
    step("redo", lambda: host.request(h, op="redo", expectedRevision=rev())["outcome"])

    b_path = outdir / "B.hwpx"
    step("save B", lambda: save(host, h, b_path))
    for page in range(host.request(h, op="info")["pageCount"]):
        step(f"render B p{page}", lambda: render(host, h, page, outdir / f"B-p{page}.png"))
    host.call("close", h)
    if b_path.exists():
        runs, bins = section_runs(b_path)
        print("B BinData:", bins)
        for i, r in enumerate(runs):
            print(f"  B 문단#{i}: {r}")
        print("B text:", host.read_text(b_path)[:400].replace("\n", "⏎"))


if __name__ == "__main__":
    main()
