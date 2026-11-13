# 검증된 다이어그램에 선택적 표현 계층을 추가한다.
from pathlib import Path
import hashlib
import math
import re
from html.parser import HTMLParser

STYLES = ("professional", "hybrid-sketch", "full-sketch")
MODES = ("draw", "flow", "steps", "combined")
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def sketch_points(width, height, seed):
    if not all(math.isfinite(v) and v >= 24 for v in (width, height)):
        raise ValueError("sketch host must be finite and at least 24px")
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    points = []
    for side in range(4):
        span = width if side % 2 == 0 else height
        count = max(2, math.ceil((span - 24) / 24))
        for i in range(count + 1):
            along = 12 + (span - 24) * i / count
            inset = 2 + digest[(i + side * 7) % len(digest)] / 255 * 2
            points.append(((along, inset), (width - inset, along),
                           (width - along, height - inset), (inset, height - along))[side])
    validate_points(points, width, height)
    return points


def validate_points(points, width, height):
    if not points or not all(math.isfinite(v) and v >= 24 for v in (width, height)):
        raise ValueError("invalid sketch bounds")
    for x, y in points:
        if not (math.isfinite(x) and math.isfinite(y) and 1 <= x <= width - 1 and 1 <= y <= height - 1):
            raise ValueError("sketch exceeds validated host bounds")
        if min(x, width - x, y, height - y) > 4.01:
            raise ValueError("sketch enters the text or icon area")


def sketch_svg(width, height, seed):
    points = sketch_points(width, height, seed)
    coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return (f'<svg class="arch-sketch" aria-hidden="true" viewBox="0 0 {width:g} {height:g}" '
            f'preserveAspectRatio="none"><polygon points="{coords}"/></svg>')


class SketchHosts(HTMLParser):
    def __init__(self, source, full):
        super().__init__(convert_charrefs=True)
        self.full = full
        self.insertions = []
        self.offsets = [0]
        self.offsets += [m.end() for m in re.finditer("\n", source)]

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get("class", "").split())
        if tag != "div":
            return
        if self.full and "tile" in classes and "bare" not in classes:
            width = height = 60
        elif "group" in classes and not classes & {"aws", "gcp", "azure", "boundary", "ga-nested"}:
            styles = dict(re.findall(r"([\w-]+)\s*:\s*([^;]+)", attrs.get("style", "")))
            try:
                width, height = (float(styles[key].removesuffix("px")) for key in ("width", "height"))
            except (KeyError, ValueError):
                raise ValueError("sketch requires computed group dimensions") from None
        else:
            return
        line, column = self.getpos()
        offset = self.offsets[line - 1] + column + len(self.get_starttag_text())
        self.insertions.append((offset, sketch_svg(width - 3, height - 3, attrs.get("data-id", "group"))))


def sketch(source, full=False):
    parser = SketchHosts(source, full)
    parser.feed(source)
    for offset, decoration in reversed(parser.insertions):
        source = source[:offset] + decoration + source[offset:]
    css = ('.arch-sketch{position:absolute;inset:0;width:100%;height:100%;overflow:hidden;'
           'border-radius:inherit;pointer-events:none;color:var(--color-neutral)}'
           '.arch-sketch polygon{fill:none;stroke:currentColor;stroke-width:1;vector-effect:non-scaling-stroke}'
           '.group.ga>.arch-sketch{color:var(--color-g1)}.group.gb>.arch-sketch{color:var(--color-accent-soft)}'
           '.group.gc>.arch-sketch{color:var(--color-g3)}.tile:has(>.arch-sketch){position:relative}')
    return source.replace("</head>", f"<style>{css}</style>\n</head>", 1)


def present(source, style="professional", animate=False, mode="flow"):
    if style not in STYLES or mode not in MODES:
        raise ValueError("invalid presentation style or animation mode")
    if not animate and style == "professional":
        return source
    if style != "professional":
        source = sketch(source, full=style == "full-sketch")
    if animate:
        if source.count('<script data-arch-diagram-viewer>') != 1:
            raise ValueError("motion requires exactly one canonical viewer")
        source = source.replace('<div class="canvas"', f'<div data-motion="{mode}" class="canvas"', 1)
        css = (ASSETS / "motion.css").read_text(encoding="utf-8")
        js = (ASSETS / "motion.js").read_text(encoding="utf-8")
        if re.search(r'<html\b[^>]*lang="ko(?:-[^"]*)?"', source):
            source = source.replace('<script data-arch-diagram-viewer>',
                '<span hidden aria-hidden="true">재생 일시정지 재시작 반복 속도 동작 줄이기 설정 적용</span>\n'
                '<script data-arch-diagram-viewer>', 1)
        source = source.replace("</head>", f"<style>\n{css}\n</style>\n</head>", 1)
        source = source.replace("</script>", "\n" + js + "\n</script>", 1)
    return source
