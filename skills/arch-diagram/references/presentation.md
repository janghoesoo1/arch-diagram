# Styles, animation and optional exports

```bash
python3 scripts/render.py spec.json out.html --icons icons --style professional
python3 scripts/render.py spec.json out.html --icons icons --style hybrid-sketch
python3 scripts/render.py spec.json out.html --icons icons --style full-sketch --animate --animation-mode combined --gif
python3 scripts/render.py spec.json out.html --icons icons --animate --animation-mode flow --png --svg --gif --gif-fps 15 --gif-width 900 --gif-duration 3
python3 scripts/render.py --help
```

Defaults: professional, no animation, no GIF. All styles decorate the same generated
HTML scene; layout.py, canonical JSON meanings, edge paths and original image bytes
are unchanged. Hybrid adds deterministic inset strokes to ordinary group boxes. Full
also decorates non-bare tile frames. Cloud-specific and dashed trust/nesting boundaries
retain their original conventions. No handwritten font or logo transformation is used.
Decorations are constrained inside the host; existing readability failures still reject
delivery. The conservative sketch effect preserves text and connector precision.

Modes: `draw` traces ordinary tile frames then original edge paths, `flow` moves tokens
on the original paths, `steps` highlights nodes then edge endpoints in authored order
with names and optional node notes, `combined` traces then runs one flow cycle.
Authored order is a presentation sequence, not an inferred execution order.
The base architecture stays visible, including while paused or JavaScript is disabled.
Controls provide play/pause, restart, 0.5/1/1.5/2× speed and loop on/off. Reduced motion
disables playback and hides animated overlays; print and PNG use the static structure.
Viewer focus and routes filter animation to the selected relationships.

New presentation options default Korean subsetting to `--kr-font auto`; cache the
font ahead of offline builds or pass a local font path. Existing professional/static
font behavior is unchanged. An explicit `--kr-font none` retains the user's font setup.
The HTML embeds scripts and assets and needs no runtime network or installed library.

## Exports and dependencies

```bash
pip install playwright Pillow
python3 -m playwright install chromium
python3 scripts/export_media.py out.html out.svg --format svg
python3 scripts/export_media.py out.html out.gif --format gif --fps 15 --width 900 --duration 3
```

Do not install dependencies automatically. HTML/sketch/motion use only Python's standard
library and browser APIs. SVG/PNG need Playwright/Chromium. GIF additionally needs Pillow.
Korean subsetting retains the existing optional fonttools/brotli requirements.

SVG is a **static light-theme foreignObject SVG**, not an all-SVG shape conversion.
It preserves HTML text wrapping, original marks and embedded font rules. Use a browser
to view it; editors that omit foreignObject cannot display the diagram correctly.

GIF requires `--animate` in render.py or an already animated HTML for export_media.py.
It captures the actual page at explicit times covering one complete motion cycle, then
encodes a repeating light-theme GIF. `--gif-duration` (0.1..30 seconds) stretches that
cycle to the requested duration; it does not truncate the draw phase. FPS is 1..30,
width is 320..1920 pixels. A 120-million-frame-pixel limit bounds encoder memory; lower
FPS, duration or width if exceeded. Defaults are 15 FPS, 900px and the native cycle
duration. Palette quantization and resizing are inherent to GIF; original HTML/PNG
provide higher color and text fidelity. Flow fades at the loop seam; draw/combined
restart their presentation sequence with the base architecture always visible.

render.py stages every requested export before publication. Any generation failure
preserves existing HTML, media and receipt and keeps rejected HTML for diagnosis.
Files use atomic replacements with rollback on publication errors; the receipt is
published last and includes export hashes. This is not a cross-file filesystem
transaction for simultaneous readers or power loss. PNG failure now returns nonzero
instead of the previous best-effort success behavior. TSX remains the documented
static React conversion with the same coordinates; animation is an HTML feature.
