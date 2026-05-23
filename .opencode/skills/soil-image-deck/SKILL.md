---
name: soil-image-deck
description: >
  Create a SOIL-style image-first presentation where each slide is a full-page
  bitmap image, then package the images into a .pptx. Use when the user asks for
  a pure image deck, all-image slides, AI-generated poster-like slides, quick
  visual-impact teaching slides, livestream opening slides, social sharing
  slides, or a deck where later text editing is not important. Supports baked
  mode and plate mode with editable PowerPoint text overlays.
metadata:
  short-description: SOIL full-image PPTX deck
compatibility: opencode
---

# SOIL Image Deck

Use this skill for visual-impact decks where every slide is driven by one
full-page image.

## Output Modes

This skill has two modes. **Always confirm the mode with the user before
generating images** if the request is ambiguous.

| | `baked`（預設） | `plate` |
|---|---|---|
| **圖片** | 含文字的完整圖 | 無文字的純底圖 |
| **PPTX** | 每頁 = 一張圖 | 底圖 + 可編輯文字框 |
| **事後編輯** | ❌ 不可改文字 | ✅ 可改文字 |
| **中文品質** | ⚠️ 需逐張檢查 | ✅ 字體可靠 |

### Mode Selection Rules

1. **Default = baked.** Unless the user explicitly mentions editable text, plate,
   or overlay, use baked mode.
2. **Use plate when:**
   - User says 「可編輯」「editable」「plate」「之後要改文字」
   - Content has dense text (>20 chars/slide) or tables
   - CJK text readability is critical
3. **Use baked when:**
   - User says 「全圖版」「圖加文字」「baked」「文字燒入圖片」
   - Content is short headlines only (≤ 20 chars/slide)
   - Speed/visual impact is priority (social media, livestream)
4. **When in doubt**, ask: 「請問要文字燒入圖片（baked），還是底圖+可編輯文字（plate）？」

## Hard Image Rule

Every slide image in this skill must be produced with the system's built-in
image generation tool (`generate_image`) first. Do not create the slide images
through local Pillow/CSS/SVG/shape rendering, procedural graphics, or placeholder
panels unless the user explicitly asks for a non-AI prototype. The value of this
skill is that the slide itself is an AI-generated visual artifact.

## Workflow

1. Determine whether the user has material, only a topic, or an existing YAML
   spec. If enough information is already present, proceed directly.
2. Produce a page plan: page number, role, core point, minimal on-image text,
   image brief, and layout hint.
3. Define an `image_policy` with style tokens, negative prompt, size, quality,
   palette, and any pages upgraded to higher quality.
4. Generate images with the built-in image generation skill and preserve those
   generated outputs for packaging into `slides/images/`.
5. Visually inspect generated images before packaging. Reject images with
   unreadable text, wrong layout, unwanted symbols, or style drift.
6. Package the deck using `scripts/pack_pptx.py`.
7. Report the final `.pptx` absolute path and mode used.

## Design Rules

- Keep each slide to one core point.
- For baked mode, keep Chinese on-image text under about 20 characters per slide
  when possible. AI image generation often renders CJK characters incorrectly;
  always visually verify baked Chinese text and regenerate if garbled.
- For plate mode, use `"Microsoft JhengHei", "Noto Sans TC", "PingFang TC",
  sans-serif` as the default Chinese font stack for overlay text boxes.
- Avoid asking image generation to render dense paragraphs or data tables.
- Use SOIL rhythm: 引起動機 -> 維持注意 -> 喚起行動.
- Use 1-2 accent colors and consistent visual style.
- Cover and action pages may use higher image quality.

## Packaging

From the project folder:

```bash
python3 ~/.gemini/antigravity/skills/soil-image-deck/scripts/pack_pptx.py \
  --images-dir ./slides/images \
  --output ./slides/output.pptx \
  --mode baked
```

For editable overlay mode:

```bash
python3 ~/.gemini/antigravity/skills/soil-image-deck/scripts/pack_pptx.py \
  --images-dir ./slides/images \
  --output ./slides/output-editable.pptx \
  --mode plate \
  --spec ./slides/spec.yaml
```

## When To Read References

- Read `references/soil-shared-rules.md` for SOIL shared design rules (rhythm,
  color, typography, image rules) that apply across all SOIL skills.
- Read `references/spec-format.md` when using `plate` mode.
- Read `references/plate-mode-guide.md` for detailed plate mode layout rules,
  text box configuration, spec.yaml format, and readability strategies.
- Read `references/image-prompts.md` before generating images.

## Dependencies

- Python packages: `python-pptx`, `Pillow`, `PyYAML`.
- Image generation must use the system's built-in image generation tool
  (`generate_image`) for every slide image. If the current environment cannot
  save those generated images to local files, stop and explain the
  file-persistence limitation instead of substituting local rendered graphics.
