---
name: arch-diagram
description: "Draw readable architecture diagrams — system / stack / infra / cloud / service-topology / 아키텍처 / 시스템 구성도 / 기술 스택 / 인프라 구성도 / 서비스 토폴로지 — from a typed JSON spec, as self-contained interactive HTML (light + dark, focus / upstream-downstream / route deep links), PNG, SVG, animated GIF, a React/TSX component, or a live artifact. Real brand logos (svgl, devicon, AWS / Google Cloud / Azure icons, Lucide), labeled group boxes (VPC, subnet, vendor, trust boundary), deterministic auto-layout with orthogonal arrows that never cross text, a machine-checked readability gate, architecture delta between two versions, optional hand-drawn sketch style and flow animation (손그림 · 움직이는 다이어그램), and first-class Korean typography. Use whenever the user asks for an architecture, system, stack, infra, deployment, or service diagram, a tech-stack overview, a diagram of a codebase, a diff of two architectures, or an animated or sketch-style architecture picture — in any language, Korean especially, even without naming an output format."
license: MIT (see LICENSE); bundled fonts are SIL OFL 1.1
compatibility: Python 3.9+ and network access to fetch logos; PNG output needs Playwright with Chromium; offline-safe Korean needs fonttools + brotli
metadata:
  version: "0.3.0"
---

# arch-diagram

Architecture diagrams that are **readable first**: official logos on white tiles, labeled group boxes, orthogonal arrows routed around text, one accent color for the primary flow, a legend under the picture, and Korean labels that render in one known face everywhere. The source of truth is a small **JSON spec**; `scripts/render.py` lays it out deterministically, builds, checks, and only then delivers the HTML (plus PNG / TSX / artifact on request).

Three lineages: the icon-and-canvas pipeline of `stack-diagram`, the editorial discipline of `diagram-design` (deletion first, complexity budget, six connector rules, a11y, Korean font gate), and the delivery model of `archify` (typed source → validated artifact with machine-readable findings, an explorable viewer, delta between versions, repository evidence). Details live in `references/` and load only when needed.

## 0. Philosophy — readability is the deliverable

Default to professional, static HTML without asking users to choose presentation options.
For natural-language style, motion or export requests, follow the selection rules in
`references/presentation.md`: generic sketch means hybrid, generic animation means flow,
and an explicit GIF request adds animation when drawing. A "data flow diagram" alone
stays static. Combine independent preferences, retain unchanged choices on revisions,
and ask only to resolve genuine conflicts or missing source material. Keep advanced
flags and update instructions out of normal replies. All styles preserve geometry,
logos and readability; TSX remains static. Optional exports retain their dependency checks.

- **The best move is usually deletion.** Every node is a distinct idea; two that always travel together are one node. Every arrow carries information; if layout already says it, drop the line.
- **Target density 4/10.** Default budget: **≤ 9 nodes, ≤ 12 edges, ≤ 4 groups, 1 focal tile, one accent-colored primary path.** Above that, an overview plus a detail diagram.
- **One signal color.** `primary` edges mark *the* request/data path. Everything else is neutral.
- **Text is sacred.** No line through label text, no label on its line, no two lines on one stroke. `check.py` fails on each.
- **Korean is not an afterthought.** Hangul runs ~1em per syllable; widths, label lengths and fonts are budgeted for it (§6, `references/korean.md`).
- **Nothing is hand-placed, nothing is unverified.** The spec says *what*; the layout says *where*; the check says *whether*; the receipt says *that it did*.

## 1. Workflow

Script and reference paths below are relative to this SKILL.md's directory; from a diagram folder run them as `python3 <skill>/scripts/…`.

1. **Settle the content** — nodes, groups, edges, the one primary path; apply the budget (§2). State the plan in one short message before drawing unless the request already pins everything. For a real codebase read `references/from-repo.md` and collect `sources` while reading.
2. **Fetch icons** — `scripts/fetch_icons.py` (§3, `references/icons.md`).
3. **Write the spec** — `<slug>.json` per `references/spec.md`: nodes on a row/column grid, groups by membership, edges by endpoint. Main-path neighbours adjacent in one row; a store directly below its owner; group members in contiguous cells.
4. **Render** — `python3 scripts/render.py <slug>.json <slug>.html --icons <icons-dir> --kr-font auto --png`. It runs spec → layout → build → check → PNG and replaces the output only when every gate passes (§5).
   Append only the presentation/export flags selected from the user's intent per `references/presentation.md`; do not show a configuration questionnaire.
   Drop `--kr-font auto` only if fonttools is missing and `--png` only if Playwright is missing; say so, print the install command, and note the PNG was not verified. A `--png` run without Playwright exits non-zero and delivers nothing.
