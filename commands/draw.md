---
description: Draw a readable architecture diagram (real logos, Korean-ready) from a one-line description of the stack
argument-hint: "<describe the stack / 스택 설명> [--png] [--tsx] [--dark-only] [--artifact]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
---

Draw an architecture diagram for `$ARGUMENTS` by following the `arch-diagram` skill (`skills/arch-diagram/SKILL.md`) end to end. Treat the skill and its references as the source of truth — do not reimplement the rules here.

## Required behaviour

1. **No description** → ask what the stack is (technologies, how they connect, where they run). Don't guess a system.
2. **Settle content first** and state the plan in one short message (nodes, groups, primary flow, what the 9-node budget pushes out) unless the request already pins everything.
3. Fetch icons with `scripts/fetch_icons.py`; on a `FAIL`, look for the official file (`name=URL`) or a Lucide pictogram per `references/icons.md`. Korean brands (토스, 카카오, 네이버…) are never in the public sources — do not fabricate a mark.
4. Lay out per `references/geometry.md`, build with `scripts/build.py`; when any label is Korean add `--kr-font auto` (fall back to the Google Fonts link if `fonttools` is missing, and say so).
5. `python3 scripts/check.py out.html` must report `PASS` before anything is delivered. Fix findings; do not suppress them.
6. Render with `scripts/render_png.py` and **look at the PNG** (both themes) using the §7 checklist. If Playwright is missing, print the install command, deliver the HTML, and say the PNG was not verified.
7. Deliver the HTML (default). `--png` also delivers the light/dark PNG pair; `--tsx` adds a component per `references/tsx.md`; `--artifact` publishes the HTML with the environment's artifact tool; `--dark-only` sets `data-theme="dark"` as authored and renders with `--single`.
8. Report file paths, the icon sources used, and any assumption made about the system.
