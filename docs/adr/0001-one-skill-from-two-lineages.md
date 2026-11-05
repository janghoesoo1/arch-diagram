# ADR 0001 — One architecture skill from two lineages

**Status:** accepted (v0.1)

## Context

Two plugins did part of the job. `stack-diagram` draws cloud-vendor-style stack pictures with real logos, a hand-placed HTML canvas, vendor drawing rules, and PNG/TSX export, but has no readability gate beyond "render and look" and treats non-Latin text as a font-stack footnote. `diagram-design` (and its Korean-font fork) has an editorial design system, a complexity budget, six machine-checked connector rules, an accessibility contract, and a Hangul font linter — across 39 diagram types drawn as pure SVG with monochrome pictograms, which reads as a schematic rather than an architecture with recognizable products.

Users wanted one plugin: architecture diagrams that look like stack diagrams (logos, groups) and read like editorial diagrams (sparse, orthogonal, labeled), with Korean as a first-class language.

## Decision

- **Scope: architecture diagrams only.** The 38 other diagram-design types, brand-profile onboarding, Mermaid/draw.io import, motion, and the stack-diagram gallery are out. Strengths were merged, not feature lists.
- **Carrier: the HTML canvas** (divs + one SVG overlay) from stack-diagram, because `<img>` tiles carry arbitrary brand marks and real CSS text layout handles Korean wrapping, veils and widths better than SVG `<text>`. SVG export is therefore not offered.
- **Rules: diagram-design's**, re-expressed for the canvas model and enforced by a new dependency-free `check.py` (nodes, groups, edges, labels, legend, Korean).
- **Korean: embedded, not linked, by default when it must travel.** `build.py --kr-font auto` subsets Pretendard per page (~8 KB/weight). Noto Sans KR via Google Fonts is the no-tooling fallback. The mono stack carries a Korean tail so role lines render predictably.
- **Packaging: diagram-design's** multi-host layout (Claude, Codex, Factory, Pi) with one shared identity across manifests, a 40 000-byte SKILL.md cap, and repository-only gates in `scripts/`.

## Consequences

- One template, one checker, one geometry; adding a diagram type is out of scope by design.
- Korean brands have no public logo source; the skill documents the official-URL / pictogram rule instead of shipping imitations.
- The vendor icon packages and built AWS/GCP/Azure examples stay out of the repository; only PNGs of diagrams are committed.
