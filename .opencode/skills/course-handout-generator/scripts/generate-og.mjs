#!/usr/bin/env node

import { writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createRequire } from "module";

const __dirname = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);

function resolvePuppeteer() {
  const candidates = [
    fileURLToPath(import.meta.url),
    join(__dirname, "package.json"),
    join(process.cwd(), "package.json"),
  ];
  for (const base of candidates) {
    try { const req = createRequire(base); return req("puppeteer"); } catch {}
  }
  return null;
}

const args = {};
process.argv.slice(2).forEach((arg, i, arr) => {
  if (arg.startsWith("--")) {
    const key = arg.slice(2);
    const val = arr[i + 1];
    if (val && !val.startsWith("--")) args[key] = val;
    else args[key] = true;
  }
});

const title = args.title || "Handout Title";
const subtitle = args.subtitle || "";
const instructor = args.instructor || "";
const color = args.color || "#B85C38";
const slug = args.slug || "handout";
const output = args.output || join(process.cwd(), `og-${slug}.png`);

const html = `<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1200px;height:630px;font-family:"Noto Sans TC","Microsoft JhengHei",sans-serif;background:linear-gradient(135deg,${color},${color}dd);display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}
.bg{position:absolute;border-radius:50%;background:rgba(255,255,255,0.06)}
.b1{width:500px;height:500px;top:-150px;right:-100px}
.b2{width:300px;height:300px;bottom:-80px;left:-60px}
.b3{width:200px;height:200px;bottom:100px;right:200px}
.c{position:relative;z-index:1;padding:60px;width:100%}
.badge{display:inline-block;background:rgba(255,255,255,0.2);color:#fff;font-size:14px;font-weight:600;padding:4px 14px;border-radius:20px;margin-bottom:24px;backdrop-filter:blur(4px)}
h1{color:#fff;font-size:48px;font-weight:800;line-height:1.2;margin-bottom:12px;max-width:800px}
.sub{color:rgba(255,255,255,0.85);font-size:22px;font-weight:400;line-height:1.4;margin-bottom:32px;max-width:650px}
.f{display:flex;align-items:center;gap:12px}
.a{width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,0.25);display:flex;align-items:center;justify-content:center;color:#fff;font-size:18px;font-weight:700}
.i{color:rgba(255,255,255,0.9);font-size:18px}
</style></head><body>
<div class="bg b1"></div><div class="bg b2"></div><div class="bg b3"></div>
<div class="c"><div class="badge">HANDOUT</div>
<h1>${title}</h1>
${subtitle ? `<div class="sub">${subtitle}</div>` : ""}
${instructor ? `<div class="f"><div class="a">${instructor.charAt(0)}</div><span class="i">${instructor}</span></div>` : ""}
</div></body></html>`;

async function main() {
  let browser;
  try {
    const puppeteer = resolvePuppeteer();
    if (!puppeteer) throw new Error("puppeteer not found");
    browser = await puppeteer.launch({ headless: true, args: ["--no-sandbox"] });
    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 630 });
    await page.setContent(html, { waitUntil: "networkidle0" });
    await page.screenshot({ path: output, type: "png" });
    console.log(`✓ OG image: ${output}`);
  } catch (err) {
    console.log("ℹ Puppeteer unavailable, saving HTML preview.");
    writeFileSync(output.replace(/\.png$/, ".html"), html);
  } finally {
    if (browser) await browser.close();
  }
}
main();
