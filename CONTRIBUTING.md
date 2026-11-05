# Contributing

## Layout

```
skills/arch-diagram/     the skill: SKILL.md, assets/ (template, examples/src/*.json specs), references/, scripts/
commands/                Claude Code slash commands (thin; they point at references)
.claude-plugin/ .codex-plugin/ .factory-plugin/ .agents/   native host manifests, one shared identity
scripts/                 repository-only gates (tests, package verifier)
docs/                    rendered example PNGs, ADRs
```

The four manifests must carry the same name, description, version, author, repository, license and keywords; `scripts/verify_package.py` fails on drift. Bump `version` in all of them together.

## Gates

```bash
python3 scripts/test_check.py          # check.py against fixtures (must pass/fail as labelled)
python3 scripts/test_layout.py         # specs lay out, build, pass the gate; render.py is atomic; diff.py annotates
python3 scripts/verify_package.py      # manifests in sync, SKILL.md ≤ 40 000 bytes, commands point at existing references
python3 skills/arch-diagram/scripts/check.py skills/arch-diagram/assets/examples/order-service.html
```

CI runs these on Python 3.9 and 3.12.

## Rebuilding the examples

```bash
S=skills/arch-diagram
python3 $S/scripts/fetch_icons.py /tmp/icons nextjs vercel hono neon upstash githubactions github "pg:lucide/credit-card" "database:lucide/database"
cp $S/assets/generic/user.svg /tmp/icons/
python3 $S/scripts/render.py $S/assets/examples/src/order-service.json $S/assets/examples/order-service.html --icons /tmp/icons --kr-font auto --png
mv $S/assets/examples/order-service.png $S/assets/examples/order-service-dark.png docs/
```

Same for `rag-chatbot.json` (svgl: nextjs vercel fastapi claude-ai supabase notion inngest). The AWS example (`aws-commerce.json`) is committed as a spec only: AWS's icon package may be used in diagrams but its redistribution is unconfirmed, so the built HTML and icon files stay out of the repository; its PNGs in `docs/` are diagrams and fine. The delta screenshot comes from `diff.py` on `order-service.json` against a head that adds Kafka, changes Upstash's role and drops GitHub Actions.

`scripts/test_layout.py` renders every spec with stand-in icons, so CI needs no network.

## Principles

- SKILL.md stays under 40 000 bytes; detail goes to `references/`.
- A new rule needs a `check.py` finding (with a `FIXES` hint) and a fixture when it is checkable from markup; a new layout behaviour needs a `test_layout.py` case.
- The viewer stays offline and dependency-free; `check.py` rejects network calls inside it.
- Never add a logo source that redraws or recolors marks.
