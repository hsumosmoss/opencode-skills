#!/usr/bin/env node

import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createRequire } from "module";

const __dirname = dirname(fileURLToPath(import.meta.url));
let yaml;
try {
  yaml = createRequire(import.meta.url)("js-yaml");
} catch {
  yaml = createRequire(join(process.cwd(), "_"))("js-yaml");
}

// ===== Config loading =====

function loadYaml(path) {
  if (!existsSync(path)) return {};
  return yaml.load(readFileSync(path, "utf-8")) || {};
}

function deepMerge(a, b) {
  const result = { ...a };
  for (const key of Object.keys(b)) {
    if (b[key] && typeof b[key] === "object" && !Array.isArray(b[key])) {
      result[key] = deepMerge(result[key] || {}, b[key]);
    } else {
      result[key] = b[key];
    }
  }
  return result;
}

// ===== Content parser =====

let stepCounter = 0;
let sectionCounter = 0;

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[:\u3000\s]+/g, "-")
    .replace(/[^\w\u4e00-\u9fff-]/g, "")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60);
}

function parseContent(md) {
  stepCounter = 0;
  sectionCounter = 0;
  const lines = md.split("\n");
  const html = [];
  const tocItems = [];
  let i = 0;
  let inGlossary = false;
  let glossaryLines = [];
  let inFlow = false;
  let flowLines = [];
  let inTags = false;
  let tagLines = [];
  let inSummary = false;
  let summaryLines = [];
  let inCodeBlock = false;
  let codeLang = "";
  let codeLines = [];
  let inList = false;
  let listHtml = "";

  function flushList() {
    if (inList) {
      html.push(listHtml + "</ul>");
      inList = false;
      listHtml = "";
    }
  }

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    const nextLine = i + 1 < lines.length ? lines[i + 1].trim() : "";

    // Fenced blocks
    if (trimmed.startsWith("```glossary")) { inGlossary = true; glossaryLines = []; i++; continue; }
    if (trimmed.startsWith("```") && !trimmed.includes("glossary")) {
      if (inCodeBlock) {
        const lang = codeLang ? ` class="language-${codeLang}"` : "";
        html.push(`<pre><code${lang}>${codeLines.join("\n")}</code></pre>`);
        inCodeBlock = false; codeLines = [];
        i++; continue;
      }
      inCodeBlock = true;
      codeLang = trimmed.slice(3).trim();
      codeLines = [];
      i++; continue;
    }
    if (inCodeBlock) { codeLines.push(trimmed); i++; continue; }

    if (trimmed === "```" && inGlossary) { inGlossary = false; flushList(); i++; continue; }
    if (inGlossary) {
      const colonIdx = trimmed.indexOf("：");
      if (colonIdx > 0) {
        const term = trimmed.slice(0, colonIdx).trim();
        const def = trimmed.slice(colonIdx + 1).trim();
        html.push(`<p class="glossary-term">${term}</p><p class="glossary-def">${def}</p>`);
      }
      i++; continue;
    }

    // [flow]
    if (trimmed === "[flow]") { inFlow = true; flowLines = []; i++; continue; }
    if (trimmed === "[/flow]") {
      inFlow = false;
      const steps = flowLines.filter(l => l.trim()).map(l => l.trim());
      const parts = steps.map(s => `<span class="flow-step">${s}</span>`).join(`<span class="flow-arrow">→</span>`);
      html.push(`<div class="flow-row">${parts}</div>`);
      i++; continue;
    }
    if (inFlow) { flowLines.push(trimmed); i++; continue; }

    // [tags]
    if (trimmed === "[tags]") { inTags = true; tagLines = []; i++; continue; }
    if (trimmed === "[/tags]") {
      inTags = false;
      const tags = tagLines.filter(l => l.trim()).map(l => {
        const m = l.match(/^\s*(\w+)\s*[:：]\s*(.+)/);
        if (m) return `<span class="tag ${m[1].toLowerCase()}">${m[2].trim()}</span>`;
        return `<span class="tag">${l.trim()}</span>`;
      }).join(" ");
      html.push(`<p>${tags}</p>`);
      i++; continue;
    }
    if (inTags) { tagLines.push(trimmed); i++; continue; }

    // [summary]
    if (trimmed === "[summary]") { inSummary = true; summaryLines = []; i++; continue; }
    if (trimmed === "[/summary]") {
      inSummary = false;
      const items = summaryLines.filter(l => l.trim()).map(l => {
        const m = l.match(/^\s*([\d.+\-]+)\s*[:：]\s*(.+)/);
        if (m) return `<div class="summary-item"><div class="num">${m[1].trim()}</div><div class="desc">${m[2].trim()}</div></div>`;
        return "";
      }).join("");
      html.push(`<div class="summary-grid">${items}</div>`);
      i++; continue;
    }
    if (inSummary) { summaryLines.push(trimmed); i++; continue; }

    // Empty line
    if (!trimmed) { flushList(); html.push(""); i++; continue; }

    // h1: section
    if (trimmed.startsWith("# ") && !trimmed.startsWith("## ")) {
      flushList();
      sectionCounter++;
      const content = trimmed.slice(2);
      const colonIdx = content.indexOf("：");
      let label = "", title = content;
      if (colonIdx > 0) { label = content.slice(0, colonIdx).trim(); title = content.slice(colonIdx + 1).trim(); }
      const id = slugify(title) || `section-${sectionCounter}`;
      const lead = nextLine.startsWith("> ") ? `<p class="lead">${nextLine.slice(2)}</p>` : "";
      if (nextLine.startsWith("> ")) i++;
      html.push(`<section class="handout-section" id="${id}"><div class="reveal">`);
      if (label) html.push(`<span class="section-label">${label}</span>`);
      html.push(`<h2 class="section-title">${title}</h2>`);
      if (lead) html.push(lead);
      tocItems.push({ id, label, title, subs: [] });
      i++; continue;
    }

    // h2: sub-section
    if (trimmed.startsWith("## ") && !trimmed.startsWith("### ")) {
      flushList();
      const title = trimmed.slice(3);
      const id = `sub-${slugify(title)}`;
      if (tocItems.length > 0) {
        tocItems[tocItems.length - 1].subs.push({ id, title });
      }
      html.push(`<h3 class="sub-title" id="${id}"><span class="bar"></span>${title}</h3>`);
      i++; continue;
    }

    // h3: card
    if (trimmed.startsWith("### ")) {
      flushList();
      const content = trimmed.slice(4);
      const emojiMatch = content.match(/^([\u{1F000}-\u{1FFFF}]|[\u2600-\u27BF]|[\u{2700}-\u{27BF}]|[✅⚠️💡🔧📖🎯🔑🛠️])\s*/u);
      let icon = "", title = content;
      if (emojiMatch) { icon = emojiMatch[1]; title = content.slice(emojiMatch[0].length); }
      html.push(`<div class="card"><h3 class="card-title">${icon ? `<span class="icon">${icon}</span>` : ""}${title}</h3>`);
      // Collect body until next heading or empty line
      i++;
      while (i < lines.length) {
        const t = lines[i].trim();
        if (!t || t.startsWith("#") || t.startsWith("```") || t.startsWith("[") || t.startsWith("`step`") || t.startsWith("> **")) break;
        if (t.startsWith("- ")) {
          html.push(`<ul>${collectList(lines, i)}`);
          while (i < lines.length && lines[i].trim().startsWith("- ")) i++;
          html.push("</ul>");
          continue;
        }
        html.push(`<p>${t}</p>`);
        i++;
      }
      html.push(`</div>`);
      continue;
    }

    // step
    if (trimmed.startsWith("`step`")) {
      flushList();
      stepCounter++;
      const rest = trimmed.slice(6).trim();
      const colonIdx = rest.indexOf("：");
      let name = rest, desc = "";
      if (colonIdx > 0) { name = rest.slice(0, colonIdx).trim(); desc = rest.slice(colonIdx + 1).trim(); }
      html.push(`<div class="step"><div class="step-num">${stepCounter}</div><div class="step-content"><h4>${name}</h4>${desc ? `<p>${desc}</p>` : ""}</div></div>`);
      i++; continue;
    }

    // Checklist
    if (trimmed.startsWith("- [x] ") || trimmed.startsWith("- [ ] ")) {
      flushList();
      html.push('<ul class="checklist">');
      while (i < lines.length) {
        const t = lines[i].trim();
        const checked = t.startsWith("- [x] ");
        const unchecked = t.startsWith("- [ ] ");
        if (!checked && !unchecked) break;
        const text = t.slice(checked ? 6 : 6);
        html.push(`<li>${text}</li>`);
        i++;
      }
      html.push("</ul>");
      continue;
    }

    // Unordered list
    if (trimmed.startsWith("- ") && !trimmed.startsWith("- [") && !trimmed.startsWith(">")) {
      const items = [];
      while (i < lines.length) {
        const t = lines[i].trim();
        if (!t.startsWith("- ")) break;
        items.push(t.slice(2));
        i++;
      }
      html.push(`<ul>${items.map(it => `<li>${it}</li>`).join("")}</ul>`);
      continue;
    }

    // Tip / Warning
    if (trimmed.startsWith("> **💡") || trimmed.startsWith("> **⚠️")) {
      const isWarning = trimmed.includes("⚠️");
      const m = trimmed.match(/^> \*\*([\u{1F000}-\u{1FFFF}]|[\u2600-\u27BF]|[✅⚠️💡🔧📖🎯🔑🛠️])\s*([^*]+)\*\*\s*(.*)/u);
      if (m) {
        const label = m[2].trim();
        const text = m[3].trim();
        const cls = isWarning ? "warning-box" : "tip-box";
        html.push(`<div class="${cls}"><span class="label">${m[1]} ${label}</span> ${text}</div>`);
      } else {
        html.push(`<blockquote>${trimmed.slice(2)}</blockquote>`);
      }
      i++; continue;
    }

    // Table
    if (trimmed.startsWith("|")) {
      flushList();
      const tableHtml = [];
      let inHeader = true;
      tableHtml.push("<table>");
      while (i < lines.length) {
        const t = lines[i].trim();
        if (!t.startsWith("|")) break;
        // Skip separator row
        if (t.match(/^\|[\s:-]+\|/)) { i++; inHeader = false; continue; }
        const cells = t.split("|").filter(c => c !== undefined).map(c => c.trim()).filter(c => c);
        const tag = inHeader ? "th" : "td";
        tableHtml.push(`<tr>${cells.map(c => `<${tag}>${c}</${tag}>`).join("")}</tr>`);
        i++;
      }
      tableHtml.push("</table>");
      html.push(tableHtml.join(""));
      continue;
    }

    // Regular paragraph
    flushList();
    html.push(`<p>${trimmed}</p>`);
    i++;
  }

  flushList();
  return { html: html.filter(h => h !== "").join("\n"), toc: tocItems };
}

