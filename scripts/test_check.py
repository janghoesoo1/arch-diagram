#!/usr/bin/env python3
"""Fixture tests for skills/arch-diagram/scripts/check.py.

Each case takes the clean fixture, applies one mutation, and asserts that exactly the expected
finding id appears (or that the result stays clean). Run: python3 scripts/test_check.py
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK = ROOT / "skills/arch-diagram/scripts/check.py"
FIXTURE = ROOT / "scripts/fixtures/clean.html"

spec = importlib.util.spec_from_file_location("check", CHECK)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

CLEAN = FIXTURE.read_text(encoding="utf-8")
failures = 0


def run(text: str, **kw):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(text)
        p = Path(f.name)
    try:
        return check.run(p, **kw)
    finally:
        p.unlink()


def ids(rep, level=None):
    return {cid for lvl, cid, _ in rep.items if level is None or lvl == level}


def expect(name, text, fail=(), warn=(), clean=False, **kw):
    global failures
    rep = run(text, **kw)
    got_f, got_w = ids(rep, "FAIL"), ids(rep, "WARN")
    ok = True
    if clean and (got_f or got_w):
        ok = False
    for cid in fail:
        if cid not in got_f:
            ok = False
    for cid in warn:
        if cid not in got_w:
            ok = False
    if ok:
        print(f"ok    {name}")
    else:
        failures += 1
        print(f"FAIL  {name}: expected fail={set(fail)} warn={set(warn)} clean={clean}; got fail={got_f} warn={got_w}")
        for lvl, cid, msg in rep.items:
            print(f"        [{lvl}] {cid}: {msg}")


def mut(old: str, new: str, text: str = CLEAN) -> str:
    assert old in text, f"mutation anchor missing: {old!r}"
    return text.replace(old, new, 1)


# --- clean ---------------------------------------------------------------------------------------
expect("clean fixture passes", CLEAN, clean=True)

# --- structure -----------------------------------------------------------------------------------
expect("leftover token", mut('src="data:image/svg+xml;base64,PHN2Zy8+"', 'src="%%ICON_api%%"'), fail=["unresolved-token", "icon-not-inlined"])
expect("placeholder", mut("<h1>주문 흐름</h1>", "<h1>[TITLE]</h1>"), fail=["placeholder"])
expect("script", mut("</body>", "<script>1</script></body>"), fail=["script"])
expect("remote image", mut('src="data:image/svg+xml;base64,PHN2Zy8+"', 'src="https://example.com/x.svg"'), fail=["remote-asset", "icon-not-inlined"])
expect("viewBox mismatch", mut('viewBox="0 0 600 440"', 'viewBox="0 0 800 440"'), fail=["canvas-viewbox"])
expect("inline canvas size wins", mut('<div class="canvas" role="img"', '<div class="canvas" style="width:600px;height:440px" role="img"'), clean=True)

# --- a11y ----------------------------------------------------------------------------------------
expect("missing aria-label", mut('aria-label="사용자가 API를 거쳐 데이터베이스에 닿는다."', 'aria-label=""'), fail=["a11y-label"])
expect("missing role", mut('role="img"', 'role="figure"'), fail=["a11y-role"])
expect("edges not hidden", mut('aria-hidden="true"', 'aria-hidden="false"'), warn=["a11y-edges"])

# --- korean --------------------------------------------------------------------------------------
expect("hangul without korean family", mut('"Pretendard", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic"', '"Arial"'), fail=["korean-font-stack"])
expect("hangul without webfont", mut('<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600&display=swap" rel="stylesheet">', ""), warn=["korean-webfont"])
expect("hangul with lang=en", mut('<html lang="ko">', '<html lang="en">'), warn=["lang"])
expect("mono without korean tail", mut('--font-mono: "JetBrains Mono", ui-monospace, var(--font-kr), monospace;', '--font-mono: "JetBrains Mono", monospace;'), warn=["korean-mono"])
latin = CLEAN
for a, b in (("사용자가 API를 거쳐 데이터베이스에 닿는다.", "A user reaches the database through the API."),
             ("사용자", "User"), ("API 서버", "API"), ("데이터베이스", "Database"), ("주문 흐름", "Order flow"),
             ("주 요청 경로", "request path"), ("내부 연결", "internal"), ("저장소", "Storage")):
    latin = latin.replace(a, b)
latin = latin.replace('<html lang="ko">', '<html lang="en">').replace(
    '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600&display=swap" rel="stylesheet">', "")
expect("latin page needs no korean font", latin, clean=True)

# --- nodes ---------------------------------------------------------------------------------------
expect("name too long for three lines", mut("<span>데이터베이스</span>", "<span>아주아주아주아주 긴 이름의 데이터베이스 서버 인스턴스 클러스터</span>"), fail=["name-fit"])
expect("role too wide", mut("<span>PostgreSQL</span>", "<span>PostgreSQL 16 primary with streaming replica</span>"), warn=["role-fit"])
expect("node outside canvas", mut('style="left:396px;top:280px"', 'style="left:560px;top:280px"'), fail=["node-in-canvas"])
expect("overlapping nodes", mut('style="left:396px;top:280px"', 'style="left:240px;top:120px"'), fail=["node-overlap"])
expect("two focal tiles", mut('<div class="tile"><img src="data:image/svg+xml;base64,PHN2Zy8+" alt=""></div>\n      <div class="name"><span>사용자</span>',
                              '<div class="tile focal"><img src="data:image/svg+xml;base64,PHN2Zy8+" alt=""></div>\n      <div class="name"><span>사용자</span>'), fail=["focal"])
expect("off-grid warns", mut('style="left:44px;top:120px"', 'style="left:46px;top:120px"'), warn=["grid"])

# --- groups --------------------------------------------------------------------------------------
expect("node sticks out of group", mut("left:372px; top:220px; width:180px; height:212px", "left:372px; top:220px; width:140px; height:212px"), fail=["node-in-group"])
expect("groups overlap without nesting", mut("</svg>", '</svg>\n    <div class="group gb" style="left:300px; top:200px; width:200px; height:100px;"><div class="g-label">X</div></div>'), fail=["group-overlap"])

# --- edges ---------------------------------------------------------------------------------------
expect("diagonal edge", mut('d="M144 150 H306"', 'd="M144 150 L306 170"'), fail=["edge-diagonal"])
expect("unanchored endpoint", mut('d="M144 150 H306"', 'd="M144 150 H280"'), warn=["edge-anchor"])
expect("edge through label text", mut('d="M354 226 V256 H462 V274"', 'd="M354 180 V256 H462 V274"'), fail=["edge-through-text"])
expect("edge through non-endpoint tile", mut("</svg>", '<path class="n" d="M20 160 H306"/></svg>'), fail=["edge-through-node"])
expect("shared stroke", mut("</svg>", '<path class="n" d="M144 150 H306"/></svg>'), fail=["edge-overlap"])
expect("attach points too close", mut("</svg>", '<path class="n" d="M358 226 V256"/></svg>'), fail=["edge-attach"])
expect("label on its line", mut('x="225" y="142"', 'x="225" y="152"'), fail=["label-on-line"])
expect("label on a tile", mut('x="225" y="142"', 'x="120" y="150"'), fail=["label-on-node"])
expect("label in group corner", mut("</svg>", '<text class="el" x="380" y="240">corner</text></svg>'), warn=["label-group-corner"])
expect("edge through group corner", mut("</svg>", '<path class="n" d="M380 226 V300"/></svg>'), warn=["edge-label-corner"])
expect("long label", mut(">HTTPS<", ">this label is far too long<"), warn=["label-length"])

# --- budget / legend -----------------------------------------------------------------------------
many = CLEAN
node_html = lambda left, top, i: f'<div class="node" style="left:{left}px;top:{top}px"><div class="tile"><img src="data:image/svg+xml;base64,PHN2Zy8+" alt=""></div><div class="name"><span>N{i}</span></div><div class="role"><span>r</span></div></div>\n'
nodes = "".join(node_html(40 + i * 140, 520, i) for i in range(4)) + "".join(node_html(40 + i * 140, 660, 4 + i) for i in range(3))
many = mut("<!-- END NODES -->", nodes + "<!-- END NODES -->", mut("height: 440px", "height: 800px", mut('viewBox="0 0 600 440"', 'viewBox="0 0 600 800"')))
expect("ten nodes warn", many, warn=["budget-nodes"])
expect("legend missing swatch", mut('<span><span class="sw n"></span>내부 연결</span>', ""), warn=["legend-missing"])
expect("legend extra swatch", mut("</figcaption>", '<span><span class="sw n dash"></span>배포</span></figcaption>'), warn=["legend-extra"])

print()
if failures:
    print(f"{failures} test(s) failed")
    sys.exit(1)
print("all check.py fixture tests passed")
