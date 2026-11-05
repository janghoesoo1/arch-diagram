# Third-party licenses and trademarks

arch-diagram is MIT-licensed (`LICENSE`). It derives from two MIT-licensed projects and bundles or fetches the following.

## Derived from

- **stack-diagram** — Copyright caru-ini, MIT. https://github.com/caru-ini/stack-diagram — icon fetching chain, canvas template, vendor drawing rules, PNG/TSX export.
- **diagram-design** — Copyright Cathryn Lavery, MIT. https://github.com/cathrynlavery/diagram-design — editorial rules, complexity budget, connector rules, accessibility contract, Korean font gate (via the fork https://github.com/janghoesoo1/diagram-design-korean-font).

## Bundled fonts (SIL Open Font License 1.1)

- **Geist** — Vercel. `skills/arch-diagram/assets/fonts/Geist.woff2`, license in `OFL-Geist.txt`.
- **JetBrains Mono** — JetBrains. `skills/arch-diagram/assets/fonts/JetBrainsMono.woff2`, license in `OFL-JetBrainsMono.txt`.

## Fetched at build time (not bundled)

- **Pretendard** — Kil Hyung-jin, SIL OFL 1.1. https://github.com/orioncactus/pretendard — downloaded by `build.py --kr-font auto` and embedded as a per-page glyph subset.
- **Noto Sans KR** — Google, SIL OFL 1.1 — linked from Google Fonts when no Korean face is embedded.
- **Lucide** — ISC. https://lucide.dev — concept pictograms via `lucide/<icon>`, tinted to the diagram's ink (they are not brand marks).
- **svgl** (https://svgl.app), **devicon** (MIT, https://devicon.dev), **gilbarbara/logos** (CC0) — brand logos, fetched unmodified.
- **AWS Architecture Icons**, **Google Cloud product icons**, **Azure Public Service Icons** — each vendor's official package, read at run time; permitted in architecture diagrams and documentation by each vendor; redistribution unconfirmed, so never commit the packages or loose files.

## Generic pictograms

`skills/arch-diagram/assets/generic/*.svg` (user, browser, internet, server, device) are original line drawings from stack-diagram, MIT.

All brand names and logos are trademarks of their respective owners. Their appearance in a diagram does not imply endorsement. The scripts never recolor or alter a brand logo.
