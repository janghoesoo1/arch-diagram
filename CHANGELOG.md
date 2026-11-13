# Changelog

## 0.3.1 — 2026-11-13

- Spec validation rejects group parent cycles (previously a hang), more than three same-row lines between two tiles (previously a crash), `tile`/`delta` values that are not the documented words (previously written into HTML attributes unescaped) and icon names `fetch_icons.py` cannot produce.
- `diff.py` tells parallel edges between the same pair apart by label; sketch styles place their SVG correctly when text contains U+2028; a malformed `name=URL` no longer aborts the whole icon batch.
- SKILL.md description fits the 1024-character Agent Skills cap (now gated) and names sketch/animation/GIF; stale `--dark-only` and `--figure` command text removed; file lists and doctor checks cover the 0.3.0 scripts and assets.

## 0.3.0 — 2026-11-06

- Natural-language style, animation and export selection with conservative defaults, concise command hints and explicit revision/conflict handling.
- Optional draw, flow, steps and combined animation, with playback controls and reduced-motion support.
- Hybrid and full sketch styles that preserve canonical layout and brand icons.
- Optional SVG/GIF exports and staged media publication.
- Synchronized native plugin versions and explicit Claude Code auto-update, manual update and reload instructions.

## 0.2.0 — 2026-11-05

The archify lineage: a typed source, a delivery contract, an explorable artifact.

- **`scripts/layout.py`** — JSON spec → canvas HTML, deterministically: columns sized from the widest name (Korean auto-widened), row pitch 160 / 248 around group borders, group boxes computed from members and children (geometric nesting), automatic routing (tile-side, box-bottom→tile-top, elbows through the routing band, fanned attach points, request/return offsets, skip-over-the-top, hops on the lower-priority line), label placement clear of lines, tiles, borders and other labels, legend from the kinds used. Refuses a non-member that would land inside a group.
- **`scripts/render.py`** — spec → layout → build → check → PNG; replaces the output only when every gate passes; writes `<out>.receipt.json`; keeps `<out>.rejected.html` on failure.
- **`scripts/diff.py`** — architecture delta between two specs; `--annotate` renders added (green) / changed (amber) / removed (ghost) with a legend.
- **Viewer** in the template — offline, self-contained: focus, authored upstream/downstream reach, route, find, theme, deep links (`#focus=<id>&reach=…`, `#route=a~b`), a card with role, group, note and `sources`. Static meaning preserved without JS; toolbar and card sit outside the PNG capture.
- **`check.py`** — findings carry `target` and `fix`; `label-overlap` added; the one viewer script is allowed and must stay network-free.
- **References** — `spec.md`, `viewer.md`, `from-repo.md`; SKILL.md rewritten spec-first; commands `draw` (with `--repo`) and new `diff`.
- Examples re-authored as specs (`assets/examples/src/*.json`); `docs/` gains the delta and viewer screenshots; `scripts/test_layout.py` added to CI.

## 0.1.0 — 2026-11-05

First release: stack-diagram's icon/canvas pipeline + diagram-design's editorial rules, Korean-first (`build.py --kr-font auto`, `check.py` Korean gate), examples, commands, multi-host manifests.
