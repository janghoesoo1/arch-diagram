# ADR 0002 — Spec-first delivery, borrowed from archify

**Status:** accepted (v0.2)

## Context

v0.1 asked the agent to hand-place every node and edge in HTML and then run a gate. It worked, but each repair was a coordinate hunt, revisions rewrote the whole canvas, and the delivered page could not be interrogated. `archify` (tt-a1i/archify, Apache-2.0) solved these with a typed JSON IR, deterministic renderers, validators that return rule codes and fixes, an atomic `finalize`, an explorable viewer with deep links, and an architecture delta. It is a Node.js project with ten diagram types and a 780 KB viewer; arch-diagram is Python, one type, one small template.

## Decision

Adopt archify's *contracts*, not its code:

- **Typed source.** `assets/examples/src/*.json` per `references/spec.md`: nodes on a row/column grid, groups by membership and `parent`, edges by endpoint and kind. Coordinates are never authored.
- **Deterministic layout** in Python (`layout.py`), implementing `geometry.md` so the agent's placement decisions are rows, columns and membership only.
- **Delivery contract.** `render.py` runs spec → layout → build → check (→ PNG) and replaces the output only on a full pass, with a receipt; findings carry `target` and `fix`. Repairs edit the spec.
- **Viewer.** One inline, network-free script (`<script data-arch-diagram-viewer>`): focus, authored reach, route, deep links, a node card with `sources`. Static meaning without JS; `check.py` permits exactly this script and rejects any network API inside it.
- **Delta.** `diff.py` compares specs and annotates the head for rendering with added / changed / removed markers.
- **Evidence.** `sources` per node and `references/from-repo.md`, following archify's repository-authoring rules (cite the call site, name uncertainty, no invented services).

Not adopted: other diagram types, explainers, motion, share cards, the brand-mark catalog (it would conflict with the official-marks rule), update checks, Node tooling.

## Consequences

- Hand-placed HTML remains an escape hatch, but the examples, commands and tests are spec-first.
- The layout engine encodes placement taste; a new routing need is a `layout.py` change plus a `test_layout.py` case, never a per-diagram coordinate.
- Stable node ids become part of the contract: diffs and deep links depend on them.
