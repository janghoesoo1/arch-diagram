# Icons — sources, spec forms, and vendor drawing rules

`scripts/fetch_icons.py OUTDIR spec [spec …]` fetches brand marks **unmodified** and writes `OUTDIR/<name>.<ext>` plus `manifest.json` (`source`, `url`, `file`, `white_fill`, `dark_file`). `build.py` turns each file into `%%ICON_<name>%%`.

## Spec forms

| Spec | Meaning | Example |
|---|---|---|
| `name` | slug = name | `hono` |
| `name:slug` | different slug | `betterauth:better-auth` |
| `name=URL` | explicit file | `orpc=https://orpc.unnoq.com/logo.webp` |
| `name:aws/<Service>` | official AWS icon | `fargate:aws/fargate`, `s3:aws/s3`, `user:aws/General-User` |
| `name:gcp/<Product>` | official Google Cloud icon | `run:gcp/cloud-run`, `lb:gcp/load-balancing` |
| `name:azure/<Service>` | official Azure icon | `app:azure/app-service`, `vnet:azure/vnet` |
| `name:lucide/<icon>` | Lucide line icon, tinted to ink | `cron:lucide/clock`, `pg:lucide/credit-card` |

Chain for plain slugs: **svgl → devicon → gilbarbara/logos**. svgl is matched by exact normalized title, so a miss falls through instead of shipping the wrong brand. When a brand ships light/dark variants, the light one becomes `<name>` (tiles are white in both themes) and the dark one `<name>_dark` for group labels.

## Rules

- **Never recolor a logo.** A white or very light mark goes on `tile dark`; the `white_fill` flag is a heuristic (a white inner detail on a colored mark trips it), so glance at the SVG first.
- **Official marks only.** simple-icons is deliberately not a source. On `FAIL`, look in the project's repo (`logo*.svg` at the root, `docs/`, `assets/`, `public/`) or site (`/logo.svg`, `/favicon.svg`, `/images/logo.svg`) and pass `name=URL`.
- **Korean services are in no public icon library.** 토스 / 토스페이먼츠, 카카오 / 카카오페이, 네이버 / 네이버클라우드, 쿠팡, 배달의민족, 당근, 라인 등은 svgl · devicon · gilbarbara 모두에 없다. Use, in order: (1) the official asset from the brand's press kit or developer site (`name=URL`, SVG or PNG); (2) the brand's `/favicon.svg` or apple-touch-icon; (3) a Lucide pictogram for the *role* (`credit-card` for a PG, `message-circle` for a messenger, `shopping-bag`, `truck`) and let the Korean name carry the brand. Never a redrawn or recolored imitation, never text in a tile.
- **Concepts get pictograms.** `user`, `browser`, `internet`, `server`, `device` are in `assets/generic/` — copy one into the icons dir under the node's name. Anything else: `lucide/<icon>` (browse lucide.dev/icons). Concept icons are not brand marks, so tinting them to the diagram's ink is fine (the script does it).
- **Vendor sub-products** (Cloudflare D1/R2/KV, Vercel KV/Blob, Supabase Auth/Storage) usually have no distinct logo: reuse the vendor logo and let the name carry the distinction.
- **Group-label icons render at 14px** and need a square glyph; wordmarks turn to mud. If the main icon is a wordmark, fetch the brand's square icon separately for the label.
- **Dark theme**: group labels sit on the group's tint. If `<name>_dark` exists, use the template's `lt`/`dk` pair; if a mark has black parts and no dark variant, add class `plate` (white backing, dark theme only).
- Raster logos (png/webp) are fine; everything embeds as data URIs.

## AWS — AWS's own icons and drawing rules

- Fetch with `name:aws/<Name>`; the `AWS-` / `Amazon-` prefix is optional, acronyms work (`s3 sqs sns ses ecs eks ecr elb alb nlb iam kms msk vpc cloudfront rds elasticache lambda dynamodb`), a miss prints every name. A bare `dynamodb` goes through the third-party chain — always write `aws/`.
- Service icons carry their own square → `tile bare`. People and generic nodes inside the AWS area use the general icons (`user:aws/General-User`, `General-Users`, `General-Client`, `General-Internet`, `General-Server`) in `tile bare res` with the template's `lt`/`dk` pair.
- Groups: `group aws` for AWS Cloud (label icon `aws:aws/AWS-Cloud-logo` at 30px flush in the corner), plus `region`, `az`, `vpc`, `private`, `public`. Square corners, outline only, ink label, no tint.
- Inside a VPC show public and private subnets when you know or can safely infer the split (internet-facing load balancer public; app servers and databases private).
- Edges inside the AWS area: `<path class="aws" … marker-end="url(#open)"/>`, `aws dash` for deploy, plain `.el` labels, no legend entry.
- Names: `Amazon S3`, `AWS Fargate` (full), short form in the role line. `Amazon` / `AWS` must stay on the first line: use `wide` whenever the name would wrap after the prefix.
- Keep the icon package and loose icon files out of repositories.

## Google Cloud — Google's icons, the normal style

- Fetch with `name:gcp/<Product>`. Core products have their own icon; every other product uses its category icon per Google's guide (`Cloud Load Balancing` → Networking, `Memorystore` → Databases). Write the product's name; the script picks the icon. `gcp:google-cloud` is the mark for the group label; `gemini` and `firebase` are bare slugs.
- Icons go on the normal white tile; edges and legend stay as usual. Groups: `group gcp` plus `vpc`, `region`, `subnet`, `zone`. A VPC is global and a subnet regional: region inside VPC, never the reverse. Global / serverless services (external LB, Cloud Storage, Cloud Run) stay outside the VPC.
- Because icons are shared, write full product names (`Cloud Load Balancing`, not `LB`) and use `wide` when needed.

## Azure — Microsoft's icons, the normal style

- Fetch with `name:azure/<Name>`; `Azure-` / `Microsoft-` prefix and a plural `s` optional; short forms work (`aks vm vnet nsg waf blob cosmos redis postgres functions front-door apim ai-search`). Microsoft Entra ID has a separate icon set → `name=URL`.
- White tiles, usual edges and legend. Groups: `group azure` (label `azure:azure/Azure-A`) plus `rg`, `region`, `vnet`, `subnet`, `zone`; a `vnet` / `subnet` label carries its icon. A VNet belongs to one region. Global services (Front Door) stay outside the region. App Service sits outside the VNet unless in an ASE; a PaaS reached via private endpoint may sit inside with `private endpoint` as its role.
- Microsoft asks for the full service name beside each icon (`Azure SQL Database`); never crop, flip, rotate, or reshape an icon; use it only for the service it stands for. Keep the package out of repositories.

**A vendor's rules cover only its own area.** Everything outside that group — a user beside it, an edge crossing into it — keeps the normal tiles, groups, edges, and legend.

## Footer credit

Credit the sources actually used from `manifest.json`: `icons: svgl / devicon / Lucide`; source `aws` reads `AWS Architecture Icons`, `gcp` reads `Google Cloud product icons`, `azure` reads `Azure Public Service Icons`, `explicit` reads the brand's own site. Logos remain their owners' trademarks; their use in a diagram implies no endorsement.
