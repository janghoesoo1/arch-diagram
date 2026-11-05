---
name: arch-diagram
description: "Draw readable architecture diagrams — system / stack / infra / cloud / service-topology / 아키텍처 / 시스템 구성도 / 기술 스택 / 인프라 구성도 / 서비스 토폴로지 — as self-contained HTML (light + dark), PNG, a React/TSX component, or a live artifact. Real brand logos on tiles (svgl, devicon, official AWS / Google Cloud / Azure icon packages, Lucide pictograms for concepts), labeled group boxes (VPC, subnet, vendor, trust boundary), orthogonal arrows that never cross label text, a legend strip, and first-class Korean typography (Pretendard / Noto Sans KR embedded, Hangul width budgets, lang=ko). Use whenever the user asks for an architecture, system, stack, infra, deployment, or service diagram, a tech-stack overview, or wants logos arranged into a picture of how services connect — in any language, Korean especially, even without naming an output format."
license: MIT (see LICENSE); bundled fonts are SIL OFL 1.1
compatibility: Python 3.9+ and network access to fetch logos; PNG output needs Playwright with Chromium; offline-safe Korean needs fonttools + brotli
metadata:
  version: "0.1"
---

# arch-diagram

Architecture diagrams that are **readable first**: official logos on white tiles, labeled group boxes, orthogonal arrows routed around text, one accent color for the primary flow, a legend under the picture, and Korean labels that render in one known face everywhere. One self-contained HTML file is the source of truth; PNG, TSX, and artifacts derive from it.

This skill merges two lineages: the icon-and-geometry pipeline of `stack-diagram` (logo fetching, tile canvas, vendor drawing rules, PNG/TSX export) and the editorial discipline of `diagram-design` (deletion-first philosophy, complexity budget, mandatory connector rules, a11y contract, Korean font gate). Details live in `references/` and load only when needed.

## 0. Philosophy — readability is the deliverable

- **The best move is usually deletion.** Every node is a distinct idea; two that always travel together are one node. Every arrow carries information; if layout already says it, drop the line.
- **Target density 4/10.** Complete enough to be true, sparse enough to read without a guide. Default budget: **≤ 9 nodes, ≤ 12 edges, ≤ 4 groups, 1 focal tile, one accent-colored primary path.** Above that, draw an overview plus a detail diagram.
- **One signal color.** Accent (`.e`) marks *the* request/data path. Everything else is neutral. If you want to accent four things you have not decided what the diagram is about.
- **Text is sacred.** No line may pass through label text, no label may sit on its line, no two lines may share a stroke. `scripts/check.py` fails on each of these.
- **Korean is not a translation afterthought.** Hangul runs ~1em per syllable, so node widths, label lengths, and fonts are budgeted for it from the start (§6, `references/korean.md`).

## 1. Workflow

1. **Settle the content** — nodes, groups, edges; apply the budget (§2). State the plan in one short message before drawing unless the request already pins everything.
2. **Fetch icons** — `scripts/fetch_icons.py` (§3, `references/icons.md`).
3. **Plan coordinates** — `references/geometry.md`. Node = tile + text beneath it; edges connect node boundaries, never tile-to-tile through text.
4. **Build** — copy `assets/template.html`, replace GROUPS / EDGES / NODES / header, run `scripts/build.py` (§5). Korean labels → `--kr-font auto`.
5. **Check** — `python3 scripts/check.py out.html` must say `PASS` (§7).
6. **Render and look** — `scripts/render_png.py`; read the PNG with your own eyes (§7 checklist).
7. **Deliver** — HTML (default), PNG pair, TSX, or artifact (§8).

## 2. Content

From the user's description decide:

