# Geometry — coordinates, spacing, and the connector rules

The canvas is a fixed-size, absolutely positioned coordinate system (default 1000 × 540; size it to the content). Nodes are `position:absolute` divs; edges live in one SVG overlay whose `viewBox` equals the canvas size. Everything is hand-placed, so the rules below — not an auto-layout — are what keep the result clean. `scripts/check.py` enforces the ones marked **[checked]**.

## The node box

```
left  = cx − width/2        width 132 (default) | 172 (.wide) | 212 (.xwide)
tile  = 60 × 60 at the top of the node, centered   → spans cx±30, top … top+60
name  = 13px / 600 display font, baseline ≈ top+81  (one line; two lines allowed)
role  = 9.5px mono, baseline ≈ top+96
box   = width × 100   (× 117 when the name wraps to two lines)
```

**A node is its tile plus the text beneath it.** All anchoring treats `(left … left+width, top … top+100)` as the connection boundary. Beside the tile (y < top+62) only the tile occupies space — that is where horizontal edges and their labels live.

Korean names: ~1em per syllable at 13px. A 132px node (124px usable) holds ~9 syllables, or ~5 syllables plus a short Latin word. Longer → `wide`. See `korean.md`.

## Groups are siblings; nesting is geometric

Every `.group` and `.node` is a **direct child of `.canvas`**, positioned in canvas coordinates. A nested group (VPC inside AWS Cloud, subnet inside VPC) is simply a second sibling drawn inside the first's rectangle — never a `<div>` inside the parent's `<div>`, which would make its coordinates relative and break every rule below. `check.py` fails on DOM nesting. Draw groups before edges and edges before nodes so the paint order is zones → lines → tiles.

## Spacing constants

