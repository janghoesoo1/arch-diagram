---
description: Draw a readable architecture diagram (real logos, Korean-ready, interactive) from a one-line description or a codebase
argument-hint: "<describe the stack / 스택 설명 | --repo <path>> [--style professional|hybrid-sketch|full-sketch] [--animate] [--animation-mode draw|flow|steps|combined] [--gif] [--svg] [--png] [--tsx] [--artifact] [--dark-only]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

Draw an architecture diagram for `$ARGUMENTS` by following the `arch-diagram` skill (`skills/arch-diagram/SKILL.md`) end to end. The skill and its references are the source of truth — do not reimplement the rules here.

## Required behaviour

1. **No description and no `--repo`** → ask what the stack is. Don't guess a system. With `--repo <path>`, follow `references/from-repo.md`: read manifests and deployment config, trace the requested path, record `sources` per node, and name the revision in the kicker.
2. **Settle content first** and state the plan in one short message (nodes, groups, primary path, what the 9-node budget pushes out) unless the request already pins everything.
3. Work in a folder per diagram: fetch icons with `scripts/fetch_icons.py` into `icons/`; on a `FAIL`, find the official file (`name=URL`) or use a Lucide pictogram per `references/icons.md`. Korean brands are never in the public sources — do not fabricate a mark.
4. Write `<slug>.json` per `references/spec.md` (rows/columns, groups by membership, edges by endpoint). Never hand-place coordinates and never edit the built HTML.
5. Run `python3 scripts/render.py <slug>.json <slug>.html --icons icons/ --kr-font auto --png` (drop `--kr-font auto` only if fonttools is missing, and say so; drop `--png` only if Playwright is missing, print the install command, and say the PNG was not verified). A non-zero exit is never success: read the findings and their `fix`, repair the **spec**, re-run. Two non-converging repairs mean the content is over budget — split it and say so.
6. **Look at the PNG** (both themes) with the skill's §7 checklist before delivering.
7. Deliver the HTML (default, interactive). `--png` also hands over the light/dark pair; `--tsx` adds a component per `references/tsx.md`; `--artifact` publishes the HTML with the environment's artifact tool; `--dark-only` renders with `data-theme="dark"` as authored.
8. Reply briefly: a link to the HTML, the icon sources used, any assumption or omission, and the deep-link hint (`#focus=<id>`) when the user will explore it. Keep the receipt path for troubleshooting only.

For optional styles, motion, SVG or GIF, follow `references/presentation.md`. Forward
`--style`, `--animate`, `--animation-mode`, `--svg`, `--gif`, `--gif-fps`, `--gif-width`
and `--gif-duration` to render.py. Defaults remain professional and static. Never infer
GIF from animation alone; `--gif` requires `--animate`. `--help` shows the renderer options.
