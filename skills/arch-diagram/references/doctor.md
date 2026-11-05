# Environment doctor

Load this when the user asks for diagnostics, a health check, or first-run troubleshooting, or invokes `/arch-diagram:doctor`.

One read-only report on whether this machine can run the full pipeline. Resolve the installation from this loaded reference (the directory containing `SKILL.md`), never from the user's current working directory. Do not install anything; print copy-pastable fixes.

Flags: `--strict` (warnings count as failures), `--json` (append a machine-readable block).

## Checks, in order

1. **Python** — `python3` then `python`; need ≥ 3.9. `fail` if absent or older.
2. **Skill files** — `SKILL.md`, `assets/template.html` (carrying `data-arch-diagram-viewer`), `assets/fonts/Geist.woff2`, `assets/fonts/JetBrainsMono.woff2`, `scripts/fetch_icons.py`, `scripts/layout.py`, `scripts/build.py`, `scripts/check.py`, `scripts/render.py`, `scripts/render_png.py`, `scripts/diff.py` present under the resolved root. Then run the shipped spec through the pipeline offline as a smoke test: `python3 scripts/render.py assets/examples/src/order-service.json <tmp>/smoke.html --icons <tmp>/icons --kr-font none` with one stand-in SVG per icon name copied from `assets/generic/server.svg` — a `PASS` on every gate proves layout, build and check work on this machine. Missing → `fail` with "reinstall or update arch-diagram".
3. **Icon sources reachable** — one HEAD/GET each to `https://api.svgl.app?search=hono`, `https://raw.githubusercontent.com/devicons/devicon/master/icons/hono/hono-original.svg`, `https://cdn.jsdelivr.net/`. Unreachable → `warn` ("logos cannot be fetched; pass name=URL or work from a cached icons dir"). Skip the AWS / GCP / Azure packages (large); mention they are fetched on demand.
4. **Korean font embedding** — `import fontTools` and `import brotli` in the active interpreter. Missing → `warn`: `pip install fonttools brotli` (needed only for `--kr-font auto`; otherwise Noto Sans KR is linked from Google Fonts).
5. **Pretendard cache** — `~/.cache/arch-diagram/fonts/Pretendard-Regular.woff2` and `-SemiBold.woff2` (or `$ARCH_DIAGRAM_FONT_DIR`). Absent → `info` ("downloaded on first `--kr-font auto`").
6. **Playwright** — `import playwright` and a Chromium build in its cache (`~/Library/Caches/ms-playwright` on macOS, `~/.cache/ms-playwright` on Linux, `%LOCALAPPDATA%\ms-playwright` on Windows). Missing → `warn`: `pip install playwright && python3 -m playwright install --with-deps chromium`.
7. **Korean / Japanese render fonts** — `fc-list :lang=ko` and `:lang=ja` where `fc-list` exists; on macOS assume Apple SD Gothic Neo / Hiragino. None → `warn`: `sudo apt-get install fonts-noto-cjk` (Linux), or build with `--kr-font auto` so no host font is needed.
8. **Path hygiene** — paths with spaces that would need quoting in the printed commands → `warn`.

## Output contract

```
Doctor summary: <PASS|WARN|FAIL> (<n> pass, <n> warn, <n> fail)
[PASS] Python 3.12.4 at /usr/bin/python3
[PASS] skill files present at ~/.claude/plugins/…/skills/arch-diagram
[WARN] fontTools not importable — Korean embedding unavailable (Google Fonts link will be used)
…

Next actions
- pip install fonttools brotli
- pip install playwright && python3 -m playwright install --with-deps chromium
```

Only `Next actions` when something is warn/fail. With `--json`: `{"status", "counts": {"pass","warn","fail"}, "checks": [{"name","status","message","fix"?}], "timestamp"}`.

## Safety

Read-only. If a check command fails unexpectedly, capture stderr, mark the check, continue. Never claim a check passed unless it was verified in this run.
