# Korean labels — fonts, widths, wording

Korean is a first-class label language here, not a fallback. Three things go wrong with Korean in generated diagrams, and each has a mechanism:

| Failure | Mechanism |
|---|---|
| Hangul renders in a different face on every machine (or as tofu / Chinese glyph variants on Linux) | Font stack with a Korean tail in the template; `build.py --kr-font auto` embeds a Pretendard subset; `check.py` fails on Hangul with no Korean face; `render_png.py` warns when the render host has no Korean font |
| Names overflow or wrap mid-word | 1em-per-syllable budget; `wide` / `xwide` nodes; `word-break: keep-all`; `check.py` estimates widths and fails on a third line |
| Labels read as translated English | Wording rules below: brand names Latin, roles Korean, short noun phrases, `①②③` for order |

## Fonts

```css
--font-kr:      "Pretendard", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic";
--font-display: "Geist", var(--font-kr), …, sans-serif;     /* names, titles, group labels */
--font-mono:    "JetBrains Mono", ui-monospace, "SF Mono", Menlo, var(--font-kr), monospace;  /* roles, edge labels */
```

- **Geist stays first.** It draws every Latin glyph; the browser falls through to the Korean faces only for characters Geist lacks. Latin diagrams render byte-for-byte the same as before.
- **Pretendard** (SIL OFL) is the embed target: a Korean companion to Inter, metrically close to Geist, installed on most Korean developer machines. `build.py --kr-font auto` downloads Regular + SemiBold once to `~/.cache/arch-diagram/fonts/` (override with `ARCH_DIAGRAM_FONT_DIR`), subsets them to the characters on the page with fontTools, and inlines ≈ 8 KB per weight. The result renders identically offline, in CI, and in an artifact sandbox.
- **Noto Sans KR** is the webfont fallback: without `--kr-font`, `build.py` links it from Google Fonts when it finds Hangul. Online viewers get a consistent face; offline viewers get the OS face.
- **The mono stack carries the same Korean tail.** Mono is for technical strings (`:8443`, `gRPC`, `webhook`), which are not translated. But a role line such as `프론트엔드 · SSR` is common and must not fall into whatever the OS substitutes for `monospace` — with the tail, its Hangul renders in Pretendard at a predictable width. (There is no real CJK mono webfont; `Noto Sans Mono CJK KR` does not exist on Google Fonts and silently resolves to generic monospace.)
- `<html lang="ko">`: shared CJK code points (·, some punctuation, ㈜) pick Korean glyph variants. `build.py` switches `en` → `ko` automatically; `check.py` warns otherwise.
- Linux render hosts without the embedded font need `fonts-noto-cjk` (`apt-get install fonts-noto-cjk`); `render_png.py` prints the hint when `fc-list :lang=ko` finds nothing.

## Width budget

Budget **1em per Hangul syllable** (full-width), not a Latin average. Spaces 0.28em, Latin lowercase ≈ 0.56em.

| Element | Size | Usable width | Fits roughly |
|---|---|---|---|
| Name, default node | 13px / 600 | 124px | 9 syllables · or 5 syllables + a short Latin word (`Hono API`) |
| Name, `wide` | 13px | 164px | 12 syllables · `Amazon ElastiCache` |
| Name, `xwide` | 13px | 204px | 15 syllables · `Azure Database for PostgreSQL` |
| Role | 9.5px mono | 124px | 12 syllables · `프론트엔드 · SSR` |
| Edge label | 10.5px mono | — | ≤ 16 columns, Hangul = 2 (`결제 요청` = 8) |
| Group label | 12px / 600 | — | 2–4 syllables (`저장소`, `사내망`, `결제 영역`); a long label widens the no-go corner |

Two-line names are allowed (the box grows to 117px; use row pitch 160) but prefer one line: shorten (`재고 데이터베이스` → `재고 DB`) or widen. Three lines fail `check.py`.

`word-break: keep-all` keeps Korean words whole and wraps at spaces; `overflow-wrap: anywhere` is the last resort for an unspaced word wider than the box — avoid needing it.

## Wording

- **Brand names stay Latin in the brand's casing**: `Next.js`, `Kafka`, `GitHub Actions`, `Amazon S3`. Do not transliterate (`넥스트`), do not translate.
- **Roles and concepts go Korean**: `프론트엔드 · SSR`, `백엔드 · RPC`, `결제 대행사`, `주문 서비스`, `사용자`, `관리자`. Mixed-script roles separate Latin and Korean with a middle dot `·` (U+00B7), never a slash crammed between syllables.
- **Short noun phrases, no particles, no verbs** in names and labels: `결제 요청` not `결제를 요청한다`; `재고 조회` not `재고를 조회함`. The lede sentence is where verbs go.
- **Edge labels** name the protocol or the action: `HTTPS`, `gRPC`, `SQL`, `결제 요청`, `알림 전송`, `배포`. Accent-path labels (`.el.a`) in the user's language; keep Latin protocol names Latin.
- **Reading order**: left → right, top → bottom. When sequence matters, mark the primary path with `①②③` (`<text class="el step">①</text>`) placed like a label — Korean readers expect the circled numbers, and both Pretendard and Noto Sans KR carry them.
- **Legend** in Korean: `주 요청 경로` · `내부 연결` · `비동기 · 배포` (or `개발 · 배포`). One entry per edge kind used.
- **Title / kicker / lede / `aria-label`** in Korean when the labels are Korean. The `aria-label` is one sentence saying what connects to what — it doubles as the alt text of the exported PNG.
- Common pairs: 사용자 / 고객 / 관리자 · 게이트웨이 · 인증 서비스 · 주문 서비스 · 결제 대행사 (PG) · 알림 · 저장소 / 데이터베이스 / 캐시 / 객체 저장소 · 메시지 큐 · 배치 / 스케줄러 · 사내망 / 외부망 · 공용 서브넷 / 사설 서브넷.

## Mixed Korean + Japanese / Chinese

The stack also names Hiragino / Noto Sans JP after the Korean faces, so a Japanese label on the same page renders — but Han characters shared between Korean, Japanese, and Chinese take the *page* language's variant. One `lang` per page; if a diagram mixes languages heavily, wrap the other-language label in `<span lang="ja">`.

## Checklist (Korean-specific)

- [ ] `<html lang="ko">`, title / lede / legend / `aria-label` in Korean
- [ ] Built with `--kr-font auto` when the file must render offline, in CI, or as an artifact
- [ ] Every name fits its node on one line (or a deliberate two with row pitch 160)
- [ ] Brand names Latin, roles Korean, no particles or verbs in labels
- [ ] `check.py` reports no `korean-*`, `name-fit`, `role-fit`, or `label-length` findings
- [ ] PNG read at 100%: no mid-word wrap, no clipped syllable, no mismatched face between name and role
