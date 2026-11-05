---
description: Run the arch-diagram readability gate on a diagram HTML file
argument-hint: "<diagram.html> [--strict] [--faithful] [--json]"
allowed-tools:
  - Read
  - Bash
  - Glob
---

Run `python3 <skill>/scripts/check.py $ARGUMENTS` where `<skill>` is the directory of the loaded `skills/arch-diagram/SKILL.md`, and relay the findings.

## Required behaviour

1. **No file** → ask which `.html` to check. (A spec `.json` → run `render.py` instead; its receipt carries the same findings.)
2. Print the checker's output as-is; `--json` adds `target` and `fix` per finding — relay the fix for each `FAIL` (the rules are in `references/geometry.md` and `references/korean.md`). When the diagram came from a spec, the fix is an edit to the spec, not to the HTML.
3. Offer to apply the fixes and re-run; do not edit the file without the user's go-ahead.
4. Read-only otherwise: no installs, no rebuilds.