5. **Repair from the receipt** — a failing gate prints each finding with its `fix`; edit the spec (never the HTML) and re-run. Two repairs that do not converge mean the content is over budget: split it.
6. **Look at the PNG** with the §7 checklist before delivering.
7. **Deliver** — HTML (default, with the viewer), the PNG pair, TSX, or an artifact (§8). For a revision, edit the spec and re-render; for "what changed", `scripts/diff.py` (§9).

Work in a folder per diagram (`<slug>.json`, `icons/`, `<slug>.html`, `<slug>.receipt.json`, PNGs) so repairs and revisions reuse the icons.

## 2. Content

- **Nodes.** One technology or component each: `name` in brand casing (`Next.js`, `GitHub Actions`) or a Korean role name (`결제 대행사`), a short `role` (`http server`, `PostgreSQL 16`, `프론트엔드 · SSR`), an `icon`, a `row`/`col`.
- **Groups.** A box around what shares a runtime, vendor, repo, or trust boundary; nest with `parent` (cloud → VPC → subnet is the sanctioned depth). Labels in brand casing or a 2–4 syllable Korean noun (`저장소`, `사내망`).
- **Edges**, three kinds: `primary` (accent, one continuous path), `internal` (neutral), `async` (dashed: deploy, webhook, cron, return). Labels 1–2 words.
- **Focal** (optional): the single component the diagram is about.
- **Reading order** is left→right, top→bottom; add `①②③` to labels when sequence matters.

Infer groups and flows from what the tools are; ask only when the diagram would be wrong either way. Over 9 nodes? Merge vendor sub-products into one tile, move dev tooling to its own diagram.

## 3. Icons

```bash
python3 scripts/fetch_icons.py <icons-dir> nextjs vercel hono "betterauth:better-auth" "orpc=https://orpc.unnoq.com/logo.webp"
python3 scripts/fetch_icons.py <icons-dir> "aws:aws/AWS-Cloud-logo" "vpc:aws/vpc" "fargate:aws/fargate" "s3:aws/s3"
python3 scripts/fetch_icons.py <icons-dir> "gcp:google-cloud" "run:gcp/cloud-run" "azure:azure/Azure-A" "app:azure/app-service"
python3 scripts/fetch_icons.py <icons-dir> "user:lucide/user" "cron:lucide/clock" "pg:lucide/credit-card"
```

Chain: **svgl → devicon → gilbarbara/logos**; vendor packages read live; Lucide for concepts; `assets/generic/` for user / browser / internet / server. `manifest.json` records sources; `<name>_dark` variants become the dark-theme pair automatically. Rules (full text in `references/icons.md`): never recolor; official marks only (`name=URL` on a miss); **Korean brands (토스·카카오·네이버…) are in no public source** → official asset URL or a Lucide pictogram, never an imitation; concepts get pictograms not text; AWS / GCP / Azure areas follow the vendor's drawing rules (`tile: "bare"`, `kind: "aws vpc"` …); group-label icons need a square mark.

## 4. Layout — what the spec decides, what the engine does

You decide **rows, columns, membership, kinds**. `layout.py` does the rest per `references/geometry.md`: column widths from the widest name (Korean auto-widened to `wide`/`xwide`), 160px row pitch (248 when a group border lies between rows), group boxes padded around members and children, tile-side / box-bottom→tile-top / elbow routing, attach points fanned ≥ 12px, request/return pairs offset, the lower-priority line hopping a crossing, labels slid to a clear spot, legend from the kinds used.

Placement that keeps lines straight: main-path neighbours in adjacent columns; a store or cache in the cell directly below its reader; a return or deploy source on the side of the main path that has no stores; external actors outside every group. The engine refuses a non-member that would land inside a group's box — move it to another column.

## 5. Render and deliver

```bash
python3 scripts/render.py spec.json out.html --icons icons/ --kr-font auto --png     # gates: spec → layout → build → check → png
python3 scripts/layout.py spec.json draft.html --icons icons/                         # draft only (hand-tuning escape hatch)
python3 scripts/check.py out.html --json                                              # the gate alone: findings with target + fix
```

A passing run writes `out.html` and `out.receipt.json` (gates, findings, sha256, PNG paths). A failing run leaves the previous `out.html` untouched, keeps `out.rejected.html`, prints findings with fixes, exits non-zero. `--strict` makes warnings fatal; `--faithful` raises the node cap to 20 for a deliberately dense import. Korean: `--kr-font auto` embeds a Pretendard subset (≈ 8 KB per weight) so the file renders identically offline, in CI and in an artifact sandbox; without it the page links Noto Sans KR.

