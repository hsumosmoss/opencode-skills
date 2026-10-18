# Visual Assets

Use visuals only when they teach, orient, or create attention.

Every visual image in this reference must be generated with Codex's built-in
image generation capability unless it is a real user-provided asset. Local
rendering with shapes, CSS, Pillow, SVG art, or placeholder panels is not an
acceptable substitute for AI-generated visuals.

## Visual Roles

| Role | Use | Suggested Placement |
|---|---|---|
| illustration | concept or scenario image | right column or inset |
| background | cover/action/section visual | full bleed with overlay |
| hero | strong half-slide visual | right half |
| side_panel | decorative but meaningful strip | left or right edge |
| section_divider | chapter transition | full bleed |
| accent | small supporting icon/object | near the relevant text |

## Prompt Rules

- Include a consistent style token from the style engine.
- Ask for no readable text unless text must be baked into the image.
- Reserve clean space for text overlays on backgrounds.
- For editable-text image plates, generate the plate around the final text
  layout. Ask for a calm dark or light text zone in the exact side/region where
  PowerPoint text will sit, instead of adding a large overlay panel afterward.
- Use `low` quality for drafts and most illustrations; upgrade visual anchor
  pages only when needed.

## Editable Plate Rules

Use these rules when the output is "AI image + editable PowerPoint text":

- Generate fresh text-free plate images for the deck instead of trying to fix a
  busy image with opaque masks.
- Treat the image as the designed page background: it should already include
  quiet negative space, edge framing, or a natural empty panel for text.
- Do not cover more than about 35-45% of the image with a post-added rectangle
  or translucent mask. If text does not read, regenerate the image with better
  reserved space.
- Keep overlay text to one editable PowerPoint text object per phrase. Avoid
  duplicate shadow text layers unless the user explicitly prefers visual polish
  over easy editing.
- If a slide needs dense bullets, split the slide or redesign the image plate;
  do not solve it by darkening the whole page.

## Final Deck Rule

Do not embed relative paths that will break after moving the deck folder. Insert
images into the PPTX file itself.