- **Nodes.** One technology or component each: a name (brand casing: `Next.js`, `GitHub Actions`; or a Korean role name: `결제 대행사`, `주문 서비스`) and a short role line (`http server`, `PostgreSQL 16`, `프론트엔드 · SSR`). Brand names stay Latin; the role line may be Korean.
- **Groups.** A box around things that share a runtime, vendor, repo, or trust boundary. One nesting level is fine; deeper is noise. Group labels use the brand's casing or a short Korean noun (`저장소`, `사내망`).
- **Edges**, three kinds, in the legend's words:
  - `.e` accent solid — the primary request/data flow. One continuous path reads best (사용자 → 앱 → API → …).
  - `.n` neutral solid — secondary / internal connections.
  - `.n.dash` neutral dashed — dev-time, deploy-time, async, return (CI, webhooks, cron).
- **Focal tile** (optional, `tile focal`): the single component the diagram is *about*.

Infer sensible groups and flows from what the tools are; ask only when a tool is ambiguous enough that the diagram would be wrong either way. Korean reading order is left→right, top→bottom; when order matters add `①②③` step labels (`.el.step`) on the primary path.

Budget check before drawing: if you are over 9 nodes, which can be merged (same vendor sub-products → one tile, name carries the distinction) or cut (dev tooling → its own diagram)?

## 3. Icons

```bash
python3 scripts/fetch_icons.py <icons-dir> nextjs vercel hono "betterauth:better-auth" "orpc=https://orpc.unnoq.com/logo.webp"
python3 scripts/fetch_icons.py <icons-dir> "aws:aws/AWS-Cloud-logo" "vpc:aws/vpc" "fargate:aws/fargate" "s3:aws/s3"
python3 scripts/fetch_icons.py <icons-dir> "gcp:google-cloud" "run:gcp/cloud-run" "sql:gcp/cloud-sql"
python3 scripts/fetch_icons.py <icons-dir> "azure:azure/Azure-A" "app:azure/app-service" "vnet:azure/vnet"
python3 scripts/fetch_icons.py <icons-dir> "user:lucide/user" "cron:lucide/clock" "pg:lucide/credit-card"
```

Spec forms: `name` · `name:slug` · `name=URL` · `name:aws/<Service>` · `name:gcp/<Product>` · `name:azure/<Service>` · `name:lucide/<icon>`. Chain: **svgl → devicon → gilbarbara/logos**; vendor packages are read live from AWS / Google / Microsoft; Lucide for concepts. The script writes `manifest.json`, saves `<name>_dark` when the brand ships a dark variant, and flags white-fill marks.

Rules that matter more than the mechanics (full text in `references/icons.md`):

- **Never recolor a logo.** White or very light mark → `tile dark`, not a fill change.
- **Official marks only.** No simple-icons monochrome redraws. On `FAIL`, find the brand's own file (repo root `logo*.svg`, `/public`, site `/logo.svg`, `/favicon.svg`) and pass `name=URL`.
- **Korean services (토스, 카카오, 네이버, 쿠팡, 배민…) are in no public source.** Pass the official asset from the brand's press / developer page as `name=URL`, or use a Lucide pictogram and let the name carry the brand. Never a hand-drawn imitation.
- **Concepts get pictograms, not text or emoji**: `user`, `browser`, `internet`, `server` from `assets/generic/`, anything else via `lucide/<icon>`.
- **Vendor sub-products** (Cloudflare D1/R2/KV, Vercel KV…) reuse the vendor logo; the name carries the distinction.
- **AWS / Google Cloud / Azure areas follow the vendor's own drawing rules** — bare tiles for AWS service icons, `group aws|gcp|azure` with `region | vpc | subnet | az | private | public | rg | vnet | zone`, full product names beside icons. The rules apply only inside that vendor's group.
- **Group-label icons render at 14px** and need a square glyph; use `lt`/`dk` pairs or `plate` so the mark survives the dark theme.

## 4. Layout — the short version

Read `references/geometry.md` before placing anything. The constants:

