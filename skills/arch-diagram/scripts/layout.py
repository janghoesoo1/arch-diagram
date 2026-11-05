#!/usr/bin/env python3
"""Deterministic layout: a typed JSON spec → a draft arch-diagram HTML.

    python3 layout.py SPEC.json DRAFT.html [--icons DIR] [--template PATH]

The spec names nodes on a row/column grid, groups by membership, and edges by endpoint;
this script does the geometry (references/geometry.md) so nobody hand-places coordinates:

  columns   width = widest node in the column (auto-widened for Korean names), 68px apart
  rows      160px between tile tops; 248px when a group border lies between the rows
  groups    the padded box around their members (24px sides, 60px label band, 50px below);
            nesting is geometric, parents grow around children (+24 sides, +40 above)
  edges     same row → tile side to tile side; stacked → box bottom to tile top; otherwise an
            elbow through the routing band between the rows; attach points fanned ≥ 12px apart;
            a request/return pair offset; the lower-priority line hops a crossing
  labels    beside their own segment, clear of lines, tiles, group borders and other labels

The same spec always yields the same HTML, and a change to one node moves only what depends
on it. `references/spec.md` documents the format; `check.py` remains the gate on the result.
"""
from __future__ import annotations

import html
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("check", HERE / "check.py")
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)

TEMPLATE = HERE.parent / "assets" / "template.html"
WIDTHS = {"default": 132, "wide": 172, "xwide": 212}
TILE, NODE_H, NAME_LINE = 60, 100, 17
COL_GAP, ROW_PITCH, ROW_PITCH_BAND = 68, 160, 248
GROUP_SIDE, GROUP_TOP, GROUP_BOTTOM, NEST_SIDE, NEST_TOP = 24, 60, 50, 24, 40
GAP_OUT, GAP_IN = 4, 6                    # line start / end clearance from the tile
KIND_CLASS = {"primary": "e", "internal": "n", "async": "n dash"}
KIND_PRIORITY = {"primary": 3, "internal": 2, "async": 1}
LEGEND = {
    "ko": {"primary": "주 요청 경로", "internal": "내부 연결", "async": "비동기 · 배포",
           "added": "추가", "removed": "삭제", "changed": "변경"},
    "en": {"primary": "request path", "internal": "internal", "async": "async / deploy",
           "added": "added", "removed": "removed", "changed": "changed"},
}
PALETTES = {   # --color-g1 family hints: (light g1, g1-soft, g1-ink, g1-tint, dark g1, g1-soft, g1-ink, g1-tint)
    "warm": None,
    "graphite": ("oklch(40% 0.02 258)", "oklch(60% 0.02 258)", "oklch(34% 0.02 258)", "oklch(95% 0.004 258 / .5)",
                 "oklch(75% 0.01 258)", "oklch(55% 0.01 258)", "oklch(88% 0.01 258)", "oklch(26% 0.008 258 / .5)"),
    "green": ("oklch(62% 0.14 150)", "oklch(74% 0.11 150)", "oklch(46% 0.12 150)", "oklch(96% 0.02 150 / .5)",
              "oklch(70% 0.13 150)", "oklch(56% 0.10 150)", "oklch(80% 0.12 150)", "oklch(26% 0.03 150 / .4)"),
    "blue": ("oklch(60% 0.15 250)", "oklch(72% 0.12 250)", "oklch(46% 0.13 250)", "oklch(96% 0.015 250 / .5)",
             "oklch(70% 0.13 250)", "oklch(56% 0.10 250)", "oklch(80% 0.11 250)", "oklch(26% 0.03 250 / .4)"),
    "purple": ("oklch(58% 0.17 300)", "oklch(70% 0.13 300)", "oklch(44% 0.15 300)", "oklch(96% 0.02 300 / .5)",
               "oklch(70% 0.14 300)", "oklch(56% 0.11 300)", "oklch(80% 0.12 300)", "oklch(26% 0.04 300 / .4)"),
}


class SpecError(Exception):
    pass


def snap(v, up=True):
    return int(math.ceil(v / 4) * 4) if up else int(math.floor(v / 4) * 4)


def esc(s):
    return html.escape(str(s), quote=True)


