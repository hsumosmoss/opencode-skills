---
name: course-handout-generator
description: >
  Generate structured, print-friendly teaching handouts from Markdown content.
  Uses a build pipeline: config.yaml + content.md → base.html template → handout HTML.
  Supports 12+ component types including tables, step-by-step guides, cards, flowcharts,
  glossary, and troubleshooting references. A4-optimized with print CSS.
compatibility: opencode
metadata:
  short-description: 教學講義產生器（Markdown → HTML 建置管線）
  dependencies: Node.js, js-yaml
---

# Course Handout Generator

Build pipeline: **`config.yaml` + `content.md` → `base.html` → `dist/index.html`**

## When to Use

- Creating class notes, lecture summaries, or lab manuals
- Building technical reference handouts with procedures and data tables
- Converting course outlines into detailed A4-printable learning material
- Making cheat sheets, terminology references, or troubleshooting guides

## Quick Start

### 1. Create content

```
mkdir my-handout
```

Write `my-handout/config.yaml`:
```yaml
page:
  title: "蘭州拉麵職人之路"
  subtitle: "從和麵到拉麵，傳承百年手藝"
instructor:
  name: "馬建國"
```

Write `my-handout/content.md` using handout Markdown syntax (see `reference/components.md`).

### 2. Build

```bash
node skills/course-handout-generator/scripts/build.mjs my-handout
```

Output: `my-handout/dist/index.html`

### 3. Preview with hot-reload

```bash
node skills/course-handout-generator/scripts/dev.mjs my-handout
# → http://localhost:3000
```

## Content Syntax

Read `reference/components.md` for complete syntax reference.

| Syntax | Component |
|---|---|
| `# LABEL：Title` + `> lead` | Section with numbered label |
| `## Sub Title` | Sub-section |
| `### 🔧 Card Title` + list | Info card |
| `\| Table \|` | Data table |
| `` `step` Name: Desc `` | Numbered step |
| `> **💡 Tip** text` | Tip box |
| `> **⚠️ Warning** text` | Warning box |
| `[flow]...[/flow]` | Flow chart |
| `[tags]\ncolor: text\n[/tags]` | Color tags |
| `[summary]\nN: desc\n[/summary]` | Summary grid |
| `- [x] item` | Checklist |
| `` ` ```glossary` `` | Glossary |
| ` ```bash` | Code block |

## Config System

Two-layer config with deep merge:

| Layer | File | Purpose |
|---|---|---|
| Global | `config/global.yaml` | Defaults (colors, layout, footer) |
| Per-handout | `<dir>/config.yaml` | Title, subtitle, instructor override |

## Output

| Deliverable | Path |
|---|---|
| Main handout | `<dir>/dist/index.html` |
| OG thumbnail | `node scripts/generate-og.mjs --title "..." --slug <name>` |

## References

- `reference/base.html` — Handlebars-like template with `{{PLACEHOLDER}}` markers
- `reference/components.md` — Complete Markdown → HTML mapping with examples
- `reference/config-example.yaml` — Full configuration reference
- `reference/content-example.md` — Example content showing all component types

## Dependencies

- **Node.js** (v18+)
- **js-yaml** (npm): `npm install js-yaml` (or install globally)
- **Puppeteer** (optional): for OG thumbnail generation

## Commands

This skill provides `.agents/commands/`:
- `generate-handout` — Build handout for a course directory
- `preview-handout` — Start dev server with auto-rebuild
