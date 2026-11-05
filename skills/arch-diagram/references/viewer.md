# Viewer — exploring a delivered diagram

Every built page carries one small, offline, self-contained script (`<script data-arch-diagram-viewer>` in the template). Without it — print, PNG, reduced-capability hosts — the diagram keeps its complete meaning; with it the reader can interrogate the *authored* graph. Nothing is inferred from geometry: upstream/downstream and routes follow `data-from`/`data-to` on the edges, exactly as the spec wrote them.

Read this only when the user asks for a reader-facing capability (deep links, reach, route, theme). Ordinary generation needs nothing here.

## Interactions

| Action | How | Result |
|---|---|---|
| Focus | click a node, or Enter/Space on it | its edges and neighbours stay lit, everything else dims; a card shows name, role, group, upstream, downstream, note, sources |
| Reach | `U` / `D`, or the card's 상류 추적 / 하류 추적 buttons | everything authored upstream or downstream of the focus |
| Route | focus the start, press `R`, click the end | the shortest authored directed path, or "no authored directed route" |
| Find | `/` then type part of a name or an id, Enter | focuses the match |
| Theme | `T` or the toolbar button | toggles `data-theme="dark"`; the choice is remembered per viewer |
| Clear | `Esc`, the toolbar button, the card's ×, or a click outside | back to the static diagram |
| Help | `?` | the key list in the toolbar hint |

Nodes in the card are buttons: clicking one moves the focus along the graph.

## Deep links

The hash mirrors the state and is restored on load:

- `#focus=<id>` — focus one node
- `#focus=<id>&reach=upstream` / `&reach=downstream` — focus plus reach
- `#route=<from>~<to>` — a directed route between two ids

The card's 링크 복사 copies the current address. Ids come from the spec, so links survive re-renders that keep the ids.

## What the viewer never does

- No network, no storage beyond the theme preference, no external script — `check.py` rejects any `fetch`, `XMLHttpRequest`, `import()`, `WebSocket` or `sendBeacon` inside the viewer block and any second script.
- No motion, no auto-layout, no editing: the HTML is the checked artifact; exploration state is not exported. `render_png.py` captures the default state (no hash) and the toolbar/card sit outside `.figure`.
- Korean/English UI follows `<html lang>`; the markup for a non-Korean page is already localized by `layout.py` so the page carries no stray Hangul.

## Sharing a view

For a specific reading ("the checkout path"), send the deep link — or render a PNG of it: open the file with the hash in headless Chromium and screenshot `.figure` (`render_png.py` does not take a hash; use the viewer in a browser or a small Playwright script). The canonical PNG remains the unfocused diagram.