# ----------------------------------------------------------------------------- spec
def load_spec(path: Path) -> dict:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SpecError(f"{path}: invalid JSON ({e})")
    return validate_spec(spec)


def validate_spec(spec: dict) -> dict:
    problems = []
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise SpecError("spec needs a non-empty \"nodes\" list")
    ids = set()
    for n in nodes:
        for key in ("id", "name", "icon"):
            if not n.get(key):
                problems.append(f"node {n.get('id') or n.get('name') or '?'}: missing \"{key}\"")
        if n.get("id") in ids:
            problems.append(f"duplicate node id \"{n['id']}\"")
        ids.add(n.get("id"))
        if not isinstance(n.get("row"), int) or not isinstance(n.get("col"), int) or n.get("row", 0) < 0 or n.get("col", 0) < 0:
            problems.append(f"node \"{n.get('id')}\": row and col must be non-negative integers")
        if n.get("width") not in (None, "default", "wide", "xwide", "auto"):
            problems.append(f"node \"{n.get('id')}\": width must be auto | default | wide | xwide")
    cells = {}
    for n in nodes:
        key = (n.get("row"), n.get("col"))
        if key in cells:
            problems.append(f"nodes \"{cells[key]}\" and \"{n['id']}\" share cell row {key[0]} col {key[1]}")
        cells[key] = n.get("id")
    groups = spec.get("groups") or []
    gids = set()
    for g in groups:
        if not g.get("id") or not g.get("label"):
            problems.append(f"group {g.get('id') or '?'}: needs \"id\" and \"label\"")
        if g.get("id") in gids:
            problems.append(f"duplicate group id \"{g['id']}\"")
        gids.add(g.get("id"))
    for g in groups:
        if g.get("parent") and g["parent"] not in gids:
            problems.append(f"group \"{g['id']}\": parent \"{g['parent']}\" does not exist")
    for n in nodes:
        if n.get("group") and n["group"] not in gids:
            problems.append(f"node \"{n['id']}\": group \"{n['group']}\" does not exist")
    edges = spec.get("edges") or []
    for i, e in enumerate(edges):
        for key in ("from", "to"):
            if e.get(key) not in ids:
                problems.append(f"edge {i + 1}: \"{key}\" = {e.get(key)!r} is not a node id")
        if e.get("from") == e.get("to"):
            problems.append(f"edge {i + 1}: from and to are the same node")
        if e.get("kind", "internal") not in KIND_CLASS:
            problems.append(f"edge {i + 1}: kind must be primary | internal | async")
    if sum(1 for n in nodes if n.get("focal")) > 1:
        problems.append("at most one node may be focal")
    if problems:
        raise SpecError("\n".join(problems))
    return spec


# ----------------------------------------------------------------------------- layout
def node_width(n) -> int:
    w = n.get("width") or "auto"
    if w in WIDTHS:
        return WIDTHS[w]
    name_w = check.text_width(n["name"], 13) + 8
    role_w = check.text_width(n.get("role", ""), 9.5, mono=True) + 8
    need = max(name_w, role_w)
    for key in ("default", "wide", "xwide"):
        if need <= WIDTHS[key]:
            return WIDTHS[key]
    return WIDTHS["xwide"]      # the name wraps to two lines; check.py reports three


