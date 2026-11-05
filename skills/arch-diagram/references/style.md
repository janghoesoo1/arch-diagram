# Style — tokens, accent discipline, themes

Every color and font flows through the `:root` tokens in `assets/template.html`. Retune tokens; never scatter literal values through the markup.

## Tokens

| Token | Role |
|---|---|
| `--color-paper`, `--color-paper-2` | page / canvas background, region fill |
| `--color-rule`, `--color-rule-2` | graph-paper grid, hairline borders |
| `--color-ink`, `--color-ink-2` | primary text, boundary strokes |
| `--color-neutral`, `--color-muted` | neutral edges, role text, legend |
| `--color-accent` | **the** signal color: primary flow edges, focal tile ring, kicker |
| `--color-graphite` | dark tile for white / very light logos |
| `--color-g1*` | group palette A (warm vendor) — retune the hue per vendor: Vercel/GitHub → graphite (`oklch(40% 0.02 258)`), Cloudflare/AWS → orange (`55`), Supabase → green (`150`) |
| `--color-accent-soft/-tint` | group palette B (accent family: repo, tooling, internal platform) |
| `--color-g3*` | group palette C (neutral: on-prem, trust zone, "everything else") |
| `--color-veil` | translucent paper behind name/role spans |
| `--font-display / --font-body / --font-mono / --font-kr` | see `korean.md` |

Dark theme (`[data-theme="dark"]`) redefines every token; tiles stay white so logos survive.

## Accent discipline

- Accent on **one continuous primary path** (`.e`) and at most **one** focal tile. `check.py` warns above 5 accent segments and fails on a second focal tile.
- Everything else neutral: `.n` solid for internal, `.n.dash` for dev / deploy / async / return.
- Group tints are whispers (≤ 50 % alpha); the border carries the group, not the fill.
- No shadows beyond the tile's 1px lift; no gradients; no glow. Borders are in.

## Node treatment

| Node | Tile class |
|---|---|
| Brand with a colored mark | (default) white tile |
| Brand with a white / very light mark | `dark` |
| AWS service icon (carries its own square) | `bare` |
| AWS general icon (user, client, internet) | `bare res` |
| The component the diagram is about | `focal` (one) |
| Wide-aspect logo | `wide` on the **tile** (`.tile.wide`) — distinct from `.node.wide` |

## Typography

| Element | Font | Size |
|---|---|---|
| Title `h1` | display 700 | 22–30px |
| Kicker | mono | 11px, accent |
| Lede | body | 12px / 1.7 |
| Node name | display 600 | 13px |
| Node role | mono | 9.5px, muted |
| Group label | display 600 | 12px |
| Edge label | mono | 10.5px, halo |
| Step marker `①` | display 600 | 12px |
| Legend, footer | mono | 10px |

Mono is for technical content (ports, protocols, commands, versions) — it is not a blanket "dev" font. Names are never mono.

## Page

Header (kicker · title · lede) → `figure` (scroller + canvas, legend) → footer (author · icon credits · made-with link). The canvas sits in a hairline-bordered scroller so a wide diagram scrolls instead of overflowing on a narrow page. Nothing else: no summary cards, no second diagram on the same page — one diagram, one file.
