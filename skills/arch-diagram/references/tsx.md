# TSX output

Convert the built HTML into one self-contained React component the user can drop into their codebase. Geometry and content are identical to the HTML; only the packaging changes.

## Shape

```tsx
// ArchDiagram.tsx — no props required, no dependencies
const ICONS = {
  hono: "data:image/svg+xml;base64,...",
  // one entry per icon, copied from the built HTML's data URIs
} as const;

const T = {
  paper: "oklch(98.5% 0.004 250)",
  ink: "oklch(24% 0.02 258)",
  accent: "oklch(58% 0.2 256)",
  rule2: "oklch(83% 0.011 255)",
  // mirror every :root token: drop "--color-", camelCase the rest
  // (--color-paper-2 → paper2, --color-g1-ink → g1Ink, --color-accent-soft → accentSoft)
} as const;

const FONT_KR = '"Pretendard", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic"';
const FONT_DISPLAY = `"Geist", ${FONT_KR}, ui-sans-serif, system-ui, sans-serif`;
const FONT_MONO = `"JetBrains Mono", ui-monospace, "SF Mono", Menlo, ${FONT_KR}, monospace`;

export default function ArchDiagram() {
  return (
    <figure style={{ width: "fit-content", maxWidth: "100%", wordBreak: "keep-all" }}>
      <div style={{ overflowX: "auto", border: `1px solid ${T.rule2}`, borderRadius: 10 }}>
        <div role="img" aria-label="…" style={{ position: "relative", width: 1000, height: 540, background: T.paper /* grid via backgroundImage */ }}>
          {/* groups, svg edges, nodes — same coordinates as the HTML */}
        </div>
      </div>
      <figcaption style={{ /* legend */ }}>…</figcaption>
    </figure>
  );
}
```

## Rules

- **Self-contained**: data-URI icons in a const, tokens in a const, inline `style` objects. No CSS files, no Tailwind assumptions, no imports beyond React. It must compile in any TSX project as-is.
- **Do not embed the woff2 fonts** (Geist, JetBrains Mono, or the Pretendard subset). A component ships inside an app with its own font pipeline. Keep the fallback stacks above and say in a leading comment that loading Geist / JetBrains Mono / Pretendard restores the reference look. For a Korean app, Pretendard is almost always already loaded.
- Convert classes to small local components or mapped style objects: `<Node cx={342} top={120} icon="nextjs" name="Next.js" role="프론트엔드 · SSR" wide? dark? focal? />`, `<Group x y w h kind="ga" label="Vercel" icon? />`. Readability of the file is the point of asking for TSX.
- The SVG edge overlay transfers as-is; JSX-ify attribute names (`stroke-width` → `strokeWidth`, `marker-end` → `markerEnd`, `paint-order` → `paintOrder`, `text-anchor` → `textAnchor`, `stroke-dasharray` → `strokeDasharray`). `context-stroke` for the marker fill works in current browsers; keep it.
- Dark theme: accept a `theme?: "light" | "dark"` prop that swaps the token object, or drop it — ask only if the user cares.
- Hover ring on tiles becomes `onMouseEnter`/`Leave` state or is dropped.
- `lang="ko"` goes on the figure when the labels are Korean.
- Deliver to the workspace as `<Name>Diagram.tsx`; don't publish TSX as an artifact (it is code for their repo, not a page).
