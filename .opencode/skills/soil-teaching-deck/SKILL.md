---
name: soil-teaching-deck
description: >
  Create, analyze, or improve SOIL-style teaching PowerPoint decks. Use when the
  user asks for teaching slides, classroom slides, lesson-material-to-slides,
  SOIL slides, instructional presentation design, or a review of an existing
  teaching deck's cognitive load and teaching flow. Produces editable .pptx
  slides with PowerPoint text objects, optional AI illustrations, optional
  geometry diagrams, and a SOIL teaching structure.
metadata:
  short-description: SOIL editable teaching PPTX deck
compatibility: opencode
---

# SOIL Teaching Deck

Use this skill for editable instructional PowerPoint decks. The goal is teaching
clarity first, visual design second, and file correctness last.

## Output Contract

- Produce an editable `.pptx` unless the user asks only for diagnosis or style.
- Text should remain PowerPoint text objects.
- Every non-geometric visual image, including cover visuals, background images,
  illustrations, section-divider images, and card images, must be generated with
  the system's built-in image generation tool (`generate_image`) first. Do not
  substitute local shape rendering or procedural placeholder images for AI
  images.
- For math symbols in PowerPoint, use the two-layer text-box approach when needed:
  keep readable surrounding text editable, and isolate symbols/formulas in
  separate boxes or rendered image snippets if PowerPoint text handling is weak.
- Report the final absolute file path.

## 教學設計框架

本 Skill 支援六套教學設計框架，各解決不同層面的問題：

| 框架 | 解決什麼 | 何時使用 |
|------|---------|--------|
| **SOIL 六引擎** | 怎麼做投影片 | 每次都用（核心引擎） |
| **ADDIE** | 全生命週期管理 | 首次設計課程 / 課程改版 |
| **UbD** | 教什麼才對 | 不確定重點時，以終為始 |
| **Merrill** | 怎麼教才會用 | 職業技能培訓、實作工作坊 |
| **Gagné** | 課堂節奏怎麼控 | 長課程、線上教學 |
| **ARCS** | 學生沒動力怎麼辦 | 法規/SOP 等枯燥內容 |

詳細說明見 `references/addie-framework.md` 與
`references/teaching-design-frameworks.md`。

## Mode Selection

Choose the path from the user's request:

- Full course design (first time): run ADDIE full cycle (A → D₁ → D₂/SOIL → I → E).
- Material to deck: run SOIL engines 1-6 directly (ADDIE-D₂).
- Topic only: first expand a minimal teaching outline, then run engines 1-6.
- Existing deck review: inspect the deck, run cognitive diagnosis, then propose
  or implement fixes.
- Course revision from feedback: run ADDIE-E → A → D₁ → SOIL.
- Style definition: run only the style engine and output a reusable style spec.

If the user has already provided enough detail, do not stop for a long interview.
Ask only the next missing detail that affects the work, usually audience and
lesson duration.

## Core Workflow

### ADDIE 戰略層（適用於首次設計完整課程）

0a. **Analysis（分析）**：確認聽眾身份、先備知識、預期達成程度、授課時間與
    場地限制。產出學習者分析表。見 `references/addie-framework.md`。
0b. **Design（設計）**：制定 ABCD 格式的教學目標、安排單元順序與時間配比、
    決定評量策略。產出教學設計稿。

### SOIL 戰術層（引擎 1-6 = ADDIE 的 D₂ Development）

1. Concept positioning: identify the one big idea, three sub-ideas, common
   misunderstandings, takeaway sentence, minimal fact pack, and slide-vs-talk
   split. See `references/soil-engines.md`.
2. Context positioning: arrange 引起動機 -> 維持注意 -> 喚起行動.
3. Page architecture: choose page roles, one core point per page, layout recipe,
   and any `visuals` or `geometry` needs. See `references/layout-recipes.md`.
4. Cognitive editing: reduce noise, chunk, add information, structure, sequence,
   and step the content.
5. Style construction: define palette, fonts, title/body scale, motif, and image
   policy.
6. Build and verify the PPTX using the local presentation workflow. Prefer the
   available Presentations skill when it is active; otherwise use
   `python-pptx` patterns consistent with the repo.

### ADDIE 後續層（教學後）

7. **Implementation（執行）**：提供教學準備清單與講稿備忘錄。
8. **Evaluation（評估）**：提供回饋問卷模板與測驗題目生成。
   評估結果可回饋至步驟 0a，形成迭代改進循環。

## Design Rules

- Use a 16:9 wide deck.
- Type scale: cover title 72-84pt, slide title 44-56pt, subtitle 28-34pt,
  body 18-21pt, muted 14-16pt.
- Use bold, readable Chinese fonts. Default font stack:
  `"Microsoft JhengHei", "Noto Sans TC", "PingFang TC", sans-serif`.
  Override only when a project font is clearly available.
- Keep page titles short, ideally <= 10 Chinese characters.
- Use fixed alignment grids and consistent margins.
- Every page should have either a visual, a diagram, a comparison structure, a
  strong question, or a clear typographic focal point.
- Use only 1-2 accent colors.

## References

- Read `references/addie-framework.md` when the user is designing a course for
  the first time, revising from feedback, or needs learner analysis help.
- Read `references/teaching-design-frameworks.md` when the user mentions UbD,
  backward design, Merrill, Gagné, ARCS, or needs help choosing a teaching
  framework. Also read when the course is skill-based (Merrill), motivationally
  challenging (ARCS), or needs precise pacing (Gagné).
- Read `references/soil-shared-rules.md` for SOIL shared design rules (rhythm,
  color, typography, image rules) that apply across all SOIL skills.
- Read `references/soil-engines.md` for SOIL planning outputs.
- Read `references/layout-recipes.md` before building slides.
- Read `references/visual-assets.md` when AI illustrations or background images
  are needed.
- Read `references/geometry.md` for math diagrams.
- Read `references/validation.md` before final delivery.

## Environment Notes

- Use shell commands appropriate to the user's operating system (e.g. zsh on
  macOS, PowerShell on Windows).
- Use the system's built-in image generation tool (`generate_image`) for every
  bitmap visual image. Only precise math/geometry diagrams are exempt; those
  should be deterministic SVG/Python drawings for correctness.
- Do not hardcode agent-specific paths (e.g. `/home/claude`,
  `.claude/skills/`).
