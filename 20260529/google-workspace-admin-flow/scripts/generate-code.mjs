#!/usr/bin/env node
/**
 * 行政專案工作流 Code.gs 生成器
 *
 * 用法：
 *   node generate-code.mjs --root <folderId> [options]
 *
 * 必填：
 *   --root <folderId>       Drive 總資料夾 ID
 *
 * 選填：
 *   --control <sheetId>     既有總控表 ID（留空會自動建）
 *   --calendar <id>         Calendar ID（預設 primary）
 *   --admin <email>         錯誤通知收件 Email
 *   --timezone <tz>         時區（預設 Asia/Taipei）
 *   --offices <list>        處室列表逗號分隔（會把 Form 改成下拉選單）
 *   --out <path>            輸出檔案路徑（預設 ./build/Code.gs）
 *
 * 範例：
 *   node generate-code.mjs --root 1AbCd... --calendar primary --admin a@b.com
 *   node generate-code.mjs --root 1AbCd... --offices "教務處,學務處,總務處"
 */

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEMPLATE_PATH = resolve(__dirname, '..', 'templates', 'Code.gs');

// ── 解析 CLI 參數 ──────────────────────────────────────────
function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i];
    if (!k.startsWith('--')) continue;
    const v = argv[i + 1];
    if (!v || v.startsWith('--')) { args[k.slice(2)] = true; continue; }
    args[k.slice(2)] = v;
    i++;
  }
  return args;
}

// ── 清理 ID（支援整段 URL）──────────────────────────────────
function cleanId(value) {
  if (!value) return '';
  const t = String(value).trim();
  const patterns = [/\/folders\/([a-zA-Z0-9_-]+)/, /\/d\/([a-zA-Z0-9_-]+)/];
  for (const p of patterns) {
    const m = t.match(p);
    if (m) return m[1];
  }
  return t;
}

// ── 主流程 ─────────────────────────────────────────────────
async function main() {
  const args = parseArgs(process.argv);

  if (!args.root) {
    console.error('❌ 缺少 --root 參數');
    console.error('用法：node generate-code.mjs --root <folderId>');
    process.exit(1);
  }

  const settings = {
    rootFolderId:    cleanId(args.root),
    controlSheetId:  cleanId(args.control || ''),
    calendarId:      args.calendar || 'primary',
    adminEmail:      args.admin || 'admin@example.com',
    timezone:        args.timezone || 'Asia/Taipei',
  };

  console.log('🔧 生成器設定：');
  Object.entries(settings).forEach(([k, v]) => console.log(`   ${k}: ${v || '(空)'}`));

  // 讀取模板
  let code = await readFile(TEMPLATE_PATH, 'utf8');

  // 替換 SETTINGS 區塊
  const newSettings = [
    'const SETTINGS = {',
    `  rootFolderId:    ${JSON.stringify(settings.rootFolderId)},`,
    `  controlSheetId:  ${JSON.stringify(settings.controlSheetId)},`,
    `  calendarId:      ${JSON.stringify(settings.calendarId)},`,
    `  adminEmail:      ${JSON.stringify(settings.adminEmail)},`,
    `  timezone:        ${JSON.stringify(settings.timezone)},`,
    '};',
  ].join('\n');

  code = code.replace(/const SETTINGS = \{[\s\S]*?\};/m, newSettings);

  // 客製化處室列表 → Form 改下拉選單
  if (args.offices) {
    const officeList = args.offices.split(/[,，]/).map(s => s.trim()).filter(Boolean);
    const officeJson = JSON.stringify(officeList);
    code = code.replace(
      /f\.addTextItem\(\)\.setTitle\('承辦處室'\)\.setRequired\(true\)\.setHelpText\([^)]+\);/,
      `f.addListItem().setTitle('承辦處室').setRequired(true).setChoiceValues(${officeJson});`,
    );
    console.log(`   officesOverride: ${officeJson}`);
  }

  // 寫出
  const outPath = resolve(args.out || './build/Code.gs');
  await mkdir(dirname(outPath), { recursive: true });
  await writeFile(outPath, code, 'utf8');

  console.log(`✅ 已產出：${outPath}`);
  console.log('');
  console.log('下一步：');
  console.log('  1. 開 https://script.google.com 新建專案');
  console.log('  2. 把產出的 Code.gs 內容貼進去');
  console.log('  3. 執行 installFlow()');
  console.log('  或');
  console.log('  跑 deploy-via-clasp.ps1 自動部署');
}

main().catch(err => {
  console.error('❌ 生成失敗：', err.message);
  process.exit(1);
});
