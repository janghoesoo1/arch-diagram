# Styles, animation and optional exports

## Natural-language selection (agent instructions)

Interpret intent, not isolated keywords. These rules apply to the skill and both draw
and export commands. Users do not need to learn flags or choose from a settings menu.
Do not ask about style, motion mode, FPS, width or duration when a default suffices.

| User intent / example | Renderer selection |
|---|---|
| "결제 시스템 구성도 그려줘" / "draw the payment architecture" | Professional, no animation, HTML. Keep the normal PNG verification workflow. |
| "손그림 느낌으로" / "sketch style" | `--style hybrid-sketch`; keep motion off unless requested. |
| "박스까지 전부 손그림으로" / "full sketch" | `--style full-sketch`; preserve logos and typography. |
| "깔끔한 기본 스타일" / "professional" | `--style professional`; style alone does not change motion. |
| "움직이게" / "데이터 흐름이 움직이게" / "animate it" | `--animate --animation-mode flow`; deliver animated HTML, not GIF. |
| "선이 그려지는 과정" / "draw-on animation" | `--animate --animation-mode draw`. |
| "노드를 차례로 강조해줘" / "highlight step by step" | `--animate --animation-mode steps`; authored order, not inferred runtime timing. |
| "그려진 다음 흐름이 움직이게" / "draw then flow" | `--animate --animation-mode combined`. |
| "GIF로 저장해줘" / "save as GIF" when drawing | `--animate --animation-mode flow --gif`, unless another motion mode was requested. |
| "PNG로 저장" / "이미지로 저장" / "save as an image" | `--png`; a static snapshot, even if HTML is animated. |
| "SVG로 저장" / "save as SVG" | `--svg`; static browser-viewable SVG. Explain the editor limitation when relevant. |
| "움직이지 않게" / "정적으로" / "no animation" | No `--animate` and no GIF; preserve the requested style. |

"데이터 흐름도" / "data flow diagram" describes content, not a request for animation.
"단계별로 설명해줘" alone asks for an explanation, not the steps animation. Negated
styles or motion must not activate the corresponding option. "발표용" or "멋지게"
alone keeps the professional/static defaults; do not invent animation or a GIF.

Combine independent preferences: "손그림 느낌으로 흐름이 움직이는 GIF" selects
`--style hybrid-sketch --animate --animation-mode flow --gif`. Do not apply all presets
in the table; choose only those matching the user's intent. Explicit flags and precise
preferences override defaults. A clear later correction replaces the earlier choice;
if equally explicit requirements still conflict ("정적인데 움직이는 GIF"), ask one
focused question rather than silently dropping either requirement. An explicitly
selected animation mode implies `--animate` in the agent's invocation. Direct CLI
validation remains unchanged.

For revisions, retain the previous style/motion unless the user changes it; a format-only
request must not reset the presentation. When exporting existing HTML, use its current
animation. If a GIF is requested from static HTML and the source spec/icons are available,
re-render to a new animated HTML using flow (or the requested mode), preserving style and
content, then export. Briefly state that GIF adds motion. If the source is unavailable,
ask for it or offer PNG; never hand-edit the HTML or pretend a static source is animated.

Keep native GIF defaults (15 FPS, 900px, one full cycle) unless explicitly overridden.
Do not ask about playback speed or looping; the HTML controls already expose those.
Do not silently replace an explicitly requested format when dependencies are missing:
report what could not be produced and the relevant setup command, without auto-installing.
Deliver a short result such as "손그림 스타일로 흐름이 움직이는 HTML을 만들었습니다."
and links. Hide internal flags, receipts and update instructions unless asked or needed
to resolve a failure. Install/update/reload guidance belongs to setup or troubleshooting.

## Advanced CLI reference

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
python3 -m playwright install --with-deps chromium
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
