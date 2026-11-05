#!/usr/bin/env python3
"""Inline fonts and icons into a diagram draft as data URIs, and settle the Korean font.

Usage:
  python3 build.py DRAFT.html ICONDIR OUT.html [--fonts DIR] [--kr-font auto|PATH|none]

Replaces:
  %%FONT_DISPLAY%%   base64 of DIR/Geist.woff2          (DIR defaults to <skill>/assets/fonts)
  %%FONT_JBM%%       base64 of DIR/JetBrainsMono.woff2
  %%ICON_<name>%%    data URI of ICONDIR/<name>.(svg|png|webp|jpg)
  <!-- KR-FONT: ... -->  see below

Korean (Hangul) labels, in order of preference:
  --kr-font auto     download Pretendard (SIL OFL) once into the font cache, subset it to the
                     characters the page actually uses, and embed the result as @font-face.
                     The page then renders Korean offline, on any machine, in one known face.
                     Needs: pip install fonttools brotli
  --kr-font PATH     same, from a local .ttf/.otf/.woff2 (e.g. a Noto Sans KR or Pretendard file)
  (default)          link Noto Sans KR from Google Fonts — renders right online; offline the OS
                     fallback (Apple SD Gothic Neo / Malgun Gothic) takes over
  --kr-font none     touch nothing (you manage Korean fonts yourself)

With Hangul present, <html lang="en"> is switched to lang="ko" so browsers pick Korean glyph
variants for shared CJK code points. Fails loudly on any unresolved %%...%% token.
"""
import base64, html as htmlmod, os, pathlib, re, sys, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_FONTS = HERE.parent / "assets" / "fonts"
MIME = {"svg": "image/svg+xml", "png": "image/png", "webp": "image/webp",
        "jpg": "image/jpeg", "jpeg": "image/jpeg"}
