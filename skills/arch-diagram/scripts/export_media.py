# 실제 브라우저 프레임으로 선택적 SVG와 GIF 파일을 내보낸다.
from __future__ import annotations

import argparse
import io
import math
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def save_gif(frames, path, fps):
    from PIL import Image
    sample_count = min(64, len(frames))
    indices = [round(i * (len(frames) - 1) / max(1, sample_count - 1)) for i in range(sample_count)]
    samples = Image.new('RGB', (128, 128 * len(indices)), 'white')
    for row, index in enumerate(indices):
        sample = frames[index].convert('RGB')
        sample.thumbnail((128, 128))
        samples.paste(sample, (0, row * 128))
    palette = samples.quantize(colors=255)
    indexed = [frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)
               for frame in frames]
    durations = [round((i + 1) * 100 / fps) * 10 - round(i * 100 / fps) * 10 for i in range(len(frames))]
    indexed[0].save(path, format="GIF", save_all=True, append_images=indexed[1:],
                    duration=durations, loop=0, disposal=2, optimize=False)


def export(source, destination, kind, fps=15, width=900, seconds=None):
    if kind not in ("svg", "gif") or not 1 <= fps <= 30 or not 320 <= width <= 1920:
        raise ValueError("export requires svg/gif, FPS 1..30 and width 320..1920")
    if seconds is not None and (not math.isfinite(seconds) or not 0.1 <= seconds <= 30):
        raise ValueError("duration must be finite and between 0.1 and 30 seconds")
    from playwright.sync_api import sync_playwright
    if kind == "gif":
        from PIL import Image
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--font-render-hinting=none"])
        try:
            page = browser.new_page(viewport={"width": 1200, "height": 1000}, reduced_motion="no-preference")
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("http://**/*", lambda route: route.abort())
            page.route("https://**/*", lambda route: route.abort())
            page.goto(Path(source).resolve().as_uri())
            page.evaluate("document.fonts.ready")
            page.evaluate("document.documentElement.removeAttribute('data-theme')")
            canvas_width = page.locator('.canvas').evaluate("e => e.offsetWidth")
            page.set_viewport_size({"width": max(1200, canvas_width + 100), "height": 1000})
            page.add_style_tag(content='.scroller{border-radius:0!important;border:none!important}.canvas{border-radius:0!important}')
            if not page.evaluate("[...document.images].every(i => i.complete && i.naturalWidth > 0)"):
                raise ValueError("export contains an unloaded icon")
            motion = page.evaluate("!!window.ArchDiagramMotion")
            if kind == "svg":
                if motion:
                    page.evaluate("ArchDiagramMotion.settle()")
                result = page.evaluate((ASSETS / "export-scene.js").read_text(encoding="utf-8"))
                Path(destination).write_text(result, encoding="utf-8")
            else:
                if not motion:
                    raise ValueError("GIF requires --animate; static specs are not silently animated")
                duration = page.evaluate("ArchDiagramMotion.duration")
                capture_ms = seconds * 1000 if seconds is not None else duration
                count = max(2, math.ceil(capture_ms * fps / 1000))
                box = page.locator('.figure').bounding_box()
                height = round(box['height'] * width / box['width'])
                if width * height * count > 120_000_000:
                    raise ValueError("GIF exceeds 120 million frame pixels; reduce width, FPS or duration")
                frames = []
                for i in range(count):
                    page.evaluate("t => ArchDiagramMotion.seek(t)", (i / count) * duration)
                    shot = page.locator('.figure').screenshot(animations="allow")
                    frame = Image.open(io.BytesIO(shot)).convert('RGB')
                    frames.append(frame.resize((width, height), Image.Resampling.LANCZOS))
                save_gif(frames, destination, fps)
            if errors:
                raise ValueError("browser error: " + "; ".join(errors))
        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser(description="Optional browser SVG/GIF export. Install playwright; GIF also needs Pillow.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--format", choices=("svg", "gif"), required=True)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--width", type=int, default=900)
    parser.add_argument("--duration", type=float)
    args = parser.parse_args()
    try:
        export(args.source, args.destination, args.format, args.fps, args.width, args.duration)
    except (ImportError, ValueError) as error:
        parser.exit(2, str(error) + "\nSetup: pip install playwright Pillow; python -m playwright install chromium\n")


if __name__ == "__main__":
    main()
