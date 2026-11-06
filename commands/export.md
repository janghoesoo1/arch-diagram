---
description: Export an arch-diagram HTML file to PNG, SVG, animated GIF or a React/TSX component
argument-hint: "<diagram.html> [PNG / SVG / GIF로 저장]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

Export the diagram at `$1` following [`skills/arch-diagram/references/export.md`](../skills/arch-diagram/references/export.md) (PNG) and [`references/tsx.md`](../skills/arch-diagram/references/tsx.md) (TSX). Treat those references as the source of truth.

Full argument string: `$ARGUMENTS`

## Defaults

- `--png`: `scripts/render_png.py <file> <base>.png --scale 2` → `<base>.png` + `<base>-dark.png`, canvas + legend (`--figure`).
- `--tsx`: `<Name>Diagram.tsx` next to the source.
- No format requested in words or flags → `--png`. Natural-language format requests
  follow `references/presentation.md`; existing advanced flags remain supported.
- `--svg` or `--gif`: follow `references/presentation.md` and run `export_media.py`
  with `--format svg|gif`; map `--gif-fps/width/duration` to `--fps/width/duration`.
  GIF requires an animated HTML source; for static input follow the source-rebuild rules
  in `references/presentation.md`, not a silent format substitution. SVG contains HTML foreignObject and is intended
  for browsers, not universal vector editors. Missing optional dependencies are reported,
  not automatically installed.

## Required behaviour

1. **No file** → ask which `.html` to export. Don't guess.
2. The file must contain `<div class="canvas">`; otherwise refuse and say it is not an arch-diagram file.
3. Run `scripts/check.py` first; export only a `PASS` file (warnings are allowed, failures are not — say what failed).
4. PNG requested but Playwright missing → print `pip install playwright && python3 -m playwright install --with-deps chromium` verbatim and stop. Do **not** auto-install.
5. `--scale` outside {1,2,3} → reject.
6. Korean labels and no embedded Korean face → warn that the render host's font will be used and offer to rebuild with `--kr-font auto`.
7. Report paths and sizes.