# Every Hangul block: syllables, Jamo, compatibility Jamo, Ext-A/B, halfwidth forms, and the
# enclosed letters (㉠, ㈀) Korean legends use as markers.
HANGUL_RE = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏ꥠ-꥿ힰ-퟿ﾠ-ￜ㈀-㈞㉠-㉾]")
KR_FONT_COMMENT_RE = re.compile(r"[ \t]*<!--\s*KR-FONT:.*?-->\n?", re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
GOOGLE_LINK = ('<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600&display=swap" '
               'rel="stylesheet">\n')
# Pretendard: SIL OFL 1.1, github.com/orioncactus/pretendard. Two static weights match the
# template's 600 names and 400 body; a variable file would be 2 MB for the same two weights.
PRETENDARD = {
    400: "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/packages/pretendard/dist/web/static/woff2/Pretendard-Regular.woff2",
    600: "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/packages/pretendard/dist/web/static/woff2/Pretendard-SemiBold.woff2",
}
CACHE = pathlib.Path(os.environ.get("ARCH_DIAGRAM_FONT_DIR") or pathlib.Path.home() / ".cache" / "arch-diagram" / "fonts")

def b64(p): return base64.b64encode(pathlib.Path(p).read_bytes()).decode()

def page_text(html):
    """The characters a reader sees: markup and comments stripped, entities decoded."""
    body = COMMENT_RE.sub("", html)
    body = re.sub(r"<(script|style)\b.*?</\1\s*>", "", body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"<[^>]+>", " ", body)
    attrs = re.findall(r'(?:aria-label|alt|title)\s*=\s*"([^"]*)"', html)
    return htmlmod.unescape(body + " " + " ".join(attrs))

def cached_pretendard():
    CACHE.mkdir(parents=True, exist_ok=True)
    out = {}
    for weight, url in PRETENDARD.items():
        p = CACHE / url.rsplit("/", 1)[1]
        if not p.exists():
            print(f"downloading {p.name} -> {CACHE}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (arch-diagram)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                p.write_bytes(r.read())
        out[weight] = p
    return out

def subset_woff2(src, chars):
    """woff2 bytes of `src` holding only `chars` (plus .notdef/space); needs fontTools + brotli."""
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        sys.exit("--kr-font needs fontTools: pip install fonttools brotli\n"
                 "(or drop the flag to link Noto Sans KR from Google Fonts instead)")
    font = TTFont(str(src))
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]          # keep kerning / ligatures the face defines
    opts.name_IDs = ["*"]; opts.notdef_outline = True; opts.recalc_bounds = True
    subsetter = subset.Subsetter(opts)
    subsetter.populate(text="".join(sorted(chars)) + " ")
    subsetter.subset(font)
    import io
    buf = io.BytesIO()
    try:
        font.save(buf)
    except ImportError:
        sys.exit("woff2 output needs brotli: pip install brotli")
    return buf.getvalue()

def kr_face_css(files, chars):
    """@font-face rules for 'Pretendard' built from {weight: path} (or {'var': path})."""
    rules = []
    for weight, path in files.items():
        data = base64.b64encode(subset_woff2(path, chars)).decode()
        w = "100 900" if weight == "var" else str(weight)
        rules.append(f'@font-face {{ font-family:"Pretendard"; font-style:normal; font-weight:{w}; font-display:swap;\n'
                     f'  src:url(data:font/woff2;base64,{data}) format("woff2"); }}')
        print(f"embedded Pretendard {w} subset: {len(chars)} glyphs, {len(data) // 1024} KB")
    return "<style>\n" + "\n".join(rules) + "\n</style>\n"

def settle_kr_font(html, mode):
    text = page_text(html)
    hangul = sorted(set(HANGUL_RE.findall(text)))
    if not hangul or mode == "none":
        if hangul and mode == "none":
            print("note: Hangul present and --kr-font none: make sure a Korean face is reachable")
        return KR_FONT_COMMENT_RE.sub("", html, count=1)
    # characters Geist lacks are what the embedded face must carry; include every non-ASCII
    # character on the page so punctuation like · and ① renders from the same face
    chars = {c for c in text if ord(c) > 0x7F and not c.isspace()}
    if mode is None:
        block = GOOGLE_LINK
        print(f"Hangul present ({len(hangul)} syllables): linked Noto Sans KR from Google Fonts. "
              "For an offline-safe file, re-run with --kr-font auto")
    elif mode == "auto":
        block = kr_face_css(cached_pretendard(), chars)
    else:
        p = pathlib.Path(mode)
        if not p.exists():
            sys.exit(f"--kr-font: {p} does not exist")
        block = kr_face_css({"var": p}, chars)
    if KR_FONT_COMMENT_RE.search(html):
        html = KR_FONT_COMMENT_RE.sub(lambda m: block, html, count=1)
    else:
        html = html.replace("</head>", block + "</head>", 1)
    # lang drives CJK glyph-variant selection; "ko" is right whenever the labels are Korean
    new, n = re.subn(r'<html(\s[^>]*?)lang="en"', r'<html\1lang="ko"', html, count=1)
    if n:
        print('switched <html lang="en"> to lang="ko" (Hangul labels)')
        html = new
    return html

def main():
    args = sys.argv[1:]
    fontsdir, kr = DEFAULT_FONTS, None
    if "--fonts" in args:
        i = args.index("--fonts"); fontsdir = pathlib.Path(args[i + 1]); del args[i:i + 2]
    if "--kr-font" in args:
        i = args.index("--kr-font"); kr = args[i + 1]; del args[i:i + 2]
    if len(args) != 3:
        print(__doc__); sys.exit(1)
    draft, icondir, out = pathlib.Path(args[0]), pathlib.Path(args[1]), pathlib.Path(args[2])
    html = draft.read_text(encoding="utf-8")

    for tok, fn in (("%%FONT_DISPLAY%%", "Geist.woff2"), ("%%FONT_JBM%%", "JetBrainsMono.woff2")):
        if tok in html:
            html = html.replace(tok, b64(fontsdir / fn))

    if icondir.is_dir():
        for f in sorted(icondir.iterdir()):
            if f.suffix.lstrip(".") not in MIME:
                continue
            tok = f"%%ICON_{f.stem}%%"
            if tok in html:
                html = html.replace(tok, f"data:{MIME[f.suffix.lstrip('.')]};base64,{b64(f)}")

    leftover = sorted(set(re.findall(r"%%[A-Za-z0-9_-]+%%", html)))
    if leftover:
        sys.exit(f"unresolved tokens: {', '.join(leftover)}\n"
                 f"(missing icon files in {icondir}? fonts dir {fontsdir} wrong?)")

    html = settle_kr_font(html, kr)
    out.write_text(html, encoding="utf-8")
    print(f"built {out} ({len(html.encode('utf-8')) // 1024} KB)")

if __name__ == "__main__":
    main()
