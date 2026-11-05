# From a repository — evidence-backed diagrams

Use this when the diagram must describe a real codebase rather than a described system. The source is the authority for what runs where, what calls what, and what persists; the diagram is done when the requested story is covered and every asserted node has supporting evidence.

## Explore on demand, not exhaustively

1. **Freeze identity.** `git rev-parse HEAD`, `git remote get-url origin` (strip any credentials), `git status --short`. Put the short revision in the kicker or footer (`kicker: "arch-diagram · acme/shop @ 3f2a9c1"`). A dirty worktree is mentioned in the reply, not hidden.
2. **Map the slice.** Start from manifests and deployment config — `package.json` / `pyproject.toml` / `go.mod`, `Dockerfile`, `docker-compose.yml`, `k8s/`, `terraform/`, `serverless.yml`, `vercel.json`, `.github/workflows/`, `.env.example`. These name the runtime units and the vendors; they decide the groups. Then read the entry point and the modules on the requested path until each responsibility reaches its actual input, output, or side effect.
3. **Trace ownership at the call site.** An edge is drawn from the code that performs the call or write (the HTTP client, the ORM, the SDK call), not from a module that merely mentions a service. A configured-but-never-called integration is an optional capability: leave it out or make it a dashed `async` edge with a note, never a primary edge.
4. **Record evidence while reading.** For each node, keep up to three `path:line` or `path:start-end` references in `sources`. Cite the file that defines or configures the unit (`docker-compose.yml:12-20`, `src/db.ts:1-9`, `k8s/api-deployment.yaml:1-40`). Edges carry no sources: the owning node's citation covers the call.
5. **Name uncertainty.** When durability, region, or a trust boundary cannot be read from the source, say so in the node's `note` ("durability unknown") or in the lede. Never turn a package description, a README claim, or an environment variable name into an unobserved service.

Stop when every requested responsibility, relationship and boundary has evidence and the remaining unknowns cannot change the picture. There is no node or citation quota, and the 9-node budget still applies: an overview of a large repo shows the runtime units, not every module.

## Mapping code to the spec

| Found in the repo | Spec |
|---|---|
| A deployable unit (service, function, job, worker) | a node; `role` = runtime + port/protocol (`Node 20 · :3000`, `cron · 02:00`) |
| A managed store or queue (Postgres, Redis, S3, Kafka) | a node with the vendor's logo; `role` = engine/version from config |
| A vendor account, cluster, VPC, repo, compose project | a group (`kind`: `ga` vendor, `gb` repo/tooling, `gc` on-prem/neutral, `aws …` for AWS layouts) |
| A trust or network boundary in config (private subnet, internal network) | a group with `kind: "aws private"` / `"boundary"` |
| An HTTP/RPC call on the main user path | `primary` edge, label = protocol or verb |
| A read/write to a store | `internal` edge, label = `SQL`, `cache`, `put` |
| CI/CD, webhooks, schedulers, retries | `async` edge |
| Users, admins, third parties | nodes with `generic` or Lucide icons, outside every group |

Brand names stay as the vendor spells them; internal service names stay as the repo spells them (`order-service`), with a Korean role line when the labels are Korean.

## Output

Render with `scripts/render.py`; the viewer shows each node's `sources` in its card, so a reviewer can jump from the picture to the file. In the reply, state the revision the diagram describes and any deliberate omissions (modules folded into one node, optional integrations left out).
