# ADR 0003 — Optional presentation over canonical geometry

Status: accepted for implementation.

## Evidence and existing architecture

Baseline: b73b4cc174035f5150ee221d134b1dea517dfc6d.
The canonical schema is the documented JSON contract in references/spec.md plus
layout.validate_spec(), not a separate JSON Schema file. layout.layout() returns
node boxes, group rectangles, routed points and crossing hops. Column sizing uses
check.text_width() including Hangul; edge routing uses orthogonal paths, dispersed
attachment points and priority-based hops. layout.render() combines this geometry
with HTML nodes/groups and an SVG edges overlay. No replacement layout is needed.

build.py embeds logos and fonts. fetch_icons.py downloads original cloud vendor
packages or brand sources without recoloring. Default Korean build behavior uses
a Google Fonts link; portable output needs --kr-font auto or a local font.
check.py parses the static HTML and validates geometry, labels, cloud rules and
offline script restrictions. The existing single viewer script implements focus,
reach, routes and themes. render.py stages layout/build/check and atomically replaces
HTML; PNG is currently best-effort after that publication. render_png.py uses
optional Playwright and captures both themes. TSX is a documented agent conversion
workflow, not a Python exporter. ADRs 0001/0002 require one geometry, original logos,
Python standard-library core and selective adoption of contracts, not frameworks.
CI runs test_check.py, test_layout.py, verify_package.py and example/template gates
on Python 3.9/3.12. All three direct baseline test commands passed locally.

## External implementation comparison

Sources pinned to [SeeCode](https://github.com/Aryanutkarsh/SeeCode/tree/9967db28e86e0e212d4ddf5a60f90fe62f3436c0)
and [Animated Sketch Diagram](https://github.com/OLDyade/animated-sketch-diagram/tree/cfc00615f600c28318a85f88505113c5b9a8b399).

| Capability | SeeCode | Animated Sketch Diagram |
|---|---|---|
| Motion | motion.mjs: reveal/trace/step/loop, step compression, CSS path tokens | svg-recipes.md: CSS offset-path on identical edge d, integral loop periods |
| Controls | viewer.client.js: replay, live/still, reduced motion and journey pause | authored example/recipe animations; no reusable controller in inspected sketchify/export modules |
| Sketch | no sketch engine in inspected motion/export modules | sketchify.js wraps Rough.js with deterministic seeds; original marker path retained |
| Export | export.mjs freezes actual page animation time; browser PNG frames and GIF encoder | render-gif.mjs seeks actual CSS animations and captures Chromium frames; ffmpeg palette encoding |
| Offline | inline motion; browser export encoders may load from CDN; CLI reads vendored encoders | local Rough.js/fonts; CLI needs installed browser, playwright-core and ffmpeg |
| Size | motion module 5,627 bytes; viewer 57,916; GIF encoder 22,617 (source sizes, not compressed bundle) | Rough.js 27,762 bytes; sketchify 2,154; GIF script 3,072; fonts additional |
| License | MIT, retain copyright and permission notice when copying | MIT; Rough.js MIT, fonts separately SIL OFL |

These are source inspections, not measured production bundle sizes or execution
tests of the reference projects. No source code or assets from either project are
copied. Their implementations inform the design; existing third-party notices remain.

## Decision and alternatives

Keep layout.py and its emitted default HTML unchanged. Use the existing rendered
HTML as the shared scene: an opt-in presentation module decorates already computed
group/node boxes and uses existing SVG edge paths. Inject motion into the existing
viewer script, preserving the one-script network-free contract. The original diagram
remains visible underneath animation so pause/reduced motion retains meaning.

Use deterministic inset sketch borders clipped to their host. Never transform
images, typography, original connectors, cloud-specific boundary styles or bare
vendor tiles. Hybrid decorates non-cloud groups; full adds ordinary tile frames.
Reject invalid decoration bounds and retain the existing readability gate.
Rough.js is an alternative but its perturbations require additional bounds checks
and a runtime dependency. A separate renderer/layout or wholesale import is rejected.

## Files and phased scope

1. presentation.py and motion.js: flow, controls, then draw/steps/combined; render.py
   routes opt-in flags through presentation before check. Professional defaults must
   remain byte-identical. No changes to layout algorithm or original template.
2. presentation.py: bounded hybrid group borders, preservation tests.
3. presentation.py: full ordinary tile frames, readability and scene tests.
4. export_media.py: browser-backed SVG (foreignObject retaining HTML layout) and GIF
   capture with explicit timestamps; render.py stages requested new exports before
   publishing HTML. Existing PNG helper settles optional motion before screenshot.
5. commands/draw.md, SKILL.md, references/presentation.md, export/spec references,
   README and CI: document flags, limitations and run new checks.
6. scripts/test_presentation.py and scripts/test_presentation_browser.py: structural,
   negative, browser and export coverage.

## Dependencies, risks and validation

Core HTML/sketch/motion adds no installed dependency. GIF uses optional Playwright
and Pillow; SVG capture uses Playwright. Existing Korean subsetting uses fonttools
and brotli. No mandatory Node, Rough.js or ffmpeg dependency.

Main risks are focus styles conflicting with animation, ornament bounds crossing
text, timing nondeterminism in GIF, Korean fallback fonts and partial export delivery.
Test baseline byte equality, logo bytes, geometry/relationships, deterministic
decoration bounds, invalid inputs, offline browser requests, themes, reduced motion,
pause/restart/speed/loop, PNG and GIF pixels and rejection preserving old outputs.
SVG uses foreignObject: browser fidelity is preferred; editor support is limited and
must be documented. GIF on a static spec requires --animate explicitly. Export
dimensions, FPS and duration are bounded to constrain memory use.

## Implementation findings

PNG failure previously delivered HTML and marked the receipt PASS. Requested media now
stages before publication and a failure preserves existing HTML/media/receipt. Publication
uses per-file atomic replacement, rollback on replacement errors, and receipt last; this
is not a filesystem-wide transaction for concurrent readers or power loss.

A global GIF palette based only on the final frame collapsed a red/blue/red regression
fixture to one frame. The encoder now samples across the cycle for its shared palette.
Reduced-motion emulation could change matches without immediately firing the change
listener; the animation tick also checks the preference and stops playback.

No optional dependency was installed locally. Playwright, Pillow and Korean font tools
were already present. Direct local Chromium launch fails at macOS MachPortRendezvous
with Permission denied (1100). Connected Chrome DevTools was used to observe the actual
HTML modes, controls, themes, offline behavior and SVG serialization. The independent
Python browser/export test commands are added to a dedicated Linux CI job; their full
local end-to-end execution remains limited by that host permission error.
