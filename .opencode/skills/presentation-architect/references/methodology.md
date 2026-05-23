# Methodology: Text to ASCII to PPT Framework

This document outlines the proven methodology for transforming raw article text into structured presentation layouts (ASCII) and finally into high-quality image prompts.

## 1. Extracting Core Information
Before generating anything visual, distill the text into key presentation constructs:
- **Core Topic**: What is the single main idea?
- **Target Audience**: Who is viewing this presentation? (Determines tone and visual style)
- **Key Points**: Break down the article into bite-sized segments. Usually, 1 paragraph = 1 or 2 bullet points on a slide.

## 2. Designing the ASCII Presentation Layout
A robust presentation requires a balanced layout. Use ASCII wireframes to plan where text and graphics go. This helps the AI understand the spatial composition when generating the final image.

### Standard Layout Patterns

**Pattern A: Title & Split Content (Classic)**
```text
+-------------------------------------------------+
| [Header] Main Slide Title Here                  |
+-------------------------------------------------+
| [Text Box]               | [Image Area]         |
| - Bullet point one       |                      |
| - Bullet point two       |      (Visual         |
| - Bullet point three     |  Representation)     |
|                          |                      |
+-------------------------------------------------+
```

**Pattern B: Center Focus (Title / Quote)**
```text
+-------------------------------------------------+
|                                                 |
|                                                 |
|            [Large Centered Text]                |
|           "A powerful quote or statement"       |
|                                                 |
|                                                 |
+-------------------------------------------------+
```

**Pattern C: Three-Column Comparison**
```text
+-------------------------------------------------+
| [Header] Feature Comparison                     |
+-------------------------------------------------+
|  [Col 1]     |    [Col 2]    |    [Col 3]       |
|  Basic       |    Pro        |    Enterprise    |
|  - $10/m     |    - $20/m    |    - $50/m       |
|  - 1 User    |    - 5 Users  |    - Unlimited   |
+-------------------------------------------------+
```

## 3. Translating ASCII to Image Generation Prompts

When converting the accepted ASCII wireframe into a prompt for the `generate_image` tool, translate the spatial relationships into descriptive language. 

**Example Translation for Pattern A:**
*ASCII Layout Intent:* Header across the top. Left side has 3 bullet points about AI. Right side has a robot illustration. Style: Pastel Watercolor.

*Prompt Construction:*
`Wide 16:9 presentation slide. Style: Pastel watercolor illustration, soft lighting. Layout: A prominent header across the top saying "The Future of AI". On the left side, three neatly aligned bullet points: "- Automation", "- Insights", "- Creation". On the right side, a beautiful watercolor illustration of a friendly metallic robot looking thoughtfully at a glowing orb. Clean layout, plenty of negative space, elegant typography.`

### Common Pitfalls to Avoid:
- **Overcrowding**: Do not put too much text on a single slide.
- **Ambiguous Text rendering**: Image generators often misspell text. Keep text inputs in the prompt concise and prominent.
- **Inconsistent Styles**: Always append the exact same style definition to every slide in a deck (e.g., "Style: Cyberpunk neon, dark background, highly detailed").