| | |
|---|---|
| Same row | centers ≥ 140px apart (boxes are 132 wide — closer and they touch); 180 when both are `wide` |
| Rows | 140px between tile tops (≈ 40px clear between one row's box bottom and the next tile top); 160 when a row has two-line names |
| Group sides | 24px outside the outermost node **boxes**: `left = leftmost cx − 90`, `right = rightmost cx + 90` (`−110 / +110` for `wide` nodes). Measure from the box, not the tile, so padding is symmetric **[checked: ≥12]** |
| Group top / bottom | top = first tile top − 60 (the label lives in that band); bottom ≥ last tile top + 150 so the role line stays inside **[checked: ≥40 under the label, ≥8 at the bottom]** |
| Group label | inside the top-left corner (`top:12px; left:12px`), no background, so the border stays unbroken. Its corner — `12 + icon + text + 10` px wide, 32 tall — is a no-go zone for edges and labels **[checked]** |
| Nested group | ≥ 16px inset on sides and bottom, top ≥ 40px below the parent's top **[checked]** |
| Grid | `left`, `top`, group `left/top/width/height` on multiples of 4 **[warned]** |
| Canvas | 36–48px margin on every side; nothing may leave it **[checked]** |

## Edge anchoring — the rule that prevents text collisions

- **Horizontal edges** (same row): tile side to tile side at `y = top + 30`, from `x = cx₁ + 30 + 4` to `x = cx₂ − 30 − 6`. Safe because nothing sits beside a tile.
- **Vertical edges** (node above node): **box bottom to tile top** — from `y = top₁ + 100 + 6` down to `y = top₂ − 6` (reverse for upward). Never from the tile bottom (`top + 60`) through the name and role **[checked: edge-through-text]**.
- **Elbow edges** (different row *and* column): the vertical segment runs in an x-corridor free of node boxes; the horizontal segment runs in the clear band between rows (`top₂ − 48 … top₂ − 12`) or between a group's bottom and the next group's top. Crossing another *edge* is normal; crossing a *node box* is not **[checked: edge-through-node]**.
- Leave a 4–6px gap between the line end and the boundary; `marker-end` supplies the touch **[checked: 2–12px]**.
- **Two parallel edges between the same tiles** (request + return): offset them, e.g. `y = top + 26` and `y = top + 50`, and put the return on `.n.dash`.

Two layers of defense are built into the template — keep them:
1. Edge labels use `paint-order: stroke` with a paper-colored halo, so lines beneath stay legible.
2. Name / role text sits in `<span>`s with a translucent paper veil, so an unavoidable crossing fades behind the text instead of striking through it. This is a safety net, not a license.

## The six connector rules **[all checked]**

1. **Orthogonal only.** `H` / `V` segments and elbows. No `L` slants, no curves. Round an elbow only with a small arc if you want (`… H x−6 a6,6 0 0 1 6,6 V …`) — optional.
2. **Label clear of its line.** Horizontal: baseline `y = lineY − 8` (text bottom ≈ 6px above the stroke). Vertical: `x = lineX + 10`, `text-anchor="start"`, mid-segment. Never on the stroke, never on a tile, never in a group's label corner.
3. **No overlapping strokes.** Two edges never share a segment; parallel segments stay ≥ 12px apart. If they want to merge, the layout is wrong — move a node or split the diagram.
4. **Fan shared sides.** N edges on one side of a tile attach at distinct points ≥ 12px apart: `cx ± 12`, `cx ± 24` on top/bottom; `top + 18 / + 30 / + 42` on the sides.
5. **No transit through a non-endpoint tile.** Reroute. (A line may cross a *group* border — that is how a flow enters a VPC.)
6. **No line through any label text**, including the source's and destination's own name/role band (`top+62 … top+100`).

## Crossing edges — hop

When two orthogonal edges must cross, put a small hop on the **less important** one (dashed, neutral, return) at the crossing point and leave the primary flow uninterrupted:

```svg
<!-- horizontal line at y hopping a vertical at x=cx -->
<path class="n dash" d="M x1 y H cx-6 a6,6 0 0 1 12,0 H x2" marker-end="url(#ar)"/>
<!-- vertical line at x hopping a horizontal at y=cy -->
<path class="n" d="M x y1 V cy-6 a6,6 0 0 0 0,12 V y2" marker-end="url(#ar)"/>
```

Never hop both. If a diagram needs more than two hops, it is over budget.

## Edge classes and labels

```html
<path class="e" d="M148 150 H306" marker-end="url(#ar)"/>        accent solid — primary flow
<path class="n" d="M487 226 V344" marker-end="url(#ar)"/>        neutral solid — internal
<path class="n dash" d="M318 382 H208" marker-end="url(#ar)"/>   dashed — dev / deploy / async
<text class="el a" x="227" y="142" text-anchor="middle">HTTPS</text>
<text class="el step" x="227" y="142" text-anchor="middle">①</text>   reading-order marker
```

The arrowhead `#ar` fills with `context-stroke`, so it takes the line's color in both themes; `#open` is the open arrowhead AWS diagrams use (`path.aws`). `.el.a` for labels on accent edges, `.el` otherwise. Keep labels to 1–2 short words (≤ 16 columns, Hangul counts 2); the role line carries detail.

## Worked example (the template)

Canvas 1000 × 540. Row 1 tiles at `top:120`: 사용자 (cx 112), 앱 (cx 342), API (cx 487). Row 2 at `top:352`: 도구 하나 (cx 172), 도구 둘 (cx 354). Vendor group `left:252 top:60 w:324 h:212` (342−90 → 487+90; 120−60; bottom 272 ≥ 120+150). Tooling group `left:84 top:292 w:360 h:212`.

```
사용자→앱   M148 150 H306   tile-mid horizontal, label "HTTPS" at (227,142)
앱→API     M376 150 H451
도구둘→하나 M318 382 H208   dashed, row 2 tile-mid, label "pre-commit" at (263,374)
```

A vertical from API down to a node at cx 487 in row 2 is `M487 226 V346` (box bottom 220+6 → tile top 352−6).

## Sanity pass

List every vertical and elbow segment and ask: *which node boxes does this x-corridor pass through between y₁ and y₂?* The answer must be none. Then run `check.py` — it asks the same question with numbers.