def layout(spec: dict, icons_dir: Path | None = None) -> dict:
    nodes = [dict(n) for n in spec["nodes"]]
    groups = {g["id"]: dict(g) for g in (spec.get("groups") or [])}
    edges = [dict(e) for e in (spec.get("edges") or [])]
    by_id = {n["id"]: n for n in nodes}

    # group tree: depth and member sets (nodes + descendant groups)
    for g in groups.values():
        g["children"], g["members"] = [], []
    for g in groups.values():
        if g.get("parent"):
            groups[g["parent"]]["children"].append(g["id"])
    for n in nodes:
        if n.get("group"):
            groups[n["group"]]["members"].append(n["id"])
    def depth(gid):
        d, g = 1, groups[gid]
        while g.get("parent"):
            d += 1; g = groups[g["parent"]]
        return d
    for g in groups.values():
        g["depth"] = depth(g["id"])
        if not g["members"] and not g["children"]:
            raise SpecError(f"group \"{g['id']}\" has no members")
    max_depth = max((g["depth"] for g in groups.values()), default=0)

    def all_nodes(gid):
        g = groups[gid]
        out = list(g["members"])
        for c in g["children"]:
            out += all_nodes(c)
        return out
    def ancestors(gid):
        out = []
        while gid:
            out.append(gid); gid = groups[gid].get("parent")
        return out

    # columns
    for n in nodes:
        n["w"] = node_width(n)
        n["lines"] = check.wrapped_lines(n["name"], 13, n["w"] - 8)
        n["h"] = NODE_H + (n["lines"] - 1) * NAME_LINE
    ncols = max(n["col"] for n in nodes) + 1
    nrows = max(n["row"] for n in nodes) + 1
    col_w = [max([n["w"] for n in nodes if n["col"] == c] or [WIDTHS["default"]]) for c in range(ncols)]
    col_x0, cursor = [], 44
    for c in range(ncols):
        col_x0.append(cursor); cursor += col_w[c] + COL_GAP

    # rows: a routing band is needed between rows when a group border lies between them
    row_groups = [set() for _ in range(nrows)]
    for n in nodes:
        if n.get("group"):
            row_groups[n["row"]].update(ancestors(n["group"]))
    row_h = [max([n["h"] for n in nodes if n["row"] == r] or [NODE_H]) for r in range(nrows)]
    row_top, band_between = [], []
    top = 36 + GROUP_TOP + NEST_TOP * max(0, max_depth - 1) if groups else 48
    for r in range(nrows):
        row_top.append(top)
        if r + 1 < nrows:
            boundary = bool(row_groups[r] ^ row_groups[r + 1])
            band_between.append(boundary)
            top += (ROW_PITCH_BAND if boundary else ROW_PITCH) + (row_h[r] - NODE_H)
    for n in nodes:
        n["x0"] = col_x0[n["col"]] + (col_w[n["col"]] - n["w"]) // 2
        n["x0"] -= n["x0"] % 4
        n["y0"] = row_top[n["row"]]
        n["x1"], n["y1"] = n["x0"] + n["w"], n["y0"] + n["h"]
        n["cx"] = n["x0"] + n["w"] / 2
        n["tile"] = (n["cx"] - TILE / 2, n["y0"], n["cx"] + TILE / 2, n["y0"] + TILE)

    # group rectangles, children first
    def group_rect(gid):
        g = groups[gid]
        xs0, ys0, xs1, ys1 = [], [], [], []
        for nid in g["members"]:
            n = by_id[nid]
            xs0.append(n["x0"] - GROUP_SIDE); xs1.append(n["x1"] + GROUP_SIDE)
            ys0.append(n["y0"] - GROUP_TOP); ys1.append(n["y1"] + GROUP_BOTTOM)
        for cid in g["children"]:
            r = group_rect(cid)
            xs0.append(r[0] - NEST_SIDE); xs1.append(r[2] + NEST_SIDE)
            ys0.append(r[1] - NEST_TOP); ys1.append(r[3] + NEST_SIDE)
        rect = (snap(min(xs0), False), snap(min(ys0), False), snap(max(xs1)), snap(max(ys1)))
        g["rect"] = rect
        return rect
    for gid in groups:
        if not groups[gid].get("parent"):
            group_rect(gid)
    # every node geometrically inside a group must belong to it (or a descendant)
    for gid, g in groups.items():
        inside = set(all_nodes(gid))
        for n in nodes:
            r = g["rect"]
            if r[0] < n["cx"] < r[2] and r[1] < n["y0"] + TILE / 2 < r[3] and n["id"] not in inside:
                raise SpecError(f"node \"{n['id']}\" sits inside group \"{gid}\" without being a member — "
                                f"keep a group's members in contiguous cells, or move \"{n['id']}\" to another column/row")
    for gid, g in groups.items():
        lw = 12 + (20 if g.get("icon") else 0) + check.text_width(g["label"], 12) + 10
        g["corner"] = (g["rect"][0], g["rect"][1], g["rect"][0] + lw, g["rect"][1] + 32)

    # edges ---------------------------------------------------------------------------------
    for i, e in enumerate(edges):
        e["i"], e["kind"] = i, e.get("kind", "internal")
        a, b = by_id[e["from"]], by_id[e["to"]]
        e["aws"] = bool(a.get("group") and b.get("group") and
                        any("aws" in (groups[g].get("kind") or "").split() for g in ancestors(a["group"])) and
                        any("aws" in (groups[g].get("kind") or "").split() for g in ancestors(b["group"])))
    # attach points per (node, side), fanned by the counterpart's position
    def fan(k):
        if k == 1: return [0]
        step = 24 if k <= 3 else 16
        return [round(-step * (k - 1) / 2 + step * j) for j in range(k)]
    sides: dict[tuple, list] = {}
    def side_of(e, node, other):
        if node["row"] == other["row"]:
            return "right" if other["cx"] > node["cx"] else "left"
        return "bottom" if other["row"] > node["row"] else "top"
    for e in edges:
        a, b = by_id[e["from"]], by_id[e["to"]]
        e["a_side"], e["b_side"] = side_of(e, a, b), side_of(e, b, a)
        # an edge that skips a node in its own row goes over the top, tile top to tile top
        if a["row"] == b["row"]:
            between = [n for n in nodes if n["row"] == a["row"] and min(a["col"], b["col"]) < n["col"] < max(a["col"], b["col"])]
            if between:
                e["a_side"], e["b_side"], e["skip"] = "top", "top", True
        sides.setdefault((a["id"], e["a_side"]), []).append((e, b))
        sides.setdefault((b["id"], e["b_side"]), []).append((e, a))
    for (nid, side), items in sides.items():
        n = by_id[nid]
        if side in ("top", "bottom"):
            items.sort(key=lambda t: (t[1]["cx"], t[1]["row"], t[0]["i"]))
            offs = fan(len(items))
            # a counterpart straight above or below gets the centre, so that line stays vertical
            for off, (e, other) in zip(offs, items):
                if abs(other["cx"] - n["cx"]) < 1 and off != 0:
                    offs = [max(-28, min(28, o - off)) for o in offs]
                    break
            for off, (e, other) in zip(offs, items):
                e["a_x" if e["from"] == nid else "b_x"] = n["cx"] + off
    # same-row lines: one y per edge, shared by both ends. A request/return pair between the
    # same tiles sits at +26 / +50; a lone line at tile mid (+30)
    pairs: dict[frozenset, list] = {}
    for e in edges:
        if e["a_side"] in ("left", "right"):
            pairs.setdefault(frozenset((e["from"], e["to"])), []).append(e)
    for key, items in pairs.items():
        leftmost = min(key, key=lambda nid: by_id[nid]["cx"])
        items.sort(key=lambda e: (e["from"] != leftmost, e["i"]))
        ys = [30] if len(items) == 1 else [26, 50] if len(items) == 2 else [18, 30, 42][:len(items)]
        for y, e in zip(ys, items):
            e["y"] = by_id[e["from"]]["y0"] + y
    # keep attach points inside the tile and out of a group's label corner
    for e in edges:
        for end, nid in (("a", e["from"]), ("b", e["to"])):
            n = by_id[nid]
            if f"{end}_x" in e and n.get("group"):
                for gid in ancestors(n["group"]):
                    c = groups[gid]["corner"]
                    # only a node in the group's first row has its incoming vertical cross the label band
                    if e[f"{end}_side"] == "top" and n["y0"] - GROUP_TOP <= c[1] + 4 and c[0] <= e[f"{end}_x"] <= c[2] + 2:
                        e[f"{end}_x"] = max(e[f"{end}_x"], min(n["cx"] + 24, c[2] + 4))

    def band_y(r_hi, r_lo):
        """y of the routing band between rows r_hi (above) and r_lo (below)."""
        return row_top[r_lo] - (76 if band_between[r_hi] else 28)

    routes = []
    for e in edges:
        a, b = by_id[e["from"]], by_id[e["to"]]
        pts = []
        if e.get("skip"):
            y = band_y(a["row"] - 1, a["row"]) if a["row"] > 0 else a["y0"] - 28
            pts = [(e["a_x"], a["y0"] - GAP_OUT), (e["a_x"], y), (e["b_x"], y), (e["b_x"], b["y0"] - GAP_IN)]
        elif a["row"] == b["row"]:
            y = e["y"]
            if a["cx"] < b["cx"]:
                pts = [(a["tile"][2] + GAP_OUT, y), (b["tile"][0] - GAP_IN, y)]
            else:
                pts = [(a["tile"][0] - GAP_OUT, y), (b["tile"][2] + GAP_IN, y)]
        else:
            down = b["row"] > a["row"]
            start = (e["a_x"], a["y1"] + GAP_OUT) if down else (e["a_x"], a["y0"] - GAP_OUT)
            end = (e["b_x"], b["y0"] - GAP_IN) if down else (e["b_x"], b["y1"] + GAP_IN)
            if abs(start[0] - end[0]) < 1:
                pts = [start, end]
            else:
                y = band_y(a["row"], b["row"]) if down else band_y(b["row"], a["row"])
                pts = [start, (start[0], y), (end[0], y), end]
        e["pts"] = pts
        routes.append(e)
    # an elbow's band segment must not share its y with another band segment it overlaps
    for e in routes:
        if len(e["pts"]) != 4:
            continue
        for _ in range(4):
            y = e["pts"][1][1]
            lo, hi = sorted((e["pts"][1][0], e["pts"][2][0]))
            clash = any(o is not e and len(o["pts"]) == 4 and abs(o["pts"][1][1] - y) < 12 and
                        min(o["pts"][1][0], o["pts"][2][0]) < hi - 2 and max(o["pts"][1][0], o["pts"][2][0]) > lo + 2
                        for o in routes[:routes.index(e)])
            if not clash:
                break
            e["pts"][1] = (e["pts"][1][0], y + 12); e["pts"][2] = (e["pts"][2][0], y + 12)

    # hops: where a horizontal segment of one edge crosses a vertical of another, the lower
    # priority edge hops (ties: the horizontal one)
    def segs(e):
        return [(e["pts"][i], e["pts"][i + 1]) for i in range(len(e["pts"]) - 1)]
    for e in routes:
        e["hops"] = {}
    for e in routes:
        for si, (p, q) in enumerate(segs(e)):
            if p[1] != q[1]:
                continue                         # want horizontal
            for o in routes:
                if o is e:
                    continue
                for sj, (u, v) in enumerate(segs(o)):
                    if u[0] != v[0]:
                        continue                 # want vertical
                    x, y = u[0], p[1]
                    if min(p[0], q[0]) + 4 < x < max(p[0], q[0]) - 4 and min(u[1], v[1]) + 4 < y < max(u[1], v[1]) - 4:
                        pe, po = KIND_PRIORITY[e["kind"]], KIND_PRIORITY[o["kind"]]
                        if pe <= po:
                            e["hops"].setdefault(si, []).append(x)
                        else:
                            o["hops"].setdefault(sj, []).append(y)

    # labels --------------------------------------------------------------------------------
    label_boxes = []
    node_rects = [n["tile"] for n in nodes] + [(n["x0"], n["y0"] + 62, n["x1"], n["y1"]) for n in nodes]
    corners = [g["corner"] for g in groups.values()]
    borders, hborders = [], []
    for g in groups.values():
        r = g["rect"]
        borders += [(r[0], r[1], r[0], r[3]), (r[2], r[1], r[2], r[3])]
        hborders += [(r[0], r[1], r[2], r[1]), (r[0], r[3], r[2], r[3])]
    all_segs = [(p, q) for e in routes for (p, q) in segs(e)]

    def box_for(x, y, w, anchor, size=10.5):
        x0 = {"middle": x - w / 2, "end": x - w}.get(anchor, x)
        return (x0, y - size * 0.8, x0 + w, y + size * 0.22)
    def clear(box, own):
        pad = 2
        for r in node_rects + corners + label_boxes:
            if check.rects_overlap(box, r, pad):
                return False
        for (p, q) in all_segs:
            if (p, q) in own:
                continue
            if check.rect_hit((p[0], p[1], q[0], q[1]), box, pad):
                return False
        for (x0, y0, x1, y1) in borders:       # a label straddling a group border reads badly
            if box[0] - 6 < x0 < box[2] + 6 and box[1] < y1 and box[3] > y0:
                return False
        for (x0, y0, x1, y1) in hborders:
            if box[1] - 4 < y0 < box[3] + 4 and box[0] < x1 and box[2] > x0:
                return False
        return True

    for e in routes:
        text = e.get("label")
        e["label_pos"] = None
        if not text:
            continue
        w = check.text_width(text, 10.5, mono=True)
        own = set(segs(e))
        candidates = []
        ordered = sorted(enumerate(segs(e)), key=lambda t: -max(abs(t[1][0][0] - t[1][1][0]), abs(t[1][0][1] - t[1][1][1])))
        for si, (p, q) in ordered:
            if p[1] == q[1]:          # horizontal: above, centred, then slid toward either end
                lo, hi = sorted((p[0], q[0]))
                mid = (lo + hi) / 2
                for dx in (0, -24, 24, -48, 48, -72, 72):
                    x = mid + dx
                    if lo + w / 2 + 6 <= x <= hi - w / 2 - 6 or dx == 0:
                        candidates.append((x, p[1] - 8, "middle"))
            else:                     # vertical: right of the line, then left
                lo, hi = sorted((p[1], q[1]))
                mid = (lo + hi) / 2 + 4
                for dy in (0, -16, 16, -32, 32):
                    candidates.append((p[0] + 10, mid + dy, "start"))
                    candidates.append((p[0] - 10, mid + dy, "end"))
        for (x, y, anchor) in candidates:
            box = box_for(x, y, w, anchor)
            if clear(box, own):
                e["label_pos"] = (x, y, anchor)
                label_boxes.append(box)
                break
        if e["label_pos"] is None:
            x, y, anchor = candidates[0]
            e["label_pos"] = (x, y, anchor)
            label_boxes.append(box_for(x, y, w, anchor))
            e["label_warning"] = f"label \"{text}\" has no clear spot — check.py may object; shorten it or move an endpoint"

    # canvas ------------------------------------------------------------------------------
    right = max([n["x1"] for n in nodes] + [g["rect"][2] for g in groups.values()])
    bottom = max([n["y1"] for n in nodes] + [g["rect"][3] for g in groups.values()])
    for e in routes:
        for (x, y) in e["pts"]:
            right, bottom = max(right, x), max(bottom, y)
    for b in label_boxes:
        right, bottom = max(right, b[2]), max(bottom, b[3])
    return {"nodes": nodes, "groups": groups, "edges": routes, "by_id": by_id,
            "canvas": (snap(right + 36), snap(bottom + 36)), "icons_dir": icons_dir}


