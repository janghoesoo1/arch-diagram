# Export — PNG, artifact, and what SVG is not

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

## SVG — not a target

The canvas is HTML (absolutely positioned divs with real text layout, `<img>` tiles, CSS veils) over one SVG edge overlay. Flattening it to a single SVG would mean re-implementing text wrapping and losing the embedded fonts; vendor icons are often complex SVGs or rasters. If the user needs a vector, offer the PNG at `--scale 3` or the HTML itself (which scales losslessly in a browser), and say why SVG is not offered.

## Naming

Write next to the source unless an output path is given: `order-service.html` → `order-service.png` + `order-service-dark.png`. Report paths and sizes after exporting.
