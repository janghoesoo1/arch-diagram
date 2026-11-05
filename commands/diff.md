---
description: Compare two arch-diagram specs and render the architecture delta (added / changed / removed)
argument-hint: "<base.json> <head.json> [--render] [--png]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

Compare the specs at `$1` and `$2` with `python3 <skill>/scripts/diff.py`, where `<skill>` is the directory of the loaded `skills/arch-diagram/SKILL.md`, following §9 of the skill and `references/spec.md`.

Full argument string: `$ARGUMENTS`

## Required behaviour

1. **Fewer than two files** → ask which two specs to compare (a current and a proposed state; or two git revisions of one spec — check out the base into a temp file).
2. Run `diff.py base head` and relay the human summary: nodes / groups / edges added, removed, changed (with the fields that changed). Match is by `id` and by `(from, to)` for edges — say so if ids look renamed rather than changed.
3. With `--render`: `diff.py base head --annotate head.delta.json`, then `render.py head.delta.json <slug>.delta.html --icons icons/ --kr-font auto [--png]` using the head's icons dir (fetch the removed nodes' icons too if missing). Report nodes the diff could not draw (`unplaced`).
4. Deliver the delta HTML/PNG with one or two sentences on what the change means for the reader (new boundary crossed, store moved, path shortened). Do not restate every item.
5. Read-only on the inputs; never modify base or head.
