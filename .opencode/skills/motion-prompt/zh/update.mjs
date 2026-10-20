#!/usr/bin/env node
/**
 * Sync the installed Motion Prompt skill from upstream, then rebuild the
 * Chinese index.
 *
 * Why this exists: the installed SKILL.md carries a local Chinese guide
 * (between the `zh-patch` markers) and a Chinese trigger phrase inside the
 * frontmatter description. Downloading upstream over it would lose both, so
 * this script stages the downloads, re-applies the two patches from
 * `zh/patch-description.txt` and `zh/patch-body.md`, backs up the old
 * SKILL.md, and finally runs `zh/build-zh-index.mjs`.
 *
 * Usage:
 *   node zh/update.mjs             # or: .\update.ps1
 *   node zh/update.mjs --check     # download + diff only, write nothing
 *   node zh/update.mjs --offline   # rebuild the index, skip downloads
 *
 * MIT License. Local addition; upstream is not modified.
 */
import { readFile, writeFile, mkdir, readdir, stat, unlink } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const BASE = "https://raw.githubusercontent.com/showheyohtaki/motion-prompt/main/skills/motion-prompt";

const FILES = [
  "SKILL.md",
  "scripts/motion-prompt.mjs",
  "references/porting.md",
];

const argv = process.argv.slice(2);
const flag = (name) => argv.includes(name);
const CHECK_ONLY = flag("--check");
const OFFLINE = flag("--offline");

const BLOCK_RE = /<!-- zh-patch:start[\s\S]*?zh-patch:end -->/;
const MARKER = "Read the catalog with the script that ships next to this file";

// The Chinese tail we own. Strip it before re-inserting so repeated syncs do
// not stack up punctuation (upstream may end with `"`, `.`, `。` or `;`).
const CN_TAIL = /[；;]?\s*中文：使用者說「打開動作庫」.*$/;

function applyDescription(text, suffix) {
  const lines = text.split("\n");
  const i = lines.findIndex((l) => l.startsWith("description:"));
  if (i < 0) return { text, ok: false, reason: "找不到 description 行" };
  const line = lines[i].replace(/\s+$/, "");
  if (!line.endsWith("'")) {
    return { text, ok: false, reason: "description 不是以單引號結尾，格式可能改了" };
  }
  let inner = line.slice(0, -1).replace(CN_TAIL, "");
  if (inner.includes(suffix)) return { text, ok: true, changed: false };
  const sep = /[.。;；,，]$/.test(inner) ? " " : "；";
  lines[i] = `${inner}${sep}${suffix}'`;
  return { text: lines.join("\n"), ok: true, changed: true };
}

function applyBody(text, block) {
  if (BLOCK_RE.test(text)) {
    const next = text.replace(BLOCK_RE, block.trim());
    return { text: next, ok: true, changed: next !== text };
  }
  const idx = text.indexOf(MARKER);
  if (idx < 0) {
    return {
      text: `${text.trimEnd()}\n\n${block.trim()}\n`,
      ok: false,
      changed: true,
      reason: `找不到插入點「${MARKER}」，已附加在檔尾`,
    };
  }
  return {
    text: text.slice(0, idx) + block.trim() + "\n\n" + text.slice(idx),
    ok: true,
    changed: true,
  };
}

async function fetchText(path) {
  const url = `${BASE}/${path}`;
  const res = await fetch(url, { signal: AbortSignal.timeout(30000) });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status} (${url})`);
  return res.text();
}

async function backupSkill() {
  const src = join(ROOT, "SKILL.md");
  if (!existsSync(src)) return null;
  const dir = join(HERE, "backup");
  await mkdir(dir, { recursive: true });
  const stamp = new Date()
    .toISOString()
    .replace(/[:.]/g, "-")
    .replace("T", "_")
    .slice(0, 19);
  const dst = join(dir, `SKILL.md.${stamp}`);
  await writeFile(dst, await readFile(src));
  const names = (await readdir(dir))
    .filter((n) => n.startsWith("SKILL.md."))
    .sort()
    .reverse();
  for (const old of names.slice(5)) await unlink(join(dir, old));
  return dst;
}

function rebuildIndex() {
  const r = spawnSync(process.execPath, [join(HERE, "build-zh-index.mjs")], {
    stdio: "inherit",
  });
  if (r.status !== 0) throw new Error("build-zh-index.mjs 失敗");
}

async function main() {
  if (!OFFLINE) {
    // Stage everything first: a half-finished sync is worse than none.
    const staged = new Map();
    for (const path of FILES) staged.set(path, await fetchText(path));

    const skillPath = join(ROOT, "SKILL.md");
    const suffix = (await readFile(join(HERE, "patch-description.txt"), "utf8")).trim();
    const block = (await readFile(join(HERE, "patch-body.md"), "utf8")).trim();

    let skill = staged.get("SKILL.md");
    const d = applyDescription(skill, suffix);
    const b = applyBody(d.text, block);
    skill = b.text;

    if (!d.ok) console.warn(`警告（description）：${d.reason}`);
    if (!b.ok) console.warn(`警告（中文導引）：${b.reason}`);

    const existing = existsSync(skillPath) ? await readFile(skillPath, "utf8") : null;

    for (const path of FILES) {
      const next = path === "SKILL.md" ? skill : staged.get(path);
      const dst = join(ROOT, path);
      const prev = existsSync(dst) ? await readFile(dst, "utf8") : null;
      if (prev === next) {
        console.log(`same      ${path}`);
        continue;
      }
      if (CHECK_ONLY) {
        console.log(`differs   ${path}`);
        continue;
      }
      await mkdir(dirname(dst), { recursive: true });
      if (path === "SKILL.md" && prev !== null) {
        const bak = await backupSkill();
        if (bak) console.log(`backup    ${bak}`);
      }
      await writeFile(dst, next, "utf8");
      console.log(`updated   ${path}`);
    }

    if (CHECK_ONLY) {
      console.log("--check：只比對，沒有寫入。");
      return;
    }
  } else {
    console.log("--offline：跳過下載，只重建索引。");
  }

  rebuildIndex();

  const missingPath = join(HERE, "missing.txt");
  const missing = existsSync(missingPath)
    ? (await readFile(missingPath, "utf8")).split(/\r?\n/).filter(Boolean)
    : [];
  if (missing.length) {
    console.log(`\n新未翻譯 ${missing.length} 筆：${missing.join(", ")}`);
    console.log("把中文補進 zh/zh.json 後再跑一次即可。");
  } else {
    console.log("\n全部 144 筆都有中文。");
  }
}

main().catch((err) => {
  console.error(`更新失敗：${err.message}`);
  process.exitCode = 1;
});
