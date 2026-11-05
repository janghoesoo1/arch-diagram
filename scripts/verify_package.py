#!/usr/bin/env python3
"""Repository package gate: manifests in sync, SKILL.md within its byte cap, commands wired.

    python3 scripts/verify_package.py

- The native host manifests (.claude-plugin, .codex-plugin, .factory-plugin) carry one shared
  identity: name, description, version, author, homepage, repository, license, keywords.
- Every marketplace resolves to the repository root ("./").
- SKILL.md stays under MAX_SKILL_BYTES and its frontmatter description names the trigger
  vocabulary (architecture, stack, infra, Korean, AWS / GCP / Azure).
- Each command in commands/ references only files that exist.
- The shipped example and the template carry no unresolved placeholders the checker would reject.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills/arch-diagram"
MAX_SKILL_BYTES = 40_000
SHARED = ("name", "description", "version", "author", "homepage", "repository", "license", "keywords")
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".factory-plugin/plugin.json")
MARKETPLACES = (".claude-plugin/marketplace.json", ".factory-plugin/marketplace.json", ".agents/plugins/marketplace.json")
TRIGGERS = ("architecture", "stack", "infra", "아키텍처", "구성도", "AWS", "Google Cloud", "Azure", "Korean", "PNG", "TSX")
REQUIRED_FILES = (
    "SKILL.md", "LICENSE", "assets/template.html", "assets/fonts/Geist.woff2", "assets/fonts/JetBrainsMono.woff2",
    "assets/fonts/OFL-Geist.txt", "assets/fonts/OFL-JetBrainsMono.txt", "assets/generic/user.svg",
    "assets/examples/order-service.html", "assets/examples/src/order-service.html",
    "scripts/fetch_icons.py", "scripts/build.py", "scripts/check.py", "scripts/render_png.py",
    "references/geometry.md", "references/icons.md", "references/korean.md", "references/style.md",
    "references/tsx.md", "references/export.md", "references/doctor.md",
)

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def load(rel: str) -> dict:
    p = ROOT / rel
    if not p.exists():
        err(f"missing {rel}")
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{rel}: invalid JSON ({e})")
        return {}


manifests = {rel: load(rel) for rel in MANIFESTS}
base = manifests[MANIFESTS[0]]
for rel, m in manifests.items():
    for key in SHARED:
        if key not in m:
            err(f"{rel}: missing {key}")
        elif m[key] != base.get(key):
            err(f"{rel}: {key} differs from {MANIFESTS[0]}")
if base.get("name") != "arch-diagram":
    err("plugin name must be arch-diagram")
if not re.fullmatch(r"\d+\.\d+\.\d+", str(base.get("version", ""))):
    err(f"version {base.get('version')!r} is not semver")
codex = manifests[".codex-plugin/plugin.json"]
if codex.get("skills") != "./skills/":
    err(".codex-plugin/plugin.json: skills must be ./skills/")
if not isinstance(codex.get("interface"), dict) or not codex["interface"].get("displayName"):
    err(".codex-plugin/plugin.json: interface.displayName missing")

for rel in MARKETPLACES:
    mp = load(rel)
    if mp.get("name") != "arch-diagram":
        err(f"{rel}: marketplace name must be arch-diagram")
    for entry in mp.get("plugins", []):
        src = entry.get("source")
        path = src.get("path") if isinstance(src, dict) else src
        if entry.get("name") != "arch-diagram" or path != "./":
            err(f"{rel}: plugin entry must be arch-diagram at ./")

skill_md = SKILL / "SKILL.md"
if skill_md.exists():
    raw = skill_md.read_bytes()
    if len(raw) > MAX_SKILL_BYTES:
        err(f"SKILL.md is {len(raw)} bytes (cap {MAX_SKILL_BYTES})")
    text = raw.decode("utf-8")
    fm = re.match(r"---\n(.*?)\n---", text, re.DOTALL)
    desc = re.search(r"^description:\s*(.*)$", fm.group(1), re.MULTILINE).group(1) if fm else ""
    if not fm or not re.search(r"^name:\s*arch-diagram\s*$", fm.group(1), re.MULTILINE):
        err("SKILL.md frontmatter must declare name: arch-diagram")
    for t in TRIGGERS:
        if t.lower() not in desc.lower():
            err(f"SKILL.md description lacks trigger word {t!r}")
    if "\r\n" in text:
        err("SKILL.md must use LF line endings")

for rel in REQUIRED_FILES:
    if not (SKILL / rel).exists():
        err(f"missing skills/arch-diagram/{rel}")

for cmd in sorted((ROOT / "commands").glob("*.md")):
    text = cmd.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "description:" not in text.split("---")[1]:
        err(f"{cmd.name}: missing frontmatter description")
    for link in re.findall(r"\]\((\.\./[^)]+)\)", text):
        if not (ROOT / "commands" / link).resolve().exists():
            err(f"{cmd.name}: broken reference {link}")
    for ref in re.findall(r"references/([a-z-]+\.md)", text):
        if not (SKILL / "references" / ref).exists():
            err(f"{cmd.name}: references/{ref} does not exist")

# the template keeps its placeholders (that is its job); the built example must not
example = SKILL / "assets/examples/order-service.html"
if example.exists():
    t = example.read_text(encoding="utf-8")
    if re.search(r"%%[A-Za-z0-9_-]+%%|\[(TITLE|KICKER|LEDE|DESC|FOOT-LEFT|ICON-SOURCES)\]", t):
        err("built example still carries placeholders")
    if "font-family:\"Pretendard\"" not in t.replace(" ", ""):
        err("built example should embed the Pretendard subset (build with --kr-font auto)")
template = SKILL / "assets/template.html"
if template.exists():
    t = template.read_text(encoding="utf-8")
    for tok in ("%%FONT_DISPLAY%%", "%%FONT_JBM%%", "<!-- KR-FONT:", 'class="canvas" role="img"', 'class="edges"', "--font-kr"):
        if tok not in t:
            err(f"template.html lost {tok!r}")

# no vendor icon packages or built vendor examples in the tree
for p in ROOT.rglob("*"):
    if p.is_file() and p.suffix == ".zip":
        err(f"zip archive committed: {p.relative_to(ROOT)}")
    if p.is_file() and p.name == "manifest.json" and "icons" in p.parts:
        err(f"icon manifest committed: {p.relative_to(ROOT)}")

if errors:
    print("\n".join(f"FAIL {e}" for e in errors))
    print(f"\n{len(errors)} problem(s)")
    sys.exit(1)
print(f"package ok: arch-diagram {base.get('version')} — manifests in sync, SKILL.md {len(skill_md.read_bytes())} bytes, commands wired")