| Thing | Value |
|---|---|
| Node box | `132 × ~100` (tile 60, name 13px/600, role 9.5px mono); `wide` 172, `xwide` 212 |
| `left` | `cx − width/2`; put `left`/`top` on the 4px grid |
| Row pitch | 140px between tile tops (160 when a row has two-line names); same-row centers ≥ 140 apart |
| Group | sides 24px outside the outermost node *boxes*; top = first tile top − 60; bottom ≥ last tile top + 150; nested ≥ 16px inset and ≥ 40px below the parent's top |
| Horizontal edge | tile side to tile side at `y = top + 30`, 4–6px gap each end |
| Vertical edge | **box bottom (`top + 100`) to tile top (`top − 6`)** — never from the tile bottom through the text |
| Elbow | vertical in an x-corridor free of node boxes; horizontal in the clear band between rows |
| Shared side | fan attach points ≥ 12px apart (`cx ± 12`, `cx ± 24`) |
| Label | 1–2 short words; horizontal: `y = lineY − 8`, vertical: `x = lineX + 10`; never on a line, a tile, or a group's label corner |
| Crossing | hop the less important line: `… H cx−6 a6,6 0 0 1 12,0 H …` |

Six connector rules are non-negotiable and machine-checked: orthogonal only · label clear of its line · no overlapping strokes · fanned attach points · no transit through a non-endpoint tile · no line through any label text.

## 5. Build

```bash
python3 scripts/build.py draft.html <icons-dir> out.html              # Latin labels, or Korean via Google Fonts link
python3 scripts/build.py draft.html <icons-dir> out.html --kr-font auto   # Korean: embed a Pretendard subset (offline-safe)
```

Copy `assets/template.html`; its markup doubles as the format documentation. Replace `[TITLE]`, `[KICKER]`, `[LEDE]`, `[DESC]` (the canvas `aria-label`: what connects to what, one sentence), `[FOOT-LEFT]`, `[ICON-SOURCES]` (from `manifest.json`: `icons: svgl / devicon / Lucide`; AWS source reads `AWS Architecture Icons`, gcp `Google Cloud product icons`, azure `Azure Public Service Icons`). Keep the canvas `.canvas` size and the `svg.edges` viewBox in sync. Set `<html lang>` to the label language (`build.py` switches `en` → `ko` when it finds Hangul).

Icons are `%%ICON_<name>%%`; fonts `%%FONT_DISPLAY%%` / `%%FONT_JBM%%` resolve from `assets/fonts` automatically. The build fails loudly on unresolved tokens. Colors and fonts flow through the `:root` tokens; retune tokens (e.g. `--color-g1` hue per vendor), never scattered values.

The **dark variant** is free: `data-theme="dark"` on `<html>`. Tiles stay white so logos survive; group-label icons follow the `lt`/`dk` rule.

## 6. Korean labels

Full guidance in `references/korean.md`. The rules you must not skip:

- **Font stack is already in the template**: `Geist → Pretendard → Noto Sans KR → Apple SD Gothic Neo → Malgun Gothic`. Geist draws Latin; Korean faces draw only Hangul. The mono stack carries the same Korean tail so `결제 · webhook` renders predictably.
- **Embed when it must travel**: `build.py --kr-font auto` subsets Pretendard to the glyphs on the page (≈ 8 KB per weight) and inlines it. Without the flag the page links Noto Sans KR from Google Fonts — fine online, OS-dependent offline. `check.py` warns when neither is present.
- **Width budget: 1em per syllable.** At 13px a default node fits ~9 syllables on one line; names of 6+ syllables that share a line with Latin, or any full vendor product name, take `wide`. Role lines at 9.5px fit ~12 syllables. `check.py` estimates and fails on a third line.
- **Mixed script**: brand names stay Latin (`Next.js`, `Kafka`), roles and concepts go Korean (`프론트엔드 · SSR`, `결제 대행사`). Latin technical strings (ports, protocols, `webhook`) stay in mono; a Korean role line is prose and reads fine on the mono stack's Korean tail.
- **Edge labels**: Korean counts double toward the 16-column limit — `결제 요청` (8 cols) good, `결제 요청을 보낸다` too long.
- **`lang="ko"`** on `<html>`, legend and `aria-label` in Korean, title in Korean. `render_png.py` warns when the render host has no Korean font.
- Rendering on Linux CI needs `fonts-noto-cjk` unless the font is embedded — another reason to embed.

