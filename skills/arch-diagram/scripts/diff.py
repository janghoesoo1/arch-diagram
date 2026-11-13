#!/usr/bin/env python3
"""Architecture delta: compare two specs and, optionally, mark the head spec for rendering.

    python3 diff.py BASE.json HEAD.json [--annotate OUT.json] [--json]

Reports nodes, groups and edges that were added, removed or changed (name, role, icon, group,
row/col for nodes; label for groups; kind/label for edges). Edges are matched by (from, to), or
by (from, to, label) when either spec draws that pair more than once.

--annotate writes HEAD with `delta` markers ("added" | "changed") on nodes, groups and edges,
and re-inserts removed nodes and edges with `delta: "removed"` so layout.py can draw them as
ghosts — a removed node keeps its base cell when that cell is free, otherwise it is listed in
the report under `unplaced` and left out of the picture. Render the annotated spec like any
other; the legend gains 추가 / 변경 / 삭제 entries automatically.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

NODE_FIELDS = ("name", "role", "icon", "group", "row", "col", "tile", "focal", "width")
GROUP_FIELDS = ("label", "kind", "parent", "icon")
EDGE_FIELDS = ("kind", "label")


def load(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"{p}: {e}")


def index(items, key):
    return {key(x): x for x in items}


def edge_key(*specs):
    dup = set()
    for s in specs:
        pairs = [(e["from"], e["to"]) for e in s.get("edges", [])]
        dup |= {p for p in pairs if pairs.count(p) > 1}
    return lambda e: (e["from"], e["to"], e.get("label", "")) if (e["from"], e["to"]) in dup else (e["from"], e["to"])


def edge_text(k):
    return f"{k[0]} → {k[1]}" + (f" [{k[2]}]" if len(k) > 2 else "")


def changed_fields(a, b, fields):
    return [f for f in fields if a.get(f) != b.get(f)]


def diff(base: dict, head: dict) -> dict:
    bn, hn = index(base.get("nodes", []), lambda n: n["id"]), index(head.get("nodes", []), lambda n: n["id"])
    bg, hg = index(base.get("groups", []), lambda g: g["id"]), index(head.get("groups", []), lambda g: g["id"])
    ek = edge_key(base, head)
    be, he = index(base.get("edges", []), ek), index(head.get("edges", []), ek)
    rep = {"nodes": {"added": [], "removed": [], "changed": []},
           "groups": {"added": [], "removed": [], "changed": []},
           "edges": {"added": [], "removed": [], "changed": []}}
    for i in hn.keys() - bn.keys():
        rep["nodes"]["added"].append(i)
    for i in bn.keys() - hn.keys():
        rep["nodes"]["removed"].append(i)
    for i in hn.keys() & bn.keys():
        f = changed_fields(bn[i], hn[i], NODE_FIELDS)
        if f:
            rep["nodes"]["changed"].append({"id": i, "fields": f})
    for i in hg.keys() - bg.keys():
        rep["groups"]["added"].append(i)
    for i in bg.keys() - hg.keys():
        rep["groups"]["removed"].append(i)
    for i in hg.keys() & bg.keys():
        f = changed_fields(bg[i], hg[i], GROUP_FIELDS)
        if f:
            rep["groups"]["changed"].append({"id": i, "fields": f})
    for k in he.keys() - be.keys():
        rep["edges"]["added"].append(list(k))
    for k in be.keys() - he.keys():
        rep["edges"]["removed"].append(list(k))
    for k in he.keys() & be.keys():
        f = changed_fields(be[k], he[k], EDGE_FIELDS)
        if f:
            rep["edges"]["changed"].append({"edge": list(k), "fields": f})
    for section in rep.values():
        for lst in section.values():
            lst.sort(key=lambda x: json.dumps(x, ensure_ascii=False))
    rep["total"] = sum(len(v) for s in rep.values() if isinstance(s, dict) for v in s.values())
    return rep


def annotate(base: dict, head: dict, rep: dict) -> tuple[dict, list[str]]:
    out = json.loads(json.dumps(head, ensure_ascii=False))
    bn = index(base.get("nodes", []), lambda n: n["id"])
    hn = index(out.get("nodes", []), lambda n: n["id"])
    cells = {(n["row"], n["col"]) for n in out.get("nodes", [])}
    unplaced = []
    for i in rep["nodes"]["added"]:
        hn[i]["delta"] = "added"
    for c in rep["nodes"]["changed"]:
        hn[c["id"]]["delta"] = "changed"
    for i in rep["nodes"]["removed"]:
        n = json.loads(json.dumps(bn[i], ensure_ascii=False))
        if (n["row"], n["col"]) in cells:
            unplaced.append(i)
            continue
        if n.get("group") and n["group"] not in {g["id"] for g in out.get("groups", [])}:
            n.pop("group")            # its group is gone too; the ghost stands alone in its old cell
        n["delta"] = "removed"; n.pop("focal", None)
        out.setdefault("nodes", []).append(n); cells.add((n["row"], n["col"]))
    hg = index(out.get("groups", []), lambda g: g["id"])
    for i in rep["groups"]["added"]:
        hg[i]["delta"] = "added"
    for c in rep["groups"]["changed"]:
        hg[c["id"]]["delta"] = "changed"
    ek = edge_key(base, head)
    he, be = index(out.get("edges", []), ek), index(base.get("edges", []), ek)
    for k in rep["edges"]["added"]:
        he[tuple(k)]["delta"] = "added"
    for c in rep["edges"]["changed"]:
        he[tuple(c["edge"])]["delta"] = "changed"
    present = {n["id"] for n in out.get("nodes", [])}
    for k in rep["edges"]["removed"]:
        if k[0] in present and k[1] in present:
            e = json.loads(json.dumps(be[tuple(k)], ensure_ascii=False))
            e["delta"] = "removed"
            out.setdefault("edges", []).append(e)
    return out, unplaced


def main() -> int:
    args = sys.argv[1:]
    out_path, as_json = None, False
    if "--annotate" in args:
        i = args.index("--annotate"); out_path = Path(args[i + 1]); del args[i:i + 2]
    if "--json" in args:
        args.remove("--json"); as_json = True
    if len(args) != 2:
        print(__doc__); return 1
    base, head = load(Path(args[0])), load(Path(args[1]))
    rep = diff(base, head)
    unplaced = []
    if out_path:
        annotated, unplaced = annotate(base, head, rep)
        out_path.write_text(json.dumps(annotated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rep["annotated"] = str(out_path)
        rep["unplaced"] = unplaced
    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        for kind in ("nodes", "groups", "edges"):
            for op in ("added", "removed", "changed"):
                for item in rep[kind][op]:
                    if isinstance(item, str): label = item
                    elif isinstance(item, list): label = edge_text(item)
                    else: label = item.get("id") or edge_text(item["edge"])
                    extra = f" ({', '.join(item['fields'])})" if isinstance(item, dict) and item.get("fields") else ""
                    print(f"{op:<8} {kind[:-1]:<6} {label}{extra}")
        print(f"delta: {rep['total']} change(s)" + (f"; annotated spec → {out_path}" if out_path else ""))
        if unplaced:
            print(f"not drawn (cell taken or group gone): {', '.join(unplaced)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