def fmt(v):
    return f"{int(v)}" if float(v).is_integer() else f"{v:.1f}"


# ----------------------------------------------------------------------------- html
def icon_tag(name, icons_dir, cls=""):
    """<img> for an icon token, with the lt/dk pair when a *_dark file exists."""
    dark = icons_dir is not None and any(icons_dir.glob(f"{name}_dark.*"))
    if dark:
        return (f'<img class="lt{(" " + cls) if cls else ""}" src="%%ICON_{name}%%" alt="">'
                f'<img class="dk{(" " + cls) if cls else ""}" src="%%ICON_{name}_dark%%" alt="">')
    return f'<img{(" class=" + chr(34) + cls + chr(34)) if cls else ""} src="%%ICON_{name}%%" alt="">'


def render(spec: dict, lay: dict, template: str) -> str:
    lang = spec.get("lang") or ("ko" if check.HANGUL_RE.search(json.dumps(spec, ensure_ascii=False)) else "en")
    words = LEGEND["ko" if lang.startswith("ko") else "en"]
    icons_dir = lay["icons_dir"]
    cw, ch = lay["canvas"]
    t = template
    t = t.replace('<html lang="ko">', f'<html lang="{esc(lang)}">', 1)
    for key, val in (("[TITLE]", spec.get("title", "")), ("[KICKER]", spec.get("kicker", "arch-diagram")),
                     ("[LEDE]", spec.get("lede", "")), ("[DESC]", spec.get("description", "")),
                     ("[FOOT-LEFT]", spec.get("footer", "")), ("[ICON-SOURCES]", spec.get("icon_sources", "icons: svgl"))):
        t = t.replace(key, esc(val))
    if not spec.get("lede"):
        t = t.replace('    <p class="lede"></p>\n', "")
    if not lang.startswith("ko"):
        # the toolbar's authored strings are Korean; the viewer re-labels them at run time, but the
        # markup must not carry Hangul into a non-Korean page (check.py reads the markup)
        for ko_s, en_s in (('placeholder="노드 찾기 ( / )" aria-label="노드 찾기"', 'placeholder="find node ( / )" aria-label="find node"'),
                           (">다크 (T)<", ">dark (T)<"), (">초기화 (Esc)<", ">clear (Esc)<"),
                           (">노드를 클릭하면 연결이 강조됩니다 · ? 도움말<", ">click a node to highlight its connections · ? help<")):
            t = t.replace(ko_s, en_s)
    t = re.sub(r"(\.canvas \{ position: relative; )width: \d+px; height: \d+px;", rf"\g<1>width: {cw}px; height: {ch}px;", t, count=1)
    pal = PALETTES.get((spec.get("theme") or {}).get("g1", "warm"))
    if pal:
        light = {"--color-g1:      oklch(68% 0.15 55);": pal[0], "--color-g1-soft: oklch(78% 0.12 55);": pal[1],
                 "--color-g1-ink:  oklch(52% 0.14 50);": pal[2], "--color-g1-tint: oklch(96.5% 0.015 60 / .5);": pal[3],
                 "--color-g1:      oklch(70% 0.14 55);": pal[4], "--color-g1-soft: oklch(58% 0.11 55);": pal[5],
                 "--color-g1-ink:  oklch(78% 0.12 55);": pal[6], "--color-g1-tint: oklch(26% 0.030 60 / .40);": pal[7]}
        for old, new in light.items():
            name = old.split(":")[0]
            t = t.replace(old, f"{name}: {new};", 1)

    # groups, outermost first so inner borders paint on top
    gl = []
    for g in sorted(lay["groups"].values(), key=lambda g: g["depth"]):
        x0, y0, x1, y1 = g["rect"]
        kind = g.get("kind") or "ga"
        icon = icon_tag(g["icon"], icons_dir) if g.get("icon") else ""
        delta = f' data-delta="{esc(g["delta"])}"' if g.get("delta") else ""
        gl.append(f'    <div class="group {esc(kind)}" data-id="{esc(g["id"])}"{delta} style="left:{x0}px; top:{y0}px; width:{x1 - x0}px; height:{y1 - y0}px;">\n'
                  f'      <div class="g-label">{icon}{esc(g["label"])}</div>\n    </div>')
    # edges
    el = []
    for e in lay["edges"]:
        cls = "aws" if e["aws"] else KIND_CLASS[e["kind"]]
        if e.get("delta"):
            cls += f" d-{e['delta']}"
        marker = "open" if e["aws"] else "ar"
        el.append(f'      <path class="{cls}" data-from="{esc(e["from"])}" data-to="{esc(e["to"])}" data-kind="{esc(e["kind"])}" d="{path_d_of(e)}" marker-end="url(#{marker})"/>')
        if e.get("label") and e["label_pos"]:
            x, y, anchor = e["label_pos"]
            lcls = "el a" if (e["kind"] == "primary" and not e["aws"]) else "el"
            el.append(f'      <text class="{lcls}" x="{fmt(x)}" y="{fmt(y)}" text-anchor="{anchor}">{esc(e["label"])}</text>')
    # nodes
    nl = []
    for n in lay["nodes"]:
        ncls = "node" + ("" if n["w"] == 132 else " wide" if n["w"] == 172 else " xwide")
        tcls = "tile" + ((" " + n["tile_class"]) if n.get("tile_class") else "") + (" focal" if n.get("focal") else "")
        attrs = f' data-id="{esc(n["id"])}"'
        if n.get("group"):
            attrs += f' data-group="{esc(n["group"])}"'
        if n.get("sources"):
            attrs += f' data-sources="{esc("; ".join(n["sources"]))}"'
        if n.get("note"):
            attrs += f' data-note="{esc(n["note"])}"'
        if n.get("delta"):
            attrs += f' data-delta="{esc(n["delta"])}"'
        role = f'<div class="role"><span>{esc(n["role"])}</span></div>' if n.get("role") else ""
        nl.append(f'    <div class="{ncls}"{attrs} style="left:{n["x0"]}px;top:{n["y0"]}px">\n'
                  f'      <div class="{tcls}">{icon_tag(n["icon"], icons_dir)}</div>\n'
                  f'      <div class="name"><span>{esc(n["name"])}</span></div>{role}\n    </div>')
    # legend: one entry per kind used, in the spec's words or the language defaults
    used = []
    for e in lay["edges"]:
        if not e["aws"] and e["kind"] not in used:
            used.append(e["kind"])
    legend_words = {**words, **(spec.get("legend") or {})}
    sw = {"primary": "sw", "internal": "sw n", "async": "sw n dash"}
    lg = [f'    <span><span class="{sw[k]}"></span>{esc(legend_words[k])}</span>' for k in ("primary", "internal", "async") if k in used]
    deltas = {x.get("delta") for x in lay["nodes"] + lay["edges"]} - {None}
    for d in ("added", "changed", "removed"):
        if d in deltas:
            lg.append(f'    <span><span class="sw box delta-{d}"></span>{esc(legend_words[d])}</span>')

    start = t.index("    <!-- GROUPS ====")
    end = t.index("  </div>\n  </div>\n\n  <!-- legend text")
    body = ("\n".join(gl) + "\n\n" if gl else "") + \
        f'    <svg class="edges" viewBox="0 0 {cw} {ch}" aria-hidden="true">\n      <defs>\n' \
        '        <marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">\n' \
        '          <path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/>\n        </marker>\n' \
        '        <marker id="open" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">\n' \
        '          <path d="M1 1 L9 5 L1 9" fill="none" stroke="context-stroke" stroke-width="1.5"/>\n        </marker>\n      </defs>\n' \
        + "\n".join(el) + "\n    </svg>\n\n" + "\n".join(nl) + "\n"
    t = t[:start] + body + "\n" + t[end:]
    t = re.sub(r'  <figcaption class="legend">.*?</figcaption>', '  <figcaption class="legend">\n' + "\n".join(lg) + "\n  </figcaption>", t, flags=re.DOTALL)
    t = t.replace("  <!-- legend text in the labels' language; one entry per edge kind actually used, nothing extra -->\n", "")
    return t