The output already contains the **viewer** (`references/viewer.md`): click a node to focus, `U`/`D` for authored upstream/downstream reach, `R` for a route, `/` find, `T` theme, deep links `#focus=<id>&reach=downstream`, `#route=<a>~<b>`. It is offline and self-contained; print, PNG and no-JS hosts see the plain diagram. Each node's `sources` and `note` appear in its card.

## 6. Korean labels

Full guidance in `references/korean.md`. Non-skippable:

- The template's stack is `Geist → Pretendard → Noto Sans KR → Apple SD Gothic Neo → Malgun Gothic`, on the mono stack too, so `결제 · webhook` renders predictably.
- `--kr-font auto` when the file must travel; `check.py` warns when no Korean face is embedded or linked.
- 1em per syllable: `layout.py` widens nodes automatically; names needing a third line fail.
- Brand names Latin, roles and concepts Korean, no particles or verbs in labels, `·` between scripts; edge labels ≤ 16 columns (Hangul = 2).
- `lang` is `ko` whenever Hangul is present (automatic); legend, lede, `description` in Korean.

## 7. Verify before delivering

The gates prove the markup; your eyes prove the picture. Open the PNG and read it as the audience would:

- Does the primary flow read as one path, in reading order?
- Every icon visible in both themes (white-on-white → `tile: "dark"`; dark group-label marks → `_dark` pair)?
- Korean names on one line (or a deliberate two)? Nothing clipped or wrapped mid-word?
- Group labels clear of nodes and lines; padding symmetric?
- Legend covers exactly the kinds used?
- Would the diagram still be understood with one node fewer? Then remove it.

Then confirm in the browser once that focus/reach behave if the user will explore it.

## 8. Deliver

- **HTML** (default) — self-contained, interactive, offline.
- **PNG** — `--png` or `render_png.py` (both themes, canvas + legend, 2×); never redrawn with another tool.
- **TSX** — `references/tsx.md`, a dependency-free component with the same geometry.
- **Artifact** — publish the HTML with the environment's artifact tool (build with `--kr-font auto` first when Korean).
- **SVG / GIF** — on explicit request, follow `references/presentation.md`; SVG is a static browser-oriented foreignObject snapshot, GIF captures animation. Never infer GIF from animation alone.

Credit icon sources in the footer; keep vendor icon packages out of repositories. Reply briefly: a link to the HTML, one or two sentences of takeaway for a codebase, any deliberate omission or assumption.

## 9. Delta and revisions

```bash
python3 scripts/diff.py base.json head.json                       # added / removed / changed nodes, groups, edges
python3 scripts/diff.py base.json head.json --annotate head.delta.json && python3 scripts/render.py head.delta.json delta.html --icons icons/ --kr-font auto
```

The annotated spec renders with green (added), amber (changed) and ghosted dashed (removed) markers and a legend for them — the picture of a proposal against the current state. Keep node ids stable across versions; that is what makes diffs and deep links meaningful.

## 10. Anti-patterns (automatic rework)

| Anti-pattern | Why it fails |
|---|---|
| Hand-editing the built HTML instead of the spec | the next render discards it; the diff is blind to it |
| Accent on 3+ edges or 2+ focal tiles | signal erased |
| A store in another column than its reader | one straight line becomes an elbow across a group |
| Non-member node between a group's members | the engine refuses; the picture would lie |
| Emoji or text in a tile; recolored / redrawn logo | not an icon; users notice |
| Korean name wrapped mid-word or in an OS fallback face | width budget / font embedding skipped |
| 12+ nodes in one canvas | it is two diagrams |
| Claiming "verified" without opening the PNG | the gate checks markup, not taste |

## 11. Files

- `assets/template.html` — canvas, tokens, viewer; markup = format reference for hand-placed drafts
- `assets/motion.js` · `motion.css` · `export-scene.js` — optional animation and SVG/GIF capture
- `assets/examples/src/*.json` — specs: Korean order service, AWS commerce, RAG chatbot; `assets/examples/*.html` built (AWS commerce is spec only)
- `scripts/fetch_icons.py` · `layout.py` · `build.py` · `check.py` · `render.py` · `render_png.py` · `diff.py` · `presentation.py` · `export_media.py`
- `references/spec.md` · `geometry.md` · `icons.md` · `korean.md` · `viewer.md` · `from-repo.md` · `style.md` · `tsx.md` · `export.md` · `presentation.md` · `doctor.md`
