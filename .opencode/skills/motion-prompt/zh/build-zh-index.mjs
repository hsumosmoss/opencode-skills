#!/usr/bin/env node
/**
 * Motion Prompt — build the Chinese index.
 *
 * Merges the upstream catalog (never edited) with the local translation
 * overlay `zh.json`, and writes:
 *   index.zh.tsv                     id / pack / category(zh) / names / meaning / tags / summary
 *   missing.txt                      upstream ids that have no Chinese entry yet
 *   ../references/motion-prompt-zh.md  human-readable cheat sheet, grouped by pack
 *
 * Usage:
 *   node build-zh-index.mjs                # fetch the live catalog
 *   node build-zh-index.mjs --local <file> # use a catalog.json on disk
 *   node build-zh-index.mjs --quiet
 *
 * MIT License. Local addition; upstream is not modified.
 */
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const DEFAULT_SOURCES = [
  "https://showheyohtaki.github.io/motion-prompt/api/v1/catalog.json",
  "https://raw.githubusercontent.com/showheyohtaki/motion-prompt/main/api/v1/catalog.json",
];

const argv = process.argv.slice(2);
const flag = (name) => argv.includes(name);
const value = (name, fallback = null) => {
  const i = argv.indexOf(name);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : fallback;
};

const quiet = flag("--quiet");
const localPath = value("--local");

async function loadCatalog() {
  if (localPath) {
    return JSON.parse(await readFile(localPath, "utf8"));
  }
  let lastError;
  for (const url of DEFAULT_SOURCES) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(20000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      lastError = err;
    }
  }
  throw new Error(
    `No catalog source answered (${lastError?.message}). ` +
      "Pass --local <path/to/catalog.json> to work offline."
  );
}

const clean = (s) => String(s ?? "").replace(/[\t\r\n]+/g, " ").trim();

// Display name: primary term plus optional aliases in full-width brackets.
// zh.json keeps them apart so the primary name never grows over time.
const zhName = (zh) => {
  if (!zh?.name) return "";
  const aka = (zh.aka ?? []).filter(Boolean);
  return aka.length ? `${zh.name}（${aka.join("／")}）` : zh.name;
};

const catalog = await loadCatalog();
const overlay = JSON.parse(await readFile(join(HERE, "zh.json"), "utf8"));
const entries = overlay.entries ?? {};
const catZh = overlay.categories ?? {};
const packZh = overlay.packs ?? {};

const records = [];
const missing = [];
const unknown = Object.keys(entries).filter(
  (id) => !catalog.elements.some((e) => e.id === id)
);

for (const el of catalog.elements) {
  const zh = entries[el.id];
  if (!zh) missing.push(el.id);
  const record = {
    id: el.id,
    pack: el.pack,
    category: el.category,
    categoryZh: clean(
      catZh[`${el.pack}/${el.category}`] ?? catZh[el.category] ?? el.category
    ),
    packZh: clean(packZh[el.pack] ?? el.pack),
    nameZh: clean(zhName(zh)),
    nameEn: clean(el.name?.en ?? ""),
    nameJa: clean(el.name?.ja ?? ""),
    meaningZh: clean(zh?.meaning ?? ""),
    tagsZh: clean((zh?.tags ?? []).join(", ")),
    summaryZh: clean(zh?.summary ?? ""),
    tagsEn: clean(el.tags?.join(", ") ?? ""),
  };
  records.push(record);
}

const rows = records.map((r) =>
  [
    r.id,
    r.pack,
    r.categoryZh,
    r.nameZh,
    r.nameEn,
    r.nameJa,
    r.meaningZh,
    r.tagsZh,
    r.summaryZh,
    r.tagsEn,
  ].join("\t")
);

const header = [
  "# Motion Prompt 中文索引",
  `# upstream version ${catalog.version} · ${catalog.count} elements · packed ${overlay.updated}`,
  "# id\tpack\tcategory\tname_zh\tname_en\tname_ja\tmeaning_zh\ttags_zh\tsummary_zh\ttags_en",
].join("\n");

await writeFile(join(HERE, "index.zh.tsv"), `${header}\n${rows.join("\n")}\n`, "utf8");
await writeFile(
  join(HERE, "missing.txt"),
  missing.length ? `${missing.join("\n")}\n` : "",
  "utf8"
);

// ---------------------------------------------------------------------------
// Cheat sheet: same data, grouped the way the gallery is (pack → category).
// ---------------------------------------------------------------------------
const mdCell = (s) => String(s ?? "").replace(/\|/g, "\\|").replace(/[\r\n]+/g, " ").trim();

const packOrder = [...(catalog.packs ?? [])].sort(
  (a, b) => (a.order ?? 0) - (b.order ?? 0)
);
const byPack = new Map();
for (const r of records) {
  if (!byPack.has(r.pack)) byPack.set(r.pack, []);
  byPack.get(r.pack).push(r);
}

const lines = [
  "# Motion Prompt 中文速查",
  "",
  `> 上游版本 \`${catalog.version}\` · ${catalog.count} 筆 · 索引更新 ${overlay.updated}`,
  ">",
  "> 來源 <https://showheyohtaki.github.io/motion-prompt/>（MIT，© Shohei Ohtaki）",
  ">",
  "> 這份表只有名稱與一句話；**秒數、緩動曲線與程式碼請用 `get` 取**：",
  "> `node scripts/motion-prompt.mjs get <id>`",
  ">",
  "> 開畫廊挑選：`node scripts/motion-prompt.mjs pick --pack <pack>`",
  "",
];

for (const pack of packOrder) {
  const items = byPack.get(pack.pack) ?? [];
  if (!items.length) continue;
  const title = packZh[pack.pack] ?? pack.title?.en ?? pack.pack;
  lines.push(`## ${pack.pack} · ${title}（${items.length}）`, "");

  const cats = [...(pack.categories ?? [])];
  const catOrder = cats.map((c) => c.slug);
  const groups = new Map();
  for (const r of items) {
    if (!groups.has(r.category)) groups.set(r.category, []);
    groups.get(r.category).push(r);
  }
  const ordered = [
    ...catOrder.filter((slug) => groups.has(slug)),
    ...[...groups.keys()].filter((slug) => !catOrder.includes(slug)),
  ];

  for (const slug of ordered) {
    const group = groups.get(slug);
    const catTitle = group[0]?.categoryZh || slug;
    lines.push(`### ${catTitle}`, "");
    lines.push("| # | 中文 | English | 一句話 |", "|---|---|---|---|");
    for (const r of group) {
      lines.push(
        `| ${r.id} | ${mdCell(r.nameZh)} | ${mdCell(r.nameEn)} | ${mdCell(r.meaningZh)} |`
      );
    }
    lines.push("");
  }
}

const cheatsheetPath = join(ROOT, "references", "motion-prompt-zh.md");
await mkdir(dirname(cheatsheetPath), { recursive: true });
await writeFile(cheatsheetPath, `${lines.join("\n").trimEnd()}\n`, "utf8");

if (!quiet) {
  const translated = catalog.elements.length - missing.length;
  console.log(`Catalog   ${catalog.version} · ${catalog.elements.length} elements`);
  console.log(`Translated ${translated} / ${catalog.elements.length}`);
  console.log(`Missing    ${missing.length}${missing.length ? ` → ${missing.join(", ")}` : ""}`);
  console.log(`Wrote      ${join(HERE, "index.zh.tsv")}`);
  console.log(`Wrote      ${cheatsheetPath}`);
  if (unknown.length) {
    console.log(`Overlay ids not in upstream (kept, ignored): ${unknown.join(", ")}`);
  }
}
