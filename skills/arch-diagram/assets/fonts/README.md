# Bundled fonts

| File | Font | License |
|---|---|---|
| `Geist.woff2` | Geist 1.800 (variable, Latin subset) | SIL OFL 1.1 — `OFL-Geist.txt` |
| `JetBrainsMono.woff2` | JetBrains Mono (variable, Latin subset) | SIL OFL 1.1 — `OFL-JetBrainsMono.txt` |

`build.py` embeds both into every generated diagram as data URIs.

**Korean is not bundled.** `build.py --kr-font auto` downloads Pretendard (SIL OFL 1.1, github.com/orioncactus/pretendard) once into `~/.cache/arch-diagram/fonts/` and embeds only the glyphs each page uses (≈ 8 KB per weight). Without the flag, pages with Hangul link Noto Sans KR from Google Fonts.
