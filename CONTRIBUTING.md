# Contributing

## Layout

```
skills/arch-diagram/     the skill: SKILL.md, assets/, references/, scripts/
commands/                Claude Code slash commands (thin; they point at references)
.claude-plugin/ .codex-plugin/ .factory-plugin/ .agents/   native host manifests, one shared identity
scripts/                 repository-only gates (tests, package verifier)
docs/                    rendered example PNGs, ADRs
```

The four manifests must carry the same name, description, version, author, repository, license and keywords; `scripts/verify_package.py` fails on drift. Bump `version` in all of them together.

## Gates

```bash
python3 scripts/test_check.py          # check.py against fixtures (must pass/fail as labelled)
python3 scripts/verify_package.py      # manifests in sync, SKILL.md ≤ 40 000 bytes, commands point at existing references
python3 skills/arch-diagram/scripts/check.py skills/arch-diagram/assets/examples/order-service.html
```

CI runs these on Python 3.9 and 3.12.

## Rebuilding the examples

```bash
S=skills/arch-diagram
python3 $S/scripts/fetch_icons.py /tmp/icons nextjs vercel hono neon upstash githubactions github "pg:lucide/credit-card" "database:lucide/database"
cp $S/assets/generic/user.svg /tmp/icons/
python3 $S/scripts/build.py $S/assets/examples/src/order-service.html /tmp/icons $S/assets/examples/order-service.html --kr-font auto
python3 $S/scripts/check.py $S/assets/examples/order-service.html
python3 $S/scripts/render_png.py $S/assets/examples/order-service.html docs/order-service.png
```

The AWS example (`examples/src/aws-commerce.html`) is committed as a draft only: AWS's icon package may be used in diagrams but its redistribution is unconfirmed, so the built HTML and the icon files stay out of the repository. Its PNGs in `docs/` are fine (they are diagrams).

## Principles

- SKILL.md stays under 40 000 bytes; detail goes to `references/`.
- A new rule needs a `check.py` finding and a fixture when it is checkable from markup.
- Never add a logo source that redraws or recolors marks.
