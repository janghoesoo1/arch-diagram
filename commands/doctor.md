---
description: One-shot environment diagnostics for arch-diagram (Python, icon sources, Korean font embedding, Playwright)
argument-hint: "[--strict] [--json]"
allowed-tools:
  - Read
  - Bash
  - Glob
---

Run environment diagnostics by following [`skills/arch-diagram/references/doctor.md`](../skills/arch-diagram/references/doctor.md). Treat that reference as the source of truth and do not reimplement its logic here.

Full argument string: `$ARGUMENTS`

## Required behaviour

1. Run the checks in the reference's order; capture stderr on failures and keep going.
2. Read-only: no installs, no file edits, no git operations.
3. Print the summary line, one line per check, and `Next actions` only when something is warn/fail.
4. `--json` appends the structured block from the reference.
5. Report only what this run verified.