## 7. Verify before delivering

```bash
python3 scripts/check.py out.html            # PASS required; --strict makes warnings fatal
python3 scripts/render_png.py out.html out.png   # writes out.png (light) + out-dark.png, canvas + legend
```

`check.py` reads the markup and fails on: unresolved tokens or placeholders, remote assets, scripts, canvas/viewBox mismatch, missing `aria-label`, nodes outside the canvas or overlapping, names that need three lines, nodes sticking out of groups, groups overlapping without nesting, diagonal edges, unanchored endpoints, edges through tiles or **any** label text, overlapping strokes, shared attach points, labels on lines / tiles / group corners, legend gaps, and Hangul without a Korean face. It warns on budget overruns, off-grid positions, and crowding.

Then open the PNG and read it as the audience would:

- Does the primary flow read as one path, in reading order?
- Every icon visible in both themes (white-on-white → `tile dark`; dark group-label marks → `dk`/`plate`)?
- Korean names on one line, or a deliberate two? Nothing clipped? Nothing wrapped mid-word?
- Group labels in their corner, clear of nodes and edges; symmetric padding?
- Legend covers exactly the edge kinds used?
- Would the diagram still be understood with one node fewer? Then remove it.

Fix and re-run until check passes and the picture reads clean. The loop is cheap; a diagram with an arrow through a label is not.

## 8. Deliver

- **HTML** (default) — the built file; offline, self-contained (when `--kr-font` was used).
- **PNG** — always by screenshotting the built HTML (`render_png.py`, `--scale 2`), never by redrawing. Default captures canvas + legend in both themes; `--selector .canvas` for the diagram alone, `--full-page` for the whole page, `--single` for the document as authored.
- **TSX** — `references/tsx.md`: a dependency-free React component with the same geometry.
- **Artifact** — publish the built HTML with the environment's artifact tool when the user will iterate in conversation; pair with a PNG when they need something to paste.
- **SVG** is deliberately not a target: brand icons are embedded rasters/complex SVGs and the canvas is HTML; PNG is the portable picture.

Credit icon sources in the footer from `manifest.json`. Brand logos remain their owners' trademarks; keep AWS / Google / Microsoft icon packages and loose files out of repositories. Keep the `made with arch-diagram` link unless asked to remove it; a default PNG does not include the footer.

## 9. Anti-patterns (automatic rework)

| Anti-pattern | Why it fails |
|---|---|
| Accent on 3+ edges or 2+ focal tiles | Signal erased |
| Arrow from tile bottom through the name | Text becomes unreadable — connect box bottom → tile top |
| Diagonal connectors | Not an engineering drawing |
| Two edges on the same stroke, or 4px apart | Untraceable |
| Label sitting on its line | Line disappears under the halo |
| Legend inside the canvas | Collides with nodes |
| Emoji or text in a tile | Not an icon |
| Recolored / redrawn logo | Users notice instantly |
| Korean name on a 132px node at 8+ syllables with Latin | Wraps or overflows — use `wide` or shorten |
| Hangul with no Korean face reachable | OS fallback, different width per machine |
| Flat VPC with public and private services mixed | First thing cloud people notice |
| 12+ nodes in one canvas | It is two diagrams |

## 10. Files

- `assets/template.html` — the canvas; markup = format reference
- `assets/examples/order-service.html` — Korean e-commerce stack (built); `examples/src/` holds the draft
- `assets/generic/` — user / browser / internet / server / device pictograms
- `assets/fonts/` — Geist + JetBrains Mono (Latin subsets, OFL)
- `scripts/fetch_icons.py` · `build.py` · `check.py` · `render_png.py`
- `references/geometry.md` · `icons.md` · `korean.md` · `style.md` · `tsx.md` · `export.md` · `doctor.md`
