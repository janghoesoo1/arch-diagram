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

1. **No file** → ask which `.html` to check.
2. Print the checker's output as-is; then, for each `FAIL`, say in one line what to change (the rule is in `references/geometry.md` or `references/korean.md`).
3. Offer to apply the fixes and re-run; do not edit the file without the user's go-ahead.
4. Read-only otherwise: no installs, no rebuilds.
