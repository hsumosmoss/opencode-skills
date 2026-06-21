# OpenCode Skills

一套專為 [OpenCode](https://opencode.ai) 設計的 Skills 擴充套件包，提供文件處理、設計、簡報、影片製作、開發工具等多領域的 AI 輔助工作流程。

**跨平台支援**：🍎 macOS (Apple Silicon) 已驗證 ｜ 🪟 Windows 已驗證

---

## 快速開始

### 安裝系統級工具
<details>
<summary><b>🍎 macOS（Apple Silicon）</b></summary>

```bash
# Homebrew（套件管理）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 核心工具
brew install ffmpeg node python@3.13 uv
uv python install 3.13

# Python 套件
pip3 install edge-tts openpyxl pandas python-pptx pillow pyyaml \
             pypdf pdfplumber reportlab defusedxml \
             playwright anthropic mcp
pip3 install "markitdown[pptx]"

# Node.js 套件
npm install -g playwright pptxgenjs sharp puppeteer
npm install -g react react-dom react-icons
npx playwright install chromium
```
</details>

<details>
<summary><b>🪟 Windows</b></summary>

```powershell
# 核心工具
winget install "FFmpeg (Essentials Build)"
winget install Python.Python.3.13
winget install OpenJS.NodeJS.LTS

# Python 套件
pip install edge-tts openpyxl pandas python-pptx pillow pyyaml `
           pypdf pdfplumber reportlab defusedxml `
           playwright anthropic mcp
pip install "markitdown[pptx]"

# Node.js 套件
npm install -g playwright pptxgenjs sharp puppeteer
npm install -g react react-dom react-icons
npx playwright install chromium

# 選擇性（字體）
Invoke-WebRequest https://github.com/ButTaiwan/genseki-font/raw/master/TW/GenSekiGothic2TW-H.otf
```
</details>

### 部署 Skills
```bash
cp -r .opencode/skills/ ~/.config/opencode/skills/
```

### 設定 OpenCode
在 `opencode.jsonc` 中加入：
```jsonc
{
  "permission": {
    "skill": { "*": "allow" }
  }
}
```

重啟後執行 `opencode debug skill` 確認載入。

---

## 所有 29 個 Skills 與依賴總表

### 🎬 影片製作

| Skill | 平台 | 用途 | 必要依賴 |
|-------|------|------|---------|
| `video-maker` | 🍎🪟 | 活動紀錄 / 教學 / 社群科普影片 | ffmpeg, edge-tts, Playwright, Node.js |
| `video-podcast-maker` | 🍎🐧 | 自動化 4K 影片播客（Remotion） | ffmpeg, edge-tts, Node.js, yarn, Remotion |

### 📄 文件處理

| Skill | 平台 | 用途 | 必要依賴 |
|-------|------|------|---------|
| `docx` | 🍎🪟🐧 | Word 文件建立/編輯/分析 | pandoc, LibreOffice, poppler, npm docx, defusedxml |
| `pdf` | 🍎🪟🐧 | PDF 處理（讀/寫/合併/OCR） | pypdf, pdfplumber, reportlab, poppler, qpdf, pytesseract |
| `pptx` | 🍎🪟🐧 | PowerPoint 簡報建立/編輯 | pptxgenjs, playwright, sharp, markitdown, LibreOffice |
| `xlsx` | 🍎🪟🐧 | Excel 試算表處理 | openpyxl, pandas, LibreOffice（公式重算）|

### 🎨 設計與前端

| Skill | 平台 | 用途 | 必要依賴 |
|-------|------|------|---------|
| `canvas-design` | 🍎🪟 | PNG/PDF 設計圖產出 | 無（系統字體） |
| `algorithmic-art` | 🍎🪟 | p5.js 生成式藝術 | 無（CDN p5.js） |
| `frontend-design` | 🍎🪟 | Web 前端設計指南 | 無（CDN 資源） |
| `web-design-engineer` | 🍎🪟 | HTML/CSS/JS/React 頁面 | 無（CDN 資源） |
| `brand-guidelines` | 🍎🪟 | 品牌色/字型規範 | 無（純文件）|
| `theme-factory` | 🍎🪟 | 主題配色套用 | 無（純參考）|
| `huashu-design` | 🍎🪟 | HTML 高保真原型/動畫 | Playwright, ffmpeg, yt-dlp, sharp |
| `web-artifacts-builder` | 🍎🪟 | React+Tailwind 複雜 artifact | Node.js, npm |

### 📊 簡報與教學

| Skill | 平台 | 用途 | 必要依賴 |
|-------|------|------|---------|
| `presentation-architect` | 🍎🪟 | 簡報架構企劃（雙模式） | Python 3 |
| `soil-html-deck` | 🍎🪟 | HTML 互動簡報 | Python 3 |
| `soil-image-deck` | 🍎🪟 | 全圖片 PPTX 簡報 | python-pptx, Pillow, PyYAML |
| `soil-teaching-deck` | 🍎🪟 | SOIL 教學 PPTX | python-pptx |
| `course-page-generator` | 🍎🪟 | 課程頁面 + OG 縮圖 | Node.js, Puppeteer |
| `course-handout-generator` | 🍎🪟 | 教學講義 Markdown→HTML 建置管線 | Node.js, js-yaml |

### 🔧 開發工具

| Skill | 平台 | 用途 | 必要依賴 |
|-------|------|------|---------|
| `mcp-builder` | 🍎🪟 | MCP Server 建構指南 | Python (anthropic, mcp) 或 TypeScript |
| `webapp-testing` | 🍎🪟 | Playwright 本機 Web 測試 | Playwright (pip) |
| `skill-creator` | 🍎🪟 | 建立自訂 Skill | Python 3 |
| `github-setup` | 🍎🪟 | Git/GitHub 連線設定 | git, gh CLI（選擇性）|

### 💬 多媒體與溝通

| Skill | 平台 | 用途 | 必要依賴 |
|-------|------|------|---------|
| `slack-gif-creator` | 🍎🪟 | Slack 最佳化 GIF 動圖 | pillow, imageio, numpy |
| `internal-comms` | 🍎🪟 | 內部通訊文件模板 | 無（純模板）|

### 🗣️ 語音

| Skill | 平台 | 用途 | 必要依賴 |
|-------|------|------|---------|
| `xu-yaowen-voice` | 🪟 | 許耀文語音克隆 TTS（VoxCPM2） | NVIDIA GPU, Python 3.10–3.12, voxcpm |

### 📝 其他

| Skill | 平台 | 用途 | 必要依賴 |
|-------|------|------|---------|
| `doc-coauthoring` | 🍎🪟 | 結構化文件協作流程 | 無（純流程）|
| `my-skill` | 🍎🪟 | Skill 開發範本 | 無（範本）|

---

## 平台圖例

| 圖示 | 平台 | 安裝命令 |
|------|------|---------|
| 🍎 | macOS (Apple Silicon) | `brew install <套件>` |
| 🪟 | Windows | `winget install <套件>` |
| 🐧 | Linux | `apt-get install <套件>` |

> 標示僅 🪟 的 Skill 表示**僅支援 Windows**（如 `xu-yaowen-voice` 依賴 NVIDIA CUDA + VoxCPM2）。

---

## 影片製作速查（video-maker）

```bash
# 1. 產生旁白（edge-tts 男聲）
python3 scripts/generate_narration.py

# 2. 啟動本地伺服器（錄影用）
python3 -m http.server 8080

# 3. Playwright 錄影
node record.cjs

# 4. Mux 合成
ffmpeg -y -ss 3 -i renders/*.webm -i master_audio.mp3 \
  -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \
  -movflags +faststart final.mp4
```

> ⚠️ 踩坑紀錄見 [video-maker/GOTCHAS.md](.opencode/skills/video-maker/GOTCHAS.md)

---

## 一鍵安裝腳本

### 🍎 macOS
```bash
# 安裝所有可能需要的套件（約 5 分鐘）
brew install ffmpeg node python@3.13 uv
pip3 install edge-tts openpyxl pandas python-pptx pillow pyyaml \
             pypdf pdfplumber reportlab defusedxml playwright
npm install -g playwright pptxgenjs sharp puppeteer
npx playwright install chromium
```

### 🪟 Windows
```powershell
# 安裝所有可能需要的套件
winget install "FFmpeg (Essentials Build)" Python.Python.3.13 OpenJS.NodeJS.LTS
pip install edge-tts openpyxl pandas python-pptx pillow pyyaml `
           pypdf pdfplumber reportlab defusedxml playwright
npm install -g playwright pptxgenjs sharp puppeteer
npx playwright install chromium
```

---

## 建立自己的 Skill

```
my-skill/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

`SKILL.md` 格式：

```markdown
---
name: my-skill
description: 何時該用這個 Skill
compatibility: opencode
---

# Skill 名稱

給 AI 的指令...
```

詳見 [`SKILLS.md`](SKILLS.md) 完整說明。

---

## 環境紀錄

| 環境 | 晶片 | 測試日期 | 測試項目 |
|------|------|---------|---------|
| macOS Sequoia 15.5 | Apple Silicon M4 | 2026-06-19 | video-maker 完整流程（edge-tts 旁白 + Playwright 錄影 + ffmpeg 合成）|
| Windows | x86_64 | 2025 | video-maker 原始開發環境 |

---

## 來源

這些 Skills 最初源自 Antigravity Editor，經改寫以相容 OpenCode 格式。
