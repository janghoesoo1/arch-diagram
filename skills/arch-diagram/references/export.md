# Export — PNG, SVG, GIF, artifact and TSX

Load this when the user asks to export, save, rasterize, share, or convert a diagram, or invokes `/arch-diagram:export`.

## PNG

```bash
python3 scripts/render_png.py out.html out.png                  # out.png (light) + out-dark.png, canvas + legend, 2×
python3 scripts/render_png.py out.html out.png --selector .canvas   # diagram only
python3 scripts/render_png.py out.html out.png --full-page      # header + figure + footer
python3 scripts/render_png.py out.html out.png --single         # the document as authored (no theme toggle)
python3 scripts/render_png.py out.html out.png --scale 3        # print-grade
```

- Always a screenshot of the built HTML in headless Chromium. Never redraw with matplotlib / PIL / a standalone SVG rasterizer: the HTML is the single source of truth and the browser's text and SVG rendering is what makes it look right.
- Both themes by default; deliver both unless the user asked for one. Corners are squared for the screenshot only.
- Setup if Playwright is missing: `pip install playwright && python3 -m playwright install --with-deps chromium`. Never auto-install; print the command and stop.
- **Korean**: if the file was built without `--kr-font`, the render host needs a Korean font (macOS and Windows have one; Linux needs `fonts-noto-cjk`). The script warns. Rebuilding with `--kr-font auto` removes the dependency entirely.
- Japanese labels without an embedded JP face need a Japanese font on the host, or CJK characters come out in Chinese glyph variants.
- Pixel size = canvas size × scale. For an exact frame (OG card 1200×630, slide 1920×1080), size the canvas to that aspect and pick the scale; do not stretch a PNG afterwards.

## Artifact

Where the environment offers an artifact / page-publishing tool, publish the built HTML as-is. Everything is a data URI (icons, Geist, JetBrains Mono, and — with `--kr-font` — Pretendard), so a blocked-network sandbox renders it fully. Without `--kr-font` the Google Fonts link may be blocked and Korean falls back to the sandbox's fonts: build with `--kr-font auto` before publishing anything with Hangul.

## TSX

See `tsx.md`. Code for their repo, not an artifact.

## SVG and GIF

See `presentation.md`. SVG preserves the HTML canvas inside SVG `foreignObject`, with
computed styles, embedded fonts and original image data. Browser viewing is supported;
many vector editors do not support foreignObject. It is a static light-theme snapshot.
GIF captures actual animation frames in Chromium and encodes them with optional Pillow.
PNG settles motion and still captures both themes. With render.py, requested export
failure now fails the run before replacing any previously delivered files.

## Naming

Write next to the source unless an output path is given: `order-service.html` → `order-service.png` + `order-service-dark.png`. Report paths and sizes after exporting.
