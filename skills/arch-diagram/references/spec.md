# Spec — the typed JSON source of a diagram

A diagram is authored as one JSON file; `scripts/layout.py` turns it into the canvas HTML deterministically (same spec → same bytes), `scripts/render.py` runs the whole pipeline and delivers atomically. Edit the JSON to revise a diagram: a change to one node moves only what depends on it, so unrelated structure stays put between revisions.

```json
{
  "title": "주문 서비스 아키텍처",
  "kicker": "arch-diagram · 예제",
  "lede": "한두 문장. 생략 가능.",
  "description": "aria-label: 무엇이 무엇과 연결되는지 한 문장.",
  "footer": "작성자 · 한 줄",
  "icon_sources": "icons: svgl / devicon / Lucide",
  "lang": "ko",
  "theme": { "g1": "graphite" },
  "groups": [
    { "id": "vercel", "label": "Vercel", "kind": "ga", "icon": "vercel" },
    { "id": "store",  "label": "저장소", "kind": "gc", "icon": "database" }
  ],
  "nodes": [
    { "id": "user", "name": "사용자",   "role": "browser",         "icon": "user",   "row": 0, "col": 0 },
    { "id": "next", "name": "Next.js",  "role": "프론트엔드 · SSR", "icon": "nextjs", "row": 0, "col": 1, "group": "vercel" },
    { "id": "hono", "name": "Hono API", "role": "백엔드 · RPC",    "icon": "hono",   "row": 0, "col": 2, "group": "vercel", "focal": true },
    { "id": "neon", "name": "Neon",     "role": "PostgreSQL 16",   "icon": "neon",   "row": 1, "col": 2, "group": "store",
      "sources": ["docker-compose.yml:12-20", "src/db.ts:1-9"] }
  ],
  "edges": [
    { "from": "user", "to": "next", "kind": "primary",  "label": "HTTPS" },
    { "from": "next", "to": "hono", "kind": "primary",  "label": "RPC" },
    { "from": "hono", "to": "neon", "kind": "internal", "label": "SQL" }
  ],
  "legend": { "async": "비동기 · 배포" }
}
```

## Page fields

| Field | Required | Meaning |
|---|---|---|
| `title` | yes | `<title>` and `h1` |
| `description` | yes | the canvas `aria-label`: what connects to what, one sentence (it is also the PNG's alt text) |
| `kicker`, `lede`, `footer` | no | header eyebrow, one-two sentence lede (omitted when empty), footer left text |
| `icon_sources` | no | footer credit from `manifest.json` (`icons: svgl / devicon / Lucide`; AWS → `AWS Architecture Icons`) |
| `lang` | no | `ko` / `en` / `ja`; default `ko` when any Hangul is present, else `en` |
| `theme.g1` | no | hue of the warm vendor palette: `warm` (default), `graphite` (Vercel, GitHub), `green`, `blue`, `purple` |
| `legend` | no | overrides for legend words: `primary`, `internal`, `async`, `added`, `changed`, `removed` |

## Nodes

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | stable identifier (`[a-z0-9_-]`), used by edges, groups, deep links (`#focus=<id>`) and diffs |
| `name` | yes | brand casing (`Next.js`) or a Korean role name (`결제 대행사`) |
| `role` | no | short mono line: `http server`, `PostgreSQL 16`, `프론트엔드 · SSR` |
| `icon` | yes | icon name as fetched (`%%ICON_<icon>%%`); a `<icon>_dark` file in the icons dir becomes the dark-theme pair automatically |
| `row`, `col` | yes | grid cell (0-based). One node per cell. Columns are as wide as their widest node |
| `group` | no | id of the group this node belongs to (innermost only) |
| `width` | no | `auto` (default: fits the name on one line → 132 / 172 / 212), or `default` / `wide` / `xwide` |
| `tile` | no | `dark` (white logo), `bare` (AWS service icon), `bare res` (AWS general icon), `wide` (wide logo) |
| `focal` | no | `true` on at most one node — the component the diagram is about |
| `sources` | no | repository evidence, up to three `path:line` or `path:start-end` strings; shown in the viewer card (`from-repo.md`) |
| `note` | no | one short sentence shown in the viewer card |
| `delta` | no | `added` / `changed` / `removed` — set by `diff.py --annotate`, not by hand |

Placement rules the layout cannot fix for you: put the main path's neighbours in adjacent columns of one row in reading order; put a store or branch directly below (or above) the node that owns it so its edge is one straight line; keep every group's members in contiguous cells (a non-member that lands inside a group's box is a spec error).

## Groups

| Field | Required | Meaning |
|---|---|---|
| `id`, `label` | yes | id for nesting/diffs; label in brand casing or a 2–4 syllable Korean noun |
| `kind` | no | `ga` (warm vendor, default) · `gb` (accent family: repo, tooling) · `gc` (neutral) · `boundary` (dashed trust boundary) · `aws`, `aws vpc`, `aws public`, `aws private`, `aws region`, `aws az` · `gcp`, `gcp vpc`, `gcp region`, `gcp subnet`, `gcp zone` · `azure`, `azure rg`, `azure region`, `azure vnet`, `azure subnet`, `azure zone` |
| `icon` | no | 14px label icon (30px for `aws`); needs a square mark; `lt`/`dk` pairs apply |
| `parent` | no | id of the enclosing group (VPC inside AWS Cloud, subnet inside VPC). Rendered as geometric nesting, parents padded around children |

Members are the nodes whose `group` is this id, plus child groups. A group's box is computed, never authored.

## Edges

| Field | Required | Meaning |
|---|---|---|
| `from`, `to` | yes | node ids; direction is the arrow |
| `kind` | no | `primary` (accent, the one request path) · `internal` (default, neutral solid) · `async` (neutral dashed: deploy, webhook, cron, return) |
| `label` | no | 1–2 short words; ≤ 16 columns, Hangul counts 2 |
| `delta` | no | set by `diff.py` |

Routing is automatic: same row → tile side to tile side (a request/return pair is offset); same column → box bottom to tile top; otherwise an elbow through the band between the rows with attach points fanned ≥ 12px apart; an edge that would pass over a node in its own row goes over the top; where lines cross, the lower-priority one (async < internal < primary) hops. Edges with both ends inside an AWS group draw in AWS's ink style with the open arrowhead and stay out of the legend.

## Commands

Style and motion are presentation CLI options, not new canonical spec fields. See
`presentation.md` for `--style`, `--animate`, `--animation-mode`, `--svg`, `--gif`,
`--gif-fps`, `--gif-width`, and `--gif-duration`. Existing node `note` values are also
shown during steps. Every style reuses the same layout and relationships.

```bash
python3 scripts/render.py spec.json out.html --icons icons/ --kr-font auto --png   # the whole pipeline, atomic
python3 scripts/layout.py spec.json draft.html --icons icons/                       # just the draft
python3 scripts/diff.py base.json head.json --annotate head.delta.json              # architecture delta
```

`render.py` writes `out.receipt.json` with every gate's result, check findings (each with `target` and `fix`), the output hash and PNG paths. On a failing gate it leaves any previous `out.html` untouched, keeps the candidate as `out.rejected.html`, and exits non-zero — repair the spec and re-run.

## Hand-placed escape hatch

`assets/template.html` can still be filled by hand (the markup is the format reference) when a layout needs something the grid cannot express. `check.py` applies the same rules; the viewer works as long as nodes carry `data-id` and edges `data-from`/`data-to`.