def path_d_of(e):
    # path_d lives in layout()'s closure for hop bookkeeping; rebuild it here from the same data
    parts = [f"M{fmt(e['pts'][0][0])} {fmt(e['pts'][0][1])}"]
    for si in range(len(e["pts"]) - 1):
        p, q = e["pts"][si], e["pts"][si + 1]
        hops = sorted(e["hops"].get(si, []), reverse=q[0] < p[0] or q[1] < p[1])
        if p[1] == q[1]:
            s = 1 if q[0] > p[0] else -1
            for x in hops:
                parts.append(f"H{fmt(x - 8 * s)} a8,8 0 0 {1 if s > 0 else 0} {fmt(16 * s)},0")
            parts.append(f"H{fmt(q[0])}")
        else:
            s = 1 if q[1] > p[1] else -1
            for y in hops:
                parts.append(f"V{fmt(y - 8 * s)} a8,8 0 0 {0 if s > 0 else 1} 0,{fmt(16 * s)}")
            parts.append(f"V{fmt(q[1])}")
    return " ".join(parts)


def tile_classes(spec):
    for n in spec["nodes"]:
        n["tile_class"] = n.get("tile") or ""


def build_draft(spec_path: Path, icons_dir: Path | None = None, template_path: Path = TEMPLATE) -> tuple[str, list[str]]:
    spec = load_spec(spec_path)
    tile_classes(spec)
    lay = layout(spec, icons_dir)
    warnings = [e["label_warning"] for e in lay["edges"] if e.get("label_warning")]
    return render(spec, lay, template_path.read_text(encoding="utf-8")), warnings


def main() -> int:
    args = sys.argv[1:]
    icons, template = None, TEMPLATE
    if "--icons" in args:
        i = args.index("--icons"); icons = Path(args[i + 1]); del args[i:i + 2]
    if "--template" in args:
        i = args.index("--template"); template = Path(args[i + 1]); del args[i:i + 2]
    if len(args) != 2:
        print(__doc__); return 1
    try:
        html_text, warnings = build_draft(Path(args[0]), icons, template)
    except SpecError as e:
        print(f"spec error:\n{e}"); return 2
    Path(args[1]).write_text(html_text, encoding="utf-8")
    for w in warnings:
        print(f"warning: {w}")
    print(f"laid out {args[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