function collectList(lines, startIdx) {
  const items = [];
  let i = startIdx;
  while (i < lines.length && lines[i].trim().startsWith("- ")) {
    items.push(`<li>${lines[i].trim().slice(2)}</li>`);
    i++;
  }
  return items.join("");
}

// ===== Template filling =====

function fillTemplate(template, vars) {
  let result = template;
  for (const [key, value] of Object.entries(vars)) {
    result = result.replace(new RegExp(`\\{\\{${key}\\}\\}`, "g"), value);
  }
  return result;
}

// ===== Main =====

function main() {
  const courseDir = process.argv[2] || ".";
  const skillDir = __dirname.replace(/scripts$/, "");

  // Load configs
  const globalConfig = loadYaml(join(skillDir, "config", "global.yaml"));
  const courseConfig = loadYaml(join(courseDir, "config.yaml"));
  const config = deepMerge(globalConfig, courseConfig);

  const page = config.page || {};
  const instructor = config.instructor || {};
  const handout = config.handout || {};
  const footer = config.footer || {};

  // Load content
  const contentPath = join(courseDir, "content.md");
  if (!existsSync(contentPath)) {
    console.error("Error: content.md not found in", courseDir);
    process.exit(1);
  }
  const md = readFileSync(contentPath, "utf-8");
  const { html: bodyHtml, toc } = parseContent(md);

  // Build TOC HTML
  const tocHtml = toc.length > 0 ? `<section class="toc-section"><div class="container"><h2>目錄</h2><ol class="toc-list">${toc.map(s =>
    `<li><a href="#${s.id}">${s.title}</a>${s.subs.length > 0 ? `<ol class="toc-sublist">${s.subs.map(sub => `<li><a href="#${sub.id}">${sub.title}</a></li>`).join("")}</ol>` : ""}</li>`
  ).join("")}</ol></div></section>` : "";

  // Build cover subtitle
  const coverSub = page.subtitle ? `<p class="subtitle">${page.subtitle}</p>` : "";

  // Build cover meta
  const metaParts = [];
  if (instructor.name) metaParts.push(`👤 ${instructor.name}`);
  if (handout.edition) metaParts.push(handout.edition);
  const coverMeta = metaParts.join(" ｜ ");

  // Load template
  const templatePath = join(skillDir, "reference", "base.html");
  if (!existsSync(templatePath)) {
    console.error("Error: base.html template not found");
    process.exit(1);
  }
  const template = readFileSync(templatePath, "utf-8");

  const vars = {
    PAGE_LANG: page.lang || "zh-TW",
    PAGE_TITLE: page.title || "Handout",
    COLOR_PRIMARY: page.color_primary || "#B85C38",
    COLOR_ACCENT: page.color_accent || "#D4A853",
    COLOR_BG: page.color_bg || "#FDF8F4",
    COLOR_TEXT: page.color_text || "#2D1B14",
    PRINT_PAGE_SIZE: handout.page_size || "A4",
    PRINT_MARGIN: handout.print_margin || "2cm",
    COVER_TAG: page.tag || "COURSE HANDOUT",
    COVER_TITLE: page.title || "Handout",
    COVER_SUBTITLE: coverSub,
    COVER_META: coverMeta,
    TOC_SECTION: tocHtml,
    CONTENT: bodyHtml,
    FOOTER_TITLE: page.title || "Handout",
    FOOTER_COPYRIGHT: footer.copyright || "© All rights reserved.",
  };

  const output = fillTemplate(template, vars);

  // Write output
  const outDir = join(courseDir, "dist");
  if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true });
  const outPath = join(outDir, "index.html");
  writeFileSync(outPath, output, "utf-8");
  console.log(`✓ Built: ${outPath}`);
}

main();
