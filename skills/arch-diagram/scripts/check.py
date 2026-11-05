#!/usr/bin/env python3
"""Readability gate for an arch-diagram HTML file. No third-party dependencies.

    python3 check.py OUT.html [--strict] [--faithful] [--json]

Reads the built (or draft) HTML and verifies, from the markup alone, the rules that make a
diagram readable — before anyone has to look at a PNG:

  structure   canvas size == edge viewBox; nothing outside the canvas; no leftover
              placeholders or %%tokens%%; icons are data URIs; no remote assets; no script
              but the template's self-contained viewer
  a11y        canvas has role="img" + aria-label; <title> set; edge overlay aria-hidden
  budget      <= 9 nodes (14 with --faithful), <= 12 edges, <= 4 groups, 1 focal tile
  nodes       no overlaps; names fit (Korean counted at 1em per syllable); row spacing
  groups      every node fully inside its group with padding; groups nest or stay apart
  edges       orthogonal only; endpoints anchored to nodes with a 4-10px gap; no edge
              through a non-endpoint tile; no edge through ANY label text; no two edges
              sharing a stroke; attach points >= 12px apart; labels clear of lines and
              tiles; nothing through a group's label corner
  legend      one swatch per edge kind used, nothing extra
  korean      lang="ko", a Korean family in the font tokens, and an embedded or linked
              Korean webfont whenever the page carries Hangul

Exit 1 on any FAIL (and on WARN with --strict). The geometry model mirrors geometry.md:
a node is its tile plus the text beneath it; 132/172/212 wide, ~100 tall (117 when the
name wraps to two lines). Estimates are conservative, so a clean run is a strong signal
and a FAIL is worth reading — but still render and look before delivering.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

HANGUL_RE = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏ꥠ-꥿ힰ-퟿ﾠ-ￜ㈀-㈞㉠-㉾]")
PLACEHOLDER_RE = re.compile(r"\[(TITLE|KICKER|LEDE|DESC|FOOT-LEFT|ICON-SOURCES)\]")
TOKEN_RE = re.compile(r"%%[A-Za-z0-9_-]+%%")
PATH_TOKEN_RE = re.compile(r"[MmHhVvLlAaZzCcSsQqTt]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
KOREAN_FAMILIES = ("pretendard", "noto sans kr", "apple sd gothic neo", "malgun gothic")
ALLOWED_REMOTE = ("https://fonts.googleapis.com/", "https://fonts.gstatic.com/")
VOID = {"img", "br", "meta", "link", "input", "hr", "source"}

NODE_WIDTHS = {"wide": 172, "xwide": 212}
TILE = 60
NODE_H = 100            # tile 60 + 8 + name 17 + 2 + role 13
NAME_LINE = 17
TEXT_TOP = 62           # text band starts just under the tile
GAP_MIN, GAP_MAX = 2, 12   # line end to node boundary (arrowhead supplies the touch)
ATTACH_MIN = 12
LABEL_CORNER_H = 32     # the band a group label occupies; its width follows the label text


# ----------------------------------------------------------------------------- text metrics
def is_wide(ch: str) -> bool:
    return bool(HANGUL_RE.match(ch)) or unicodedata.east_asian_width(ch) in ("W", "F")


def text_width(s: str, size: float, mono: bool = False) -> float:
    w = 0.0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        if is_wide(ch):
            w += 1.0
        elif mono:
            w += 0.6
        elif ch == " ":
            w += 0.28
        elif ch in ".,:;'|!il·":
            w += 0.3
        elif ch.isupper():
            w += 0.68
        elif ch.isdigit():
            w += 0.58
        else:
            w += 0.56
    return w * size


def wrapped_lines(s: str, size: float, avail: float, mono: bool = False) -> int:
    """Greedy word wrap at spaces (word-break: keep-all); an oversize word breaks anywhere."""
    lines, cur = 1, 0.0
    space = text_width(" ", size, mono)
    for word in s.split():
        ww = text_width(word, size, mono)
        if ww > avail:
            lines += math.ceil(ww / avail) - (1 if cur == 0 else 0)
            cur = ww % avail
            continue
        if cur and cur + space + ww > avail:
            lines += 1
            cur = ww
        else:
            cur = ww if cur == 0 else cur + space + ww
    return lines


def label_len(s: str) -> int:
    return sum(2 if is_wide(c) else 1 for c in s)


# ----------------------------------------------------------------------------- parsing
def parse_style(style: str) -> dict:
    out = {}
    for decl in style.split(";"):
        if ":" in decl:
            k, v = decl.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def px(v: str | None) -> float | None:
    if v is None:
        return None
    m = re.match(r"-?\d+(?:\.\d+)?", v.strip())
    return float(m.group()) if m else None


def parse_path(d: str) -> list[tuple]:
    """Segments (x1, y1, x2, y2, kind) with kind in {'H','V','L','A','C'}; relative commands resolved."""
    toks = PATH_TOKEN_RE.findall(d)
    segs, i = [], 0
    x = y = sx = sy = 0.0
    cmd = None
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t; i += 1
            if cmd in "Zz":
                if (x, y) != (sx, sy):
                    segs.append((x, y, sx, sy, "L"))
                x, y = sx, sy
                continue
        if cmd is None:
            break
        try:
            if cmd in "Mm":
                nx, ny = float(toks[i]), float(toks[i + 1]); i += 2
                if cmd == "m": nx += x; ny += y
                x, y = sx, sy = nx, ny
                cmd = "L" if cmd == "M" else "l"       # implicit lineto after moveto
            elif cmd in "Hh":
                nx = float(toks[i]); i += 1
                if cmd == "h": nx += x
                segs.append((x, y, nx, y, "H")); x = nx
            elif cmd in "Vv":
                ny = float(toks[i]); i += 1
                if cmd == "v": ny += y
                segs.append((x, y, x, ny, "V")); y = ny
            elif cmd in "Ll":
                nx, ny = float(toks[i]), float(toks[i + 1]); i += 2
                if cmd == "l": nx += x; ny += y
                kind = "H" if ny == y else "V" if nx == x else "L"
                segs.append((x, y, nx, ny, kind)); x, y = nx, ny
            elif cmd in "Aa":
                nx, ny = float(toks[i + 5]), float(toks[i + 6]); i += 7
                if cmd == "a": nx += x; ny += y
                segs.append((x, y, nx, ny, "A")); x, y = nx, ny
            elif cmd in "Cc":
                nx, ny = float(toks[i + 4]), float(toks[i + 5]); i += 6
                if cmd == "c": nx += x; ny += y
                segs.append((x, y, nx, ny, "C")); x, y = nx, ny
            elif cmd in "SsQq":
                nx, ny = float(toks[i + 2]), float(toks[i + 3]); i += 4
                if cmd in "sq": nx += x; ny += y
                segs.append((x, y, nx, ny, "C")); x, y = nx, ny
            elif cmd in "Tt":
                nx, ny = float(toks[i]), float(toks[i + 1]); i += 2
                if cmd == "t": nx += x; ny += y
                segs.append((x, y, nx, ny, "C")); x, y = nx, ny
            else:
                i += 1
        except (IndexError, ValueError):
            break
    return segs


class Diagram(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = ""
        self.styles: list[str] = []
        self.scripts = 0
        self.viewer_scripts = 0
        self.viewer_text: list[str] = []
        self._in_viewer = False
        self.remote: list[str] = []
        self.img_srcs: list[str] = []
        self.kr_link = False
        self.canvas: dict | None = None
        self.groups: list[dict] = []
        self.nodes: list[dict] = []
        self.svg: dict | None = None
        self.legend_sw: list[set] = []
        self.legend_present = False
        self.text_chunks: list[str] = []
        self._stack: list[dict] = []
        self._capture: list[str] | None = None
        self._capture_target: tuple | None = None
        self._in_style = self._in_title = self._in_defs = False
        self._text_el: dict | None = None

    # helpers
    def _classes(self, attrs): return set((attrs.get("class") or "").split())
    def _ancestor(self, cls):
        for el in reversed(self._stack):
            if cls in el["classes"]:
                return el
        return None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v if v is not None else "") for k, v in attrs}
        classes = self._classes(a)
        style = parse_style(a.get("style", ""))
        el = {"tag": tag, "classes": classes, "rec": None}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "style":
            self._in_style = True
        elif tag == "script":
            if "data-arch-diagram-viewer" in a and not a.get("src"):
                self.viewer_scripts += 1
                self._in_viewer = True
            else:
                self.scripts += 1
        elif tag == "link" and "fonts.googleapis.com" in a.get("href", ""):
            if "Noto+Sans+KR" in a.get("href", ""):
                self.kr_link = True
        for key in ("src", "href"):
            v = a.get(key, "")
            if v.startswith(("http://", "https://")) and tag not in ("a",) and not v.startswith(ALLOWED_REMOTE):
                self.remote.append(f"<{tag} {key}={v[:60]}>")
        if tag == "img":
            self.img_srcs.append(a.get("src", ""))
            node = self._ancestor("node")
            if node is not None:
                node["rec"]["imgs"].append(a.get("src", ""))
            g = self._ancestor("group")
            if g is not None and self._ancestor("g-label") is not None:
                g["rec"]["icon"] = True
        if tag == "div" and "canvas" in classes:
            self.canvas = {"w": px(style.get("width")), "h": px(style.get("height")),
                           "role": a.get("role"), "aria": a.get("aria-label", "")}
            el["rec"] = self.canvas
        elif tag == "div" and "group" in classes and self.canvas is not None:
            rec = {"x0": px(style.get("left")), "y0": px(style.get("top")),
                   "w": px(style.get("width")), "h": px(style.get("height")),
                   "classes": classes, "label": "", "parent": None, "depth": 1,
                   "dom_nested": self._ancestor("group") is not None}
            if None in (rec["x0"], rec["y0"], rec["w"], rec["h"]):
                rec["bad"] = True
            else:
                rec["x1"] = rec["x0"] + rec["w"]; rec["y1"] = rec["y0"] + rec["h"]
            self.groups.append(rec); el["rec"] = rec
        elif tag == "div" and "g-label" in classes:
            g = self._ancestor("group")
            if g is not None:
                self._capture, self._capture_target = [], (g["rec"], "label")
        elif tag == "div" and "node" in classes and self.canvas is not None:
            width = next((NODE_WIDTHS[c] for c in classes if c in NODE_WIDTHS), 132)
            rec = {"x0": px(style.get("left")), "y0": px(style.get("top")), "w": width,
                   "classes": classes, "tile": set(), "name": "", "role": "", "imgs": [],
                   "dom_nested": self._ancestor("group") is not None}
            self.nodes.append(rec); el["rec"] = rec
        elif tag == "div" and "tile" in classes:
            node = self._ancestor("node")
            if node is not None:
                node["rec"]["tile"] = classes
        elif tag == "div" and ("name" in classes or "role" in classes):
            node = self._ancestor("node")
            if node is not None:
                self._capture, self._capture_target = [], (node["rec"], "name" if "name" in classes else "role")
        elif tag == "svg" and "edges" in classes:
            self.svg = {"viewBox": a.get("viewbox", ""), "aria_hidden": a.get("aria-hidden"),
                        "paths": [], "labels": []}
            el["rec"] = self.svg
        elif tag == "defs":
            self._in_defs = True
        elif tag == "path" and self.svg is not None and not self._in_defs and self._ancestor("edges"):
            self.svg["paths"].append({"classes": classes, "d": a.get("d", ""), "segs": parse_path(a.get("d", "")),
                                      "marker": a.get("marker-end", "")})
        elif tag == "text" and self.svg is not None and self._ancestor("edges"):
            self._text_el = {"classes": classes, "x": px(a.get("x")), "y": px(a.get("y")),
                             "anchor": a.get("text-anchor", "start"), "text": ""}
            self.svg["labels"].append(self._text_el)
            self._capture, self._capture_target = [], (self._text_el, "text")
        elif "legend" in classes:
            self.legend_present = True
        elif tag == "span" and "sw" in classes and self._ancestor("legend"):
            self.legend_sw.append(classes - {"sw"})
        if tag not in VOID:
            self._stack.append(el)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "script": self._in_viewer = False
        if tag == "title": self._in_title = False
        if tag == "style": self._in_style = False
        if tag == "defs": self._in_defs = False
        # pop to the matching open element
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i]["tag"] == tag:
                closing = self._stack[i]
                del self._stack[i:]
                break
        else:
            return
        if self._capture is not None and self._capture_target is not None:
            rec, key = self._capture_target
            is_target = ((key == "label" and "g-label" in closing["classes"]) or
                         (key in ("name", "role") and key in closing["classes"]) or
                         (key == "text" and tag == "text"))
            if is_target:
                rec[key] = re.sub(r"\s+", " ", "".join(self._capture)).strip()
                self._capture = self._capture_target = None

    def handle_data(self, data):
        if self._in_style:
            self.styles.append(data)
            return
        if self._in_viewer:
            self.viewer_text.append(data)
            return
        if self._in_title:
            self.title += data
        if self._capture is not None:
            self._capture.append(data)
        if self._stack and self._stack[-1]["tag"] not in ("script",):
            self.text_chunks.append(data)


# ----------------------------------------------------------------------------- geometry helpers
def rect_hit(seg, r, pad=0.0):
    """Does an axis-aligned segment (x1,y1,x2,y2) cross rect r=(x0,y0,x1,y1) inflated by pad?"""
    x1, y1, x2, y2 = seg[:4]
    rx0, ry0, rx1, ry1 = r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad
    lx0, lx1 = min(x1, x2), max(x1, x2)
    ly0, ly1 = min(y1, y2), max(y1, y2)
    return lx1 > rx0 and lx0 < rx1 and ly1 > ry0 and ly0 < ry1


def rects_overlap(a, b, pad=0.0):
    return a[0] < b[2] + pad and b[0] < a[2] + pad and a[1] < b[3] + pad and b[1] < a[3] + pad


def inside(inner, outer, l=0, t=0, r=0, b=0):
    return (inner[0] >= outer[0] + l and inner[1] >= outer[1] + t and
            inner[2] <= outer[2] - r and inner[3] <= outer[3] - b)


def fmt(v):
    return f"{int(v)}" if float(v).is_integer() else f"{v:.1f}"


# ----------------------------------------------------------------------------- the checks
FIXES = {
    "unresolved-token": "run build.py with the icons dir that holds every %%ICON_<name>%% file",
    "placeholder": "fill the template placeholders (title, kicker, lede, description, footer, icon sources)",
    "script": "remove the script; keep only the template's data-arch-diagram-viewer block",
    "remote-asset": "inline it as a data URI (build.py does this for icons and fonts)",
    "icon-not-inlined": "run build.py over the draft",
    "canvas-viewbox": "set svg.edges viewBox to \"0 0 <canvas width> <canvas height>\"",
    "a11y-label": "write one sentence in aria-label saying what connects to what",
    "a11y-role": "add role=\"img\" to the canvas div",
    "korean-font-stack": "keep --font-kr in the font tokens (the template has it)",
    "korean-webfont": "rebuild with build.py --kr-font auto, or keep the Noto Sans KR link",
    "lang": "set <html lang=\"ko\"> (build.py switches en → ko automatically)",
    "name-fit": "shorten the name or give the node class wide / xwide (spec: \"width\")",
    "role-fit": "shorten the role line or widen the node",
    "node-in-canvas": "enlarge the canvas or move the node inward (spec: lower col/row)",
    "node-overlap": "move one node to a free cell (spec: unique row/col)",
    "node-spacing": "keep same-row centres ≥ 140px apart",
    "focal": "keep a single focal tile",
    "node-in-group": "widen the group to 24px outside the node box, 60px above, 50px below",
    "node-group-edge": "move the node fully inside or outside the group (spec: membership or cell)",
    "group-overlap": "nest one group fully inside the other, or separate them",
    "group-nesting": "inset the child ≥16px and ≥40px below the parent's top",
    "edge-diagonal": "route with H/V segments only",
    "edge-anchor": "end the line 2–12px off the tile side, tile top, or box bottom",
    "edge-through-text": "connect box bottom → tile top (never from the tile bottom); or reroute",
    "edge-through-node": "reroute around the tile, or move the node out of the corridor",
    "edge-overlap": "offset one of the lines by ≥12px (spec: layout does this for request/return pairs)",
    "edge-attach": "fan attach points ≥12px apart on that side",
    "edge-crowding": "keep parallel lines ≥12px apart",
    "edge-label-corner": "shorten the group label or move the edge's attach point",
    "label-on-node": "move the label along its segment, or onto another segment",
    "label-on-line": "place the label at y = lineY−8 (horizontal) or x = lineX+10 (vertical)",
    "label-overlap": "slide one label along its segment, or shorten it",
    "label-length": "keep edge labels to 1–2 short words; move detail into the role line",
    "label-group-corner": "move the label off the group's label corner",
    "legend-missing": "add a legend swatch for that edge kind",
    "legend-extra": "remove the unused legend entry",
    "legend": "add a legend strip under the canvas",
    "budget-nodes": "merge or cut nodes, or split into overview + detail",
    "budget-edges": "drop edges the layout already implies",
    "budget-accent": "keep accent on one continuous primary path",
    "budget-groups": "merge groups or split the diagram",
    "budget-nesting": "flatten to one nesting level (cloud → VPC → subnet excepted)",
    "grid": "snap positions to multiples of 4 (layout.py does)",
    "dom-nesting": "make every node and group a direct child of the canvas",
}


class Report:
    def __init__(self):
        self.items: list[tuple[str, str, str]] = []
        self.targets: dict[int, str] = {}
    def _add(self, level, cid, msg, target):
        self.items.append((level, cid, msg))
        if target:
            self.targets[len(self.items) - 1] = target
    def fail(self, cid, msg, target=None): self._add("FAIL", cid, msg, target)
    def warn(self, cid, msg, target=None): self._add("WARN", cid, msg, target)
    def info(self, cid, msg, target=None): self._add("INFO", cid, msg, target)
    def count(self, level): return sum(1 for l, _, _ in self.items if l == level)
    def records(self):
        out = []
        for i, (level, cid, msg) in enumerate(self.items):
            rec = {"level": level, "id": cid, "message": msg}
            target = self.targets.get(i) or (re.search(r'"([^"]+)"', msg).group(1) if re.search(r'"([^"]+)"', msg) else None)
            if target: rec["target"] = target
            if cid in FIXES: rec["fix"] = FIXES[cid]
            out.append(rec)
        return out


def run(path: Path, faithful: bool = False) -> Report:
    rep = Report()
    raw = path.read_text(encoding="utf-8")
    d = Diagram(); d.feed(raw)
    page_text = "".join(d.text_chunks)
    css = "\n".join(d.styles)

    # --- structure --------------------------------------------------------------------------
    for tok in sorted(set(TOKEN_RE.findall(raw))):
        rep.fail("unresolved-token", f"{tok} left in the file — run build.py")
    for ph in sorted(set(PLACEHOLDER_RE.findall(raw))):
        rep.fail("placeholder", f"[{ph}] placeholder still in the page")
    if d.scripts:
        rep.fail("script", f"{d.scripts} <script> element(s): a diagram is static markup (only the template's data-arch-diagram-viewer script is allowed)")
    if d.viewer_scripts > 1:
        rep.fail("script", f"{d.viewer_scripts} viewer scripts — the template carries exactly one")
    viewer_js = "".join(d.viewer_text)
    for needle in ("fetch(", "XMLHttpRequest", "import(", "WebSocket", "sendBeacon", "eval("):
        if needle in viewer_js:
            rep.fail("script", f"viewer script contains {needle!r} — the viewer must stay offline and self-contained")
            break
    for ref in d.remote:
        rep.fail("remote-asset", f"remote asset {ref} — everything but Google Fonts must be inlined")
    for src in d.img_srcs:
        if not src.startswith("data:"):
            rep.fail("icon-not-inlined", f"<img src=\"{src[:50]}\"> is not a data URI — run build.py")
            break
    if d.canvas is None:
        rep.fail("canvas", "no <div class=\"canvas\"> found")
        return rep
    cw, ch = d.canvas["w"], d.canvas["h"]
    if cw is None or ch is None:
        # the template sizes the canvas in its stylesheet; an inline style overrides it
        rule = re.search(r"\.canvas\s*\{([^}]*)\}", css)
        decl = parse_style(rule.group(1)) if rule else {}
        cw = cw if cw is not None else px(decl.get("width"))
        ch = ch if ch is not None else px(decl.get("height"))
    if cw is None or ch is None:
        rep.fail("canvas", "canvas needs a width/height in px (the .canvas rule or an inline style)")
        return rep
    if d.svg is None:
        rep.fail("edges", "no <svg class=\"edges\"> overlay found")
        return rep
    vb = [px(v) for v in d.svg["viewBox"].split()]
    if len(vb) != 4 or vb[2] != cw or vb[3] != ch:
        rep.fail("canvas-viewbox", f"svg.edges viewBox \"{d.svg['viewBox']}\" must be \"0 0 {fmt(cw)} {fmt(ch)}\" (the canvas size)")
    canvas_rect = (0, 0, cw, ch)

    # --- a11y ---------------------------------------------------------------------------------
    if not d.title.strip():
        rep.fail("title", "<title> is empty")
    if d.canvas.get("role") != "img":
        rep.fail("a11y-role", "canvas div needs role=\"img\"")
    aria = (d.canvas.get("aria") or "").strip()
    if not aria or PLACEHOLDER_RE.search(aria):
        rep.fail("a11y-label", "canvas div needs a one-sentence aria-label describing what connects to what")
    elif len(aria) < 20:
        rep.warn("a11y-label", "canvas aria-label is very short — say what connects to what")
    if d.svg.get("aria_hidden") != "true":
        rep.warn("a11y-edges", "svg.edges should carry aria-hidden=\"true\" (the canvas label describes it)")

    # --- korean -------------------------------------------------------------------------------
    hangul = bool(HANGUL_RE.search(page_text + aria + d.title))
    if hangul:
        if (d.lang or "").lower().split("-")[0] != "ko":
            rep.warn("lang", f"page carries Hangul but <html lang=\"{d.lang}\"> — set lang=\"ko\"")
        css_l = css.lower()
        if not any(f in css_l for f in KOREAN_FAMILIES):
            rep.fail("korean-font-stack", "Hangul labels but no Korean family (Pretendard / Noto Sans KR / Apple SD Gothic Neo) in the font tokens")
        embedded = 'font-family:"pretendard"' in css_l.replace(" ", "") or 'font-family:"notosanskr"' in css_l.replace(" ", "")
        if not embedded and not d.kr_link:
            rep.warn("korean-webfont", "no embedded or linked Korean webfont: rendering depends on the viewer's OS fonts (build.py --kr-font auto)")
        mono_decl = re.search(r"--font-mono\s*:\s*([^;]+)", css_l)
        if mono_decl and "font-kr" not in mono_decl.group(1) and not any(f in mono_decl.group(1) for f in KOREAN_FAMILIES):
            rep.warn("korean-mono", "--font-mono has no Korean tail: Hangul in role lines / edge labels falls to an OS monospace substitute")

    # --- nodes --------------------------------------------------------------------------------
    nodes = d.nodes
    if not nodes:
        rep.fail("nodes", "no <div class=\"node\"> elements inside the canvas")
        return rep
    off_grid = []
    for n in nodes:
        if n["x0"] is None or n["y0"] is None:
            rep.fail("node-pos", f"node \"{n['name']}\" needs inline left/top in px")
            n["x0"] = n["x0"] or 0; n["y0"] = n["y0"] or 0
        avail = n["w"] - 8
        n["lines"] = wrapped_lines(n["name"], 13, avail) if n["name"] else 1
        n["h"] = NODE_H + (n["lines"] - 1) * NAME_LINE
        n["x1"] = n["x0"] + n["w"]; n["y1"] = n["y0"] + n["h"]
        n["cx"] = n["x0"] + n["w"] / 2
        n["tile_rect"] = (n["cx"] - TILE / 2, n["y0"], n["cx"] + TILE / 2, n["y0"] + TILE)
        n["text_rect"] = (n["x0"], n["y0"] + TEXT_TOP, n["x1"], n["y1"])
        n["rect"] = (n["x0"], n["y0"], n["x1"], n["y1"])
        if not n["name"]:
            rep.fail("node-name", f"node at ({fmt(n['x0'])},{fmt(n['y0'])}) has no name")
        if n["lines"] > 2:
            rep.fail("name-fit", f"\"{n['name']}\" needs {n['lines']} lines in a {n['w']}px node — shorten it or use class wide/xwide")
        elif n["lines"] == 2:
            rep.info("name-wrap", f"\"{n['name']}\" wraps to two lines ({n['w']}px node; box grows to {n['h']}px)")
        if n["role"] and text_width(n["role"], 9.5, mono=True) > avail:
            rep.warn("role-fit", f"role \"{n['role']}\" is wider than its {n['w']}px node — shorten it or widen the node")
        if not n["imgs"]:
            rep.fail("tile-icon", f"\"{n['name']}\" has no <img> in its tile")
        if n.get("dom_nested"):
            rep.fail("dom-nesting", f"\"{n['name']}\" is nested inside a group div — nodes and groups are direct children of the canvas, in canvas coordinates")
        if not inside(n["rect"], canvas_rect):
            rep.fail("node-in-canvas", f"\"{n['name']}\" box ({fmt(n['x0'])}..{fmt(n['x1'])}, {fmt(n['y0'])}..{fmt(n['y1'])}) sticks out of the {fmt(cw)}×{fmt(ch)} canvas")
        if n["x0"] % 4 or n["y0"] % 4:
            off_grid.append(n["name"])
    focal = [n for n in nodes if "focal" in n["tile"]]
    if len(focal) > 1:
        rep.fail("focal", f"{len(focal)} focal tiles ({', '.join(x['name'] for x in focal)}) — at most one")
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            if rects_overlap(a["rect"], b["rect"]):
                rep.fail("node-overlap", f"\"{a['name']}\" and \"{b['name']}\" boxes overlap")
            elif abs(a["y0"] - b["y0"]) < 20:
                gap = max(b["x0"] - a["x1"], a["x0"] - b["x1"])
                if gap < 8:
                    rep.warn("node-spacing", f"\"{a['name']}\" and \"{b['name']}\" are {fmt(gap)}px apart — keep centers ≥ 140px apart")

    # --- budget -------------------------------------------------------------------------------
    paths = d.svg["paths"]
    n_nodes, n_edges = len(nodes), len(paths)
    cap = 14 if not faithful else 20
    if n_nodes > cap:
        rep.fail("budget-nodes", f"{n_nodes} nodes — split into an overview and a detail diagram (cap {cap})")
    elif n_nodes > 9:
        rep.warn("budget-nodes", f"{n_nodes} nodes — above the 9-node default budget; is every one load-bearing?")
    if n_edges > 12:
        rep.warn("budget-edges", f"{n_edges} edges — above the 12-edge budget; remove what layout already says")
    accent = [p for p in paths if "e" in p["classes"]]
    if len(accent) > 5:
        rep.warn("budget-accent", f"{len(accent)} accent-colored edges — the primary flow should read as one continuous path")
    # (group budget is reported after geometric nesting is resolved below)

    # --- groups -------------------------------------------------------------------------------
    groups = [g for g in d.groups if not g.get("bad")]
    for g in d.groups:
        if g.get("bad"):
            rep.fail("group-pos", f"group \"{g['label']}\" needs inline left/top/width/height in px")
        if g.get("dom_nested"):
            rep.fail("dom-nesting", f"group \"{g['label']}\" is nested inside another group div — draw nested groups as siblings positioned inside the parent")
    for g in groups:
        g["rect"] = (g["x0"], g["y0"], g["x1"], g["y1"])
    # geometric nesting: the smallest group that fully contains this one is its parent
    for g in groups:
        outer = [o for o in groups if o is not g and inside(g["rect"], o["rect"])]
        if outer:
            g["parent"] = min(outer, key=lambda o: o["w"] * o["h"])
    for g in groups:
        depth, p = 1, g["parent"]
        while p is not None:
            depth += 1; p = p["parent"]
        g["depth"] = depth
    for g in groups:
        # label corner: 12px inset + icon + text + 10px margin — edges and labels keep out of it
        lw = 12 + (20 if g.get("icon") else 0) + text_width(g["label"], 12) + 10
        g["corner"] = (g["x0"], g["y0"], min(g["x1"], g["x0"] + lw), g["y0"] + LABEL_CORNER_H)
        if not inside(g["rect"], canvas_rect):
            rep.fail("group-in-canvas", f"group \"{g['label']}\" sticks out of the canvas")
        if any(v % 4 for v in (g["x0"], g["y0"], g["w"], g["h"])):
            off_grid.append(f"group {g['label']}")
        if g["parent"] is not None and not g["parent"].get("bad"):
            p = g["parent"]
            if not inside(g["rect"], p["rect"], 16, 40, 16, 16):
                rep.warn("group-nesting", f"nested group \"{g['label']}\" should sit ≥16px inside \"{p['label']}\" and ≥40px below its top")
    top_groups = [g for g in groups if g["parent"] is None]
    if len(top_groups) > 4:
        rep.warn("budget-groups", f"{len(top_groups)} top-level groups — more than 4 reads like a swimlane")
    vendor = any(c in g["classes"] for g in groups for c in ("aws", "gcp", "azure"))
    if any(g["depth"] > (3 if vendor else 2) for g in groups):
        rep.warn("budget-nesting", "groups nested more than one level deep get noisy (cloud → VPC → subnet is the sanctioned exception)")
    for i, a in enumerate(groups):
        for b in groups[i + 1:]:
            if rects_overlap(a["rect"], b["rect"]) and not (inside(a["rect"], b["rect"]) or inside(b["rect"], a["rect"])):
                rep.fail("group-overlap", f"groups \"{a['label']}\" and \"{b['label']}\" overlap without nesting")
    for n in nodes:
        for g in groups:
            if g["x0"] <= n["cx"] <= g["x1"] and g["y0"] <= n["y0"] + TILE / 2 <= g["y1"]:
                if not inside(n["rect"], g["rect"], 12, 40, 12, 8):
                    rep.fail("node-in-group", f"\"{n['name']}\" is not fully inside group \"{g['label']}\" (need ≥12px sides, 40px under the label, 8px bottom)")
            elif rects_overlap(n["rect"], g["rect"]):
                rep.fail("node-group-edge", f"\"{n['name']}\" straddles the border of group \"{g['label']}\"")

    # --- edges --------------------------------------------------------------------------------
    def anchor(ptx, pty):
        """(node, side) when the point sits 2–12px outside a node's tile side, tile top, or box bottom."""
        best = None
        for n in nodes:
            tx0, ty0, tx1, ty1 = n["tile_rect"]
            if ty0 <= pty <= ty1:
                if GAP_MIN <= tx0 - ptx <= GAP_MAX: best = (n, "left"); break
                if GAP_MIN <= ptx - tx1 <= GAP_MAX: best = (n, "right"); break
            if tx0 - 4 <= ptx <= tx1 + 4 and GAP_MIN <= ty0 - pty <= GAP_MAX:
                best = (n, "top"); break
            if n["x0"] <= ptx <= n["x1"] and GAP_MIN <= pty - n["y1"] <= GAP_MAX:
                best = (n, "bottom"); break
        return best

    attach: dict[tuple, list] = {}
    all_segs: list[tuple] = []     # (seg, path index)
    for pi, p in enumerate(paths):
        segs = p["segs"]
        label = p["d"].strip()[:40]
        if not segs:
            rep.fail("edge-path", f"edge {pi + 1} has no drawable segments: d=\"{label}\"")
            continue
        p["ends"] = set()
        for s in segs:
            if s[4] in ("L", "C"):
                rep.fail("edge-diagonal", f"edge {pi + 1} has a diagonal/curved segment ({fmt(s[0])},{fmt(s[1])})→({fmt(s[2])},{fmt(s[3])}) — use H/V elbows only")
            if not rect_hit(s, canvas_rect) and s[4] != "A":
                rep.fail("edge-in-canvas", f"edge {pi + 1} leaves the canvas")
        for (ptx, pty), which in ((segs[0][:2], "start"), (segs[-1][2:4], "end")):
            hit = anchor(ptx, pty)
            if hit is None:
                rep.warn("edge-anchor", f"edge {pi + 1} {which} ({fmt(ptx)},{fmt(pty)}) is not 2–12px off a node's tile side, tile top or box bottom")
            else:
                n, side = hit
                p["ends"].add(id(n))
                attach.setdefault((id(n), side), []).append((ptx, pty, pi + 1, n["name"]))
        for s in segs:
            if s[4] != "A":
                all_segs.append((s, pi))
        # through nodes / text
        for n in nodes:
            for s in segs:
                if s[4] == "A":
                    continue
                if rect_hit(s, n["text_rect"], -1):
                    rep.fail("edge-through-text", f"edge {pi + 1} runs through the label text of \"{n['name']}\" — connect box-bottom to tile-top, or reroute")
                elif id(n) not in p["ends"] and rect_hit(s, n["tile_rect"], -1):
                    rep.fail("edge-through-node", f"edge {pi + 1} passes through the tile of \"{n['name']}\", which is not its endpoint")
        for g in groups:
            if any(s[4] != "A" and rect_hit(s, g["corner"], -1) for s in segs):
                rep.warn("edge-label-corner", f"edge {pi + 1} crosses the label corner of group \"{g['label']}\"")
        if not p["marker"]:
            rep.info("edge-marker", f"edge {pi + 1} has no marker-end — intended (undirected)?")
    # shared attach points
    for (nid, side), pts in attach.items():
        pts.sort()
        for a, b in zip(pts, pts[1:]):
            dist = math.hypot(a[0] - b[0], a[1] - b[1])
            if dist < ATTACH_MIN:
                rep.fail("edge-attach", f"edges {a[2]} and {b[2]} attach {fmt(dist)}px apart on the {side} of \"{a[3]}\" — fan attach points ≥12px apart")
    # overlapping / crowding strokes
    for i, (s1, p1) in enumerate(all_segs):
        for s2, p2 in all_segs[i + 1:]:
            if p1 == p2 or s1[4] != s2[4]:
                continue
            if s1[4] == "H":
                same, lo, hi = abs(s1[1] - s2[1]), max(min(s1[0], s1[2]), min(s2[0], s2[2])), min(max(s1[0], s1[2]), max(s2[0], s2[2]))
            else:
                same, lo, hi = abs(s1[0] - s2[0]), max(min(s1[1], s1[3]), min(s2[1], s2[3])), min(max(s1[1], s1[3]), max(s2[1], s2[3]))
            if hi - lo <= 3:
                continue
            if same < 1.5:
                rep.fail("edge-overlap", f"edges {p1 + 1} and {p2 + 1} share a stroke for {fmt(hi - lo)}px — offset one by ≥12px")
            elif same < ATTACH_MIN and hi - lo > 24:
                rep.warn("edge-crowding", f"edges {p1 + 1} and {p2 + 1} run {fmt(same)}px apart for {fmt(hi - lo)}px — keep parallel lines ≥12px apart")

    # --- edge labels --------------------------------------------------------------------------
    placed: list[tuple] = []
    for L in d.svg["labels"]:
        if L["x"] is None or L["y"] is None:
            rep.fail("label-pos", f"edge label \"{L['text']}\" needs x and y")
            continue
        step = "step" in L["classes"]
        size, mono = (12, False) if step else (10.5, True)
        w = text_width(L["text"], size, mono)
        x0 = {"middle": L["x"] - w / 2, "end": L["x"] - w}.get(L["anchor"], L["x"])
        box = (x0, L["y"] - size * 0.8, x0 + w, L["y"] + size * 0.22)
        if not inside(box, canvas_rect):
            rep.fail("label-in-canvas", f"edge label \"{L['text']}\" leaves the canvas")
        if label_len(L["text"]) > 16 and not step:
            rep.warn("label-length", f"edge label \"{L['text']}\" is long — keep to 1–2 short words; the role line carries detail")
        for n in nodes:
            # beside the tile a label may sit in the 36px either side of it; under it, the text band is the box
            if rects_overlap(box, n["tile_rect"]) or rects_overlap(box, n["text_rect"]):
                rep.fail("label-on-node", f"edge label \"{L['text']}\" overlaps node \"{n['name']}\"")
        for s, pi in all_segs:
            if rect_hit(s, box, 2):
                rep.fail("label-on-line", f"edge label \"{L['text']}\" touches edge {pi + 1} — keep ≥6px clear (y = lineY−8 above a horizontal line, x = lineX+10 beside a vertical one)")
                break
        for g in groups:
            if rects_overlap(box, g["corner"]):
                rep.warn("label-group-corner", f"edge label \"{L['text']}\" sits in the label corner of group \"{g['label']}\"")
        for other_text, other_box in placed:
            if rects_overlap(box, other_box, 2):
                rep.fail("label-overlap", f"edge labels \"{L['text']}\" and \"{other_text}\" overlap")
        placed.append((L["text"], box))

    # --- legend -------------------------------------------------------------------------------
    def kind(classes):
        if "aws" in classes: return None
        base = "e" if "e" in classes else "n" if "n" in classes else None
        if base is None: return None
        return base + (" dash" if "dash" in classes else "")
    used = {k for k in (kind(p["classes"]) for p in paths) if k}
    have = set()
    for sw in d.legend_sw:
        if "box" in sw:
            continue
        have.add(("n" if "n" in sw else "e") + (" dash" if "dash" in sw else ""))
    names = {"e": "accent solid (primary flow)", "n": "neutral solid", "n dash": "neutral dashed", "e dash": "accent dashed"}
    if used and not d.legend_present:
        rep.warn("legend", "no legend strip — add one entry per edge kind under the canvas")
    else:
        for k in sorted(used - have):
            rep.warn("legend-missing", f"edges use {names[k]} but the legend has no matching swatch")
        for k in sorted(have - used):
            rep.warn("legend-extra", f"legend shows {names[k]} but no edge uses it")

    if off_grid:
        rep.warn("grid", f"{len(off_grid)} position(s) off the 4px grid: {', '.join(off_grid[:4])}{'…' if len(off_grid) > 4 else ''}")
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--faithful", action="store_true", help="raise the node cap to 20 for a deliberately dense import")
    ap.add_argument("--json", action="store_true", help="append a JSON report")
    args = ap.parse_args()
    if not args.file.exists():
        print(f"no such file: {args.file}"); return 2
    rep = run(args.file, faithful=args.faithful)
    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    for level, cid, msg in sorted(rep.items, key=lambda t: order[t[0]]):
        print(f"[{level}] {cid}: {msg}")
    f, w, i = rep.count("FAIL"), rep.count("WARN"), rep.count("INFO")
    status = "FAIL" if f or (args.strict and w) else "WARN" if w else "PASS"
    print(f"check: {status} ({f} fail, {w} warn, {i} info) — {args.file.name}")
    if args.json:
        print(json.dumps({"status": status, "counts": {"fail": f, "warn": w, "info": i},
                          "findings": rep.records()}, ensure_ascii=False, indent=2))
    return 1 if status == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
