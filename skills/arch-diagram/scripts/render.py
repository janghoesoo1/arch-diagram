#!/usr/bin/env python3
"""Spec → delivered diagram, atomically: layout, build, check, and only then replace the output.

    python3 render.py SPEC.json OUT.html --icons DIR [--kr-font auto|PATH|none] [--png] [--scale 2]
                      [--allow-warn] [--strict] [--faithful] [--json]

Gates, in order (the run stops at the first failing one):
  1. spec      JSON shape, ids, grid cells, group membership      (layout.py)
  2. layout    deterministic geometry, label placement           (layout.py)
  3. build     icons + fonts inlined, Korean font settled        (build.py)
  4. check     the readability gate                              (check.py)
  5. png       optional render of both themes                    (render_png.py; needs Playwright)

A passing run writes OUT.html and OUT.receipt.json (gates, counts, findings, hashes). A failing
run leaves any previous OUT.html untouched, keeps the candidate as OUT.rejected.html, prints the
findings with their fixes, and exits non-zero. Warnings pass unless --strict; --allow-warn is
the default and exists for symmetry with check.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable or "python3"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def main() -> int:
    args = sys.argv[1:]
    opts = {"icons": None, "kr": None, "png": False, "scale": "2", "strict": False, "faithful": False, "json": False}
    for flag, key, takes in (("--icons", "icons", True), ("--kr-font", "kr", True), ("--scale", "scale", True),
                             ("--png", "png", False), ("--strict", "strict", False), ("--faithful", "faithful", False),
                             ("--json", "json", False), ("--allow-warn", None, False)):
        if flag in args:
            i = args.index(flag)
            if takes:
                if key: opts[key] = args[i + 1]
                del args[i:i + 2]
            else:
                if key: opts[key] = True
                del args[i]
    if len(args) != 2:
        print(__doc__); return 1
    spec, out = Path(args[0]), Path(args[1])
    if not spec.exists():
        print(f"no such spec: {spec}"); return 2
    icons = Path(opts["icons"]) if opts["icons"] else None
    t0 = time.time()
    receipt = {"spec": str(spec), "output": str(out), "gates": [], "status": "FAIL", "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    tmpdir = Path(tempfile.mkdtemp(prefix="arch-diagram-"))
    draft, built = tmpdir / "draft.html", tmpdir / "built.html"

    def gate(name, ok, detail=""):
        receipt["gates"].append({"name": name, "status": "pass" if ok else "fail", "detail": detail.strip()[:2000]})
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail.strip().splitlines()[0]}" if detail.strip() and not ok else ""))
        return ok

    def finish(code):
        receipt["seconds"] = round(time.time() - t0, 2)
        if opts["json"]:
            print(json.dumps(receipt, ensure_ascii=False, indent=2))
        shutil.rmtree(tmpdir, ignore_errors=True)
        return code

    # 1 + 2: spec and layout
    cmd = [PY, str(HERE / "layout.py"), str(spec), str(draft)] + (["--icons", str(icons)] if icons else [])
    r = run(cmd)
    if not gate("spec+layout", r.returncode == 0, r.stdout + r.stderr):
        return finish(2)
    for line in r.stdout.splitlines():
        if line.startswith("warning:"):
            print("  " + line)
    # 3: build
    cmd = [PY, str(HERE / "build.py"), str(draft), str(icons) if icons else str(tmpdir / "no-icons"), str(built)]
    if opts["kr"]:
        cmd += ["--kr-font", opts["kr"]]
    r = run(cmd)
    if not gate("build", r.returncode == 0, r.stdout + r.stderr):
        shutil.copy(draft, out.with_suffix(".rejected.html"))
        print(f"candidate kept at {out.with_suffix('.rejected.html')}")
        return finish(3)
    for line in r.stdout.splitlines():
        if "Hangul" in line or "embedded" in line or "switched" in line:
            print("  " + line)
    # 4: check
    cmd = [PY, str(HERE / "check.py"), str(built), "--json"] + (["--strict"] if opts["strict"] else []) + (["--faithful"] if opts["faithful"] else [])
    r = run(cmd)
    text, _, js = r.stdout.partition("\n{")
    try:
        report = json.loads("{" + js) if js else {"status": "?", "findings": []}
    except json.JSONDecodeError:
        report = {"status": "?", "findings": []}
    receipt["check"] = report
    ok = r.returncode == 0
    gate("check", ok, "" if ok else text)
    if not ok:
        for f in report.get("findings", []):
            if f["level"] == "FAIL":
                print(f"  [FAIL] {f['id']}: {f['message']}")
                if f.get("fix"):
                    print(f"         fix: {f['fix']}")
        shutil.copy(built, out.with_suffix(".rejected.html"))
        print(f"candidate kept at {out.with_suffix('.rejected.html')} — repair the spec and re-run")
        return finish(4)
    for f in report.get("findings", []):
        if f["level"] == "WARN":
            print(f"  [WARN] {f['id']}: {f['message']}")
    # deliver: atomic replace
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = out.with_suffix(out.suffix + ".tmp")
    shutil.copy(built, tmp_out)
    os.replace(tmp_out, out)
    data = out.read_bytes()
    receipt["sha256"] = hashlib.sha256(data).hexdigest()
    receipt["bytes"] = len(data)
    rejected = out.with_suffix(".rejected.html")
    if rejected.exists():
        rejected.unlink()
    # 5: png
    if opts["png"]:
        png = out.with_suffix(".png")
        r = run([PY, str(HERE / "render_png.py"), str(out), str(png), "--scale", opts["scale"]])
        if gate("png", r.returncode == 0, r.stdout + r.stderr):
            receipt["png"] = [str(png), str(png.with_name(png.stem + "-dark.png"))]
            for line in r.stdout.splitlines():
                if line.startswith("WARNING"):
                    print("  " + line)
        else:
            print("  PNG not produced (HTML was still delivered). Setup: pip install playwright && python3 -m playwright install --with-deps chromium")
    receipt["status"] = "PASS"
    out.with_suffix(".receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"delivered {out} ({len(data) // 1024} KB) · receipt {out.with_suffix('.receipt.json').name}")
    return finish(0)


if __name__ == "__main__":
    sys.exit(main())
