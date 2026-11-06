#!/usr/bin/env python3
"""Spec → delivered diagram, atomically: layout, build, check, and only then replace the output.

    python3 render.py SPEC.json OUT.html --icons DIR [--kr-font auto|PATH|none] [--png] [--scale 2]
                      [--allow-warn] [--strict] [--faithful] [--json]

Gates, in order (the run stops at the first failing one):
  1. spec      JSON shape, ids, grid cells, group membership      (layout.py)
  2. layout    deterministic geometry, label placement           (layout.py)
  3. build     icons + fonts inlined, Korean font settled        (build.py)
  4. check     the readability gate                              (check.py)
  5. exports   optional PNG/SVG/GIF, staged before publication   (Playwright; GIF also Pillow)

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
import argparse
from presentation import present, STYLES, MODES

HERE = Path(__file__).resolve().parent
PY = sys.executable or "python3"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--icons")
    parser.add_argument("--kr-font", dest="kr")
    parser.add_argument("--scale", default="2")
    for flag in ("png", "svg", "gif", "strict", "faithful", "json", "allow-warn", "animate"):
        parser.add_argument("--" + flag, action="store_true")
    parser.add_argument("--style", choices=STYLES, default="professional")
    parser.add_argument("--animation-mode", choices=MODES, default="flow")
    parser.add_argument("--gif-fps", type=int, default=15)
    parser.add_argument("--gif-width", type=int, default=900)
    parser.add_argument("--gif-duration", type=float)
    opts = vars(parser.parse_args())
    if opts["gif"] and not opts["animate"]:
        parser.error("--gif requires --animate; static specs are not silently animated")
    if not 1 <= opts["gif_fps"] <= 30 or not 320 <= opts["gif_width"] <= 1920:
        parser.error("GIF FPS must be 1..30 and width 320..1920")
    if opts["gif_duration"] is not None and not 0.1 <= opts["gif_duration"] <= 30:
        parser.error("GIF duration must be 0.1..30 seconds")
    spec, out = opts["spec"], opts["out"]
    if (opts["animate"] or opts["style"] != "professional" or opts["svg"]) and opts["kr"] is None:
        opts["kr"] = "auto"
    if not spec.exists():
        print(f"no such spec: {spec}"); return 2
    out.parent.mkdir(parents=True, exist_ok=True)
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
    if opts["animate"] or opts["style"] != "professional":
        try:
            draft.write_text(present(draft.read_text(encoding="utf-8"), opts["style"],
                                     opts["animate"], opts["animation_mode"]), encoding="utf-8")
        except ValueError as error:
            gate("presentation", False, str(error))
            return finish(2)
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
    exports = []
    for kind in ("svg", "gif"):
        if not opts[kind]:
            continue
        candidate = tmpdir / ("built." + kind)
        cmd = [PY, str(HERE / "export_media.py"), str(built), str(candidate), "--format", kind]
        if kind == "gif":
            cmd += ["--fps", str(opts["gif_fps"]), "--width", str(opts["gif_width"])]
            if opts["gif_duration"] is not None:
                cmd += ["--duration", str(opts["gif_duration"])]
        r = run(cmd)
        if not gate(kind, r.returncode == 0, r.stdout + r.stderr):
            shutil.copy(built, out.with_suffix(".rejected.html"))
            return finish(5)
        exports.append((candidate, out.with_suffix("." + kind)))
        receipt[kind] = str(out.with_suffix("." + kind))
    if opts["png"]:
        png = tmpdir / "built.png"
        r = run([PY, str(HERE / "render_png.py"), str(built), str(png), "--scale", opts["scale"]])
        if not gate("png", r.returncode == 0, r.stdout + r.stderr):
            shutil.copy(built, out.with_suffix(".rejected.html"))
            return finish(5)
        exports += [(png, out.with_suffix(".png")),
                    (tmpdir / "built-dark.png", out.with_name(out.stem + "-dark.png"))]
        receipt["png"] = [str(destination) for _, destination in exports[-2:]]
    data = built.read_bytes()
    receipt["sha256"] = hashlib.sha256(data).hexdigest()
    receipt["bytes"] = len(data)
    receipt["status"] = "PASS"
    receipt["exports"] = {str(destination): hashlib.sha256(candidate.read_bytes()).hexdigest()
                          for candidate, destination in exports}
    staged_receipt = tmpdir / "receipt.json"
    staged_receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    deliveries = exports + [(built, out), (staged_receipt, out.with_suffix(".receipt.json"))]
    staged, replaced = [], []
    try:
        for candidate, destination in deliveries:
            with tempfile.NamedTemporaryFile(dir=out.parent, prefix=".arch-diagram-", delete=False) as handle:
                staged_path = Path(handle.name)
            staged.append((staged_path, destination, destination.read_bytes() if destination.exists() else None))
            shutil.copy(candidate, staged_path)
        for staged_path, destination, previous in staged:
            os.replace(staged_path, destination)
            replaced.append((destination, previous))
    except OSError as error:
        for destination, previous in reversed(replaced):
            if previous is None:
                destination.unlink()
            else:
                with tempfile.NamedTemporaryFile(dir=out.parent, prefix=".arch-diagram-", delete=False) as handle:
                    handle.write(previous)
                    restore = Path(handle.name)
                os.replace(restore, destination)
        gate("delivery", False, str(error))
        return finish(6)
    finally:
        for staged_path, _, _ in staged:
            if staged_path.exists():
                staged_path.unlink()
    rejected = out.with_suffix(".rejected.html")
    if rejected.exists():
        rejected.unlink()
    print(f"delivered {out} ({len(data) // 1024} KB) · receipt {out.with_suffix('.receipt.json').name}")
    return finish(0)


if __name__ == "__main__":
    sys.exit(main())
