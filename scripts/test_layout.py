#!/usr/bin/env python3
"""Tests for layout.py, render.py and diff.py: the shipped specs lay out, build (offline, with stand-in
icons) and pass check.py; the layout is deterministic; the spec validator and the delta behave.

Run: python3 scripts/test_layout.py
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills/arch-diagram"
SCRIPTS = SKILL / "scripts"
SPECS = sorted((SKILL / "assets/examples/src").glob("*.json"))
PY = sys.executable


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


layout, check, diffmod = load("layout"), load("check"), load("diff")
failures = 0


def ok(name, cond, detail=""):
    global failures
    print(f"{'ok   ' if cond else 'FAIL '} {name}" + (f": {detail}" if detail and not cond else ""))
    if not cond:
        failures += 1


def stand_in_icons(spec: dict, into: Path):
    """One tiny SVG per icon name the spec uses, plus a _dark twin for group icons."""
    into.mkdir(parents=True, exist_ok=True)
    names = {n["icon"] for n in spec["nodes"]} | {g["icon"] for g in spec.get("groups", []) if g.get("icon")}
    for name in names:
        (into / f"{name}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="#3b82f6"/></svg>')
    for g in spec.get("groups", []):
        if g.get("icon"):
            (into / f"{g['icon']}_dark.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="#fff"/></svg>')


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    for spec_path in SPECS:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        icons = tmp / f"icons-{spec_path.stem}"
        stand_in_icons(spec, icons)
        out = tmp / f"{spec_path.stem}.html"
        r = subprocess.run([PY, str(SCRIPTS / "render.py"), str(spec_path), str(out), "--icons", str(icons), "--kr-font", "none", "--json"],
                           capture_output=True, text=True)
        ok(f"{spec_path.stem}: render.py delivers", r.returncode == 0 and out.exists(), r.stdout[-600:])
        if out.exists():
            rep = check.run(out)
            fails = [m for l, _, m in rep.items if l == "FAIL"]
            ok(f"{spec_path.stem}: check.py has no FAIL", not fails, "; ".join(fails))
            receipt = out.with_suffix(".receipt.json")
            ok(f"{spec_path.stem}: receipt written with sha256", receipt.exists() and "sha256" in json.loads(receipt.read_text()))
            text = out.read_text(encoding="utf-8")
            ok(f"{spec_path.stem}: nodes carry data-id and edges data-from/to", text.count('data-id="') >= len(spec["nodes"]) and text.count("data-from=") == len(spec.get("edges", [])))
            ok(f"{spec_path.stem}: exactly one viewer script, no other", text.count("<script") == 1 and "data-arch-diagram-viewer" in text)
        # determinism
        a, _ = layout.build_draft(spec_path, icons)
        b, _ = layout.build_draft(spec_path, icons)
        ok(f"{spec_path.stem}: layout is deterministic", a == b)

    # a failing candidate never replaces a delivered file
    good = SPECS[0]
    spec = json.loads(good.read_text(encoding="utf-8"))
    icons = tmp / f"icons-{good.stem}"
    out = tmp / "atomic.html"
    subprocess.run([PY, str(SCRIPTS / "render.py"), str(good), str(out), "--icons", str(icons), "--kr-font", "none"], capture_output=True)
    before = out.read_bytes()
    bad = json.loads(json.dumps(spec))
    bad["nodes"][0]["name"] = "아주아주아주아주 긴 이름의 데이터베이스 서버 인스턴스 클러스터 노드 이름"   # three lines → check FAIL
    bad["nodes"][0]["width"] = "default"
    bad_path = tmp / "bad.json"; bad_path.write_text(json.dumps(bad, ensure_ascii=False))
    r = subprocess.run([PY, str(SCRIPTS / "render.py"), str(bad_path), str(out), "--icons", str(icons), "--kr-font", "none"], capture_output=True, text=True)
    ok("render.py: failing check exits non-zero", r.returncode != 0)
    ok("render.py: previous output untouched on failure", out.read_bytes() == before)
    ok("render.py: rejected candidate kept", out.with_suffix(".rejected.html").exists())
    ok("render.py: findings carry a fix hint", "fix:" in r.stdout)

    # spec validation
    def spec_error(mutate):
        s = json.loads(json.dumps(spec))
        mutate(s)
        try:
            layout.validate_spec(s); layout.layout(s, None)
            return None
        except layout.SpecError as e:
            return str(e)
    ok("spec: duplicate cell rejected", "share cell" in (spec_error(lambda s: s["nodes"][1].update(row=s["nodes"][0]["row"], col=s["nodes"][0]["col"])) or ""))
    ok("spec: unknown edge endpoint rejected", "is not a node id" in (spec_error(lambda s: s["edges"].append({"from": s["nodes"][0]["id"], "to": "nope"})) or ""))
    ok("spec: two focal nodes rejected", "focal" in (spec_error(lambda s: [n.update(focal=True) for n in s["nodes"][:2]]) or ""))
    synthetic = {"title": "t", "description": "a b c d e f g h i j k l m n o p",
                 "groups": [{"id": "g", "label": "G"}],
                 "nodes": [{"id": "a", "name": "A", "icon": "x", "row": 0, "col": 0, "group": "g"},
                           {"id": "s", "name": "S", "icon": "x", "row": 0, "col": 1},
                           {"id": "b", "name": "B", "icon": "x", "row": 0, "col": 2, "group": "g"}],
                 "edges": [{"from": "a", "to": "b"}]}
    try:
        layout.validate_spec(synthetic); layout.layout(synthetic, None); err = None
    except layout.SpecError as e:
        err = str(e)
    ok("spec: non-member inside a group's box rejected", err is not None and "without being a member" in err, err or "no error")

    # auto width for Korean names
    ok("layout: long Korean name widens the node", layout.node_width({"name": "재고 데이터베이스 클러스터", "role": ""}) >= 172)
    ok("layout: short Latin name stays default", layout.node_width({"name": "Neon", "role": "PostgreSQL 16"}) == 132)

    # delta
    head = json.loads(json.dumps(spec))
    head["nodes"][0]["role"] = "changed role"
    removed = head["nodes"].pop()
    head["edges"] = [e for e in head["edges"] if removed["id"] not in (e["from"], e["to"])]
    head["nodes"].append({"id": "newbie", "name": "New", "icon": spec["nodes"][0]["icon"], "row": 5, "col": 0})
    head["edges"].append({"from": spec["nodes"][0]["id"], "to": "newbie", "kind": "async", "label": "new"})
    rep = diffmod.diff(spec, head)
    ok("diff: added / removed / changed nodes found", "newbie" in rep["nodes"]["added"] and removed["id"] in rep["nodes"]["removed"] and any(c["id"] == spec["nodes"][0]["id"] for c in rep["nodes"]["changed"]))
    annotated, unplaced = diffmod.annotate(spec, head, rep)
    deltas = {n["id"]: n.get("delta") for n in annotated["nodes"]}
    ok("diff: annotate marks added/changed/removed", deltas.get("newbie") == "added" and deltas.get(spec["nodes"][0]["id"]) == "changed" and deltas.get(removed["id"]) == "removed")
    ann_path = tmp / "ann.json"; ann_path.write_text(json.dumps(annotated, ensure_ascii=False))
    stand_in_icons(annotated, icons)
    html, _ = layout.build_draft(ann_path, icons)
    ok("diff: annotated spec renders with delta markers and legend", 'data-delta="added"' in html and 'data-delta="removed"' in html and "delta-added" in html)

print()
if failures:
    print(f"{failures} test(s) failed"); sys.exit(1)
print("all layout / render / diff tests passed")
